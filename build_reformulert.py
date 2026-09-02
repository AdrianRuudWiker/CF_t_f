# -*- coding: utf-8 -*-
"""
Bygger den REFORMULERTE usikkerhetsmodellen inn i
Kontantstromsmodell_petroleum.xlsx, Excel-native.

Beslutninger dette bygget realiserer (avklart med brukeren 02.09.2026):
- Persentilene ER scenariene: P90 = høy prognosert CF, P50 = median, P10 = lav.
  Ingen 3x3 av vilkårlige multiplikatorer.
- BEGGE forankringer vises: medianforankring (P50 = NB26) som hovedspor og
  forventningsforankring (E = NB26) som følsomhet, side om side i samme ark,
  drevet av SAMME trekk. Forskjellen er én multiplikativ Jensen-korreksjon
  EXP(-sigma^2/2) på prisfaktoren, så motoren trenger ikke to sett trekk.
- Kalibreringsvei (c): sigma avledes historisk av Forutsetninger!B4:B7
  (sigma = LN(persentilforhold)/NORMSINV(0,9), eksakt for en medianforankret
  lognormal), og IEA WEO NZE legges inn som et NAVNGITT SIDESCENARIO utenfor
  viften — ikke som en persentil. Viften viser markedsrisiko kalibrert på
  historikk; NZE-linjen viser politikkrisiko historikken ikke inneholder.
- Balansepris-gulv: feltnetto gulves ved 0, styrt av en bryter i arket.

Ikke-destruktivt: de eksisterende arkene (OU-motoren, 3x3-en, Miksfølsomhet)
står urørt. Bygget legger til to ark:
- "MC-motor-R" (skjult): trekk + levende formler, begge forankringer.
- "Reformulert vifte" (synlig): persentiltabell, oppsummering, NZE-sidescenario
  og parameteravlesning — alt PERCENTILE/AVERAGE-formler mot motoren.

NZE-sidescenarioet krever tall fra IEA WEO Annex A som IKKE kunne hentes
(egress-proxyen blokkerer iea.org). Cellene er lagt inn som blå input og står
tomme; scenarioet gir #N/A til de er fylt ut, i stedet for å vise et tall som
ikke har kilde.

Kjøring:  python3 build_reformulert.py
Krever:   numpy, openpyxl
"""
import numpy as np
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter as CL

FIL = "Kontantstromsmodell_petroleum.xlsx"
MOTOR, VIFTE = "MC-motor-R", "Reformulert vifte"

YEARS = list(range(2026, 2051))
NY = len(YEARS)
FU0 = 18                    # Forutsetninger: 2026 på rad 18
N = 2000                    # simuleringer
SEED = 2026

DATA0 = 10                  # motor: første simulering
C_SIM, C_W, C_Z1, C_Z2 = 1, 2, 3, 4
C_FO, C_FG = 5, 6           # prisfaktorer, beregnet én gang per simulering
C_MED, C_FOR = 8, 34        # SNCF-blokker (25 kolonner hver)
A_MED, A_FOR = 60, 65       # aggregater: KUM, NPV3, NPV2, NPV4

# Forutsetninger: nytt parameterblokk under kildenoten (rad 44)
P0 = 46
R_SIGO, R_SIGG, R_RHO, R_GULV = P0 + 1, P0 + 2, P0 + 3, P0 + 4
R_JO, R_JG, R_N, R_SEED = P0 + 5, P0 + 6, P0 + 7, P0 + 8
R_BBL, R_FX, R_BASO, R_BASG, R_KRG = P0 + 9, P0 + 10, P0 + 11, P0 + 12, P0 + 13
R_NZEO, R_NZEG, R_STPO, R_STPG = P0 + 14, P0 + 15, P0 + 16, P0 + 17
R_PNZEO, R_PNZEG, R_PSTPO, R_PSTPG = P0 + 18, P0 + 19, P0 + 20, P0 + 21
R_NZEOK = P0 + 22           # er NZE-scenarioet komplett?

C_NZEO, C_NZEG = 17, 18     # årstabell: Q, R = NZE-prisbaner (input)

BLA = Font(color="FF0000FF")
HDR = Font(color="FFFFFFFF", bold=True)
HDRF = PatternFill("solid", fgColor="FF181C62")
FET = Font(bold=True)
GRA = Font(italic=True, color="FF595959")
F2, F0 = "#,##0.00", "#,##0"


def trekk(n=N, seed=SEED):
    """Faste, persistente regimetrekk — ett per simulering.

    Samme rekkefølge som mc_reformulert.simuler (z før w), slik at Excel og
    Python-referansen kan sammenlignes på identiske trekk.
    """
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n, 2))
    w = rng.triangular(-1, 0, 1, n)
    return w, z[:, 0], z[:, 1]


def _fu(ref):
    return f"Forutsetninger!{ref}"


def _parametre(wb):
    """Nytt parameterblokk i Forutsetninger. Idempotent — skrives alltid likt."""
    fu = wb["Forutsetninger"]
    fu.cell(P0, 1, "Parametre — reformulert usikkerhetsmodell "
                   "(persentiler som scenarier)").font = FET

    rader = [
        (R_SIGO, "sigma_olje (persistent prisregime)",
         "=LN(B4)/NORMSINV(0.9)",
         "Avledet: for en medianforankret lognormal er sigma = LN(P90/P50)/z90. "
         "Historisk kalibrering, jf. B4/B5."),
        (R_SIGG, "sigma_gass (persistent prisregime)",
         "=LN(B6)/NORMSINV(0.9)",
         "Avledet på samme måte fra B6/B7."),
        (R_RHO, "korrelasjon olje/gass (regime)", 0.60,
         "Input. Regimetrekkene er korrelerte, men gass har egen dynamikk."),
        (R_GULV, "Balansepris-gulv (1 = på, 0 = av)", 1,
         "Tilbudsrespons: feltnetto gulves ved 0, ingen tapsproduksjon. "
         "Forankret i balanseprisene, deck slide 14 (~20-45 USD/fat)."),
        (R_JO, "Jensen-korreksjon olje", f"=EXP(-(B{R_SIGO}^2)/2)",
         "1/E[EXP(sigma*z)]. Brukes KUN i forventningsforankringen. "
         "Parentesen om kvadratet er nødvendig: Excel binder unær minus "
         "sterkere enn potens, så -B^2 ville blitt (-B)^2 = +B^2."),
        (R_JG, "Jensen-korreksjon gass", f"=EXP(-(B{R_SIGG}^2)/2)",
         "Samme for gass."),
        (R_N, "Antall simuleringer", N, "Faste trekk i MC-motor-R."),
        (R_SEED, "Frø (seed)", SEED, "Reproduserbart."),
        (R_BBL, "Fat per Sm3 o.e.", 6.2898, "Input, enhetskonvertering."),
        (R_FX, "NOK per USD", 10.5, "Input, enhetskonvertering."),
        (R_BASO, "Impliert basis oljepris USD/fat (2050)",
         f"=J42/(B{R_BBL}*B{R_FX})",
         "Kontroll mot deck slide 5 (70 USD/fat fra 2035). Modellen ligger "
         "marginalt lavere; avviket er dokumentert."),
        (R_BASG, "Basis gasspris USD/MMBtu (fra 2040)", 5.7,
         "Deck slide 5. Input, brukes til enhetskonvertering for gass."),
        (R_KRG, "kr/Sm3 o.e. per USD/MMBtu", f"=K42/B{R_BASG}",
         "Avledet av basisbanen, så gasspriser i USD kan legges inn direkte."),
        (R_NZEO, "IEA WEO NZE oljepris USD/fat — FYLL INN", None,
         "Annex A. Kunne ikke hentes (egress blokkert). Søketreff antydet "
         "25 USD/fat i 2050 for WEO 2025, men tallet er UVERIFISERT og er "
         "derfor ikke lagt inn."),
        (R_NZEG, "IEA WEO NZE gasspris USD/MMBtu — FYLL INN", None,
         "Annex A. Ikke funnet i det hele tatt."),
        (R_STPO, "IEA WEO STEPS oljepris USD/fat — FYLL INN", None,
         "Annex A. Kun til persentilavlesningen under, ikke til kalibrering."),
        (R_STPG, "IEA WEO STEPS gasspris USD/MMBtu — FYLL INN", None,
         "Annex A."),
        (R_PNZEO, "NZE olje faller på persentil",
         f'=IF(ISNUMBER(B{R_NZEO}),NORMSDIST(LN(B{R_NZEO}/B{R_BASO})/B{R_SIGO}),"")',
         "Leser av hvor scenarioet havner i den historisk kalibrerte viften. "
         "Viser hvor uenige kildene er — IEA kalibrerer ikke viften."),
        (R_PNZEG, "NZE gass faller på persentil",
         f'=IF(ISNUMBER(B{R_NZEG}),NORMSDIST(LN(B{R_NZEG}/B{R_BASG})/B{R_SIGG}),"")',
         ""),
        (R_PSTPO, "STEPS olje faller på persentil",
         f'=IF(ISNUMBER(B{R_STPO}),NORMSDIST(LN(B{R_STPO}/B{R_BASO})/B{R_SIGO}),"")',
         ""),
        (R_PSTPG, "STEPS gass faller på persentil",
         f'=IF(ISNUMBER(B{R_STPG}),NORMSDIST(LN(B{R_STPG}/B{R_BASG})/B{R_SIGG}),"")',
         ""),
        (R_NZEOK, "NZE-sidescenario komplett (1/0)",
         f"=IF(AND(OR(COUNT(Q{FU0}:Q42)={NY},ISNUMBER(B{R_NZEO})),"
         f"OR(COUNT(R{FU0}:R42)={NY},ISNUMBER(B{R_NZEG}))),1,0)",
         "Scenarioet gir #N/A til både olje- og gassprisen er lagt inn, "
         "enten som flatt nivå over eller som årsbane i kolonne Q/R."),
    ]
    inputrader = {R_RHO, R_GULV, R_N, R_SEED, R_BBL, R_FX, R_BASG,
                  R_NZEO, R_NZEG, R_STPO, R_STPG}
    for rad, navn, verdi, note in rader:
        fu.cell(rad, 1, navn)
        c = fu.cell(rad, 2, verdi)
        if rad in inputrader:
            c.font = BLA
        if rad in (R_PNZEO, R_PNZEG, R_PSTPO, R_PSTPG):
            c.number_format = "0.0 %"
        elif rad not in (R_GULV, R_N, R_SEED):
            c.number_format = F2
        fu.cell(rad, 3, note)

    # Årstabell: input-kolonner for NZE-prisbaner (valgfritt alternativ til
    # det flate nivået i parameterblokken).
    for col, tekst in ((C_NZEO, "NZE oljepris (USD/fat) — input, Annex A"),
                       (C_NZEG, "NZE gasspris (USD/MMBtu) — input, Annex A")):
        h = fu.cell(16, col, tekst)
        h.font, h.fill = HDR, HDRF
        for i in range(NY):
            fu.cell(FU0 + i, col).font = BLA
        fu.column_dimensions[CL(col)].width = 30


def _motor(wb, w, z1, z2, n=N):
    """Skjult motor: faste trekk + levende formler, begge forankringer."""
    if MOTOR in wb.sheetnames:
        del wb[MOTOR]
    ws = wb.create_sheet(MOTOR)
    ws.sheet_state = "hidden"

    ws.cell(1, 1, f"MC-MOTOR, REFORMULERT: {n} simuleringer, persistente "
                  f"regimetrekk. Begge forankringer på samme trekk.").font = FET
    for r, lbl in zip(range(3, 9), ("A = volO*pO + volN*pN", "B = volG*pG",
                                    "C = kostnader", "andel", "fh", "fl")):
        ws.cell(r, 2, lbl)

    hdr = ["sim", "w", "z1", "z2", "fo", "fg", ""] \
        + [f"SNCFmed_{y}" for y in YEARS] + [""] \
        + [f"SNCFfor_{y}" for y in YEARS] + [""] \
        + ["KUMmed", "NPV3med", "NPV2med", "NPV4med", ""] \
        + ["KUMfor", "NPV3for", "NPV2for", "NPV4for"]
    for c, h in enumerate(hdr, 1):
        if h:
            ws.cell(9, c, h).font = FET

    # Per-år parameterblokk over medianblokken; forventningsblokken peker på
    # de samme cellene, så tallgrunnlaget står ett sted.
    for i in range(NY):
        fr = FU0 + i
        ws.cell(3, C_MED + i, f"={_fu(f'B{fr}')}*{_fu(f'J{fr}')}"
                              f"+{_fu(f'D{fr}')}*{_fu(f'L{fr}')}")
        ws.cell(4, C_MED + i, f"={_fu(f'C{fr}')}*{_fu(f'K{fr}')}")
        ws.cell(5, C_MED + i, f"={_fu(f'M{fr}')}")
        ws.cell(6, C_MED + i, f"={_fu(f'P{fr}')}")
        ws.cell(7, C_MED + i, f"={_fu(f'H{fr}')}")
        ws.cell(8, C_MED + i, f"={_fu(f'I{fr}')}")

    sig_o, sig_g = _fu(f"$B${R_SIGO}"), _fu(f"$B${R_SIGG}")
    rho, gulv = _fu(f"$B${R_RHO}"), _fu(f"$B${R_GULV}")
    jo, jg = _fu(f"$B${R_JO}"), _fu(f"$B${R_JG}")

    fo_c, fg_c = CL(C_FO), CL(C_FG)
    for r in range(n):
        row = DATA0 + r
        ws.cell(row, C_SIM, r + 1)
        ws.cell(row, C_W, float(w[r]))
        ws.cell(row, C_Z1, float(z1[r]))
        ws.cell(row, C_Z2, float(z2[r]))
        # Prisfaktorene beregnes ÉN gang per simulering (persistent regime),
        # slik at årsformlene blir korte. Gass korreleres med olje i formelen.
        ws.cell(row, C_FO, f"=EXP({sig_o}*$C{row})")
        ws.cell(row, C_FG, f"=EXP({sig_g}*({rho}*$C{row}"
                           f"+SQRT(1-{rho}^2)*$D{row}))")
        for base, kor_o, kor_g in ((C_MED, "", ""), (C_FOR, f"*{jo}", f"*{jg}")):
            for i in range(NY):
                pc = CL(C_MED + i)      # parameterkolonnen ligger i medianblokken
                volfac = (f"IF($B{row}>=0,1+$B{row}*({pc}$7-1),"
                          f"1+$B{row}*(1-{pc}$8))")
                netto = (f"{volfac}/(1+({pc}$7+{pc}$8-2)/6)"
                         f"*({pc}$3*${fo_c}{row}{kor_o}"
                         f"+{pc}$4*${fg_c}{row}{kor_g}-{pc}$5)")
                # Gulvbryter uten å gjenta netto-uttrykket: nedre grense er 0
                # når gulv=1 og -1E30 (praktisk talt ingen grense) når gulv=0.
                ws.cell(row, base + i,
                        f"={pc}$6*MAX({netto},({gulv}-1)*1E+30)/1000")
        for base, agg in ((C_MED, A_MED), (C_FOR, A_FOR)):
            rng = f"{CL(base)}{row}:{CL(base + NY - 1)}{row}"
            ws.cell(row, agg, f"=SUM({rng})")
            ws.cell(row, agg + 1, f"=NPV({_fu('$B$8')},{rng})")
            ws.cell(row, agg + 2, f"=NPV({_fu('$B$9')},{rng})")
            ws.cell(row, agg + 3, f"=NPV({_fu('$B$10')},{rng})")
    return ws


def _vifte(wb, n=N):
    """Synlig ark: persentiler for begge forankringer, basis og NZE-scenario."""
    if VIFTE in wb.sheetnames:
        del wb[VIFTE]
    ws = wb.create_sheet(VIFTE, 4)

    ws["A1"] = ("REFORMULERT USIKKERHETSMODELL — SNCF, mrd. 2026-kroner. "
                "Persentilene er scenariene.")
    ws["A1"].font = FET
    ws["A2"] = (
        f"Én Monte Carlo på basisproduksjon, {n} simuleringer med faste trekk "
        "(frø i Forutsetninger). Pris og volum trekkes som PERSISTENTE REGIMER "
        "— ett trekk per simulering som gjelder hele perioden — fordi høy- og "
        "lavbaner historisk har vart over flere år. Pris: korrelerte lognormale "
        "faktorer på NB26-banen, sigma avledet av de historiske "
        "persentilforholdene i Forutsetninger B4:B7. Volum: triangulær vekt som "
        "interpolerer Sokkeldirektoratets lav/basis/høy. Feltnetto gulves ved 0 "
        "(balanseprisgulv). BEGGE forankringer vises på samme trekk: "
        "medianforankring har P50 = NB26 og et middel over NB26; "
        "forventningsforankring har middel = NB26 og en median under. "
        "Middelet skal ikke rapporteres som forventet innbetaling uten at "
        "avviket mot NB26 opplyses.")
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = 78

    grupper = [(2, "Medianforankring (hovedspor): P50 = NB26"),
               (8, "Forventningsforankring (følsomhet): middel = NB26"),
               (14, "Referansebaner")]
    for col, tekst in grupper:
        c = ws.cell(3, col, tekst)
        c.font, c.fill = HDR, HDRF
    kolonner = ["År"] + ["P10", "P25", "P50", "P75", "P90", "Middel"] * 2 \
        + ["NB26-basis", "IEA NZE-sidescenario"]
    for c, h in enumerate(kolonner, 1):
        cc = ws.cell(4, c, h)
        cc.font, cc.fill = HDR, HDRF

    kv = [("P10", 0.1), ("P25", 0.25), ("P50", 0.5), ("P75", 0.75), ("P90", 0.9)]
    for i in range(NY):
        row, fr = 5 + i, FU0 + i
        ws.cell(row, 1, YEARS[i])
        for j, (base, kol0) in enumerate(((C_MED, 2), (C_FOR, 8))):
            rng = f"'{MOTOR}'!{CL(base + i)}{DATA0}:{CL(base + i)}{DATA0 + n - 1}"
            for k, (_, q) in enumerate(kv):
                ws.cell(row, kol0 + k, f"=PERCENTILE({rng},{q})").number_format = F0
            ws.cell(row, kol0 + 5, f"=AVERAGE({rng})").number_format = F0
        # NB26-basis som formel, ikke hardkodet tall.
        ws.cell(row, 14, f"={_fu(f'N{fr}')}/1000").number_format = F0
        ws.cell(row, 15, _nze_formel(fr)).number_format = F0

    ws.cell(31, 1, "Oppsummering (mrd. 2026-kroner)").font = FET
    for col, tekst in ((2, "Medianforankring"), (8, "Forventningsforankring")):
        c = ws.cell(32, col, tekst)
        c.font, c.fill = HDR, HDRF
    for c, h in enumerate(["", "P10", "P25", "P50", "P75", "P90", "Middel"] * 2, 1):
        if h:
            cc = ws.cell(33, c, h)
            cc.font, cc.fill = HDR, HDRF
    for k, (navn, off) in enumerate((("Kumulativ SNCF 2026-2050", 0),
                                     ("NPV, 3 pst.", 1),
                                     ("NPV, 2 pst.", 2),
                                     ("NPV, 4 pst.", 3))):
        row = 34 + k
        ws.cell(row, 1, navn)
        for base, kol0 in ((A_MED, 2), (A_FOR, 8)):
            col = CL(base + off)
            rng = f"'{MOTOR}'!{col}{DATA0}:{col}{DATA0 + n - 1}"
            for j, (_, q) in enumerate(kv):
                ws.cell(row, kol0 + j, f"=PERCENTILE({rng},{q})").number_format = F0
            ws.cell(row, kol0 + 5, f"=AVERAGE({rng})").number_format = F0

    ws.cell(39, 1, "Kontroll mot basis").font = FET
    kontroller = [
        ("NB26-basis, kumulativ 2026-2050", f"=SUM(N5:N{4 + NY})"),
        ("NB26-basis, NPV 3 pst.", f"=NPV({_fu('$B$8')},N5:N{4 + NY})"),
        ("Median P50 kumulativ / basis - 1", "=D34/B40-1"),
        ("Median middel kumulativ / basis - 1", "=G34/B40-1"),
        ("Forventning middel kumulativ / basis - 1", "=M34/B40-1"),
        ("Sum av årsmedianer (medianforankring)", f"=SUM(D5:D{4 + NY})"),
    ]
    for k, (navn, f) in enumerate(kontroller):
        row = 40 + k
        ws.cell(row, 1, navn)
        c = ws.cell(row, 2, f)
        c.number_format = "0.0 %" if "- 1" in navn else F0

    ws.cell(47, 1, "Parametre og forankring").font = FET
    par = [
        ("sigma_olje (avledet, historisk)", f"={_fu(f'B{R_SIGO}')}", F2),
        ("sigma_gass (avledet, historisk)", f"={_fu(f'B{R_SIGG}')}", F2),
        ("korrelasjon olje/gass", f"={_fu(f'B{R_RHO}')}", F2),
        ("Balansepris-gulv (1 = på)", f"={_fu(f'B{R_GULV}')}", "0"),
        ("Antall simuleringer", f"={_fu(f'B{R_N}')}", "0"),
        ("Frø (seed)", f"={_fu(f'B{R_SEED}')}", "0"),
        ("Kalibrering", "historisk (Forutsetninger B4:B7), vei (c)", None),
        ("NZE olje faller på persentil", f"={_fu(f'B{R_PNZEO}')}", "0.0 %"),
        ("NZE gass faller på persentil", f"={_fu(f'B{R_PNZEG}')}", "0.0 %"),
        ("STEPS olje faller på persentil", f"={_fu(f'B{R_PSTPO}')}", "0.0 %"),
        ("STEPS gass faller på persentil", f"={_fu(f'B{R_PSTPG}')}", "0.0 %"),
    ]
    for k, (navn, f, fmt) in enumerate(par):
        row = 48 + k
        ws.cell(row, 1, navn)
        c = ws.cell(row, 2, f)
        if fmt:
            c.number_format = fmt

    ws.cell(60, 1,
            "IEA-scenariene er IKKE brukt til å kalibrere viften. Grunnen er at "
            "de skiller seg ved politikk og etterspørsel, ikke ved tilbudssjokk, "
            "og derfor nesten bare spenner nedsiden: STEPS ligger tett på APS "
            "mens NZE ligger langt under. Å tvinge P90 = STEPS og P10 = NZE "
            "krever sigma som er over ti ganger ulike opp og ned, og gir en "
            "vifte uten mening. NZE vises derfor som et navngitt sidescenario, "
            "og persentilavlesningen over sier hvor uenige kildene er."
            ).font = GRA
    ws.cell(61, 1,
            "NZE-kolonnen gir #N/A til prisene er lagt inn i Forutsetninger "
            f"(B{R_NZEO}/B{R_NZEG} for flatt nivå, eller kolonne Q/R for en "
            "årsbane). Tallene skal hentes fra IEA WEO Annex A."
            ).font = GRA

    ws.column_dimensions["A"].width = 38
    for col in range(2, 16):
        ws.column_dimensions[CL(col)].width = 12
    ws.freeze_panes = "B5"
    return ws


def _nze_formel(fr):
    """NZE-sidescenario for ett år: basisvolum, NZE-priser, samme gulv.

    NGL følger oljeprisen, som i resten av modellen. Prisene skaleres som
    forhold mot basisbanen, så enhetene arves fra Forutsetninger.
    """
    o_usd = (f"IF(ISNUMBER({_fu(f'Q{fr}')}),{_fu(f'Q{fr}')},"
             f"{_fu(f'$B${R_NZEO}')})")
    g_usd = (f"IF(ISNUMBER({_fu(f'R{fr}')}),{_fu(f'R{fr}')},"
             f"{_fu(f'$B${R_NZEG}')})")
    o_kr = f"{o_usd}*{_fu(f'$B${R_BBL}')}*{_fu(f'$B${R_FX}')}"
    g_kr = f"{g_usd}*{_fu(f'$B${R_KRG}')}"
    ro = f"({o_kr})/{_fu(f'J{fr}')}"
    rg = f"({g_kr})/{_fu(f'K{fr}')}"
    netto = (f"({_fu(f'B{fr}')}*{_fu(f'J{fr}')}+{_fu(f'D{fr}')}*{_fu(f'L{fr}')})"
             f"*{ro}+{_fu(f'C{fr}')}*{_fu(f'K{fr}')}*{rg}-{_fu(f'M{fr}')}")
    kropp = (f"{_fu(f'P{fr}')}*IF({_fu(f'$B${R_GULV}')}=1,"
             f"MAX({netto},0),{netto})/1000")
    return f"=IF({_fu(f'$B${R_NZEOK}')}=0,NA(),{kropp})"


def _dokumentasjon(wb):
    dok = wb["Dokumentasjon"]
    rad = dok.max_row + 2
    dok.cell(rad, 1, "REFORMULERT USIKKERHETSMODELL (arket «Reformulert "
                     "vifte» og skjult «MC-motor-R»)").font = FET
    tekster = [
        "Persentilene er scenariene: P90 er den høye prognosen, P50 "
        "sentralanslaget og P10 den lave. Den erstatter 3x3-en med vilkårlige "
        "multiplikatorer, som ble forlatt fordi høy/lav-nivåene ikke hadde "
        "kilde og fordi kombinasjonen høyt volum og lav pris ga negative tall.",
        "Usikkerheten trekkes som PERSISTENTE REGIMER, ett trekk per "
        "simulering for hele perioden, ikke som år-til-år-støy. Det speiler at "
        "høy- og lavprisperioder historisk har vart i flere år, og gir en "
        "vifte som kan leses som scenarier.",
        "Tilbudsrespons: feltnetto gulves ved 0 (bryter i Forutsetninger). "
        "Uten gulvet er om lag 11 pst. av årsobservasjonene negative, som "
        "overdriver nedsiden — produsentene stenger ned i stedet for å "
        "produsere med tap. Gulvet er forankret i balanseprisene, deck slide "
        "14 (om lag 20-45 USD/fat før skatt).",
        "BEGGE forankringer vises, på samme trekk. Medianforankring "
        "(hovedspor) setter median[pris] = NB26, slik at P50-banen ER "
        "sentralanslaget; til gjengjeld ligger middelet over NB26. "
        "Forventningsforankring setter E[pris] = NB26 via Jensen-korreksjonen "
        "EXP(-sigma^2/2); da er middelet lik NB26, men medianen faller under. "
        "Begge kan ikke oppfylles samtidig for en skjev fordeling. Middelet "
        "skal ikke presenteres som forventet innbetaling til fondet uten at "
        "avviket mot NB26 opplyses.",
        "Kalibrering: sigma avledes av de re-sentrerte historiske "
        "persentilforholdene (Forutsetninger B4:B7) som "
        "LN(forhold)/NORMSINV(0,9). Det er eksakt for en medianforankret "
        "lognormal, og gjør viften konsistent med prisskiftene i «Statisk "
        "modell» i P10/P90. Ingenting er hardkodet: endres B4:B7, endres sigma.",
        "IEA WEO er IKKE brukt til å kalibrere viftens ytterkanter. "
        "Scenariene skiller seg ved politikk og etterspørsel, ikke ved "
        "tilbudssjokk, og spenner derfor nesten bare nedsiden — IEA har ingen "
        "høyprisverden. NZE er i stedet lagt inn som et navngitt sidescenario "
        "utenfor viften, slik at markedsrisiko (viften, kalibrert på "
        "historikk) og politikkrisiko (NZE-linjen) holdes fra hverandre.",
        "Forbehold: den historiske kalibreringen bygger på 1997-2024, en "
        "periode uten gjennomført energiomstilling. Persentilavlesningen i "
        "arket viser hvor et NZE-forløp havner i viften — ligger det svært "
        "langt ute i halen, betyr det at viften ikke rommer "
        "omstillingsrisikoen, og NZE-linjen må leses som et selvstendig "
        "scenario, ikke som en usannsynlig hale.",
    ]
    for k, t in enumerate(tekster, 1):
        dok.cell(rad + k, 1, t)


def build(fil=FIL, n=N, seed=SEED):
    wb = load_workbook(fil)
    w, z1, z2 = trekk(n, seed)
    _parametre(wb)
    _motor(wb, w, z1, z2, n)
    _vifte(wb, n)
    _dokumentasjon(wb)
    wb.calculation.fullCalcOnLoad = True
    wb.save(fil)
    return fil


if __name__ == "__main__":
    print("Skrev", build())
