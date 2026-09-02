# -*- coding: utf-8 -*-
"""
PROTOTYPE — reformulert usikkerhetsmodell for SNCF (statens netto kontantstrøm
til SPU). IKKE integrert i arbeidsboken ennå; kjøres frittstående i Python.

Ideen (avklart med brukeren): i stedet for en 3x3 av vilkårlige prisskift,
kjør ÉN Monte Carlo på basisproduksjon der PERSENTILENE SELV ER SCENARIENE:
P90 = høy prognosert CF, P50 = median, P10 = lav.

Forankring i kilder (den offisielle presentasjonen "Statens petroleumsformue
til ekspertrådet for SPU", 19.03.2026 — ligger på origin/main):
- Basis-priser = deck slide 5 / IEA WEO APS: olje -> 70 USD/fat; gass 6,6
  (2030) -> 5,7 (2040+) USD/MMBtu. Verifisert at modellens pO/pG-baner
  stemmer eksakt med dette.
- Basis-produksjon + høy/lav = SDs mulighetsbilder (deck slide 10).
- Balansepriser (deck slide 14): norske prosjekter ~20-45 USD/fat før skatt
  (nyere ~30). Dette er den empiriske tilbudsrespons-terskelen.
- Pris-usikkerhet forankres i IEA WEO-scenarier: P90 ~ STEPS/Current Policies
  (høy etterspørsel), P10 ~ NZE (rask avkarbonisering). APS = basis.

Modellstruktur:
- Persistente REGIME-trekk (ett per simulering), som speiler "høybane/lavbane":
  pris = basis * lognormal faktor (persistent hele perioden), volum = triangulær
  interpolasjon lav/basis/høy (persistent). Dette matcher brukerens mentale
  modell (vedvarende høy-/lavregimer), ikke år-til-år-støy.
- Tilbudsrespons: feltets årlige netto gulves ved 0 (ingen tapsproduksjon),
  forankret i balanseprisene. Fjerner de meningsløse negative tallene.

ÅPENT SPØRSMÅL (viktigst — se HANDOFF.md):
  Brukeren mener P50 bør = NB26-basis. Med FORVENTNINGSforankring (E[pris]=NB26)
  blir medianen LAVERE enn basis (lognormal skjevhet: median = exp(-0,5*sigma^2)
  < mean = 1). Med MEDIANforankring blir P50 = basis, men middelet havner OVER
  basis. Bryteren MEDIAN_ANCHOR under lar deg teste begge. Hvilken som er riktig
  avhenger av om NB26 tolkes som forventning eller median — må avklares.

Kjøring:  python3 mc_reformulert.py
Krever:   numpy, openpyxl
"""
import numpy as np
from openpyxl import load_workbook

FIL = "Kontantstromsmodell_petroleum.xlsx"
N = 10_000
SEED = 2026

# ----- Kalibrering (justerbar — foreløpige verdier) -----
SIGMA_OLJE = 0.35      # log-std for persistent oljeprisregime (P90~100, P10~41 USD)
SIGMA_GASS = 0.45      # log-std for persistent gassprisregime
RHO = 0.60             # korrelasjon olje/gass-regime
MEDIAN_ANCHOR = False  # False: E[pris]=basis (median<basis). True: median[pris]=basis (mean>basis)
SUPPLY_FLOOR = True     # balansepris-gulv: ingen tapsproduksjon (feltnetto >= 0)
BBL, FX = 6.2898, 10.5  # fat/Sm3, NOK/USD (for prisimplikasjoner i USD)


def les_basis():
    fu = load_workbook(FIL, data_only=True)["Forutsetninger"]
    col = lambda L: np.array([fu[f"{L}{18+i}"].value for i in range(25)])
    volO, volG, volN = col("B"), col("C"), col("D")
    totH, totL = col("F"), col("G")
    pO, pG, pN, cost, snks = col("J"), col("K"), col("L"), col("M"), col("N")
    tot = volO + volG + volN
    fh, fl = totH / tot, totL / tot
    andel = snks / (volO * pO + volG * pG + volN * pN - cost)
    return dict(volO=volO, volG=volG, volN=volN, fh=fh, fl=fl,
                pO=pO, pG=pG, pN=pN, cost=cost, andel=andel)


def simuler(b):
    rng = np.random.default_rng(SEED)
    # Persistente prisregimer (lognormal faktor, ett trekk per sim)
    L = np.linalg.cholesky([[1, RHO], [RHO, 1]])
    z = rng.standard_normal((N, 2)) @ L.T
    drift_o = 0.0 if MEDIAN_ANCHOR else -0.5 * SIGMA_OLJE ** 2
    drift_g = 0.0 if MEDIAN_ANCHOR else -0.5 * SIGMA_GASS ** 2
    oilfac = np.exp(SIGMA_OLJE * z[:, 0] + drift_o)[:, None]
    gasfac = np.exp(SIGMA_GASS * z[:, 1] + drift_g)[:, None]
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
    sncf, oilfac, gasfac = simuler(b)
    disc = np.arange(1, 26)
    cum = sncf.sum(axis=1)
    npv3 = (sncf / 1.03 ** disc).sum(axis=1)
    basis_cum = (b["andel"] * (b["volO"] * b["pO"] + b["volN"] * b["pN"]
                 + b["volG"] * b["pG"] - b["cost"]) / 1000).sum()
    p = lambda a, q: np.percentile(a, q)
    print(f"Forankring: {'MEDIAN (P50=basis)' if MEDIAN_ANCHOR else 'FORVENTNING (E=basis)'}"
          f" | gulv: {SUPPLY_FLOOR} | sigma olje/gass {SIGMA_OLJE}/{SIGMA_GASS}")
    print(f"Impliert oljepris USD/fat (2035+): P10 {68*p(oilfac,10):.0f} / "
          f"P50 {68*p(oilfac,50):.0f} / P90 {68*p(oilfac,90):.0f}")
    print(f"Impliert gasspris USD/MMBtu (2040+): P10 {5.7*p(gasfac,10):.1f} / "
          f"P50 {5.7*p(gasfac,50):.1f} / P90 {5.7*p(gasfac,90):.1f}")
    print(f"Kumulativ til fondet (mrd.): P10 {p(cum,10):.0f} / P50 {p(cum,50):.0f} / "
          f"P90 {p(cum,90):.0f} / middel {cum.mean():.0f} (basis {basis_cum:.0f})")
    print(f"NPV 3 pst. (mrd.):           P10 {p(npv3,10):.0f} / P50 {p(npv3,50):.0f} / "
          f"P90 {p(npv3,90):.0f} / middel {npv3.mean():.0f}")
    print(f"Andel negative årsverdier: {(sncf<0).mean()*100:.1f}%")
