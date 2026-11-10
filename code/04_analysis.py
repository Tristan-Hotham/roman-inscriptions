"""Step 4: the planned analysis (NOTES.md). Writes data/results.json (every number quoted anywhere), data/aoristic.csv (annual
curves), data/provinces_summary.csv, data/age_models.csv and SCR/mc.npz (Monte Carlo curves for the figures)."""
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from common import *

warnings.filterwarnings("ignore")
rng = np.random.default_rng(2026)
R = {}
I = pd.read_csv(f"{DATA}/inscriptions.csv.gz", low_memory=False)
prep = jload(f"{SCR}/prep.json")
YRS = np.arange(Y0, Y1 + 1)
NY = len(YRS)

# ---------------- Part 1: the epigraphic habit ----------------
dated = I.not_before.notna() & I.not_after.notna()
I["width"] = I.not_after - I.not_before
R["n"] = {"all": int(len(I)), "dated": int(dated.sum()), "edh": int(I.edh_id.notna().sum()), "edcs": int(I.edcs_id.notna().sum()),
          "main": int((dated & (I.width <= 100)).sum()), "w50": int((dated & (I.width <= 50)).sum()), "w200": int((dated & (I.width <= 200)).sum()),
          "swapped": prep["n_swapped"], "median_width": float(I.width.median()), "provinces_edcs": int(I.province.nunique()),
          "rome": int((I.province == "Roma").sum()), "italy": int((I.group == "Italy").sum()), "christian": int(I.christian.sum()), "christian_rome": int((I.christian & (I.province == "Roma")).sum())}
R["n"]["rome_italy_pc"] = 100 * (R["n"]["rome"] + R["n"]["italy"]) / R["n"]["all"]
R["n"]["rome_pc"] = 100 * R["n"]["rome"] / R["n"]["all"]
R["n"]["main_pc"] = 100 * R["n"]["main"] / R["n"]["dated"]


def aoristic(nb, na):
    """annual aoristic sum over YRS: each item spreads weight 1 over its years (inclusive); returns (curve, weight inside window)"""
    nb = np.asarray(nb, float); na = np.asarray(na, float)
    w = 1.0 / (na - nb + 1)
    a = np.clip(nb, Y0, Y1 + 1) - Y0; b = np.clip(na + 1, Y0, Y1 + 1) - Y0
    diff = np.zeros(NY + 2)
    np.add.at(diff, a.astype(int), w); np.add.at(diff, b.astype(int), -w)
    c = np.cumsum(diff)[:NY]
    return c, float(c.sum())


def ma(c, k=25):
    return np.convolve(c, np.ones(k) / k, mode="same")


def peak(c):
    m = ma(c)
    inner = (YRS >= Y0 + 12) & (YRS <= Y1 - 12)
    return int(YRS[inner][np.argmax(m[inner])])


def mc(nb, na, reps=1000, keep=False):
    """Monte Carlo dating: one uniform year per item per replicate; peak years and (optionally) the curves"""
    nb = np.asarray(nb, int); na = np.asarray(na, int)
    peaks = []; curves = []; raws = []
    for _ in range(reps):
        y = nb + np.floor(rng.random(len(nb)) * (na - nb + 1)).astype(int)
        inside = (y >= Y0) & (y <= Y1)
        h = np.bincount(y[inside] - Y0, minlength=NY).astype(float)
        peaks.append(peak(h))
        if keep:
            curves.append(ma(h)); raws.append(h)
    if keep:
        mc.raws = np.array(raws)   # unsmoothed replicate curves (for the window ratio, which is defined on the unsmoothed curve)
    return np.array(peaks), (np.array(curves) if keep else None)


def window_ratio(c, a=(193, 235), b=(250, 300)):
    m1 = c[(YRS >= a[0]) & (YRS <= a[1])].mean(); m2 = c[(YRS >= b[0]) & (YRS <= b[1])].mean()
    return float(m1), float(m2), float(m1 / m2)


D = I[dated].copy()
sets = {"main": D[D.width <= 100], "all_dated": D, "w50": D[D.width <= 50], "w200": D[D.width <= 200]}
curves = {}
R["habit"] = {}
for k, s in sets.items():
    c, inside = aoristic(s.not_before, s.not_after)
    curves[k] = c
    m1, m2, rr = window_ratio(c)
    R["habit"][k] = {"n": int(len(s)), "inside_pc": 100 * inside / len(s), "peak_year": peak(c), "mean_193_235": m1, "mean_250_300": m2, "ratio": rr,
                     "max_ma25": float(ma(c).max())}
pk, cur = mc(sets["main"].not_before, sets["main"].not_after, reps=1000, keep=True)
R["habit"]["main"]["mc_peak_lo"] = int(np.percentile(pk, 2.5)); R["habit"]["main"]["mc_peak_hi"] = int(np.percentile(pk, 97.5))
R["habit"]["main"]["mc_peak_median"] = int(np.median(pk))
band = np.percentile(cur, [2.5, 97.5], axis=0)
# MC ratio: on the unsmoothed replicate curves, like the point estimate (review fix: the smoothed curves gave an interval
# that did not contain the point estimate)
rat = []
for cc in mc.raws[:1000]:
    rat.append(cc[(YRS >= 193) & (YRS <= 235)].mean() / cc[(YRS >= 250) & (YRS <= 300)].mean())
R["habit"]["main"]["mc_ratio_lo"] = float(np.percentile(rat, 2.5)); R["habit"]["main"]["mc_ratio_hi"] = float(np.percentile(rat, 97.5))
h1 = R["habit"]["main"]
R["habit"]["h1a_supported"] = bool(175 <= h1["peak_year"] <= 250 and h1["ratio"] >= 1.5)
# decades: 1st, 2nd, 3rd century means (main)
c = curves["main"]
R["habit"]["century_mean"] = {str(a): float(c[(YRS >= a) & (YRS < a + 100)].mean()) for a in (1, 101, 201, 301)}
R["habit"]["c3_vs_c2"] = R["habit"]["century_mean"]["201"] / R["habit"]["century_mean"]["101"]
R["habit"]["fall_250_vs_peak"] = h1["mean_250_300"] / h1["max_ma25"]
# sensitivity table
R["habit"]["sens"] = [{"label": lab, "n": R["habit"][k]["n"], "peak": R["habit"][k]["peak_year"], "ratio": R["habit"][k]["ratio"]}
                      for k, lab in (("main", "Range 100 years or less (main)"), ("w50", "Range 50 years or less"), ("w200", "Range 200 years or less"), ("all_dated", "All dated"))]
pd.DataFrame({"year": YRS, **{k: np.round(v, 3) for k, v in curves.items()}, "mc_lo": np.round(band[0], 2), "mc_hi": np.round(band[1], 2)}).to_csv(f"{DATA}/aoristic.csv", index=False)

# two visible spikes: things dated to one year (AD 123: stamped bricks and objects, mostly in Rome) and Vesuvius (AD 79)
s123 = I[(I.not_before == 123) & (I.not_after == 123)]
s79 = I[(I.not_after == 79) & I.place.fillna("").str.contains("Pompei|Stabia|Herculaneum|Ercolano")]
R["spikes"] = {"n_123": int(len(s123)), "n_123_rome": int((s123.province == "Roma").sum()),
               "n_123_stamps": int(s123.type_auto.isin(["identification inscription", "owner/artist inscription"]).sum()),
               "n_vesuvius_79": int(len(s79)), "n_pompeii_79": int(s79.place.str.contains("Pompei").sum())}

# by type and Christian
M = sets["main"]
R["types"] = {}
tcur = {}
for lab, sel in (("epitaph", M.type == "epitaph"), ("votive", M.type == "votive"), ("honorific", M.type == "honorific"), ("building", M.type == "building"),
                 ("milestone", M.type == "milestone"), ("christian", M.christian), ("non_christian", ~M.christian)):
    s = M[sel]
    c, _ = aoristic(s.not_before, s.not_after)
    tcur[lab] = c
    p, _ = mc(s.not_before, s.not_after, reps=200)
    R["types"][lab] = {"n": int(len(s)), "peak_year": peak(c), "lo": int(np.percentile(p, 2.5)), "hi": int(np.percentile(p, 97.5))}
pd.DataFrame({"year": YRS, **{k: np.round(v, 3) for k, v in tcur.items()}}).to_csv(f"{DATA}/aoristic_types.csv", index=False)
cn, _ = aoristic(M[~M.christian].not_before, M[~M.christian].not_after)
m1, m2, rr = window_ratio(cn)
R["habit"]["non_christian"] = {"peak_year": peak(cn), "ratio": rr}

# by province (EDCS province, at least 1,000 dated in the main set) and by region group
R["prov_peaks"] = []
pcur = {}
for p_, s in M.groupby("province"):
    if len(s) < 1000:
        continue
    c, _ = aoristic(s.not_before, s.not_after)
    pk_, _ = mc(s.not_before, s.not_after, reps=200)
    R["prov_peaks"].append({"province": p_, "group": region_group(p_), "n": int(len(s)), "peak_year": peak(c), "lo": int(np.percentile(pk_, 2.5)),
                            "hi": int(np.percentile(pk_, 97.5)), "ratio": window_ratio(c)[2]})
    pcur[p_] = c
R["prov_peaks"].sort(key=lambda x: x["peak_year"])
R["n"]["prov_peaks"] = len(R["prov_peaks"])
R["n"]["prov_peaks_severan"] = sum(175 <= x["peak_year"] <= 250 for x in R["prov_peaks"])
gcur = {}
for g_, s in M.groupby("group"):
    c, _ = aoristic(s.not_before, s.not_after); gcur[g_] = c
pd.DataFrame({"year": YRS, **{k: np.round(v, 3) for k, v in gcur.items()}}).to_csv(f"{DATA}/aoristic_groups.csv", index=False)

# density per DARE province
area = prep["area_km2"]
P = I.groupby("dare_province").size()
rows = []
for k, a in area.items():
    rows.append({"dare_province": k, "area_km2": round(a), "n": int(P.get(k, 0)), "per1000km2": P.get(k, 0) / a * 1000})
PS = pd.DataFrame(rows).sort_values("per1000km2", ascending=False)
PS.to_csv(f"{DATA}/provinces_summary.csv", index=False)
PS2 = PS[PS.area_km2 > 5000]
R["density"] = {"top": PS2.head(6).to_dict("records"), "bottom": PS2[PS2.n > 0].tail(6).to_dict("records"), "n_prov": int(len(PS)),
                "rome_n": int(P.get("Roma (city)", 0)), "outside": int(P.get("outside DARE provinces", 0)),
                "britannia": PS[PS.dare_province == "Britannia"].to_dict("records")[0],
                "empire_per1000": float((len(I) - P.get("Roma (city)", 0) - P.get("outside DARE provinces", 0)) / sum(area.values()) * 1000),
                "empire_area_km2": float(sum(area.values()))}
R["urban"] = {k: 100 * v for k, v in I.urban_context.value_counts(normalize=True).to_dict().items()}
R["types_all"] = {k: int(v) for k, v in I.type.value_counts().to_dict().items()}

# ---------------- Part 2: ages ----------------
A = pd.read_csv(f"{DATA}/ages.csv.gz", low_memory=False)
an = jload(f"{SCR}/ages_n.json")
A["cluster"] = A.place.fillna(A.lat.round(2).astype(str) + "," + A.lon.round(2).astype(str))
R["ages"] = {"n_epitaphs": an["n_epitaphs"], "n": int(len(A)), "n_stones": int(A.lire_id.nunique()), "form_A": int((A.form == "A").sum()),
             "form_B": int((A.form == "B").sum()), "plus_minus": int(A.plus_minus.sum()), "stones_pc": 100 * A.lire_id.nunique() / an["n_epitaphs"],
             "validation": {"n_read": 200, "n_wrong": 1, "wrong_note": "years lived after a patron's death", "noage_read": 100, "noage_missed": 5,
                            "noage_missed_rule": 2, "noage_missed_outside_rule": 3}}


def whipple(x):
    x = x[(x >= 23) & (x <= 62)]
    return 500 * np.mean(x % 5 == 0) if len(x) else np.nan


def boot_whipple(df, reps=1000, lo=23, hi=62):
    d = df[(df.age >= lo) & (df.age <= hi)]
    g = d.groupby("lire_id").age.apply(np.array)
    arr = g.values; n = len(arr)
    m5 = np.array([np.sum(a % 5 == 0) for a in arr]); cnt = np.array([len(a) for a in arr])
    est = 500 * m5.sum() / cnt.sum()
    bs = []
    for _ in range(reps):
        j = rng.integers(0, n, n)
        bs.append(500 * m5[j].sum() / cnt[j].sum())
    return float(est), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), int(cnt.sum())


def myers(x):
    """Myers' blended index, ages 10 to 89 (0 = no preference, 90 = all on one digit)"""
    x = np.asarray(x)
    s1 = np.array([np.sum((x >= 10) & (x <= 79) & (x % 10 == d)) for d in range(10)])
    s2 = np.array([np.sum((x >= 20) & (x <= 89) & (x % 10 == d)) for d in range(10)])
    bl = s1 * np.arange(1, 11) + s2 * np.arange(9, -1, -1)
    p = 100 * bl / bl.sum()
    return float(np.sum(np.abs(p - 10)) / 2)


W = {}
w_all = boot_whipple(A)
R["ages"]["whipple"] = {"all": {"W": w_all[0], "lo": w_all[1], "hi": w_all[2], "n": w_all[3], "abcc": 100 * (1 - (w_all[0] - 100) / 400)}}
for g_ in GROUPS:
    s = A[A.group == g_]
    if ((s.age >= 23) & (s.age <= 62)).sum() < 200:
        continue
    w = boot_whipple(s)
    R["ages"]["whipple"][g_] = {"W": w[0], "lo": w[1], "hi": w[2], "n": w[3], "abcc": 100 * (1 - (w[0] - 100) / 400)}
R["ages"]["h2a_all_above_100"] = all(v["lo"] > 100 for v in R["ages"]["whipple"].values())
for u in ("large", "medium", "small", "rural"):
    w = boot_whipple(A[A.urban_context == u])
    R["ages"]["whipple"]["urban_" + u] = {"W": w[0], "lo": w[1], "hi": w[2], "n": w[3]}
for nm, s in (("christian", A[A.christian]), ("non_christian", A[~A.christian]), ("form_A", A[A.form == "A"]), ("form_B", A[A.form == "B"]),
              ("plus_minus", A[A.plus_minus]), ("no_plus_minus", A[~A.plus_minus])):
    w = boot_whipple(s, reps=300)
    R["ages"]["whipple"][nm] = {"W": w[0], "lo": w[1], "hi": w[2], "n": w[3]}
# terminal digits and the age histogram
x = A.age.values
R["ages"]["digits_23_62"] = {str(d): int(np.sum((x >= 23) & (x <= 62) & (x % 10 == d))) for d in range(10)}
R["ages"]["myers"] = {"all": myers(x)}
for g_ in GROUPS:
    s = A[A.group == g_].age.values
    if ((s >= 10) & (s <= 89)).sum() >= 300:
        R["ages"]["myers"][g_] = myers(s)
hist = np.bincount(np.clip(x, 0, 110), minlength=111)
pd.DataFrame({"age": np.arange(111), "n": hist}).to_csv(f"{DATA}/age_hist.csv", index=False)
# Hopkins-style descriptives
R["ages"]["hopkins"] = {"under10_pc": 100 * np.mean(x < 10), "under1_pc": 100 * np.mean(x < 1), "mean": float(x.mean()), "median": float(np.median(x)),
                        "n_100plus": int(np.sum(x >= 100)), "pc_70plus": 100 * np.mean(x >= 70), "by_group": {}}
for g_ in GROUPS:
    s = A[A.group == g_].age.values
    if len(s) >= 300:
        R["ages"]["hopkins"]["by_group"][g_] = {"n": int(len(s)), "mean": float(s.mean()), "median": float(np.median(s)), "under10_pc": 100 * np.mean(s < 10),
                                                "pc_70plus": 100 * np.mean(s >= 70), "n_100plus": int(np.sum(s >= 100))}
hb = R["ages"]["hopkins"]["by_group"]
R["ages"]["hopkins"]["mean_range"] = [min(v["mean"] for v in hb.values()), max(v["mean"] for v in hb.values())]
R["ages"]["hopkins"]["mean_min_group"] = min(hb, key=lambda k: hb[k]["mean"]); R["ages"]["hopkins"]["mean_max_group"] = max(hb, key=lambda k: hb[k]["mean"])

# the planned model
X = A[(A.age >= 23) & (A.age <= 62)].copy()
X["m5"] = (X.age % 5 == 0).astype(int)
X["band"] = pd.cut(X.age, [22, 32, 42, 52, 62], labels=["23-32", "33-42", "43-52", "53-62"]).astype(str)
X = X[X.group.isin(GROUPS) & X.urban_context.notna()]
X["grp"] = X.group.str.replace(" ", "_")
X["chr"] = X.christian.astype(int)
FORM = "m5 ~ C(grp, Treatment('Rome')) + C(urban_context, Treatment('large')) + C(band, Treatment('23-32')) + chr"


def fit(df, form=FORM):
    m = smf.glm(form, data=df, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df.cluster)[0]})
    return m


def orci(m, term):
    b = m.params[term]; se = m.bse[term]
    return {"or": float(np.exp(b)), "lo": float(np.exp(b - 1.96 * se)), "hi": float(np.exp(b + 1.96 * se)), "p": float(m.pvalues[term])}


m = fit(X)
TA = "C(grp, Treatment('Rome'))[T.Africa]"; TR_ = "C(urban_context, Treatment('large'))[T.rural]"
R["ages"]["model"] = {"n": int(m.nobs), "clusters": int(X.cluster.nunique()), "africa_vs_rome": orci(m, TA), "rural_vs_large": orci(m, TR_),
                      "bands": {b: orci(m, f"C(band, Treatment('23-32'))[T.{b}]") for b in ("33-42", "43-52", "53-62")},
                      "christian": orci(m, "chr"), "groups": {g_: orci(m, f"C(grp, Treatment('Rome'))[T.{g_.replace(' ', '_')}]") for g_ in GROUPS if g_ != "Rome" and f"C(grp, Treatment('Rome'))[T.{g_.replace(' ', '_')}]" in m.params},
                      "urban": {u: orci(m, f"C(urban_context, Treatment('large'))[T.{u}]") for u in ("medium", "small", "rural")}}
tab = pd.DataFrame({"term": m.params.index, "coef": m.params.values, "se": m.bse.values, "p": m.pvalues.values})
tab.to_csv(f"{DATA}/age_models.csv", index=False)
mm = R["ages"]["model"]
R["ages"]["h2b_supported"] = mm["africa_vs_rome"]["lo"] > 1
R["ages"]["h2c_supported"] = mm["rural_vs_large"]["lo"] > 1
R["ages"]["h2d_supported"] = all(mm["bands"][b]["or"] > 1 for b in mm["bands"]) and mm["bands"]["53-62"]["or"] > mm["bands"]["33-42"]["or"]
# robustness
rob = []
def add(lab, df, form=FORM):
    try:
        mr = fit(df, form)
        a = orci(mr, TA) if TA in mr.params else None
        r_ = orci(mr, TR_) if TR_ in mr.params else None
        rob.append({"label": lab, "n": int(mr.nobs), "africa": a, "rural": r_})
    except Exception as e:
        rob.append({"label": lab, "error": str(e)[:80]})
X72 = A[(A.age >= 23) & (A.age <= 72) & A.group.isin(GROUPS) & A.urban_context.notna()].copy()
X72["m5"] = (X72.age % 5 == 0).astype(int)
X72["band"] = pd.cut(X72.age, [22, 32, 42, 52, 62, 72], labels=["23-32", "33-42", "43-52", "53-62", "63-72"]).astype(str)
X72["grp"] = X72.group.str.replace(" ", "_"); X72["chr"] = X72.christian.astype(int)
add("Ages 23 to 72", X72)
add("Vixit form only", X[X.form == "A"])
add("Excluding Christian inscriptions", X[X.christian == 0], FORM.replace(" + chr", ""))
add("One age per stone (the first)", X[X["first"]])
add("Excluding plus minus ages", X[~X.plus_minus])
for g_ in GROUPS:
    if g_ in ("Rome", "Africa"):
        continue
    add(f"Leave out {g_}", X[X.group != g_])
R["ages"]["robust"] = rob
R["ages"]["robust_rural_all_above1"] = all(r_.get("rural") and r_["rural"]["lo"] > 1 for r_ in rob if "rural" in r_ and r_.get("rural"))
R["ages"]["robust_africa_all_above1"] = all(r_.get("africa") and r_["africa"]["lo"] > 1 for r_ in rob if r_.get("africa"))
# by century (midpoint of the date range, dated range 100 or less), descriptive
A["mid"] = (A.not_before + A.not_after) / 2
A["w"] = A.not_after - A.not_before
cent = {}
for a_, lab in ((-50, "1st c. BC to AD 50"), (51, "AD 51 to 150"), (151, "151 to 250"), (251, "251 to 350"), (351, "351 to 450")):
    s = A[(A.w <= 100) & (A.mid >= a_) & (A.mid < a_ + 100)]
    if ((s.age >= 23) & (s.age <= 62)).sum() >= 200:
        w = boot_whipple(s, reps=300)
        cent[lab] = {"W": w[0], "lo": w[1], "hi": w[2], "n": w[3]}
R["ages"]["by_period"] = cent

# ---------------- Part 3: soldiers ----------------
S = pd.read_csv(f"{DATA}/soldiers.csv")
sn = jload(f"{SCR}/soldiers_n.json")
St = S[~S.diploma].copy()
St["cluster"] = St.place.fillna(St.lat.round(2).astype(str) + "," + St.lon.round(2).astype(str))
R["soldiers"] = {"n_stones": sn["n_soldier_stones"], "n_diplomas": sn["n_diplomas"], "n_mapped": int(len(St)), "n_mapped_diplomas": int(S.diploma.sum()),
                 "mapped_pc": 100 * len(St) / sn["n_soldier_stones"], "n_place": int((St.precision == "place").sum()), "n_region": int((St.precision == "region").sum()),
                 "n_ambiguous_dropped": sn["n_ambiguous"], "how": St.how.value_counts().to_dict(),
                 "median_km": float(St.dist_km.median()), "pc_over_500": 100 * float((St.dist_km > 500).mean()), "pc_under_50": 100 * float((St.dist_km < 50).mean()),
                 "n_origins": int(St.origin.nunique()), "origin_check": {"tokens_used_2plus": int((pd.read_csv(f"{SCR}/origo_check.csv").groupby("token").size() >= 2).sum()), "singleton_sample": 60, "singleton_wrong": 4}}
st = St.copy()
st["early"] = st.not_after <= 100
st["late"] = (st.not_before >= 101) & (st.not_after <= 300)
P3 = st[st.early | st.late].copy()
P3["later"] = P3.late.astype(int)
P3["logd"] = np.log(P3.dist_km.clip(lower=1))


def qreg(df, reps=1000):
    df = df.reset_index(drop=True)
    b = smf.quantreg("logd ~ later", df).fit(q=0.5).params["later"]
    cl = pd.factorize(df.cluster)[0]; ncl = cl.max() + 1
    idx = [np.where(cl == k)[0] for k in range(ncl)]
    bs = []
    for _ in range(reps):
        pick = np.concatenate([idx[k] for k in rng.integers(0, ncl, ncl)])
        d = df.iloc[pick]
        if d.later.nunique() < 2:
            continue
        try:
            bs.append(smf.quantreg("logd ~ later", d).fit(q=0.5).params["later"])
        except Exception:
            pass
    return {"b": float(b), "ratio": float(np.exp(b)), "lo": float(np.exp(np.percentile(bs, 2.5))), "hi": float(np.exp(np.percentile(bs, 97.5))),
            "n": int(len(df)), "n_early": int((df.later == 0).sum()), "n_late": int((df.later == 1).sum()), "clusters": int(ncl),
            "med_early": float(df[df.later == 0].dist_km.median()), "med_late": float(df[df.later == 1].dist_km.median()),
            "over500_early": 100 * float((df[df.later == 0].dist_km > 500).mean()), "over500_late": 100 * float((df[df.later == 1].dist_km > 500).mean())}


R["soldiers"]["h3"] = qreg(P3)
R["soldiers"]["h3_supported"] = R["soldiers"]["h3"]["hi"] < 1
rob3 = [{"label": "Main: all mapped soldier stones", **R["soldiers"]["h3"]}]
for lab, sel in (("City origins only", P3.precision == "place"), ("Excluding findspots in Rome", P3.province != "Roma"),
                 ("Excluding Rome and Italy", ~P3.group.isin(["Rome", "Italy"])), ("Date range 100 years or less", (P3.not_after - P3.not_before) <= 100)):
    d = P3[sel]
    if d.later.nunique() == 2 and len(d) >= 40:
        rob3.append({"label": lab, **qreg(d, reps=500)})
R["soldiers"]["robust"] = rob3
# top routes (origin region or town -> EDCS province of the findspot)
St["dest"] = St.province
routes = St.groupby(["origin", "dest"]).size().sort_values(ascending=False).head(12)
R["soldiers"]["top_routes"] = [{"origin": o, "dest": d_, "n": int(n_)} for (o, d_), n_ in routes.items()]
R["soldiers"]["top_origins"] = [{"origin": o, "n": int(n_)} for o, n_ in St.origin.value_counts().head(10).items()]
R["soldiers"]["rome_dest_pc"] = 100 * float((St.province == "Roma").mean())
R["soldiers"]["longest"] = St.sort_values("dist_km", ascending=False).head(3)[["origin", "province", "dist_km"]].to_dict("records")

jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({"habit": {k: R["habit"]["main"][k] for k in ("peak_year", "mc_peak_lo", "mc_peak_hi", "ratio", "mc_ratio_lo", "mc_ratio_hi")},
                  "sens": R["habit"]["sens"], "types": R["types"]}, indent=0))
