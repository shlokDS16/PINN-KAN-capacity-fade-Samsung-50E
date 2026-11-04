"""D011 judge section 4.3: type-I error and power of the log-ratio rule (studentized sign-flip permutation test AND BCa lower bound).

Rule for margin m on L_c = ln(S_comp,c / S_PINN,c), one value per condition (seed-averaged scores):
  pass(a, m)  <=>  p_signflip(mean(L - m); studentized) <= a   AND   BCa one-sided lower bound of mean(L) at 1-a  > m.
  Superiority m = ln(1.02); non-inferiority m = -ln(1.10).
Note: under sign flips sum(x^2) is invariant, so the studentized statistic is a monotone function of the mean: the
studentized and the plain sign-flip test are the same test; the t form is kept to follow the ruling.

Null-boundary cells: mean(L) = m exactly (the mean is the estimand). Shapes of L (CV of condition errors 0.45, correlation
rho of the arms' log errors, sigma_L = s sqrt(2(1-rho)), s = sqrt(ln(1+0.45^2))):
  isu_right / isu_left : standardised ISU (power law - LightGBM) training-side shape, skew +1.06 / -1.06
  normal               : normal L (two lognormal arms)
  contam               : both arms lognormal; PINN score x k on a Bernoulli(f=0.10) share of conditions, k solved so the PP
                         difference S_comp - S_PINN has skewness -1.06 (population value, 400k conditions)
All shapes + seed noise on the log ratio, SD sqrt(2) * 0.05 / sqrt(5).
Sims use B_sf sign flips and B_boot resamples (spot check at 100,000 / 10,000 = the final-analysis settings).
Usage: python -P stats_signflip_sim.py <ROOT> <tag> <n_list> <shape_list> <nsim_null> <nsim_pow> [B_sf] [B_boot] [mode]
"""
import os, sys, json, time
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np, pandas as pd
from scipy import stats, optimize

ROOT, TAG = sys.argv[1], sys.argv[2]
NS = [int(x) for x in sys.argv[3].split(",")]
SHAPES = sys.argv[4].split(",")
NSIM_NULL, NSIM_POW = int(sys.argv[5]), int(sys.argv[6])
B_SF = int(sys.argv[7]) if len(sys.argv) > 7 else 4000
B_BOOT = int(sys.argv[8]) if len(sys.argv) > 8 else 1000
MODE = sys.argv[9] if len(sys.argv) > 9 else "full"      # full | spot
sys.path.insert(0, f"{ROOT}/code/prereg")
import stats_rule as R

OUT = f"{ROOT}/runs/prereg/stats_ruling"
A_FAM = 0.025
LEVELS = {"a/4": A_FAM / 4, "a/3": A_FAM / 3, "a/2": A_FAM / 2, "a": A_FAM}      # a = last Holm step = gatekept level
M_S, M_N = np.log(1.02), -np.log(1.10)
CV = 0.45
S_LN = np.sqrt(np.log(1 + CV ** 2))
RHOS = {"rho0.95": 0.95, "rho0.90": 0.90, "rho0.75": 0.75}
SEED_SD = np.sqrt(2) * 0.05 / np.sqrt(5)
F_CONT = 0.10

cond = pd.read_csv(f"{OUT}/cond_isu_W4.csv").dropna()
emp = (cond["pl"] - cond["lgb"]).values
emp = (emp - emp.mean()) / emp.std(ddof=0)


def solve_k(rho, rng):
    """k such that the PP difference S_comp - k^{Bernoulli(f)} S_PINN has skewness -1.06 (population, MC)."""
    N = 400000
    g = rng.standard_normal(N); e1 = rng.standard_normal(N); e2 = rng.standard_normal(N)
    sc = np.exp(-S_LN ** 2 / 2 + S_LN * (np.sqrt(rho) * g + np.sqrt(1 - rho) * e1))
    sp = np.exp(-S_LN ** 2 / 2 + S_LN * (np.sqrt(rho) * g + np.sqrt(1 - rho) * e2))
    c = rng.random(N) < F_CONT
    def sk(k):
        d = sc - np.where(c, k, 1.0) * sp
        return stats.skew(d) + 1.06
    return float(optimize.brentq(sk, 1.05, 12.0))


def gen(shape, rho, n, mean_target, rng, nb, kcont):
    sigL = S_LN * np.sqrt(2 * (1 - rho))
    if shape in ("isu_right", "isu_left"):
        z = rng.choice(emp, (nb, n)) + 0.2 * rng.standard_normal((nb, n))
        z = (z - emp.mean()) / np.sqrt(1 + 0.04)
        z = -z if shape == "isu_left" else z
        L = mean_target + sigL * z
    elif shape == "normal":
        L = mean_target + sigL * rng.standard_normal((nb, n))
    elif shape == "contam":
        c = rng.random((nb, n)) < F_CONT
        L = mean_target + sigL * rng.standard_normal((nb, n)) - np.log(kcont) * c + F_CONT * np.log(kcont)
    else:
        raise ValueError(shape)
    return L + SEED_SD * rng.standard_normal((nb, n))


def reject_batch(X, m, rng):
    """X: (nb, n) L values. Returns dict level -> boolean array (rule passes at that level)."""
    nb, n = X.shape
    x = X - m
    Q = (x ** 2).sum(1)
    S = rng.choice([-1.0, 1.0], size=(B_SF, n))
    mstar = (S @ x.T) / n                                              # (B, nb)
    tstar = mstar / np.sqrt(np.maximum((Q - n * mstar ** 2) / (n * (n - 1)), 1e-300))
    mobs = x.mean(1)
    tobs = mobs / np.sqrt(np.maximum((Q - n * mobs ** 2) / (n * (n - 1)), 1e-300))
    p = (1 + (tstar >= tobs - 1e-12).sum(0)) / (1 + B_SF)
    out = {k: np.zeros(nb, bool) for k in LEVELS}
    for i in range(nb):
        need = [k for k, a in LEVELS.items() if p[i] <= a]
        if not need:
            continue
        idx = rng.integers(0, n, (B_BOOT, n))
        boot = X[i][idx].mean(1)
        for k in need:
            out[k][i] = R.bca_lower(X[i], LEVELS[k], boot=boot) > m
    return out


def run_cell(shape, rho, n, mean_target, m, nsim, rng, kcont, bs=100):
    cnt = {k: 0 for k in LEVELS}
    done = 0
    while done < nsim:
        nb = min(bs, nsim - done)
        X = gen(shape, rho, n, mean_target, rng, nb, kcont)
        r = reject_batch(X, m, rng)
        for k in LEVELS:
            cnt[k] += int(r[k].sum())
        done += nb
    return {k: cnt[k] / nsim for k in LEVELS}


def wilson_upper(p, n, z=1.96):
    c = (p + z * z / (2 * n) + z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)
    return float(c)


def main():
    rng = np.random.default_rng(20261105 + sum(NS) + len(SHAPES))
    t0 = time.time()
    res = dict(settings=dict(B_sf=B_SF, B_boot=B_BOOT, nsim_null=NSIM_NULL, nsim_pow=NSIM_POW, levels=LEVELS, m_S=M_S, m_N=M_N,
                             cv=CV, seed_sd=SEED_SD, f_cont=F_CONT, mode=MODE), null=[], power=[], kcont={})
    for rn, rho in RHOS.items():
        res["kcont"][rn] = solve_k(rho, rng)
    effects = [0.06, 0.08, 0.10, 0.15, 0.20]
    for shape in SHAPES:
        for n in NS:
            for rn, rho in RHOS.items():
                k = res["kcont"][rn]
                for bname, m in (("sup_boundary", M_S), ("ni_boundary", M_N)):
                    r = run_cell(shape, rho, n, m, m, NSIM_NULL, rng, k)
                    res["null"].append(dict(shape=shape, n=n, rho=rn, boundary=bname, nsim=NSIM_NULL,
                                            **{f"rej_{a}": v for a, v in r.items()}))
                if MODE == "spot":
                    continue
                for eff in effects:
                    r = run_cell(shape, rho, n, -np.log(1 - eff), M_S, NSIM_POW, rng, k)
                    res["power"].append(dict(shape=shape, n=n, rho=rn, test="S", effect=eff, **{f"pow_{a}": v for a, v in r.items()}))
                r = run_cell(shape, rho, n, 0.0, M_N, NSIM_POW, rng, k)
                res["power"].append(dict(shape=shape, n=n, rho=rn, test="N_at_equality", effect=0.0, **{f"pow_{a}": v for a, v in r.items()}))
            print(shape, n, "done", round(time.time() - t0), "s", flush=True)
    res["seconds"] = time.time() - t0
    json.dump(res, open(f"{OUT}/signflip_{TAG}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
