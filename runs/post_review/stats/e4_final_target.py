"""E4 / Q4: error at the final forecast check-up of each held-out cell, by arm, at g1 (m = 8, k = 2) and g4 (m = 32, k = full), from the stored ensemble predictions.
No refit. POST-HOC, EXPLORATORY. Unit: the held-out condition (n = 40). d = e_A1 - e_comparator in percentage points (negative: A1 lower error than the comparator).
The 388-day sensitivity row is printed beside, never in place of, the unaltered result."""
import sys
sys.path.insert(0, r"C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\post_review\stats")
import numpy as np
from scipy import stats as sps
from common import *

gt, gt_sha = load_frozen_graph_test()
ARMS_ALL = ["A1", "A9", "A10", "A10P", "A11", "A12", "A2", "A4", "A5", "A13", "A15", "G15", "R1", "R2"]
COMPS = ["D*", "A9", "A10", "A10P", "R1"]      # D*, A9 (law's contribution), A10 and its second form A10P (dataset authors' refit), R1 persistence


def cell_table(g):
    """per (fold, arm, cell): arrays of t, error pp; plus window end. Returns DataFrame rows per cell and arm."""
    m, ph = G[g]["m"], G[g]["phase"]
    rows, hz, pooled = [], [], {}
    dstar = {}
    for f in FOLDS:
        d = load_pred(f, m)
        comp = jload(os.path.join(RUNS, "conf_samsung_B_f%d_m%d" % (f, m), "comparators.json"))
        dstar[f] = comp["D*"]["arm"]
        win = pd.read_csv(os.path.join(RUNS, "conf_samsung_B_f%d_m%d" % (f, m), "window.csv"))
        wlast = win.groupby("cell_id").t.max().to_dict()
        k0 = d[(d.phase == "outer_test_k0") & (d.arm == "A1") & (d.seed == "ens")]
        x = d[(d.phase == ph) & (d.seed == "ens")]
        base = x[x.arm == "A1"].sort_values(["cell_id", "t"])
        ref_t = {c: g_.t.values for c, g_ in base.groupby("cell_id")}
        for arm, a in x.groupby("arm"):
            for cid, ca in a.groupby("cell_id"):
                ca = ca.sort_values("t")
                if not np.array_equal(ca.t.values, ref_t[cid]):
                    raise SystemExit("forecast set differs between arms: %s %s %s" % (f, arm, cid))
                e = np.abs(ca.pred_retention.values - ca.true_retention.values) * 100.0
                t = ca.t.values
                kk = k0[k0.cell_id == cid].t.values
                before = kk[kk < t[0]]
                if len(before):
                    wend, src = float(before.max()), "k0_forecast_row"
                else:
                    wend, src = float(wlast[cid]), "window_csv_fallback"
                rows.append(dict(fold=f, arm=arm, cell=cid, cond=ca.cond.iloc[0], n_fc=len(t), final_err=float(e[-1]), last3_rmse=float(np.sqrt(np.mean(e[-3:] ** 2))),
                                 rmse_all=float(np.sqrt(np.mean(e ** 2))), t_final=float(t[-1]), t_first=float(t[0]), wend=wend, wsrc=src,
                                 h_final_days=float(t[-1] - wend), h_first_days=float(t[0] - wend)))
                if arm == "A1":
                    for i, ee in enumerate(e):
                        pooled.setdefault(i + 1, []).append(ee)
    return pd.DataFrame(rows), dstar, {h: dict(rmse_pp=float(np.sqrt(np.mean(np.square(v)))), n=len(v)) for h, v in pooled.items()}


def validate(g, T, dstar):
    """condition mean of cell RMSE (ensemble) against the stored condition_scores json, every arm present in both"""
    out = {}
    for f in FOLDS:
        cs = jload(os.path.join(RUNS, "conf_samsung_B_f%d_m%d" % (f, G[g]["m"]), G[g]["scores"]))
        for arm, scs in cs.items():
            s = T[(T.fold == f) & (T.arm == arm)].groupby("cond").rmse_all.mean()
            if len(s) == 0:
                continue
            md = max(abs(s[c] - v) for c, v in scs.items())
            out[(arm, f)] = float(md)
    return out


def cond_vals(T, arm_by_fold, col):
    """condition value = mean over the condition's cells of col; arm_by_fold: dict fold -> arm"""
    parts = []
    for f, a in arm_by_fold.items():
        s = T[(T.fold == f) & (T.arm == a)].groupby("cond")[col].mean()
        parts.append(s)
    return pd.concat(parts).sort_index()


def stat_block(d, label, B=B_BOOT):
    d = np.asarray(d, float)
    lo, hi, r, cov = gt.order_stat_interval(d, 0.05)
    mlo, mhi = bca(d, np.mean, label + "|BCa_mean", B)
    dlo, dhi = bca(d, np.median, label + "|BCa_median", B)
    return dict(n=int(d.size), median=float(np.median(d)), median_order_stat_ci95=[lo, hi], order_stat_rank=int(r), order_stat_coverage=cov,
                median_bca_ci95=[dlo, dhi], mean=float(d.mean()), mean_bca_ci95=[mlo, mhi],
                n_A1_lower=int((d < 0).sum()), n_A1_higher=int((d > 0).sum()), n_equal=int((d == 0).sum()))


res = {"note": "POST-HOC, EXPLORATORY (D048). d = A1 final-check-up error minus comparator error, in percentage points; negative = A1 lower. Unit: held-out condition. No tier, no p-value.",
       "frozen_graph_test_sha256": gt_sha, "bootstrap_B": B_BOOT, "seed_rule": "SeedSequence([20261105, crc32(label)])", "cells": {}}
for g in ("g1", "g4"):
    T, dstar, hpool = cell_table(g)
    val = validate(g, T, dstar)
    gres = {"D_star_arm_by_fold": dstar, "validation_max_abs_diff_condition_score_pp": {"%s|fold%d" % k: v for k, v in val.items()},
            "validation_ok": bool(max(val.values()) < 1e-9),
            "table_D1_check_A1_pooled_rmse_by_forecast_index": {str(h): hpool[h] for h in sorted(hpool)[:3]}}
    if not gres["validation_ok"]:
        gres["validation_FAILED"] = True
    T.to_csv(os.path.join(OUT, "e4_cell_level_%s.csv" % g), index=False)
    gres["n_cells_per_arm"] = int(T[T.arm == "A1"].shape[0])
    gres["window_end_source_counts"] = T[T.arm == "A1"].wsrc.value_counts().to_dict()
    # 388-day gap
    A = T[T.arm == "A1"]
    gap = A[A.h_first_days >= 380]
    gres["first_check_up_gap_ge_380_days"] = [dict(cell=r.cell, cond=r.cond, fold=int(r.fold), h_first_days=r.h_first_days, h_final_days=r.h_final_days) for r in gap.itertuples()]
    drop_conds = sorted(set(gap.cond))
    # condition values by arm; D* by fold
    amap = {a: {f: a for f in FOLDS} for a in ARMS_ALL if (T.arm == a).any()}
    amap["D*"] = dict(dstar)
    amap["D*"] = {int(k): v for k, v in dstar.items()}
    fe = {a: cond_vals(T, am, "final_err") for a, am in amap.items() if all((T[(T.fold == f) & (T.arm == am[f])].shape[0] > 0) for f in FOLDS)}
    l3 = {a: cond_vals(T, am, "last3_rmse") for a, am in amap.items() if a in fe}
    hdays = cond_vals(T, {f: "A1" for f in FOLDS}, "h_final_days")
    conds = fe["A1"].index
    for a in fe:
        assert (fe[a].index == conds).all(), a
    assert len(conds) == 40
    # descriptive by arm
    gres["by_arm_final_error_pp"] = {a: dict(median=float(v.median()), mean=float(v.mean()), arm_by_fold=amap[a] if a == "D*" else None) for a, v in fe.items()}
    gres["by_arm_last3_rmse_pp"] = {a: dict(median=float(v.median()), mean=float(v.mean())) for a, v in l3.items()}
    gres["condition_final_horizon_days"] = dict(median=float(hdays.median()), min=float(hdays.min()), max=float(hdays.max()))
    # paired differences
    cuts = np.quantile(hdays.values, [1 / 3, 2 / 3])
    tert = np.where(hdays.values <= cuts[0], 0, np.where(hdays.values <= cuts[1], 1, 2))
    gres["tertile_cut_points_days"] = [float(cuts[0]), float(cuts[1])]
    gres["tertile_sizes"] = [int((tert == i).sum()) for i in range(3)]
    gres["comparators"] = {}
    for comp in COMPS:
        if comp not in fe:
            gres["comparators"][comp] = {"available": False}
            continue
        d = (fe["A1"] - fe[comp]).values
        cres = {"available": True, "unaltered_final_target": stat_block(d, "E4|%s|%s|all" % (g, comp)),
                "median_comparator_pp": float(fe[comp].median()), "median_A1_pp": float(fe["A1"].median())}
        # last-three-check-up stability row: condition RMSE, paired log ratio as in the endpoint
        L = np.log(l3[comp].values / l3["A1"].values)
        lo, hi, r, cov = gt.order_stat_interval(L, 0.05)
        cres["last3_rmse_log_ratio"] = dict(n=40, median_L=float(np.median(L)), median_order_stat_ci95=[lo, hi], n_positive=int((L > 0).sum()),
                                           note="L = ln(S_comparator / S_A1) on the condition RMSE over the last three check-ups; positive favours A1")
        # sensitivity: drop the condition containing the 388-day cell (n = 39), and drop the cell only
        keep = ~conds.isin(drop_conds)
        if (~keep).any():
            cres["sensitivity_drop_condition_388d"] = stat_block(d[keep], "E4|%s|%s|dropcond" % (g, comp))
            Tc = T[~T.cell.isin(list(gap.cell))]
            fe2 = {a: cond_vals(Tc, amap[a], "final_err") for a in ("A1", comp)}
            dd = (fe2["A1"] - fe2[comp]).values
            cres["sensitivity_drop_cell_388d"] = stat_block(dd, "E4|%s|%s|dropcell" % (g, comp))
        # tertiles of final horizon in days
        tt = []
        for i in range(3):
            sel = tert == i
            if sel.sum() >= 3:
                lo, hi, r, cov = gt.order_stat_interval(d[sel], 0.05)
                mlo, mhi = bca(d[sel], np.mean, "E4|%s|%s|tert%d|BCa_mean" % (g, comp, i))
                tt.append(dict(tertile=i + 1, n=int(sel.sum()), horizon_days_range=[float(hdays.values[sel].min()), float(hdays.values[sel].max())],
                               median=float(np.median(d[sel])), median_order_stat_ci95=[lo, hi], mean=float(d[sel].mean()), mean_bca_ci95=[mlo, mhi],
                               n_A1_lower=int((d[sel] < 0).sum())))
        cres["horizon_tertiles"] = tt
        rho, pv = sps.spearmanr(d, hdays.values)
        rng = mc_rng("E4|%s|%s|spearman" % (g, comp))
        idx = rng.integers(0, 40, (B_BOOT, 40))
        bs = np.array([sps.spearmanr(d[i], hdays.values[i])[0] for i in idx])
        bs = bs[np.isfinite(bs)]
        cres["spearman_d_vs_final_horizon_days"] = dict(rho=float(rho), ci95_percentile_condition_bootstrap=[float(np.quantile(bs, .025)), float(np.quantile(bs, .975))], n_finite_resamples=int(bs.size),
                                                       note="description only; the final check-up falls at different calendar times in different conditions")
        gres["comparators"][comp] = cres
    # reconciliation with the frozen endpoint: median log ratio of condition RMSE over ALL forecast check-ups, A1 against D*
    cs_all = {a: cond_vals(T, amap[a], "rmse_all") for a in ("A1", "D*", "R1") if a in amap}
    Lr = np.log(cs_all["D*"].values / cs_all["A1"].values)
    gres["reconcile_frozen_endpoint_A1_vs_Dstar"] = dict(median_L=float(np.median(Lr)), n_positive=int((Lr > 0).sum()), n=40,
                                                         mean_condition_score_A1_pp=float(cs_all["A1"].mean()), mean_condition_score_Dstar_pp=float(cs_all["D*"].mean()))
    res["cells"][g] = gres
    print(g, "validation", gres["validation_ok"], "max", max(val.values()), "| 388d:", gres["first_check_up_gap_ge_380_days"], "| Table D.1 h=1:", gres["table_D1_check_A1_pooled_rmse_by_forecast_index"]["1"])
jdump(res, "e4_final_target.json")
