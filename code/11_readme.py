"""Step 11: README.md from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
h = R["habit"]["main"]; a = R["ages"]; s = R["soldiers"]; m = a["model"]
md = f"""# Where Romans wrote

{R['n']['all']:,} Latin inscriptions from the Roman Empire (LIRE v2.1, merged from EDCS and EDH) mapped by findspot and through time, with three tests fixed in advance in a written plan (NOTES.md): the timing of the "epigraphic habit", the rounding of ages on tombstones, and the distance between soldiers' stated homes and their stones. A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/{SLUG}/
Paper: {{https://doi.org/10.5281/zenodo.24114976}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/roman-inscriptions/}}
Code and data: {REPO}

## Headline results

- Rome has {R['n']['rome']:,} inscriptions ({R['n']['rome_pc']:.1f}%); Rome and the rest of Italy {R['n']['rome_italy_pc']:.1f}%. Greek inscriptions are not in the data.
- The epigraphic habit (inscriptions with a date range of 100 years or less, N = {h['n']:,}; aoristic counts): the mean number per year in AD 193 to 235 is {h['ratio']:.2f} times that in 250 to 300 (Monte Carlo 95% interval {h['mc_ratio_lo']:.2f} to {h['mc_ratio_hi']:.2f}).
- But the empire-wide peak is AD {h['peak_year']} (95% interval AD {h['mc_peak_lo']} to {h['mc_peak_hi']}), not Severan: H1a fails by its planned rule, because Rome and Italy peak in the first century. {R['n']['prov_peaks_severan']} of the {R['n']['prov_peaks']} provinces with at least 1,000 dated inscriptions peak in AD 175 to 250. Votive inscriptions peak in AD {R['types']['votive']['peak_year']}, honorific in {R['types']['honorific']['peak_year']}, milestones in {R['types']['milestone']['peak_year']}.
- Ages at death: {a['n']:,} stated ages on {a['n_stones']:,} epitaphs (199 of 200 checked by hand correct). Whipple index {a['whipple']['all']['W']:.1f} (95% CI {a['whipple']['all']['lo']:.1f} to {a['whipple']['all']['hi']:.1f}); Rome {a['whipple']['Rome']['W']:.0f}, Africa {a['whipple']['Africa']['W']:.0f}, Danube and Balkans {a['whipple']['Danube and Balkans']['W']:.0f}.
- Planned model (ages 23 to 62, clustered by findspot, N = {m['n']:,}): Africa vs Rome OR {m['africa_vs_rome']['or']:.2f} ({m['africa_vs_rome']['lo']:.2f} to {m['africa_vs_rome']['hi']:.2f}), not supported; rural vs large city OR {m['rural_vs_large']['or']:.2f} ({m['rural_vs_large']['lo']:.2f} to {m['rural_vs_large']['hi']:.2f}), supported but not robust (vixit form only: {a['robust_vixit_rural']['or']:.2f}, {a['robust_vixit_rural']['lo']:.2f} to {a['robust_vixit_rural']['hi']:.2f}); rounding rises with age (OR {m['bands']['53-62']['or']:.2f} for 53 to 62 against 23 to 32).
- Tombstones are not life tables: mean stated age {a['hopkins']['by_group']['Rome']['mean']:.1f} in Rome, {a['hopkins']['by_group']['Africa']['mean']:.1f} in Africa; {a['hopkins']['by_group']['Africa']['n_100plus']} African ages of 100 or more.
- Soldiers: {s['n_mapped']:,} of {s['n_stones']:,} military stones ({s['mapped_pc']:.1f}%) name a home that could be mapped; median distance {s['median_km']:.0f} km, {s['pc_over_500']:.0f}% over 500 km. Later stones (AD 101 to 300) name homes further away, not nearer (ratio of medians {s['h3']['ratio']:.2f}, {s['h3']['lo']:.2f} to {s['h3']['hi']:.2f}); town origins only: {s['city_only']['ratio']:.2f} ({s['city_only']['lo']:.2f} to {s['city_only']['hi']:.2f}). H3 not supported; the stones that name a home are a selected sample.

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

Hotham, T. (2026) Where Romans Wrote: The Epigraphic Habit, Age Rounding and Soldiers' Origins in 200,000 Latin Inscriptions. Zenodo. {{https://doi.org/10.5281/zenodo.24114976}}
"""
for bad in ("—", "–", "DSIT", "DCMS"):
    assert bad not in md, bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(md)
print("README", len(md.split()), "words")
