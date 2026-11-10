"""Step 6: data for the interactive page.
  data/hex.json       hexagons (flat-topped, Web Mercator, radius 25 km in Mercator metres, about 35 km across at 45 N): centre, total
                      by type, and the aoristic expected count in each 25-year bin by type (sparse), top findspots and three example
                      inscriptions (EDCS/EDH ids) per hexagon
  data/flows.json     soldiers' stated origin to findspot (no names of people), with period and distance
  data/places.json    search list: findspots (modern place and ancient name) with counts and a point
  data/site.json      bins, type labels, totals per bin for the page header"""
import numpy as np
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
I = pd.read_csv(f"{DATA}/inscriptions.csv.gz", low_memory=False)
RAD = 25000.0
BINS = list(range(-50, 400, 25))          # bin starts: -50 .. 375
NB = len(BINS)
TYPES = ["epitaph", "votive", "honorific", "building", "milestone", "other"]
I["t"] = I.type.where(I.type.isin(TYPES), "other").map({t: k for k, t in enumerate(TYPES)})

# web mercator and hex index (flat-topped axial coordinates)
lon = np.radians(I.lon.values); lat = np.radians(I.lat.values)
X = 6378137.0 * lon; Y = 6378137.0 * np.log(np.tan(np.pi / 4 + lat / 2))
q = (2 / 3 * X) / RAD; r = (-1 / 3 * X + np.sqrt(3) / 3 * Y) / RAD
# cube rounding
x_, z_ = q, r; y_ = -x_ - z_
rx, ry, rz = np.round(x_), np.round(y_), np.round(z_)
dx, dy, dz = np.abs(rx - x_), np.abs(ry - y_), np.abs(rz - z_)
m1 = (dx > dy) & (dx > dz); m2 = ~m1 & (dy > dz)
rx = np.where(m1, -ry - rz, rx); rz = np.where(~m1 & ~m2, -rx - ry, rz)
I["hq"] = rx.astype(int); I["hr"] = rz.astype(int)
I["hid"] = I.hq.astype(str) + "_" + I.hr.astype(str)

# aoristic weight of each inscription in each 25-year bin
nb = I.not_before.fillna(-9999).values; na = I.not_after.fillna(-9999).values
dated = I.not_before.notna().values & I.not_after.notna().values
W = np.zeros((len(I), NB), np.float32)
span = np.where(dated, na - nb + 1, 1)
for k, b0 in enumerate(BINS):
    lo = np.maximum(nb, b0); hi = np.minimum(na, b0 + 24)
    W[:, k] = np.where(dated & (hi >= lo), (hi - lo + 1) / span, 0)

hexes = []
g = I.groupby("hid", sort=False)
for hid, s in g:
    idx = s.index.values
    qq, rr = int(s.hq.iloc[0]), int(s.hr.iloc[0])
    cx = RAD * 1.5 * qq; cy = RAD * np.sqrt(3) * (rr + qq / 2)
    clon = np.degrees(cx / 6378137.0); clat = np.degrees(2 * np.arctan(np.exp(cy / 6378137.0)) - np.pi / 2)
    tot = np.bincount(s.t.values, minlength=6).tolist()
    sp = []
    for t in range(6):
        sel = idx[s.t.values == t]
        if not len(sel):
            continue
        wb = W[sel].sum(0)
        for k in np.nonzero(wb >= 0.05)[0]:
            sp.append([int(k), t, round(float(wb[k]), 1)])
    pl = s.place.fillna("").replace("", np.nan).dropna().value_counts().head(3)
    an = s.ancient_place.dropna().value_counts().head(2)
    ex = s.sample(min(3, len(s)), random_state=1)
    exs = [[e.edcs_id if isinstance(e.edcs_id, str) else "", e.edh_id if isinstance(e.edh_id, str) else ""] for e in ex.itertuples()]
    prov = s.province.value_counts().index[0] if s.province.notna().any() else ""
    hexes.append([qq, rr, round(clon, 3), round(clat, 3), tot, sp, [[k, int(v)] for k, v in pl.items()], list(an.index), exs, prov])
jsave({"rad": RAD, "bins": BINS, "types": TYPES, "fields": ["q", "r", "lon", "lat", "total_by_type", "bins_sparse[bin,type,w]", "top_places", "ancient", "examples[edcs,edh]", "province"],
       "hex": hexes}, f"{DATA}/hex.json")

# flows
S = pd.read_csv(f"{DATA}/soldiers.csv")
S = S[~S.diploma].copy()
S["per"] = np.where(S.not_after <= 100, "early", np.where(S.not_before >= 101, "late", "span"))
S["dk"] = S.lon.round(2).astype(str) + "," + S.lat.round(2).astype(str)
F = S.groupby(["origin", "o_lon", "o_lat", "precision", "dk", "lon", "lat", "per"]).agg(n=("lire_id", "size"), km=("dist_km", "first"),
                                                                                         place=("place", "first"), prov=("province", "first")).reset_index()
flows = [[r.origin, round(r.o_lon, 3), round(r.o_lat, 3), r.precision[0], round(r.lon, 3), round(r.lat, 3), r.per, int(r.n), round(r.km), r.place if isinstance(r.place, str) else "", r.prov if isinstance(r.prov, str) else ""]
         for r in F.itertuples()]
jsave({"fields": ["origin", "o_lon", "o_lat", "precision(p/r)", "lon", "lat", "period", "n", "km", "findspot", "province"], "flows": flows}, f"{DATA}/flows.json")

# search list: findspots
P = I.groupby("place").agg(n=("lire_id", "size"), lon=("lon", "median"), lat=("lat", "median"), anc=("ancient_place", lambda x: x.dropna().iloc[0] if x.notna().any() else ""),
                            prov=("province", lambda x: x.mode().iloc[0] if x.notna().any() else "")).reset_index().sort_values("n", ascending=False)
P = P[P.n >= 2]
places = [[r.place, r.anc, round(r.lon, 4), round(r.lat, 4), int(r.n), r.prov] for r in P.itertuples()]
jsave({"fields": ["findspot", "ancient", "lon", "lat", "n", "province"], "places": places}, f"{DATA}/places.json")

tb = W.sum(0)
site = {"bins": BINS, "types": TYPES, "per_bin": [round(float(v)) for v in tb], "n": R["n"]["all"], "rad": RAD}
jsave(site, f"{DATA}/site.json")
print(len(hexes), "hexes;", {f: os.path.getsize(f"{DATA}/{f}") // 1024 for f in ("hex.json", "flows.json", "places.json")}, "KB")
