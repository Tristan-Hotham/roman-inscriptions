# roman-inscriptions: working notes and analysis plan

"Where Romans wrote: 200,000 Latin inscriptions mapped". Author Dr Tristan Hotham, Independent researcher.

## Status

- Phase 1 (this section, 2026): data inspected for structure only (columns, value lists, date-range widths, EDCS status categories). No time curve, age distribution, rounding index or soldier distance has been computed. The plan below is pre-specified in a written plan before any outcome is looked at. Anything not in it is labelled exploratory.
- Phase 2: run the plan, then paper, page, blog, collage, GIF.

## Data (facts found in phase 1)

- LIRE v2.1 (Latin Inscriptions of the Roman Empire; Kaše, Heřmánková and Sobotková; Zenodo 10.5281/zenodo.7577788; CC BY 4.0): 203,466 Latin inscriptions, every one with a findspot point and `geotemporal? = True` (LIRE keeps only inscriptions with coordinates and a date range overlapping 50 BC to AD 350). Merged from EDCS (Epigraphik-Datenbank Clauss/Slaby) and EDH (Epigraphic Database Heidelberg): 64,869 rows have an EDH id, 200,962 an EDCS id.
- Dates: `not_before`, `not_after` (years; negative = BC). 203,380 have both. Median width 99 years; 72% have a range of 100 years or less, 37% 50 or less. 38 rows have not_before > not_after (to be swapped and flagged).
- The "clean" EDH fields (`type_of_inscription_clean`, `type_of_monument_clean`, `material_clean`, `province_label_clean`) exist only for EDH rows (64k). For the whole set I use: `province` (EDCS province names, 65 values incl. Rome, the Italian regions and a few "A | B" ambiguous cases), `type_of_inscription_auto` (LIRE's own classifier, filled for 174k rows), `status` (EDCS category list: "tituli sepulcrales", "milites", "inscriptiones christianae", ...), `urban_context` (large, medium, small, rural: distance to a city in Hanson's list, as set by LIRE).
- `people`: EDH only, names and sex; no age, origin or military data. Ages and origins must therefore come from the text.
- Text: `inscription` (EDCS/EDH edition with Leiden-style brackets: expansions in (), restorations in [], line breaks /) and `clean_text_interpretive_word` (expanded, brackets removed). Ages and origins are read from `inscription`, so that restored numerals can be identified.
- Provinces: Digital Atlas of the Roman Empire (DARE, Johan Åhlfeldt, Lund University), province polygons of about AD 117 with the eleven Augustan regions of Italy, as packaged on GitHub by klokantech/roman-empire (data/provinces.geojson, provinces_label.geojson, places_low/medium/high.geojson). Licence: CC BY 4.0 (checked at review). Used for the map outline, province areas and the place gazetteer for soldiers' origins.

## Pre-specified analysis plan

### Part 1. The epigraphic habit in space and time

- Unit: inscription. Time: aoristic weighting. Each dated inscription spreads a total weight of 1 evenly over the years from not_before to not_after inclusive (a range of zero years counts as one year). The empire-wide curve is the sum, per year, from 50 BC to AD 400, smoothed only by the binning (25-year bins for display; annual for the peak).
- Main set: inscriptions with a date range of 100 years or less (about 72%). Sensitivity: all dated; range 50 or less; range 200 or less; Monte Carlo dating (draw one year uniformly in each range, 1,000 replicates) giving a 95% band for the curve and for the peak year.
- H1a (MacMullen 1982): the number of inscriptions per year rises through the first and second centuries to a peak in the Severan period (AD 193 to 235) and then falls steeply. Test: the year of the maximum of the aoristic curve (main set, 25-year moving average) and its Monte Carlo 95% interval; ratio of the mean annual sum in 193 to 235 to that in 250 to 300. Against H1a: a peak outside 175 to 250, or a ratio under 1.5.
- H1b: the timing differs by type and region. Peak years computed separately for epitaphs, votive, honorific, building and milestone inscriptions (by `type_of_inscription_auto`), for Christian inscriptions (EDCS status), and for each province with at least 1,000 dated inscriptions in the main set. Descriptive; no ranking claims beyond what the intervals allow.
- Space: inscriptions per 1,000 km2 by province (DARE area, equal-area projection) and per hexagon (about 50 km across) on the map. Rome and the Italian regions are reported separately; the density figure is descriptive and depends on modern collecting (stated).
- Exploratory only: share of inscriptions in large, medium, small and rural contexts by province.

### Part 2. Ages at death on epitaphs and age rounding

- Extraction (fixed now, before any distribution is seen): in `inscription`, remove expansion brackets "(" ")" and line breaks; tokenise; a stated age is a token of the form an/ann/annis/annos/annorum/annoru/anno/annu (any case) immediately followed by a Roman numeral token [IVXL]+ (C allowed only as "C" = 100 or a prefix of up to 110) with no square bracket, question mark or editorial mark in or touching the numeral; and either (a) one of vixit, vixsit, bixit, vix, vix(it) abbreviations "v" or "vix" within the two tokens before, or (b) the form annorum/annor/annoru (genitive "aged N"). "anno" counts only under (a) (to exclude era and consular dating). Excluded if any of milit, stip, aer, meruit, militavit, militans, stipendiorum, emeritus, sacerdo, mil appears in the three tokens before (years of service, not age). Ages 0 to 110 kept. Number words (e.g. octoginta) are not read; this is reported. Only epitaphs count: `type_of_inscription_auto == "epitaph"` or EDCS status "tituli sepulcrales". Several ages on one stone are all kept (a row per age); the inscription is the cluster.
- A random sample of 200 extracted ages will be read by eye against the text and the error rate reported; a second sample of 100 epitaphs with no extracted age will be read to estimate missed ages.
- Rounding measure: Whipple's index on ages 23 to 62: W = 500 × (share of ages ending in 0 or 5). 100 = no rounding, 500 = every age a multiple of 5. Also the ABCC numeracy index (A'Hearn, Baten and Crayen 2009) = 100 × (1 − (W − 100)/400). Bootstrap 95% CIs by resampling inscriptions.
- H2a: ages on epitaphs are rounded everywhere: W > 100 in every province group with at least 200 ages in 23 to 62. Against: any group with a CI including 100.
- H2b (Duncan-Jones 1977, 1990): rounding is heavier in the African provinces (Africa Proconsularis, Numidia, Mauretania Caesariensis, Mauretania Tingitana) than in the city of Rome. Test: logistic regression of "age is a multiple of 5" (ages 23 to 62) on region group (Rome; rest of Italy; Africa; Hispania; Gaul and the Germanies; Danube and Balkans; Britain; East), urban context, age band (23 to 32, 33 to 42, 43 to 52, 53 to 62) and Christian status, SEs clustered by findspot (LIRE `place`, else rounded coordinates). Main contrast: Africa vs Rome (odds ratio, 95% CI). Against: OR at or below 1.
- H2c: rounding is heavier in rural than in large urban contexts (same model). Against: OR at or below 1.
- H2d: rounding rises with age (age band terms). Against: no increase.
- Robustness: (1) ages 23 to 72; (2) only stones with the "vixit" form; (3) excluding Christian inscriptions; (4) leave one region group out for the rural contrast; (5) one age per stone (the first); (6) Myers' blended index as an alternative measure (all terminal digits, ages 10 to 89); (7) dated stones only, by century (aoristic: midpoint), descriptive.
- Life expectancy: no estimate will be made. Instead, following Hopkins (1966), the paper shows why: (i) the share of commemorated deaths under age 10 compared with the share expected in any plausible pre-modern population (cited, not computed); (ii) the mean recorded age by region group, whose spread is far larger than any plausible mortality difference; (iii) the count of ages of 100 and over. These are descriptive.

### Part 3. Soldiers on the move

- Soldier stones: EDCS status contains "milites", or the text has a military term (miles, mil(es) leg(ionis), legio/leg with numeral, cohors/coh, ala, eques, veteranus/vet, centurio, signifer, beneficiarius, optio, praetorianus, classis). Military diplomas (status "diplomata militaria" or type "military diploma") are a separate group (their origo is the recipient's home; findspot is often near home, so they are reported apart and not mixed into the stone flows).
- Origo: "natione X", "nat(ione) X", "domo X", "domu X", "natus X", "cives X", "civis X". X = the next one or two tokens, with tribe names (the 35 voting tribes) removed and a following city name kept. Restored or uncertain tokens are dropped.
- Gazetteer: exact (case-insensitive, accents removed) match of X or its nominative guess (-ae to -a, -i to -is/-um/-ium, -o to -um/-us, -e to -is) to DARE Latin place names; nationes (Thrax, Bessus, Syrus, Pannonius, Dalmata, Batavus, Raetus, Noricus, Dacus, Hispanus, Afer, Maurus, Surus, Cappadox, Frisius, Tungrus, Ubius, Treverus, Breucus, Azalus, Boius and similar) mapped by hand to a region point (DARE province label point or the people's main town), flagged `precision = region`. Every origin that is used at least twice is checked by eye and recorded in code/origo_overrides.csv; singletons are used only if the automatic match is exact and unique.
- Outcome: great-circle distance from origin point to findspot (km).
- H3 (Forni 1953; Mann 1983): soldiers' origins become more local over time. Test: compare median distance (and the share from more than 500 km) for stones dated wholly before AD 100 (not_after <= 100) with those dated wholly from AD 101 to 300 (not_before >= 101). Quantile regression of log distance on period, with SEs clustered by findspot. Against: no fall, or a CI including zero.
- Robustness: city origins only (no region-level nationes); legionaries vs auxiliaries/fleet (by term); excluding Rome (praetorians and the fleet at Misenum distort the picture); range 100 years or less only.
- If fewer than 300 soldier stones with a mapped origo result, Part 3 is reported as descriptive only and kept small.

### Planned outputs

Aoristic curve (empire and by type), province densities, map of hex densities with a time slider, age heaping charts (terminal digits; Whipple by region with CIs), soldier flows map and distance by period. Everything quoted goes through data/results.json.

### Known caveats to state

- The corpus records what survived, was found, was published and was entered in EDCS/EDH. Rome and Italy are dominant (about 47% of rows are Rome or the Italian regions); the density map shows modern collecting as much as ancient writing.
- Dates are editors' ranges, many of them conventional (e.g. "71 to 300"), and some type-based (Christian epitaphs are dated late because they are Christian). The aoristic curve inherits this.
- LIRE excludes inscriptions without coordinates or outside its date window; Greek inscriptions are not in it.
- Ages are ages as written by commemorators, not true ages.

## Log

- 2026: plan written after structural inspection only.

## Phase 2 log (construction details found while running the plan)

Every change below was made while reading the planned validation samples, before the outcome it could affect was computed, unless marked otherwise.

- Ages (02_ages.py). Reading the first validation sample showed four things the written rule handled badly, all fixed before any distribution was computed: (1) years of marriage ("cum qua vixit annis X", "vixit mecum") are not ages: excluded when cum/mecum/secum/tecum is in the four tokens before the year word; (2) Roman numerals are parsed strictly as written on stone (IIII, VIIII, XXXX, and the forms IIX = 8 and XXC = 80); anything else is not a numeral; (3) a restored letter in the word "annos" itself is accepted (the numeral must still be intact); (4) "annos plus minus LX" is read, with the age flagged as plus minus (the plan's "immediately followed" would have dropped these; they are reported separately and excluded in a robustness check).
- Age validation (final rule): of 200 extracted ages read against the text, 199 are ages at death as written; one counts years lived after a patron's death. Of 100 epitaphs with no extracted age, 5 state an age legibly: 2 that the rule should have caught (an age after "vixit plus minus annos" and one excluded by the marriage window) and 3 outside the rule (an age with "anni" and no vixit, an age with "fecit annos", an age of 115).
- Soldiers (03_soldiers.py). Military stones defined as planned (EDCS "milites" or a military word); this includes officers' and senators' careers that name a legion. Origin forms: domo, natione, civis, and a voting tribe after the filiation followed within three tokens by a DARE place form (the commonest way a legionary's origo is written, e.g. "Pollia Mutina"; the plan's "filius <tribe> ... X" form). Fixes found by reading every origin token used twice or more (126 tokens) and a sample of 60 singletons: automatic matches are allowed only against DARE settlements (types 11 to 13) west of 46 E, and a token that is a common personal name in EDH (20 or more uses) is matched only to a major town; 16 tokens mapped by hand (e.g. Bononia to Bologna, Mediolano to Milan, Philippopoli to Plovdiv), 33 rejected (cognomina such as Niger, Magnus, Silo; ambiguous names such as Heraclea, Augusta, Foro, Neapoli; a legion name, Gallica; Stobera, whose DARE namesake is in the far east). code/origo_overrides.csv lists every decision. 4 of the 60 singletons read were wrong and were corrected; the rest of the singletons were not all read, so some error remains (about 7% on that sample).
- 865 soldier stones have a mapped origin (4.4% of 19,484 military stones), above the planned 300 threshold, so Part 3 is reported as planned.

## Phase 2 results against the plan (main specifications)

- H1a, empire-wide: NOT supported by the planned rule. The annual curve (range 100 years or less) peaks in AD 68 (Monte Carlo 95% interval AD 13 to 71), not in the Severan period, because Rome and Italy, 61% of the corpus, peak in the early first century. The fall after the Severans is strong: the mean in 193 to 235 is 2.2 times that in 250 to 300 (Monte Carlo 2.16 to 2.24). Province by province (H1b) the Severan peak is common outside Italy: 10 of the 27 provinces with at least 1,000 dated inscriptions peak between 175 and 250 (Africa, Numidia, Mauretania Caesariensis, Dacia, Noricum, both Pannonias, Germania inferior, Baetica, Dalmatia), Italy and Narbonensis in the first century, Rome (Christian catacombs) in the late fourth.
- H2a supported: Whipple 303 (95% CI 298 to 307) overall; every region group above 100.
- H2b not supported: Africa vs Rome OR 1.22 (0.88 to 1.68) once urban context, age band and Christian status are held fixed, although the raw Whipple index is higher in Africa (323) than in Rome (248).
- H2c supported in the main model (rural vs large city OR 1.50, 1.09 to 2.07) but not robust: with the vixit form only the CI includes 1 (OR 1.29, 0.92 to 1.82).
- H2d supported: rounding rises with age band (OR 1.7, 2.1, 2.5 against 23 to 32).
- H3 not supported: later soldiers' stated origins are not nearer; the main quantile model gives a median distance 1.37 times longer for stones of 101 to 300 (1.22 to 1.90), but city origins alone show no change (1.03, 0.81 to 1.65). The difference comes from the mix of origin forms (ethnic nationes of the fleet and guard in Rome and Italy are later), not from a measurable change in recruitment.

- Final values are in data/results.json (the numbers above were copied from it; results.json is authoritative). Egypt and Africa nationes were moved from DARE province label points (which fall in the desert) to Memphis and Carthage before the final run.
- Three of the six planned hypotheses failed by their own criteria (H1a, H2b, H3); H2c holds in the main model but not in the vixit-only check.

## Independent review (2026)

- The Monte Carlo interval for the 193 to 235 / 250 to 300 ratio had been computed on 25-year smoothed replicate curves while the point estimate uses the unsmoothed curve, so the interval (2.06 to 2.13) did not contain the estimate (2.20). Fixed in 04_analysis.py (ratio on the unsmoothed replicates; same draws, nothing else changes): 2.16 to 2.24. results.json patched with the values from an exact replay of the same random draws.
- Added n.christian_rome (42,181) so the paper no longer attributes all 49,396 Christian inscriptions to Rome.
- DARE licence corrected from CC BY-SA to CC BY 4.0 (DARE's own statement, as quoted by AWOL; the vector map project states CC BY).
- Wording: 154 is a count of ages of 100 or more in Africa (on 153 stones), not stones; "61% of all Latin inscriptions" now "of the inscriptions in LIRE".
- Figures: map labels moved onto open sea; time-chart legend moved below the plot; clipped titles fixed; collage Rome label moved off Calabria; GIF legend now shows all six classes with the right colours, below the map.
