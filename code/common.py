"""Shared paths, constants and helpers for the roman-inscriptions study ("Where Romans wrote: 200,000 Latin inscriptions mapped").

Inputs (read in place, never modified or copied into the repo):
  LIRE   /home/claude/newdata/raw_new14/inscriptions/LIRE_v2-1.parquet: LIRE v2.1, Latin Inscriptions of the Roman Empire
         (Kase, Hermankova and Sobotkova; Zenodo 10.5281/zenodo.7577788; CC BY 4.0), 203,466 inscriptions from EDCS and EDH.
  DARE   SCR/dare/provinces.geojson, provinces_label.geojson, places_{low,medium,high}.geojson: Digital Atlas of the Roman
         Empire (Johan Ahlfeldt, Lund University; CC BY 4.0), as packaged by klokantech/roman-empire on GitHub
         (git clone https://github.com/klokantech/roman-empire, data/). Province polygons of about AD 117 with the Augustan
         regions of Italy; ancient places with Latin names, used as the gazetteer for soldiers' origins.
  GEO    /home/claude/newdata/raw/geo/: Natural Earth land and countries (public domain), context for static figures.
Scratch goes to SCR and is deleted at the end.
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIRE = os.environ.get("RI_LIRE", "/home/claude/newdata/raw_new14/inscriptions/LIRE_v2-1.parquet")
SCR = os.environ.get("RI_SCRATCH", "/home/claude/scratch/roman-inscriptions")
DARE = os.environ.get("RI_DARE", os.path.join(SCR, "dare"))
GEO = os.environ.get("RI_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("RI_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "roman-inscriptions"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
LIRE_DOI = "10.5281/zenodo.7577788"

Y0, Y1 = -50, 400          # aoristic window (years; negative = BC); LIRE itself keeps 50 BC to AD 350 overlaps
BIN = 25                    # display bins

# region groups for the age models (EDCS province names)
AFRICA = {"Africa proconsularis", "Numidia", "Mauretania Caesariensis", "Mauretania Tingitana"}
HISP = {"Hispania citerior", "Baetica", "Lusitania"}
GAUL = {"Gallia Narbonensis", "Aquitani(c)a", "Lugudunensis", "Belgica", "Germania superior", "Germania inferior",
        "Belgica | Germania superior", "Belgica | Germania inferior", "Alpes Maritimae", "Alpes Cottiae", "Alpes Poeninae", "Alpes Graiae"}
DANUBE = {"Raetia", "Noricum", "Pannonia superior", "Pannonia inferior", "Pannonia inferior | Pannonia superior", "Dalmatia",
          "Moesia superior", "Moesia inferior", "Dacia", "Thracia", "Macedonia", "Achaia"}
EAST = {"Asia", "Galatia", "Syria", "Aegyptus", "Arabia", "Pontus et Bithynia", "Palaestina", "Cappadocia", "Creta et Cyrenaica",
        "Lycia et Pamphylia", "Cilicia", "Cyprus", "Mesopotamia", "Regnum Bospori", "Armenia"}
ISLANDS = {"Sicilia", "Sardinia", "Corsica"}
GROUPS = ["Rome", "Italy", "Africa", "Hispania", "Gaul and Germany", "Danube and Balkans", "Britain", "East", "Islands"]


def region_group(p):
    if p == "Roma": return "Rome"
    if isinstance(p, str) and ("Regio" in p or p == "Italia"): return "Italy"
    if p in AFRICA: return "Africa"
    if p in HISP: return "Hispania"
    if p in GAUL: return "Gaul and Germany"
    if p in DANUBE: return "Danube and Balkans"
    if p == "Britannia": return "Britain"
    if p in EAST: return "East"
    if p in ISLANDS: return "Islands"
    return "Other"


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    """dotted path into results; keys that contain dots are found by joining parts; list indices allowed"""
    v = R
    parts = path.split(".")
    i = 0
    while i < len(parts):
        if isinstance(v, list):
            v = v[int(parts[i])]; i += 1; continue
        for j in range(len(parts), i, -1):
            k = ".".join(parts[i:j])
            if k in v:
                v = v[k]; i = j; break
        else:
            raise KeyError(path)
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "yr": return f"AD {int(v)}" if v > 0 else f"{-int(v)} BC"
    raise ValueError(f)


def gc_km(lat1, lon1, lat2, lon2):
    import numpy as np
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))


TENS = {"": 0, "X": 10, "XX": 20, "XXX": 30, "XXXX": 40, "XL": 40, "L": 50, "LX": 60, "LXX": 70, "LXXX": 80, "LXXXX": 90, "XC": 90,
        "XXC": 80}
UNITS = {"": 0, "I": 1, "II": 2, "III": 3, "IIII": 4, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "VIIII": 9, "IX": 9, "IIX": 8}
_RN = re.compile(r"^(C?)(XXC|XC|XL|L?X{0,4})(IIX|IX|IV|V?I{0,4})$")


def roman(s):
    """Roman numeral as written on stone (additive IIII, VIIII, XXXX; subtractive IV, IX, XL, XC; the forms IIX = 8 and XXC = 80)
    to int, or None if the token is not such a numeral (up to 199)"""
    m = _RN.match(s.upper())
    if not m or not s:
        return None
    return (100 if m.group(1) else 0) + TENS[m.group(2)] + UNITS[m.group(3)]
