"""Step 1: the slim per-inscription table (no texts) and the province areas.
Reads LIRE (non-text columns) and the DARE province polygons; writes
  data/inscriptions.csv.gz   one row per LIRE inscription: ids, point, EDCS province, DARE province (point in polygon),
                             region group, LIRE auto type, Christian flag (EDCS status), dates, urban context, findspot name
  data/provinces.geojson     DARE provinces (simplified) with area and counts, for the page
  SCR/meta.parquet           working copy of the needed columns (scratch)"""
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from shapely.geometry import shape, Point, mapping
from shapely import STRtree
from pyproj import Geod
from common import *

cols = ["LIST-ID", "EDCS-ID", "EDH-ID", "trismegistos_uri", "province", "place", "type_of_inscription_auto", "type_of_inscription_clean",
        "status", "not_before", "not_after", "Longitude", "Latitude", "urban_context", "urban_context_city", "findspot_ancient_clean"]
d = pq.read_table(LIRE, columns=cols).to_pandas()
n_raw = len(d)
d = d.rename(columns={"LIST-ID": "lire_id", "EDCS-ID": "edcs_id", "EDH-ID": "edh_id", "Longitude": "lon", "Latitude": "lat"})
d["tm_id"] = d.trismegistos_uri.str.extract(r"(\d+)\s*$")[0]
sw = d.not_before > d.not_after
d.loc[sw, ["not_before", "not_after"]] = d.loc[sw, ["not_after", "not_before"]].values
d["date_swapped"] = sw
st = d.status.fillna("")
d["christian"] = st.str.contains("inscriptiones christianae")
d["epitaph"] = (d.type_of_inscription_auto == "epitaph") | st.str.contains("tituli sepulcrales")
d["group"] = d.province.map(region_group)
TYPES = {"epitaph": "epitaph", "votive inscription": "votive", "honorific inscription": "honorific", "building/dedicatory inscription": "building",
         "mile-/leaguestone": "milestone"}
d["type"] = d.type_of_inscription_auto.map(TYPES).fillna("other")
d.loc[d.type_of_inscription_auto.isna(), "type"] = "unknown"

# DARE province by point in polygon (nearest polygon within 25 km for coastal points)
P = jload(f"{DARE}/provinces.geojson")["features"]
geoms = [shape(f["geometry"]).buffer(0) for f in P]
names = [f["properties"]["name"] for f in P]
tree = STRtree(geoms)
pts = [Point(x, y) for x, y in zip(d.lon, d.lat)]
hit = tree.query(pts, predicate="intersects")
dp = np.full(len(d), None, object)
dp[hit[0]] = np.array(names, object)[hit[1]]
miss = np.where(pd.isna(dp))[0]
for i in miss:
    j = tree.nearest(pts[i])
    if geoms[j].distance(pts[i]) < 0.25:
        dp[i] = names[j]
ITALY = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"}
d["dare_province"] = [("Italia, regio " + x) if x in ITALY else x for x in dp]
d.loc[d.dare_province.isna(), "dare_province"] = "outside DARE provinces"
d.loc[d.province == "Roma", "dare_province"] = "Roma (city)"     # the city is counted apart from the Italian region polygons

geod = Geod(ellps="WGS84")
area = {}
feats = []
for g, nm in zip(geoms, names):
    a = abs(geod.geometry_area_perimeter(g)[0]) / 1e6
    key = ("Italia, regio " + nm) if nm in ITALY else nm
    area[key] = area.get(key, 0) + a
cnt = d.dare_province.value_counts()
for g, nm in zip(geoms, names):
    key = ("Italia, regio " + nm) if nm in ITALY else nm
    s = g.simplify(0.03, preserve_topology=True)
    n = int(cnt.get(key, 0))
    n_norome = n
    feats.append({"type": "Feature", "properties": {"name": key, "area_km2": round(area[key]), "n": n, "n_excl_rome": int(n_norome),
                  "per1000": round(n_norome / area[key] * 1000, 2)}, "geometry": mapping(s)})
gj = {"type": "FeatureCollection", "features": feats}
s = json.dumps(gj, separators=(",", ":"))
s = re.sub(r"(-?\d+\.\d{3})\d+", r"\1", s)
open(f"{DATA}/provinces.geojson", "w").write(s)

out = d[["lire_id", "edcs_id", "edh_id", "tm_id", "lon", "lat", "province", "dare_province", "group", "place", "findspot_ancient_clean",
         "urban_context", "type", "type_of_inscription_auto", "christian", "epitaph", "not_before", "not_after", "date_swapped"]].copy()
out = out.rename(columns={"findspot_ancient_clean": "ancient_place", "type_of_inscription_auto": "type_auto"})
out["lon"] = out.lon.round(5); out["lat"] = out.lat.round(5)
out.to_csv(f"{DATA}/inscriptions.csv.gz", index=False, compression="gzip")
jsave({"area_km2": area, "n_raw": n_raw, "n_swapped": int(sw.sum()), "n_outside_dare": int((d.dare_province == "outside DARE provinces").sum()),
       "n_nearest": int(len(miss) - (d.dare_province == "outside DARE provinces").sum())}, f"{SCR}/prep.json", indent=1)
print(n_raw, "rows; swapped", int(sw.sum()), "; outside DARE", int((d.dare_province == "outside DARE provinces").sum()), "of", len(miss), "missed",
      "; size", os.path.getsize(f"{DATA}/inscriptions.csv.gz") // 1024, "KB; provinces", os.path.getsize(f"{DATA}/provinces.geojson") // 1024, "KB")
print(d.dare_province.value_counts().head(12))
