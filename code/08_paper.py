"""Step 8: the paper. Fills code/paper_template.tex + paper_body.tex from data/results.json, builds the tables and compiles with
xelatex. Output: release/paper/Hotham_Where_Romans_Wrote.pdf and .tex beside the f_*.pdf figures. The DOI stays a placeholder
(https://doi.org/10.5281/zenodo.24114976 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/08_paper.py"""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Where_Romans_Wrote"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    for k in ("f0", "f1", "f2", "f3"):
        if f == k: return f"{float(v):.{k[1]}f}".replace("-", "$-$")
    return tex(str(v))


def yr(v):
    return f"{int(v)}" if v > 0 else f"{-int(v)} BC"


def table(label, caption, cols, head, rows, size="\\small", spec=None):
    return (f"\\begin{{table}}[tbp]\\centering{size}\\caption{{{caption}}}\\label{{tab:{label}}}\\begin{{tabular}}{{{spec or cols}}}\\toprule {head}\\\\\\midrule\n"
            + "".join(r + "\\\\\n" for r in rows) + "\\bottomrule\\end{tabular}\\end{table}")


I = pd.read_csv(f"{DATA}/inscriptions.csv.gz", usecols=["group", "not_before", "not_after", "epitaph"], low_memory=False)
A = pd.read_csv(f"{DATA}/ages.csv.gz", usecols=["group"], low_memory=False)
S = pd.read_csv(f"{DATA}/soldiers.csv"); S = S[~S.diploma]
I["main"] = (I.not_after - I.not_before) <= 100
rows = []
for g in GROUPS + ["Other"]:
    s = I[I.group == g]
    if not len(s): continue
    rows.append(f"{tex(g)} & {len(s):,} & {100 * len(s) / len(I):.1f} & {int(s.main.sum()):,} & {int(s.epitaph.sum()):,} & {int((A.group == g).sum()):,} & {int((S.group == g).sum()):,}")
rows.append(f"\\midrule All & {len(I):,} & 100.0 & {int(I.main.sum()):,} & {int(I.epitaph.sum()):,} & {len(A):,} & {len(S):,}")
TC = table("corpus", "The corpus by regional group (EDCS provinces grouped; Appendix B): inscriptions, share, inscriptions with a date range of 100 years or less (the main set of Part 1), epitaphs, extracted ages, and military stones with a mapped origin (by findspot).",
           "lrrrrrr", "Group & Inscriptions & \\% & Range $\\leq$100 & Epitaphs & Ages & Soldiers", rows)

h = R["habit"]
rows = [f"{tex(x['label'])} & {x['n']:,} & {x['peak']} & {x['ratio']:.2f}" for x in h["sens"]]
rows.append(f"Main set, Monte Carlo (1,000 draws) & {h['main']['n']:,} & {h['main']['mc_peak_median']} [{h['main']['mc_peak_lo']}, {h['main']['mc_peak_hi']}] & {h['main']['ratio']:.2f} [{h['main']['mc_ratio_lo']:.2f}, {h['main']['mc_ratio_hi']:.2f}]")
TH = table("habit", "H1a. Peak year of the 25-year moving mean of the aoristic sum, and the ratio of the mean annual count in AD 193 to 235 to that in 250 to 300, by dating set. Brackets: Monte Carlo 95\\% intervals. The planned test required a peak in 175 to 250 and a ratio of at least 1.5.",
           "lrrr", "Dating set & N & Peak (AD) & Ratio 193--235 / 250--300".replace("--", " to "), rows)

TL = {"epitaph": "Epitaphs", "votive": "Votive", "honorific": "Honorific", "building": "Building or dedicatory", "milestone": "Milestones", "christian": "Christian (EDCS category)", "non_christian": "Not Christian"}
rows = [f"{TL[k]} & {v['n']:,} & {yr(v['peak_year'])} & {yr(v['lo'])} to {yr(v['hi'])}" for k, v in R["types"].items()]
TT = table("types", "Peak year by type of inscription (LIRE type; main set) with Monte Carlo 95\\% intervals (200 replicates).", "lrrr", "Type & N & Peak (AD) & 95\\% interval", rows)

rows = [f"{tex(p['province'].replace(' / ', ', '))} & {tex(p['group'])} & {p['n']:,} & {yr(p['peak_year'])} & {yr(p['lo'])} to {yr(p['hi'])} & {p['ratio']:.1f}" for p in R["prov_peaks"]]
TP = table("peaks", "Peak year by EDCS province (main set, provinces with at least 1,000 inscriptions), Monte Carlo 95\\% interval (200 replicates), and the ratio of the mean annual count in 193 to 235 to that in 250 to 300.",
           "llrrrr", "Province & Group & N & Peak & 95\\% interval & Ratio", rows, size="\\footnotesize")

W = R["ages"]["whipple"]; M = R["ages"]["myers"]
rows = [f"All ages & {W['all']['n']:,} & {W['all']['W']:.1f} & [{W['all']['lo']:.1f}, {W['all']['hi']:.1f}] & {W['all']['abcc']:.1f} & {M['all']:.1f}"]
rows.append("\\multicolumn{6}{l}{\\textit{Regional group}}")
for g in GROUPS:
    if g in W:
        rows.append(f"\\quad {tex(g)} & {W[g]['n']:,} & {W[g]['W']:.1f} & [{W[g]['lo']:.1f}, {W[g]['hi']:.1f}] & {W[g]['abcc']:.1f} & {M.get(g, float('nan')):.1f}")
rows.append("\\multicolumn{6}{l}{\\textit{Urban context}}")
for u in ("large", "medium", "small", "rural"):
    v = W["urban_" + u]; rows.append(f"\\quad {u} & {v['n']:,} & {v['W']:.1f} & [{v['lo']:.1f}, {v['hi']:.1f}] & & ")
rows.append("\\multicolumn{6}{l}{\\textit{Form and status}}")
for k, lab in (("form_A", "vixit form"), ("form_B", "genitive form (annorum)"), ("plus_minus", "given plus minus"), ("christian", "Christian"), ("non_christian", "not Christian")):
    v = W[k]; rows.append(f"\\quad {lab} & {v['n']:,} & {v['W']:.1f} & [{v['lo']:.1f}, {v['hi']:.1f}] & & ")
TW = table("whipple", "Age rounding: Whipple's index on ages 23 to 62 with bootstrap 95\\% intervals (stones resampled), the ABCC index, and Myers' blended index (ages 10 to 89; groups with at least 300 ages). N: ages 23 to 62. Britain and the East have fewer than 200 ages in the range.",
           "lrrlrr", "Subset & N & Whipple & 95\\% CI & ABCC & Myers", rows)

mm = R["ages"]["model"]
f = lambda v: f"{v['or']:.2f} & [{v['lo']:.2f}, {v['hi']:.2f}] & {v['p']:.3f}"
rows = ["\\multicolumn{4}{l}{\\textit{Regional group (reference: Rome)}}"] + [f"\\quad {tex(g)} & {f(v)}" for g, v in mm["groups"].items()]
rows += ["\\multicolumn{4}{l}{\\textit{Urban context (reference: large)}}"] + [f"\\quad {u} & {f(v)}" for u, v in mm["urban"].items()]
rows += ["\\multicolumn{4}{l}{\\textit{Age band (reference: 23 to 32)}}"] + [f"\\quad {b.replace('-', ' to ')} & {f(v)}" for b, v in mm["bands"].items()]
rows += [f"Christian inscription & {f(mm['christian'])}"]
TM = table("model", f"The planned model (H2b to H2d): logistic regression of whether a stated age (23 to 62) is a multiple of five. Odds ratios with 95\\% intervals from standard errors clustered by findspot. N = {mm['n']:,} ages, {mm['clusters']:,} findspots.",
           "lrlr", "Term & Odds ratio & 95\\% CI & $p$", rows)

rows = [f"Main model & {mm['n']:,} & {mm['africa_vs_rome']['or']:.2f} [{mm['africa_vs_rome']['lo']:.2f}, {mm['africa_vs_rome']['hi']:.2f}] & {mm['rural_vs_large']['or']:.2f} [{mm['rural_vs_large']['lo']:.2f}, {mm['rural_vs_large']['hi']:.2f}]"]
for r in R["ages"]["robust"]:
    a, u = r.get("africa"), r.get("rural")
    rows.append(f"{tex(r['label'])} & {r['n']:,} & " + (f"{a['or']:.2f} [{a['lo']:.2f}, {a['hi']:.2f}]" if a else "") + " & " + (f"{u['or']:.2f} [{u['lo']:.2f}, {u['hi']:.2f}]" if u else ""))
TR = table("robust", "Planned robustness checks for the age model: odds ratios (95\\% CI) for Africa against Rome and rural against large urban contexts.", "lrll", "Specification & N & Africa vs Rome & Rural vs large", rows)

HB = R["ages"]["hopkins"]["by_group"]
rows = [f"{tex(g)} & {v['n']:,} & {v['mean']:.1f} & {v['median']:.0f} & {v['under10_pc']:.1f} & {v['pc_70plus']:.1f} & {v['n_100plus']}" for g, v in HB.items()]
hh = R["ages"]["hopkins"]
rows.append(f"\\midrule All & {R['ages']['n']:,} & {hh['mean']:.1f} & {hh['median']:.0f} & {hh['under10_pc']:.1f} & {hh['pc_70plus']:.1f} & {hh['n_100plus']}")
TK = table("hopkins", "Stated ages at death by regional group (groups with at least 300 ages): mean, median, share under ten, share of 70 or more, and number of ages of 100 or more.",
           "lrrrrrr", "Group & Ages & Mean & Median & Under 10 (\\%) & 70+ (\\%) & 100+", rows)

rows = [f"{tex(r['label'])} & {r['n_early']} / {r['n_late']} & {r['med_early']:.0f} & {r['med_late']:.0f} & {r['ratio']:.2f} & [{r['lo']:.2f}, {r['hi']:.2f}]" for r in R["soldiers"]["robust"]]
T3 = table("h3", "H3. Median distance (km) from stated origin to findspot for military stones dated wholly before AD 101 (earlier) and wholly in 101 to 300 (later), and the ratio of medians from a median regression of log distance, with cluster bootstrap 95\\% intervals (findspots resampled). H3 predicted a ratio below 1.",
           "lrrrrl", "Specification & N earlier / later & Earlier & Later & Ratio & 95\\% CI", rows)

o = R["soldiers"]["top_origins"]; rt = R["soldiers"]["top_routes"]
rows = [f"{tex(a['origin'])} & {a['n']} & {tex(b['origin'])} to {tex(b['dest'].replace(' / ', ', '))} & {b['n']}" for a, b in zip(o, rt)]
TO = table("routes", "The ten commonest stated origins on military stones and the commonest origin to findspot-province routes.", "lrlr", "Origin & Stones & Route & Stones", rows, size="\\footnotesize")

MF = pd.read_csv(f"{DATA}/age_models.csv")
lab = lambda t: (t.replace("C(grp, Treatment('Rome'))[T.", "Group: ").replace("C(urban_context, Treatment('large'))[T.", "Urban: ").replace("C(band, Treatment('23-32'))[T.", "Age band: ").replace("]", "").replace("_", " ").replace("chr", "Christian"))
rows = [f"{tex(lab(r.term))} & {r.coef:.3f} & ({r.se:.3f}) & {r.p:.3f}".replace("-0.", "$-$0.").replace(" -", " $-$") for r in MF.itertuples()]
TF = table("modelfull", f"Full coefficients of the planned age model (logit scale; clustered standard errors). N = {mm['n']:,}.", "lrrr", "Term & Coefficient & (SE) & $p$", rows, size="\\footnotesize")

t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("%%BODY%%", open(os.path.join(ROOT, "code", "paper_body.tex"), encoding="utf-8").read())
t = t.replace("{{AI}}", AI)
for k, v in (("TABLE_CORPUS", TC), ("TABLE_HABIT", TH), ("TABLE_TYPES", TT), ("TABLE_PEAKS", TP), ("TABLE_WHIPPLE", TW), ("TABLE_MODEL", TM), ("TABLE_ROBUST", TR),
             ("TABLE_HOPKINS", TK), ("TABLE_H3", T3), ("TABLE_ROUTES", TO), ("TABLE_MODELFULL", TF)):
    assert "{{" + k + "}}" in t, k
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m_: tfmt(get(R, m_.group(1)), m_.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24114976", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:5]
for bad in ("DSIT", "DCMS", "pre-registered", "preregistered", "civil serv"):
    assert bad not in t, bad
cites = set(re.findall(r"\\cite[pt]?(?:\[[^\]]*\])*\{([^}]+)\}", t)); cites = {c.strip() for x in cites for c in x.split(",")}
items = set(re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", t))
assert cites <= items, cites - items
labels = set(re.findall(r"\\label\{([^}]+)\}", t)); refs = set(re.findall(r"\\ref\{([^}]+)\}", t))
print("references", len(items), "uncited", sorted(items - cites), "; unreferenced labels", sorted(l for l in labels - refs if not l.startswith("sec:")), "; missing", sorted(refs - labels))
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:15])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
body = txt.split("\nReferences\n")[0]
ab = txt.split("Abstract")[1].split("Keywords")[0]
print("paper", r.returncode, len(txt.split()), "words total;", len(body.split()), "before references; abstract", len(ab.split()), "words;",
      [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013"))
