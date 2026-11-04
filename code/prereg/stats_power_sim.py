"""Power / size simulation for the preregistered decision rule (STATS_RULING.md item 7). CPU only, synthetic.

Scale: comparator mean score E = 1 (all effects and margins are fractions of E; multiply by the comparator's
inner-CV RMSE in pp). Assumptions (none is a Samsung number):
  - condition-level paired differences d_c = mu + sigma_d * Z_c + seed noise, n conditions, iid across conditions;
  - sigma_d / E from the correlation rho between the two arms' condition errors: SD(e)/E = 0.45 (measured on
    training sides of ISU/SNL, stats_warp_calibration.py), sigma_d = 0.45 sqrt(2 (1 - rho)) E:
      rho = 0.95 -> 0.14 (variants of one model: H1a, H1b), 0.90 -> 0.20, 0.75 -> 0.32 (different families:
      H1c; ISU power law vs LightGBM measured 0.75);
  - Z shape: 'skew' = standardised ISU (power law - LightGBM) condition differences resampled with jitter
    (skewness 1.06, excess kurtosis 2.7), 'skew_left' its mirror image, 'normal';
  - seed noise: each arm's condition score is a mean over S seeds with per-seed SD sigma_s = 0.05 E, so the
    difference gets variance 2 sigma_s^2 / S (S = 5);
  - decision rule exactly as stats_rule.tier (exact Wilcoxon AND BCa lower limit, both at the Holm step level).
Usage: python -P stats_power_sim.py <ROOT> [nsim] [B] [family alpha, one-sided, default 0.025]
"""
import os, sys, json, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np, pandas as pd

ROOT = sys.argv[1]
NSIM = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
B = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
A_FAM = float(sys.argv[4]) if len(sys.argv) > 4 else 0.025      # family-wise one-sided alpha (= two-sided 0.05)
sys.path.insert(0, f"{ROOT}/code/prereg")
import stats_rule as R

OUT = f"{ROOT}/runs/prereg/stats_ruling"
S_SEEDS, SIG_S = 5, 0.05
D_SUP, D_NI = 0.02, 0.10
ALPHAS = {"holm4_first": A_FAM / 4, "holm3_first": A_FAM / 3, "holm_last": A_FAM}

cond = pd.read_csv(f"{OUT}/cond_isu_W4.csv").dropna()
emp = (cond["pl"] - cond["lgb"]).values
emp = (emp - emp.mean()) / emp.std(ddof=0)


def shape(kind, rng, size):
    if kind == "normal":
        return rng.standard_normal(size)
    z = rng.choice(emp, size) + 0.2 * rng.standard_normal(size)
    z = (z - emp.mean()) / np.sqrt(1 + 0.04)
    return -z if kind == "skew_left" else z


def draw(n, mu, sig, kind, rng):
    return mu + sig * shape(kind, rng, n) + rng.standard_normal(n) * np.sqrt(2 * SIG_S ** 2 / S_SEEDS)


def one_cell(n, mu, sig, kind, rng):
    cnt = {a: dict(S=0, NI_or_S=0) for a in ALPHAS}
    for _ in range(NSIM):
        d = draw(n, mu, sig, kind, rng)
        boot = d[rng.integers(0, n, (B, n))].mean(1)
        for a, al in ALPHAS.items():
            t, _ = R.tier(d, D_SUP, D_NI, al, boot=boot)
            cnt[a]["S"] += (t == "S"); cnt[a]["NI_or_S"] += (t in ("S", "N"))
    return {a: {k: v / NSIM for k, v in c.items()} for a, c in cnt.items()}


def conj(n, mu, sig, rho_c, m_family, rng):
    """P(all three superiority hypotheses rejected by Holm) with equal mu, common correlation rho_c between the
    contrasts (shared factor), Wilcoxon only (BCa omitted: slightly optimistic). m_family = 3 or 4 (4th contrast
    assumed to be rejected first with p ~ 0)."""
    ok = 0
    for _ in range(NSIM):
        sh = rng.standard_normal(n)
        ps = []
        for _k in range(3):
            d = mu + sig * (np.sqrt(rho_c) * sh + np.sqrt(1 - rho_c) * rng.standard_normal(n)) \
                + rng.standard_normal(n) * np.sqrt(2 * SIG_S ** 2 / S_SEEDS)
            ps.append(R.wilcoxon_p(d, D_SUP))
        ps = sorted(ps)
        if m_family == 4:
            thr = [A_FAM / 3, A_FAM / 2, A_FAM]          # the 4th hypothesis is rejected first at A_FAM/4, rest as Holm-3
        else:
            thr = [A_FAM / 3, A_FAM / 2, A_FAM]
        ok += all(p <= t for p, t in zip(ps, thr))
    return ok / NSIM


def main():
    rng = np.random.default_rng(20261105)
    t0 = time.time()
    res = dict(settings=dict(nsim=NSIM, B=B, S=S_SEEDS, sigma_seed=SIG_S, delta_sup=D_SUP, delta_ni=D_NI, alphas=ALPHAS),
               power=[], size=[], conj=[])
    mus = [0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20]
    sig_map = {"rho0.95": 0.45 * np.sqrt(2 * 0.05), "rho0.90": 0.45 * np.sqrt(2 * 0.10), "rho0.75": 0.45 * np.sqrt(2 * 0.25)}
    # power grid
    for kind, ns in (("skew", (40, 27, 13)), ("normal", (40,))):
        for n in ns:
            for sname, sig in sig_map.items():
                for mu in mus:
                    r = one_cell(n, mu, sig, kind, rng)
                    res["power"].append(dict(shape=kind, n=n, rho=sname, sigma_d=sig, mu=mu, **{f"{a}__{k}": v for a, c in r.items() for k, v in c.items()}))
                print(kind, n, sname, "done", round(time.time() - t0), "s", flush=True)
    # size at the null boundaries (should be <= alpha_step): S-null mu = D_SUP, NI-null mu = -D_NI
    for kind in ("skew", "skew_left", "normal"):
        for n in (40, 13):
            for sname, sig in sig_map.items():
                for label, mu in (("sup_boundary", D_SUP), ("ni_boundary", -D_NI)):
                    cnt = {a: 0 for a in ALPHAS}
                    for _ in range(NSIM):
                        d = draw(n, mu, sig, kind, rng)
                        boot = d[rng.integers(0, n, (B, n))].mean(1)
                        for a, al in ALPHAS.items():
                            lo = R.bca_lower(d, al, boot=boot)
                            if label == "sup_boundary":
                                cnt[a] += (R.wilcoxon_p(d, D_SUP) <= al and lo > D_SUP)
                            else:
                                cnt[a] += (R.wilcoxon_p(d, -D_NI) <= al and lo > -D_NI)
                    res["size"].append(dict(shape=kind, n=n, rho=sname, boundary=label, **{f"rej_{a}": cnt[a] / NSIM for a in ALPHAS}))
        print("size", kind, round(time.time() - t0), "s", flush=True)
    # conjunction of three contrasts under Holm
    for sname in ("rho0.95", "rho0.90"):
        for mu in (0.04, 0.06, 0.08, 0.10, 0.15):
            res["conj"].append(dict(n=40, rho=sname, mu=mu, rho_contrasts=0.5,
                                    all3_pass_holm=conj(40, mu, sig_map[sname], 0.5, 3, rng)))
    res["seconds"] = time.time() - t0
    json.dump(res, open(f"{OUT}/power_sim_alpha{A_FAM}.json", "w"), indent=1)
    print("done", round(time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
