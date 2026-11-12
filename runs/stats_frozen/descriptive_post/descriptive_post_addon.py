"""Add-on to descriptive_post.py (run after it): adds (a) descriptive counts of the exploratory sqrt(t) baseline against the scored arms' condition scores,
(b) horizon-1 RMSE by fold. Descriptive; no test, no tier. Writes into descriptive_post.json under keys item5_vs_scored_arms and item2_h1_by_fold."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import descriptive_post as D

res = D.J(os.path.join(D.OUT, "descriptive_post.json"))
vs = {}
for g, (m, fn) in {"g1": (8, "condition_scores_k2.json"), "g4": (32, "condition_scores.json")}.items():
    rows = res["item5_exploratory_sqrt"][g]["_cell_rows"]
    by = {}
    for x in rows:
        by.setdefault(x["cond"], {"sq": [], "r1": []})
        by[x["cond"]]["sq"].append(x["rmse_sqrt"])
        by[x["cond"]]["r1"].append(x["rmse_R1"])
    sq = {c: float(np.mean(v["sq"])) for c, v in by.items()}
    r1 = {c: float(np.mean(v["r1"])) for c, v in by.items()}
    a1, a10 = {}, {}
    for f in D.FOLDS:
        c = D.J(os.path.join(D.RUNS, f"conf_samsung_B_f{f}_m{m}", fn))
        a1.update(c["A1"])
        a10.update(c["A10"])
    vs[g] = {"condition_score_file": fn, "same_conditions": bool(set(a1) == set(sq)), "n_conditions": len(sq), "A1_mean_pp": float(np.mean(list(a1.values()))),
             "A1_median_pp": float(np.median(list(a1.values()))), "A10_mean_pp": float(np.mean(list(a10.values()))),
             "n_conditions_A1_lt_sqrt": int(sum(a1[c] < sq[c] for c in sq)), "n_conditions_A10_lt_sqrt": int(sum(a10[c] < sq[c] for c in sq)),
             "n_conditions_sqrt_lt_R1": int(sum(sq[c] < r1[c] for c in sq))}
res["item5_vs_scored_arms"] = vs
h1 = {}
for g, (m, k) in {"g1": (8, "2"), "g4": (32, "full")}.items():
    h1[g] = {}
    for f in D.FOLDS:
        mt = D.J(os.path.join(D.RUNS, f"conf_samsung_B_f{f}_m{m}", "metrics.json"))["outer_test_by_k"][k]
        h1[g][str(f)] = {a: mt[a]["horizon_rmse_pp"]["1"] for a in ("A1", "A9", "A10", "R1")}
res["item2_h1_by_fold"] = h1
json.dump(res, open(os.path.join(D.OUT, "descriptive_post.json"), "w", encoding="utf8"), indent=1, default=float)
print(json.dumps(vs, indent=1))
print(json.dumps(h1))
