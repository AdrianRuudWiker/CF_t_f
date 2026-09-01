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

- `Kontantstromsmodell_petroleum.xlsx` — hovedleveransen. Seks synlige ark
  pluss skjult motor:
  - **Forutsetninger**: alt tallgrunnlag (blå celler = input, svarte =
    formler) og parametre i B4-B15 (prisskift, rente, sigma, kappa,
    korrelasjon). Årstabell rad 17-42 (2025-2050), kolonner A-P.
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
  - **Dokumentasjon**: antakelser, begrensninger, kilder.
- `mc_simulering.py` — valgfri Python-referanse; leser parametre fra
  arbeidsboken. 10 000 simuleringer. Brukes til verifikasjon.
- `build_workbook.py` — regenererer MC-motoren fra input og baker inn
  forventningsforankringen (Jensen på pris, mean-1 på volum). Bevarer de
  faste trekkene og de synlige arkene.
- `lag_figurer.py` — regenererer de tre SVG-figurene fra de forventnings-
  forankrede tallene (FINs designprofil), lest fra de 2 000 faste trekkene.
- `viftefigur_sncf.svg` — tetthetsvifte for årlig SNCF (gradert opasitet,
  kuttet ved 5-95-persentil, median hvit med mørk kontur, NB26-basis rød
  stiplet).
- `akkumulert_sncf.svg` — akkumulert SNCF med persentilbånd og sluttverdier.
- `fordelinger_sncf.svg` — histogrammer (SNCF 2035 og kumulativ) med modus,
  median, middelverdi og basisbane markert.

## Modellarkitektur

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
- recalc uten formelfeil (159 000 formler).

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
