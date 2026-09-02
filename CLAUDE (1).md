# Kontantstrømmodell for petroleumsvirksomheten (SNCF)

Simulering av statens netto kontantstrøm (SNCF) fra petroleumsvirksomheten
2026-2050 under usikkerhet i pris og produksjonsvolum. Bygget i samtale med
Claude 01.09.2026 for saksbehandler i Finansdepartementet, Avdeling for
formuesforvaltning. Alle beløp i faste 2026-kroner.

## Kritiske arbeidsregler

- **All kommunikasjon og dokumentasjon på norsk bokmål.** Følg
  Finansdepartementets skrivestil der prosa produseres.
- **Leveranser må være Excel-native.** Brukeren har ikke Python-tilgang på
  jobb. Python kan brukes til å BYGGE og VERIFISERE, men sluttproduktet skal
  fungere i ren Excel (formler, ikke skript). Monte Carlo-motoren er derfor
  implementert med faste trekk + levende formler i arket.
- **Aldri hardkod resultater der en formel kan stå.** Endres parametre i
  Forutsetninger-arket, skal alt reberegnes.
- **Konfidensialitet:** Kildefilen Mulighetsbilde_Petroleum.xlsx (intern
  NB26-arbeidsbok) skal IKKE ligge i dette repoet. Alle nødvendige data er
  ekstrahert til modellarbeidsboken med kildehenvisning.
- Figurer følger FINs designprofil: fargene #181c62 (mørkeblå), #4156a6,
  #5b91cc, #f15d61 (rød, kun fremheving); hvit bakgrunn; ingen tittel/kilde
  inne i selve figuren; norske akselabels ("Mrd. 2026-kroner"); tusenskille
  med mellomrom, desimalkomma. SVG er standard leveranseformat.

## Filer i repoet

- `Kontantstromsmodell_petroleum.xlsx` — hovedleveransen. Fem synlige ark
  pluss to skjulte motorer:
  - **Forutsetninger**: alt tallgrunnlag (blå celler = input, svarte =
    formler) og parametre i B4-B15 (prisskift, rente, sigma, kappa,
    korrelasjon). Årstabell rad 17-42 (2025-2050), kolonner A-P, med Q/R som
    input for NZE-prisbaner. Rad 46-68 er parameterblokken for den
    reformulerte modellen (avledet sigma, korrelasjon, gulvbryter,
    Jensen-korreksjoner, enhetskonvertering, IEA-input og persentilavlesning).
  - **Statisk modell**: SNCF per år for 3 volumbaner x 3 prisnivåer
    (levende formler), kontrollkolonne (basis minus SNKS = 0), to
    3x3-matriser (NPV 3 pst. og kumulativ), rentefølsomhet.
  - **Miksfølsomhet**: lavbanen med gassandel +/- 10 pp.
  - **Monte Carlo**: persentiltabell og oppsummering, alt PERCENTILE-formler
    mot motoren.
  - **MC-motor** (skjult): 2 000 simuleringer. Kolonner: w (volumvekt,
    statisk), z1/z2 (normaltrekk, statiske, frø 2026), logMo/logMg
    (OU-prosess, formler), SNCF per år (formler), NPV2/3/4 og kumulativ per
    simulering. Per-år-parametre i rad 3-8 over SNCF-blokken.
  - **Reformulert vifte**: den ØNSKEDE modellen — persentiler som scenarier,
    begge forankringer side om side (B-G medianforankret, H-M forventnings-
    forankret), NB26-basis og IEA NZE-sidescenario i N/O, oppsummering rad
    31-37, kontroll mot basis rad 39-45, parameteravlesning rad 47-58.
  - **MC-motor-R** (skjult): 2 000 simuleringer av den reformulerte modellen.
    Kolonner: w, z1, z2 (persistente trekk, ett per simulering, frø 2026),
    fo/fg (prisfaktorer, beregnet én gang per simulering), SNCF per år for
    begge forankringer, og KUM/NPV3/NPV2/NPV4 per forankring. Per-år-parametre
    i rad 3-8 over medianblokken; forventningsblokken peker på de samme
    cellene.
  - **Dokumentasjon**: antakelser, begrensninger, kilder.
- `mc_simulering.py` — valgfri Python-referanse; leser parametre fra
  arbeidsboken. 10 000 simuleringer. Brukes til verifikasjon.
- `build_workbook.py` — regenererer MC-motoren fra input og baker inn
  forventningsforankringen (Jensen på pris, mean-1 på volum). Bevarer de
  faste trekkene og de synlige arkene.
- `lag_figurer.py` — regenererer de tre SVG-figurene fra de forventnings-
  forankrede tallene (FINs designprofil), lest fra de 2 000 faste trekkene.
- `build_reformulert.py` — bygger den reformulerte modellen (arket
  «Reformulert vifte» + skjult «MC-motor-R» + parameterblokken) inn i
  arbeidsboken. Ikke-destruktivt: de eksisterende arkene står urørt.
- `verifiser_reformulert.py` — verifiserer Excel-formlene mot Python med
  `formulas`-biblioteket, på en liten, strukturelt identisk testbok.
- `mc_reformulert.py` — Python-referanse for den reformulerte modellen.
  Rapporterer begge forankringer side om side. Brytere: `MEDIAN_ANCHOR`,
  `KALIBRERING` ("historisk"/"hybrid"/"manuell"), `SUPPLY_FLOOR`.
- `kalibrering.py` — kalibreringsverktøy: løser sigma fra måltall, leser av
  hvilken persentil et måltall havner på, og finner forsoningspunktet der
  median- og forventningsforankring faller sammen.
- `lag_figur_reformulert.py` — regenererer `reformulert_vifte.svg` og
  `reformulert_akkumulert.svg` fra arbeidsbokens egne trekk, med begge
  forankringer i samme figur.
- `viftefigur_sncf.svg` — tetthetsvifte for årlig SNCF (gradert opasitet,
  kuttet ved 5-95-persentil, median hvit med mørk kontur, NB26-basis rød
  stiplet).
- `akkumulert_sncf.svg` — akkumulert SNCF med persentilbånd og sluttverdier.
- `fordelinger_sncf.svg` — histogrammer (SNCF 2035 og kumulativ) med modus,
  median, middelverdi og basisbane markert.
- `reformulert_vifte.svg` / `reformulert_akkumulert.svg` — den reformulerte
  modellen: bånd og median medianforankret, forventningsforankret median som
  egen linje, NB26-basis rød stiplet.
- `HANDOFF.md` — status, åpne valg og beslutningsgrunnlag mellom økter.

## Modellarkitektur

To modeller deler samme tallgrunnlag i Forutsetninger. Den REFORMULERTE er den
ønskede leveransen; den gamle beholdes som mellomstasjon og sammenligning.

### Reformulert modell (ønsket retning) — «Reformulert vifte» + «MC-motor-R»

SNCF_t = andel_t * MAX(volfaktor_t/E[volfaktor_t]
         * (volO_t*pO_t*Fo + volG_t*pG_t*Fg + volN_t*pN_t*Fo - kostnader_t), 0)

- **Fo, Fg**: PERSISTENTE prisregimer — ett lognormalt trekk per simulering
  som gjelder hele perioden. Fo = EXP(sigma_o*z1),
  Fg = EXP(sigma_g*(rho*z1 + SQRT(1-rho^2)*z2)), rho = 0,60. NGL følger olje.
  Medianforankret er dette uttrykket brukt som det står (median = 1 eksakt);
  forventningsforankret ganges det med EXP(-sigma^2/2) slik at E = 1.
- **sigma avledes**, ikke gjettes: sigma = LN(persentilforhold)/NORMSINV(0,9)
  fra B4:B7. Gir 0,393 (olje) og 0,490 (gass). Da reproduserer viften de
  statiske prisskiftene i «Statisk modell» i P10/P90.
- **volfaktor**: ett triangulært trekk per simulering (w i [-1,1]) som
  interpolerer SDs lav/basis/høy for hele banen, delt på E[volfaktor] =
  1+(fh+fl-2)/6 så volumet er forventningsforankret.
- **MAX(..., 0)**: balansepris-gulv, tilbudsrespons. Bryter i B50.
  I arket skrevet som MAX(netto, (gulv-1)*1E+30) for å slippe å gjenta
  netto-uttrykket.
- **IEA WEO NZE** ligger som navngitt sidescenario i kolonne O, med basisvolum
  og NZE-priser. Gir #N/A til prisene er lagt inn (B60/B61 eller Q/R).

### Gammel modell (mellomstasjon) — «Statisk modell», «Monte Carlo», «MC-motor»

SNCF_t = andel_t * volfaktor_t * (volO_t*pO_t*Mo_t + volG_t*pG_t*Mg_t
         + volN_t*pN_t*Mo_t - kostnader_t)

- **andel_t** (statsandelen, 0,87-1,01): kalibrert per år slik at basisbanen
  reproduserer NB26s SNKS-anslag EKSAKT. Fanger skatt + SDØE + utbytte uten
  eksplisitt skattemodell. andel = SNKS / (inntekter - kostnader).
- **volfaktor**: 1 i basis; totalbane_høy/basis eller lav/basis ellers.
  Skalerer både inntekter og kostnader (konstante enhetskostnader).
- **Priser**: NB26-baner per Sm3 o.e. Statiske skift (3x3): historiske
  persentiler (P90/P50, P10/P50 av realpris 1997-2024), RE-SENTRERT på NB26
  (delt på geo-senter så høy/lav er symmetrisk rundt banen): olje 1,654/0,605,
  gass 1,873/0,534. NGL følger olje. 3x3 = scenario (vedvarende regime); MC =
  sannsynlighet (se beslutningslogg #12).
- **Monte Carlo**: volum = ETT triangulærtrekk per simulering (w i [-1,1])
  som interpolerer lav/basis/høy for hele banen. Pris = gjennomsnitts-
  reverterende OU på logpris, MEDIANFORANKRET i NB26-banen. Estimert med
  AR(1) på realpriser 1997-2024: kappa olje 0,212 (halveringstid 3 år),
  gass 0,330 (1,7 år); residual-sigma 0,232/0,386; residualkorrelasjon
  0,674. NGL følger oljesjokket. Pris-volum-korrelasjon = 0.
- **Diskontering**: 3 pst. realrente (= formuesberegningen i NB26 og
  forventet realavkastning i SPU). Følsomhet 2 og 4 pst. Rundskriv R-109
  (4 pst.) gjelder samfunnsøkonomiske analyser av tiltak, IKKE
  formuesberegning — ikke bytt uten grunn.

## Beslutningslogg (avklart med brukeren, endres ikke uten ny avklaring)

1. Målvariabel: statens netto kontantstrøm, direkte.
2. Statsandel: kalibrert mot NB26-basis (ikke full skattemodell).
3. Kostnader: proporsjonal skalering med volumfaktor.
4. Prissplitt: to priser (olje, gass), NGL som olje.
5. Prisgrunnlag: NB26 som senterbane. LSEG-terminkurver kun rimelighets-
   sjekk (OBS: brukerens LSEG-tilgang dekker IKKE historical_pricing).
6. Statiske skift: historisk persentilkalibrering.
7. Enheter: NOK, faste 2026-kroner.
8. MC: pris og volum stokastisk. GBM ble valgt først, FORKASTET 01.09.2026
   av brukeren (implausible haler: gass-P90 over 10x banen i 2050) og
   erstattet med estimert OU. mc_simulering.py har OVERSTYR_KAPPA=0.0 for
   å gjenskape GBM.
9. Resultater: vifte, akkumulert og NPV-fordeling.
10. Horisont 2026-2050 (Sokkeldirektoratets mulighetsbilder slutter 2050).
11. Forankring: prisen var først MEDIANforankret. Endret 01.09.2026 (avklart
    med brukeren) til FORVENTNINGSforankring, fordi NB26-banen er en
    forventningsbane, ikke en median: E[SNCF] skal være lik NB26-basis. Bakt
    inn i MC-motoren via `build_workbook.py` (Jensen-korreksjon på logpris,
    E[Mo]=E[Mg]=1; volumfaktoren delt på E[volfaktor]=1+(fh+fl-2)/6).
13. REFORMULERT MODELL (02.09.2026, avklart med brukeren): 3x3-en med
    vilkårlige multiplikatorer er FORLATT. Erstattet av én Monte Carlo på
    basisproduksjon der PERSENTILENE SELV ER SCENARIENE (P90 = høy prognose,
    P50 = sentralanslag, P10 = lav). Usikkerheten trekkes som PERSISTENTE
    REGIMER, ett trekk per simulering for hele perioden, ikke år-til-år-støy —
    det speiler at høy- og lavprisperioder historisk varer i flere år.
    Tilbudsrespons: feltnetto gulves ved 0, forankret i balanseprisene
    (deck slide 14). Bygget av `build_reformulert.py`. De gamle arkene beholdes
    som mellomstasjon.
14. Forankring i den reformulerte modellen: BEGGE vises (02.09.2026).
    Medianforankring er hovedsporet — median[pris] = NB26, så P50-banen ER
    sentralanslaget, som persentiler-som-scenarier krever, og som er slik
    Norges Banks og IMFs vifter er bygget. Forventningsforankring følger som
    følsomhet via Jensen-korreksjonen EXP(-sigma^2/2). Begge kan ikke oppfylles
    samtidig: middel/median-gapet i kontantstrømmen er 18-25 pst. uansett, og
    forankringen bestemmer bare hvilken av dem NB26 ligger på. MIDDELET SKAL
    IKKE rapporteres som forventet innbetaling uten at avviket mot NB26
    opplyses.
15. Kalibrering av den reformulerte modellen: vei (c) — historisk motor med
    IEA WEO NZE som NAVNGITT SIDESCENARIO utenfor viften. sigma avledes av de
    re-sentrerte historiske persentilforholdene (B4:B7) som
    LN(forhold)/NORMSINV(0,9), som er eksakt for en medianforankret lognormal:
    sigma_olje 0,393, sigma_gass 0,490. IEA-forankring av ytterkantene
    (P90 = STEPS, P10 = NZE) ble PRØVD OG FORKASTET: scenariene skiller seg ved
    politikk og etterspørsel, ikke tilbudssjokk, og spenner nesten bare
    nedsiden — STEPS impliserer sigma 0,064, NZE 0,803, altså 12,5x forskjell,
    og en symmetrisk sigma som treffer NZE gir P90 = 196 USD/fat.
12. 3x3 er et SCENARIOverktøy, MC et SANNSYNLIGHETSverktøy — de svarer på
    ulike spørsmål og skal ikke ha samme høy/lav. De statiske prisskiftene ble
    re-sentrert på NB26 01.09.2026 (avklart med brukeren): de rå historiske
    persentilene var ikke sentrert på anker-banen (geo-senter olje 0,87, gass
    1,08), noe som blåste opp de negative lavpris-hjørnene. Bakt inn i
    `build_workbook.py` (`_recenter_price_shifts`, idempotent fra HIST_SHIFTS).

## Verifikasjoner (må holdes ved endringer)

- Kontrollkolonnen i Statisk modell = 0 hvert år (basis == NB26 SNKS).
- Inntekter - kostnader == Formue-fanens NKS på maskinpresisjon (1e-16).
- Excel-motor vs Python på identiske 2 000 trekk: avvik < 0,03 i persentiler.
- Middel (MC) ~= kumulativ basis: 4 823 mot 4 861 på de 2 000 faste trekkene
  (avvik 0,8 pst. = samplingsstøy i det faste utvalget; ~4 863 ved 200 000).
- Excel-motor vs. Python (mc_simulering.py) på identiske formler: eksakt match
  (verifisert med `formulas`-biblioteket, avvik 0).
- Reformulert modell: Excel-formlene mot Python på identiske trekk, verifisert
  med `formulas`-biblioteket på en strukturelt identisk testbok — største
  avvik 1,8e-12 i motoren, og persentil-/aggregatformlene i det synlige arket
  matcher eksakt. Kjør `python3 verifiser_reformulert.py`.
- Reformulert modell, forankringsidentiteter: median[prisfaktor] = 1 (eksakt,
  uavhengig av sigma) og E[prisfaktor] * Jensen-korreksjon = 1 (eksakt).
- Reformulert modell, gulvet: 0,0 pst. negative årsverdier med gulvet på, mot
  9,7-11,2 pst. uten. Gulvet har altså reell effekt og fjerner de negative
  tallene som var den opprinnelige innvendingen.
- Reformulert modell, P50 mot basis: kumulativ P50 4 990 mot basis 4 861
  (+2,7 pst.) i medianforankringen; sum av årsmedianer 4 943. Avviket er
  simuleringsstøy pluss at medianen av en sum ikke er summen av medianer.
- recalc uten formelfeil (279 000 formler; 158 000 i den gamle MC-motoren,
  120 000 i MC-motor-R).

## Kjente feller i tallgrunnlaget (funnet og løst — ikke gjeninnfør dem)

- "Faste priser"-kostnadsradene i NB26-arbokens Formue-fane (rad 54/57) er
  IKKE løpende/deflator — de ligger ~24 pst. lavere (egen basis). Riktig
  realkostnad = løpende utgifter (rad 59) / deflator (rad 44, basisår 2026).
- Formue-fanens header sier "2025-kroner", men deflatoren er 1,0 i 2026:
  serien er 2026-kroner.
- Sokkeldirektoratets basistall (Ressursrapport fig. 3.2) avviker litt fra
  NB26 (annen årgang). NB26 er eneste tallgrunnlag; SD brukes kun til
  totalbanene høy/lav (fig. 1.10).
- Skaleringsfeil å unngå: vekstfaktor fra C til D er (D-C)/C, ikke (D-C)/D.
- De rå historiske prisskiftene var IKKE sentrert på NB26 (geo-senter olje
  0,87, gass 1,08) — de bar med seg den historiske medianens skjevhet. Nå
  re-sentrert. Ikke gjeninnfør rå P90/P10 som skift uten sentrering.

## Sentrale antakelser og forbehold (i prioritert rekkefølge)

1. Konstant ressursmiks i høy/lav (SD har ikke splitten; kvantifisert:
   +/- 10 pp gassandel flytter NPV +/- 242 mrd. på 3 068 — annenordens).
2. Ingen tilbudsrespons: negative SNCF-år (ca. 10 pst. av observasjonene,
   sent i perioden) overdriver nedsiden. Presedens finnes (negative påløpte
   petroleumsskatter i 2020).
3. Forventningsforankring: NB26-banen er FORVENTNINGSbanen, og simuleringen
   er forankret slik at E[SNCF] = NB26-basis i både pris og volum. Pga.
   lognormal høyreskjevhet ligger MC-MEDIANEN noe UNDER middelet/basis (kum.
   median ~4 606 mot middel ~4 823 på de 2 000 faste trekkene) — det er
   statistikk, ikke feil.
4. Valutakurs implisitt i prisbanene.
5. Kalibrering på 28 årsobservasjoner uten ekstern kryssjekk. Sigma
   (0,2325/0,3856) har ~14 pst. relativ standardfeil; kappa er mer usikker og
   nedadbiaset på kort utvalg. Punktestimatene brukes som sentrale;
   estimeringsusikkerheten er dokumentert (følsomhet på sigma/kappa utsatt).

## Nøkkeltall (2 000 sim., frø 2026)

- 3x3 NPV (3 pst.): basis/basis 3 753; spenn 33 (høy vol/lav pris) til
  12 524 mrd. (re-sentrerte prisskift). NB: de dype negative hjørnene i den
  gamle versjonen (-322) var delvis artefakt av usentrerte skift. Reell
  netto-negativ nedside fanges av MC-viften (~10 pst. av årene) og av
  tilbudsrespons-varianten (utsatt).
- MC NPV 3 pst. (forventningsforankret): P10 1 782 / P50 3 564 / P90 5 859,
  middel 3 712 mrd. (middel = basis; median under pga. høyreskjevhet).
- Akkumulert 2026-2050: P10 2 256 / P25 3 268 / P50 4 606 / P75 6 037 /
  P90 7 680 mrd.
- SVG-figurene er regenerert med de forventningsforankrede tallene
  (`lag_figurer.py`). Middelverdi ~= basis, median under (høyreskjevhet).

### Reformulert modell (2 000 faste trekk, frø 2026, sigma 0,393/0,490)

Basis: kumulativ 4 861, NPV 3 pst. 3 753 mrd.

| | P10 | P25 | P50 | P75 | P90 | Middel |
|---|---|---|---|---|---|---|
| Kumulativ, medianforankret | 646 | 2 399 | **4 990** | 8 538 | 12 993 | 6 075 |
| NPV 3 pst., medianforankret | 576 | 1 923 | 3 858 | 6 505 | 9 728 | 4 642 |
| Kumulativ, forventningsforankret | 283 | 1 582 | 3 935 | 7 208 | 11 202 | **4 997** |
| NPV 3 pst., forventningsforankret | 261 | 1 314 | 3 083 | 5 487 | 8 396 | 3 832 |

- Medianforankret: P50 +2,7 pst. mot basis, middel +25,0 pst.
- Forventningsforankret: P50 -19,1 pst., middel +2,8 pst.
- 0,0 pst. negative årsverdier (gulvet virker; 9,7-11,2 pst. uten).
- Impliserte priser, medianforankret: olje P10 41 / P50 68 / P90 112 USD/fat;
  gass P10 3,0 / P50 5,7 / P90 10,8 USD/MMBtu.
- IEA-scenariene i denne viften: STEPS (76 USD) faller på P61, NZE (25 USD) på
  P0,5. Begge tall er UVERIFISERTE søketreff — Annex A kunne ikke hentes.
- NB26s egen formuesberegning (statens del, 2026-2090, 3 pst.): 4 721 mrd.
  Differansen mot vår NPV (3 753) er halen 2051-2090 (968 mrd. i nåverdi).

## Naturlige neste steg

- Gjør byggingen reproduserbar: et `build_workbook.py` som regenererer hele
  arbeidsboken fra input-JSON, slik at endringer kan versjonsstyres som kode
  i stedet for binærfil-erstatning.
- Tilbudsrespons-variant (gulv/nedstengingslogikk) som følsomhet.
- Native Excel-diagrammer i arbeidsboken (vifte som persentillinjer).
- Be Sokkeldirektoratet om ressurssplitt for mulighetsbildene er avklart
  som IKKE mulig — de har den ikke.
