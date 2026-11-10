"""Step 10: blog post and meta (release/blog), Reddit post (reddit/post.md), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24114976, https://doi.org/10.5281/zenodo.24114976 and https://blog.tristanhotham.com/2026/10/31/roman-inscriptions/ are left for the publisher to fill."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_Where_Romans_Wrote"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
h = R["habit"]["main"]
meta = {"title": "Where Romans wrote",
        "slug": "roman-inscriptions",
        "excerpt": f"I mapped {R['n']['all']:,} Latin inscriptions through time. Under the Severans the empire carved {h['ratio']:.1f} times as many a year as in AD 250 to 300; ages on tombstones were rounded to fives; and soldiers' stated homes were a median {R['soldiers']['median_km']:,.0f} km from their stones.",
        "seo_description": f"{R['n']['all']:,} Latin inscriptions mapped through time: the rise and fall of Roman writing, rounded ages on tombstones and soldiers far from home.",
        "tags": ["maps", "data visualisation", "Roman Empire", "Latin inscriptions", "epigraphy", "ancient history", "demography", "Roman army"],
        "header_alt": "Title card on pale paper reading 'Where Romans wrote' beside a map of the Roman Empire covered in orange hexagons, darkest in central Italy and along the Rhine."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

s_ = R["soldiers"]; a_ = R["ages"]
reddit = f"""**Title:** [OC] I mapped {R['n']['all']:,} Latin inscriptions from the Roman Empire. Under the Severan emperors Romans carved {h['ratio']:.1f}x as many a year as two generations later.

**Body:**

Every Latin inscription in the LIRE dataset (tombstones, altars, honours, milestones), placed by findspot and spread over its date range.

- {R['n']['rome_italy_pc']:.0f}% of the inscriptions in the dataset come from Rome ({R['n']['rome']:,}) and the rest of Italy.
- AD 193 to 235 produced {h['ratio']:.1f} times as many inscriptions a year as AD 250 to 300. But the empire-wide peak is AD {h['peak_year']}: Italy wrote first, and {R['n']['prov_peaks_severan']} of {R['n']['prov_peaks']} big provinces peaked in AD 175 to 250.
- {a_['n']:,} ages at death on tombstones: ages ending in 0 or 5 are hugely over-represented (Whipple index {a_['whipple']['all']['W']:.0f}, where 100 = no rounding, 500 = all rounded).
- {a_['hopkins']['by_group']['Africa']['n_100plus']} ages on tombstones in Roman Africa are 100 or more. Tombstones are not life tables.
- {s_['n_mapped']:,} soldiers' stones name the man's home: median {s_['median_km']:,.0f} km away, {s_['pc_over_500']:.0f}% more than 500 km.

Caveats: these are the inscriptions that survived, were found and were digitised, so Rome and Italy dominate and Greek inscriptions are not included. Dates are editors' ranges.

Interactive map with a time slider: https://maps.tristanhotham.com/roman-inscriptions/

**Source comment:**

Data: LIRE v2.1 (Kaše, Heřmánková and Sobotková, Aarhus University; built from the Epigraphik-Datenbank Clauss/Slaby and the Epigraphic Database Heidelberg), CC BY 4.0. Provinces and ancient places: Digital Atlas of the Roman Empire (Lund University). Method: aoristic counts with Monte Carlo dating; ages read with a fixed rule checked by hand; analysis pre-specified in a written plan. Tools: Python (pandas, statsmodels, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/roman-inscriptions
"""
for bad in ("\u2014", "\u2013", "--"):
    assert bad not in reddit
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(reddit)

Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in ("inscriptions.csv.gz", "ages.csv.gz", "soldiers.csv", "aoristic.csv", "aoristic_types.csv", "aoristic_groups.csv", "age_hist.csv", "age_models.csv",
               "provinces_summary.csv", "provinces.geojson", "results.json"):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("``", "\"").replace("''", "\"").replace("~", " ").replace("\\textit{", "").replace("}", "").replace("\\", "")
zmeta = {"title": "Where Romans Wrote: The Epigraphic Habit, Age Rounding and Soldiers' Origins in 200,000 Latin Inscriptions",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/roman-inscriptions/}}.</p>"
                        "<p>Sources: LIRE v2.1, Latin Inscriptions of the Roman Empire (V. Kaše, P. Heřmánková and A. Sobotková, Aarhus University; Zenodo doi:10.5281/zenodo.7577788; "
                        "CC BY 4.0), built from the Epigraphik-Datenbank Clauss/Slaby and the Epigraphic Database Heidelberg; provinces and ancient places from the Digital Atlas "
                        "of the Roman Empire (J. Åhlfeldt, Lund University; CC BY 4.0); Natural Earth. Text, figures and derived data CC BY 4.0; "
                        "code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["Latin epigraphy", "epigraphic habit", "aoristic analysis", "age heaping", "Whipple index", "Roman army", "recruitment", "digital epigraphy", "Roman Empire"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.5281/zenodo.7577788", "relation": "references", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
