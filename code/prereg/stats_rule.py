"""Decision rule of runs/prereg/STATS_RULING.md as code (importable; used by the power simulation and, later, by
the confirmatory analysis script). Pure functions, no data access.

d = vector of condition-level paired differences (comparator score minus PINN-KAN score, percentage points;
positive favours PINN-KAN), one value per held-out condition, each already averaged over seeds.
"""
import numpy as np
from scipy import stats

Z = stats.norm
ALPHA_FAMILY = 0.025      # one-sided family-wise level (= two-sided 0.05 for a directional claim)


def holm_thresholds(m, alpha=ALPHA_FAMILY):
    """Step-down thresholds alpha/m, alpha/(m-1), ..., alpha for the sorted p-values."""
    return [alpha / (m - i) for i in range(m)]


def holm_reject(pvals, alpha=ALPHA_FAMILY):
    """Holm step-down. pvals: dict name -> p. Returns dict name -> (adjusted p, rejected) and the step level used."""
    names = sorted(pvals, key=pvals.get)
    m = len(names)
    out, adj_prev, stop = {}, 0.0, False
    for i, n in enumerate(names):
        adj = min(1.0, max(adj_prev, (m - i) * pvals[n]))
        adj_prev = adj
        out[n] = (adj, adj <= alpha)
    return out


def bca_lower(d, alpha, B=10000, rng=None, boot=None):
    """One-sided BCa lower limit of the mean at confidence 1-alpha, resampling conditions (the unit).
    boot: optional precomputed bootstrap means (same d)."""
    d = np.asarray(d, float)
    n = len(d)
    th = d.mean()
    if boot is None:
        rng = np.random.default_rng() if rng is None else rng
        boot = d[rng.integers(0, n, (B, n))].mean(1)
    frac = np.clip((boot < th).mean(), 1.0 / (len(boot) + 1), 1 - 1.0 / (len(boot) + 1))
    z0 = Z.ppf(frac)
    jk = (d.sum() - d) / (n - 1)
    dj = jk.mean() - jk
    den = 6.0 * (np.sum(dj ** 2) ** 1.5)
    a = np.sum(dj ** 3) / den if den > 0 else 0.0
    za = Z.ppf(alpha)
    adj = Z.cdf(z0 + (z0 + za) / (1 - a * (z0 + za)))
    return float(np.quantile(boot, np.clip(adj, 0, 1)))


def wilcoxon_p(d, shift):
    """One-sided exact Wilcoxon signed-rank p for H0: pseudo-median(d) <= shift."""
    x = np.asarray(d, float) - shift
    if np.all(x == 0):
        return 1.0
    return float(stats.wilcoxon(x, alternative="greater", method="auto", zero_method="wilcox").pvalue)


def tier(d, delta_sup, delta_ni, alpha_step, B=10000, rng=None, boot=None):
    """Hierarchical outcome of one contrast at the Holm step level alpha_step.
    Pass criterion for a margin m: exact one-sided Wilcoxon p(d - m) <= alpha_step AND BCa one-sided lower limit
    of the mean > m at confidence 1 - alpha_step. Returns 'S' (superior by delta_sup), 'N' (non-inferior within
    delta_ni) or '-' (neither)."""
    lo = bca_lower(d, alpha_step, B=B, rng=rng, boot=boot)
    s = wilcoxon_p(d, delta_sup) <= alpha_step and lo > delta_sup
    if s:
        return "S", lo
    nI = wilcoxon_p(d, -delta_ni) <= alpha_step and lo > -delta_ni
    return ("N" if nI else "-"), lo


def effect_summary(s_comp, s_pinn, B=10000, seed=0):
    """Numbers for tables and the abstract, from the condition-level scores (seed-averaged RMSE, pp) of the
    comparator and PINN-KAN: mean paired difference (pp) with BCa 95 % interval, relative reduction
    mean(d)/mean(s_comp) with a percentile interval from the same condition resamples, matched-pairs rank-biserial
    r, share of conditions won."""
    s_comp, s_pinn = np.asarray(s_comp, float), np.asarray(s_pinn, float)
    d = s_comp - s_pinn
    n = len(d)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, (B, n))
    boot = d[idx].mean(1)
    rel = boot / s_comp[idx].mean(1)
    lo, hi = bca_lower(d, 0.025, boot=boot), -bca_lower(-d, 0.025, boot=-boot)
    nz = d[d != 0]
    ranks = stats.rankdata(np.abs(nz))
    rb = (ranks[nz > 0].sum() - ranks[nz < 0].sum()) / ranks.sum() if len(nz) else 0.0
    return dict(n=n, mean_pp=float(d.mean()), ci95=[lo, hi], rel_reduction=float(d.mean() / s_comp.mean()),
                rel_ci95=[float(np.quantile(rel, 0.025)), float(np.quantile(rel, 0.975))],
                rank_biserial=float(rb), share_won=float((d > 0).mean()))
