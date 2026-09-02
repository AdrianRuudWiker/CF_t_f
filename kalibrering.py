# -*- coding: utf-8 -*-
"""
Kalibrering av prisusikkerheten i den reformulerte SNCF-modellen mot
IEA WEO-scenarier.

Ideen fra HANDOFF.md er at viftens ytterkanter skal være forankret i noe
autoritativt: P90 ~ IEA WEO STEPS/Current Policies (høy etterspørsel etter
fossil energi), P50 = basis = IEA WEO APS (= deck slide 5), P10 ~ IEA WEO NZE
(rask avkarbonisering).

Modulen gjør to ting:

1. `sigma_fra_mal` løser den inverse kalibreringen. Med MEDIANforankring er
   prisfaktoren en lognormal med median 1, altså pris_q = basis * exp(sigma*z_q)
   der z_q er standardnormalkvantilet. Da er

       sigma = ln(mål / basis) / z_q

   Dette gir ETT sigma per side av fordelingen. Er de to sidene ulike, kan en
   symmetrisk lognormal ikke treffe begge målene samtidig — se `rapport()`.

2. `SPLITT-LOGNORMAL`: når sidene er ulike (og det er de, kraftig, for IEA-
   scenariene) brukes en todelt lognormal med eget sigma opp og ned:

       faktor = exp(sigma_ned * z)  for z < 0
       faktor = exp(sigma_opp * z)  for z >= 0

   Medianen er eksakt 1 uansett sigma-ene, så medianforankringen er bevart.
   Dette er den eneste formen som kan treffe STEPS og NZE samtidig OG holde
   P50 = basis. (Med forventningsforankring må driften løses ut samtidig, og
   medianen flytter seg — nok en grunn til å velge medianforankring.)

MÅLTALLENE ER IKKE VERIFISERT. Nettadgangen i containeren blokkerer iea.org,
iea.blob.core.windows.net, regjeringen.no og alt annet utenom søk, så
Annex A-tabellen i WEO kunne ikke hentes. Oljetallene under kommer fra
søketreff på WEO 2025 og må bekreftes mot Annex A før bruk. Gasstallene er
IKKE funnet i det hele tatt og står som None. Fyll inn `MAL` og kjør på nytt.

Kjøring:  python3 kalibrering.py
"""
import numpy as np
from statistics import NormalDist

norm_ppf = NormalDist().inv_cdf  # standardnormalens kvantilfunksjon (stdlib)

# --- Basis (deck slide 5 / IEA WEO APS, faste 2026-kroner) -------------------
BASIS_OLJE = 70.0   # USD/fat fra 2035
BASIS_GASS = 5.7    # USD/MMBtu fra 2040

# --- Måltall fra IEA WEO ----------------------------------------------------
# kilde: se docstring. None = ikke funnet, må fylles inn av bruker.
MAL = {
    "olje": {
        "hoy":  {"verdi": 76.0, "scenario": "WEO 2025 STEPS 2050",
                 "kilde": "søketreff, IKKE verifisert mot Annex A"},
        "lav":  {"verdi": 25.0, "scenario": "WEO 2025 NZE 2050",
                 "kilde": "søketreff, IKKE verifisert mot Annex A"},
    },
    "gass": {
        "hoy":  {"verdi": None, "scenario": "WEO STEPS, gass EU 2050",
                 "kilde": "IKKE FUNNET — fyll inn"},
        "lav":  {"verdi": None, "scenario": "WEO NZE, gass EU 2050",
                 "kilde": "IKKE FUNNET — fyll inn"},
    },
}

# Hvilke persentiler ytterkantene skal representere.
P_HOY, P_LAV = 90, 10


def sigma_fra_mal(basis, mal, persentil):
    """Sigma i en medianforankret lognormal som treffer `mal` i `persentil`."""
    if mal is None:
        return None
    return np.log(mal / basis) / norm_ppf(persentil / 100.0)


def fan(basis, sigma_ned, sigma_opp, persentiler=(5, 10, 25, 50, 75, 90, 95)):
    """Prisbane-persentiler for en todelt (splitt-)lognormal med median 1."""
    ut = {}
    for q in persentiler:
        z = norm_ppf(q / 100.0)
        s = sigma_ned if z < 0 else sigma_opp
        ut[q] = basis * np.exp(s * z)
    return ut


def middel_splitt(sigma_ned, sigma_opp, n=2_000_000, seed=2026):
    """Forventningsverdi av splitt-lognormalen (numerisk)."""
    z = np.random.default_rng(seed).standard_normal(n)
    s = np.where(z < 0, sigma_ned, sigma_opp)
    return float(np.exp(s * z).mean())


def rapport():
    print("=" * 78)
    print("KALIBRERING AV PRISUSIKKERHET MOT IEA WEO-SCENARIER")
    print("=" * 78)
    print(f"Ytterkanter tolkes som P{P_LAV} og P{P_HOY}. Medianforankring:")
    print("median[pris] = basis, som gir P50 = deck slide 5 / APS eksakt.\n")

    for vare, basis, enhet in (("olje", BASIS_OLJE, "USD/fat"),
                               ("gass", BASIS_GASS, "USD/MMBtu")):
        m = MAL[vare]
        s_opp = sigma_fra_mal(basis, m["hoy"]["verdi"], P_HOY)
        s_ned = sigma_fra_mal(basis, m["lav"]["verdi"], P_LAV)
        print(f"--- {vare.upper()} (basis {basis:g} {enhet}) ---")
        for side, s, p in (("høy", s_opp, P_HOY), ("lav", s_ned, P_LAV)):
            d = m["hoy" if side == "høy" else "lav"]
            if d["verdi"] is None:
                print(f"  P{p:<2} mål: — ({d['scenario']}: {d['kilde']})")
            else:
                print(f"  P{p:<2} mål: {d['verdi']:g} {enhet}  → sigma "
                      f"{s:.3f}   [{d['scenario']}; {d['kilde']}]")
        if s_opp is not None and s_ned is not None:
            print(f"  Symmetrikrav: sigma_opp {s_opp:.3f} vs sigma_ned "
                  f"{s_ned:.3f} — forhold {s_ned / s_opp:.1f}x.")
            if s_ned / s_opp > 1.5 or s_opp / s_ned > 1.5:
                print("  => ÉN symmetrisk lognormal kan IKKE treffe begge. "
                      "Bruk splitt-lognormal.")
                sym_hvis_ned = fan(basis, s_ned, s_ned)
                sym_hvis_opp = fan(basis, s_opp, s_opp)
                print(f"     Symmetrisk med sigma={s_ned:.3f} (treffer lav): "
                      f"P{P_HOY} blir {sym_hvis_ned[P_HOY]:.1f} {enhet} "
                      f"(mål {m['hoy']['verdi']:g}).")
                print(f"     Symmetrisk med sigma={s_opp:.3f} (treffer høy): "
                      f"P{P_LAV} blir {sym_hvis_opp[P_LAV]:.1f} {enhet} "
                      f"(mål {m['lav']['verdi']:g}).")
            f = fan(basis, s_ned, s_opp)
            b = " / ".join(f"P{q} {f[q]:.1f}" for q in sorted(f))
            print(f"  Splitt-lognormal treffer begge. Vifte ({enhet}): {b}")
            print(f"  Impliert forventning: "
                  f"{basis * middel_splitt(s_ned, s_opp):.1f} {enhet} "
                  f"({100 * (middel_splitt(s_ned, s_opp) - 1):+.0f} pst. mot basis)")
        print()


def plassering():
    """Hvor i den historisk kalibrerte viften faller IEA-scenariene?

    Den motsatte spørsmålsstillingen av `rapport()`: i stedet for å tvinge
    sigma til å treffe IEA, holdes sigma fast på den historiske kalibreringen
    (Forutsetninger!B4:B7) og vi leser av hvilken persentil IEA-scenariene
    havner på. Det gjør uenigheten mellom kildene eksplisitt og målbar.
    """
    import mc_reformulert as mc

    b = mc.les_basis()
    mc.KALIBRERING = "historisk"
    s_on, s_oo, s_gn, s_go = mc.sigmaer(b)
    cdf = NormalDist().cdf
    print("=" * 78)
    print("PLASSERING AV IEA-SCENARIENE I DEN HISTORISK KALIBRERTE VIFTEN")
    print("=" * 78)
    for vare, basis, enhet, s_ned, s_opp in (
            ("olje", mc.BASIS_OLJE_USD, "USD/fat", s_on, s_oo),
            ("gass", mc.BASIS_GASS_USD, "USD/MMBtu", s_gn, s_go)):
        print(f"--- {vare.upper()} (basis {basis:g} {enhet}, "
              f"sigma ned/opp {s_ned:.3f}/{s_opp:.3f}) ---")
        for side in ("hoy", "lav"):
            d = MAL[vare][side]
            if d["verdi"] is None:
                print(f"  {d['scenario']}: mål ikke funnet — fyll inn MAL")
                continue
            lf = np.log(d["verdi"] / basis)
            s = s_opp if lf >= 0 else s_ned
            q = 100 * cdf(lf / s)
            print(f"  {d['scenario']} = {d['verdi']:g} {enhet} → persentil "
                  f"P{q:.1f}  [{d['kilde']}]")
        print()


if __name__ == "__main__":
    rapport()
    plassering()
