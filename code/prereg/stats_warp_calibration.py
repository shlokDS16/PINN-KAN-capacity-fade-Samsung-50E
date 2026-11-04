"""Statistician support run (STATS_RULING.md, items 1, 2 and 7). TRAINING SIDES ONLY, ISU and SNL pilots.

For each P3 outer Test-B fold the outer test cells are dropped from the frame before anything else (same
enforcement as p3_headroom.py). On the remaining training cells it computes, per condition:
  - LOO replicate floor (the P3 definition),
  - WARP: window-aware replicate predictor (other replicates' mean loss trajectory, scaled (mult) or shifted (add)
    to the held-out cell's own window; no label after the window of the held-out cell is used),
  - inner-CV (3 folds by condition, P3 partitions) errors of two FIXED-parameter learners (power law, LightGBM)
    used only to calibrate the paired spread of condition-level differences between learners.
No outer test fold is read, predicted or scored. No Samsung file is opened.

Usage: python -P stats_warp_calibration.py <ROOT>
"""
import os, sys, json
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np, pandas as pd

ROOT = sys.argv[1]
sys.path.insert(0, f"{ROOT}/code/pilots")
import p3_headroom as P3           # project code (not a download)

LGB_P = dict(n_est=200, lr=0.05, leaves=8, mcs=20, sub=0.8, col=0.8, l2=1.0, mono=False, tau_log=True)
PL_P = dict(blo=0.3, bhi=1.2)


def warp_one(cells, j, others, mode):
    """Predicted retention at cell j's forecast times from the other replicates, adjusted to j's window."""
    cj = cells[j]
    tw, rw = cj["tw"][1:], cj["rw"][1:]                      # window points after the reference check-up
    def mloss(t):
        v = [1.0 - np.interp(t, cells[k]["full_t"], cells[k]["full_r"]) for k in others if cells[k]["full_t"][-1] >= t]
        return np.mean(v) if v else np.nan
    mw = np.array([mloss(t) for t in tw])
    lw = 1.0 - rw
    ok = ~np.isnan(mw)
    if mode == "mult":
        den = float(np.sum(mw[ok] ** 2))
        k = float(np.clip(np.sum(lw[ok] * mw[ok]) / den, 0.25, 4.0)) if den > 1e-12 else 1.0
        adj = lambda m: k * m
    else:
        off = (lw[ok][-1] - mw[ok][-1]) if ok.any() else 0.0
        adj = lambda m: np.clip(m + off, 0.0, None)
    preds, idx = [], []
    for i, t in enumerate(cj["tf"]):
        m = mloss(t)
        if not np.isnan(m):
            preds.append(1.0 - adj(m)); idx.append(i)
    return np.array(preds), np.array(idx, dtype=int)


def floors(cells, mode):
    byc = {}
    for c, v in cells.items():
        byc.setdefault(v["cond"], []).append(c)
    rows = []
    for cond, cs in byc.items():
        if len(cs) < 2:
            continue
        for j in cs:
            others = [k for k in cs if k != j]
            if mode == "loo":
                tf = cells[j]["tf"]; preds, ok = [], []
                for i, t in enumerate(tf):
                    vals = [np.interp(t, cells[k]["full_t"], cells[k]["full_r"]) for k in others if cells[k]["full_t"][-1] >= t]
                    if vals:
                        preds.append(np.mean(vals)); ok.append(i)
                preds, ok = np.array(preds), np.array(ok, dtype=int)
            else:
                preds, ok = warp_one(cells, j, others, mode)
            if len(ok) == 0:
                continue
            rows.append(dict(cell=j, cond=cond, rmse=P3.cell_rmse_pp(preds, cells[j]["rf"][ok])))
    tab = pd.DataFrame(rows)
    return tab.groupby("cond").rmse.mean()


def run(ds, W):
    split = json.load(open(f"{ROOT}/runs/splits/{ds}_testB.json"))
    res3 = json.load(open(f"{ROOT}/runs/pilot_P3/{ds}_W{int(W)}/results.json"))
    full = (P3.load_isu if ds == "isu" else P3.load_snl)(ROOT, W)
    strata = None
    if ds == "snl":
        strata = dict(zip(full.cond, full.cond.str.split("|").str[0]))
    out = dict(folds={}, cond={})
    cond_pc = {}
    for f in sorted(split["folds"], key=int):
        test_cells = set(split["folds"][f]["test_cells"])
        train = full[~full.cell.isin(test_cells)].copy()                      # ENFORCEMENT
        assert not (set(train.cell) & test_cells)
        cells, _ = P3.build_cells(train, ds, W)
        assert not (set(cells) & test_cells)
        names = sorted(cells)
        conds = sorted(set(cells[c]["cond"] for c in names), key=str)
        folds1 = P3.inner_folds(conds, 1 * 1000 + int(f), strata)
        fl = {m: floors(cells, m) for m in ("loo", "mult", "add")}
        multi = set(fl["loo"].index)
        # fixed-parameter learners, inner CV on the training side only
        e = {}
        for kind, p in (("pl", PL_P), ("lgb", LGB_P)):
            _, tab = P3.oof_error(cells, names, folds1, kind, p, ds, 1, None)
            e[kind] = tab.groupby("cond").rmse.mean()
        best_e = res3["folds"][f]["learners"][res3["folds"][f]["best_flexible"]]["inner_cv"]   # tuned, from P3 results
        row = dict(n_multi=len(multi),
                   loo_median=float(fl["loo"].median()), loo_mean=float(fl["loo"].mean()),
                   warp_mult_median=float(fl["mult"].median()), warp_mult_mean=float(fl["mult"].mean()),
                   warp_add_median=float(fl["add"].median()), warp_add_mean=float(fl["add"].mean()),
                   p3_best_tuned_inner_cv=float(best_e), p3_loo_median=float(res3["folds"][f]["floor"]["floor_median"]),
                   fixed_pl_mean=float(e["pl"].mean()), fixed_lgb_mean=float(e["lgb"].mean()))
        row["ratio_best_over_loo_median"] = best_e / row["loo_median"]
        row["ratio_best_over_warp_mult_median"] = best_e / row["warp_mult_median"]
        row["ratio_best_over_warp_add_median"] = best_e / row["warp_add_median"]
        out["folds"][f] = row
        for c in conds:
            d = cond_pc.setdefault(c, dict(loo=[], mult=[], add=[], pl=[], lgb=[]))
            if c in fl["loo"].index:
                for m in ("loo", "mult", "add"):
                    d[m].append(float(fl[m][c]))
            for kind in ("pl", "lgb"):
                if c in e[kind].index:
                    d[kind].append(float(e[kind][c]))
        print(ds, W, f, {k: round(v, 3) for k, v in row.items() if isinstance(v, float)}, flush=True)
    df = pd.DataFrame({c: {k: (np.mean(v) if v else np.nan) for k, v in d.items()} for c, d in cond_pc.items()}).T
    df.index.name = "cond"
    df.to_csv(f"{ROOT}/runs/prereg/stats_ruling/cond_{ds}_W{int(W)}.csv")
    m = df.dropna()
    summ = dict(n_conditions_all=int(len(df)), n_conditions_multi=int(len(m)),
                mean_over_folds={k: float(np.mean([out["folds"][f][k] for f in out["folds"]]))
                                 for k in out["folds"]["0"] if isinstance(out["folds"]["0"][k], float)})
    d_pl_lgb = m.pl - m.lgb
    summ["paired"] = dict(
        mean_err_pl=float(m.pl.mean()), mean_err_lgb=float(m.lgb.mean()), sd_err_lgb=float(m.lgb.std(ddof=1)),
        cv_err_lgb=float(m.lgb.std(ddof=1) / m.lgb.mean()),
        corr_pl_lgb=float(np.corrcoef(m.pl, m.lgb)[0, 1]),
        mean_d_pl_minus_lgb=float(d_pl_lgb.mean()), sd_d_pl_minus_lgb=float(d_pl_lgb.std(ddof=1)),
        skew_d=float(((d_pl_lgb - d_pl_lgb.mean()) ** 3).mean() / d_pl_lgb.std(ddof=0) ** 3),
        excess_kurt_d=float(((d_pl_lgb - d_pl_lgb.mean()) ** 4).mean() / d_pl_lgb.std(ddof=0) ** 4 - 3),
        median_warp_mult=float(m.mult.median()), median_warp_add=float(m["add"].median()), median_loo=float(m.loo.median()),
        sd_d_over_median_warp_mult=float(d_pl_lgb.std(ddof=1) / m.mult.median()),
        sd_d_over_median_warp_add=float(d_pl_lgb.std(ddof=1) / m["add"].median()),
        sd_d_over_median_loo=float(d_pl_lgb.std(ddof=1) / m.loo.median()),
        sd_err_lgb_over_median_warp_mult=float(m.lgb.std(ddof=1) / m.mult.median()),
        corr_lgb_warpmult=float(np.corrcoef(m.lgb, m.mult)[0, 1]), corr_lgb_loo=float(np.corrcoef(m.lgb, m.loo)[0, 1]))
    out["summary"] = summ
    out["audit"] = dict(test_cells_read=False, note="training frames only, per outer fold")
    os.makedirs(f"{ROOT}/runs/prereg/stats_ruling", exist_ok=True)
    json.dump(out, open(f"{ROOT}/runs/prereg/stats_ruling/warp_{ds}_W{int(W)}.json", "w"), indent=1)
    return out


if __name__ == "__main__":
    os.makedirs(f"{ROOT}/runs/prereg/stats_ruling", exist_ok=True)
    for ds, W in (("isu", 4), ("snl", 100)):
        r = run(ds, W)
        print(json.dumps(r["summary"], indent=1))
