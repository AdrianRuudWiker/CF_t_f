# HANDOFF — SNCF-modell, status og videre arbeid

Overlevering til ny chat-økt. Prosjektet: modell for statens netto kontantstrøm
(SNCF) fra petroleum → innbetaling til SPU, 2026-2050, faste 2026-kroner.
Bygget for saksbehandler i FIN, Avdeling for formuesforvaltning. Alt på norsk
bokmål. Leveranse skal fungere Excel-native (bruker har ikke Python på jobb).

Gren: `claude/sncf-anchor-calibrate-smb2ii` (bygger på PR #1-grenen
`claude/claude-md-review-verify-70a7je`, som er merget inn).
Se `CLAUDE (1).md` for full modelldokumentasjon.

## 1. FORANKRING — AVKLART 02.09.2026: BEGGE SKAL VISES

**Brukerens beslutning: vis begge forankringer i leveransen.** Medianforankring
er hovedsporet (P50 = NB26), forventningsforankring følger som følsomhet i eget
ark, slik at Jensen-effekten blir eksplisitt for leseren i stedet for skjult i
et metodevalg. `mc_reformulert.py` rapporterer nå begge side om side
(`python3 mc_reformulert.py`).

Konsekvens for bygging: Excel-leveransen trenger to persentilsett fra samme
motor. Det er billig — forskjellen er én multiplikativ driftsfaktor på
prisfaktoren, så MC-motoren kan beholde ett sett trekk og bare skalere prisen.
Ikke to motorer.

Hvorfor de to skiller seg: prisen er en lognormal faktor. For lognormal er
median = exp(-0,5σ²) < mean = 1. Forventningsforankring (E[faktor]=1) presser
derfor medianen under basis; medianforankring (median[faktor]=1) løfter middelet
over basis. **Man kan ikke få begge.** Kontantstrømmens middel/median-gap er
ca. 18-25 pst. uansett valg — driftsleverasje (inntekt minus kostnad) forsterker
prisgapet på 6-11 pst. Forankringen bestemmer bare hvilken av de to NB26 blir
liggende på.

Med historisk kalibrert sigma (se punkt 2), kumulativ 2026-2050, mrd. 2026-kr,
basis 4 861:

| | Forventningsforankring | Medianforankring |
|---|---|---|
| Kumulativ P50 | 3 975 (−18,2 pst.) | **5 006 (+3,0 pst.)** |
| Kumulativ middel | 5 011 (+3,1 pst.) | 6 087 (+25,2 pst.) |
| Sum av årsmedianer | 3 946 | 4 971 (≈ basis) |
| NPV 3 pst. P50 | 3 105 (−17,3 pst.) | 3 874 (+3,2 pst.) |
| Impliert oljepris P50 | 63 USD/fat | 68 USD/fat (= basis) |

Faglig begrunnelse for at medianforankring er HOVEDsporet (tre grunner):
1. Basis er IEA WEO APS (deck slide 5) — et *scenario*, ikke et
   sannsynlighetsvektet gjennomsnitt. IEA presiserer selv at scenariene ikke er
   prognoser. Et scenario merket «sentralt» leses naturlig som «like sannsynlig
   over som under», altså en median.
2. Designet krever det. Hele poenget er at persentilene ER scenariene. Er
   P50 ≠ NB26, presenterer modellen tre scenarier der ingen av dem er det
   offisielt vedtatte sentralanslaget. Det er ikke holdbart i et FIN-notat.
3. Offisiell praksis. Norges Banks rente- og inflasjonsvifter og IMF WEOs
   vifter legger sentralbanen på medianen.

Motargumentet, som må stå i Dokumentasjon-arket: terminprisene fram til 2035
(deck slide 5) er nærmest en *forventning* om prisen, og med medianforankring
havner modellens forventede innbetaling til fondet ~25 pst. over NB26s eget
anslag. **Middelet skal derfor ikke rapporteres som «forventet innbetaling»
uten at avviket mot NB26 er opplyst.** Praktisk: rapporter persentiler, ikke
middel.

## 2. KALIBRERING AV SIGMA — IEA-planen holder ikke, historisk gjør det

`kalibrering.py` gjør begge veier: løser sigma fra måltall, og leser av hvilken
persentil et gitt måltall havner på i den historiske kalibreringen.

### Nettadgang: IEA-tallene kunne ikke hentes
Containerens egress-proxy blokkerer `iea.org`, `iea.blob.core.windows.net`,
`regjeringen.no`, `carbonbrief.org` og alt annet direkte oppslag — bare
websøk kommer ut. Annex A-prisforutsetningene i WEO er derfor **ikke** hentet.
Fra søketreff (WEO 2025, **IKKE verifisert mot Annex A**): olje STEPS 80 USD/fat
i 2035 og 76 i 2050; NZE 33 i 2035 og 25 i 2050. Gassprisene ble ikke funnet i
det hele tatt. Presentasjonen i repoet er gjennomsøkt (alle 15 slides) — den
oppgir bare APS som langsiktig anker, ingen STEPS/NZE-tall.
**Brukeren har IEA-tilgang på jobb og bør lime inn Annex A-tabellen;**
fyll den inn i `MAL` i `kalibrering.py`.

### Det strukturelle funnet: IEA-scenariene kan ikke kalibrere en vifte
Planen «P90 ~ STEPS, P10 ~ NZE» virker ikke. IEA-scenariene skiller seg ved
*politikk og etterspørsel*, ikke ved tilbudssjokk, så de spenner nesten bare
nedsiden av prisfordelingen. IEA har ingen høyprisverden. Med basis 70:
- STEPS 76 ⇒ sigma_opp = 0,064. NZE 25 ⇒ sigma_ned = 0,803. **12,5x forskjell.**
- Symmetrisk sigma = 0,803 (treffer NZE) gir P90 = 196 USD/fat.
- Symmetrisk sigma = 0,064 (treffer STEPS) gir P10 = 64 USD/fat.
- Splitt-lognormal treffer begge, men viften blir meningsløs: P25 41, P75 73,
  og impliert forventning 57 USD/fat — 18 pst. UNDER deckets egen basis.

Kjørt i modellen kollapser den varianten også P50 (til 4 117, −15,3 pst.), fordi
CF-medianen ikke er prismedianen når flere risikofaktorer virker sammen.

### Anbefalt kalibrering: historisk, lest ut av arbeidsboken
`KALIBRERING="historisk"` leser `Forutsetninger!B4:B7` — de re-sentrerte
historiske persentilforholdene (P90/P50 og P10/P50 av realpris 1997-2024) — og
regner sigma = ln(forhold)/z_p eksakt. Ingenting hardkodes (CLAUDE.md-regelen).
Resultat: **sigma_olje 0,393, sigma_gass 0,490** — og forholdstallene er
eksakt symmetriske i log, så splitt-lognormalen kollapser til én sigma per vare.
Nær dagens ad hoc 0,35/0,45, men nå avledet i stedet for gjettet.

Gevinsten: den reformulerte viften reproduserer da de statiske prisskiftene i
«Statisk modell» nøyaktig i P10/P90. De to modellene blir konsistente, og
sigma oppdaterer seg selv hvis persentilforholdene endres.

Implisert: olje P10 41 / P50 68 / P90 112 USD/fat; gass P10 3,0 / P50 5,7 /
P90 10,8 USD/MMBtu. Kumulativ P10 688 / P50 5 006 / P90 12 679, middel 6 087.
Balansepris-gulvet virker: 0,0 pst. negative årsverdier (mot 11,2 pst. uten).

### Uenigheten mellom kildene, målt
Holder man historisk sigma fast, faller IEA-scenariene på:
- STEPS (76 USD) → **P61** — praktisk sett umulig å skille fra basis.
- NZE (25 USD) → **P0,5** — en 1-av-200-hendelse.

Altså: den historiske kalibreringen behandler en NZE-verden som nærmest
utelukket. Det er en **politisk-faglig vurdering**, ikke noe modellen kan
avgjøre. Historikken 1997-2024 er en verden uten gjennomført energiomstilling;
kalibrerer man på den, antar man implisitt at omstillingsrisikoen ligner
fortidens prisrisiko.

### Forsoningspunktet — det mest interessante funnet
`kalibrering.py forsoningspunkt()` løser hvilken nedside-sigma som gir
E = median = basis samtidig (medianen i splitt-lognormalen er alltid 1; er også
forventningen 1, faller de to forankringene sammen og hele spørsmålet i punkt 1
forsvinner for den varen). Lukket form:
E = e^(σ_ned²/2)·Φ(−σ_ned) + e^(σ_opp²/2)·Φ(σ_opp).

- **Olje:** forsoning ved σ_ned = 0,780, altså **P10 = 25,0 USD/fat**. Det er
  praktisk talt identisk med det (uverifiserte) NZE-tallet 25. Med
  hybridkalibrering blir E[oljefaktor] = 1,0005 — median og forventning
  sammenfaller, og oljeprisen blir 25 / 68 / 112 / middel 68 i BEGGE
  forankringer. Sammenfallet er tilfeldig, ikke utledet, og hviler på et tall
  som må verifiseres. Men det peker på noe reelt: median-vs-forventning-
  problemet er et symptom på at nedsiden i den historiske fordelingen er for
  TYNN, ikke et iboende metodeproblem.
- **Gass:** forsoning ville krevd σ_ned = 1,306, altså **P10 = 1,07 USD/MMBtu**.
  Ingen IEA-scenario er i nærheten. Gass kan derfor ikke forsones slik, og et
  middel/median-gap på gass står uansett igjen og må opplyses.

### Kjørte tall for hybrid (nedside olje = NZE 25, gass historisk)
Kumulativ: median­forankret P10 105 / P50 4 729 / P90 12 658 / middel 5 740
(P50 −2,7 pst., middel +18,1 pst. mot basis). Forventningsforankret
P10 32 / P50 4 265 / P90 11 745 / middel 5 217.
Merk P10 = 105 mrd. — hybriden sier at i tiendeperecentilen får fondet nær
ingenting. Det er et kraftig utsagn som må tåle å bli utfordret.

### Tre veier — anbefaling
- **(a) Ren historisk:** σ 0,393/0,490 fra `Forutsetninger!B4:B7`. Forsvarlig,
  verifiserbart, konsistent med «Statisk modell» i P10/P90.
- **(b) Hybrid:** nedside forankret i NZE, oppside i historikk. **Kan ikke
  bygges nå** — gass-NZE-tallet mangler, så gass faller tilbake på historikk og
  viften blir skjev på en måte som er vanskelig å forklare (olje σ_ned 0,78 mot
  gass 0,49). Forsoningspunktet for gass (1,07 USD/MMBtu) viser at hybriden
  ikke kan gjøres symmetrisk konsistent i det hele tatt.
- **(c) Historisk motor + NZE som navngitt sidescenario** utenfor viften.

**ANBEFALING: (c).** (a) og (c) er SAMME motor — (c) legger bare på en merket
linje i figuren, altså null ekstra modellrisiko. Den skiller de to
usikkerhetstypene som faktisk er ulike: viften viser markedsrisiko kalibrert på
historikk, NZE-linjen viser politikkrisiko som historikken ikke inneholder. Det
er også spørsmålet ekspertrådet vil stille. Og valget er reversibelt: kommer
Annex A-tallene inn og støtter hybriden, slås den på med én bryter
(`KALIBRERING="hybrid"`), som allerede er implementert.

**Ikke bygget inn i arbeidsboken** — venter på brukerens valg av (a)/(b)/(c),
per instruks.

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
- Basis = IEA WEO APS. IEA-forankring av ytterkantene (P90 ~ STEPS, P10 ~ NZE)
  er PRØVD OG FORKASTET — se punkt 2 over. Sigma kalibreres historisk.

Nåværende oppsett (`MEDIAN_ANCHOR=True`, `KALIBRERING="historisk"`,
sigma olje/gass 0,393/0,490 lest ut av `Forutsetninger!B4:B7`):
- Impliert oljepris: P10 41 / P50 68 / P90 112 USD/fat (middel 73).
- Impliert gasspris: P10 3,0 / P50 5,7 / P90 10,8 USD/MMBtu (middel 6,4).
- Kumulativ til fondet: P10 688 / P50 5 006 / P90 12 679 / middel 6 087.
- NPV3: P10 601 / P50 3 874 / P90 9 581 / middel 4 658.
- 0,0 pst. negative årsverdier.

Nytt i `mc_reformulert.py`: splitt-lognormal (eget sigma over/under medianen,
median bevart eksakt), `KALIBRERING`-bryter, sigma avledet fra arbeidsboken.
Viftefigur `reformulert_vifte.svg` er fra det GAMLE oppsettet og må regenereres
når forankring og kalibrering er låst.

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

Brukerens URL-kilder (til IEA-kalibrering og produksjon). MERK: ingen av disse
kan hentes fra containeren — egress-proxyen blokkerer alle. Må limes inn:
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
   siden ~2010). IEA-ankeret høy=STEPS/lav=NZE er senere FORKASTET (punkt 2):
   scenariene spenner bare nedsiden og kan ikke kalibrere ytterkantene.
5. Vis begge horisonter (2050/3 pst. + 2060/4 pst.).

## Neste steg (prioritert)
1. Forankring er avklart (begge vises, punkt 1). **Gjenstår: brukerens valg av
   kalibreringsvei (a)/(b)/(c) — anbefalt (c).** Brukeren svarte «usikker»
   02.09.2026; beslutningsgrunnlaget står i punkt 2, inkludert
   forsoningspunktet og hvorfor (b) ikke kan bygges nå. Ingenting bygges i
   arbeidsboken før dette er låst.
2. Brukeren limer inn IEA WEO Annex A-prisforutsetningene (kan ikke hentes fra
   containeren — egress blokkert) inn i `MAL` i `kalibrering.py`, så
   plasseringstallene (STEPS P61 / NZE P0,5) kan verifiseres mot faktiske tall
   i stedet for søketreff.
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
