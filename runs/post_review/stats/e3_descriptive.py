"""E3: descriptive seed-spread summaries of the five-seed ensembles (A1; A9 as a second column) at g1 and g4, from stored predictions. No refit, no conformal method.
The spread is OPTIMISATION (training-seed) spread; it is not a predictive uncertainty and no coverage guarantee is claimed. POST-HOC, EXPLORATORY (D048).
Intervals: cluster bootstrap over the 40 held-out conditions (seed rule SeedSequence([20261105, crc32(label)]))."""
import sys
sys.path.insert(0, r"C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\post_review\stats")
import numpy as np
from scipy import stats as sps
from common import *

ARMS = ["A1", "A9"]
B_POINT_SPEARMAN = 2000          # point-level Spearman bootstrap (re-ranking per resample); stated in the output


def build(g, arm):
    m, ph = G[g]["m"], G[g]["phase"]
    frames = []
    ens_check = 0.0
    for f in FOLDS:
        d = load_pred(f, m)
        x = d[(d.phase == ph) & (d.arm == arm)]
        s = x[x.seed.isin(["0", "1", "2", "3", "4"])]
        piv = s.pivot_table(index=["cell_id", "cond", "t", "true_retention"], columns="seed", values="pred_retention", aggfunc="first").reset_index()
        assert piv[["0", "1", "2", "3", "4"]].notna().all().all(), "missing seed rows"
        e = x[x.seed == "ens"][["cell_id", "t", "pred_retention"]].rename(columns={"pred_retention": "ens"})
        piv = piv.merge(e, on=["cell_id", "t"])
        ens_check = max(ens_check, float(np.abs(piv[["0", "1", "2", "3", "4"]].mean(1) - piv.ens).max()))
        piv["fold"] = f
        piv = piv.sort_values(["cell_id", "t"])
        piv["h"] = piv.groupby("cell_id").cumcount() + 1
        frames.append(piv)
    P = pd.concat(frames, ignore_index=True)
    S = P[["0", "1", "2", "3", "4"]].values * 100.0
    y = P.true_retention.values * 100.0
    mu = S.mean(1)
    sd = S.std(1, ddof=1)
    out = dict(P=P, S=S, y=y, mu=mu, sd=sd, ens=P.ens.values * 100.0, ens_check=ens_check)
    return out


def cluster_ratio_ci(num, den, cond_idx, label, B=B_BOOT):
    """ratio of sums (pooled share) with a cluster bootstrap over conditions"""
    nc = cond_idx.max() + 1
    sn = np.bincount(cond_idx, weights=num, minlength=nc)
    sdn = np.bincount(cond_idx, weights=den, minlength=nc)
    rng = mc_rng(label)
    cnt = np.array([np.bincount(rng.integers(0, nc, nc), minlength=nc) for _ in range(B)])
    r = (cnt @ sn) / (cnt @ sdn)
    return float(sn.sum() / sdn.sum()), [float(np.quantile(r, .025)), float(np.quantile(r, .975))]


res = {"note": "POST-HOC, EXPLORATORY (D048). OPTIMISATION (training-seed) spread of five seeds; NOT a predictive uncertainty; no calibration or coverage guarantee for new conditions. No conformal method.",
       "bootstrap_B": B_BOOT, "bootstrap_B_point_level_spearman": B_POINT_SPEARMAN, "interval_unit": "held-out condition (cluster bootstrap, percentile 95 %)", "cells": {}}
for g in ("g1", "g4"):
    res["cells"][g] = {}
    for arm in ARMS:
        D = build(g, arm)
        P, S, y, mu, sd, ens = D["P"], D["S"], D["y"], D["mu"], D["sd"], D["ens"]
        conds = sorted(P.cond.unique())
        assert len(conds) == 40
        ci = P.cond.map({c: i for i, c in enumerate(conds)}).values
        n = len(P)
        ae = np.abs(ens - y)                      # absolute error of the five-seed ensemble mean, pp
        lo_, hi_ = S.min(1), S.max(1)
        covered = {"seed_min_max_envelope": ((y >= lo_) & (y <= hi_)).astype(float)}
        for k in (1, 2, 3):
            covered["mean_pm_%d_seed_sd" % k] = (np.abs(y - mu) <= k * sd).astype(float)
        # horizon-index tertiles (fixed cut points on the pooled forecast index h, no tuning)
        hc = np.quantile(P.h.values, [1 / 3, 2 / 3])
        ter = np.where(P.h.values <= hc[0], 0, np.where(P.h.values <= hc[1], 1, 2))
        r = dict(n_points=int(n), n_cells=int(P.cell_id.nunique()), n_conditions=40, ens_equals_seed_mean_max_abs_diff_retention=D["ens_check"],
                 horizon_index_tertile_cut_points=[float(hc[0]), float(hc[1])])
        cov = {}
        for name, v in covered.items():
            est, ciw = cluster_ratio_ci(v, np.ones(n), ci, "E3|%s|%s|cov|%s" % (g, arm, name))
            row = dict(share=est, ci95=ciw, by_horizon_index_tertile=[])
            for t in range(3):
                sel = ter == t
                e2, c2 = cluster_ratio_ci(v * sel, sel.astype(float), ci, "E3|%s|%s|cov|%s|t%d" % (g, arm, name, t)) if sel.any() else (float("nan"), [float("nan")] * 2)
                row["by_horizon_index_tertile"].append(dict(tertile=t + 1, n=int(sel.sum()), share=e2, ci95=c2))
            cov[name] = row
        r["coverage_of_observed_retention"] = cov
        # nominal reference for the +-k SD columns under a Gaussian predictive law is deliberately NOT given: the spread is not a predictive law.
        # spread against error
        sd_m, sd_ci = cluster_ratio_ci(sd, np.ones(n), ci, "E3|%s|%s|meanSD" % (g, arm))
        ae_m, ae_ci = cluster_ratio_ci(ae, np.ones(n), ci, "E3|%s|%s|meanAE" % (g, arm))
        ratio, ratio_ci = cluster_ratio_ci(sd, ae, ci, "E3|%s|%s|SDoverAE" % (g, arm))
        r["mean_seed_sd_pp"] = dict(value=sd_m, ci95=sd_ci)
        r["mean_abs_error_of_ensemble_pp"] = dict(value=ae_m, ci95=ae_ci)
        r["mean_seed_sd_over_mean_abs_error"] = dict(value=ratio, ci95=ratio_ci)
        r["mean_envelope_half_width_pp"] = float(((hi_ - lo_) / 2).mean())
        # spread-skill: point level
        rho_pt = float(sps.spearmanr(sd, ae)[0])
        rng = mc_rng("E3|%s|%s|spearman_point" % (g, arm))
        groups = [np.where(ci == c)[0] for c in range(40)]
        bs = []
        for _ in range(B_POINT_SPEARMAN):
            pick = rng.integers(0, 40, 40)
            ix = np.concatenate([groups[c] for c in pick])
            bs.append(sps.spearmanr(sd[ix], ae[ix])[0])
        bs = np.array(bs)
        r["spread_skill"] = dict(spearman_point_level=dict(rho=rho_pt, ci95=[float(np.nanquantile(bs, .025)), float(np.nanquantile(bs, .975))], note="seed SD against absolute error of the ensemble mean; ranks the errors, no coverage claim"))
        # condition level: mean seed SD against condition RMSE (frozen definition: mean over cells of cell RMSE)
        P2 = P.assign(sd=sd, e2=(ens - y) ** 2)
        cellg = P2.groupby(["cond", "cell_id"]).agg(sd=("sd", "mean"), mse=("e2", "mean")).reset_index()
        cellg["rmse"] = np.sqrt(cellg.mse)
        cond_df = cellg.groupby("cond").agg(sd=("sd", "mean"), rmse=("rmse", "mean"))
        rho_c = float(sps.spearmanr(cond_df.sd, cond_df.rmse)[0])
        rng = mc_rng("E3|%s|%s|spearman_cond" % (g, arm))
        bc = np.array([sps.spearmanr(cond_df.sd.values[i], cond_df.rmse.values[i])[0] for i in (rng.integers(0, 40, 40) for _ in range(B_BOOT))])
        r["spread_skill"]["spearman_condition_level"] = dict(n=40, rho=rho_c, ci95=[float(np.nanquantile(bc, .025)), float(np.nanquantile(bc, .975))])
        # mean absolute error within quintiles of seed SD
        qc = np.quantile(sd, [.2, .4, .6, .8])
        qi = np.digitize(sd, qc)
        r["spread_skill"]["mean_abs_error_by_seed_sd_quintile"] = [dict(quintile=q + 1, n=int((qi == q).sum()), seed_sd_range_pp=[float(sd[qi == q].min()), float(sd[qi == q].max())], mean_abs_error_pp=float(ae[qi == q].mean()),
                                                                     mean_seed_sd_pp=float(sd[qi == q].mean())) for q in range(5)]
        # rank histogram: rank of the observation among the five seed forecasts (0..5 forecasts below it)
        rk = (S < y[:, None]).sum(1)
        hist = []
        for k in range(6):
            est, ciw = cluster_ratio_ci((rk == k).astype(float), np.ones(n), ci, "E3|%s|%s|rank%d" % (g, arm, k))
            hist.append(dict(n_forecasts_below_observation=k, count=int((rk == k).sum()), share=est, ci95=ciw))
        r["rank_histogram"] = dict(bins=hist, uniform_reference_share=1 / 6, note="a flat histogram is not claimed or tested; shown as description")
        # one training-side band: the five-seed min-max envelope (optimisation spread)
        r["training_side_band"] = dict(definition="min and max of the five seed forecasts at each check-up (optimisation spread)",
                                       mean_full_width_pp=float((hi_ - lo_).mean()), median_full_width_pp=float(np.median(hi_ - lo_)), share_of_points_with_observation_inside=cov["seed_min_max_envelope"]["share"],
                                       share_ci95=cov["seed_min_max_envelope"]["ci95"], label="optimisation spread, not predictive uncertainty")
        # observed-error quantiles (descriptive; not an interval; no recalibration)
        qs = (0.5, 0.8, 0.9, 0.95)
        r["observed_abs_error_quantiles_pp"] = {"overall": {str(q): float(np.quantile(ae, q)) for q in qs},
                                                 "by_horizon_index_tertile": [{str(q): float(np.quantile(ae[ter == t], q)) for q in qs} for t in range(3)],
                                                 "condition_rmse": {str(q): float(np.quantile(cond_df.rmse.values, q)) for q in qs},
                                                 "label": "observed on these 40 conditions; not a predictive interval; no coverage guarantee for new conditions"}
        res["cells"][g][arm] = r
        print(g, arm, "n", n, "env cover", round(cov["seed_min_max_envelope"]["share"], 3), "sd/ae", round(ratio, 3), "spearman", round(rho_pt, 3), "ens check", D["ens_check"])
jdump(res, "e3_descriptive.json")
