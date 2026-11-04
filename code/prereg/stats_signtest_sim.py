"""Fallback of D011 section 4.4: exact one-sided sign test on L - m (estimand: median condition log ratio).
Size at the median boundary (exact, by theory) and power at the MDE-table effects; same shapes and settings as
stats_signflip_sim.py, with the MEDIAN of L set to the target (the mean differs under skew).
Usage: python -P stats_signtest_sim.py <ROOT> [nsim]"""
import sys, json
from math import comb
import numpy as np
ROOT = sys.argv[1]; NSIM = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
sys.argv = [sys.argv[0], ROOT, "unused", "40", "normal", "1", "1"]
sys.path.insert(0, f"{ROOT}/code/prereg")
import stats_signflip_sim as S

def tail(n, k):          # P(Bin(n, .5) >= k)
    return sum(comb(n, j) for j in range(k, n + 1)) / 2 ** n

def crit(n, a):          # smallest k with P(X>=k) <= a
    for k in range(n + 1):
        if tail(n, k) <= a:
            return k
    return n + 1

rng = np.random.default_rng(777)
res = dict(size_exact={}, power=[], levels=S.LEVELS)
for n in (40, 13):
    for ln, a in S.LEVELS.items():
        k = crit(n, a)
        res["size_exact"][f"n{n}_{ln}"] = dict(k=k, actual_size=tail(n, k) if k <= n else 0.0, nominal=a)
kc = {rn: S.solve_k(r, rng) for rn, r in S.RHOS.items()}
for shape in ("isu_right", "isu_left", "normal", "contam"):
    for rn, rho in S.RHOS.items():
        big = S.gen(shape, rho, 400, 0.0, rng, 1000, kc[rn])
        med0 = float(np.median(big))
        for n in (40, 13):
            for test, m, effs in (("S", S.M_S, [0.06, 0.08, 0.10, 0.15, 0.20]), ("N_at_equality", S.M_N, [0.0])):
                for eff in effs:
                    tgt = -np.log(1 - eff) - med0
                    X = S.gen(shape, rho, n, tgt, rng, NSIM, kc[rn])
                    pos = (X > m).sum(1)
                    row = dict(shape=shape, n=n, rho=rn, test=test, effect=eff)
                    for ln, a in S.LEVELS.items():
                        row[f"pow_{ln}"] = float((pos >= crit(n, a)).mean())
                    res["power"].append(row)
json.dump(res, open(f"{ROOT}/runs/prereg/stats_ruling/signtest_fallback.json", "w"), indent=1)
print("done")
