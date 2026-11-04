"""Decision rule of runs/prereg/STATS_RULING.md as code (importable; used by the power simulation and, later, by
the confirmatory analysis script). Pure functions, no data access.

d = vector of condition-level paired differences (comparator score minus PINN-KAN score, percentage points;
positive favours PINN-KAN), one value per held-out condition, each already averaged over seeds.
"""
import numpy as np
from scipy import stats

Z = stats.norm


def holm_thresholds(m):
    """Step-down thresholds alpha/m, alpha/(m-1), ..., alpha for the sorted p-values (alpha = 0.05)."""
    return [0.05 / (m - i) for i in range(m)]


def holm_reject(pvals, alpha=0.05):
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


def effect_summary(d, e_comp, B=10000, seed=0):
    """Numbers for tables/abstract: mean paired difference (pp), BCa 95% interval, relative reduction vs the
    comparator's mean score, rank-biserial r (matched pairs), share of conditions won."""
    d = np.asarray(d, float)
    n = len(d)
    rng = np.random.default_rng(seed)
    boot = d[rng.integers(0, n, (B, n))].mean(1)
    lo, hi = bca_lower(d, 0.025, boot=boot), -bca_lower(-d, 0.025, boot=-boot)
    nz = d[d != 0]
    ranks = stats.rankdata(np.abs(nz))
    rb = (ranks[nz > 0].sum() - ranks[nz < 0].sum()) / ranks.sum() if len(nz) else 0.0
    return dict(n=n, mean_pp=float(d.mean()), ci95=[lo, hi], rel_reduction=float(d.mean() / e_comp),
                rel_ci95=[lo / e_comp, hi / e_comp], rank_biserial=float(rb), share_won=float((d > 0).mean()))
