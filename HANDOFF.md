# HANDOFF — SNCF-modell, status og videre arbeid

Overlevering til ny chat-økt. Prosjektet: modell for statens netto kontantstrøm
(SNCF) fra petroleum → innbetaling til SPU, 2026-2050, faste 2026-kroner.
Bygget for saksbehandler i FIN, Avdeling for formuesforvaltning. Alt på norsk
bokmål. Leveranse skal fungere Excel-native (bruker har ikke Python på jobb).

Gren: `claude/claude-md-review-verify-70a7je`. PR #1 mot main.
Se `CLAUDE (1).md` for full modelldokumentasjon.

## DET SENTRALE ÅPNE SPØRSMÅLET (start her)

Brukeren mener **P50 (median) bør = NB26-basis** — "50-persentil = NB26". I
dagens forventningsforankring blir medianen LAVERE enn basis, og brukeren er
ikke fornøyd med det.

Hvorfor median < basis i dag: prisen modelleres som en lognormal faktor med
E[faktor]=1 (forventningsforankret). For lognormal er median = exp(-0,5σ²) <
mean = 1. Så median pris < basis → median CF < basis.

To valg (bryter `MEDIAN_ANCHOR` i `mc_reformulert.py`):
| | Forventningsforankring (dagens) | Medianforankring |
|---|---|---|
| Kumulativ P50 | 4 116 | **4 973 (≈ basis 4 861)** |
| Kumulativ middel | 4 964 | 5 848 |
| NPV3 P50 | 3 210 | 3 853 |

- **Forventningsforankring:** E[pris]=NB26 → median under basis. Riktig HVIS
  NB26 er en forventningsbane.
- **Medianforankring:** median[pris]=NB26 → P50≈basis (det brukeren vil ha),
  men middelet havner OVER basis.

Hvilken som er riktig avhenger av om NB26 tolkes som forventning eller median.
Tidligere i prosjektet sa brukeren "forventning/sentralbane", men intuisjonen
nå peker mot medianforankring. **Må avklares først i ny økt.** Merk: for en
vifte der "P50 = sentralanslaget = NB26" er medianforankring mest intuitivt for
en leser, og er slik offisielle vifter (f.eks. inflasjonsrapporter) ofte er.

## Hvor vi står — to spor

### Spor 1: Committet leveranse (i repoet, PR #1)
Arbeidsboken `Kontantstromsmodell_petroleum.xlsx` + `mc_simulering.py` +
`build_workbook.py` + `lag_figurer.py` + SVG-figurer. Historikk på grenen:
- K3-fiks: MC forventningsforankret i NB26 (Jensen på pris, mean-1 på volum).
- Statiske prisskift re-sentrert på NB26 (3x3 som scenarioverktøy).
- `build_workbook.py` regenererer MC-motoren idempotent; `_recenter_price_shifts`,
  `_static_supply_floor` (sistnevnte ble laget men er IKKE aktiv i committet kode
  — se git-historikk; ble revertert da vi tok et steg tilbake).

VIKTIG: brukeren ble frustrert over multiplikator-3x3-en og de negative tallene.
Vi forlot den tilnærmingen til fordel for Spor 2. Committet bok er altså en
mellomstasjon, ikke ønsket sluttdesign.

### Spor 2: Reformulert modell (ØNSKET RETNING) — `mc_reformulert.py`
Prototype, ikke integrert i boka ennå. Kjør `python3 mc_reformulert.py`.

Idé: én Monte Carlo på basisproduksjon der **PERSENTILENE SELV ER SCENARIENE**:
P90 = høy prognosert CF, P50 = median, P10 = lav. Ingen egen 3x3.
- Persistente REGIME-trekk (ett per sim) for pris (lognormal faktor) og volum
  (triangulær lav/basis/høy) — speiler "høybane/lavbane har vart over flere år".
- Tilbudsrespons: feltnetto gulves ved 0 (ingen tapsproduksjon), forankret i
  balanseprisene. Fjerner de meningsløse negative tallene (0 % negative år).
- Forankret i IEA WEO: P90 ~ STEPS/Current Policies, P10 ~ NZE, basis = APS.

Resultat (forventningsforankret, sigma olje/gass 0,35/0,45):
- Impliert oljepris: P10 41 / P50 64 / P90 100 USD/fat.
- Impliert gasspris: P10 2,9 / P50 5,2 / P90 9,3 USD/MMBtu.
- Kumulativ til fondet: P10 537 / P50 4 116 / P90 10 326 / middel 4 964.
- NPV3: P10 478 / P50 3 210 / P90 7 825.
Viftefigur laget (scratchpad `reformulert_vifte.svg`) — kopi committet som
referanse.

## KILDER (autoritative)

Offisiell presentasjon på `origin/main` (hentes med
`git checkout origin/main -- "Statens petroleumsformue til ekspertrådet for SPU (002).pptx"`):
**"Statens petroleumsformue til ekspertrådet for SPU"**, Per Valvatne, 19.03.2026.
Nøkkelslides:
- Slide 5 (PRISER): olje forward til 2035 så **70 USD/fat**; gass ED til 2030,
  så **6,6 → 5,7 USD/MMBtu** (2030-2040), 5,7 fra 2040. Langsiktig = **IEA WEO
  APS**. Offisiell NNV 2026-**2060** med **4 pst.** = **4 800 mrd.** (i 2025,
  statsbudsjettets deflator).
- Slide 10: SDs mulighetsbilder (produksjon) — basis 235→83, høy 117, lav 8
  mill Sm³ o.e. mot 2050. Vid vifte.
- Slide 14: Balansepriser før skatt ~20-45 USD/fat (nyere ~30). Brent-historikk
  2010-2024 ~20-125 USD.
- Slide 7-8: ressursregnskap (15,7 mrd Sm³ o.e., 57 % produsert).

VERIFISERT: modellens basis-prisbaner stemmer eksakt med deck slide 5
(olje→68≈70, gass 6,6→5,7). Basis er altså allerede autoritativ = APS.

VIKTIG OPPKLARING: "4 800" er NNV **2026-2060 @ 4 pst.** — en ANNEN størrelse
enn modellens kumulative 4 861 (2026-2050, udiskontert) eller NPV3 3 753.
Likheten er tilfeldig. Brukeren vil "vise begge": 2050/3 pst. som hovedmodell +
2060/4 pst. som sammenligning mot 4 800 (krever ekstrapolering 2051-2060 utover
SD-dataene).

Brukerens URL-kilder (til IEA-kalibrering og produksjon):
- IEA WEO 2024: iea.org/reports/world-energy-outlook-2024
- IEA WEO 2025 Current Policies: iea.org/reports/world-energy-outlook-2025/current-policies-scenario
- Perspektivmeldingen/oljemelding: regjeringen.no .../stm202520260001000dddopri.pdf
- Norsk Petroleum produksjonsprognoser: norskpetroleum.no/en/production-and-exports/production-forecasts/
- Sodir ressursregnskap 2025 og "the shelf 2025"
- S&P/IEA oljeetterspørsel til 2050 (Current Policies)

## Beslutninger tatt (avklart med bruker)
1. NB26/deck-basis (APS) er senterbanen. Verifisert autoritativ.
2. 3x3 med vilkårlige multiplikatorer FORKASTET. Persentiler-som-scenarier valgt.
3. Negative CF-tall er en modellfeil (manglende tilbudsrespons), ikke en egenskap
   — skal fjernes med balansepris-gulv.
4. Gass behandles med egen prisdynamikk (størst inntekt, frikoblet fra olje
   siden ~2010). IEA-anker: høy=STEPS, lav=NZE.
5. Vis begge horisonter (2050/3 pst. + 2060/4 pst.).

## Neste steg (prioritert)
1. **Avklar forankring** (median vs forventning — se øverst). Sannsynligvis
   medianforankring gitt brukerens intuisjon; sett `MEDIAN_ANCHOR=True`.
2. Hente EKSAKTE IEA WEO STEPS/NZE olje- og gasspriser fra lenkene; kalibrere
   SIGMA_OLJE/SIGMA_GASS så P90/P10 treffer STEPS/NZE presist.
3. Vurdere om persistent regime-trekk er nok, eller om det trengs år-til-år-
   variasjon i tillegg (i dag er pris ren persistent faktor).
4. Foredle tilbudsrespons: fra hardt 0-gulv til en balansepris-basert gradvis
   nedstenging (bruk fordelingen ~20-45 USD fra slide 14).
5. 2060/4 pst.-utvidelse (ekstrapoler produksjon/pris 2051-2060).
6. Integrere i leveransen: Excel-native motor (via `build_workbook.py`),
   `mc_simulering.py`, regenerere figurer (`lag_figurer.py`), oppdatere CLAUDE.md.
7. Rydde: filnavn `CLAUDE (1).md` → `CLAUDE.md`.

## Praktisk
- Miljø: `pip install numpy openpyxl matplotlib cairosvg python-pptx`.
- `soffice`/LibreOffice er ØDELAGT i containeren (kan ikke reberegne xlsx eller
  konvertere). Bruk `formulas`-biblioteket for å verifisere Excel-formler mot
  Python; bruk `cairosvg` for SVG→PNG QA.
- FIN designprofil på figurer: `fin_chart_style.py` fra fin-designprofil-skillen.
  Arial mangler i containeren → faller tilbake på DejaVu Sans (sanksjonert).
- Konfidensialitet: `Mulighetsbilde Petroleum.xlsx` ligger i repoet; brukeren
  har valgt å beholde den (avvik fra CLAUDE.md-regel, men bevisst).
