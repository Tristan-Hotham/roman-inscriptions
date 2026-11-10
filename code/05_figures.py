"""Step 5: static figures for the paper (release/paper/f_*.pdf), the blog (release/blog/b_*.png, 1800 px) and the page (img/*.jpg).
All numbers come from data/ files written by steps 1 to 4."""
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm, ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
I = pd.read_csv(f"{DATA}/inscriptions.csv.gz", usecols=["lon", "lat", "province", "group", "type", "not_before", "not_after"], low_memory=False)
YR = pd.read_csv(f"{DATA}/aoristic.csv")

# ---------- 1. density map ----------
x, y = proj(I.lon.values, I.lat.values)
fig = plt.figure(figsize=(11, 8.6), facecolor=PAPER)
ax = fig.add_axes([0.0, 0.0, 1.0, 0.9])
base_map(ax)
bins = [1, 3, 10, 30, 100, 300, 100000]
hb = ax.hexbin(x, y, gridsize=(170, 125), extent=EXT, mincnt=1, bins=None, linewidths=0, zorder=3,
               cmap=ListedColormap(SEQ), norm=BoundaryNorm(bins, len(SEQ)))
lab = ["1 to 2", "3 to 9", "10 to 29", "30 to 99", "100 to 299", "300 or more"]
lg = ax.legend(handles=[Patch(facecolor=c, label=l) for c, l in zip(SEQ, lab)], loc="lower left", title="Inscriptions per hexagon (about 30 km)",
               fontsize=9.5, title_fontsize=10, frameon=True, ncol=3, bbox_to_anchor=(0.01, 0.01))
lg.get_frame().set_facecolor(PAPER); lg.get_frame().set_edgecolor(RULE)
# label points (lon, lat) chosen to sit on open sea (review fix: Rome, Carthage and Salona labels sat on Sardinia and Italy)
for nm, lo, la, tlo, tla in (("Rome", 12.49, 41.89, 12.1, 39.9), ("Carthage", 10.32, 36.85, 7.4, 37.95), ("Mainz", 8.27, 50.0, 4.0, 56.0),
                             ("Salona", 16.48, 43.54, 17.45, 41.8)):
    px_, py_ = proj(lo, la); tx_, ty_ = proj(tlo, tla)
    ax.annotate(nm, (px_, py_), xytext=(tx_, ty_), va="center", fontsize=(9 if nm == "Salona" else 10.5), color=FG, ha="center",
                arrowprops=dict(arrowstyle="-", color=FG, lw=0.7), bbox=dict(boxstyle="round,pad=0.25", fc=PAPER, ec=RULE), zorder=6)
fig.text(0.02, 0.965, "Where Romans wrote", fontproperties=DISP, fontsize=24, color=FG, va="top")
fig.text(0.02, 0.92, f"{R['n']['all']:,} Latin inscriptions (LIRE v2.1) by findspot; grey lines: provinces of about AD 117 (DARE)", fontproperties=SERP,
         fontsize=12.5, color=MUT, va="top")
savefig(fig, "map", blog="map", img="map")

# ---------- 2. the curve through time ----------
fig, ax = plt.subplots(figsize=(11, 5.6), facecolor=PAPER)
ax.set_facecolor(PAPER); style_axes(ax)
ax.axvspan(193, 235, color="#EFE3C4", zorder=0)
ax.text(214, 0.97, "Severan\nemperors", transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=9.5, color=MUT)
ax.fill_between(YR.year, YR.mc_lo, YR.mc_hi, color="#C9D7E3", lw=0, label="Monte Carlo dating, 95% band (25-year mean)")
ax.plot(YR.year, YR.main, color=FG, lw=1.0, alpha=0.55, label="Aoristic sum, each year")
ax.plot(YR.year, np.convolve(YR.main, np.ones(25) / 25, mode="same"), color=HOT, lw=2.2, label="25-year moving mean")
h = R["habit"]["main"]
ax.annotate(f"Peak: AD {h['peak_year']}\n(95% interval AD {h['mc_peak_lo']} to {h['mc_peak_hi']})", (h["peak_year"], h["max_ma25"]),
            xytext=(-30, h["max_ma25"] * 1.18), fontsize=10, color=FG, arrowprops=dict(arrowstyle="-", color=FG, lw=0.7))
ax.set_xlim(-50, 400); ax.set_ylim(0, None)
ax.set_xlabel("Year (negative = BC)"); ax.set_ylabel("Inscriptions per year")
ax.legend(frameon=False, fontsize=9.5, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3)  # review fix: legend overlapped labels
sp = R["spikes"]
ax.annotate(f"AD 123: {sp['n_123']:,} items dated\nto one year, mostly in Rome", (123, YR.main[YR.year == 123].iloc[0]), xytext=(-40, 1350), ha="left", fontsize=9.5, color=FG,
            arrowprops=dict(arrowstyle="-", color=FG, lw=0.7))
ax.annotate("AD 79: Vesuvius\n(Pompeii, Herculaneum)", (79, YR.main[YR.year == 78].iloc[0]), xytext=(20, 900), fontsize=9.5, color=FG,
            arrowprops=dict(arrowstyle="-", color=FG, lw=0.7), ha="center")
ax.set_title(f"Dated inscriptions per year, empire-wide (date range 100 years or less, N = {h['n']:,})", loc="left", fontsize=12, color=FG)
fig.tight_layout()
savefig(fig, "time", blog="time", img="time")

# ---------- 3. Rome and Italy vs the provinces ----------
G = pd.read_csv(f"{DATA}/aoristic_groups.csv")
fig, axs = plt.subplots(2, 4, figsize=(12, 5.8), facecolor=PAPER, sharex=True)
order = ["Rome", "Italy", "Africa", "Hispania", "Gaul and Germany", "Danube and Balkans", "Britain", "East"]
for a, g in zip(axs.flat, order):
    a.set_facecolor(PAPER); style_axes(a)
    a.axvspan(193, 235, color="#EFE3C4", zorder=0)
    v = np.convolve(G[g], np.ones(25) / 25, mode="same")
    a.fill_between(G.year, 0, v, color=GCOL[g], alpha=0.25, lw=0); a.plot(G.year, v, color=GCOL[g], lw=1.8)
    a.set_title(g, loc="left", fontsize=11, color=FG); a.set_xlim(-50, 400); a.set_ylim(0, v.max() * 1.15)
    a.tick_params(labelsize=8.5)
fig.suptitle("Each region's own curve: inscriptions per year, 25-year mean (shaded band: the Severan emperors, AD 193 to 235)", x=0.01, ha="left", fontsize=12, color=FG)
fig.tight_layout(rect=(0, 0, 1, 0.95))
savefig(fig, "groups", blog="groups", img="groups")

# ---------- 4. province peaks ----------
P = R["prov_peaks"]
fig, ax = plt.subplots(figsize=(9, 7.6), facecolor=PAPER)
ax.set_facecolor(PAPER)
ax.axvspan(193, 235, color="#EFE3C4", zorder=0)
for i, p in enumerate(P):
    c = GCOL.get(p["group"], MUT)
    ax.plot([p["lo"], p["hi"]], [i, i], color=c, lw=2.2, solid_capstyle="round")
    ax.plot(p["peak_year"], i, "o", color=c, ms=7, mec=PAPER, mew=1.5)
ax.set_yticks(range(len(P))); ax.set_yticklabels([f"{p['province'].replace(' / ', ', ')} ({p['n']:,})" for p in P], fontsize=9)
ax.set_xlim(-60, 400); ax.grid(axis="x", color=RULE, lw=0.6); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.set_xlabel("Peak year (dot) and Monte Carlo 95% interval (bar)")
groups_present = [g for g in order + ["Islands"] if any(p["group"] == g for p in P)]
ax.legend(handles=[Line2D([0], [0], marker="o", color=GCOL[g], lw=2, label=g) for g in groups_present], frameon=False, fontsize=9, loc="lower right")
ax.set_title("When each province wrote most\n(provinces with 1,000 or more dated inscriptions)", loc="left", fontsize=12, color=FG)
fig.tight_layout()
savefig(fig, "peaks", blog="peaks", img="peaks")

# ---------- 5. ages: terminal digits and the age histogram ----------
H = pd.read_csv(f"{DATA}/age_hist.csv")
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.8), facecolor=PAPER, gridspec_kw={"width_ratios": [2.2, 1]})
for a in (a1, a2):
    a.set_facecolor(PAPER); style_axes(a)
cols = [HOT if v % 5 == 0 and v > 0 else "#9AA3AD" for v in H.age]
a1.bar(H.age, H.n, width=0.8, color=cols)
a1.set_xlim(-1, 101); a1.set_xlabel("Age at death as written"); a1.set_ylabel("Stated ages")
a1.set_title(f"{R['ages']['n']:,} ages on {R['ages']['n_stones']:,} epitaphs: red = multiples of 5", loc="left", fontsize=11.5, color=FG)
d = R["ages"]["digits_23_62"]
vals = [d[str(i)] for i in range(10)]
a2.bar(range(10), vals, color=[HOT if i in (0, 5) else "#9AA3AD" for i in range(10)], width=0.7)
a2.axhline(sum(vals) / 10, color=FG, lw=1, ls=(0, (3, 3)))
a2.text(9.4, sum(vals) / 10 * 1.06, "no rounding", ha="right", fontsize=9, color=FG)
a2.set_xticks(range(10)); a2.set_xlabel("Last digit of the age (ages 23 to 62)")
w = R["ages"]["whipple"]["all"]
a2.set_title(f"Whipple index {w['W']:.0f}\n(100 = no rounding, 500 = all)", loc="left", fontsize=11.5, color=FG)
fig.tight_layout()
savefig(fig, "ages", blog="ages", img="ages")

# ---------- 6. Whipple by region and setting ----------
WW = R["ages"]["whipple"]
rows = [(g, WW[g]) for g in ["Rome", "Italy", "Islands", "Gaul and Germany", "Africa", "Hispania", "Danube and Balkans"] if g in WW]
rows2 = [(lab, WW["urban_" + u]) for u, lab in (("large", "Large city"), ("medium", "Medium town"), ("small", "Small town"), ("rural", "Countryside"))]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6), facecolor=PAPER, gridspec_kw={"width_ratios": [1.4, 1]})
for a, rr, title in ((a1, rows, "By region"), (a2, rows2, "By setting (LIRE urban context)")):
    a.set_facecolor(PAPER)
    for i, (lab, v) in enumerate(rr):
        c = GCOL.get(lab, "#55606B")
        a.barh(i, v["W"] - 100, left=100, color=c, height=0.6)
        a.plot([v["lo"], v["hi"]], [i, i], color=FG, lw=1.2)
        a.text(v["hi"] + 6, i, f"{v['W']:.0f}", va="center", fontsize=9.5, color=FG)
    a.set_yticks(range(len(rr))); a.set_yticklabels([f"{l} ({v['n']:,})" for l, v in rr], fontsize=9.5)
    a.set_xlim(100, 420); a.axvline(100, color=FG, lw=0.8)
    a.grid(axis="x", color=RULE, lw=0.6); a.set_axisbelow(True)
    for s in ("top", "right"): a.spines[s].set_visible(False)
    a.set_title(title, loc="left", fontsize=11.5, color=FG); a.set_xlabel("Whipple index (ages 23 to 62), 95% CI")
fig.tight_layout()
savefig(fig, "whipple", blog="whipple", img="whipple")

# ---------- 7. Hopkins: what the tombstones say about age ----------
HB = R["ages"]["hopkins"]["by_group"]
gs = [g for g in ["Rome", "Italy", "Gaul and Germany", "Danube and Balkans", "Islands", "Hispania", "Africa"] if g in HB]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4), facecolor=PAPER)
for a, key, title, fmt_ in ((a1, "mean", "Mean age at death on the stones", "{:.0f}"), (a2, "under10_pc", "Share of stated ages under 10 (%)", "{:.0f}%")):
    a.set_facecolor(PAPER)
    vals = [HB[g][key] for g in gs]
    a.barh(range(len(gs)), vals, color=[GCOL[g] for g in gs], height=0.6)
    for i, v in enumerate(vals):
        a.text(v + max(vals) * 0.02, i, fmt_.format(v), va="center", fontsize=9.5, color=FG)
    a.set_yticks(range(len(gs))); a.set_yticklabels(gs, fontsize=9.5); a.invert_yaxis()
    a.grid(axis="x", color=RULE, lw=0.6); a.set_axisbelow(True)
    for s in ("top", "right"): a.spines[s].set_visible(False)
    a.set_title(title, loc="left", fontsize=11.5, color=FG); a.set_xlim(0, max(vals) * 1.18)
fig.tight_layout()
savefig(fig, "hopkins", blog="hopkins", img="hopkins")

# ---------- 8. soldiers' flows ----------
S = pd.read_csv(f"{DATA}/soldiers.csv")
S = S[~S.diploma]
fig = plt.figure(figsize=(11, 8.6), facecolor=PAPER)
ax = fig.add_axes([0.0, 0.0, 1.0, 0.9])
base_map(ax, lw=0.35)
from matplotlib.collections import LineCollection
ox, oy = proj(S.o_lon.values, S.o_lat.values); dx_, dy_ = proj(S.lon.values, S.lat.values)
early = (S.not_after <= 100).values; late = (S.not_before >= 101).values
segs = []; cols = []
for i in range(len(S)):
    # a gentle arc: a quadratic curve bowed to the left of travel
    p0 = np.array([ox[i], oy[i]]); p2 = np.array([dx_[i], dy_[i]])
    mid = (p0 + p2) / 2; v = p2 - p0; nrm = np.array([-v[1], v[0]]) * 0.18
    t = np.linspace(0, 1, 24)[:, None]
    segs.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * (mid + nrm) + t ** 2 * p2)
    cols.append(COOL if early[i] else (HOT if late[i] else "#8C8C8C"))
ax.add_collection(LineCollection(segs, colors=cols, linewidths=0.7, alpha=0.45, zorder=5))
ax.scatter(dx_, dy_, s=7, color=FG, zorder=6, lw=0)
ax.scatter(ox, oy, s=16, facecolor="white", edgecolor=FG, lw=0.7, zorder=7)
lg = ax.legend(handles=[Line2D([0], [0], color=COOL, lw=2, label="stone dated before AD 101"), Line2D([0], [0], color=HOT, lw=2, label="stone dated AD 101 or later"),
                        Line2D([0], [0], color="#8C8C8C", lw=2, label="date range spans AD 100"),
                        Line2D([0], [0], marker="o", color="white", mec=FG, lw=0, label="stated origin (town or region)"),
                        Line2D([0], [0], marker="o", color=FG, lw=0, ms=4, label="where the stone stands")],
               loc="lower left", fontsize=9.5, frameon=True, bbox_to_anchor=(0.01, 0.01))
lg.get_frame().set_facecolor(PAPER); lg.get_frame().set_edgecolor(RULE)
s_ = R["soldiers"]
fig.text(0.02, 0.965, "Soldiers far from home", fontproperties=DISP, fontsize=24, color=FG, va="top")
fig.text(0.02, 0.92, f"{s_['n_mapped']:,} military stones that state where the man came from; median distance {s_['median_km']:,.0f} km", fontproperties=SERP,
         fontsize=12.5, color=MUT, va="top")
savefig(fig, "soldiers", blog="soldiers", img="soldiers")

# ---------- 9. robustness: age models and soldier distance ----------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5.6), facecolor=PAPER)
rob = [r for r in R["ages"]["robust"] if r.get("rural")]
main = R["ages"]["model"]
rows = [("Main model", main["africa_vs_rome"], main["rural_vs_large"])] + [(r["label"], r["africa"], r["rural"]) for r in rob]
for a, k, title in ((a1, 1, "Africa vs Rome"), (a2, 2, "Countryside vs large city")):
    pass
a1.set_facecolor(PAPER)
for i, (lab, af, ru) in enumerate(rows):
    for off, v, c in ((-0.15, af, GCOL["Africa"]), (0.15, ru, "#55606B")):
        if v:
            a1.plot([v["lo"], v["hi"]], [i + off, i + off], color=c, lw=2); a1.plot(v["or"], i + off, "o", color=c, ms=5)
a1.axvline(1, color=FG, lw=0.8); a1.set_yticks(range(len(rows))); a1.set_yticklabels([r[0] for r in rows], fontsize=8.5); a1.invert_yaxis()
a1.set_xscale("log"); a1.set_xticks([0.5, 1, 2, 3]); a1.set_xticklabels(["0.5", "1", "2", "3"])
a1.legend(handles=[Line2D([0], [0], color=GCOL["Africa"], marker="o", label="Africa vs Rome"), Line2D([0], [0], color="#55606B", marker="o", label="Countryside vs large city")],
          frameon=False, fontsize=9, loc="lower right")
a1.set_title("Odds that an age is a multiple of 5 (95% CI)", loc="left", fontsize=11, color=FG)
for s in ("top", "right"): a1.spines[s].set_visible(False)
a2.set_facecolor(PAPER)
rs = R["soldiers"]["robust"]
for i, r in enumerate(rs):
    a2.plot([r["lo"], r["hi"]], [i, i], color=HOT, lw=2); a2.plot(r["ratio"], i, "o", color=HOT, ms=6)
    a2.text(r["hi"] * 1.03, i, f"{r['ratio']:.2f} (N {r['n']})", va="center", fontsize=8.5, color=FG)
a2.axvline(1, color=FG, lw=0.8); a2.set_yticks(range(len(rs))); a2.set_yticklabels([r["label"].replace("Main: all mapped soldier stones", "Main: all mapped stones") for r in rs], fontsize=8.5)
a2.invert_yaxis(); a2.set_xscale("log"); a2.set_xticks([0.5, 1, 2, 3]); a2.set_xticklabels(["0.5", "1", "2", "3"]); a2.set_xlim(0.5, 3.5)
a2.set_title("Soldiers: later vs earlier median distance (95% CI)", loc="left", fontsize=11, color=FG)
for s in ("top", "right"): a2.spines[s].set_visible(False)
fig.tight_layout()
savefig(fig, "robust", blog=None, img="robust")
print("figures done")
