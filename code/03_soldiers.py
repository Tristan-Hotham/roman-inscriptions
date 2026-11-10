"""Step 3: soldiers on the move. Soldier stones, their stated origin (origo) and where they stand.
Soldier stone: EDCS status "milites" or a military word in the text (NOTES.md); military diplomas are kept apart.
Origo forms read from the `inscription` text (expansions resolved, restorations dropped):
  domo X [Y]      "from the home X" (a tribe name before a city is skipped)
  natione X       ethnic adjective, mapped by hand to a region point (code/natio.csv)
  civis/cives X   when X is an ethnic or a place
  filius <tribe> ... X   a voting tribe after the filiation, then within three tokens a token that is a case form of a DARE place
Gazetteer: DARE Latin place names (all places with a Latin name); each name expanded into its usual case forms (Mediolanum ->
Mediolano, Aquileia -> Aquileiae, Carnuntum -> Carnunto, Ateste, Narbo -> Narbone ...). A form that points at several DARE
places more than 50 km apart is ambiguous: it is used only through code/origo_overrides.csv, which also fixes or rejects every
origin used at least twice (checked by eye). Writes data/soldiers.csv (one row per soldier stone with an origin, no text) and
SCR/origo_check.csv (the list read by eye, with text snippets; scratch only)."""
import unicodedata
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from common import *

I = pd.read_csv(f"{DATA}/inscriptions.csv.gz", low_memory=False)
T = pq.read_table(LIRE, columns=["LIST-ID", "inscription", "status"]).to_pandas().rename(columns={"LIST-ID": "lire_id"})
D = I.merge(T, on="lire_id", how="left")


def clean(s):
    s = re.sub(r"<([^=>]*)=[^>]*>", r"\1", s)
    s = re.sub(r"\{[^}]*\}", "", s)
    s = s.replace("(!)", "").replace("/", "")
    return re.sub(r"\(([^()?]*)\)", r"\1", s)


def norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return s.replace("y", "i").replace("ph", "f").replace("k", "c").replace("j", "i").replace("u", "v").replace("v", "u")


MIL = re.compile(r"\b(miles|militis|militi|milites|legionis|legio|legioni|cohortis|cohors|cohorte|alae|ala|eques|equiti|equitis|"
                 r"veteranus|veterano|veterani|centurio|centurioni|centurionis|signifer|signifero|beneficiarius|beneficiario|optio|optioni|"
                 r"praetoriae|praetorianus|classis|stipendiorum|militavit|militans|evocatus|tesserarius|decurio alae)\b", re.I)
D["txt"] = D.inscription.fillna("").map(clean)
st = D.status.fillna("")
D["diploma"] = st.str.contains("diplomata militaria") | (D.type_auto == "military diploma")
D["soldier"] = (st.str.contains("milites") | D.txt.map(lambda x: bool(MIL.search(x)))) & ~D.diploma
TRIBES = {norm(t) for t in ["Aemilia", "Aniensis", "Arnensis", "Camilia", "Claudia", "Clustumina", "Collina", "Cornelia", "Esquilina", "Fabia",
                            "Falerna", "Galeria", "Horatia", "Lemonia", "Maecia", "Menenia", "Oufentina", "Ufentina", "Palatina", "Papiria",
                            "Pollia", "Pomptina", "Pupinia", "Publilia", "Quirina", "Romilia", "Sabatina", "Scaptia", "Sergia", "Stellatina",
                            "Suburana", "Teretina", "Tromentina", "Velina", "Voltinia", "Voturia", "Ulpia", "Flavia", "Aelia", "Aurelia"]}
TRIBE_STRICT = TRIBES - {norm(t) for t in ["Ulpia", "Flavia", "Aelia", "Aurelia", "Claudia", "Cornelia"]}

# ---- gazetteer ----
G = []
for fn in ("places_low", "places_medium", "places_high"):
    for f in jload(f"{DARE}/{fn}.geojson")["features"]:
        p = f["properties"]; nm = (p.get("latin") or "").strip()
        nm = re.sub(r"[\*\?\[\]\(\)]", "", nm).strip()
        if not nm:
            continue
        lon, lat = f["geometry"]["coordinates"][:2]
        G.append((p["id"], nm, lon, lat, fn == "places_low", int(p.get("major") or 0), str(p.get("type"))))
G = pd.DataFrame(G, columns=["dare_id", "latin", "lon", "lat", "low", "major", "dtype"]).drop_duplicates("dare_id")
GALL = G.copy()                                   # every named DARE place (for override targets)
# automatic matching only against settlements west of 46 E (the empire and its neighbours) (DARE types 11 to 13), never mountains, harbours, rivers or roadside places
G = G[(G.lon < 46) & G.dtype.isin(["11", "12", "13"]) & ~G.latin.str.contains(r"\b(Mons|Portus|Vicus|Fluvi|Insula|Promunturium|Lacus|Silva|Statio|Mutatio|Mansio)\b")]


def forms(name):
    """case forms of a Latin place name (first word only for compound names, plus the full name)"""
    out = set()
    for w in {name.split()[0], name}:
        n = norm(w)
        out.add(n)
        for a, bs in (("um", ["o", "i"]), ("us", ["o", "i"]), ("a", ["ae", "a"]), ("ae", ["is", "arum"]), ("i", ["is", "orum"]),
                      ("is", ["i", "e"]), ("o", ["one", "oni"]), ("on", ["one"]), ("e", ["e", "i"]), ("es", ["ibus"])):
            if n.endswith(a) and len(n) > len(a) + 2:
                for b in bs:
                    out.add(n[: -len(a)] + b)
    return out


FORM = {}
G = G.reset_index(drop=True)
for r in G.itertuples():
    for fo in forms(r.latin):
        FORM.setdefault(fo, []).append(r.Index)


# personal names in EDH (name parts used at least 20 times) are never read as places unless the place is a major town (places_low)
_NC = {}
for ptxt in pq.read_table(LIRE, columns=["people"]).column(0).to_pylist():
    for nm_ in re.findall(r"'#text': '([^']+)'", ptxt or ""):
        for w in nm_.split():
            w = norm(re.sub(r"[^A-Za-z]", "", w))
            if w:
                _NC[w] = _NC.get(w, 0) + 1
NAMES = {w for w, c in _NC.items() if c >= 20}


def lookup(tok):
    """unique DARE place for a token, 'ambiguous', or None"""
    c = FORM.get(norm(re.sub(r"[^A-Za-z]", "", tok)))
    if not c or len(re.sub(r"[^A-Za-z]", "", tok)) < 4 or not tok[:1].isupper():
        return None
    g = G.loc[c]
    if norm(re.sub(r"[^A-Za-z]", "", tok)) in NAMES:
        g = g[g.low]
        if not len(g):
            return None
    if len(g) == 1:
        return g.index[0]
    spread = gc_km(g.lat.values[:, None], g.lon.values[:, None], g.lat.values[None, :], g.lon.values[None, :]).max()
    if spread < 50:
        return g.sort_values(["low", "major"], ascending=False).index[0]
    return "ambiguous"


NAT = pd.read_csv(os.path.join(ROOT, "code", "natio.csv"))
PL = {f["properties"]["name"]: f["geometry"]["coordinates"] for f in jload(f"{DARE}/provinces_label.geojson")["features"]}
def _res(r):
    if r.kind == "province":
        return PL[r.target]
    g = GALL[GALL.dare_id == str(r.target)]          # kind = place: target is a DARE place id
    assert len(g), r.target
    return [g.lon.iloc[0], g.lat.iloc[0]]
NAT[["lon", "lat"]] = [_res(r) for r in NAT.itertuples()]
NATD = {norm(r.form): r for r in NAT.itertuples()}
OVR = pd.read_csv(os.path.join(ROOT, "code", "origo_overrides.csv"))
OVRD = {norm(r.token): r for r in OVR.itertuples()}

rows = []
S = D[D.soldier | D.diploma]
for r in S.itertuples():
    toks = r.txt.split()
    found = None
    for k, t in enumerate(toks):
        tl = t.lower()
        cand = []
        if tl in ("domo", "domu", "domus"):
            nx = [x for x in toks[k + 1:k + 3]]
            if nx and norm(re.sub(r"[^A-Za-z]", "", nx[0])) in TRIBES and len(nx) > 1:
                nx = nx[1:]
            cand = [("domo", x) for x in nx[:1]]
        elif tl in ("natione", "natio", "nationis"):
            cand = [("natione", x) for x in toks[k + 1:k + 2]]
        elif tl in ("civis", "cives", "civi", "civem"):
            cand = [("civis", x) for x in toks[k + 1:k + 2]]
        elif norm(re.sub(r"[^A-Za-z]", "", t)) in TRIBE_STRICT and any(x.lower() in ("filius", "filio", "fil", "f", "filii", "filium") for x in toks[max(0, k - 2):k]):
            cand = [("tribe", x) for x in toks[k + 1:k + 4]]
        for how, x in cand:
            if "[" in x or "]" in x or "?" in x:
                continue
            xn = norm(re.sub(r"[^A-Za-z]", "", x))
            if not xn:
                continue
            if xn in OVRD:
                o = OVRD[xn]
                if o.action == "reject":
                    continue
                if o.kind == "province":
                    lo, la = PL[o.target]; found = (how, x, o.target, lo, la, "region", "override"); break
                g = GALL[GALL.dare_id == str(int(o.target))].iloc[0]
                found = (how, x, g.latin, g.lon, g.lat, "place", "override DARE " + str(g.dare_id)); break
            if how in ("natione", "civis") and xn in NATD:
                n_ = NATD[xn]; found = (how, x, n_.region, n_.lon, n_.lat, "region", "natio table"); break
            if how in ("domo", "civis", "tribe", "natione"):
                j = lookup(x)
                if j is None:
                    continue
                if j == "ambiguous":
                    found = (how, x, None, np.nan, np.nan, "ambiguous", "ambiguous"); break
                g = G.loc[j]; found = (how, x, g.latin, g.lon, g.lat, "place", "DARE " + str(g.dare_id)); break
        if found:
            break
    if found:
        rows.append((r.lire_id,) + found)
O = pd.DataFrame(rows, columns=["lire_id", "how", "token", "origin", "o_lon", "o_lat", "precision", "match"])
O = O.merge(I[["lire_id", "lon", "lat", "province", "group", "place", "not_before", "not_after"]], on="lire_id", how="left")
O = O.merge(D[["lire_id", "diploma"]], on="lire_id")
O["dist_km"] = gc_km(O.o_lat, O.o_lon, O.lat, O.lon).round(1)
# eye check list: every token used at least twice, and every singleton, with snippets (scratch only)
tc = O.token.map(lambda x: norm(re.sub(r"[^A-Za-z]", "", x))).value_counts()
O["token_n"] = O.token.map(lambda x: tc[norm(re.sub(r"[^A-Za-z]", "", x))])
snip = D.set_index("lire_id").txt
chk = O.assign(snippet=O.apply(lambda r: (lambda s, t: s[max(0, s.find(t) - 70): s.find(t) + 30])(snip[r.lire_id], r.token), axis=1))
chk.sort_values(["token_n", "token"], ascending=[False, True]).to_csv(f"{SCR}/origo_check.csv", index=False)
keep = O[(O.precision != "ambiguous") & (O.o_lat.notna())]
keep = keep[(keep.token_n >= 2) | (keep.match != "ambiguous")]
keep.drop(columns=["token_n"]).to_csv(f"{DATA}/soldiers.csv", index=False)
jsave({"n_soldier_stones": int(D.soldier.sum()), "n_diplomas": int(D.diploma.sum()), "n_with_origin_candidates": int(len(O)),
       "n_ambiguous": int((O.precision == "ambiguous").sum()), "n_mapped": int(len(keep)), "n_mapped_stones": int(keep[~keep.diploma].shape[0]),
       "n_mapped_diplomas": int(keep[keep.diploma].shape[0]), "by_how": keep.how.value_counts().to_dict(), "by_precision": keep.precision.value_counts().to_dict()},
      f"{SCR}/soldiers_n.json", indent=1)
print(D.soldier.sum(), "soldier stones;", D.diploma.sum(), "diplomas;", len(O), "with an origin candidate;", len(keep), "mapped;",
      keep.how.value_counts().to_dict(), keep.precision.value_counts().to_dict())
