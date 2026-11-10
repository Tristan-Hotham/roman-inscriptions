"""Step 4b: a few derived numbers quoted in the text, added to data/results.json (so every quoted number is in it)."""
from common import *

R = jload(f"{DATA}/results.json")
d = R["ages"]["digits_23_62"]
R["ages"]["digit_expected"] = sum(d.values()) / 10
R["ages"]["digit_0_ratio"] = d["0"] / R["ages"]["digit_expected"]
R["ages"]["digit_5_ratio"] = d["5"] / R["ages"]["digit_expected"]
R["ages"]["validation"]["n_right"] = R["ages"]["validation"]["n_read"] - R["ages"]["validation"]["n_wrong"]
R["habit"]["max_share_pc"] = 100 / min(x["ratio"] for x in R["habit"]["sens"])
R["habit"]["fall_pc"] = 100 * (1 - 1 / R["habit"]["main"]["ratio"])
rob = {r["label"]: r for r in R["ages"]["robust"]}
R["ages"]["robust_vixit_rural"] = rob["Vixit form only"]["rural"]
R["soldiers"]["city_only"] = R["soldiers"]["robust"][1]
assert R["soldiers"]["city_only"]["label"] == "City origins only"
import pandas as pd
A = pd.read_csv(f"{DATA}/ages.csv.gz", low_memory=False)
X = A[(A.age >= 23) & (A.age <= 62)]
R["ages"]["mix"] = {g: {"rural_pc": 100 * float((X[X.group == g].urban_context == "rural").mean()), "large_pc": 100 * float((X[X.group == g].urban_context == "large").mean()),
                        "mean_age": float(X[X.group == g].age.mean())} for g in ("Rome", "Africa")}
S = pd.read_csv(f"{DATA}/soldiers.csv"); S = S[~S.diploma]
e = S[S.not_after <= 100]; l = S[(S.not_before >= 101) & (S.not_after <= 300)]
R["soldiers"]["mix"] = {"early_region_pc": 100 * float((e.precision == "region").mean()), "late_region_pc": 100 * float((l.precision == "region").mean()),
                        "early_rome_italy_pc": 100 * float(e.group.isin(["Rome", "Italy"]).mean()), "late_rome_italy_pc": 100 * float(l.group.isin(["Rome", "Italy"]).mean())}
jsave(R, f"{DATA}/results.json", indent=1)
print("derived", R["ages"]["digit_expected"], R["habit"]["fall_pc"], R["habit"]["max_share_pc"])
