"""House style for the static figures: light paper, Fraunces titles, Source Serif and IBM Plex Mono text."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
from common import *

_FD = os.path.join(SCR, "fonts")
os.makedirs(_FD, exist_ok=True)
if not os.path.exists(f"{_FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{_FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{_FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{_FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 11, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72", "axes.unicode_minus": False, "pdf.fonttype": 42})
PAPER, FG, MUT, RULE = "#F6F4EF", "#1D2128", "#636A72", "#DDD8CC"
SEA, LAND, EDGE = "#E4ECF0", "#ECE8DF", "#CFC8B8"
HOT, COOL = "#B3202A", "#2F7FB8"
CAT = ["#B3202A", "#2F7FB8", "#D08A1E", "#3B8B5A", "#7A4FA0", "#C2577F"]
GCOL = {"Rome": "#B3202A", "Italy": "#D08A1E", "Africa": "#3B8B5A", "Hispania": "#C2577F", "Gaul and Germany": "#2F7FB8",
        "Danube and Balkans": "#7A4FA0", "Britain": "#2E9C9C", "East": "#8A6A3B", "Islands": "#55606B"}
SEQ = ["#FBE9D6", "#F4C9A0", "#E89A63", "#D06A38", "#A9411F", "#6E2412"]


def style_axes(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=RULE, lw=0.6)
    ax.set_axisbelow(True)


def savefig(fig, stem, blog=None, img=None, pdf=True):
    """f_<stem>.pdf for the paper, release/blog/b_<blog>.png at 1800 px wide, img/<img>.jpg for the page"""
    os.makedirs(f"{REL}/paper", exist_ok=True); os.makedirs(f"{REL}/blog", exist_ok=True)
    if pdf:
        fig.savefig(f"{REL}/paper/f_{stem}.pdf", facecolor=fig.get_facecolor())
    w = fig.get_figwidth()
    if blog:
        fig.savefig(f"{REL}/blog/b_{blog}.png", dpi=1800 / w, facecolor=fig.get_facecolor())
    if img:
        tmp = f"{SCR}/_tmp.png"
        fig.savefig(tmp, dpi=1400 / w, facecolor=fig.get_facecolor())
        from PIL import Image
        Image.open(tmp).convert("RGB").save(f"{IMG}/{img}.jpg", quality=86, optimize=True)
        os.remove(tmp)
    plt.close(fig)


# ---- map helpers: Lambert azimuthal equal-area centred on the Mediterranean ----
from pyproj import Transformer
_TR = Transformer.from_crs(4326, "+proj=laea +lat_0=42 +lon_0=14 +units=km", always_xy=True)
EXT = (-2500, 2650, -1850, 1950)          # km: Britain and Iberia to Syria, the Rhine to the Sahara edge


def proj(lon, lat):
    return _TR.transform(np.asarray(lon, float), np.asarray(lat, float))


def _rings(geom):
    from shapely.geometry import shape
    g = shape(geom)
    for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
        yield np.asarray(p.exterior.coords)


_LAND = None


def land_patches():
    global _LAND
    if _LAND is None:
        from matplotlib.patches import Polygon as MPoly
        _LAND = []
        for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]:
            for r in _rings(f["geometry"]):
                if r[:, 0].max() < -20 or r[:, 0].min() > 60 or r[:, 1].max() < 15 or r[:, 1].min() > 65:
                    continue
                x, y = proj(r[:, 0], r[:, 1])
                _LAND.append(np.c_[x, y])
    return _LAND


def base_map(ax, ext=EXT, provinces=True, lw=0.5):
    from matplotlib.patches import Polygon as MPoly
    from matplotlib.collections import PatchCollection, LineCollection
    ax.set_facecolor(SEA)
    ax.add_collection(PatchCollection([MPoly(r, closed=True) for r in land_patches()], facecolor=LAND, edgecolor=EDGE, lw=0.4, zorder=1))
    if provinces:
        segs = []
        for f in jload(f"{DATA}/provinces.geojson")["features"]:
            for r in _rings(f["geometry"]):
                x, y = proj(r[:, 0], r[:, 1]); segs.append(np.c_[x, y])
        ax.add_collection(LineCollection(segs, colors="#9B907C", linewidths=lw, zorder=4, alpha=0.8))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
