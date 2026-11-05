"""D018 action A3: fb_tables.csv = fallback (fixed design-effect sign test) counts, one-sided lower-bound order statistic, and interval ranks,
for every n of Test B after the 3.3(11) exclusions (40 down to 35), the ISU n (63 down to 58) and every level in use, for the sensitivity grid
rho_s0 in {0, 0.01, 0.02, 0.03, 0.05} (rho_s0 = 0.03 is the confirmatory value).  Also item (f): coverage of the one-sided upper limit of the
intra-fold sign correlation (simulation).  Only code/pinnkan/graph_test.py is used.  Usage: python -P build_fb_tables.py"""
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
from pinnkan import graph_test as gt

LEVELS = [("0.005 (secondary Holm 1/5)", 0.005), ("0.00625 (Holm 1/4)", 0.00625), ("0.00833 (Holm 1/3)", 0.025 / 3), ("0.0125 (graph, w=1/2, one chain)", 0.0125),
          ("0.025 (graph both chains; reverse S; last Holm step; NC-2; GAP-1)", 0.025), ("0.0195 (w=0.78, P chain)", 0.0195), ("0.0055 (w=0.78, K chain)", 0.0055)]
NS = [("Test B", n) for n in range(40, 34, -1)] + [("ISU", n) for n in range(63, 57, -1)]
rows = []
for dom, n in NS:
    for rho in gt.RHO_GRID:
        tb = gt.betabin_tail_table(n, rho)
        t0 = gt.binom_tail_table(n)
        for lab, a in LEVELS:
            k = gt.betabin_crit(n, a, rho)
            ok = k <= n
            rows.append(dict(kind="test", domain=dom, n=n, rho_s0=rho, level_label=lab, level=a, positives_needed=k if ok else np.nan,
                             reachable=ok, size_under_betabin_null=float(tb[k]) if ok else np.nan, size_if_independent=float(t0[k]) if ok else np.nan,
                             lower_bound_order_stat=(n - k + 1) if ok else np.nan, interval_rank=np.nan, interval_lo_index=np.nan, interval_hi_index=np.nan, coverage=np.nan))
        for lab, a in (("two-sided 0.05 (95 % interval)", 0.05), ("two-sided 0.05/9 (simultaneous over 9 cells)", 0.05 / 9), ("two-sided 0.05/18 (descriptive)", 0.05 / 18)):
            r, cov = gt.dep_interval_rank(n, a, rho)
            rows.append(dict(kind="interval", domain=dom, n=n, rho_s0=rho, level_label=lab, level=a, positives_needed=np.nan, reachable=r > 0,
                             size_under_betabin_null=np.nan, size_if_independent=np.nan, lower_bound_order_stat=np.nan, interval_rank=r,
                             interval_lo_index=r if r else 1, interval_hi_index=(n + 1 - r) if r else n, coverage=cov))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(HERE, "fb_tables.csv"), index=False)
print(df[(df.rho_s0 == 0.03) & (df.kind == "test") & (df.domain == "Test B")].pivot_table(index="n", columns="level_label", values="positives_needed").to_string())

# ---- item (f): coverage of the one-sided 95 % upper limit of the intra-fold sign ICC (5 folds of 8), latent Gaussian fold effect
ST = pd.read_csv(os.path.join(HERE, "cond_structure.csv"))
fold, lab = ST.fold.to_numpy(), pd.factorize(ST.lab_majority)[0]
rng = np.random.default_rng(np.random.SeedSequence([20261105, 77]))
out = []
for icc_lat in (0.0, 0.05, 0.10, 0.20):
    true_sign = (2 / np.pi) * np.arcsin(icc_lat)                       # sign correlation of two conditions in one fold (Gaussian latent)
    up, pt, cover, exceed = [], [], 0, 0
    nrep = 4000
    for _ in range(nrep):
        z = np.sqrt(icc_lat) * rng.standard_normal(5)[fold] + np.sqrt(1 - icc_lat) * rng.standard_normal(40)
        rep = gt.dependence_report((z > np.median(z)).astype(float), fold, lab)
        up.append(rep["rho_fold_upper"]); pt.append(rep["rho_fold"])
        cover += rep["rho_fold_upper"] >= true_sign
        exceed += rep["exceeds_rho_s0"]
    out.append(dict(latent_fold_icc=icc_lat, true_sign_corr=true_sign, mean_point=float(np.mean(pt)), mean_upper=float(np.mean(up)),
                    coverage_of_upper_limit=cover / nrep, share_point_above_0_03=exceed / nrep, nrep=nrep))
pd.DataFrame(out).to_csv(os.path.join(HERE, "f_upper_bound_coverage.csv"), index=False)
print(pd.DataFrame(out).round(3).to_string())
