"""Fix 11 (median condition score per arm and D*, g1 and g4) and fix 18 (model-defined calendar share by temperature and laboratory).
Descriptive only: no test, no tier. Reads run outputs only (condition_scores, comparators, condition_meta, superposition.csv); never data/.
Run from MAIN: OMP_NUM_THREADS=1 .venv/Scripts/python.exe -P runs/stats_frozen/descriptive_post/descriptive_post_tables.py"""
import json
import os
import re
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
from pinnkan import stats_v4 as v4  # noqa: E402

R = os.path.join(ROOT, "runs")
OUT = os.path.dirname(os.path.abspath(__file__))


def store_for(m):
    return v4.Store.from_runs([os.path.join(R, f"conf_samsung_B_f{f}_m{m}") for f in range(5)])


def table(st, key):
    t = st.tables[key]
    res = {}
    for a, sc in sorted(t.items()):
        v = np.array(list(sc.values()), float)
        res[a] = dict(n_conditions=int(v.size), mean_pp=float(v.mean()), median_pp=float(np.median(v)),
                      min_pp=float(v.min()), max_pp=float(v.max()))
    return res


def fix11():
    arm = json.load(open(os.path.join(R, "stats_frozen", "post", "arm_table.json"), encoding="utf8"))
    out = {"definition": "condition score = primary endpoint per held-out condition (condition_scores.json; pp). median_pp = median over the 40 conditions; "
                         "mean_pp = plain mean over the same 40 conditions (equals arm_table mean_pp, which weights folds by condition counts). "
                         "D* = per fold the arm named in comparators.json['D*'] (inner-CV winner), assembled as stats_v4.Store.from_runs does; the D* column pools different learners across folds. Descriptive, no test.",
           "cells": {}, "mean_check_vs_arm_table": {}}
    for tag, m, k in (("g1", 8, "2"), ("g4", 32, "full")):
        st = store_for(m)
        key = st.key(m, k)
        out["cells"][tag] = dict(m=m, k=k, store_key=list(key), table=table(st, key),
                                 d_star_by_fold={str(r["fold"]): r["comparators"].get("D*") for r in st.notes["runs"]})
        ref = arm["cells"][f"{m}|{k}"]
        chk = {}
        for a, e in out["cells"][tag]["table"].items():
            if a in ref:
                chk[a] = dict(mine=e["mean_pp"], arm_table=ref[a]["mean_pp"], absdiff=abs(e["mean_pp"] - ref[a]["mean_pp"]))
        out["mean_check_vs_arm_table"][tag] = chk
        out["cells"][tag]["max_absdiff_mean_vs_arm_table"] = max(c["absdiff"] for c in chk.values())
    return out


def fix18():
    parts = []
    for f in range(5):
        d = os.path.join(R, f"conf_samsung_B_f{f}_m32")
        df = pd.read_csv(os.path.join(d, "superposition.csv"))
        meta = json.load(open(os.path.join(d, "condition_meta.json"), encoding="utf8"))
        df["lab"] = df["cond"].map(lambda c: sorted(meta[c]["lab"].items(), key=lambda kv: (-kv[1], kv[0]))[0][0])
        df["T"] = df["cond"].map(lambda c: re.match(r"T(\d+)", c).group(1))
        df["fold"] = f
        parts.append(df)
    df = pd.concat(parts, ignore_index=True)
    exc = df["cal_exceeds_total"].astype(str).str.lower().isin(["true", "1"])
    df["gt1"] = df["share_cal"] > 1
    res = dict(source="runs/conf_samsung_B_f{0..4}_m32/superposition.csv (the runs physval item 4 reads); lab from condition_meta.json (majority lab of the condition's cells); T from the condition key",
               definition="share_cal = model-defined counterfactual calendar share (PREREG_v4 11a item 4); n_gt1 = cells with share_cal > 1",
               n_rows=int(len(df)), n_cells_per_arm={a: int(len(g)) for a, g in df.groupby("arm")},
               n_cal_exceeds_total_flag=int(exc.sum()), by={})

    def summ(g):
        return dict(n_cells=int(len(g)), n_conditions=int(g["cond"].nunique()), median=float(g["share_cal"].median()),
                    min=float(g["share_cal"].min()), max=float(g["share_cal"].max()), n_gt1=int(g["gt1"].sum()))
    for name, col in (("temperature_C", "T"), ("laboratory", "lab")):
        res["by"][name] = {arm: {str(k): summ(g) for k, g in ga.groupby(col)} for arm, ga in df.groupby("arm")}
    res["by"]["all"] = {arm: summ(g) for arm, g in df.groupby("arm")}
    res["lab_by_temperature_cells"] = {str(k): {str(l): int(n) for l, n in g["lab"].value_counts().items()} for k, g in df[df.arm == "A1"].groupby("T")}
    res["note"] = ("There is no 35 C storage in these data; the 35 C cells are all laboratory INT (see lab_by_temperature_cells). "
                   "Temperature and laboratory are confounded at 35 C; the by-laboratory and by-temperature rows are not independent comparisons.")
    return res


def main():
    out = {"fix11": fix11(), "fix18": fix18()}
    json.dump(out, open(os.path.join(OUT, "descriptive_post_tables.json"), "w", encoding="utf8"), indent=1)
    print("max |mean - arm_table| g1/g4:", out["fix11"]["cells"]["g1"]["max_absdiff_mean_vs_arm_table"],
          out["fix11"]["cells"]["g4"]["max_absdiff_mean_vs_arm_table"])


if __name__ == "__main__":
    main()
