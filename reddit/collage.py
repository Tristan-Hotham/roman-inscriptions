"""Reddit collage (r/dataisbeautiful style, light background): the density map of Latin inscriptions, the curve through time,
the rounding of ages on tombstones and the soldiers' journeys, with the key numbers. Reads data/ files and data/results.json.
Run from the study root: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection
from figstyle import *

R = jload(f"{DATA}/results.json")
I = pd.read_csv(f"{DATA}/inscriptions.csv.gz", usecols=["lon", "lat"])
YR = pd.read_csv(f"{DATA}/aoristic.csv")
G = pd.read_csv(f"{DATA}/aoristic_groups.csv")
H = pd.read_csv(f"{DATA}/age_hist.csv")
S = pd.read_csv(f"{DATA}/soldiers.csv"); S = S[~S.diploma]

fig = plt.figure(figsize=(16, 13.5), facecolor=PAPER)
fig.text(0.03, 0.972, "Where Romans wrote: 203,466 Latin inscriptions".replace("203,466", f"{R['n']['all']:,}"), fontproperties=DISP, fontsize=34, color=FG, va="top")
fig.text(0.03, 0.928, f"Every Latin inscription in the LIRE dataset by findspot and date. Under the Severans (AD 193 to 235)\nthe empire carved {R['habit']['main']['ratio']:.1f} times as many a year as in AD 250 to 300.",
         fontproperties=SERP, fontsize=15.5, color=MUT, va="top")

# big map
ax = fig.add_axes([0.01, 0.40, 0.60, 0.50])
ext = (-2350, 2550, -1450, 1650)
base_map(ax, ext=ext, lw=0.35)
x, y = proj(I.lon.values, I.lat.values)
ax.hexbin(x, y, gridsize=(160, 115), extent=EXT, mincnt=1, linewidths=0, zorder=3, cmap=ListedColormap(SEQ), norm=BoundaryNorm([1, 3, 10, 30, 100, 300, 1e5], 6))
lab = ["1 to 2", "3 to 9", "10 to 29", "30 to 99", "100 to 299", "300 or more"]
lg = ax.legend(handles=[Patch(facecolor=c, label=l) for c, l in zip(SEQ, lab)], loc="upper right", title="Inscriptions per hexagon (about 30 km)", fontsize=10.5,
               title_fontsize=11, frameon=True, ncol=2, bbox_to_anchor=(0.995, 0.995))
lg.get_frame().set_facecolor(PAPER); lg.get_frame().set_edgecolor(RULE)
for nm, lo, la, tlo, tla in (("Rome\n" + f"{R['n']['rome']:,}", 12.49, 41.89, 12.2, 39.5), ("Carthage", 10.32, 36.85, 5.6, 38.4)):
    px_, py_ = proj(lo, la); tx_, ty_ = proj(tlo, tla)
    ax.annotate(nm, (px_, py_), xytext=(tx_, ty_), fontsize=11, color=FG, ha="center", va="center",
                arrowprops=dict(arrowstyle="-", color=FG, lw=0.8, shrinkA=0), bbox=dict(boxstyle="round,pad=0.25", fc=PAPER, ec=RULE), zorder=7)
ax.text(0.01, 0.01, "Grey lines: provinces of about AD 117", transform=ax.transAxes, fontsize=10, color=MUT, va="bottom")

# time curve
a = fig.add_axes([0.66, 0.635, 0.31, 0.21]); a.set_facecolor(PAPER); style_axes(a)
a.axvspan(193, 235, color="#EFE3C4")
for g, c in (("Rome", GCOL["Rome"]), ("Italy", GCOL["Italy"]), ("Africa", GCOL["Africa"]), ("Danube and Balkans", GCOL["Danube and Balkans"])):
    v = np.convolve(G[g], np.ones(25) / 25, mode="same")
    a.plot(G.year, v / v.max(), color=c, lw=2.2, label=g if g != "Danube and Balkans" else "Danube, Balkans")
a.set_xlim(-50, 400); a.set_ylim(0, 1.12); a.set_yticks([0, 0.5, 1]); a.set_yticklabels(["0", "half", "peak"])
a.legend(frameon=False, fontsize=9.5, loc="lower left", ncol=4, bbox_to_anchor=(0.0, 0.98), handlelength=1.5, columnspacing=1.0)
a.set_xlabel("year AD (25-year mean; each region scaled to its own peak)", fontsize=9.5)
fig.text(0.66, 0.885, "Italy wrote first; the provinces peaked under the Severans", fontproperties=DISPB, fontsize=14, color=FG, va="bottom")
a.text(214, 0.04, "Severans", ha="center", fontsize=9, color=MUT)

# ages
b = fig.add_axes([0.66, 0.37, 0.31, 0.17]); b.set_facecolor(PAPER); style_axes(b)
b.bar(H.age, H.n, width=0.85, color=[HOT if v % 5 == 0 and v > 0 else "#9AA3AD" for v in H.age])
b.set_xlim(-1, 91); b.set_xlabel("age at death on the tombstone", fontsize=10); b.set_ylabel("ages", fontsize=10)
b.legend(handles=[Patch(color=HOT, label="multiple of 5"), Patch(color="#9AA3AD", label="other ages")], frameon=False, fontsize=9.5, loc="upper right")
fig.text(0.66, 0.555, f"The dead were rounded to fives ({R['ages']['n']:,} ages)", fontproperties=DISPB, fontsize=14, color=FG, va="bottom")

# soldiers
c_ = fig.add_axes([0.01, 0.07, 0.45, 0.30])
base_map(c_, ext=(-1900, 2300, -1300, 1500), provinces=False)
ox, oy = proj(S.o_lon.values, S.o_lat.values); dx_, dy_ = proj(S.lon.values, S.lat.values)
segs = []; cols = []
for i in range(len(S)):
    p0 = np.array([ox[i], oy[i]]); p2 = np.array([dx_[i], dy_[i]]); mid = (p0 + p2) / 2; v = p2 - p0; nrm = np.array([-v[1], v[0]]) * 0.18
    t = np.linspace(0, 1, 20)[:, None]; segs.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * (mid + nrm) + t ** 2 * p2)
    cols.append(COOL if S.not_after.iloc[i] <= 100 else (HOT if S.not_before.iloc[i] >= 101 else "#8C8C8C"))
c_.add_collection(LineCollection(segs, colors=cols, linewidths=0.6, alpha=0.45, zorder=5))
c_.scatter(ox, oy, s=10, facecolor="white", edgecolor=FG, lw=0.5, zorder=6)
lg = c_.legend(handles=[Line2D([0], [0], color=COOL, lw=2, label="stone before AD 101"), Line2D([0], [0], color=HOT, lw=2, label="AD 101 or later"),
                        Line2D([0], [0], color="#8C8C8C", lw=2, label="date spans AD 100"), Line2D([0], [0], marker="o", color="white", mec=FG, lw=0, label="stated home")],
               loc="lower left", fontsize=9.5, frameon=False, bbox_to_anchor=(1.0, 0.0))
lg.get_frame().set_facecolor(PAPER); lg.get_frame().set_edgecolor(RULE)
fig.text(0.02, 0.375, f"Soldiers far from home: {R['soldiers']['n_mapped']:,} stones name a home, median {R['soldiers']['median_km']:,.0f} km away", fontproperties=DISPB, fontsize=14, color=FG, va="bottom")

# numbers
y0 = 0.30
nums = [(f"{R['n']['rome_italy_pc']:.0f}%", "of the inscriptions\nare from Rome and Italy"),
        (f"AD {R['habit']['main']['peak_year']}", "empire-wide peak year:\nItaly sets the curve"),
        (f"{R['n']['prov_peaks_severan']} of {R['n']['prov_peaks']}", "big provinces peak\nin AD 175 to 250"),
        (f"{R['ages']['whipple']['all']['W']:.0f}", "Whipple index of ages\n(100 none, 500 all rounded)"),
        (f"{R['ages']['hopkins']['by_group']['Africa']['n_100plus']}", "ages of 100 or more\non African tombstones"),
        (f"{R['soldiers']['pc_over_500']:.0f}%", "of soldiers' homes are\nmore than 500 km away")]
for k, (big, small) in enumerate(nums):
    xx = 0.62 + (k % 2) * 0.19; yy = y0 - (k // 2) * 0.08
    fig.text(xx, yy, big, fontproperties=DISP, fontsize=26, color=HOT, va="top")
    fig.text(xx, yy - 0.037, small, fontsize=10.5, color=FG, va="top", linespacing=1.2)
fig.text(0.03, 0.012, "Data: LIRE v2.1 (Kaše, Heřmánková, Sobotková; from EDCS and EDH), CC BY 4.0. Provinces and places: Digital Atlas of the Roman Empire (Lund University).\n"
         "Counts through time share each inscription over its date range. Greek inscriptions not included; the record favours Rome, Italy and well-studied provinces.",
         fontsize=10, color=MUT, va="bottom")
fig.text(0.97, 0.042, "Dr Tristan Hotham  ·  maps.tristanhotham.com/roman-inscriptions", fontsize=11, color=FG, ha="right")
out = os.path.join(ROOT, "reddit", "roman_inscriptions_collage.png")
fig.savefig(out, dpi=170, facecolor=PAPER)
plt.close(fig)
from PIL import Image
im = Image.open(out); print(out, im.size)
assert im.size[0] >= 2400
