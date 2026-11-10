"""Step 2: ages at death stated on epitaphs, read from the LIRE `inscription` text (EDCS/EDH edition with Leiden-style marks).
Rule (NOTES.md, fixed before any age was looked at): an age is an "ann-" token (an, ann, annis, annos, annorum, annoru, anno, annu,
annum, annus) followed at once by an intact Roman numeral, with either a form of "vixit" in the two tokens before (form A) or the
genitive "annorum" (form B, "aged N"). "anno" only in form A. Not ages: years of service (milit-, stip-, aer-, meruit, emerit-,
sacerdo- in the three tokens before) and years of marriage ("cum qua vixit annis", "vixit mecum": cum/mecum/secum/tecum/cum quo in
the window), a correction found while reading the planned validation sample (logged in NOTES.md). Numerals with a restored
letter ([ ]), a query (?) or an editorial mark are dropped. Ages 0 to 110. Epitaphs only.
Writes data/ages.csv.gz (one row per stated age, no text) and SCR/age_samples.csv (validation samples, with text, not shipped)."""
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from common import *

I = pd.read_csv(f"{DATA}/inscriptions.csv.gz", low_memory=False)
T = pq.read_table(LIRE, columns=["LIST-ID", "inscription"]).to_pandas().rename(columns={"LIST-ID": "lire_id"})
I = I.merge(T, on="lire_id", how="left")
E = I[I.epitaph & I.inscription.notna()].copy()

ANN = re.compile(r"^(an|ann|anni|annis|annos|annorum|annoru|annor|anno|annu|annum|annus|annoro|annoris)$", re.I)
GEN = re.compile(r"^(annorum|annoru|annor|annoro)$", re.I)
VIX = re.compile(r"^([vb]i[xc]+s?[ie]?t?|[vb]i[xc]+s?i|vix|vixsit|bixsit|vixet|bixit|vicxit|visit|vixerit|vixerunt)$", re.I)
SERV = re.compile(r"^(milit|stip|aer|meru|emerit|sacerdo|mil$)", re.I)
MARR = re.compile(r"^(cum|mecum|secum|tecum|quocum|quacum)$", re.I)
NUM = re.compile(r"^[IVXLC]+$")


def clean(s):
    s = re.sub(r"<([^=>]*)=[^>]*>", r"\1", s)       # <v=B> corrections: keep the reading
    s = re.sub(r"\{[^}]*\}", "", s)                  # {s} superfluous letters
    s = s.replace("(!)", "")
    s = s.replace("/", "")                           # line breaks join split words and numerals
    s = re.sub(r"\(([^()?]*)\)", r"\1", s)           # expansions ann(is) -> annis
    return s


PM = re.compile(r"^(plus|minus|pl|min|p|m|plu|minu|plusminus)$", re.I)
rows = []
for lid, txt in zip(E.lire_id.values, E.inscription.values):
    toks = clean(txt).split()
    for k in range(len(toks) - 1):
        a = re.sub(r"[\[\]]", "", toks[k])          # a restored letter in the word itself is accepted; never in the numeral
        if not ANN.match(a):
            continue
        j = k + 1
        while j < len(toks) and j <= k + 2 and PM.match(toks[j]) and not NUM.match(toks[j]):
            j += 1                                    # "annos plus minus LX": the age follows the plus minus
        if j >= len(toks):
            continue
        nt = toks[j]
        pm = j > k + 1
        if not NUM.match(nt):
            continue
        prev = [re.sub(r"[^A-Za-z]", "", t) for t in toks[max(0, k - 3):k]]
        pm = pm or any(PM.match(t) and t.lower().startswith("pl") for t in prev[-2:])
        form = None
        if any(VIX.match(t) for t in prev[-2:]):
            form = "A"
        elif GEN.match(a):
            form = "B"
        if form is None or (a.lower() == "anno" and form != "A"):
            continue
        if any(SERV.match(t) for t in prev):
            continue
        window = [re.sub(r"[^A-Za-z]", "", t) for t in toks[max(0, k - 4):k]]
        if any(MARR.match(t) for t in window):
            continue
        v = roman(nt)
        if v is None or v > 110:
            continue
        rows.append((lid, v, form, k, pm))
A = pd.DataFrame(rows, columns=["lire_id", "age", "form", "pos", "plus_minus"])
A["first"] = ~A.duplicated("lire_id")
A = A.merge(I[["lire_id", "province", "group", "urban_context", "christian", "not_before", "not_after", "place", "lon", "lat"]], on="lire_id", how="left")
A.drop(columns=["pos"]).to_csv(f"{DATA}/ages.csv.gz", index=False, compression="gzip")

# validation samples (texts kept in scratch only)
rng = np.random.default_rng(2026)
s1 = A.sample(200, random_state=2026)[["lire_id", "age", "form"]].merge(I[["lire_id", "inscription"]], on="lire_id")
noage = E[~E.lire_id.isin(A.lire_id)].sample(100, random_state=2026)[["lire_id", "inscription"]]
s1.assign(sample="extracted").to_csv(f"{SCR}/age_sample_extracted.csv", index=False)
noage.assign(sample="no_age").to_csv(f"{SCR}/age_sample_noage.csv", index=False)
jsave({"n_epitaphs": int(len(E)), "n_ages": int(len(A)), "n_stones": int(A.lire_id.nunique()), "form": A.form.value_counts().to_dict()},
      f"{SCR}/ages_n.json", indent=1)
print(len(E), "epitaphs with text;", len(A), "ages on", A.lire_id.nunique(), "stones;", A.form.value_counts().to_dict())
