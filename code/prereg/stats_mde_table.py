"""Reads runs/prereg/stats_ruling/power_sim.json, interpolates the minimum detectable relative effect (80 % power)."""
import json, sys, numpy as np, pandas as pd
ROOT = sys.argv[1]; TAG = sys.argv[2] if len(sys.argv) > 2 else "0.025"
r = json.load(open(f"{ROOT}/runs/prereg/stats_ruling/power_sim_alpha{TAG}.json"))
p = pd.DataFrame(r["power"])
def mde(g, col, target=0.8):
    g = g.sort_values("mu"); x, y = g.mu.values, g[col].values
    if y.max() < target: return np.nan
    i = int(np.argmax(y >= target))
    if i == 0: return float(x[0])
    return float(x[i-1] + (target - y[i-1]) * (x[i] - x[i-1]) / (y[i] - y[i-1]))
rows = []
for (sh, n, rho), g in p.groupby(["shape", "n", "rho"]):
    rows.append(dict(shape=sh, n=n, rho=rho, sigma_d=round(float(g.sigma_d.iloc[0]), 3),
                     mde_holm4_step1=mde(g, "holm4_first__S"), mde_holm3_step1=mde(g, "holm3_first__S"),
                     mde_last_step=mde(g, "holm_last__S")))
t = pd.DataFrame(rows).round(3)
t.to_csv(f"{ROOT}/runs/prereg/stats_ruling/mde_table_alpha{TAG}.csv", index=False)
print(t.to_string())
