# Statens petroleumsformue — kontantstrømmodell

Underlag til vedlegg for Ekspertrådet for SPU. Anslår statens netto
kontantstrøm fra petroleumsvirksomheten fremover, med usikkerhetsbånd, og hva
den betyr for tilflyten til SPU.

---

## Til Claude Code — les dette først

Arbeid ett steg om gangen og stopp mellom hvert. Ikke hopp fremover.

**Nå: steg 0.** Kjør `python -m src.inspiser` og vis meg utskriften.
Radnumrene under «Datagrunnlag» er en hypotese fra gjennomgangen av den
forrige modellen, ikke en spesifikasjon. Ikke skriv uttrekkskode før
strukturen er bekreftet mot den faktiske filen. Den forrige modellen ble
skrevet mot antatte radnumre, og resultatet var en lavbane som lå over
basisbanen i fire år.

Deretter: implementer `src/uttrekk.py`, bygg `data/inndata.csv`, fyll ut
`data/kilder.csv`, og kjør `pytest -v`. Alle ni tester skal være grønne.
Rapporter særlig `test_volumforhold_hoy_lav` — den avgjør om resten av planen
holder.

Ferdig, skal ikke skrives om: `src/fred.py`, `src/sodir.py`,
`src/persistens.py`, `src/figurer.py`, `src/inspiser.py`, `tests/`.
Stubber: `src/uttrekk.py`, `src/modell.py`, `src/prisprosess.py`,
`src/fond.py`. Kontrakten står i docstringen til hver.

Der README er taus: spør. Ikke velg selv.

**Gren.** Alt nytt arbeid ligger på `modell-v2`, uten historikk fra den gamle
modellen:

```bash
git tag arkiv-2026-09 && git push --tags
git checkout --orphan modell-v2
git rm -rf .
# legg inn denne mappen
git add . && git commit -m "Ny modell: skjelett, Sodir-utledning og tester"
```

`main` og `claude/sncf-anchor-calibrate-smb2ii` blir liggende urørt som
sidegrener. Taggen gjør at ingenting går tapt selv om de slettes senere. Når
vedlegget er ferdig: `git branch -M modell-v2 main`.

---

## Premisset

Ved 4 pst. realrente ligger om lag 74 pst. av nåverdien i 2026–2035, 93 pst.
innenfor 2045, og under 3 pst. etter 2050. Presisjon hører hjemme i det første
tiåret. Halen behandles grovt og dokumenteres.

Prosjektet er en omskriving. Den forrige modellen lå i Excel med om lag
330 000 formler, og de fleste svakhetene fulgte av det: 2 000 trekk fordi flere
ikke fikk plass, ett prissjokk per simulering fordi en full prosess ville krevd
25 kolonner ekstra per faktor, og ingen termstruktur fordi det ville krevd enda
flere. Her er Excel utdataformat, aldri regnemotor.

Perspektivmeldingen 2024 inngår ikke. Sammenligningen mot de 4 800 mrd. kronene
er lagt bort, og med den spørsmålet om deflator og basisår.

---

## Plan

### Steg 0 — uttrekk

Alle serier hentes én gang til `data/inndata.csv`, med årgangsmerking og enhet
per serie i `data/kilder.csv`. Ingen tall limes inn manuelt noe sted. Dette er
det som gjør NB27-oppdateringen senere i år til én endring og en ny kjøring.

**Regel:** finnes noe i en kildefil, blir det en kolonne. Er noe utregnet, blir
det det ikke. Forholdstall og realkostnader avledes i `modell.py`, aldri i
`inndata.csv`. Slik er filen en tro gjengivelse av kildene, og ingenting kan
drive stille.

### Steg 1 — utlede Sokkeldirektoratets forutsetninger

Tallene bak figur 2.5 og 2.6 er ikke publisert, men nivåene lar seg lese av
figurene, og avlesningen reproduserer alle fire spennene Sokkeldirektoratet
oppgir i teksten. Se `src/sodir.py`, som er ferdig.

| mrd. 2026-kroner | Høy | Basis | Lav |
|---|---|---|---|
| udiskontert, 80 USD | 14 800 | 12 400 | 7 400 |
| udiskontert, parret | 19 900 (100 USD) | — | 4 700 (60 USD) |
| NNV 4 pst., 80 USD | 9 100 | 7 500 | 5 900 |
| NNV 4 pst., parret | 12 200 | — | 3 900 |

Teksten oppgir bare én pris per fat, ingen gassprisbane, så all produksjon ser
ut til å være verdsatt til én felles pris per fat oljeekvivalent.

Med den forutsetningen er det ingen frie parametere igjen ut over
valutakursen. Priselastisiteten i hver bane gir `m·R` og `m·C`; volumene er
kjent; prisen er kjent. Dermed er `m` bestemt, og deretter begge
kostnadsbanene. Steget er ikke en test av motoren, men en gjenutledning av
Sokkeldirektoratets egen uttaksrate og kostnadsbane, som deretter kan
sammenlignes med NB26s. Den sammenligningen har ingen gjort.

Tre resultater, i denne rekkefølgen:

1. **Volumforholdet.** `m·R_Høy / m·R_Lav = 1,89` er fritt for både `m` og
   pris, og er derfor en parameterfri kontroll mot de faktiske banene. Testes i
   `tests/test_uttrekk.py`. Slår den feil, stopp og les figurene på nytt før
   noe annet gjøres.
2. **Marginalandelen.** `m = 20 400 / (5,13 · kumulativt volum Høy)`.
   Referanse: 0,80–0,82 er den strukturelle andelen (78 pst. marginalskatt
   pluss SDØE). Om lag 1,00 ville betydd at tallet gjelder sektorens
   verdiskaping, ikke statens.
3. **Kostnadene.** `m·C_Høy = 5 600` og `m·C_Lav = 3 400` gir
   Sokkeldirektoratets impliserte kumulative kostnad når `m` er kjent.
   Kostnadsandelen av inntekten er 27,5 pst. i Høy og 31,5 pst. i Lav — høyere
   kostnader i lavbanen, som fallende kapasitetsutnyttelse tilsier.

### Steg 2 — bytte til Energidepartementets prisbaner

Samme motor, med olje og gass priset hver for seg. **Dette steget er
leveransen.**

Én Sm³ o.e. er 6,29 fat væske, men som gass om lag 37,9 MMBtu. Flat prising til
80 USD per fat o.e. gir 503 USD per Sm³ o.e. for alt. Energidepartementets
forutsetninger gir 440 USD for olje og 216 USD for gass. Flat prising verdsetter
altså olje 14 pst. høyere og **gass 2,33 ganger høyere**.

Ved en gassandel på om lag 50 pst. av gjenværende ressurser og en kostnadsandel
på 30 pst. gir det en nettoeffekt på 2,05. Det observerte avviket mellom
Sokkeldirektoratets Basis-nåverdi på 7 500 og NB26s egen bane på 3 671 er 2,04.

Hovedfiguren er en fossefigur fra 7 500 ned til 3 671, med gassprisleddet som
den dominerende søylen. Det er en publisert ekstern verdsetting av gjenværende
ressurser som er dobbelt så høy som statens egen, og forskjellen er nesten
utelukkende én forutsetning om gass. Gitt at gassandelen av produksjonen stiger
og staten bærer to atskilte spotprisrisikoer, viser den figuren poenget bedre
enn en følsomhetstabell.

**Merk:** en del av faktoren kan skyldes horisont. Sokkeldirektoratets
kontantstrøm løper trolig over full feltlevetid, mens 3 671 er avkortet i 2060.
Horisonten skal være et eget ledd i fossefiguren, ikke en antakelse.

### Steg 3 — det rutenettet ikke kan vise

Prisvifte på Basis-banen alene, som viser at usikkerheten bygger seg opp over
tid og at nåverdifordelingen er strammere enn årsfordelingen. Deretter et tynt
fondsregnskap: tilflyt inn, uttak ut, 3 pst. realavkastning, og
kryssningspunktet der uttak passerer tilflyt. Begge er støttefigurer.

**Regel gjennom hele:** pris- og volumusikkerhet ganges aldri sammen.
Prisusikkerhet vises på én produksjonsbane; volumusikkerhet vises som navngitte
baner ved faste priser. Sokkeldirektoratets volumer inneholder allerede et
lønnsomhetsfilter, så et uavhengig prissjokk lagt oppå dem beskriver en verden
deres egen metode utelukker.

---

## Figurer

Fem. Den midterste bærer vedlegget.

1. Produksjon, tre mulighetsbilder til 2050.
2. Netto kontantstrøm og nåverdi per bane — egen versjon av figur 2.5 og 2.6, med Energidepartementets priser ved siden av Sokkeldirektoratets.
3. **Fossefigur fra Sokkeldirektoratets prising til Energidepartementets**, med olje, gass og horisont som atskilte ledd.
4. Prisvifte, Basis-banen.
5. Tilflyt mot uttak i pst. av fondsverdi, med kryssningspunktet.

matplotlib, Liberation Sans, FIN-farger. Se `src/figurer.py`.

---

## Datagrunnlag

| Serie | Kilde | Status |
|---|---|---|
| produksjon olje / gass / NGL | Mulighetsbilde, Formue rad 30–32 | **Har** (intern, i `.gitignore`) |
| prisbaner olje / gass / NGL | Formue rad 38–40 | **Har** |
| påløpte driftsutgifter | Formue rad 55 | **Har** |
| påløpte investeringsutgifter | Formue rad 58 | **Har** |
| deflator, basisår 2026 | Formue rad 44 | **Har** |
| SNKS | Formue rad 84 | **Har** |
| marginalskattesats | Skiftberegning rad 7 | **Har**, ubrukt i forrige modell |
| SDØE-andeler per ressurs | Skiftberegning rad 37–39 | **Har**, ubrukt |
| gassprisgjennomslag | Skiftberegning rad 17 | **Har**, se åpne punkter |
| tre mulighetsbilder 2025–2050 | Ressursrapport 2026 | **Har.** Høy har endret profil fra RR24 |
| oljekorrigert underskudd, fondsverdi | Mulighetsbilde eller NB26 | **Sjekk.** Kun steg 3 |
| WTI månedlig fra 1946, KPI, Brent, OVX | FRED | **Hentes av `src/fred.py`** |
| TTF/NBP fra 1997 | Macrobond | **Mangler.** Kun steg 3 |
| implisitt volatilitet gass | Macrobond, ATM på ICE TTF-opsjoner. Utenfor lisensen: rullerende 12 mnd. realisert volatilitet på frontkontrakten | **Mangler.** Kun steg 3 |

Radnumrene er en hypotese. Bekreft med `python -m src.inspiser`.

**Feller i denne filen.** Kostnader er påløpte utgifter delt på deflatoren, ikke
arbeidsbokens «faste priser»-rader, som ligger om lag 24 pst. lavere på egen
basis. Drifts- og investeringsutgifter hentes hver for seg, ikke som sum;
driftsandelen stiger fra 31 til 40 pst. over perioden. Arkene starter i ulike år
(KVARTS 1997, Formue 2007, Sodir 1970) — juster på årstall og la hull stå tomme,
ikke som null. Enhet føres for hver eneste kolonne i `kilder.csv`; sammenblanding
av mill. og mrd. er det mest sannsynlige som går galt.

**σ fra implisitt volatilitet.** OVX er annualisert implisitt volatilitet for
*spot*. Modellen bruker årsgjennomsnitt. Variansen til gjennomsnittet av en
brownsk bane over et år er σ²/3, så standardavviket er σ/√3. OVX har median om
lag 36 pst. over hele perioden og 48 pst. siste tolv måneder, som gir σ på om lag
21 og 28 pst. Uten korreksjonen overvurderes σ med om lag 70 pst., i nettopp det
tiåret som bærer tre firedeler av nåverdien.

---

## Modellen

**Deterministisk motor.** Modellerer avvik fra basis, ikke nivåer, slik at
basisidentiteten mot NB26 holder eksakt per konstruksjon:

```
SNCF[t] = maks( SNKS_basis[t] + m[t] · (Δinntekt[t] − Δkostnad[t]), 0 )
```

`m[t]` er *marginal* statlig uttaksrate, regnet fra marginalskattesats 0,78 og
SDØEs produksjonsandeler. Den ligger på 0,80–0,82. Bruk aldri
gjennomsnittsandelen `SNKS/(inntekt−kostnad)` som marginalrate; det var feilen i
den forrige modellen, og den overdrev priselastisiteten med 8–20 pst.

**Volum.** `f[t] = SD_scenario[t] / SD_basis[t]`, anvendt på NB26s basisbane.
Aldri `SD_scenario / NB26_basis`. Ressursmiks antas lik i alle tre banene;
følsomhet ±10 prosentenheter gassandel flytter nåverdien med om lag ±242 mrd.
kroner.

**Prisprosess (kun steg 3).**

```
d[t] = χ[t] + ξ[t]
χ[t] = a·χ[t−1] + √(1−ω)·σ·ε[t]      transitorisk
ξ[t] = ξ[t−1]   + √ω·σ·η[t]          varig
d[0] = 0
```

`d[0] = 0` er hele rettelsen av termstrukturen. ω og a kalibreres ved å matche
modellens simulerte impulsrespons mot den empiriske. På 79 år realpris ligger
andelen av et prissjokk som gjenstår etter ti år på 0,73–0,82, standardfeil om
lag 0,18; variansforholdstesten gir 0,66–0,79. Sentralanslag φ = 0,75, følsomhet
0,5 og 1,0. Forbeholdene i docstringen til `src/persistens.py` skal gjengis i
METODE.md. Medianforankring: `exp(d)` har median 1, så ingen `−½V`-korreksjon.

**Fondsregnskap (steg 3).** Hele netto kontantstrøm overføres til fondet; det
gjøres ingen fradrag på vei inn. Uttaket er det oljekorrigerte underskuddet.

```
Fond[t] = Fond[t−1] + SNCF[t] − uttak[t] + r·Fond[t−1]
```

Deterministisk, uten fordeling på avkastning. Med fondet på om lag 22 500 mrd.
kroner er ett prosentpoeng avkastning om lag 225 mrd. kroner, mot en årlig
kontantstrøm på om lag 686 mrd. kroner. En fordeling ville gjort viften til en
figur om aksjemarkedet. Valutakurs holdes fast, med fotnote.

---

## Åpne punkter

1. **Valutakursen bak Sokkeldirektoratets tall.** Siste frie inndata i steg 1. Energidepartementets forutsetning er trolig svaret.
2. **Horisonten i Sokkeldirektoratets kontantstrøm.** Full feltlevetid eller avkortet i 2050? Eget ledd i fossefiguren.
3. **`Gassprisgjennomslag = 0,50`.** Faktor to på 32–51 pst. av inntektsgrunnlaget. Parameter med standardverdi 1,0, bryter til 0,50. Avklares med ED.
4. **φ for gass** kan ikke estimeres troverdig på 28 år. Antakelse, ikke anslag.

---

## Arbeidsregler

- Norsk bokmål. `pst.`, `mrd. kroner`, komma som desimaltegn, mellomrom som tusenskille, «om lag», «anslås».
- Ingen hardkodede inndata. Alt leses fra `inndata.csv`.
- Enhver antakelse som ikke er estimert, merkes som antakelse i `METODE.md`.
- Excel er utdataformat, aldri regnemotor.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.inspiser        # steg 0, første handling
pytest -v
```
