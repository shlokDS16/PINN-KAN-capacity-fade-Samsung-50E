"""Writes cond_structure.csv: the 40 Test B cycling conditions with fold (samsung_splits_v2.json, B) and lab/temperature
(data/raw/samsung50e_meta/experiments_meta.csv, columns serial, lab, type, stage, amb_temp_tp, soc_max_tp, dod_tp, c_ch_tp, c_dch_tp ONLY).
No capacity value is read; the metadata file has none. Lab of a condition = majority lab of its cells (ties: alphabetical).
Usage: python -P make_structure.py <ROOT>"""
import csv, json, sys
from collections import Counter
ROOT = sys.argv[1]
B = json.load(open(f"{ROOT}/runs/prereg/samsung_splits_v2.json"))["B"]["folds"]
fold_of = {c: int(f) for f, v in B.items() for c in v["test_conditions"]}
cols = ["lab", "type", "amb_temp_tp", "soc_max_tp", "dod_tp", "c_ch_tp", "c_dch_tp"]
labs = {}
for r in csv.DictReader(open(f"{ROOT}/data/raw/samsung50e_meta/experiments_meta.csv")):
    r = {k.strip(): v for k, v in r.items()}
    if r["type"] != "z":
        continue
    cid = "T%g|SOCmax%g|DoD%g|Cch%g|Cdch%g" % tuple(float(r[c]) for c in cols[2:])
    labs.setdefault(cid, []).append(r["lab"].strip())
assert set(labs) == set(fold_of) and len(labs) == 40
with open(f"{ROOT}/runs/prereg/stats_sim_v4/cond_structure.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["cond", "fold", "temp", "lab_majority", "labs_all", "n_cells"])
    for c in sorted(labs):
        cnt = Counter(labs[c]); top = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        w.writerow([c, fold_of[c], c.split("|")[0][1:], top, "+".join(sorted(cnt)), len(labs[c])])
