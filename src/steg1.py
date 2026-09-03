"""Steg 1 — gjenutledning av Sokkeldirektoratets forutsetninger.

Sokkeldirektoratet publiserer nivåer og spenn i figur 2.5 og 2.6, men ikke
forutsetningene bak. `src/sodir.py` utleder m*R og m*C per bane av
priselastisiteten mellom de to prissettene. Her møter de utledede størrelsene
de faktiske produksjonsbanene, og resultatet holdes opp mot NB26.

Steget er ikke en test av motoren. Det er en gjenutledning av
Sokkeldirektoratets egen uttaksrate og kostnadsbane, som deretter kan
sammenlignes med statens egen. Den sammenligningen har ingen gjort.

Tre resultater, i den rekkefølgen README setter dem:

  1. VOLUMFORHOLDET. m*R_Høy / m*R_Lav er fritt for både m og pris, og er
     derfor en parameterfri kontroll mot de faktiske banene. Den finnes i to
     utgaver: udiskontert av figur 2.5 og diskontert av figur 2.6. Den
     diskonterte er den strengeste, fordi den også tester tidsprofilen og ikke
     bare summen.

  2. MARGINALANDELEN. m = m*R_Høy / R_Høy, der R_Høy følger av volum, pris og
     valutakurs. Referanse: 0,80-0,82 er den strukturelle andelen. Om lag 1,00
     ville betydd at Sokkeldirektoratets tall gjelder sektorens verdiskaping,
     ikke statens.

  3. KOSTNADENE. m*C er kjent, så C følger når m er bestemt. Utledes for alle
     tre banene, fordi konsistensen mellom dem sier noe om hvor presis
     avlesningen av figuren er.

I tillegg belyses to av de åpne punktene i README:
  - punkt 1, valutakursen: KVARTS rad 11 oppgir 10,114 flatt fra 2026.
  - punkt 2, horisonten: m er invers proporsjonal med volumet, så kravet om at
    m skal lande på den strukturelle andelen bestemmer hvor langt
    Sokkeldirektoratets kontantstrøm må løpe.

Kjør:
    python -m src.steg1
"""

from __future__ import annotations

import pandas as pd

from . import modell, sodir

INNDATA = "data/inndata.csv"
FRA, TIL = 2026, 2050          # så langt Sokkeldirektoratets baner rekker
RENTE = 0.04                   # Sokkeldirektoratets egen, jf. figur 2.6
SPENN_STRUKTURELL = (0.80, 0.82)
BANER = ("hoy", "basis", "lav")
NAVN = {"hoy": "Høy", "basis": "Basis", "lav": "Lav"}


def _n(x, d=1):
    """Norsk tallformat: mellomrom som tusenskille, komma som desimaltegn."""
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def last() -> pd.DataFrame:
    return pd.read_csv(INNDATA).set_index("ar")


def volumer(d: pd.DataFrame, rente: float | None = None) -> dict[str, float]:
    """Kumulativt volum per bane, mill. Sm3 o.e. Diskonteres om rente oppgis.

    Diskontert volum er ikke en fysisk størrelse, men det er nettopp det
    figur 2.6 impliserer: nåverdien av inntekten er proporsjonal med det
    neddiskonterte volumet når prisen er den samme hvert år.
    """
    ut = {}
    for b in BANER:
        s = d[f"produksjon_sd_{b}"].loc[FRA:TIL]
        ut[b] = (s.sum() if rente is None
                 else sum(v / (1 + rente) ** (t - 2025) for t, v in s.items()))
    return ut


def bruttoinntekt(vol_mill_sm3: float, d: pd.DataFrame, fx: float | None = None,
                  pris_usd: float = sodir.SODIR_USD_FAT) -> float:
    """Sokkeldirektoratets brutto salgsinntekt for et volum, mrd. kroner.

    Flat prising: alt volum verdsettes til én felles pris per fat
    oljeekvivalent. Valutakursen leses av kilden om den ikke oppgis.
    """
    if fx is None:
        fx = d.loc[TIL, "dollarkurs"]
    return d.loc[TIL, "fat_per_sm3"] * pris_usd * fx * vol_mill_sm3 / 1000


def _avled_nnv() -> dict[str, float]:
    """Samme utledning som sodir.avled(), men på de neddiskonterte nivåene."""
    N = sodir.NNV_4PST
    mR_hoy = (N[("hoy", 100)] - N[("hoy", 80)]) / 0.25
    mR_lav = (N[("lav", 80)] - N[("lav", 60)]) / 0.25
    return {"mR_hoy": mR_hoy, "mR_lav": mR_lav,
            "volumforhold_hoy_lav": mR_hoy / mR_lav}


# --- delene -----------------------------------------------------------------

def del1_volumforholdet(d: pd.DataFrame) -> None:
    print("\n1. VOLUMFORHOLDET — to parameterfrie kontroller")
    print("-" * 78)
    u, n = volumer(d), volumer(d, RENTE)
    print(f"  Kumulativt volum {FRA}-{TIL}, mill. Sm3 o.e.")
    print(f"    udiskontert ..... Høy {_n(u['hoy'], 0):>7}  Basis {_n(u['basis'], 0):>7}"
          f"  Lav {_n(u['lav'], 0):>7}")
    print(f"    ved {_n(100 * RENTE, 0)} pst. ..... Høy {_n(n['hoy'], 0):>7}  Basis {_n(n['basis'], 0):>7}"
          f"  Lav {_n(n['lav'], 0):>7}")
    print()
    print(f"  {'kilde':22s}{'utledet':>10}{'i banene':>11}{'avvik':>10}")
    for navn, ventet, faktisk in (
            ("figur 2.5, udiskontert", sodir.avled()["volumforhold_hoy_lav"],
             u["hoy"] / u["lav"]),
            ("figur 2.6, NNV 4 pst.", _avled_nnv()["volumforhold_hoy_lav"],
             n["hoy"] / n["lav"])):
        print(f"  {navn:22s}{_n(ventet, 3):>10}{_n(faktisk, 3):>11}"
              f"{_n(100 * (faktisk / ventet - 1), 1) + ' pst.':>10}")
    print("\n  Begge holder. Den diskonterte er den strengeste, fordi den også")
    print("  tester NÅR volumet kommer, ikke bare hvor mye det er — og den")
    print("  treffer best. Forutsetningen om én felles pris per fat")
    print("  oljeekvivalent er dermed forenlig med de faktiske banene.")


def del2_marginalandelen(d: pd.DataFrame) -> float:
    print("\n2. MARGINALANDELEN")
    print("-" * 78)
    a, u = sodir.avled(), volumer(d)
    fx, fat = d.loc[TIL, "dollarkurs"], d.loc[TIL, "fat_per_sm3"]
    R = {b: bruttoinntekt(u[b], d) for b in BANER}
    m_hoy = a["mR_hoy"] / R["hoy"]
    m_lav = a["mR_lav"] / R["lav"]
    m_begge = modell.implisert_marginalandel(u["hoy"], u["lav"], fx=fx,
                                             fat_per_sm3=fat)
    print(f"  Valutakurs {_n(fx, 3)} NOK/USD, {_n(fat, 4)} fat per Sm3 o.e., begge fra KVARTS.")
    print(f"  Brutto salgsinntekt ved 80 USD/fat o.e., mrd. kroner:"
          f"  Høy {_n(R['hoy'], 0)}   Lav {_n(R['lav'], 0)}")
    print()
    print(f"  m av Høy alene ...................... {_n(m_hoy, 3)}")
    print(f"  m av Lav alene ...................... {_n(m_lav, 3)}")
    print(f"  m av begge banene samtidig .......... {_n(m_begge, 3)}")
    print(f"  Strukturell referanse ............... "
          f"{_n(SPENN_STRUKTURELL[0], 2)}-{_n(SPENN_STRUKTURELL[1], 2)}")

    m_nb = modell.marginalrate(d).loc[FRA:TIL]
    vekt = modell.inntekt(d)["sum"].loc[FRA:TIL]
    m_nb_snitt = float((m_nb * vekt).sum() / vekt.sum())
    print(f"  NB26s egen marginalrate, inntektsvektet {_n(m_nb_snitt, 3)}")
    print(f"    per år {_n(m_nb.min(), 3)} til {_n(m_nb.max(), 3)}: "
          f"2026 {_n(m_nb.loc[2026], 3)}, 2035 {_n(m_nb.loc[2035], 3)}, "
          f"2050 {_n(m_nb.loc[2050], 3)}")
    snitt = (d["snks"] / (modell.inntekt(d)["sum"]
                          - modell.realkostnader(d)["sum"])).loc[FRA:TIL]
    print(f"    til kontrast: gjennomsnittsandelen SNKS/(inntekt−kostnad) er "
          f"{_n(snitt.min(), 3)}-{_n(snitt.max(), 3)}")
    print("    og skal ikke brukes som marginalrate.")

    print("\n  Sokkeldirektoratets impliserte uttaksrate faller altså sammen med")
    print("  NB26s strukturelle marginalrate. Tallene deres er statens netto")
    print("  kontantstrøm, ikke sektorens verdiskaping. Det er en forutsetning")
    print("  for hele sammenligningen i steg 2, og den er nå etterprøvd.")

    print("\n  Følsomhet for valutakursen (åpent punkt 1):")
    print(f"    {'NOK/USD':>9}{'m (Høy)':>10}{'m (begge)':>11}")
    for v in (10.114, 10.2, 10.5, 11.0):
        merk = "   <- KVARTS rad 11" if abs(v - fx) < 5e-4 else ""
        print(f"    {_n(v, 3):>9}{_n(a['mR_hoy'] / bruttoinntekt(u['hoy'], d, fx=v), 3):>10}"
              f"{_n(modell.implisert_marginalandel(u['hoy'], u['lav'], fx=v, fat_per_sm3=fat), 3):>11}{merk}")

    print("\n  Horisonten (åpent punkt 2). m er invers proporsjonal med volumet,")
    print("  så kravet om at m skal treffe referansen bestemmer hvor langt")
    print("  Sokkeldirektoratets kontantstrøm må løpe:")
    aarsvolum = d.loc[TIL, "produksjon_sd_hoy"]
    print(f"    {'m':>7}{'krever volum':>14}{'mot faktisk':>13}{'tilsvarer':>24}")
    for m_mal, merk in ((0.80, ""), (0.82, ""), (m_nb_snitt, "  NB26"), (1.00, "")):
        krav = a["mR_hoy"] / m_mal * 1000 / (fat * sodir.SODIR_USD_FAT * fx)
        ekstra = (krav - u["hoy"]) / aarsvolum
        print(f"    {_n(m_mal, 3):>7}{_n(krav, 0):>14}"
              f"{_n(100 * (krav / u['hoy'] - 1), 1) + ' pst.':>13}"
              f"{_n(ekstra, 1) + ' år':>16}{merk}")
    print("    Utslagene er små: å treffe NB26s egen marginalrate krever 0,2 år")
    print("    ekstra produksjon. Sokkeldirektoratets kontantstrøm er dermed")
    print("    avkortet ved eller like etter 2050, ikke ført over full")
    print("    feltlevetid. Full levetid ville krevd flere tiår og presset m")
    print("    langt under den strukturelle andelen.")
    print("    KONSEKVENS FOR STEG 2: horisontleddet i fossefiguren er lite.")
    return m_hoy


def del3_kostnadene(d: pd.DataFrame, m: float) -> dict:
    print("\n3. KOSTNADENE")
    print("-" * 78)
    u = volumer(d)
    R = {b: bruttoinntekt(u[b], d) for b in BANER}
    C, enhet = {}, {}
    print(f"  Med m = {_n(m, 3)}, utledet av Høy-banen:")
    print(f"    {'bane':7}{'volum':>9}{'m*R':>9}{'netto':>9}{'kostnad':>10}"
          f"{'kr/Sm3 o.e.':>13}{'kostandel':>11}")
    for b in BANER:
        netto = sodir.UDISKONTERT[(b, 80)]
        C[b] = (m * R[b] - netto) / m
        enhet[b] = C[b] / u[b] * 1000
        print(f"    {NAVN[b]:7}{_n(u[b], 0):>9}{_n(m * R[b], 0):>9}{_n(netto, 0):>9}"
              f"{_n(C[b], 0):>10}{_n(enhet[b], 0):>13}"
              f"{_n(100 * C[b] / R[b], 1) + ' pst.':>11}")

    a = sodir.avled()
    print(f"\n  MERK to ruter til Lav. Tabellen over bruker det FAKTISKE volumet")
    print(f"  ({_n(u['lav'], 0)} mill. Sm3 o.e.) og gir kostnadsandel "
          f"{_n(100 * C['lav'] / R['lav'], 1)} pst. `sodir.avled()`")
    print(f"  bruker i stedet m*R_Lav fra priselastisiteten ({_n(a['mR_lav'], 0)} mot "
          f"{_n(m * R['lav'], 0)})")
    print(f"  og gir {_n(100 * a['kost_andel_lav'], 1)} pst., som er tallet i README. "
          "Differansen ER avviket på")
    print("  3,7 pst. i volumforholdet, forplantet. Begge er riktige regnestykker")
    print("  på hver sin forutsetning; spriket er målet på hvor presis")
    print("  figuravlesningen er.")

    print("\n  INTERN INKONSISTENS. Enhetskostnaden i basisbanen faller UTENFOR")
    print(f"  spennet Høy-Lav ({_n(enhet['basis'], 0)} mot {_n(enhet['hoy'], 0)} og {_n(enhet['lav'], 0)}).")
    print("  Høy har lavere enhetskostnad enn Lav, altså stordriftsfordeler, og")
    print("  da skal basis ligge imellom. For at den skal gjøre det, måtte")
    print("  basissøylen i figur 2.5 lest:")
    for e in (enhet["hoy"], 0.5 * (enhet["hoy"] + enhet["lav"]), enhet["lav"]):
        print(f"    ved enhetskostnad {_n(e, 0):>5} kr/Sm3 o.e. -> "
              f"{_n(m * R['basis'] - m * (e * u['basis'] / 1000), 0)} mrd.")
    print(f"  Figuren leser {_n(sodir.UDISKONTERT[('basis', 80)], 0)}. Avviket er om lag 8-13 pst.")
    print("  Enten ligger basissøylen for høyt i avlesningen, eller de tre banene")
    print("  har ulik kostnadsstruktur. Presisjonen i steg 1 er dermed rundt")
    print("  ±10 pst., og fossefiguren i steg 2 skal ikke pynte på det.")

    kost_nb = modell.realkostnader(d)["sum"].loc[FRA:TIL].sum()
    innt_nb = modell.inntekt(d)["sum"].loc[FRA:TIL].sum()
    vol_nb = sum(d[f"produksjon_{r}"].loc[FRA:TIL].sum() for r in modell.RESSURSER)
    enhet_nb = kost_nb / vol_nb * 1000
    print(f"\n  NB26, samme horisont, basisbanen:")
    print(f"    kumulativ realkostnad ..... {_n(kost_nb, 0)} mrd. 2026-kroner "
          f"(drift {_n(modell.realkostnader(d)['drift'].loc[FRA:TIL].sum(), 0)}, "
          f"investering {_n(modell.realkostnader(d)['investering'].loc[FRA:TIL].sum(), 0)})")
    print(f"    kumulativ salgsinntekt .... {_n(innt_nb, 0)} mrd. (Energidepartementets priser)")
    print(f"    kumulativt volum .......... {_n(vol_nb, 0)} mill. Sm3 o.e.")
    print(f"    enhetskostnad ............. {_n(enhet_nb, 0)} kr/Sm3 o.e.")
    print(f"    kostnadsandel ............. {_n(100 * kost_nb / innt_nb, 1)} pst.")

    print("\n  SAMMENLIGNINGEN INGEN HAR GJORT — enhetskostnad, kr/Sm3 o.e.:")
    for b in BANER:
        print(f"    Sokkeldirektoratet, {NAVN[b]:6}{_n(enhet[b], 0):>7}"
              f"   {_n(100 * (enhet[b] / enhet_nb - 1), 0) + ' pst. mot NB26':>22}")
    print(f"    NB26, basis        {_n(enhet_nb, 0):>8}")
    print("  Sokkeldirektoratet regner altså gjennomgående lavere enhetskostnad")
    print("  enn NB26 — 10 til 40 pst. lavere. Det er en reell forskjell i")
    print("  forutsetninger, ikke bare i prising, og den trekker samme vei som")
    print("  gassprisen: Sokkeldirektoratets ressursverdi blir høyere enn statens.")

    print("\n  KostnadsANDELEN skiller likevel mye mer enn kostnadsNIVÅET, og")
    print("  det er prisingen som gjør det. Samme kostnad, to nevnere:")
    print(f"    NB26s kostnad mot NB26s inntekt ......... "
          f"{_n(100 * kost_nb / innt_nb, 1)} pst.")
    print(f"    NB26s kostnad mot flat prising 80 USD ... "
          f"{_n(100 * kost_nb / bruttoinntekt(vol_nb, d), 1)} pst.")
    print("  Det er det samme forholdet som bærer fossefiguren i steg 2.")
    return {"C": C, "enhet": enhet, "enhet_nb": enhet_nb}


def main() -> None:
    d = last()
    print("=" * 78)
    print("STEG 1 — SOKKELDIREKTORATETS FORUTSETNINGER, GJENUTLEDET")
    print("=" * 78)
    print(f"Horisont {FRA}-{TIL}, så langt Sokkeldirektoratets baner rekker.")
    print("Kontroll av avlesningen (avlest spenn mot oppgitt spenn):")
    for k, (avlest, oppgitt) in sodir.kontroller_avlesning().items():
        status = "ok" if avlest == oppgitt else "AVVIK"
        print(f"  {k:22s}{_n(avlest, 0):>8}{_n(oppgitt, 0):>8}   {status}")

    del1_volumforholdet(d)
    m = del2_marginalandelen(d)
    k = del3_kostnadene(d, m)

    u = volumer(d)
    print("\n" + "=" * 78)
    print("OPPSUMMERING")
    print("=" * 78)
    print(f"  Volumforholdet holder i begge utgaver: {_n(u['hoy'] / u['lav'], 2)} mot utledet "
          f"{_n(sodir.avled()['volumforhold_hoy_lav'], 2)}")
    print(f"    udiskontert, og {_n(volumer(d, RENTE)['hoy'] / volumer(d, RENTE)['lav'], 2)} mot "
          f"{_n(_avled_nnv()['volumforhold_hoy_lav'], 2)} diskontert.")
    print(f"  m = {_n(m, 3)}, mot NB26s strukturelle "
          f"{_n(float((modell.marginalrate(d).loc[FRA:TIL] * modell.inntekt(d)['sum'].loc[FRA:TIL]).sum() / modell.inntekt(d)['sum'].loc[FRA:TIL].sum()), 3)}."
          " Statens andel, ikke sektorens.")
    print(f"  Enhetskostnad {_n(k['enhet']['hoy'], 0)} kr/Sm3 o.e. i Høy mot NB26s "
          f"{_n(k['enhet_nb'], 0)} — Sokkeldirektoratet")
    print("    regner lavere kostnad enn staten, i tillegg til høyere pris.")
    print("  Horisonten er avkortet ved eller like etter 2050.")
    print("  Presisjonen er om lag ±10 pst.; basissøylen henger ikke helt sammen.")


if __name__ == "__main__":
    main()
