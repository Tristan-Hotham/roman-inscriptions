"""Step 9: header.png, the 1200 x 630 social card: title on paper, the density map on the right."""
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap, BoundaryNorm
from figstyle import *

R = jload(f"{DATA}/results.json")
I = pd.read_csv(f"{DATA}/inscriptions.csv.gz", usecols=["lon", "lat"])
x, y = proj(I.lon.values, I.lat.values)
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=PAPER)
ax = fig.add_axes([0.40, 0.0, 0.60, 1.0])
ext = (-2100, 2500, -1700, 1700)
base_map(ax, ext=ext, lw=0.3)
ax.hexbin(x, y, gridsize=(150, 110), extent=EXT, mincnt=1, linewidths=0, zorder=3, cmap=ListedColormap(SEQ), norm=BoundaryNorm([1, 3, 10, 30, 100, 300, 1e5], 6))
fig.text(0.035, 0.86, "DATA STUDY · 2026", fontsize=13, color=HOT, va="top")
fig.text(0.035, 0.78, "Where\nRomans\nwrote", fontproperties=DISP, fontsize=60, color=FG, va="top", linespacing=0.95)
fig.text(0.035, 0.30, f"{R['n']['all']:,} Latin inscriptions\nmapped through time", fontproperties=SERP, fontsize=19, color=FG, va="top", linespacing=1.2)
fig.text(0.035, 0.07, "Dr Tristan Hotham · maps.tristanhotham.com", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=PAPER)
from PIL import Image
im = Image.open(os.path.join(ROOT, "header.png")).convert("RGB"); im.save(os.path.join(ROOT, "header.png"), optimize=True)
print(im.size)
