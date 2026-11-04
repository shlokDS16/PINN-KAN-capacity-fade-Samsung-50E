"""Pilot P3: headroom on TRAINING folds only (D010 judge, sections 6 and 7).

For every outer Test-B fold (runs/splits/<ds>_testB.json) the outer TEST conditions are removed from the data
frame before anything else happens; all later steps see only the training frame. Inside it, grouped CV by
condition is used for: replicate floor, tuned GP-ARD, tuned LightGBM, tuned per-cell power law, persistence.
No outer fold is ever predicted or scored; no model is refit on the full training set (not needed for the
inner-CV verdict).

Usage: python -P p3_headroom.py <ROOT> <isu|snl> <window> [n_trials] [seed]
"""
import os
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "2")
import sys, json, time, hashlib, subprocess, warnings
import numpy as np, pandas as pd
import optuna, lightgbm as lgb
import scipy.optimize
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel as C, Matern, RBF, WhiteKernel

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

N_INNER = 3
LIFE_LEVEL = 0.70          # forecast set ends at (and includes) the first check-up below 70 % retention
STRESS = {"isu": ["charge_c", "discharge_c", "dod_pct"],
          "snl": ["is_LFP", "is_NCA", "is_NMC", "temp_c", "dod", "charge_c", "discharge_c"]}
TAU_UNIT = {"isu": 1.0, "snl": 25.0}     # one check-up step: ~1 week (ISU), 25 cycles (SNL grid)
SNL_GRID = 25


# ------------------------------------------------------------------ data
def load_isu(root, W):
    cap = pd.read_csv(f"{root}/data/processed/isu_capacity.csv")
    cond = pd.read_csv(f"{root}/data/processed/isu_conditions.csv")
    cap = cap.merge(cond, on="group")
    cap["cond"] = cap.group.astype(int)
    cap = cap.rename(columns={"week": "t", "retention": "r"})
    return cap[["cell", "cond", "t", "r", "charge_c", "discharge_c", "dod_pct"]]


def load_snl(root, W):
    cells = pd.read_csv(f"{root}/data/processed/snl_cells.csv")
    cells["cond"] = (cells.chemistry + "|" + cells.temp_c.astype(str) + "C|" + cells.soc_window + "|ch"
                     + cells.charge_c.astype(str) + "|dis" + cells.discharge_c.astype(str))
    cy = pd.read_csv(f"{root}/data/processed/snl_cycles.csv", usecols=["cell", "cycle", "q_dis_ah"])
    cy = cy[cy.q_dis_ah > 0.05]                                    # drop invalid records (P1 caveat)
    first = cy[cy.cycle == 1].set_index("cell").q_dis_ah
    cy = cy[(cy.cycle - 1) % SNL_GRID == 0].copy()                 # check-up grid: cycles 1, 26, 51, ...
    cy["r"] = cy.q_dis_ah / cy.cell.map(first)
    cy = cy.rename(columns={"cycle": "t"}).merge(cells, on="cell")
    for ch in ("LFP", "NCA", "NMC"):
        cy[f"is_{ch}"] = (cy.chemistry == ch).astype(float)
    cy["dod"] = np.where(cy.soc_window == "0-100", 1.0, 0.6)
    return cy[["cell", "cond", "t", "r"] + STRESS["snl"]]


def build_cells(df, ds, W):
    """One dict per eligible cell: window summary, forecast times/values, static features."""
    out, excluded = {}, []
    for cell, d in df.groupby("cell", sort=True):
        d = d.sort_values("t")
        t, r = d.t.values.astype(float), d.r.values.astype(float)
        below = np.where(r < LIFE_LEVEL)[0]
        last_idx = below[0] if len(below) else len(r) - 1
        win = t <= W + 1e-9
        fc = np.array([(not win[i]) and i <= last_idx for i in range(len(r))])
        if fc.sum() == 0 or win.sum() < 3:
            excluded.append(cell)
            continue
        tw, rw = t[win], r[win]
        slope = np.polyfit(tw, rw, 1)[0]
        h = len(tw) // 2
        s1 = np.polyfit(tw[: h + 1], rw[: h + 1], 1)[0] if h >= 1 else slope
        s2 = np.polyfit(tw[h:], rw[h:], 1)[0] if len(tw) - h >= 2 else slope
        out[cell] = dict(cond=d.cond.iloc[0], tw=tw, rw=rw, t_last=tw[-1], r_last=rw[-1],
                         summ=np.array([rw[-1], rw[1], slope * TAU_UNIT[ds], (s2 - s1) * TAU_UNIT[ds], tw[-1]]),
                         tf=t[fc], rf=r[fc],
                         stress=d[STRESS[ds]].iloc[0].values.astype(float), full_t=t, full_r=r)
    return out, excluded


# ------------------------------------------------------------------ metrics
def cell_rmse_pp(pred, truth):
    return 100.0 * float(np.sqrt(np.mean((pred - truth) ** 2)))


def condition_table(cells, preds):
    rows = [dict(cell=c, cond=cells[c]["cond"], rmse=cell_rmse_pp(preds[c], cells[c]["rf"])) for c in preds]
    return pd.DataFrame(rows)


def cond_avg(tab, conds=None):
    if conds is not None:
        tab = tab[tab.cond.isin(conds)]
    pc = tab.groupby("cond").rmse.mean()
    return float(pc.mean()), float(pc.median()), pc


# ------------------------------------------------------------------ replicate floor
def replicate_floor(cells):
    """Leave-one-replicate-out RMSE (pp) of the mean trajectory of the other replicates of the same condition,
    evaluated at the left-out cell's forecast times (linear interpolation in time; replicates that do not reach
    that time are skipped). Per condition: mean over its replicates; judge margin: median over conditions."""
    byc = {}
    for c, v in cells.items():
        byc.setdefault(v["cond"], []).append(c)
    rows = []
    for cond, cs in byc.items():
        if len(cs) < 2:
            continue
        for j in cs:
            others = [k for k in cs if k != j]
            tf = cells[j]["tf"]
            preds, ok = [], []
            for i, t in enumerate(tf):
                vals = [np.interp(t, cells[k]["full_t"], cells[k]["full_r"]) for k in others
                        if cells[k]["full_t"][-1] >= t]
                if vals:
                    preds.append(np.mean(vals)); ok.append(i)
            if not ok:
                continue
            ok = np.array(ok)
            rows.append(dict(cell=j, cond=cond, rmse=cell_rmse_pp(np.array(preds), cells[j]["rf"][ok])))
    tab = pd.DataFrame(rows)
    mean_, med_, pc = cond_avg(tab)
    return dict(floor_median=med_, floor_mean=mean_, n_conditions=int(len(pc))), pc


# ------------------------------------------------------------------ inner folds
def inner_folds(conds, seed, strata=None):
    rng = np.random.default_rng(seed)
    conds = sorted(conds, key=str)
    if strata is not None:
        order = []
        for s in sorted(set(strata[c] for c in conds)):
            g = [c for c in conds if strata[c] == s]
            rng.shuffle(g); order += g
    else:
        order = list(rng.permutation(conds))
    return {c: i % N_INNER for i, c in enumerate(order)}


# ------------------------------------------------------------------ learners
def feat_rows(cell, ds, tau_log, fs):
    tau = cell["tf"] - cell["t_last"]
    tt = np.log1p(tau / TAU_UNIT[ds]) if tau_log else tau / TAU_UNIT[ds]
    static = np.concatenate([cell["stress"], cell["summ"]])
    X = np.column_stack([np.tile(static, (len(tau), 1)), tt])
    if fs == "min":   # stress + r_last + window slope + tau
        k = len(cell["stress"])
        X = X[:, list(range(k)) + [k + 0, k + 2, X.shape[1] - 1]]
    return X


def stack(cells, names, ds, tau_log, fs, m=None, with_y=True):
    Xs, ys, ws, idx = [], [], [], []
    for c in names:
        X = feat_rows(cells[c], ds, tau_log, fs)
        y = cells[c]["r_last"] - cells[c]["rf"]
        sel = np.arange(len(y))
        if m is not None and len(y) > m:
            sel = np.unique(np.round(np.linspace(0, len(y) - 1, m)).astype(int))
        Xs.append(X[sel]); ys.append(y[sel]); ws.append(np.full(len(sel), 1.0 / len(sel))); idx.append(c)
    return np.vstack(Xs), np.concatenate(ys), np.concatenate(ws)


def predict_cells(cells, names, ds, predfun, tau_log, fs):
    out = {}
    for c in names:
        drop = predfun(feat_rows(cells[c], ds, tau_log, fs))
        out[c] = np.clip(cells[c]["r_last"] - drop, 0.0, 1.1)
    return out


def fit_gp(cells, tr, p, ds, seed):
    X, y, _ = stack(cells, tr, ds, p["tau_log"], p["fs"], m=p["m"])
    mu, sd = X.mean(0), X.std(0); sd[sd < 1e-9] = 1.0
    d = X.shape[1]
    base = (Matern(length_scale=np.ones(d), length_scale_bounds=(1e-2, 1e3), nu=p["nu"]) if p["nu"] > 0
            else RBF(length_scale=np.ones(d), length_scale_bounds=(1e-2, 1e3)))
    k = C(1.0, (1e-2, 1e2)) * base + WhiteKernel(1e-2, (p["noise_lo"], 1.0))

    def opt(obj, th0, bounds):
        r = scipy.optimize.minimize(obj, th0, method="L-BFGS-B", jac=True, bounds=bounds, options={"maxiter": 60})
        return r.x, r.fun

    gp = GaussianProcessRegressor(k, normalize_y=True, optimizer=opt, n_restarts_optimizer=0, random_state=seed)
    gp.fit((X - mu) / sd, y)
    return lambda Xn: gp.predict((Xn - mu) / sd)


def fit_lgb(cells, tr, p, ds, seed):
    X, y, w = stack(cells, tr, ds, p["tau_log"], "full")
    mono = [0] * X.shape[1]
    if p["mono"]:
        mono[-1] = 1
    mdl = lgb.LGBMRegressor(n_estimators=p["n_est"], learning_rate=p["lr"], num_leaves=p["leaves"],
                            min_child_samples=p["mcs"], subsample=p["sub"], subsample_freq=1,
                            colsample_bytree=p["col"], reg_lambda=p["l2"], monotone_constraints=mono,
                            n_jobs=1, random_state=seed, deterministic=True, force_row_wise=True, verbose=-1)
    mdl.fit(X, y, sample_weight=w * len(w) / w.sum())
    return mdl.predict


def powerlaw_predict(cell, blo, bhi):
    """r(t) = 1 - a t^b, b in [blo, bhi] on a 41-point geometric grid, a>=0 closed form; fitted to the window
    (t>0) and extrapolated to the forecast times."""
    tw, rw = cell["tw"][1:], cell["rw"][1:]
    y = np.clip(1.0 - rw, 0.0, None)
    bs = np.geomspace(blo, bhi, 41)
    best = None
    for b in bs:
        x = tw ** b
        a = max(float(x @ y / (x @ x)), 0.0)
        e = float(np.sum((a * x - y) ** 2))
        if best is None or e < best[0]:
            best = (e, a, b)
    _, a, b = best
    return np.clip(1.0 - a * cell["tf"] ** b, 0.0, 1.1)


# ------------------------------------------------------------------ tuning
def oof_error(cells, names, folds, kind, p, ds, seed, evalset):
    preds = {}
    for k in range(N_INNER):
        tr = [c for c in names if folds[cells[c]["cond"]] != k]
        te = [c for c in names if folds[cells[c]["cond"]] == k]
        if not te or not tr:
            continue
        if kind == "gp":
            f = fit_gp(cells, tr, p, ds, seed); preds.update(predict_cells(cells, te, ds, f, p["tau_log"], p["fs"]))
        elif kind == "lgb":
            f = fit_lgb(cells, tr, p, ds, seed); preds.update(predict_cells(cells, te, ds, f, p["tau_log"], "full"))
        elif kind == "pl":
            for c in te:
                preds[c] = powerlaw_predict(cells[c], p["blo"], p["bhi"])
        elif kind == "persist":
            for c in te:
                preds[c] = np.full(len(cells[c]["rf"]), cells[c]["r_last"])
    tab = condition_table(cells, preds)
    return cond_avg(tab, evalset)[0], tab


def suggest(trial, kind):
    if kind == "gp":
        return dict(nu=trial.suggest_categorical("nu", [1.5, 2.5, -1.0]), m=trial.suggest_categorical("m", [3, 4, 6]),
                    tau_log=trial.suggest_categorical("tau_log", [False, True]),
                    fs=trial.suggest_categorical("fs", ["full", "min"]),
                    noise_lo=trial.suggest_float("noise_lo", 1e-6, 1e-2, log=True))
    if kind == "lgb":
        return dict(n_est=trial.suggest_int("n_est", 50, 600), lr=trial.suggest_float("lr", 0.01, 0.3, log=True),
                    leaves=trial.suggest_int("leaves", 4, 32), mcs=trial.suggest_int("mcs", 5, 60),
                    sub=trial.suggest_float("sub", 0.5, 1.0), col=trial.suggest_float("col", 0.5, 1.0),
                    l2=trial.suggest_float("l2", 1e-3, 10.0, log=True), mono=trial.suggest_categorical("mono", [False, True]),
                    tau_log=trial.suggest_categorical("tau_log", [False, True]))
    if kind == "pl":
        lo = trial.suggest_float("blo", 0.05, 1.0, log=True)
        hi = trial.suggest_float("bhi_over_lo", 1.0, 20.0, log=True)
        return dict(blo=lo, bhi=lo * hi if hi > 1.0001 else lo * 1.0001)
    return {}


def tune(cells, names, folds, folds2, kind, ds, n_trials, seed, evalset):
    t0 = time.time()
    if kind == "persist":
        e, tab = oof_error(cells, names, folds, kind, {}, ds, seed, evalset)
        return dict(best_params={}, inner_cv=e, inner_cv_repartition=oof_error(cells, names, folds2, kind, {}, ds, seed, evalset)[0], n_trials=0, seconds=time.time() - t0), tab
    def obj(trial):
        return oof_error(cells, names, folds, kind, suggest(trial, kind), ds, seed, None)[0]   # objective: all training conditions
    st = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=seed))
    st.optimize(obj, n_trials=n_trials, catch=(Exception,))
    bp = suggest(optuna.trial.FixedTrial(st.best_params), kind)
    e1, tab = oof_error(cells, names, folds, kind, bp, ds, seed, evalset)
    e2 = oof_error(cells, names, folds2, kind, bp, ds, seed, evalset)[0]
    return dict(best_params={k: (v if not isinstance(v, (np.floating, np.integer)) else float(v)) for k, v in bp.items()},
                inner_cv=e1, inner_cv_repartition=e2, n_trials=n_trials,
                n_failed=int(sum(t.state.name != "COMPLETE" for t in st.trials)), seconds=time.time() - t0), tab


# ------------------------------------------------------------------ main
def git_commit(root):
    try:
        return subprocess.check_output(["git", "-C", root, "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    root, ds, W = sys.argv[1], sys.argv[2], float(sys.argv[3])
    n_trials = int(sys.argv[4]) if len(sys.argv) > 4 else 20
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    outdir = f"{root}/runs/pilot_P3/{ds}_W{int(W)}"
    os.makedirs(outdir, exist_ok=True)
    split_path = f"{root}/runs/splits/{ds}_testB.json"
    split_sha0 = sha(split_path)
    split = json.load(open(split_path))
    full = (load_isu if ds == "isu" else load_snl)(root, W)
    strata = None
    if ds == "snl":
        strata = dict(zip(full.cond, full.cond.str.split("|").str[0]))
    res = {"folds": {}}
    used_cells, test_cells_all, fold_overlap = set(), set(), []
    cond_err = {}                                # condition -> list of best-learner OOF errors over folds
    cond_floor = {}
    for f in sorted(split["folds"], key=int):
        test_cells = set(split["folds"][f]["test_cells"]); test_cells_all |= test_cells
        # ---- ENFORCEMENT: outer test cells are dropped from the frame before anything else runs
        train = full[~full.cell.isin(test_cells)].copy()
        assert not (set(train.cell) & test_cells) and not (set(train.cond) & set(split["folds"][f]["test_conditions"]))
        cells, excluded = build_cells(train, ds, W)
        assert not (set(cells) & test_cells)
        used_cells |= set(cells)
        fold_overlap += sorted(set(cells) & test_cells)
        names = sorted(cells)
        conds = sorted(set(cells[c]["cond"] for c in names), key=str)
        folds1 = inner_folds(conds, seed * 1000 + int(f), strata)
        folds2 = inner_folds(conds, seed * 1000 + 500 + int(f), strata)
        floor, floor_pc = replicate_floor(cells)
        multi = set(floor_pc.index)
        out = dict(n_train_conditions=len(conds), n_train_cells_eligible=len(names), excluded_train_cells=excluded,
                   n_multi_replicate_conditions=len(multi), floor=floor, learners={})
        for kind in ["persist", "pl", "lgb", "gp"]:
            r, tab = tune(cells, names, folds1, folds2, kind, ds, n_trials, seed * 7 + int(f), multi)
            _, _, pc_all = cond_avg(tab)
            r["inner_cv_all_conditions_mean"] = float(pc_all.mean())
            r["inner_cv_multi_median"] = float(cond_avg(tab, multi)[1])
            out["learners"][kind] = r
            r["_pc"] = pc_all
            print(f"[{ds} W={W}] fold {f} {kind}: inner-CV {r['inner_cv']:.3f} pp (floor median {floor['floor_median']:.3f}, mean {floor['floor_mean']:.3f}) {r['seconds']:.0f}s", flush=True)
        flex = {k: out["learners"][k]["inner_cv"] for k in ("gp", "lgb")}
        best = min(flex, key=flex.get)
        out["best_flexible"] = best
        out["ratio_best_over_floor_median"] = flex[best] / floor["floor_median"]
        out["ratio_best_over_floor_mean"] = flex[best] / floor["floor_mean"]
        out["ratio_best_repartition_over_floor_median"] = out["learners"][best]["inner_cv_repartition"] / floor["floor_median"]
        for c, v in out["learners"][best]["_pc"].items():
            cond_err.setdefault(c, []).append(float(v))
        for c, v in floor_pc.items():
            cond_floor[c] = float(v)
        for k in out["learners"]:
            out["learners"][k].pop("_pc")
        res["folds"][f] = out
    # ---- audit: the outer test cells were never part of any frame used
    assert not fold_overlap, fold_overlap          # per-fold check done in the loop
    assert sha(split_path) == split_sha0
    # ---- pooled verdict
    F = res["folds"]
    fl_med = np.array([F[f]["floor"]["floor_median"] for f in F]); fl_mean = np.array([F[f]["floor"]["floor_mean"] for f in F])
    best_e = np.array([F[f]["learners"][F[f]["best_flexible"]]["inner_cv"] for f in F])
    best_e2 = np.array([F[f]["learners"][F[f]["best_flexible"]]["inner_cv_repartition"] for f in F])
    summ = dict(ratio_primary=float(np.mean(best_e / fl_med)), ratio_like_for_like_mean=float(np.mean(best_e / fl_mean)),
                ratio_repartition=float(np.mean(best_e2 / fl_med)),
                per_fold_ratio=[float(x) for x in best_e / fl_med], min_fold_ratio=float((best_e / fl_med).min()),
                mean_best_error_pp=float(best_e.mean()), mean_floor_median_pp=float(fl_med.mean()), mean_floor_mean_pp=float(fl_mean.mean()))
    for k in ("persist", "pl", "gp", "lgb"):
        e = np.array([F[f]["learners"][k]["inner_cv"] for f in F])
        summ[f"mean_inner_cv_{k}_pp"] = float(e.mean()); summ[f"ratio_{k}"] = float(np.mean(e / fl_med))
    # cluster bootstrap by condition (conditions = units; floor per condition is training-set independent)
    cs = sorted(set(cond_err) & set(cond_floor), key=str)
    e_c = np.array([np.mean(cond_err[c]) for c in cs]); fl_c = np.array([cond_floor[c] for c in cs])
    rng = np.random.default_rng(12345)
    bs_j, bs_l = [], []
    for _ in range(10000):
        i = rng.integers(0, len(cs), len(cs))
        bs_j.append(e_c[i].mean() / np.median(fl_c[i])); bs_l.append(e_c[i].mean() / fl_c[i].mean())
    summ["pooled_condition_level"] = dict(n_conditions=len(cs), ratio_judge_literal=float(e_c.mean() / np.median(fl_c)),
                                         ci95_judge_literal=[float(np.percentile(bs_j, 2.5)), float(np.percentile(bs_j, 97.5))],
                                         ratio_like_for_like=float(e_c.mean() / fl_c.mean()),
                                         ci95_like_for_like=[float(np.percentile(bs_l, 2.5)), float(np.percentile(bs_l, 97.5))],
                                         mean_error_pp=float(e_c.mean()), median_floor_pp=float(np.median(fl_c)), mean_floor_pp=float(fl_c.mean()))
    summ["verdict_rule"] = "ratio_primary > 1.2: superiority winnable; <= 1.2: contrast (iii) preregistered as non-inferiority"
    summ["verdict"] = "SUPERIORITY WINNABLE" if summ["ratio_primary"] > 1.2 else "NON-INFERIORITY"
    res["summary"] = summ
    res["audit"] = dict(outer_test_cells_total=len(test_cells_all), cells_used_in_any_frame=len(used_cells),
                        intersection_within_fold=len(fold_overlap), split_file_sha256=split_sha0,
                        split_file_unchanged_after_run=True, test_fold_scored=False)
    cfg = dict(pilot="P3", dataset=ds, window=W, window_unit="weeks" if ds == "isu" else "cycles", n_trials=n_trials, seed=seed,
               inner_folds=N_INNER, life_level=LIFE_LEVEL, snl_grid=SNL_GRID, commit=git_commit(root),
               threads=os.environ.get("OMP_NUM_THREADS"), cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"),
               split_file=split_path, split_sha256=split_sha0, command=" ".join(sys.argv))
    json.dump(cfg, open(f"{outdir}/config.json", "w"), indent=1)
    json.dump(res, open(f"{outdir}/results.json", "w"), indent=1)
    pd.DataFrame(dict(cond=cs, best_learner_inner_cv_pp=e_c, replicate_floor_pp=fl_c)).to_csv(f"{outdir}/condition_level.csv", index=False)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
