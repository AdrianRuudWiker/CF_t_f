# -*- coding: utf-8 -*-
"""
PROTOTYPE — reformulert usikkerhetsmodell for SNCF (statens netto kontantstrøm
til SPU). IKKE integrert i arbeidsboken ennå; kjøres frittstående i Python.

Ideen (avklart med brukeren): i stedet for en 3x3 av vilkårlige prisskift,
kjør ÉN Monte Carlo på basisproduksjon der PERSENTILENE SELV ER SCENARIENE:
P90 = høy prognosert CF, P50 = median, P10 = lav.

Forankring i kilder (den offisielle presentasjonen "Statens petroleumsformue
til ekspertrådet for SPU", 19.03.2026 — ligger i repoet):
- Basis-priser = deck slide 5 / IEA WEO APS: olje -> 70 USD/fat fra 2035; gass
  6,6 (2030) -> 5,7 (2040+) USD/MMBtu. Verifisert at modellens pO/pG-baner
  stemmer eksakt med dette.
- Basis-produksjon + høy/lav = SDs mulighetsbilder (deck slide 10).
- Balansepriser (deck slide 14): norske prosjekter ~20-45 USD/fat før skatt
  (nyere ~30). Dette er den empiriske tilbudsrespons-terskelen.

Modellstruktur:
- Persistente REGIME-trekk (ett per simulering), som speiler "høybane/lavbane":
  pris = basis * lognormal faktor (persistent hele perioden), volum = triangulær
  interpolasjon lav/basis/høy (persistent). Dette matcher brukerens mentale
  modell (vedvarende høy-/lavregimer), ikke år-til-år-støy.
- Tilbudsrespons: feltets årlige netto gulves ved 0 (ingen tapsproduksjon),
  forankret i balanseprisene. Fjerner de meningsløse negative tallene.

FORANKRING (bryteren MEDIAN_ANCHOR):
  MEDIAN_ANCHOR=True  -> median[pris] = basis, altså P50 = NB26/APS. Da er
    P50-banen i viften nøyaktig det offisielle sentralanslaget, som er det
    persentiler-som-scenarier-designet krever. Prisen er at MIDDELET havner
    over basis (høyreskjev fordeling + driftsleverasje i kontantstrømmen).
  MEDIAN_ANCHOR=False -> E[pris] = basis. Da er middelet lik basis, men
    medianen (og dermed P50-banen) faller ~15 pst. UNDER NB26.
  Se HANDOFF.md. Middel/median-gapet i kontantstrømmen er ca. 18 pst. uansett
  valg; forankringen bestemmer bare hvilken av dem NB26 blir liggende på.

KALIBRERING av sigma (bryteren KALIBRERING):
  "historisk" (anbefalt): sigma leses ut av arbeidsbokens egne re-sentrerte
    historiske persentilforhold i Forutsetninger!B4:B7 (P90/P50 og P10/P50 av
    realpris 1997-2024, re-sentrert på NB26). For en medianforankret lognormal
    er sigma = ln(forhold) / z_p eksakt. Ingenting hardkodes, og den
    reformulerte viften reproduserer da de statiske prisskiftene i
    "Statisk modell" nøyaktig i P10/P90 — modellene blir konsistente.
  "manuell": bruker SIGMA_*_NED/OPP-konstantene under.

  Todelt (splitt-)lognormal støttes: eget sigma over og under medianen,
      faktor = exp(sigma_ned * z) for z < 0,  exp(sigma_opp * z) for z >= 0.
  Medianen er eksakt 1 uansett sigma-ene, så medianforankringen bevares. Dette
  er nødvendig hvis ytterkantene skal forankres i kilder som er asymmetriske
  rundt basis — se kalibrering.py og merknaden om IEA-scenariene der.

Kjøring:  python3 mc_reformulert.py
Krever:   numpy, openpyxl
"""
from statistics import NormalDist

import numpy as np
from openpyxl import load_workbook

FIL = "Kontantstromsmodell_petroleum.xlsx"
N = 10_000
SEED = 2026

# ----- Forankring og kalibrering -----
MEDIAN_ANCHOR = True     # True: median[pris]=basis (P50=NB26). False: E[pris]=basis
KALIBRERING = "historisk"  # "historisk" (fra Forutsetninger!B4:B7) eller "manuell"
SUPPLY_FLOOR = True      # balansepris-gulv: ingen tapsproduksjon (feltnetto >= 0)
RHO = 0.60               # korrelasjon olje/gass-regime

# Brukes bare når KALIBRERING == "manuell". Sett ned == opp for symmetrisk.
SIGMA_OLJE_NED = SIGMA_OLJE_OPP = 0.35
SIGMA_GASS_NED = SIGMA_GASS_OPP = 0.45

BBL, FX = 6.2898, 10.5   # fat/Sm3, NOK/USD (for prisimplikasjoner i USD)
P_KANT = 90              # persentilen de historiske forholdstallene gjelder
BASIS_OLJE_USD, BASIS_GASS_USD = 68.0, 5.7  # modellens basisnivå sent i banen

_z = NormalDist().inv_cdf


def les_basis():
    fu = load_workbook(FIL, data_only=True)["Forutsetninger"]
    col = lambda L: np.array([fu[f"{L}{18+i}"].value for i in range(25)])
    volO, volG, volN = col("B"), col("C"), col("D")
    totH, totL = col("F"), col("G")
    pO, pG, pN, cost, snks = col("J"), col("K"), col("L"), col("M"), col("N")
    tot = volO + volG + volN
    fh, fl = totH / tot, totL / tot
    andel = snks / (volO * pO + volG * pG + volN * pN - cost)
    par = {c: fu[f"B{r}"].value for c, r in
           (("k_olje_hoy", 4), ("k_olje_lav", 5), ("k_gass_hoy", 6), ("k_gass_lav", 7))}
    return dict(volO=volO, volG=volG, volN=volN, fh=fh, fl=fl,
                pO=pO, pG=pG, pN=pN, cost=cost, andel=andel, par=par)


def sigmaer(b):
    """(olje_ned, olje_opp, gass_ned, gass_opp) etter valgt kalibrering."""
    if KALIBRERING == "manuell":
        return SIGMA_OLJE_NED, SIGMA_OLJE_OPP, SIGMA_GASS_NED, SIGMA_GASS_OPP
    if KALIBRERING != "historisk":
        raise ValueError(f"ukjent KALIBRERING: {KALIBRERING!r}")
    # sigma = ln(persentilforhold) / z_p for en medianforankret lognormal
    zp = _z(P_KANT / 100.0)
    p = b["par"]
    return (-np.log(p["k_olje_lav"]) / zp, np.log(p["k_olje_hoy"]) / zp,
            -np.log(p["k_gass_lav"]) / zp, np.log(p["k_gass_hoy"]) / zp)


def _faktor(z, s_ned, s_opp, median_anchor):
    """Splitt-lognormal faktor. Uten medianforankring trekkes middelet til 1."""
    f = np.exp(np.where(z < 0, s_ned, s_opp) * z)
    return f if median_anchor else f / f.mean()


def simuler(b):
    rng = np.random.default_rng(SEED)
    s_on, s_oo, s_gn, s_go = sigmaer(b)
    # Persistente prisregimer (ett korrelert trekk per simulering)
    L = np.linalg.cholesky([[1, RHO], [RHO, 1]])
    z = rng.standard_normal((N, 2)) @ L.T
    oilfac = _faktor(z[:, 0], s_on, s_oo, MEDIAN_ANCHOR)[:, None]
    gasfac = _faktor(z[:, 1], s_gn, s_go, MEDIAN_ANCHOR)[:, None]
    # Persistent volum (triangulær lav/basis/høy), forventningsforankret
    w = rng.triangular(-1, 0, 1, N)
    volfac = np.where(w[:, None] >= 0, 1 + w[:, None] * (b["fh"] - 1),
                      1 - (-w[:, None]) * (1 - b["fl"]))
    volfac = volfac / (1 + (b["fh"] + b["fl"] - 2) / 6)
    # Kontantstrøm med balansepris-gulv (NGL følger olje)
    gross = volfac * (b["volO"] * b["pO"] * oilfac + b["volN"] * b["pN"] * oilfac
                      + b["volG"] * b["pG"] * gasfac - b["cost"])
    if SUPPLY_FLOOR:
        gross = np.maximum(gross, 0.0)
    sncf = b["andel"] * gross / 1000.0
    return sncf, oilfac[:, 0], gasfac[:, 0]


if __name__ == "__main__":
    b = les_basis()
    s_on, s_oo, s_gn, s_go = sigmaer(b)
    sncf, oilfac, gasfac = simuler(b)
    disc = np.arange(1, 26)
    cum = sncf.sum(axis=1)
    npv3 = (sncf / 1.03 ** disc).sum(axis=1)
    basis_cum = (b["andel"] * (b["volO"] * b["pO"] + b["volN"] * b["pN"]
                 + b["volG"] * b["pG"] - b["cost"]) / 1000).sum()
    p = lambda a, q: np.percentile(a, q)
    print(f"Forankring: {'MEDIAN (P50=basis)' if MEDIAN_ANCHOR else 'FORVENTNING (E=basis)'}"
          f" | gulv: {SUPPLY_FLOOR} | kalibrering: {KALIBRERING}")
    print(f"Sigma olje ned/opp {s_on:.3f}/{s_oo:.3f} | "
          f"gass ned/opp {s_gn:.3f}/{s_go:.3f}")
    print(f"Impliert oljepris USD/fat (2035+): P10 {BASIS_OLJE_USD*p(oilfac,10):.0f} / "
          f"P50 {BASIS_OLJE_USD*p(oilfac,50):.0f} / P90 {BASIS_OLJE_USD*p(oilfac,90):.0f} "
          f"/ middel {BASIS_OLJE_USD*oilfac.mean():.0f}")
    print(f"Impliert gasspris USD/MMBtu (2040+): P10 {BASIS_GASS_USD*p(gasfac,10):.1f} / "
          f"P50 {BASIS_GASS_USD*p(gasfac,50):.1f} / P90 {BASIS_GASS_USD*p(gasfac,90):.1f} "
          f"/ middel {BASIS_GASS_USD*gasfac.mean():.1f}")
    print(f"Kumulativ til fondet (mrd.): P10 {p(cum,10):.0f} / P50 {p(cum,50):.0f} / "
          f"P90 {p(cum,90):.0f} / middel {cum.mean():.0f} (basis {basis_cum:.0f})")
    print(f"NPV 3 pst. (mrd.):           P10 {p(npv3,10):.0f} / P50 {p(npv3,50):.0f} / "
          f"P90 {p(npv3,90):.0f} / middel {npv3.mean():.0f}")
    print(f"Andel negative årsverdier: {(sncf<0).mean()*100:.1f}%")
