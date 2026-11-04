"""Aggregates runs/prereg/stats_ruling/negctl/summary_s*.json (negcontrol_check.py) for NEGCONTROL_RULING.md. Exact tests only (no RNG)."""
import glob
import json
import sys

import numpy as np
from scipy import stats

ROOT = sys.argv[1]
OUT = f"{ROOT}/runs/prereg/stats_ruling/negctl"
LN = np.log(1.02)


def sign_p_one(L, m=0.0):
    L = np.asarray(L, float)
    return float(stats.binom.sf(int((L > m).sum()) - 1, len(L), 0.5))


rows = []
for f in sorted(glob.glob(f"{OUT}/summary_s*.json")):
    r = json.load(open(f))
    real = r["real"]["cond_scores"]
    row = {"seed": r["seed"]}
    for v in ("clean", "leakA", "leakB"):
        x = r[v]
        cs = x["cond_scores"]
        conds = sorted(cs["A1"])
        L9 = np.array([np.log(cs["A9"][c] / cs["A1"][c]) for c in conds])          # >0: A1 better than A9 (permuted stress)
        L2 = np.array([np.log(cs["R2"][c] / cs["A1"][c]) for c in conds])
        Lp = np.array([np.log(cs["A1"][c] / real["A1"][c]) for c in conds])         # >0: scrambling the stress hurts A1
        L9r = np.array([np.log(real["A9"][c] / real["A1"][c]) for c in conds])
        nc = x["negative_control"]
        row[v] = dict(max_dpred=x["max_abs_dpred"], max_dpred_outer=x["max_abs_dpred_outer"], tuning_same=x["tuning_same"], n_cond=len(conds),
                      orig_pass_resid=nc["pass_residual_effect_vanishes"], orig_pass_R2=nc["pass_A1_not_better_than_R2"], orig_pass=nc["passed"],
                      mean_L9_perm=float(L9.mean()), mean_L2_perm=float(L2.mean()),
                      A1_perm_pp=float(np.mean([cs["A1"][c] for c in conds])), A1_real_pp=float(np.mean([real["A1"][c] for c in conds])),
                      A9_perm_pp=float(np.mean([cs["A9"][c] for c in conds])), A9_real_pp=float(np.mean([real["A9"][c] for c in conds])),
                      nc2a_median_L=float(np.median(Lp)), nc2a_p=sign_p_one(Lp), nc2a_pass=bool(sign_p_one(Lp) <= 0.025),
                      L9_real_mean=float(L9r.mean()),
                      A1_beats_A9_perm_p=sign_p_one(L9, LN))
    rows.append(row)
json.dump(rows, open(f"{OUT}/aggregate.json", "w"), indent=1)
n = len(rows)
print("seeds", [r["seed"] for r in rows])
for v in ("clean", "leakA", "leakB"):
    print(v,
          "| NC-1 flagged (max dpred > 1e-12):", sum(r[v]["max_dpred"] > 1e-12 for r in rows), "/", n,
          "| max dpred min..max:", f"{min(r[v]['max_dpred'] for r in rows):.3g}..{max(r[v]['max_dpred'] for r in rows):.3g}",
          "| orig(i) pass:", sum(r[v]["orig_pass_resid"] for r in rows), "orig(ii) pass:", sum(r[v]["orig_pass_R2"] for r in rows), "orig both:", sum(r[v]["orig_pass"] for r in rows),
          "| NC-2a pass:", sum(r[v]["nc2a_pass"] for r in rows),
          "| mean L(A9/A1) perm:", [round(r[v]["mean_L9_perm"], 2) for r in rows],
          "| A1 beats A9 (perm) one-sided p<=.025:", sum(r[v]["A1_beats_A9_perm_p"] <= 0.025 for r in rows))
print("L(A9/A1) real stress:", [round(r["clean"]["L9_real_mean"], 2) for r in rows])
print("A1 perm / real pp:", [(round(r["clean"]["A1_perm_pp"], 2), round(r["clean"]["A1_real_pp"], 2)) for r in rows])
print("A9 perm / real pp:", [(round(r["clean"]["A9_perm_pp"], 2), round(r["clean"]["A9_real_pp"], 2)) for r in rows])
print("NC-2a median L clean:", [round(r["clean"]["nc2a_median_L"], 2) for r in rows], "p:", [round(r["clean"]["nc2a_p"], 4) for r in rows])
