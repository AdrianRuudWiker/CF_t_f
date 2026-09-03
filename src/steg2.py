"""Steg 2 — Energidepartementets prisbaner mot Sokkeldirektoratets. LEVERANSEN.

Samme motor som steg 1, men med olje og gass priset hver for seg. Poenget er
en enkelt observasjon: Sokkeldirektoratet verdsetter gjenværende ressurser til
om lag det dobbelte av statens eget anslag, og forskjellen er nesten
utelukkende én forutsetning om gass.

REGNESTYKKET
    Én Sm3 o.e. er 6,29 fat væske, men som gass om lag 37,9 MMBtu. Flat
    prising til 80 USD per fat oljeekvivalent gir derfor 503 USD per Sm3 o.e.
    for ALT volum. Energidepartementets forutsetninger gir 440 USD for olje
    (70 USD/fat) og 216 USD for gass (5,7 USD/MMBtu). Flat prising verdsetter
    altså olje om lag 1,14 ganger høyere og gass 2,33 ganger høyere, målt på
    de langsiktige nivåene.

    Målt over hele perioden og inntektsvektet blir forholdene noe andre —
    om lag 1,19 for olje og 1,90 for gass — fordi Energidepartementets
    gasspris starter høyt og faller, mens oljeprisen stiger til 2035.

BROEN
    Fossefiguren går fra Sokkeldirektoratets 7 500 mrd. kroner ned til NB26s
    3 671. Den bygges i motsatt retning, fra NB26 og opp, fordi motoren er
    forankret der: kalles kontantstrom() uten argumenter, ER resultatet NB26s
    egen bane. Da er hvert ledd et etterprøvbart avvik og ikke en avstemming.

    Alt regnes som NNV med 4 pst., datert 2025. Det er Sokkeldirektoratets
    egen rente i figur 2.6, og samme datering som NB26-tallet.

    VIKTIG FUNN, som endrer bildet fra steg 1: Sokkeldirektoratets tall er
    internt konsistente i NÅVERDI, men ikke udiskontert. Enhetskostnaden som
    Høy- og Lav-banen impliserer, er 1 354 og 1 336 kr/Sm3 o.e. diskontert —
    1,4 pst. fra hverandre. Udiskontert er de 1 397 og 1 731, altså 24 pst.
    fra hverandre. Figur 2.6 er derfor det pålitelige grunnlaget, og
    ±10 pst.-forbeholdet fra steg 1 gjaldt den udiskonterte avlesningen.

    Residualen i broen er om lag 6 pst. og står som eget ledd. Den skal ikke
    fordeles ut på de andre leddene.

FIGURER
    1. Produksjon, tre mulighetsbilder til 2050.
    2. Netto kontantstrøm og nåverdi per bane, med begge prissett.
    3. Fossefiguren. Den bærer vedlegget.

    Figurene følger FINs designprofil, med to bevisste avvik fastsatt av
    prosjektet: Liberation Sans i stedet for Open Sans, og grå bakgrunn
    (#ededee) for dokumentfigurer. Se src/figurer.py.

REGELEN SOM GJELDER GJENNOM HELE
    Pris- og volumusikkerhet ganges aldri sammen. Prisusikkerhet vises på én
    produksjonsbane (steg 3); volumusikkerhet vises som navngitte baner ved
    faste priser (figur 2). Sokkeldirektoratets volumer inneholder allerede et
    lønnsomhetsfilter, så et uavhengig prissjokk lagt oppå dem beskriver en
    verden deres egen metode utelukker.

Kjør:
    python -m src.steg2
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import figurer, modell, sodir, steg1

FRA, TIL = 2026, 2050
TIL_LANG = 2060
RENTE = 0.04
BANER = ("hoy", "basis", "lav")
NAVN = {"hoy": "Høy", "basis": "Basis", "lav": "Lav"}


def _n(x, d=1):
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def nnv(s: pd.Series, fra: int = FRA, til: int = TIL, rente: float = RENTE) -> float:
    """Nåverdi datert 2025 — første beløp i 2026 diskonteres én periode."""
    return sum(s[t] / (1 + rente) ** (t - 2025) for t in range(fra, til + 1)
               if t in s.index and pd.notna(s[t]))


def flat_pris(d: pd.DataFrame) -> float:
    """Sokkeldirektoratets flate pris, kr/Sm3 o.e. Alt volum, samme pris."""
    return (d.loc[TIL, "fat_per_sm3"] * sodir.SODIR_USD_FAT
            * d.loc[TIL, "dollarkurs"])


def flate_priser(d: pd.DataFrame) -> pd.DataFrame:
    f = flat_pris(d)
    return pd.DataFrame({r: pd.Series(f, index=d.index) for r in modell.RESSURSER})


def sd_enhetskostnad(d: pd.DataFrame) -> dict[str, float]:
    """Sokkeldirektoratets impliserte enhetskostnad, kr per diskontert Sm3 o.e.

    Utledes av figur 2.6: m*R følger av priselastisiteten mellom de to
    prissettene, m*C er m*R minus nettonivået, og m av volum, pris og
    valutakurs. Høy og Lav gir to uavhengige anslag; at de er 1,4 pst. fra
    hverandre er den sterkeste indikasjonen på at avlesningen er god.
    """
    N = sodir.NNV_4PST
    mR = {"hoy": (N[("hoy", 100)] - N[("hoy", 80)]) / 0.25,
          "lav": (N[("lav", 80)] - N[("lav", 60)]) / 0.25}
    v = steg1.volumer(d, RENTE)
    R = {b: flat_pris(d) * v[b] / 1000 for b in v}
    ut = {}
    for b in ("hoy", "lav"):
        m = mR[b] / R[b]
        ut[b] = (mR[b] - N[(b, 80)]) / m / v[b] * 1000
        ut[f"m_{b}"] = m
    # Basis interpoleres lineært i diskontert volum mellom Lav og Høy.
    ut["basis"] = ut["lav"] + (v["basis"] - v["lav"]) / (v["hoy"] - v["lav"]) \
        * (ut["hoy"] - ut["lav"])
    return ut


def broen(d: pd.DataFrame) -> pd.Series:
    """Leddene fra NB26s 3 671 opp til Sokkeldirektoratets 7 500.

    Rekkefølgen er valgt slik at de to prisleddene ligger inntil hverandre og
    de små leddene rammer dem inn. Fossefigurer er veiavhengige, så
    rekkefølgen er et valg og oppgis: horisont, volum, pris, kostnad,
    uttaksrate, avlesning.
    """
    p, k, m = modell.realpriser(d), modell.realkostnader(d), modell.marginalrate(d)
    v = {r: d[f"produksjon_{r}"] for r in modell.RESSURSER}
    tot = sum(v.values())
    f_vol = d["produksjon_sd_basis"] / tot          # NB26s volum -> SDs basis
    flat = flat_pris(d)

    # Bruttoledd, før uttaksrate. Prisleddene regnes PÅ SDs volumbane, slik at
    # volumleddet ikke dobbeltelles.
    brutto = {
        "volum": (nnv(((f_vol - 1)) * sum(v[r] * p[r] for r in modell.RESSURSER)
                      / modell.MILL_PER_MRD)
                  - nnv(k["sum"] * (f_vol - 1))),
        "olje": nnv(f_vol * (v["olje"] * (flat - p["olje"])
                             + v["ngl"] * (flat - p["ngl"])) / modell.MILL_PER_MRD),
        "gass": nnv(f_vol * v["gass"] * (flat - p["gass"]) / modell.MILL_PER_MRD),
    }
    e = sd_enhetskostnad(d)
    C_sd = e["basis"] * steg1.volumer(d, RENTE)["basis"] / 1000
    brutto["kostnad"] = nnv(k["sum"] * f_vol) - C_sd

    innt = modell.inntekt(d)["sum"].loc[FRA:TIL]
    m_nb = float((m.loc[FRA:TIL] * innt).sum() / innt.sum())
    m_sd = e["m_hoy"]

    ledd = {"NB26, NNV 4 pst. 2026-2060": nnv(d["snks"], FRA, TIL_LANG),
            "Horisont: 2051-2060 tas ut": -nnv(d["snks"], TIL + 1, TIL_LANG)}
    for navn, nokkel in (("Volum: NB26 → SD basis", "volum"),
                         ("Pris: olje og NGL → 80 USD", "olje"),
                         ("Pris: gass → 80 USD", "gass"),
                         ("Kostnad: NB26 → SD", "kostnad")):
        ledd[navn] = m_nb * brutto[nokkel]
    ledd["Uttaksrate: 0,824 → 0,780"] = (m_sd - m_nb) * sum(brutto.values())
    ledd["Avlesning av figur 2.6"] = (sodir.NNV_4PST[("basis", 80)]
                                      - sum(ledd.values()))
    return pd.Series(ledd)


def kontantstrommer(d: pd.DataFrame) -> dict[tuple[str, str], pd.Series]:
    """SNCF per volumbane og prissett. Nøkkel (bane, prissett)."""
    vb = modell.volumbaner(d)
    flat = flate_priser(d)
    ut = {}
    for b in BANER:
        ut[(b, "ed")] = modell.kontantstrom(d, volum=vb[b])
        ut[(b, "flat")] = modell.kontantstrom(d, priser=flat, volum=vb[b])
    return ut


# --- figurer ----------------------------------------------------------------

def _akser(ax, enhet: str) -> None:
    """FIN-konvensjon: y-akse på begge sider, tickmarks inn, ingen på x-aksen.

    Ligger her og ikke i figurer.py, som README merker som ferdig.
    """
    ax.tick_params(axis="y", direction="in", right=True, labelright=False,
                   length=3, width=0.5)
    ax.tick_params(axis="x", length=0)
    for s in ("left", "bottom"):
        ax.spines[s].set_linewidth(0.5)
        ax.spines[s].set_color("black")
    ax.spines["right"].set_visible(True)
    ax.spines["right"].set_linewidth(0.5)
    ax.spines["right"].set_color("black")
    ax.yaxis.set_major_formatter(
        lambda v, _: f"{v:,.0f}".replace(",", " ").replace("-", "−"))
    ax.set_ylabel(None)
    ax.text(0, 1.02, enhet, transform=ax.transAxes, fontsize=8, ha="left")


def figur1_produksjon(d: pd.DataFrame):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    h = d["produksjon_sd_historisk"].dropna()
    ax.plot(h.index, h.values, color="black", lw=1.5, label="Historisk")
    for b, farge in (("hoy", figurer.LYSEBLA), ("basis", figurer.MORKEBLA),
                     ("lav", figurer.MELLOMBLA)):
        s = d[f"produksjon_sd_{b}"].dropna()
        ax.plot(s.index, s.values, color=farge, lw=1.5, label=NAVN[b])
    ax.set_xlim(1971, 2050)
    ax.set_ylim(0, None)
    _akser(ax, "Mill. Sm³ o.e.")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=4)
    figurer.lagre(fig, "figur1_produksjon")
    plt.close(fig)


def figur2_baner(d: pd.DataFrame, cf: dict):
    """Egen versjon av Sokkeldirektoratets figur 2.5 og 2.6.

    Søylene er modellens egne tall på de to prissettene. De røde strekene er
    Sokkeldirektoratets PUBLISERTE nivåer, så leseren ser hvor godt
    gjenskapingen treffer og hvor mye Energidepartementets priser ligger under.
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    fig, akser = plt.subplots(1, 2, figsize=(7.2, 3.4))
    x = np.arange(3)
    paneler = (("Mrd. 2026-kroner, udiskontert",
                lambda s: s.loc[FRA:TIL].sum(), sodir.UDISKONTERT),
               (f"Mrd. 2026-kroner, nåverdi {_n(100 * RENTE, 0)} pst.",
                nnv, sodir.NNV_4PST))
    for ax, (enhet, fn, publisert) in zip(akser, paneler):
        for i, (pris, farge, etikett) in enumerate(
                (("flat", figurer.LYSEBLA, "Modellen, flat pris 80 USD/fat o.e."),
                 ("ed", figurer.MORKEBLA, "Modellen, Energidepartementets priser"))):
            ax.bar(x + (i - 0.5) * 0.4, [fn(cf[(b, pris)]) for b in BANER],
                   0.38, color=farge, label=etikett if ax is akser[0] else None)
        for j, b in enumerate(BANER):
            ax.plot([j - 0.45, j + 0.45], [publisert[(b, 80)]] * 2,
                    color=figurer.ROD, lw=1.5, solid_capstyle="round")
        ax.set_xticks(x, [NAVN[b] for b in BANER])
        _akser(ax, enhet)
    akser[0].legend(
        handles=[plt.Rectangle((0, 0), 1, 1, color=figurer.LYSEBLA),
                 plt.Rectangle((0, 0), 1, 1, color=figurer.MORKEBLA),
                 Line2D([0], [0], color=figurer.ROD, lw=1.5)],
        labels=["Modellen, flat pris 80 USD/fat o.e.",
                "Modellen, Energidepartementets priser",
                "Sokkeldirektoratets publiserte nivå"],
        loc="upper center", bbox_to_anchor=(1.12, -0.09), ncol=1)
    figurer.lagre(fig, "figur2_baner")
    plt.close(fig)


# Rekkefølgen i fossefiguren. Fossefigurer er veiavhengige, så rekkefølgen er
# et valg: de fire substansielle leddene først, fallende, deretter de to
# tekniske og horisonten. Da leses figuren ovenfra og ned uten pukkel.
FOSSE_ORDEN = ["Pris: gass → 80 USD", "Pris: olje og NGL → 80 USD",
               "Kostnad: NB26 → SD", "Volum: NB26 → SD basis",
               "Uttaksrate: 0,824 → 0,780", "Avlesning av figur 2.6",
               "Horisont: 2051-2060 tas ut"]
FOSSE_ETIKETT = {"Pris: gass → 80 USD": "Gasspris",
                 "Pris: olje og NGL → 80 USD": "Oljepris\nog NGL",
                 "Kostnad: NB26 → SD": "Kostnad",
                 "Volum: NB26 → SD basis": "Volum",
                 "Uttaksrate: 0,824 → 0,780": "Uttaks-\nrate",
                 "Avlesning av figur 2.6": "Avlesning",
                 "Horisont: 2051-2060 tas ut": "Horisont"}


def figur3_fossefigur(d: pd.DataFrame, b: pd.Series):
    """Fra Sokkeldirektoratets 7 500 ned til NB26s 3 671.

    Broen er bygget nedenfra i broen(); her snus fortegnene, slik at figuren
    leses i den retningen spørsmålet stilles: hvorfor er Sokkeldirektoratets
    ressursverdi dobbelt så høy som statens?
    """
    import matplotlib.pyplot as plt

    start = sodir.NNV_4PST[("basis", 80)]
    slutt = b.iloc[0]
    mellom = [(navn, -b[navn]) for navn in FOSSE_ORDEN]

    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    n = len(mellom) + 2
    ax.bar(0, start, 0.62, color=figurer.MORKEBLA)
    ax.text(0, start + 160, _n(start, 0), ha="center", fontsize=8.5)

    niva = start
    for i, (navn, v) in enumerate(mellom, start=1):
        bunn, topp = min(niva, niva + v), max(niva, niva + v)
        farge = (figurer.ROD if navn.startswith("Pris: gass")
                 else figurer.MELLOMBLA if v < 0 else figurer.LYSEBLA)
        ax.bar(i, topp - bunn, 0.62, bottom=bunn, color=farge)
        ax.plot([i - 0.31, i + 0.69], [niva + v] * 2, color="#666666",
                lw=0.6, zorder=0)
        ax.text(i, topp + 160, f"{'+' if v > 0 else '−'}{_n(abs(v), 0)}",
                ha="center", fontsize=8.5)
        niva += v
    ax.bar(n - 1, slutt, 0.62, color=figurer.MORKEBLA)
    ax.text(n - 1, slutt + 160, _n(slutt, 0), ha="center", fontsize=8.5)

    ax.set_xticks(range(n),
                  ["Sokkel-\ndirektoratet"]
                  + [FOSSE_ETIKETT[k] for k, _ in mellom] + ["NB26"],
                  fontsize=8)
    ax.set_xlim(-0.7, n - 0.3)
    ax.set_ylim(0, start * 1.10)
    _akser(ax, "Mrd. 2026-kroner, nåverdi 4 pst.")
    figurer.lagre(fig, "figur3_fossefigur")
    plt.close(fig)


# --- rapport ----------------------------------------------------------------

def main() -> None:
    figurer.sett_stil(dokument=True)
    d = steg1.last()
    flat = flat_pris(d)
    p = modell.realpriser(d)
    fx = d.loc[TIL, "dollarkurs"]

    print("=" * 78)
    print("STEG 2 — ENERGIDEPARTEMENTETS PRISBANER MOT SOKKELDIREKTORATETS")
    print("=" * 78)

    print("\nA. PRISINGEN")
    print("-" * 78)
    print(f"  Flat prising, 80 USD per fat o.e.: {_n(flat, 0)} kr/Sm3 o.e. "
          f"({_n(flat / fx, 0)} USD)")
    print(f"  {'':22}{'kr/Sm3 o.e.':>13}{'USD':>8}{'flat/ED':>10}")
    enheter = {"olje": ("USD/fat", d.loc[TIL, "fat_per_sm3"]),
               "gass": ("USD/MMBtu", sodir.MMBTU_PER_SM3),
               "ngl": ("USD/fat", d.loc[TIL, "fat_per_sm3"])}
    for r in modell.RESSURSER:
        pr = p[r].loc[TIL]
        e, faktor = enheter[r]
        print(f"  ED {r:<19}{_n(pr, 0):>13}{_n(pr / fx / faktor, 1):>8}"
              f"{_n(flat / pr, 2):>10}   ({e}, {TIL})")

    innt = modell.inntekt(d)
    v = {r: d[f"produksjon_{r}"] for r in modell.RESSURSER}
    print("\n  Inntektsvektet over hele perioden, diskontert — det som faktisk")
    print("  driver broen, siden gassprisen faller og oljeprisen stiger:")
    for r in modell.RESSURSER:
        ed = nnv(v[r] * p[r] / modell.MILL_PER_MRD)
        fl = nnv(v[r] * flat / modell.MILL_PER_MRD)
        print(f"    {r:<6}{_n(fl / ed, 2)}x   (ED {_n(ed, 0)} → flat {_n(fl, 0)} mrd.)")

    print("\nB. SOKKELDIREKTORATETS KOSTNAD — KONSISTENT I NÅVERDI")
    print("-" * 78)
    e = sd_enhetskostnad(d)
    print(f"  Implisert enhetskostnad, kr per diskontert Sm3 o.e.:")
    print(f"    Høy {_n(e['hoy'], 0)}   Lav {_n(e['lav'], 0)}   "
          f"avvik {_n(100 * (e['hoy'] / e['lav'] - 1), 1)} pst.")
    print(f"    interpolert til Basis: {_n(e['basis'], 0)}")
    print(f"  Implisert uttaksrate: Høy {_n(e['m_hoy'], 3)}   Lav {_n(e['m_lav'], 3)}")
    print("\n  RETTELSE TIL STEG 1: udiskontert var de samme enhetskostnadene")
    print("  1 397 og 1 731, altså 24 pst. fra hverandre, og jeg konkluderte")
    print("  med ±10 pst. presisjon. Diskontert er de 1,4 pst. fra hverandre.")
    print("  Figur 2.6 er det pålitelige grunnlaget; forbeholdet gjaldt den")
    print("  udiskonterte avlesningen i figur 2.5.")

    print("\nC. BROEN")
    print("-" * 78)
    b = broen(d)
    print(f"  {'ledd':32s}{'mrd.':>9}{'nivå':>9}")
    akk = 0.0
    for navn, verdi in b.items():
        akk += verdi
        fortegn = "" if navn.startswith("NB26") else ("+" if verdi > 0 else "−")
        print(f"  {navn:32s}{fortegn + _n(abs(verdi), 0):>9}{_n(akk, 0):>9}")
    print(f"  {'= SD Basis, figur 2.6':32s}{'':9}{_n(sodir.NNV_4PST[('basis', 80)], 0):>9}")
    res = b["Avlesning av figur 2.6"]
    print(f"\n  Residualen er {_n(abs(res), 0)} mrd., "
          f"{_n(abs(100 * res / sodir.NNV_4PST[('basis', 80)]), 1)} pst. av 7 500.")
    print("  Den står som eget ledd og fordeles ikke ut på de andre.")

    print("\n  Gassleddet er det klart største, som forventet. Men kostnadsleddet")
    print("  er nesten like stort som oljeleddet: Sokkeldirektoratet regner både")
    print("  høyere pris OG lavere kostnad enn staten. Horisonten er liten, slik")
    print("  steg 1 varslet.")

    print("\nD. KONTANTSTRØM PER BANE")
    print("-" * 78)
    cf = kontantstrommer(d)
    print(f"  {'bane':7}{'udisk. ED':>12}{'udisk. flat':>13}"
          f"{'NNV ED':>10}{'NNV flat':>11}{'forhold':>9}")
    for bane in BANER:
        u_ed = cf[(bane, "ed")].loc[FRA:TIL].sum()
        u_fl = cf[(bane, "flat")].loc[FRA:TIL].sum()
        n_ed, n_fl = nnv(cf[(bane, "ed")]), nnv(cf[(bane, "flat")])
        print(f"  {NAVN[bane]:7}{_n(u_ed, 0):>12}{_n(u_fl, 0):>13}"
              f"{_n(n_ed, 0):>10}{_n(n_fl, 0):>11}{_n(n_fl / n_ed, 2) + 'x':>9}")
    print(f"\n  Sokkeldirektoratets egne nivåer, NNV 4 pst.: "
          f"Høy {_n(sodir.NNV_4PST[('hoy', 80)], 0)}, "
          f"Basis {_n(sodir.NNV_4PST[('basis', 80)], 0)}, "
          f"Lav {_n(sodir.NNV_4PST[('lav', 80)], 0)}")

    print("\n  Kontroll: kalles motoren uten argumenter, skal den gi NB26 eksakt.")
    basis = modell.kontantstrom(d)
    avvik = (basis - d["snks"]).loc[FRA:TIL].abs().max()
    print(f"    største avvik mot NB26s SNKS: {avvik:.2e} mrd.")
    bind = modell.gulvet_binder(d)
    print(f"    gulvet maks(., 0) binder i {int(bind.loc[FRA:TIL].sum())} av 25 år på basis")
    for bane in ("hoy", "lav"):
        bb = modell.gulvet_binder(d, volum=modell.volumbaner(d)[bane])
        print(f"    ... og i {int(bb.loc[FRA:TIL].sum())} år på {NAVN[bane].lower()}banen")

    print("\n  Gassprisgjennomslag (åpent punkt 3), NNV 4 pst. på basisbanen:")
    for g in (1.0, 0.5):
        s = modell.kontantstrom(d, priser=flate_priser(d), gassprisgjennomslag=g)
        print(f"    gjennomslag {_n(g, 2)}: flat prising gir {_n(nnv(s), 0)} mrd.")
    print("    Halvt gjennomslag halverer gassleddet i broen. Tallet må avklares")
    print("    med Energidepartementet før fossefiguren publiseres.")

    print("\nE. FIGURER")
    print("-" * 78)
    figur1_produksjon(d)
    figur2_baner(d, cf)
    figur3_fossefigur(d, b)
    for f in ("figur1_produksjon", "figur2_baner", "figur3_fossefigur"):
        print(f"  output/figurer/{f}.svg")


if __name__ == "__main__":
    main()
