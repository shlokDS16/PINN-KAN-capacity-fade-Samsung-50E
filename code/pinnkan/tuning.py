"""Nested tuning driver (PREREG_v2 sections 7, 8). Training conditions only: inner folds are grouped by condition and stratified by
temperature, inside the outer-training cells. TPE sampler seed = outer-fold index; tuning fits use seed 1000 + outer fold.
The tuned objective is the primary endpoint computed out-of-fold: pooled cell RMSE (pp) averaged within condition, then over conditions.

Budget rule: N = 20 trials x 3 inner folds; N = 40 if the median fit is under 20 s for every neural arm; if the median hard-ODE fit exceeds
30 s or the PINN fit exceeds 90 s, the equal-for-all Partial plan applies (N = 10, 2 inner folds). Seeds stay 5 (final refits)."""
import time

import numpy as np
import optuna

from .arms import ARMS, NEURAL, TOURNAMENT_HP, make_arm, suggest_hp
from .data import prepare_many
from .law import BACKBONES
from .metrics import condition_scores, primary_score, score_prepared

optuna.logging.set_verbosity(optuna.logging.WARNING)
BIG = 1e6   # objective value of a trial whose forecast is not finite


def choose_budget(median_fit_secs):
    """median_fit_secs: {arm_id: median seconds of a fit on a training fold}. -> dict(n_trials, inner_k, rule)"""
    neural = {a: s for a, s in median_fit_secs.items() if a in NEURAL}
    hard = median_fit_secs.get("A2")
    pinn = [s for a, s in neural.items() if ARMS[a].family == "pinn"]
    if (hard is not None and hard > 30.0) or (pinn and max(pinn) > 90.0):
        return {"n_trials": 10, "inner_k": 2, "rule": "Partial plan (equal for every arm): hard > 30 s or PINN > 90 s"}
    if neural and all(s < 20.0 for s in neural.values()):
        return {"n_trials": 40, "inner_k": 3, "rule": "N = 40: every neural arm median fit < 20 s"}
    return {"n_trials": 20, "inner_k": 3, "rule": "N = 20 default"}


def inner_k_for_m(m, partial=False, thin_folds=2):
    """PREREG_v4 4.1 with D020 C2: inner folds `thin_folds` (default 2; 4 only if the P6b decision file says adopt) for m in {8, 16}, 3 for m = 32; the Partial plan returns every cell
    to 2. None (no grid) keeps the V3 value 3 (2 under the Partial plan). The backbone tournament of the cell uses the same value."""
    if partial:
        return 2
    return 3 if (m is None or m >= 32) else int(thin_folds)


def inner_folds(cells, k, seed, spec, target_kind="cycling"):
    """condition -> inner fold, conditions of the scored kind only, stratified by temperature (round-robin through shuffled temperature strata)"""
    temp = {}
    for c in cells:
        if c.kind == target_kind:
            temp[c.cond] = float(c.raw[spec.strat_index]) if spec.strat_index is not None else 0.0
    assert temp, f"no {target_kind} cells to partition: the tuned task must be the scored task (review M3)"
    rng = np.random.default_rng([20261106, 21, int(seed)])
    order = []
    for T in sorted(set(temp.values())):
        g = sorted(c for c in temp if temp[c] == T)
        rng.shuffle(g)
        order += g
    return {c: i % k for i, c in enumerate(order)}


def cv_rows(arm_id, hp, cells, fold_of, k, spec, rule, seed, ctx, target_kind="cycling"):
    """out-of-fold per-cell rows over the k inner folds; also seconds spent in fits"""
    rows, secs, nfit = [], 0.0, 0
    assert {c.kind for c in cells if c.cond in fold_of} == {target_kind}, "inner folds partition cells of another kind than the scored one"
    for f in range(k):
        val = [c for c in cells if c.kind == target_kind and fold_of.get(c.cond) == f]
        tr = [c for c in cells if not (c.kind == target_kind and fold_of.get(c.cond) == f)]
        if not val:
            continue
        t0 = time.time()
        arm = make_arm(arm_id, spec, hp, seed, dict(ctx, rule=rule)).fit(tr)
        secs += time.time() - t0
        nfit += 1
        prep = prepare_many(val, rule, oracle=bool(ctx.get("oracle", False)))
        if prep:
            rows += score_prepared(arm.predict([p.win for p in prep]), prep)
    return rows, secs / max(nfit, 1)


def tune(arm_id, cells, spec, rule, n_trials, inner_k, outer_fold, ctx, target_kind="cycling"):
    """-> dict(best_hp, inner_cv_pp, cond_scores, trials, n_failed, median_fit_seconds, ...). Uses training cells only (the caller passes nothing else)."""
    seed = 1000 + int(outer_fold)
    fold_of = inner_folds(cells, inner_k, seed, spec, target_kind)
    a = ARMS[arm_id]
    out = {"arm": arm_id, "tuning_seed": seed, "tpe_seed": int(outer_fold), "inner_k": inner_k, "n_trials": n_trials if a.tuned else 0,
           "n_inner_conditions": len(fold_of)}
    if not a.tuned:
        rows, s = cv_rows(arm_id, {}, cells, fold_of, inner_k, spec, rule, seed, ctx, target_kind)
        out.update(best_hp={}, inner_cv_pp=primary_score(rows), cond_scores=condition_scores(rows), trials=[], n_failed=0, median_fit_seconds=s, rows=rows)
        return out
    trial_rows, trial_secs = {}, {}

    def objective(trial):
        hp = suggest_hp(trial, a.space)
        t0 = time.time()
        rows, s = cv_rows(arm_id, hp, cells, fold_of, inner_k, spec, rule, seed, ctx, target_kind)
        trial_rows[trial.number], trial_secs[trial.number] = rows, s
        v = primary_score(rows)
        return v if np.isfinite(v) else BIG

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=int(outer_fold)))
    max_failed = max(2, n_trials // 4)       # equal-budget rule (review m7): failed trials are redrawn until N valid ones exist, up to a cap
    while True:
        done = [t for t in study.trials if t.state.name == "COMPLETE"]
        failed = len(study.trials) - len(done)
        if len(done) >= n_trials:
            break
        if failed > max_failed:
            raise RuntimeError(f"{arm_id}: {failed} failed tuning trials (cap {max_failed}); the arm cannot receive the same N valid trials as the others")
        study.optimize(objective, n_trials=n_trials - len(done), catch=(Exception,))
    if not done:
        raise RuntimeError(f"{arm_id}: every tuning trial failed")
    best = min(done, key=lambda t: t.value)
    rows = trial_rows[best.number]
    out.update(best_hp=dict(best.params), inner_cv_pp=float(best.value), cond_scores=condition_scores(rows), rows=rows,
               trials=[{"number": t.number, "params": t.params, "value": t.value, "state": t.state.name, "fit_seconds": trial_secs.get(t.number)} for t in study.trials],
               n_failed=int(sum(t.state.name != "COMPLETE" for t in study.trials)),
               median_fit_seconds=float(np.median([trial_secs[t.number] for t in done])))
    return out


def backbone_tournament(cells, spec, rule, inner_k, outer_fold, ctx, target_kind="cycling"):
    """hard-ODE-KAN at default settings per backbone; the simplest backbone within one standard error of the best, on training conditions only"""
    seed = 1000 + int(outer_fold)
    fold_of = inner_folds(cells, inner_k, seed, spec, target_kind)
    res = {}
    for bb in BACKBONES:
        rows, _ = cv_rows("A2", TOURNAMENT_HP, cells, fold_of, inner_k, spec, rule, seed, dict(ctx, backbone=bb), target_kind)
        cs = condition_scores(rows)
        v = np.array(list(cs.values()))
        res[bb] = {"mean_pp": float(v.mean()) if len(v) else float("nan"), "se_pp": float(v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else 0.0, "n_conditions": len(v)}
    ok = {b: r for b, r in res.items() if np.isfinite(r["mean_pp"])}
    best = min(ok, key=lambda b: ok[b]["mean_pp"])
    thr = ok[best]["mean_pp"] + ok[best]["se_pp"]
    chosen = next(b for b in BACKBONES if b in ok and ok[b]["mean_pp"] <= thr)
    return {"chosen": chosen, "best": best, "table": res, "rule": "simplest backbone within one SE of the best (constant < self_limiting < accelerating)"}
