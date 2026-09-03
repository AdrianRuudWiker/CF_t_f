# Full gjennomgang av modellen — 02.09.2026

Etterprøving av alle valg i SNCF-modellen, på brukerens forespørsel etter at
Excel-kravet falt bort. Alt under er REESTIMERT eller REGNET PÅ NYTT fra
kildedataene, ikke gjengitt fra tidligere dokumentasjon.

Datagrunnlaget som er brukt i gjennomgangen:
`Mulighetsbilde Petroleum.xlsx`, fanene KVARTS (historiske prisserier
1997-2090, rad 24-31), Formue (SNKS og formuesberegning, rad 84 og 93-103)
og Skiftberegning (marginalskatt og prisgjennomslag, ikke brukt i modellen).

---

## Del 1. Valg som holder — etterprøvd og bekreftet

### 1.1 Estimeringen er gjort på NOK-serien, ikke USD. Riktig.
Kontantstrømmen er i kroner, så prisusikkerheten skal måles i kroner. Kronen
demper: standardavviket i årlige logendringer er 0,288 for olje i USD mot
0,249 i NOK, altså 13 pst. lavere. For gass er dempingen 5 pst.

Reestimering av AR(1) på log realpris 1997-2024, NOK-serien:

| | kappa reestimert | dokumentert | sigma reestimert | dokumentert |
|---|---|---|---|---|
| olje | 0,2082 | 0,2116 | 0,2371 | 0,2325 |
| gass | 0,3271 | 0,3304 | 0,3933 | 0,3856 |
| korrelasjon | 0,6735 | 0,6742 | | |

Persentilforholdene reproduseres EKSAKT på NOK-serien: olje P90/P50 = 1,4305
og P10/P50 = 0,5230, gass 2,0153 og 0,5747. På USD-serien blir de 1,7864 og
1,6651 — altså helt andre tall. Kalibreringen er gjort på riktig serie.

De små restavvikene i sigma (2 pst.) skyldes trolig frihetsgradkonvensjon.
Ikke vesentlig, men verdt å vite at tallene ikke er bit-identiske.

### 1.2 NGL følger oljen. Godt underbygget.
Korrelasjon i årlige logendringer: 0,945 mot olje, 0,593 mot gass.
Regresjonskoeffisient på olje: 1,05. Dette er den best underbygde antakelsen
i modellen.

### 1.3 Pris-volum-korrelasjon = 0. Empirisk forsvarlig.
Korrelasjon mellom prisendring og produksjonsendring, 1997-2024:

| lag | 0 år | 5 år | 8 år | 10 år |
|---|---|---|---|---|
| korrelasjon | −0,10 | −0,27 | −0,11 | +0,07 |

Ingen systematisk sammenheng i dataene. Teorien sier at høy pris gir
investeringer som gir volum med lag, men på norsk sokkel dominerer
feltmodning. Å sette korrelasjonen til null er forsvarlig.

### 1.4 Volumbanene har termstruktur, og modellen bruker den riktig.
SDs mulighetsbilder som forhold mot basis: 1,01-1,02 i 2026, 0,73-1,24 i
2036, 0,19-1,84 i 2050. Usikkerheten vokser med horisonten slik den skal.
(Se likevel 2.5 om hvordan spennet brukes.)

### 1.5 De to kalibreringene er internt konsistente.
Persentilforholdene og AR(1)-prosessens stasjonære standardavvik skal være
samme tall for en stasjonær prosess. Olje: 0,388 mot 0,393 (+1 pst.).
Gass: 0,532 mot 0,490 (−8 pst.). De stemmer.

**Dette gir samtidig den presise diagnosen av dagens prismodell:** den
persistente regimefaktoren ER AR(1)-prosessens langsiktige fordeling, pålagt
allerede fra år 1. Oppbyggingen mot den fordelingen er hoppet over. Det er
hele mangelen — ikke nivået på usikkerheten, men fordelingen av den over tid.

---

## Del 2. Problemer funnet i gjennomgangen

### 2.1 Vi kan ikke avvise at prisen er en random walk
Dickey-Fuller-test på log realpris 1997-2024:

| | phi | standardfeil | t mot phi = 1 | konklusjon |
|---|---|---|---|---|
| olje | 0,794 | 0,108 | −1,91 | kan ikke avvise |
| gass | 0,629 | 0,150 | −2,47 | kan ikke avvise |

Kritisk verdi er om lag −3,0 på 5 pst. nivå. **Reversjon mot normalen er en
antakelse vi legger inn, ikke et funn i dataene.** Det er en helt legitim
antakelse — økonomisk teori for råvarer med tilbudsrespons støtter den — men
den må presenteres som antakelse.

### 2.2 Reverteringsfarten er nedadbiasert, og korreksjonen er stor
OLS på AR(1) undervurderer phi systematisk i korte utvalg. Kendalls
tilnærming, skjevhet ≈ −(1+3·phi)/T:

| | phi (OLS) | halveringstid | phi (bias-korrigert) | halveringstid |
|---|---|---|---|---|
| olje | 0,794 | 3,0 år | **0,919** | **8,2 år** |
| gass | 0,629 | 1,5 år | 0,736 | 2,3 år |

Oljens halveringstid nesten tredobles. Dette er direkte relevant: det er
forskjellen mellom «prissjokk vasker ut på tre år» og «prissjokk varer et
tiår», og det avgjør hvor mye regimerisiko modellen har.

### 2.3 Reverteringsfarten er målt mot feil attraktor
AR(1) er estimert rundt det historiske gjennomsnittet: 92 USD/fat for olje og
9,8 USD/MMBtu for gass. Modellen bruker farten til å revertere mot
NB26-BANEN, som ligger på 68 USD og 5,7 USD. Estimatet svarer på «hvor fort
går prisen tilbake til 92», og brukes som «hvor fort går den tilbake til 68».
At det overføres er en antakelse som ikke er dokumentert.

### 2.4 «Olje og gass er frikoblet siden 2010» stemmer ikke i dataene
Dette er den dokumenterte begrunnelsen for egen gassdynamikk. Korrelasjon i
årlige logendringer: 0,643 i 1998-2010, **0,774** i 2011-2024. Samvariasjonen
gikk OPP, ikke ned.

Den kontraktsmessige frikoblingen fra oljeindeksering til hubprising er reell,
men den reduserte ikke den statistiske samvariasjonen — begge drives av felles
makro- og energietterspørselssjokk. Begrunnelsen bør omformuleres.

Samtidig: modellen setter korrelasjonen til 0,60 for hånd, mens den estimerte
residualkorrelasjonen er 0,674 og samvariasjonen i den siste perioden 0,774.
Sigma avledes fra data, men rho gjettes. Det er inkonsekvent.

### 2.5 Den triangulære volumvekten krymper SDs spenn til det halve
Vekten w er triangulær på [−1, 1], og SDs høy- og lavbane treffes bare ved
w = ±1, som har tetthet null. Resultat i 2050:

| | lav | høy |
|---|---|---|
| SDs mulighetsbilder | 0,19 | 1,84 |
| Modellens volum-P10/P90 | 0,64 | 1,46 |

Sannsynligheten for å komme forbi halvveis mot høybanen er 13 pst. Modellen
bruker altså under halvparten av SDs oppgitte spenn som sitt 80 pst.-intervall.
Om det er riktig avhenger av om SDs høy og lav er ment som ytterpunkter eller
som et sannsynlig spenn — det må avklares mot SD, og valget må dokumenteres.

### 2.6 Kostnadsmodellen har to ulike antakelser, og bare den ene er vår
NB26s egen basisbane har STIGENDE enhetskostnad: fra 1 736 til 2 413 mill. kr
per mill. Sm3 o.e. fra 2026 til 2050, altså +39 pst., eller +1,78 pst. per år.
Halefeltene er dyrere per enhet.

Modellen skalerer likevel kostnadene proporsjonalt med volumfaktoren, altså
konstant enhetskostnad PÅ TVERS av volumbaner. I lavvolumbanen faller
kostnadene like mye som volumet. Faste driftskostnader på produserende felt
faller ikke slik, så nedsiden burde vært verre.

Kvantifisert med en fast kostnadsandel som ikke skalerer:

| fast andel | kumulativ P10 | P50 | P90 |
|---|---|---|---|
| 0 pst. (dagens) | 718 | 4 983 | 12 712 |
| 30 pst. | 713 | 4 968 | 12 778 |
| 50 pst. | 719 | 4 969 | 12 828 |

Nesten ingen effekt — men bare fordi **gulvet maskerer den**. I den verdenen
der kostnadsstrukturen betyr noe, er nettoen allerede gulvet til null. Det er
verdt å merke seg: gulvet gjør modellen ufølsom for en antakelse som ellers
ville vært viktig, og det er en skjult kobling mellom to valg.

### 2.7 Gulvet virker på aggregatet, ikke per felt
`MAX(sum over alle felt, 0)` er ikke det samme som `sum over felt av
MAX(felt, 0)`. I virkeligheten stenger enkeltfelt ned mens andre fortsetter.
Aggregatgulvet lar tapsfelt fortsette så lenge summen er positiv, og
undervurderer dermed tilbudsresponsen. Retningen på feilen er kjent, størrelsen
ikke — den krever feltnivådata modellen ikke har.

### 2.8 2 000 trekk gir merkbar simuleringsstøy
Spredning i resultatet over 60 ulike frø, kumulativ 2026-2050:

| | snitt | st.avvik mellom frø |
|---|---|---|
| P10 | 724 | 87 mrd. (11,9 pst.) |
| P50 | 5 040 | 147 mrd. (2,9 pst.) |
| P90 | 12 615 | 305 mrd. (2,4 pst.) |

Valget av frø flytter P10 med rundt 90 mrd. Antallet var satt til 2 000 fordi
trekkene måtte ligge som celler i et regneark. Med Python er 200 000 gratis.

---

## Del 3. Alternativer å vurdere

### 3.1 Prisprosess
- **To faktorer, begge reverterende** (anbefalt): rask syklisk med
  halveringstid ~3 år pluss langsom nivåfaktor med halveringstid 20-30 år.
  Gir termstruktur, avgrenset 2050-bånd og ekte regimerisiko. Kanonisk form er
  Schwartz-Smith.
- **Bias-korrigert AR(1)**: enkleste forbedring, halveringstid 8 år for olje.
  Løser mye av regimerisikoen uten ny modellstruktur.
- **Regimeskiftmodell** (Markov): to tilstander, høy og lav pris, med
  overgangssannsynligheter. Nær brukerens mentale modell, men 28 observasjoner
  er for lite til å estimere overgangsmatrisen.
- **Blokk-bootstrap på historiske baner**: ingen parametrisk form, bevarer
  faktisk observert persistens og skjevhet. Svakhet: kan bare gjenskape
  fortiden, og fortiden har ingen energiomstilling.

### 3.2 Volumusikkerhet
- Tolke SDs høy/lav som P10/P90 i stedet for ytterpunkter (skalere w).
- Behandle de tre banene som diskrete scenarier med eksplisitte
  sannsynligheter i stedet for en kontinuerlig interpolasjon.
- Modellere reserveusikkerhet direkte fra Sodirs ressursregnskap, med
  uoppdagede ressurser som egen fordeling.

### 3.3 Statsandelen
Kildefilen har en fane `Skiftberegning` med marginalskattesats,
gassprisgjennomslag og en full skiftmodell til 2090 — altså NB26s eget verktøy
for hvordan statens inntekter responderer på prisendringer. Modellen bruker
den ikke; den holder statsandelen fast per år uansett pris. Med 78 pst.
marginalskatt pluss SDØE er det ikke opplagt at gjennomsnittsandelen og
marginalandelen er like. **Dette bør kryssjekkes mot Skiftberegning-fanen** —
det er en konkret, tilgjengelig kilde.

### 3.4 Diskonteringsrenten
3 pst. er valgt fordi det er NB26s formuesberegning og SPUs forventede
realavkastning. Et alternativ som ikke er drøftet: kontantstrømmen er RISIKABEL
og samvarierer med verdensøkonomien, så en risikojustert rente er
forsvarlig — det er nettopp begrunnelsen for 4 pst. i R-109 og i PM-tallet.
Valget mellom 3 og 4 pst. er ikke bare en konvensjonsforskjell, det er et
spørsmål om nåverdien skal være risikojustert. Bør drøftes eksplisitt.

### 3.5 Arkitektur, nå som Excel-kravet er falt
- Simuleringen flyttes til Python med fritt antall trekk; Excel beholdes som
  presentasjonslag med resultattabeller, ikke som regnemotor.
- Parameterusikkerhet kan tas med: bootstrap på sigma, kappa og korrelasjon,
  slik at viften også dekker estimeringsusikkerhet og ikke bare prosessrisiko.
- Gradvis nedstenging basert på balanseprisfordelingen (deck slide 14) i
  stedet for et hardt aggregatgulv.
- Kjøringene versjonsstyres som kode med frø og parametre, og resultatene
  eksporteres. Da er hele leveransen reproduserbar fra kommandolinjen.

---

## Del 4. Prioritert rekkefølge

1. **Prisprosessen.** Den bestemmer forankringen og kalibreringen, så den må
   avgjøres først. Anbefaling: to faktorer, med bias-korrigert reversjon i den
   sykliske og et nivåbånd satt ved skjønn.
2. **Volumspennet.** Avklar om SDs høy/lav er ytterpunkter eller P10/P90.
   Effekten er stor og valget er udokumentert.
3. **Statsandelen mot Skiftberegning-fanen.** Konkret kryssjekk mot en kilde
   vi allerede har.
4. **Diskonteringsrenten.** Drøft risikojustering eksplisitt, ikke som
   konvensjon.
5. **Arkitektur og antall trekk.** Enkelt når 1-4 er avklart.
6. **Kostnadsstruktur og gulv per felt.** Lavest prioritet, siden gulvet i dag
   maskerer effekten — men koblingen bør dokumenteres.
