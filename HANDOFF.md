# HANDOFF — SNCF-modell, status og videre arbeid

Overlevering til ny chat-økt. Prosjektet: modell for statens netto kontantstrøm
(SNCF) fra petroleum → innbetaling til SPU, faste 2026-kroner. Hovedhorisont
2026-2050 (kildebelagt), med ekstrapolert utvidelse til 2060 for
sammenligning mot PM-referansen.
Bygget for saksbehandler i FIN, Avdeling for formuesforvaltning. Alt på norsk
bokmål. Leveranse skal fungere Excel-native (bruker har ikke Python på jobb).

Gren: `claude/sncf-anchor-calibrate-smb2ii` (bygger på PR #1-grenen
`claude/claude-md-review-verify-70a7je`, som er merget inn).
Se `CLAUDE (1).md` for full modelldokumentasjon.

## 0. PREMISSENDRING 02.09.2026 — EXCEL-KRAVET ER OPPHEVET

Brukeren har Python-tilgang på jobb likevel. Excel-native var en bærende
premiss for arkitekturen, så flere valg må vurderes på nytt. Samtidig har
brukeren reist et faglig spørsmål om prisprosessen: bør prisene bare sjokkes
fra basisbanen med et godt valgt standardavvik og reversjon mot normalen?

Det er i praksis et forslag om å gå tilbake mot OU-prosessen som ligger i den
GAMLE motoren, og bort fra dagens persistente regimetrekk. Analysen under
(punkt 5) viser at forslaget peker på en reell mangel ved dagens modell, men
at det ikke finnes noen enkel én-faktor-løsning. **Hele prosjektet skal
gjennomgås på nytt med alle valg — se punkt 6.**

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
**Brukeren har IEA-tilgang på jobb og bør lime inn Annex A-tabellen.** To
steder: `MAL` i `kalibrering.py`, og de blå cellene B60-B63 i Forutsetninger
(eller kolonne Q/R for en årsbane).

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
Kumulativ: medianforankret P10 105 / P50 4 729 / P90 12 658 / middel 5 740
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

**VALGT 02.09.2026: vei (c).** Bygget inn i arbeidsboken.

## 3. BYGGET — status 02.09.2026

Begge valg er låst og bygget inn i `Kontantstromsmodell_petroleum.xlsx` av
`build_reformulert.py`. Ikke-destruktivt: de gamle arkene står urørt.

Nytt i boka:
- **«Reformulert vifte»** (synlig, plassert før Dokumentasjon): persentiler for
  BEGGE forankringer side om side (B-G median, H-M forventning), NB26-basis og
  NZE-sidescenario i N/O, oppsummering (kumulativ + NPV 2/3/4) rad 31-37,
  kontroll mot basis rad 39-45, parameteravlesning rad 47-58, og to
  gråtonenoter som forklarer hvorfor IEA ikke kalibrerer viften.
- **«MC-motor-R»** (skjult): 2 000 simuleringer, 120 000 formler. Persistente
  trekk (w, z1, z2 — ett per simulering), prisfaktorene fo/fg beregnet én gang
  per simulering, og SNCF per år for begge forankringer på SAMME trekk.
- **Forutsetninger rad 46-68**: parameterblokk. sigma avledet av B4:B7,
  korrelasjon, gulvbryter, Jensen-korreksjoner, enhetskonvertering, IEA-input
  (blå, tomme) og persentilavlesning for NZE/STEPS.
- **Forutsetninger kolonne Q/R**: input for NZE-prisbaner per år.
- **Dokumentasjon**: sju nye avsnitt om den reformulerte modellen.
- Figurer: `reformulert_vifte.svg` og `reformulert_akkumulert.svg`, begge med
  medianforankrede bånd og den forventningsforankrede medianen som egen linje.

Forventede tall når boka åpnes (2 000 faste trekk, frø 2026):
kumulativ medianforankret P10 646 / P50 4 990 / P90 12 993 / middel 6 075;
forventningsforankret P10 283 / P50 3 935 / P90 11 202 / middel 4 997.
0,0 pst. negative årsverdier.

Verifikasjon: `python3 verifiser_reformulert.py` bygger en liten, strukturelt
identisk testbok med de SAMME funksjonene og evaluerer den med
`formulas`-biblioteket (soffice er ødelagt). Største avvik mot Python 1,8e-12.
Testen fanget to reelle feil: (i) Excel binder unær minus sterkere enn potens,
så `EXP(-B47^2/2)` ble `EXP(+B47^2/2)` — må skrives `EXP(-(B47^2)/2)`;
(ii) testboken må skrive de avledede kolonnene E/H/I/O/P som formler, siden
openpyxl fjerner bufrede verdier og `data_only` derfor gir None.

## 4. UTVIDELSE TIL 2060 OG SAMMENLIGNINGEN MOT 4 800 — 02.09.2026

Bygget som eget synlig ark «Utvidelse 2060». Hovedmodellen beholder 2026-2050,
som er kildebelagt; 2051-2060 er ekstrapolert og merket som det, også i
figurene (grått felt fra 2050).

Ekstrapoleringen: volumer, totalbaner og kostnader føres videre med de
geometriske ratene over de siste fem årene av basisbanen (olje −3,35 pst.,
gass −3,70 pst., kostnader −2,93 pst. per år), prisene holdes flate — de er
flate fra 2041 i basisbanen uansett — og statsandelen holdes på 0,983, snittet
av 2046-2050. Vindu og et påslag i prosentpoeng er input, så halen kan
stresstestes fra arket.

**Broen (basisbanen, mrd. 2026-kroner, neddiskontert til 2025):**

| | mrd. |
|---|---|
| 1. Basis NNV 3 pst., 2026-2050 | 3 753 |
| 2. Effekt av rente 3 → 4 pst. | −276 |
| 3. Effekt av horisont 2051-2060, ved 4 pst. | +186 |
| 4. = Modellens basis NNV 2026-2060, 4 pst. | **3 663** |
| 5. PM-referanse | 4 800 |
| 6. Differanse | **−1 137** (−23,7 pst.) |

**Hovedfunnet: horisont og rente opphever nesten hverandre.** Overgangen fra 3
til 4 pst. koster mer enn de ti ekstra årene tilfører, så nettoeffekten er bare
−90 mrd. Differansen mot 4 800 ligger dermed i kontantstrømmens NIVÅ og var
der allerede på 2026-2050 med 3 pst. (3 753 mot 4 800). Utvidelsen løser altså
ikke gapet — den viser at gapet ikke handler om horisont eller rente.

Robusthet: et påslag på alle nedgangsrater fra 0 til +5 prosentpoeng flytter
NNV 4 pst. bare fra 3 663 til 3 716 mrd. (+3,4 pp gir tilnærmet flat
oljeproduksjon; merk at et FELLES påslag ikke kan nulle ut rater som er ulike,
så ved +3,4 pp begynner kostnadene å vokse svakt). Halen er liten og ligger
langt ute i diskonteringen, så konklusjonen henger ikke på
ekstrapoleringsvalget.

### Halekontroll — RETTET 02.09.2026, og en feil i tidligere dokumentasjon

NB26s egen SNKS-bane går til 2090 i kildefilen (`Mulighetsbilde
Petroleum.xlsx`, Formue rad 84, verifisert identisk med Forutsetninger!N for
2026-2050). Halen trenger altså ikke gjettes.

| | modellens ekstrapolering | NB26s egen bane |
|---|---|---|
| Hale 2051-2060, udiskontert | 599 | 629 |
| Hale 2051-2060, NNV 4 pst. | 186 | 194 |
| Hale 2051-2090, NNV 3 pst. | 415 | 425 |
| NNV 4 pst. 2026-2060 | 3 663 | **3 671** |

Ekstrapoleringen traff altså 2-4 pst. lavt — den er **validert mot kilden**, og
gapet mot 4 800 er uendret.

**FEIL I TIDLIGERE DOKUMENTASJON, nå rettet:** påstanden om at NB26s
formuesberegning er «2026-2090 med 3 pst. = 4 721» og at differansen mot vår
3 753 «er halen 2051-2090 (968 mrd.)» holder ikke. Tallet 4 721,1 er
`NPV(3%; SNKS 2025:2090)` — altså fra **2025** og **datert 2024** (Excels NPV
daterer ett år før første beløp). Verifisert til 4 721,1 mot Formue rad 100 på
maskinpresisjon. De «968» var i hovedsak 2025-kontantstrømmen (684 mrd.)
pluss ett års diskontering, ikke halen. Modellen har dermed INGEN uforklart
differanse mot NB26 — den reproduserer NB26 der horisontene overlapper.

### Gapet mot 4 800 er ikke en definisjonsforskjell

Testet på NB26s egen bane, med 4 pst.:

| definisjon | mrd. | mot 4 800 |
|---|---|---|
| 2026-2060, datert 2025 (deckets ordlyd) | 3 671 | −1 129 |
| 2025-2060, datert 2024 | 4 188 | −612 |
| 2025-2090, datert 2024 (som NB26s formuesber.) | 4 294 | −506 |
| 2025-2090, datert 2025 | 4 466 | −334 |

Ingen omdatering eller omhorisontering kommer opp til 4 800. Differansen
ligger derfor i at PM bygger på en materielt høyere kontantstrømbane enn NB26
— en årgangs- eller forutsetningsforskjell, ikke en regnemåte. Repoet har
ingen PM-data, så hvilken av forutsetningene som skiller, kan ikke avgjøres
herfra.

**Konsekvens for leveransen: 4 800 og modellens tall skal IKKE presenteres som
samme størrelse.** Den tidligere merknaden om at likheten mellom 4 800 og
kumulativ 4 861 var tilfeldig, er nå bekreftet og tallfestet — 4 861 er
udiskontert, og diskontert lander modellen på 3 663-3 753 uansett
horisont/rente-kombinasjon.

## 5. PRISPROSESSEN — brukerens forslag, og trilemmaet

Brukerens forslag 02.09: sjokk prisene fra basisbanen med et godt valgt
standardavvik, med reversjon mot normalen. Det er i praksis OU-prosessen i den
gamle motoren. Forslaget treffer en REELL mangel ved dagens modell, men
løsningen er ikke en én-faktor-prosess. Alle tall under: 20 000 sim.,
medianforankret, basis kumulativ 4 861.

### Mangelen forslaget avdekker: dagens modell har ingen termstruktur
Den persistente regimefaktoren har samme st.avvik i logpris i 2026 som i 2050
(0,393). Konsekvensen er at SNCF 2026 får spennet P10 164 til P90 1 168 mot en
basis på 521 — for et år der prisene i stor grad er låst av terminmarkedet og
produksjonen er kjent. Usikkerhet skal vokse med horisonten; her gjør den det
ikke.

### Trilemmaet: tre egenskaper, og ingen enkel prosess gir alle tre
(a) smal vifte i 2026, (b) et avgrenset og fornuftig bånd i 2050, (c) ekte
regimerisiko i det kumulative — altså at en lavprisverden kan vare.

| prosess | halv.tid | sd 2026 | sd 2050 | SNCF 2026 P10-P90 | kum. P10 | P50 | P90 |
|---|---|---|---|---|---|---|---|
| Dagens, rent regime | ∞ | 0,393 | 0,393 | 164 – 1 168 | 646 | 4 990 | 12 993 |
| OU, estimert kappa | 2,9 år | 0,232 | 0,378 | 248 – 939 | 3 210 | 5 714 | 9 172 |
| OU + nivåvandring 0,05 | 2,9 år | 0,237 | 0,456 | 245 – 946 | 2 926 | 5 765 | 9 988 |
| Halv kappa + nivå 0,05 | 6,2 år | 0,237 | 0,579 | 245 – 946 | 2 285 | 6 114 | 12 966 |
| Kvart kappa + nivå 0,05 | 12,8 år | 0,237 | 0,745 | 245 – 946 | 1 752 | 6 425 | 17 219 |
| Nesten ingen reversjon | 65 år | 0,237 | 1,059 | 245 – 946 | 1 245 | 6 834 | 27 213 |

- Dagens modell gir (b) og (c), men bryter (a).
- Ren OU gir (a) og (b), men bryter (c): kumulativ P10 går fra 646 til 3 210
  fordi årssjokkene vasker ut hverandre.
- Å senke kappa for å få (c) tilbake bryter (b): sd 2050 løper til 1,06 og
  P90 til 27 213. Det er nøyaktig GBM-oppførselen som ble forkastet 01.09.

### Anbefalt løsning: to faktorer som BEGGE reverterer, i ulik fart
En rask syklisk faktor (halveringstid ~3 år, som AR(1) estimerer greit) pluss
en LANGSOM nivåfaktor (halveringstid 20-30 år, ikke en ren random walk).
Nivåfaktoren er i praksis «det persistente regimet», men den bygger seg opp
over tid i stedet for å bli pålagt i år 1. Da blir 2026 smal, 2050 avgrenset,
og nivået varer i tiår innenfor én simulering.

### Ubehagelig funn om kalibreringen (berører beslutning 15)
Det historiske båndet (sigma 0,393, fra P90/P50 = 1,65 på 1997-2024) er bare
marginalt bredere enn et rimelig ETTÅRS standardavvik for olje (0,25-0,30).
De 28 årsobservasjonene måler altså i hovedsak SYKELEN, ikke 25-års
nivåskift. Å bruke 0,393 som 2050-bånd undervurderer dermed sannsynligvis
langsiktig usikkerhet. Ved todeling bør 2050-båndet settes bevisst BREDERE enn
det historiske — og det er en skjønnsvurdering, ikke et estimat.

### Interaksjon med forankringen (berører beslutning 14)
Under den persistente modellen ga medianforankring kumulativ P50 ≈ basis
(+2,7 pst.) nesten tilfeldig. Med reversjon drifter kumulativ P50 til +18 pst.
over basis, fordi hvert års forventede prisfaktor er over 1 og 25 delvis
uavhengige år snitter mot forventningen framfor medianen. Ønskes «P50 = NB26»
på KUMULATIVT nivå, må det bli et eksplisitt kalibreringsmål, ikke et
biprodukt.

## 6. FULL GJENNOMGANG — status for hvert valg

Brukeren har bedt om at hele prosjektet gjennomgås på nytt. Statusmerking:
**REÅPNET** = må avgjøres på nytt, **BERØRT** = kan endres av et annet valg,
**STÅR** = ikke berørt av premissendringen.

| # | Valg | Status |
|---|---|---|
| — | Excel-native arkitektur (2 000 faste trekk i celler, alt som formler) | **REÅPNET** — premisset falt |
| 8 | Prisprosess (GBM forkastet → OU → persistent regime) | **REÅPNET** — se punkt 5 |
| 13 | Persentiler som scenarier, persistente regimer | **REÅPNET** — designet står, prosessen ikke |
| 14 | Forankring: begge vises | **BERØRT** — interaksjonen i punkt 5 |
| 15 | Kalibrering vei (c), historisk sigma | **BERØRT** — historisk bånd måler sykel |
| 6 | Statiske prisskift, historisk persentilkalibrering | **BERØRT** — brukes nå til å avlede sigma |
| 12 | 3x3 som scenarioverktøy vs MC | **BERØRT** — kan bortfalle helt |
| 2 | Statsandel kalibrert, ikke modellert | **STÅR** — men Python åpner for eksplisitt skattemodell |
| 16 | Horisont 2060 | **STÅR** — men NB26s egen bane til 2090 kan nå brukes |
| 1, 3, 4, 5, 7, 9, 10 | Målvariabel, kostnadsskalering, prissplitt, prisgrunnlag, enheter, resultatformer, hovedhorisont | **STÅR** |

Utsatte punkter som Python nå gjør praktiske: bootstrap på sigma/kappa
(estimeringsusikkerheten er dokumentert men ikke tallfestet i modellen),
bias-korreksjon av kappa (kjent nedadbiasert på kort utvalg), gradvis
nedstenging basert på balanseprisfordelingen i stedet for hardt 0-gulv, og
flere simuleringer enn 2 000.

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

### Spor 2: Reformulert modell (ØNSKET RETNING) — nå i boka
INTEGRERT 02.09.2026, se punkt 3. Python-referansen er `mc_reformulert.py`
(kjør `python3 mc_reformulert.py`); Excel-versjonen bygges av
`build_reformulert.py`.

Idé: én Monte Carlo på basisproduksjon der **PERSENTILENE SELV ER SCENARIENE**:
P90 = høy prognosert CF, P50 = median, P10 = lav. Ingen egen 3x3.
- Persistente REGIME-trekk (ett per sim) for pris (lognormal faktor) og volum
  (triangulær lav/basis/høy) — speiler "høybane/lavbane har vart over flere år".
- Tilbudsrespons: feltnetto gulves ved 0 (ingen tapsproduksjon), forankret i
  balanseprisene. Fjerner de meningsløse negative tallene (0 % negative år).
- Basis = IEA WEO APS. IEA-forankring av ytterkantene (P90 ~ STEPS, P10 ~ NZE)
  er PRØVD OG FORKASTET — se punkt 2 over. Sigma kalibreres historisk.

Python-referansens oppsett (`MEDIAN_ANCHOR=True`, `KALIBRERING="historisk"`,
sigma olje/gass 0,393/0,490 lest ut av `Forutsetninger!B4:B7`, 10 000 sim.):
- Impliert oljepris: P10 41 / P50 68 / P90 112 USD/fat (middel 73).
- Impliert gasspris: P10 3,0 / P50 5,7 / P90 10,8 USD/MMBtu (middel 6,4).
- Kumulativ til fondet: P10 688 / P50 5 006 / P90 12 679 / middel 6 087.
- NPV3: P10 601 / P50 3 874 / P90 9 581 / middel 4 658.
- 0,0 pst. negative årsverdier.

Nytt i `mc_reformulert.py`: splitt-lognormal (eget sigma over/under medianen,
median bevart eksakt), `KALIBRERING`-bryter, sigma avledet fra arbeidsboken.
Figurene er regenerert mot det låste oppsettet med `lag_figur_reformulert.py`.

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
1. Brukeren limer inn IEA WEO Annex A-prisforutsetningene (kan ikke hentes fra
   containeren — egress blokkert). To steder: `MAL` i `kalibrering.py`, og de
   blå cellene B60-B63 i Forutsetninger. Da tennes NZE-sidescenarioet i
   kolonne O (gir #N/A til da), og persentilavlesningen (STEPS P61 / NZE P0,5)
   kan verifiseres mot faktiske tall i stedet for søketreff.
3. Vurdere om persistent regime-trekk er nok, eller om det trengs år-til-år-
   variasjon i tillegg (i dag er pris ren persistent faktor).
4. Foredle tilbudsrespons: fra hardt 0-gulv til en balansepris-basert gradvis
   nedstenging (bruk fordelingen ~20-45 USD fra slide 14).
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
