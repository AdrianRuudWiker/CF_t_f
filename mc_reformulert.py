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
# Forankringen er avklart med brukeren 02.09.2026: BEGGE skal vises i
# leveransen — medianforankring som hovedspor, forventningsforankring som
# følsomhet — slik at Jensen-effekten blir eksplisitt for leseren.
MEDIAN_ANCHOR = True     # True: median[pris]=basis (P50=NB26). False: E[pris]=basis
KALIBRERING = "historisk"  # "historisk", "hybrid" eller "manuell"
SUPPLY_FLOOR = True      # balansepris-gulv: ingen tapsproduksjon (feltnetto >= 0)
RHO = 0.60               # korrelasjon olje/gass-regime

# Brukes bare når KALIBRERING == "manuell". Sett ned == opp for symmetrisk.
SIGMA_OLJE_NED = SIGMA_OLJE_OPP = 0.35
SIGMA_GASS_NED = SIGMA_GASS_OPP = 0.45

# Brukes bare når KALIBRERING == "hybrid": nedsiden forankres i IEA WEO NZE,
# oppsiden i historikken (IEA har ikke noe høyprisscenario). None = mangler
# tall; da faller varen tilbake på historisk kalibrering på begge sider.
NZE_OLJE_USD = 25.0      # WEO 2025 NZE 2050 — søketreff, IKKE verifisert
NZE_GASS_USD = None      # IKKE FUNNET — fyll inn fra Annex A
P_NZE = 10               # persentilen NZE skal ligge på

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


NYE = 10                 # ekstrapolerte år 2051-2060
VINDU = 5                # vindu for nedgangsraten, som i arket


def forleng(b, nye=NYE, vindu=VINDU, rjust=0.0):
    """Forlenger basisgrunnlaget forbi 2050, slik arket «Utvidelse 2060» gjør.

    Dette er en SELVSTENDIG implementasjon av arkets logikk, ikke en lesing av
    arkets resultater — det er nettopp poenget når den brukes til å verifisere
    Excel-formlene. Volumer, totalbaner og kostnader føres videre med den
    geometriske raten over de siste `vindu` årene (pluss et påslag `rjust` i
    prosentpoeng); prisene holdes flate; statsandelen settes til snittet over
    samme vindu.

    Returnerer et dict med samme nøkler som les_basis, men bare halen.
    """
    v = vindu
    rate = lambda a: (a[-1] / a[-1 - v]) ** (1 / v) - 1 + rjust
    steg = np.arange(1, nye + 1)
    ut = {k: b[k][-1] * (1 + rate(b[k])) ** steg
          for k in ("volO", "volG", "volN", "cost")}
    # fh/fl er forholdstall; rekonstruer totalbanene, forleng dem, del på nytt
    tot = b["volO"] + b["volG"] + b["volN"]
    totH_e = (b["fh"] * tot)[-1] * (1 + rate(b["fh"] * tot)) ** steg
    totL_e = (b["fl"] * tot)[-1] * (1 + rate(b["fl"] * tot)) ** steg
    tot_e = ut["volO"] + ut["volG"] + ut["volN"]
    ut["fh"], ut["fl"] = totH_e / tot_e, totL_e / tot_e
    for k in ("pO", "pG", "pN"):
        ut[k] = np.repeat(b[k][-1], nye)
    ut["andel"] = np.repeat(b["andel"][-v:].mean(), nye)
    return ut


def kjed(b, e):
    """Kjeder basisgrunnlaget 2026-2050 med halen fra `forleng`."""
    return {k: (np.concatenate([b[k], e[k]]) if k in e else b[k])
            for k in b if k != "par"}


def sigmaer(b):
    """(olje_ned, olje_opp, gass_ned, gass_opp) etter valgt kalibrering."""
    if KALIBRERING == "manuell":
        return SIGMA_OLJE_NED, SIGMA_OLJE_OPP, SIGMA_GASS_NED, SIGMA_GASS_OPP
    if KALIBRERING not in ("historisk", "hybrid"):
        raise ValueError(f"ukjent KALIBRERING: {KALIBRERING!r}")
    # sigma = ln(persentilforhold) / z_p for en medianforankret lognormal
    zp = _z(P_KANT / 100.0)
    p = b["par"]
    s = [-np.log(p["k_olje_lav"]) / zp, np.log(p["k_olje_hoy"]) / zp,
         -np.log(p["k_gass_lav"]) / zp, np.log(p["k_gass_hoy"]) / zp]
    if KALIBRERING == "hybrid":
        # Bytt ut NEDSIDEN med den som treffer NZE i P_NZE. Oppsiden står, siden
        # IEA-scenariene ikke spenner høyprisverdener. Mangler et NZE-tall,
        # beholdes den historiske nedsiden for den varen.
        znze = _z(P_NZE / 100.0)
        for i, (mal, basis) in enumerate(((NZE_OLJE_USD, BASIS_OLJE_USD),
                                          (NZE_GASS_USD, BASIS_GASS_USD))):
            if mal is not None:
                s[2 * i] = np.log(mal / basis) / znze
    return tuple(s)


def _middel_splitt(s_ned, s_opp):
    """E[splitt-lognormal] i lukket form.

    Med ∫_a^b e^{sz}φ(z)dz = e^{s²/2}[Φ(b−s) − Φ(a−s)] blir
        E = e^{σ_ned²/2}·Φ(−σ_ned) + e^{σ_opp²/2}·Φ(σ_opp).
    Symmetrisk (σ_ned = σ_opp = σ) reduseres dette til e^{σ²/2}, som er den
    Jensen-korreksjonen Excel-motoren bruker.
    """
    cdf = NormalDist().cdf
    return (np.exp(s_ned ** 2 / 2) * cdf(-s_ned)
            + np.exp(s_opp ** 2 / 2) * cdf(s_opp))


def _faktor(z, s_ned, s_opp, median_anchor):
    """Splitt-lognormal faktor. Uten medianforankring trekkes middelet til 1.

    Middelet deles på den EKSAKTE forventningen, ikke på utvalgsgjennomsnittet,
    slik at Python og Excel-motoren gir identiske tall på samme trekk.
    """
    f = np.exp(np.where(z < 0, s_ned, s_opp) * z)
    return f if median_anchor else f / _middel_splitt(s_ned, s_opp)


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


DISC = np.arange(1, 26)


def basisbane(b):
    """Basis-SNCF per år (mrd.) — NB26/APS, uten usikkerhet."""
    return (b["andel"] * (b["volO"] * b["pO"] + b["volN"] * b["pN"]
            + b["volG"] * b["pG"] - b["cost"]) / 1000)


def kjor(b, median_anchor=None, kalibrering=None):
    """Én kjøring. Returnerer nøkkeltall som dict, uten å skrive ut."""
    global MEDIAN_ANCHOR, KALIBRERING
    if median_anchor is not None:
        MEDIAN_ANCHOR = median_anchor
    if kalibrering is not None:
        KALIBRERING = kalibrering
    s = sigmaer(b)
    sncf, oilfac, gasfac = simuler(b)
    cum = sncf.sum(axis=1)
    npv3 = (sncf / 1.03 ** DISC).sum(axis=1)
    q = lambda a, p: np.percentile(a, p)
    kv = lambda a, s_: (q(a, 10) * s_, q(a, 50) * s_, q(a, 90) * s_, a.mean() * s_)
    return dict(
        forankring="Median" if MEDIAN_ANCHOR else "Forventning",
        kalibrering=KALIBRERING, sigma=s,
        olje=kv(oilfac, BASIS_OLJE_USD), gass=kv(gasfac, BASIS_GASS_USD),
        kum=(q(cum, 10), q(cum, 50), q(cum, 90), cum.mean()),
        npv3=(q(npv3, 10), q(npv3, 50), q(npv3, 90), npv3.mean()),
        sum_aarsmedian=np.percentile(sncf, 50, axis=0).sum(),
        neg=(sncf < 0).mean() * 100)


def _rad(navn, t, d=0, bredde=34):
    return navn + f"{t[0]:.{d}f} / {t[1]:.{d}f} / {t[2]:.{d}f} / {t[3]:.{d}f}".ljust(bredde)


if __name__ == "__main__":
    b = les_basis()
    bb = basisbane(b)
    bc, bn = bb.sum(), (bb / 1.03 ** DISC).sum()
    print(f"BASIS (NB26 / deck slide 5 / IEA WEO APS): kumulativ {bc:.0f} mrd. | "
          f"NPV 3 pst. {bn:.0f} mrd.")
    print(f"Gulv: {SUPPLY_FLOOR} | korrelasjon olje/gass: {RHO} | N = {N:_}\n")

    # Begge forankringer vises, etter brukerens beslutning 02.09.2026.
    for kal in ("historisk", "hybrid"):
        res = [kjor(b, median_anchor=ma, kalibrering=kal) for ma in (True, False)]
        s = res[0]["sigma"]
        print("=" * 78)
        print(f"KALIBRERING: {kal.upper()}   sigma olje ned/opp "
              f"{s[0]:.3f}/{s[1]:.3f} | gass ned/opp {s[2]:.3f}/{s[3]:.3f}")
        print("=" * 78)
        print(f"{'':<22}{'MEDIANFORANKRING (hovedspor)':<36}"
              f"{'FORVENTNINGSFORANKRING (følsomhet)'}")
        print(f"{'':<22}{'P10 / P50 / P90 / middel':<36}{'P10 / P50 / P90 / middel'}")
        print(_rad(f"{'Oljepris USD/fat':<22}", res[0]["olje"])
              + _rad("", res[1]["olje"]))
        print(_rad(f"{'Gasspris USD/MMBtu':<22}", res[0]["gass"], 1)
              + _rad("", res[1]["gass"], 1))
        print(_rad(f"{'Kumulativ mrd.':<22}", res[0]["kum"])
              + _rad("", res[1]["kum"]))
        print(_rad(f"{'NPV 3 pst. mrd.':<22}", res[0]["npv3"])
              + _rad("", res[1]["npv3"]))
        for navn, nokkel, fmt in (("P50 vs basis", "kum", lambda r: f"{100*(r['kum'][1]/bc-1):+.1f} pst."),
                                  ("Middel vs basis", "kum", lambda r: f"{100*(r['kum'][3]/bc-1):+.1f} pst."),
                                  ("Sum årsmedianer", "sum_aarsmedian", lambda r: f"{r['sum_aarsmedian']:.0f} mrd."),
                                  ("Negative årsverdier", "neg", lambda r: f"{r['neg']:.1f} pst.")):
            print(f"{navn:<22}{fmt(res[0]):<36}{fmt(res[1])}")
        print()
