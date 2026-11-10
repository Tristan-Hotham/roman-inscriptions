# Where Romans wrote

203,466 Latin inscriptions from the Roman Empire (LIRE v2.1, merged from EDCS and EDH) mapped by findspot and through time, with three tests fixed in advance in a written plan (NOTES.md): the timing of the "epigraphic habit", the rounding of ages on tombstones, and the distance between soldiers' stated homes and their stones. A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/roman-inscriptions/
Paper: https://doi.org/10.5281/zenodo.24114976
Blog post: https://blog.tristanhotham.com/2026/10/31/roman-inscriptions/
Code and data: https://github.com/Tristan-Hotham/roman-inscriptions

## Headline results

- Rome has 75,301 inscriptions (37.0%); Rome and the rest of Italy 61.0%. Greek inscriptions are not in the data.
- The epigraphic habit (inscriptions with a date range of 100 years or less, N = 147,438; aoristic counts): the mean number per year in AD 193 to 235 is 2.20 times that in 250 to 300 (Monte Carlo 95% interval 2.16 to 2.24).
- But the empire-wide peak is AD 68 (95% interval AD 13 to 71), not Severan: H1a fails by its planned rule, because Rome and Italy peak in the first century. 10 of the 27 provinces with at least 1,000 dated inscriptions peak in AD 175 to 250. Votive inscriptions peak in AD 209, honorific in 205, milestones in 247.
- Ages at death: 29,598 stated ages on 27,387 epitaphs (199 of 200 checked by hand correct). Whipple index 302.6 (95% CI 298.4 to 306.8); Rome 248, Africa 323, Danube and Balkans 372.
- Planned model (ages 23 to 62, clustered by findspot, N = 14,036): Africa vs Rome OR 1.22 (0.88 to 1.68), not supported; rural vs large city OR 1.50 (1.09 to 2.07), supported but not robust (vixit form only: 1.29, 0.92 to 1.82); rounding rises with age (OR 2.48 for 53 to 62 against 23 to 32).
- Tombstones are not life tables: mean stated age 23.2 in Rome, 47.8 in Africa; 154 African ages of 100 or more.
- Soldiers: 865 of 19,484 military stones (4.4%) name a home that could be mapped; median distance 674 km, 68% over 500 km. Later stones (AD 101 to 300) name homes further away, not nearer (ratio of medians 1.37, 1.22 to 1.90); town origins only: 1.03 (0.81 to 1.65). H3 not supported; the stones that name a home are a selected sample.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; hexagons (about 35 km) with a 25-year time slider and play button, filter by type, soldiers' journeys, DARE provinces, search by findspot, popups linking to EDCS and EDH, layers panel, full screen. |
| `img/*.jpg` | Figures on the page. |
| `header.png` | Social card, 1200 x 630. |
| `data/inscriptions.csv.gz` | One row per LIRE inscription, without texts: LIRE, EDCS, EDH and Trismegistos ids; findspot point and name; EDCS and DARE province; regional group; urban context; type; Christian and epitaph flags; dates. |
| `data/ages.csv.gz` | One row per stated age at death (no text): form, plus minus flag, province, setting, dates. |
| `data/soldiers.csv` | Military stones with a mapped origin: origin form and word, origin point and precision, findspot, dates, distance. |
| `data/aoristic*.csv`, `data/age_hist.csv`, `data/age_models.csv`, `data/provinces_summary.csv` | Curves, age histogram, model coefficients, province densities. |
| `data/provinces.geojson` | DARE provinces (simplified) with counts and areas. |
| `data/hex.json`, `data/flows.json`, `data/places.json`, `data/site.json` | Page data. |
| `data/results.json` | Every number quoted anywhere. |
| `code/` | Scripts in order, templates, hand decisions on origins (`natio.csv`, `origo_overrides.csv`), `qa.js`. |
| `release/` | Paper (PDF, LaTeX, figures, `cover_note.md`), blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the looping GIF and the post text. |
| `NOTES.md` | The analysis plan, written before any result, and the log of changes. |

## Method in brief

- Time: each inscription's weight is spread evenly over its date range (aoristic); 1,000 Monte Carlo draws of one year per inscription give intervals. Main set: ranges of 100 years or less; checks with 50, 200 and all.
- Ages: "ann-" word followed by an intact Roman numeral, after "vixit" or in the form "annorum N"; not years of service or marriage; epitaphs only. Whipple index (23 to 62) with a stone bootstrap; logistic model with errors clustered by findspot.
- Soldiers: origins from "domo", "natione", "civis" or tribe plus town, matched to DARE; every origin used twice or more checked by eye. Median regression with a findspot cluster bootstrap.

## How to rerun

Needs Python 3 with numpy, pandas, pyarrow, shapely, pyproj, statsmodels, matplotlib, Pillow, fontTools; xelatex; node with Playwright for QA. Inputs are listed in `code/common.py` (LIRE parquet from Zenodo; DARE files from `git clone https://github.com/klokantech/roman-empire`, data/ copied to the scratch folder).

```
python3 code/01_prepare.py      # slim table, DARE provinces
python3 code/02_ages.py         # ages at death
python3 code/03_soldiers.py     # soldiers' origins
python3 code/04_analysis.py     # the planned analysis (a few minutes)
python3 code/04b_derived.py     # derived numbers
python3 code/05_figures.py      # figures
python3 code/06_site_data.py    # page data
python3 code/07_site.py         # index.html
python3 code/08_paper.py        # paper (DOI=10.5281/zenodo.N to fill the DOI)
python3 code/09_header.py       # header.png
python3 reddit/collage.py       # collage
python3 code/10_release.py      # blog, Reddit post, Zenodo files
python3 code/11_readme.py       # this README
node code/qa.js                 # screenshots
```

## Sources and licences

- LIRE v2.1, Latin Inscriptions of the Roman Empire, V. Kaše, P. Heřmánková and A. Sobotková (SDAM, Aarhus University), Zenodo doi:10.5281/zenodo.7577788, CC BY 4.0; built from EDCS (M. Clauss et al.) and EDH (G. Alföldy and C. Witschel, eds).
- Digital Atlas of the Roman Empire, J. Åhlfeldt, Lund University (CC BY 4.0), via github.com/klokantech/roman-empire.
- Base map: OpenFreeMap Positron (OpenStreetMap, ODbL). Static maps: Natural Earth (public domain).
- Code MIT; text, figures and derived data CC BY 4.0. See LICENSE.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.

## Citation

Hotham, T. (2026) Where Romans Wrote: The Epigraphic Habit, Age Rounding and Soldiers' Origins in 200,000 Latin Inscriptions. Zenodo. https://doi.org/10.5281/zenodo.24114976
