"""Order-of-magnitude anchor for the intra-group correlation of a log ratio between two learners (power law vs LightGBM, inner-CV
condition errors of the P3 pilot, TRAINING sides only; STATS_RULING cond_snl_W100.csv).  Groups = chemistry (3 groups, 23 conditions):
the nearest available analogue of 'lab' (groups of conditions measured on different hardware / materials).  Not Samsung, not folds.
Usage: python -P anchor_icc.py <ROOT>"""
import sys, json
import numpy as np, pandas as pd
ROOT = sys.argv[1]
d = pd.read_csv(f"{ROOT}/runs/prereg/stats_ruling/cond_snl_W100.csv").dropna(subset=["pl", "lgb"])
g = d["cond"].str.split("|").str[0].to_numpy()
L = np.log(d["pl"].to_numpy() / d["lgb"].to_numpy())

def icc(x, g):
    u = np.unique(g); k = len(u); n = len(x)
    gs = [x[g == a] for a in u]
    nbar = (n - sum(len(v) ** 2 for v in gs) / n) / (k - 1)
    msb = sum(len(v) * (v.mean() - x.mean()) ** 2 for v in gs) / (k - 1)
    msw = sum(((v - v.mean()) ** 2).sum() for v in gs) / (n - k)
    return float((msb - msw) / (msb + (nbar - 1) * msw)), {a: int((g == a).sum()) for a in u}

rng = np.random.default_rng(0)
out = {"n": len(L), "groups": icc(L, g)[1], "icc_L": icc(L, g)[0], "icc_sign": icc((L > np.median(L)).astype(float), g)[0]}
# permutation spread of the ICC under no grouping (shows how uninformative 3 groups of 23 are)
perm = [icc(L, rng.permutation(g))[0] for _ in range(2000)]
out["icc_L_perm_90pct_range"] = [float(np.quantile(perm, .05)), float(np.quantile(perm, .95))]
json.dump(out, open(f"{ROOT}/runs/prereg/stats_sim_v4/anchor_icc_snl.json", "w"), indent=1)
print(json.dumps(out, indent=1))
