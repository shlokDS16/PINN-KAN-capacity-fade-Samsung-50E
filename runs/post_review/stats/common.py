"""Shared helpers for the no-refit post-hoc statistics (D048). POST-HOC, EXPLORATORY. Reads stored files only; writes only into this folder.
The frozen graph_test module is loaded read-only by file path (no package import, no bytecode written)."""
import sys, os, json, zlib, hashlib, importlib.util
import numpy as np
import pandas as pd
from scipy import stats

sys.dont_write_bytecode = True
ROOT = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
RUNS = os.path.join(ROOT, "runs")
OUT = os.path.join(RUNS, "post_review", "stats")
FROZEN = os.path.join(RUNS, "stats_frozen", "analysis")
MC_SEED_ROOT = 20261105          # frozen Monte Carlo seed root (negcontrol.MC_SEED_ROOT); seed rule SeedSequence([root, crc32(label)])
B_BOOT = 10000


def load_frozen_graph_test():
    p = os.path.join(ROOT, "code", "pinnkan", "graph_test.py")
    spec = importlib.util.spec_from_file_location("frozen_graph_test", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["frozen_graph_test"] = m
    spec.loader.exec_module(m)
    return m, hashlib.sha256(open(p, "rb").read()).hexdigest()


def mc_rng(label):
    return np.random.default_rng(np.random.SeedSequence([MC_SEED_ROOT, zlib.crc32(label.encode())]))


def jload(p):
    return json.load(open(p, encoding="utf8"))


def jdump(o, name):
    with open(os.path.join(OUT, name), "w", encoding="utf8") as f:
        json.dump(o, f, indent=1, allow_nan=True)


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def bca(x, stat, label, B=B_BOOT, alpha=0.05):
    """BCa interval of stat(x) over resampled units (same construction as stats_step.bca_mean_ci, generalised to any statistic).
    RNG: SeedSequence([20261105, crc32(label)])."""
    x = np.asarray(x, float)
    n = len(x)
    th = float(stat(x))
    if n < 3 or np.allclose(x, x[0]):
        return th, th
    rng = mc_rng(label)
    idx = rng.integers(0, n, (B, n))
    boot = np.sort(np.array([stat(x[i]) for i in idx]) if stat is not np.mean else x[idx].mean(1))
    z0 = stats.norm.ppf(np.clip((boot < th).mean(), 1.0 / (B + 1), 1 - 1.0 / (B + 1)))
    jk = np.array([stat(np.delete(x, i)) for i in range(n)])
    d = jk.mean() - jk
    den = 6.0 * (np.sum(d ** 2) ** 1.5)
    acc = float(np.sum(d ** 3) / den) if den > 0 else 0.0
    out = []
    for q in (alpha / 2, 1 - alpha / 2):
        zq = stats.norm.ppf(q)
        p = stats.norm.cdf(z0 + (z0 + zq) / (1 - acc * (z0 + zq)))
        out.append(float(np.quantile(boot, np.clip(p, 0, 1))))
    return out[0], out[1]


def load_pred(fold, m):
    d = pd.read_csv(os.path.join(RUNS, "conf_samsung_B_f%d_m%d" % (fold, m), "predictions.csv"), dtype={"seed": str})
    return d


G = {"g1": dict(m=8, phase="outer_test_k2", scores="condition_scores_k2.json"),
     "g4": dict(m=32, phase="outer_test_kfull", scores="condition_scores.json")}
FOLDS = range(5)
