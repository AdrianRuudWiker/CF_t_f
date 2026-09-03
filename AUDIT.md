# AUDIT — gjennomgang av SNCF-modellen

Uavhengig, lesende gjennomgang av repoet `AdrianRuudWiker/CF_t_f`, utført
03.09.2026. Ingen filer er endret; denne rapporten er den eneste nye filen.
Alle tall under er regnet ut på nytt fra kildedataene i denne økten, ikke
gjengitt fra repoets egen dokumentasjon. Der jeg gjengir andres tall, står det
eksplisitt.

Rapporten er skrevet på bokmål etter arbeidsreglene i repoet. Si fra hvis du
vil ha den på engelsk.

**Kort oppsummering.** Datagrunnlaget er solid og sporbart, og basisbanen
reproduserer Nasjonalbudsjettet 2026 eksakt. Selve usikkerhetsmodellen har tre
alvorlige svakheter: prisviften har ingen termstruktur (2026 er like usikkert
som 2050), nåverdiviften er like bred som årsviften fordi det bare trekkes ett
prissjokk per simulering, og volumbåndet er bygget på et forholdstall mellom to
ulike årganger. Sentralanslaget treffer ikke 4 800 mrd. og kan ikke gjøre det —
men det er en årgangsforskjell mellom PM og NB26, ikke en modellfeil.
Anbefalingen er å beholde datalaget og skrive om modellen fra bunnen i Python.

---

## 1. Inventar

### 1.1 Grener — hvor «modellen» faktisk ligger

Dette er det første du må vite, fordi svaret på «hva ligger i repoet» avhenger
av hvilken gren man ser på.

| gren | commits | innhold |
|---|---|---|
| `main` | 3 (alle «Add files via upload») | **bare den gamle modellen.** Arbeidsboken der har fem synlige ark og én skjult motor. Ingen av Python-skriptene bortsett fra `mc_simulering.py`. Ingen HANDOFF, ingen GJENNOMGANG. |
| `claude/claude-md-review-verify-70a7je` | +4 | mellomstasjon: forventningsforankring, re-sentrerte prisskift, første prototype av den reformulerte modellen |
| `claude/sncf-anchor-calibrate-smb2ii` | +11 | **alt det faktiske arbeidet.** Reformulert modell bygget inn i arbeidsboken, utvidelse til 2060, broen mot 4 800, verifikasjonssuite, GJENNOMGANG.md |

En kollega som klonet `main` i dag ville altså få en modell som er forlatt, og
ikke se noe av arbeidet fra 02.09. Det bør ryddes uansett hva dere ellers
bestemmer.

### 1.2 Datafiler

| fil | hva | dekning og enheter | kilde og sporbarhet |
|---|---|---|---|
| `Mulighetsbilde Petroleum.xlsx` (1,6 MB) | **den egentlige primærkilden.** Intern NB26-arbeidsbok. Fanene KVARTS (prisserier og produksjon 1997-2090), Formue (produksjon, priser, kostnader, SNKS, formuesberegning 2007-2090), Skiftberegning (marginalskatt, SDØE-andeler, prisgjennomslag 2001-2090), Petoro, Investments, NGL-pris | mill. kr løpende og faste, mill. Sm³ o.e., kr/Sm³ o.e. | Finansdepartementet/Nasjonalbudsjettet 2026. **Intern, ikke offentlig.** CLAUDE-filens egen regel sier at den ikke skal ligge i repoet; den ligger der likevel, bevisst valgt |
| `ressursrapport-resource-report-2026-bakgrunnsdata-numbers.xlsx` (213 kB) | Sokkeldirektoratets bakgrunnstall, 25 figurark | mill. Sm³ o.e. per år | Sokkeldirektoratet, Ressursrapport 2026. Publisert og siterbar. **Bare Fig. 1.10 (basis/høy/lav totalproduksjon) er i bruk.** Fig. 3.2 har olje/NGL/kondensat/gass-splitt, men bare til 2035 |
| `Kontantstromsmodell_petroleum.xlsx` (5,8 MB) | modellen | 2025-2060 | avledet. Alt tallgrunnlag er **limt inn som tall** i Forutsetninger — ingen formellenke tilbake til kildefilene |
| `Statens petroleumsformue til ekspertrådet for SPU (002).pptx` (4,7 MB) | Per Valvatne (ED), 19.03.2026, 15 slides | — | autoritativ for prisforutsetninger (slide 5), mulighetsbildene (slide 10) og balansepriser (slide 14). Det er her tallet 4 800 kommer fra |

### 1.3 Skript

| fil | status | hva den gjør |
|---|---|---|
| `mc_reformulert.py` | **LEVENDE** — Python-referansen for den ønskede modellen | Leser Forutsetninger, simulerer, rapporterer begge forankringer. Kjørt: virker |
| `build_reformulert.py` (39 kB) | **LEVENDE** | Bygger «Reformulert vifte», skjult «MC-motor-R», «Utvidelse 2060» og parameterblokken inn i arbeidsboken |
| `verifiser_reformulert.py` | **LEVENDE** — og den beste enkeltfilen i repoet | Bygger en strukturelt identisk testbok og evaluerer Excel-formlene mot Python med `formulas`. Kjørt: alle kontroller passerer, største avvik 1,8e-12 |
| `kalibrering.py` | **HALVDØD** | Løser sigma fra måltall og finner forsoningspunktet. Hybrid-veien er død kode: IEA-tallene finnes ikke |
| `lag_figur_reformulert.py` | LEVENDE | Genererer `reformulert_vifte.svg` og `reformulert_akkumulert.svg` |
| `mc_simulering.py` | **DØD** — gammelt spor | OU-prosess, forventningsforankret. Kjørt: virker, men gir en annen modell enn den ønskede |
| `build_workbook.py` | **DØD** — gammelt spor | Bygger den gamle MC-motoren |
| `lag_figurer.py` | **DØD** — gammelt spor | Genererer de tre gamle SVG-ene |

### 1.4 Arbeidsboken — arkene

| ark | status | formler |
|---|---|---|
| Forutsetninger | levende, felles datalag for begge spor | 141 |
| Statisk modell (3×3) | **død** — forlatt 02.09., står igjen | 289 |
| Miksfølsomhet | **død** | 80 |
| Monte Carlo + MC-motor (skjult) | **død** — gammel OU-motor | 179 + 158 200 |
| Reformulert vifte + MC-motor-R (skjult) | levende | 414 + 172 210 |
| Utvidelse 2060 | levende | 242 |
| Dokumentasjon | levende, men har feil (se 3.9) | 0 |

**331 755 formler til sammen. Null bufrede verdier.** Dette er verdt et eget
avsnitt: fordi arbeidsboken sist ble skrevet av `openpyxl`, inneholder den
ingen beregnede verdier i det hele tatt. Åpner du den i Excel, regner den seg
opp; men ingen annen leser — ikke Python, ikke en nettleser, ikke en
konverteringstjeneste — kan hente ut ett eneste resultat. Alle tall i
dokumentasjonen kommer fra Python-referansen, ikke fra arbeidsboken.

### 1.5 Figurer

De fem SVG-ene er generert med matplotlib. Tre av dem (`viftefigur_sncf.svg`,
`akkumulert_sncf.svg`, `fordelinger_sncf.svg`) hører til det døde sporet.
FIN-fargene er på plass (#181c62, #4156a6, #5b91cc, #f15d61, #ededee), men
**skrifttypen er DejaVu Sans, ikke Liberation Sans** — 214 forekomster i
`reformulert_vifte.svg`. Liberation Sans ligger faktisk installert i
containeren (`/usr/share/fonts/truetype/liberation/`), så dette er bare et
feilvalg i skriptene, ikke en begrensning.

### 1.6 Hardkodede tall

Regelen i `CLAUDE (1).md` er «aldri hardkod resultater der en formel kan stå».
Den holdes for beregninger, men ikke for input. Følgende er skrevet inn som
tall og har ingen levende kobling til kilden:

| hvor | verdi | kommentar |
|---|---|---|
| `build_workbook.py:52` | `HIST_SHIFTS` = 1,4305 / 0,523 / 2,0153 / 0,5747 | historiske persentilforhold. **Jeg har reberegnet dem fra KVARTS 1997-2024 og de stemmer eksakt.** Men de er frosset: oppdateres KVARTS, følger de ikke med |
| Forutsetninger B4:B7 | 1,6538 / 0,6047 / 1,8726 / 0,5340 | de samme, re-sentrert på geometrisk senter. Reberegnet og bekreftet |
| Forutsetninger B11:B15 | sigma 0,2325/0,3856, rho 0,6742, kappa 0,2116/0,3304 | AR(1)-estimater. Jeg får 0,2371/0,3933, 0,6735, 0,2334/0,3961 ved reestimering — små avvik i frihetsgradkonvensjon, ikke vesentlig |
| Forutsetninger B49 | rho = 0,60 | **gjettet.** Estimatet er 0,674, og samvariasjonen 2011-2024 er 0,774. Sigma avledes fra data, rho gjettes — inkonsekvent |
| Forutsetninger B56 | 10,5 NOK/USD | **hardkodet valutakurs.** Basisbanens egen impliserte kurs er 10,18 (J42 = 4 480 kr/Sm³ o.e. ⇒ 70 USD/fat krever 10,18). Konsekvens: arkets kontrollcelle B57 viser 67,8 USD/fat mot deckets 70 |
| Forutsetninger B55, B58 | 6,2898 fat/Sm³, 5,7 USD/MMBtu | konverteringsfaktorer, greie nok |
| Utvidelse 2060 B13, B14 | 4 800 og deflatorjustering = 1 | **B14 = 1 er en udokumentert antakelse.** Se 3.4 |
| `kalibrering.py:47-48` | 70,0 og 5,7 | basispriser, duplisert fra arket |
| `mc_reformulert.py:80` | NZE 25 USD/fat | uverifisert søketreff, brukt i en kalibreringsvei som ikke kan bygges |
| Forutsetninger B18:N42 | hele årstabellen | limt inn fra NB26. Ingen formellenke, ingen versjonsmerking |

---

## 2. Hva modellen faktisk gjør

### 2.1 Kontantstrømmen — strukturell på inntektssiden, redusert form på skattesiden

Kjernen er én linje, per år:

```
SNCF_t = andel_t × MAX( volumfaktor_t × (volO_t·pO_t·Fo + volN_t·pN_t·Fo
                                       + volG_t·pG_t·Fg − kostnader_t), 0 )
```

Inntektssiden er strukturell: tre produksjonsserier (råolje, naturgass,
NGL/kondensat) ganget med tre prisserier i kr/Sm³ o.e., minus én samlet
kostnadsserie. Så langt er dette et ordentlig oppbygd regnestykke.

Skattesiden er ikke modellert. `andel_t` er **kalibrert per år** slik at
basisbanen reproduserer NB26s SNKS-anslag eksakt:

```
andel_t = SNKS_t / (inntekter_t − kostnader_t)
```

Den varierer fra 0,868 til 1,008 over 2026-2050, med snitt 0,934. At den er
over 1,0 i to år (2030 og 2049) viser at dette ikke er en «andel» i noen
meningsfull forstand — det er en residual som fanger opp periodisering
(påløpt mot betalt skatt), utbytte fra Equinor og alt annet på én gang.

Basiskontrollen holder likevel eksakt. Jeg regnet den ut på nytt: kumulativ
basis 2026-2050 = **4 861 mrd.**, NNV 3 pst. = **3 753 mrd.**, NNV 4 pst. =
**3 477 mrd.** Identisk med NB26s egen SNKS-bane.

### 2.2 Prisprosessen — to forskjellige, i samme arbeidsbok

Det ligger **to uforenlige prisprosesser** i boken samtidig:

**Gammelt spor (ark «Monte Carlo», skjult «MC-motor»):** Ornstein-Uhlenbeck på
logpris rundt NB26-banen, med årlige sjokk. Estimert med AR(1) på realpriser
1997-2024 i NOK: kappa olje 0,2116 (halveringstid ~3 år), kappa gass 0,3304,
residual-sigma 0,2325/0,3856, residualkorrelasjon 0,6742.

**Levende spor (ark «Reformulert vifte», skjult «MC-motor-R»):** ikke en
prosess i det hele tatt, men **ett persistent lognormalt sjokk per simulering**
som gjelder hele horisonten:

```
Fo = EXP(sigma_o · z1),   Fg = EXP(sigma_g · (rho·z1 + √(1−rho²)·z2))
```

sigma avledes av persentilforholdene som `LN(P90/P50)/z₉₀`, som gir
**sigma_olje 0,3926 og sigma_gass 0,4895**. rho settes til 0,60 for hånd. NGL
følger oljesjokket fullt ut — den best underbygde antakelsen i modellen
(korrelasjon 0,945 i årlige logendringer mot olje).

Olje og gass modelleres altså separat, med egen sigma og korrelert sjokk.

### 2.3 Produksjonsusikkerhet — stokastisk, men fra tre baner

Ett trekk per simulering: `w ~ Triangular(−1, 0, 1)`. Ved w = 0 blir volumet
basis; ved w = +1 treffes Sokkeldirektoratets høybane, ved w = −1 lavbanen;
imellom interpoleres lineært. Faktoren deles på sin egen forventning
`1 + (fh + fl − 2)/6` slik at volumet er forventningsforankret.

Produksjonen ER splittet i væske og gass — olje, gass og NGL hver for seg fra
NB26. Men usikkerheten virker på **totalen**: høy- og lavbanen fra SD er bare
totaltall, og modellen antar samme ressursmiks i alle tre banene. Den
antakelsen er dokumentert og følsomheten er tallfestet (±10 pp gassandel
flytter NNV ±242 mrd.).

### 2.4 Korrelasjoner

| par | verdi | hvordan satt |
|---|---|---|
| olje–gass (pris) | 0,60 | **gjettet.** Estimatet er 0,674 |
| pris–volum | **0** | pålagt. Empirisk forsvart: målt korrelasjon mellom prisendring og produksjonsendring 1997-2024 er −0,10 samtidig, −0,27 med fem års lag |
| NGL–olje | **1,0** | NGL følger oljesjokket identisk |
| NOK/USD | **ingen** | valutakursen er implisitt i NB26s kroneprisbaner, og eksplisitt bare som en hardkodet 10,5 for visning |

### 2.5 Diskontering og deflatering

Diskonteringen skjer med Excels `NPV()`, som diskonterer første beløp én
periode. Med første beløp i 2026 gir det en nåverdi **datert 2025** — samme
konvensjon som PM-tallet. Det er riktig gjort.

Hovedrenten er 3 pst. (NB26s formuesberegning og SPUs forventede
realavkastning), med 2 og 4 pst. som følsomhet. 4 pst. brukes bare i
sammenligningen mot 4 800.

Deflateringen er **NB26s egen deflator** (Formue rad 44, basisår 2026), ikke
statsbudsjettets utgiftsdeflator. Kostnadene er regnet som løpende utgifter
(rad 59) delt på den deflatoren. Jeg har verifisert at modellens kostnadskolonne
matcher dette eksakt. Dette er ikke nødvendigvis samme deflator som PM bruker —
se 3.4.

### 2.6 Hvor viften kommer fra

Persentiler av en Monte Carlo, 2 000 simuleringer med **faste trekk lagret som
tall i celler**. Ikke et rutenett. 3×3-rutenettet finnes fortsatt i «Statisk
modell», men er forlatt som designvalg.

Antallet 2 000 er ikke en statistisk vurdering — det er så mange rader Excel
tåler med 172 000 formler oppå. Jeg målte frøavhengigheten over 60 frø:
kumulativ P10 varierer med **9,3 pst.** mellom frø (standardavvik 67 mrd. rundt
et snitt på 721). P50 og P90 varierer med 2,4 pst.

---

## 3. Revisjon

### 3.1 Termstrukturen — det største problemet

Du spør om prisprosessen blåser opp på 20-35 års sikt. Svaret er nei — den
gjør det motsatte, og det er verre.

Standardavvik i log oljepris etter horisont:

| horisont | dagens modell (persistent regime) | gammel OU | ren random walk |
|---|---|---|---|
| 1 år | 0,393 | 0,233 | 0,233 |
| 5 år | 0,393 | 0,360 | 0,520 |
| 10 år | 0,393 | 0,376 | 0,735 |
| 25 år | 0,393 | 0,378 | 1,163 |
| 35 år | 0,393 | 0,378 | 1,375 |

Den impliserte oljeprisviften, basis 68 USD/fat:

| år | dagens modell | gammel OU | random walk |
|---|---|---|---|
| 2026 | **41 – 112** | 50 – 92 | 50 – 92 |
| 2035 | 41 – 112 | 42 – 110 | 27 – 174 |
| 2050 | 41 – 112 | 42 – 110 | **15 – 302** |

Din bekymring for random walk er berettiget — den gir P90 = 302 USD/fat i
2050 — men den er ikke i bruk. Problemet i den levende modellen er det
omvendte: **usikkerheten vokser ikke i det hele tatt.** Modellen sier at
oljeprisen i 2026 like gjerne kan bli 41 som 112 USD/fat, i et år der
terminkurven er kjent og produksjonen er i gang. Følgen på kontantstrømmen:
SNCF 2026 får P10 167 og P90 1 164 mrd. mot en basis på 521.

Dette er ikke en tilfeldig svakhet. Den persistente regimefaktoren ER
AR(1)-prosessens stasjonære fordeling, pålagt fra og med år 1. Oppbyggingen mot
den fordelingen er hoppet over.

### 3.2 Nåverdiviften diversifiserer ikke — og det er innebygd

Dette er samme feil sett fra en annen vinkel, og det er den som gjør mest
skade på tallene du skal presentere. Jeg kjørte begge prosessene på 200 000
trekk:

| | SNCF 2026 | SNCF 2035 | Kumulativ | NNV 3 pst. |
|---|---|---|---|---|
| **dagens modell** P10 | 167 | 34 | 722 | 632 |
| P50 | 539 | 218 | 5 017 | 3 886 |
| P90 | 1 164 | 527 | 12 652 | 9 551 |
| P90/P10 | 7,0 | 15,5 | **17,5** | **15,1** |
| **gammel OU** P10 | 249 | 31 | 3 029 | 2 362 |
| P50 | 528 | 217 | 5 638 | 4 327 |
| P90 | 943 | 534 | 9 192 | 6 971 |
| P90/P10 | 3,8 | 17,1 | **3,0** | **3,0** |

Målt som diversifiseringsgevinst — hvor mye smalere den kumulative fordelingen
er enn gjennomsnittet av årsfordelingene:

- dagens modell: **+8 pst.** (praktisk talt ingenting)
- gammel OU: **+56 pst.**

Du har helt rett i at nåverdien skal være strammere enn årsstrømmene. Dagens
modell gir deg ikke det, fordi det bare trekkes **ett** prissjokk per
simulering. Én lognormal variabel styrer alle 25 år, og da er summen like
usikker som leddene. Det er et bevisst designvalg («persistente regimer»), men
det er ytterpunktet: null utvasking over 25 år.

Sannheten ligger mellom 3,0 og 15-17 ganger. **Hele nedsiden i leveransen —
kumulativ P10 på 722 mrd. — er et resultat av dette valget, ikke av data.**

### 3.3 Pris–produksjon: hjørnet finnes, og det er like stort som uavhengighet tilsier

Jeg målte det direkte: sannsynligheten for at prisfaktoren ligger under sin
25-persentil **og** volumet i 2050 over sin 75-persentil er **6,3 pst.** — som
er nøyaktig 0,25 × 0,25. Uavhengigheten er reell, ikke bare nominell.

Din innvending er riktig, og den er sterkere enn den empiriske
nullkorrelasjonen antyder. Den historiske korrelasjonen måler produksjon fra
felt som allerede var bygget ut. Det er ikke det relevante spørsmålet for
2035-2050, når en stor del av produksjonen kommer fra prosjekter som ennå ikke
er besluttet. En lavprisverden der de prosjektene likevel bygges ut, er ikke en
sjeldenhet — den er en selvmotsigelse. Modellen produserer den i 6 pst. av
simuleringene.

Balanseprisgulvet demper det litt, men på feil sted: det virker på
kontantstrømmen etter at volumet er bestemt, ikke på investeringsbeslutningen.

### 3.4 4 800 mrd. — kontrollert, ikke reprodusert, og det er ikke modellens feil

Dette er kontrollert grundig i repoet allerede, og jeg har regnet det ut på
nytt uavhengig. Resultatene stemmer.

Broen på basisbanen, alt neddiskontert til 2025:

| | mrd. 2026-kr |
|---|---|
| 1. Modellens NNV 3 pst., 2026-2050 | 3 753 |
| 2. Effekt av rente 3 → 4 pst. | −276 |
| 3. Effekt av horisont 2051-2060 ved 4 pst. | +186 |
| 4. = Modellens NNV 2026-2060, 4 pst. | **3 663** |
| 5. PM-referanse | 4 800 |
| 6. Differanse | **−1 137 (−23,7 pst.)** |

Det avgjørende funnet er dette: **NB26s egen SNKS-bane gir samme svar.** Jeg
regnet `NPV(4 %; SNKS 2026:2060)` direkte på Formue rad 84 og fikk **3 671
mrd.** Modellen ligger 8 mrd. fra NB26 på deckets egen definisjon. Gapet mot
4 800 er altså **ikke** en modellfeil — det er en forskjell mellom PMs
kontantstrømbane og NB26s.

Ingen omdatering eller omhorisontering lukker gapet. På NB26s egen bane:

| definisjon | 4 pst. |
|---|---|
| 2026-2060, datert 2025 (deckets ordlyd) | 3 671 |
| 2025-2090, datert 2024 (som NB26s formuesberegning) | 4 294 |
| 2025-2090, datert 2025 | 4 466 |

Hva som ville lukket det: et **uniformt prispåslag på 13,2 pst.** (olje 77 i
stedet for 68 USD/fat), eller 31 pst. mer volum. Det er en helt plausibel
årgangsforskjell mellom PM 2024 og NB26 — PM ble laget med 2024-forutsetninger.

To ting som ikke er avklart:

1. **Deflatoren.** PM oppgir faste priser med statsbudsjettets
   utgiftsdeflator; modellen bruker NB26s deflator med basisår 2026. Cellen
   `Utvidelse 2060!B14` er satt til 1 uten begrunnelse. Er 4 800 i 2025-kroner,
   tilsvarer det **4 949** i modellens 2026-kroner, og gapet vokser til −1 286.
2. **Utvidelsen til 2060 var unødvendig.** NB26s egen bane går til 2090 for
   produksjon, priser, kostnader og SNKS. Ti år er ekstrapolert med geometriske
   rater når kilden lå i samme arbeidsbok. Ekstrapoleringen traff 2-4 pst. lavt,
   så den er validert — men den er også overflødig kompleksitet.

### 3.5 Gearing — fanget, og faktisk overdrevet

Din bekymring er at en flat prosentsats vil undervurdere asymmetrien. For
denne modellen er det motsatt vei: `andel_t` ganges med **nettoen**, ikke med
bruttoinntekten, så hele driftsleverasjen er med. Forholdet inntekt/netto
stiger fra 1,76 i 2026 til 3,55 i 2050 — modellen blir altså stadig mer
priselastisk utover i perioden, slik den skal.

Problemet er at den blir for elastisk. Kildefilens egen `Skiftberegning`-fane
oppgir marginalskattesats 78 pst. og SDØEs produksjonsandeler per år. Det gir
et marginalt statlig uttak av en inntektsendring:

| år | modellens `andel` | SDØE olje | marginalt uttak olje | inntekt/netto |
|---|---|---|---|---|
| 2026 | 0,971 | 0,178 | 0,819 | 1,76 |
| 2035 | 0,879 | 0,140 | 0,811 | 2,21 |
| 2050 | 0,968 | 0,108 | 0,804 | 3,55 |

Elastisiteten d ln SNCF / d ln oljepris:

| år | modellen | strukturelt (78 pst. + SDØE) | modell/struktur |
|---|---|---|---|
| 2026 | 0,87 | 0,74 | **1,19** |
| 2035 | 1,38 | 1,28 | 1,08 |
| 2050 | 2,43 | 2,02 | **1,20** |

Modellen overdriver altså priselastisiteten med 8-20 pst. Feilen oppstår fordi
`andel_t` er en **gjennomsnittsandel** brukt som om den var en **marginalandel**.
De sammenfaller ikke: gjennomsnittsandelen inneholder utbytte og
periodiseringseffekter som ikke skalerer med prisen.

**Og et funn til, som kan være større:** `Skiftberegning` oppgir
**gassprisgjennomslag = 0,50** for hele perioden 2001-2090. NB26s eget verktøy
antar altså at bare halvparten av en gassprisendring slår gjennom i den
realiserte kontantstrømmen. Modellen antar 100 pst. Gass er 32-51 pst. av
inntektene. Hvis de 50 prosentene skal tas på alvor, er gassbidraget til viften
omtrent dobbelt så bredt som det burde være. Jeg vet ikke om `Gassprisgjennomslag`
betyr det jeg tror — det er ett av spørsmålene til slutt.

### 3.6 Volumbåndet er bygget på et forholdstall mellom to årganger

Dette fant jeg ikke i repoets egen dokumentasjon, og det er en reell feil.

Volumfaktorene beregnes som `fh = totH/tot` og `fl = totL/tot`, der `totH` og
`totL` er Sokkeldirektoratets høy- og lavbane fra Ressursrapport 2026, mens
`tot` er **NB26s** basisproduksjon. De to årgangene har ulik basisbane:

| år | SDs egen basis | NB26s basis | avvik | `fh` i modellen | SDs eget forhold | `fl` i modellen | SDs eget forhold |
|---|---|---|---|---|---|---|---|
| 2026 | 238,9 | 236,4 | −1,0 pst. | 1,016 | 1,006 | **1,010** | 1,000 |
| 2028 | 229,0 | 218,6 | −4,6 pst. | 1,060 | 1,012 | **1,023** | 0,976 |
| 2035 | 161,1 | 161,8 | +0,4 pst. | 1,232 | 1,237 | 0,790 | 0,793 |
| 2040 | 123,0 | 128,9 | +4,8 pst. | 1,413 | 1,480 | 0,523 | 0,548 |
| 2050 | 91,8 | 86,0 | −6,3 pst. | **1,835** | 1,719 | **0,192** | 0,180 |

To konsekvenser:

1. **I 2026-2029 ligger «lavbanen» over modellens basis** (fl = 1,010 til
   1,023). Volumusikkerheten i de fire første årene er ensidig oppover —
   modellen kan ikke produsere et volum under basis i 2026. Det er ikke et
   modelleringsvalg, det er en artefakt av å blande to årganger.
2. **I 2050 er hele båndet blåst opp med 6,8 pst.** fordi nevneren er for
   liten.

Og oppå det kommer en motsatt feil: den triangulære vekten treffer SDs
ytterpunkter bare ved w = ±1, som har tetthet null. Modellens faktiske
volumfordeling i 2050 er P10 0,55 til P90 1,45, mot SDs oppgitte 0,19 til 1,84.
**Modellen bruker under halvparten av SDs spenn som sitt 80 pst.-intervall.**

De to feilene peker hver sin vei, ingen av dem er dokumentert som et valg, og
netto effekt er ikke opplagt.

### 3.7 Gulvet gjør modellen ufølsom for kostnadsstrukturen

Balanseprisgulvet `MAX(netto, 0)` binder oftere enn dokumentasjonen antyder.
Målt på 200 000 trekk:

| år | andel simuleringer som gulves |
|---|---|
| 2030 | 6,6 pst. |
| 2040 | 10,1 pst. |
| 2045 | 15,7 pst. |
| 2050 | **18,2 pst.** |

18,4 pst. av simuleringene har minst ett gulvet år. I 2050 er SNCF P10 nøyaktig
**0** — nedre kant av viften er gulvet, ikke økonomi.

Det har to følger. For det første maskerer gulvet kostnadsstrukturen: repoets
egen test viser at å gjøre 50 pst. av kostnadene faste knapt flytter noe, men
det er bare fordi nettoen allerede er gulvet i de tilstandene der det ville
betydd noe. For det andre virker gulvet på **aggregatet**, ikke per felt.
`MAX(Σ felt, 0)` er ikke `Σ MAX(felt, 0)` — i virkeligheten stenger enkeltfelt
ned mens andre går videre, så aggregatgulvet undervurderer tilbudsresponsen.

### 3.8 Forankringen — et reelt problem, håndtert på en måte som dobler leveransen

Prisfaktoren er lognormal, så median og forventning kan ikke begge være lik
basis. Valget er avklart som «vis begge», og arbeidsboken har derfor to
komplette persentilsett side om side.

Konsekvensen av valget er stor:

| | medianforankret | forventningsforankret |
|---|---|---|
| kumulativ P50 | 5 006 (+3,0 pst. mot basis) | 3 973 (−18,3 pst.) |
| kumulativ middel | 6 087 (+25,2 pst.) | 5 011 (+3,1 pst.) |

Jeg mener dette er riktig identifisert, men feil løst. Å vise to fullstendige
vifter tvinger leseren til å velge mellom to sett offisielle tall, og i et
notat til ekspertrådet er det ett spørsmål for mye. Poenget hører hjemme i én
fotnote: rapporter persentiler, ikke middelverdi, og opplys at middelet ligger
over NB26 fordi fordelingen er høyreskjev.

### 3.9 Mindre feil og inkonsistenser

- **Dokumentasjon-arket har seks duplikate avsnitt.** `build_reformulert.py`
  sin dokumentasjonssynkronisering er ikke idempotent — kjøres den to ganger,
  legges avsnittene inn på nytt.
- **Dokumentasjon rad 34 gjentar en påstand som er trukket tilbake.** Den sier
  at NB26 impliserer en hale etter 2050 verdt «om lag 968 mrd.». Repoets egen
  GJENNOMGANG viser at dette er feil (4 721 er `NPV(3 %; 2025:2090)` datert
  2024, så de 968 er i hovedsak 2025-kontantstrømmen på 684 mrd.). Rettelsen er
  gjort i markdown-filene, men ikke i arbeidsboken. **Arbeidsboken er det
  leseren får.**
- **NZE-sidescenarioet gir #N/A.** Kolonne O på «Reformulert vifte» og cellene
  B60-B63 er tomme plassholdere fordi IEA-tallene ikke lot seg hente. En
  arbeidsbok som leveres med #N/A i en synlig kolonne, blir ikke lest velvillig.
- **Filnavnet `CLAUDE (1).md`** — dokumentasjonen refererer til `CLAUDE.md`.
- **Impliserte priser stemmer ikke helt med decket.** Arkets kontrollcelle B57
  gir 67,8 USD/fat mot deckets 70, fordi valutakursen er satt til 10,5 mens
  banen impliserer 10,18.

### 3.10 Det som faktisk er kontrollert, og som holder

For balansens skyld — dette er verifisert og jeg fant ingen feil:

- Basisbanen reproduserer NB26s SNKS eksakt, alle 25 år.
- `verifiser_reformulert.py` kjører grønt: Excel-formlene regner identisk med
  Python på identiske trekk, største avvik 1,8e-12. Det er ordentlig arbeid.
- Estimeringen er gjort på NOK-serien, ikke USD. Riktig, siden kontantstrømmen
  er i kroner. Jeg reproduserte persentilforholdene eksakt på NOK-serien
  (olje 1,4305 / 0,5230) — på USD-serien blir de helt andre tall.
- NGL følger olje: korrelasjon 0,945 i årlige logendringer. Godt underbygget.
- Diskonteringskonvensjonen (`NPV()` datert 2025) matcher PM-tallets ordlyd.
- Kostnadsfellen er unngått: modellen bruker løpende utgifter delt på deflator,
  ikke arbeidsbokens «faste priser»-rader, som ligger ~24 pst. lavere på egen
  basis.

---

## 4. Dom

### 4.1 Hva som er verdt å beholde

1. **Datalaget.** Forutsetninger-arkets årstabell, den kalibrerte statsandelen,
   og identiteten mot NB26s SNKS. Det er ryggraden, og den er riktig.
2. **Broanalysen mot 4 800.** Den viser at horisont og rente nesten opphever
   hverandre, og at differansen ligger i kontantstrømmens nivå. Det er det mest
   verdifulle enkeltresultatet i repoet, og det står seg.
3. **Oppklaringen av NB26s formuesberegning** (4 721 = `NPV(3 %; 2025:2090)`
   datert 2024). Reelt detektivarbeid som fjernet en uforklart differanse.
4. **`verifiser_reformulert.py` og disiplinen bak.** Uansett hva dere bygger
   videre, behold vanen med å verifisere motoren mot en uavhengig referanse.
5. **Funnet at IEA-scenariene ikke kan kalibrere en vifte.** STEPS impliserer
   sigma 0,064, NZE impliserer 0,803 — 12,5 ganger forskjell, fordi scenariene
   skiller seg ved politikk, ikke ved tilbudssjokk. Det sparer dere for en
   blindvei og bør stå i notatet.
6. **`Skiftberegning`-fanen**, som ingen har brukt ennå. Den har marginalskatt,
   SDØE-andeler per ressurs og prisgjennomslag til 2090.

### 4.2 Hva som bør kastes

1. **Excel som regnemotor.** 331 755 formler, null bufrede verdier, 5,8 MB.
   Dette er årsaken til nesten alle andre kompromisser: 2 000 trekk fordi flere
   ikke får plass, ett sjokk per simulering fordi en full prosess ville krevd
   25 kolonner ekstra per faktor, ingen termstruktur fordi det ville krevd enda
   flere. Premisset er falt bort. Excel bør være **utdataformat**, ikke motor.
2. **Hele det gamle sporet.** «Statisk modell», «Miksfølsomhet», «Monte Carlo»,
   «MC-motor», `mc_simulering.py`, `build_workbook.py`, `lag_figurer.py` og de
   tre gamle SVG-ene. To uforenlige prisprosesser i samme arbeidsbok er ikke
   dokumentasjon av utviklingen, det er en felle for neste leser.
3. **Den doble forankringen som leveranseform.** Behold innsikten, kast det
   andre persentilsettet.
4. **Splitt-lognormalen og hybridkalibreringen.** Maskineri bygget for en vei
   som ikke kan gås, fordi gasstallene fra IEA ikke finnes.
5. **Ekstrapoleringen til 2060.** NB26s egen bane går til 2090.
6. **`Mulighetsbilde Petroleum.xlsx` ut av repoet** før noe deles. Den er en
   intern arbeidsbok, og repoets egen regel sier at den ikke skal ligge der.
   Trekk ut de nødvendige seriene med kildehenvisning.

### 4.3 Refaktorere eller starte på nytt?

**Start på nytt med modellen. Behold datalaget.**

Begrunnelsen er at feilene ikke er lokale. Termstrukturen, manglende
diversifisering i nåverdien og antallet trekk er alle konsekvenser av at
motoren måtte være regnearkformler. Du kan ikke rette dem enkeltvis — du må
fjerne begrensningen. Og når den er fjernet, er den riktige modellen mindre
enn den nåværende, ikke større.

Konkret målbilde, som svarer til at du verdsetter enkelt og intuitivt:

- **Én inndatafil** (CSV eller ett Excel-ark) med én rad per år og én kolonne
  per serie, pluss en kildekolonne per serie. Alt hentet ut av
  `Mulighetsbilde Petroleum.xlsx` og Ressursrapporten én gang, med
  årgangsmerking.
- **Én Python-modul på 200-300 linjer** som leser den filen, simulerer og
  skriver ut. 200 000 trekk tar sekunder.
- **Én prisprosess**, med termstruktur, dokumentert i tre linjer matematikk.
- **Excel og SVG som utdata**, generert av skriptet, uten formler.
- **Ingen skjulte ark.**

Det er tre til fire dagers arbeid, og resultatet kan forklares på én side.

### 4.4 De tre tingene som mest sannsynlig er materielt gale i dagens tall

**1. Nedsiden i det kumulative er en modellartefakt.** Kumulativ P10 på
722 mrd. — mot en basis på 4 861 — sier at fondet i tiendepersentilen får
nesten ingenting over 25 år. Det tallet kommer av at ett enkelt prissjokk
styrer alle 25 årene, uten noen utvasking. Med årlige sjokk og reversjon blir
samme P10 3 029 mrd. Det er en firedobling, og forskjellen er et
modelleringsvalg, ikke data. Dette er tallet ekspertrådet vil feste seg ved,
og det er det svakest funderte i leveransen.

**2. Viften er altfor bred i de første årene og for smal i de siste.**
Oljepris P10 41 / P90 112 USD/fat i **2026** er ikke troverdig når terminkurven
er kjent. Samtidig er 0,393 i 2050 sannsynligvis for smalt: 28 årsobservasjoner
måler i hovedsak konjunktursykelen, ikke 25-års nivåskift, og det historiske
båndet er bare marginalt bredere enn et rimelig ettårs standardavvik for olje
(0,25-0,30). Modellen har altså feil fordeling av usikkerheten over tid i
begge ender.

**3. Volumbåndet er beregnet mot feil nevner, og deretter halvert.** SDs
høy/lav er delt på NB26s basis, ikke SDs egen. Det gjør at «lavbanen» ligger
over basis i 2026-2029 og at båndet er 6,8 pst. for bredt i 2050. Så krymper
den triangulære vekten båndet til under halvparten av SDs oppgitte spenn.
Ingen av delene er dokumentert som et valg.

Rett under: den marginale statsandelen er 8-20 pst. for høy, og gassprisen slår
kanskje bare halvt gjennom ifølge NB26s eget verktøy. Begge deler treffer
elastisiteten, som er det viftens bredde til slutt består av.

### 4.5 Data du mangler — og data du allerede har uten å vite det

**Du har allerede, i `Mulighetsbilde Petroleum.xlsx`:**

- **Kostnadsbanen, splittet, til 2090.** Formue rad 55 (påløpte
  driftsutgifter), rad 58 (påløpte investeringsutgifter), rad 59 (sum), rad 44
  (deflator). Driftsandelen stiger fra 31 pst. i 2026 til 40 pst. i 2050.
  Modellen bruker bare summen. Splitten er nettopp det du trenger for et
  skille mellom faste og variable kostnader.
- **Produksjon per ressurstype til 2090.** Formue rad 30-32.
- **Marginalskattesats (0,78) og SDØEs produksjonsandeler per ressurs og år.**
  Skiftberegning rad 7 og 37-39, KVARTS rad 392-395 og 400.
- **Gassprisgjennomslag (0,50).** Skiftberegning rad 17.
- **Prisbaner til 2090.** Formue rad 38-40.

Modellens horisont er begrenset til 2050 av Sokkeldirektoratets mulighetsbilder
— men det gjelder bare **volumusikkerheten**. Basisbanen kunne gått til 2090
uten en eneste ekstrapolert verdi.

**Du mangler faktisk:**

1. **PM 2024s egen kontantstrømbane.** Uten den kan gapet på 1 130 mrd. ikke
   dekomponeres. Det er den eneste manglende opplysningen som direkte påvirker
   hovedkonklusjonen.
2. **Lengre prishistorikk.** 28 årsobservasjoner er for lite til å estimere
   reverteringsfart. Dickey-Fuller-testen kan ikke avvise random walk for
   noen av varene (t = −1,91 for olje, −2,47 for gass, kritisk verdi ≈ −3,0),
   og OLS-estimatet er nedadbiasert: bias-korrigert stiger oljens halveringstid
   fra 3,0 til 8,2 år. Månedlig Brent fra 1988 og TTF/NBP fra 1997 ville gitt
   et estimat man kan forsvare.
3. **Ressursmiks for SDs høy- og lavbane.** Repoet noterer at SD ikke har den.
   Da må antakelsen om konstant miks stå, men følsomheten bør vises.
4. **NOK/USD.** Ingen serie i repoet. I dag er kursen en hardkodet 10,5 brukt
   bare til visning, mens basisbanen implisitt bruker 10,18.
5. **Balanseprisfordeling per prosjekt.** Deck slide 14 viser 20-45 USD/fat, men
   bare som bilde. Uten fordelingen kan nedstengingslogikken ikke bli annet enn
   et hardt aggregatgulv.
6. **IEA WEO Annex A.** Kan ikke hentes herfra — egress-proxyen blokkerer
   `iea.org`. Trengs bare hvis dere vil ha NZE som navngitt sidescenario.

---

## Åpne spørsmål

Disse må besvares før vi designer erstatningen. De er sortert etter hvor mye
de påvirker resultatet.

1. **Hvor mye av en lavprisperiode skal kunne vare?** Dette er det ene valget
   som styrer nedsiden i nåverdien. Konkret: hvis oljeprisen faller 30 pst.
   under banen i 2030, hvor stor del av det avviket skal være igjen i 2040?
   Dagens modell svarer «alt»; ren OU svarer «ingenting». Et tall mellom 0 og
   1 er nok — jeg oversetter det til parametre.

2. **Hvor bredt skal 2050-båndet være?** Historikken gir P10 41 / P90 112
   USD/fat, men de 28 observasjonene måler i hovedsak sykelen. Skal 2050
   settes bevisst bredere? Og skal en NZE-lignende verden ligge **inne** i
   viften eller **ved siden av** som navngitt sidescenario?

3. **Skal 2026-2028 ha en smal vifte?** Terminkurven er kjent til 2035 ifølge
   deck slide 5. Skal modellen forankres i den for de første årene, eller skal
   viften starte bredt fra år 1 slik som nå?

4. **Er `Gassprisgjennomslag = 0,50` i Skiftberegning det jeg tror?** Altså at
   bare halvparten av en gassprisendring slår gjennom i realiserte inntekter?
   Hvis ja, er gassbidraget til dagens vifte omtrent dobbelt så bredt som det
   burde være, og det bør rettes. Hvis nei — hva betyr tallet?

5. **Skal statsandelen bli strukturell?** Vi har 78 pst. marginalskatt og
   SDØE-andeler per ressurs og år i kildefilen. Alternativet er å beholde den
   kalibrerte gjennomsnittsandelen, som treffer nivået eksakt, men overdriver
   priselastisiteten med 8-20 pst. Jeg anbefaler en mellomvei: kalibrert nivå,
   strukturell margin. Er det akseptabelt for ekspertrådet?

6. **Er Sokkeldirektoratets høy- og lavbane ytterpunkter eller et
   sannsynlig spenn?** Dagens triangulære vekt behandler dem som ytterpunkter
   med tetthet null og bruker under halvparten av spennet som 80 pst.-intervall.
   Skal de i stedet tolkes som P10/P90? Er dette avklart med SD?

7. **Hvilken basisproduksjon er den riktige — SDs eller NB26s?** De avviker med
   opptil 6,3 pst., og i dag blandes de: SDs høy/lav deles på NB26s basis. Det
   må velges én.

8. **Hva er 4 800 uttrykt i?** Hvilket basisår, og statsbudsjettets
   utgiftsdeflator eller NB26s? Forskjellen er om lag 150 mrd. Og har du tilgang
   til PMs egen kontantstrømbane, slik at differansen kan dekomponeres i pris,
   volum og kostnad?

9. **Skal hovedmodellen gå til 2060 eller 2090?** NB26s bane går til 2090.
   Volumusikkerheten fra SD slutter i 2050. Ett alternativ er basis til 2090 og
   vifte til 2050, med halen som deterministisk tillegg.

10. **Median eller forventning — velg én.** Skal P50-banen være NB26s
    sentralanslag (medianforankring), eller skal middelverdien være det
    (forventningsforankring)? Begge kan ikke oppfylles. Jeg anbefaler
    medianforankring med én fotnote om middelet.

11. **Skal nedstengingen være gradvis?** Dagens harde gulv binder i 18 pst. av
    simuleringene i 2050 og gjør P10 nøyaktig null. Alternativet er en gradvis
    nedstenging basert på balansepriser — men da trenger vi fordelingen bak
    deck slide 14.

12. **Skal `Mulighetsbilde Petroleum.xlsx` ut av repoet?** Skal noe av dette
    deles utenfor avdelingen, må den ut og seriene ekstraheres med
    kildehenvisning.

13. **Hva er egentlig leveransen?** Et notat med figurer, en arbeidsbok andre
    skal kunne endre forutsetninger i, eller et Python-repo som kjøres på nytt?
    Svaret bestemmer hvor mye som skal ligge i Excel.
