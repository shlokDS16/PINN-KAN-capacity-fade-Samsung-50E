"""Pilot P6b: does four-fold inner CV beat two-fold at m = 8?  (D020 judge section 4, rule R2'; design basis 01_mlexpert.md section 4 with R1 and C3 deleted)

DEVELOPMENT DATA (ISU), NON-CONFIRMATORY. ISU is not blind (PREREG 3.4). Nothing here is evidence for Samsung. CPU only.

Design (fixed by the ruling; nothing below is chosen after a result)
  * ISU Test B, runs/splits/isu_testB.json (sha256 checked before and after). For each of the 5 outer folds the outer-test conditions and cells are never
    loaded (data.load_split role='train' filters them before any array is built) and the identifier audit of p3_headroom.main() is repeated.
  * Pseudo-train = the nested max-min subset of m = 8 of the fold's training conditions (PREREG 4.1 selector on ISU coordinates). Pseudo-test = the fold's other
    training conditions. Window W = 2 weeks for inner-CV scoring and for the pseudo-test (data.WindowRule.for_grid, as run.py does at m < 32).
  * Arms A1 (ISU form), A2, A4 (= AG at m < 32), A9, A11, A12 with their confirmatory spaces. N = 20 TPE trials (sampler seed = outer fold, tuning seed
    1000 + fold), final refits seeds 0-4 on the pseudo-train, inner_k in {2, 4}; the backbone tournament takes the same inner_k and is run per (fold, inner_k)
    on the pseudo-train only. Laws-based arms (A1, A2, A4) use the backbone chosen by the tournament of their (fold, inner_k) cell; A9, A11, A12 ignore it.
  * Endpoint: the ensemble score of the ruling (section 1): for every arm the mean of its five refit forecasts (a non-finite value of a seed is replaced by the
    persistence forecast seed-wise BEFORE averaging), cell RMSE in pp, mean within condition. The per-seed score is reported as a descriptive row.
  * Rule R2' (printed by `aggregate`, nobody chooses): q_a = median over the pooled pseudo-test conditions of ln(S_a,2fold / S_a,4fold) (pooled value of a condition =
    mean of its log ratios over the folds in which it is pseudo-test). Adopt four inner folds for m in {8, 16}, for every tuned arm, iff q_a > 0 for at least 5 of
    the 6 arms AND min_a q_a > -ln(1.02); otherwise keep 2. An arm that did not finish, or any non-finite q, means the default (keep 2).
  * Reported, no decision: per-fold values, selected configurations and grid-edge hits, seed SD and the per-seed against ensemble share, A1 against D* under each
    variant, and the inversion-convergence diagnostic (final gradient norm of the test-time inversion of A1, A2, A9 at k = 2 and the prediction spread across
    three random initialisations). No rule is attached to the diagnostic.

Usage (from ROOT, interpreter .venv/Scripts/python.exe -P):
    python -P code/pilots/p6b_inner_folds.py run [--config code/pilots/p6b_config.json] [--out runs/pilot_P6b]
    python -P code/pilots/p6b_inner_folds.py aggregate [--out runs/pilot_P6b]
    python -P code/pilots/p6b_inner_folds.py run --smoke --out <scratch dir>     # mechanics test only: 1 fold, 2 trials, 2 seeds, steps_scale 0.02; writes nowhere under runs/pilot_P6b
"""
import os
import sys

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"       # CPU only (an empty value is dropped by Windows; -1 hides every device, as pinnkan/__init__ does)
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import csv
import hashlib
import json
import math
import subprocess
import time
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))

SCRIPT = os.path.join(HERE, "p6b_inner_folds.py")
DEFAULT_CONFIG = os.path.join(HERE, "p6b_config.json")
ARM_COST_S = {"A1": 14.5, "A4": 10.6, "A9": 2.7, "A2": 2.5, "A11": 2.2, "A12": 0.3}     # build_v1 timing table (judge section 4), used only to order the jobs


# ============================================================================================ pure helpers (unit-tested without torch)
def rule_verdict(q, arms, min_pos=5, floor_ratio=1.02):
    """Rule R2' (D020 judge section 4). q: arm -> q_a. -> dict(adopt, n_positive, min_q, threshold, reason). Incomplete or non-finite input = keep 2 (default)."""
    thr = -math.log(floor_ratio)
    missing = [a for a in arms if a not in q or q[a] is None or not math.isfinite(q[a])]
    if missing:
        return dict(adopt=False, n_positive=None, min_q=None, threshold=thr, reason=f"incomplete or non-finite q for {missing}: default applies (keep 2 inner folds)")
    vals = [q[a] for a in arms]
    npos, mn = int(sum(v > 0 for v in vals)), float(min(vals))
    adopt = bool(npos >= min_pos and mn > thr)
    return dict(adopt=adopt, n_positive=npos, min_q=mn, threshold=thr,
                reason=(f"{npos} of {len(arms)} arms with q > 0 (need >= {min_pos}); min q = {mn:.5f} against floor {thr:.5f} -> " + ("ADOPT four inner folds for m in {8, 16}" if adopt else "KEEP two inner folds")))


def ensemble_forecasts(per_seed_clean):
    """per_seed_clean: list over seeds of {cell_id: finite forecast array} -> {cell_id: mean over seeds}"""
    ids = per_seed_clean[0].keys()
    return {c: np.mean([d[c] for d in per_seed_clean], axis=0) for c in ids}


def clean_seedwise(preds, y_last_of):
    """non-finite forecast values of ONE seed are replaced by that cell's persistence value (last window retention); -> (cleaned dict, number replaced)"""
    from pinnkan.metrics import clean_forecast
    out, nbad = {}, 0
    for c, p in preds.items():
        out[c], b = clean_forecast(p, y_last_of[c])
        nbad += b
    return out, nbad


def pooled_log_ratio(per_fold_a, per_fold_b):
    """per_fold_*: {fold: {cond: score}} -> {cond: mean over the folds in which cond is in both of ln(a/b)}, {cond: n_folds}"""
    acc = {}
    for f in per_fold_a:
        if f not in per_fold_b:
            continue
        for c in set(per_fold_a[f]) & set(per_fold_b[f]):
            acc.setdefault(c, []).append(math.log(per_fold_a[f][c] / per_fold_b[f][c]))
    return {c: float(np.mean(v)) for c, v in acc.items()}, {c: len(v) for c, v in acc.items()}


def median_q(pooled):
    return float(np.median(list(pooled.values()))) if pooled else float("nan")


def edge_hits(space, hp):
    """{hyperparameter: True if the selected value sits on an end of its (ordered, numeric) grid / within 5 % of the end of its range}"""
    out = {}
    for name, sp in space.items():
        if name not in hp:
            continue
        v = hp[name]
        if sp[0] == "cat":
            opts = sp[1]
            if name == "nu" or not all(isinstance(o, (int, float)) and not isinstance(o, bool) for o in opts):
                continue
            s = sorted(opts)
            out[name] = bool(v == s[0] or v == s[-1])
        elif sp[0] == "logu":
            x = (math.log(v) - math.log(sp[1])) / (math.log(sp[2]) - math.log(sp[1]))
            out[name] = bool(x < 0.05 or x > 0.95)
        elif sp[0] == "int":
            x = (v - sp[1]) / (sp[2] - sp[1])
            out[name] = bool(x < 0.05 or x > 0.95)
    return out


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*a):
    try:
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"unavailable: {e}"


def code_hashes():
    d = os.path.join(ROOT, "code", "pinnkan")
    return {f: sha256_file(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".py")}


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def jdump(obj, path):
    def default(o):
        if isinstance(o, np.generic):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        return str(o)
    with open(path, "w", encoding="utf8") as fh:
        json.dump(obj, fh, indent=1, default=default)


# ============================================================================================ per-fold data (workers)
_FOLD_CACHE = {}


def fold_data(fold, cfg):
    """-> dict(spec, rule, train (pseudo-train cells), test (pseudo-test cells), kept, audit). Only the training side of the fold is ever loaded."""
    key = (fold, cfg["m"], cfg["window_W_weeks"])
    if key in _FOLD_CACHE:
        return _FOLD_CACHE[key]
    from pinnkan.data import WindowRule, load_split
    from pinnkan.specs import SPECS
    spec = SPECS[cfg["dataset"]]
    full = load_split(cfg["dataset"], cfg["test"], fold, role="train", root=ROOT, m=None)
    sub = load_split(cfg["dataset"], cfg["test"], fold, role="train", root=ROOT, m=int(cfg["m"]), subset=cfg["subset"])
    kept = list(sub.subset_info["kept"])
    train = list(sub.train)
    pseudo_test = [c for c in full.train if c.cond not in set(kept)]
    sp = json.load(open(os.path.join(ROOT, cfg["split_file"]), encoding="utf8"))["folds"][str(fold)]
    test_conds, test_cells, train_conds = set(map(str, sp["test_conditions"])), set(map(str, sp["test_cells"])), set(map(str, sp["train_conditions"]))
    used_conds = {c.cond for c in train} | {c.cond for c in pseudo_test}
    used_cells = {c.cell_id for c in train} | {c.cell_id for c in pseudo_test}
    assert not (used_conds & test_conds) and not (used_cells & test_cells), "outer-test condition or cell reached the pilot frame"
    assert used_conds <= train_conds, "a condition outside the fold's training set was loaded"
    assert {c.cond for c in train} == set(kept) and len(kept) == int(cfg["m"]) and not ({c.cond for c in train} & {c.cond for c in pseudo_test})
    base = WindowRule.for_spec(spec)
    rule = WindowRule.for_grid(spec, float(cfg["window_W_weeks"]), base)          # as run.py: rule_tune = WindowRule.for_grid(spec, 2 if m < 32 ...) -> W = 2 weeks on ISU
    audit = dict(fold=fold, n_outer_test_conditions=len(test_conds), n_outer_test_cells=len(test_cells), n_training_conditions=len(train_conds),
                 n_pseudo_train_conditions=len(kept), n_pseudo_test_conditions=len({c.cond for c in pseudo_test}), n_pseudo_test_cells=len(pseudo_test),
                 intersection_conditions_with_outer_test=len(used_conds & test_conds), intersection_cells_with_outer_test=len(used_cells & test_cells),
                 test_fold_scored=False, pseudo_train_conditions=kept, split_sha256_file=full.split_sha256, fold_hash_ok=bool(full.hash_ok and sub.hash_ok),
                 window_W=rule.W, min_window_points=rule.min_window_points, subset_sha256=sub.subset_info["sha256"])
    out = dict(spec=spec, rule=rule, train=train, test=pseudo_test, kept=kept, audit=audit)
    _FOLD_CACHE[key] = out
    return out


def make_ctx(cfg, rule, backbone):
    return {"backbone": backbone, "steps_scale": float(cfg["steps_scale"]), "rule": rule, "extra_twin_raw": None, "oracle": False, "per_cell_factor": True,
            "lab_indicator": False, "a10_starts": 8, "pinn": {}}


def _init_worker():
    import torch
    torch.set_num_threads(1)
    import pinnkan  # noqa: F401  (forces CPU, puts code/ on sys.path)
    assert not torch.cuda.is_available(), "CUDA is visible: the pilot is CPU only"


def job_tournament(task):
    cfg, out_dir, fold, k = task
    path = os.path.join(out_dir, "units", f"tournament_f{fold}_k{k}.json")
    if os.path.exists(path):
        return dict(kind="tournament", fold=fold, k=k, cpu=json.load(open(path))["cpu_seconds"], skipped=True)
    from pinnkan import tuning
    t0, c0 = time.time(), time.process_time()
    D = fold_data(fold, cfg)
    ctx = make_ctx(cfg, D["rule"], "self_limiting")
    tb = tuning.backbone_tournament(D["train"], D["spec"], D["rule"], k, fold, ctx, "cycling")
    tb.update(fold=fold, inner_k=k, wall_seconds=time.time() - t0, cpu_seconds=time.process_time() - c0, audit=D["audit"])
    jdump(tb, path)
    return dict(kind="tournament", fold=fold, k=k, cpu=tb["cpu_seconds"], wall=tb["wall_seconds"], chosen=tb["chosen"])


# ----------------------------------------------------------------------------------------- inversion diagnostic (replicas of the production test-time loops)
def _run_inversion(params, loss_fn, predict_fn, steps, lr):
    """Adam on the leaf tensors `params` exactly as the production loops do (zero_grad, loss, backward, step); returns per-cell gradient norms at the start and at the
    final iterate, the predictions after `steps` and after 2 x `steps` (same optimiser state continued)."""
    import torch
    opt = torch.optim.Adam(params, lr=lr)

    def gnorm():
        opt.zero_grad()
        loss_fn().backward()
        sq = 0.0
        for p in params:
            g = p.grad.detach()
            sq = sq + (g.reshape(g.shape[0], -1) ** 2).sum(1)
        opt.zero_grad()
        return np.sqrt(sq.numpy())

    g0 = gnorm()
    for _ in range(steps):
        opt.zero_grad()
        loss_fn().backward()
        opt.step()
    g1 = gnorm()
    p1 = predict_fn()
    for _ in range(steps):
        opt.zero_grad()
        loss_fn().backward()
        opt.step()
    p2 = predict_fn()
    return dict(g_init=g0, g_final=g1, pred=p1, pred_2x=p2)


def _invert(arm_id, model, spec, wcells, hp, init, steps_ctx):
    """one inversion of `arm_id`'s test-time latent(s) from `init` (None = production initialisation) -> dict as _run_inversion"""
    import torch
    from pinnkan import law as _law
    from pinnkan.hard import split_by_cell
    from pinnkan.law import SIGMA, batch_forecast_query, batch_from_windows, retention_from_y
    bw = batch_from_windows(spec, wcells, indicator=False)
    bq = batch_forecast_query(spec, wcells)
    Ct = bw.C
    flags = [p.requires_grad for p in model.parameters()]
    for p in model.parameters():
        p.requires_grad_(False)

    def to_pred(values):
        return {k: retention_from_y(spec, v) for k, v in split_by_cell(bq, values).items()}

    try:
        if arm_id == "A1":
            lam, seed, n_col, steps, lr = float(hp.get("lam_res", 1.0)), 0, 16, 200, 0.05
            u = torch.tensor(np.stack([np.random.default_rng([int(seed), zlib.crc32(cid.encode())]).random(n_col) for cid in bw.ids]), dtype=torch.float32)
            tc = bw.t_end.unsqueeze(1) + u * (model.col_t_max - bw.t_end).clamp_min(0.0).unsqueeze(1)
            to_n = spec.t_scale / spec.efc_scale
            nu = torch.stack([torch.tensor(bw.curves[c].rate(tc[c].numpy() * spec.t_scale) * to_n, dtype=torch.float32) for c in range(Ct)])
            cc = torch.arange(Ct).unsqueeze(1).expand(Ct, n_col).reshape(-1)
            tc, nu = tc.reshape(-1), nu.reshape(-1)
            mu = torch.zeros(Ct)
            z = (torch.zeros(Ct, model.zdim) if init is None else torch.tensor(init["z"], dtype=torch.float32)).clone().requires_grad_(True)
            delta = (mu if init is None else torch.tensor(init["delta"], dtype=torch.float32)).clone().requires_grad_(True)

            def loss_fn():
                F = model.F(bw.obs_t, bw.s[bw.obs_cell], z[bw.obs_cell])
                data = ((F - bw.obs_y) ** 2).sum()
                A_cal, A_cyc = model.law.amplitudes(bw.s, bw.is_cyc, delta)
                R = model.residual(tc, bw.s[cc], z[cc], A_cal[cc], A_cyc[cc], nu)
                return (data + lam * model.pts_per_cell * Ct * (R ** 2).mean()) / SIGMA ** 2 + _tau_term(delta, mu) + (z ** 2).sum()      # = pinn.invert_pinn's loss

            def predict_fn():
                with torch.no_grad():
                    return to_pred(model.F(bq.obs_t, bq.s[bq.obs_cell], z[bq.obs_cell]))
            params = [z, delta]
        elif arm_id == "A2":
            steps, lr = 300, 0.05
            mu = torch.zeros(Ct)
            delta = (mu if init is None else torch.tensor(init["delta"], dtype=torch.float32)).clone().requires_grad_(True)

            def loss_fn():
                r = model.predict_y(bw, delta) - bw.obs_y
                return (r ** 2).sum() / SIGMA ** 2 + ((delta - mu) ** 2).sum() / _law.TAU ** 2

            def predict_fn():
                with torch.no_grad():
                    return to_pred(model.predict_y(bq, delta))
            params = [delta]
        elif arm_id == "A9":
            steps, lr = 150, 0.05
            zmu = torch.zeros(Ct, model.zdim)
            z = (zmu if init is None else torch.tensor(init["z"], dtype=torch.float32)).clone().requires_grad_(True)

            def loss_fn():
                r = model.F(bw.obs_t, bw.s[bw.obs_cell], z[bw.obs_cell]) - bw.obs_y
                return (r ** 2).sum() / SIGMA ** 2 + ((z - zmu) ** 2).sum()

            def predict_fn():
                with torch.no_grad():
                    return to_pred(model.F(bq.obs_t, bq.s[bq.obs_cell], z[bq.obs_cell]))
            params = [z]
        else:
            raise ValueError(arm_id)
        out = _run_inversion(params, loss_fn, predict_fn, steps, lr)
        out["ids"] = list(bw.ids)
        out["zdim"] = getattr(model, "zdim", 0)
        out["Ct"] = Ct
        return out
    finally:
        for p, f in zip(model.parameters(), flags):
            p.requires_grad_(f)


def _tau_term(delta, mu):
    from pinnkan import pinn as _pinn
    return ((delta - mu) ** 2).sum() / _pinn.TAU ** 2


def inversion_diagnostic(arm_id, arm_obj, prep, hp, rng_key):
    """final gradient norm of the production test-time inversion + prediction spread over the zero initialisation and three random ones (judge section 4)"""
    from pinnkan import law as _law
    spec, wcells = arm_obj.spec, [p.win for p in prep]
    prod = _invert(arm_id, arm_obj.model, spec, wcells, hp, None, None)
    Ct, zdim = prod["Ct"], max(int(prod["zdim"]), 1)
    runs = [prod]
    for j in range(3):
        r = np.random.default_rng(list(rng_key) + [j])
        init = {"z": r.normal(0.0, 0.5, size=(Ct, zdim)), "delta": r.normal(0.0, _law.TAU, size=Ct)}
        runs.append(_invert(arm_id, arm_obj.model, spec, wcells, hp, init, None))
    ids = prod["ids"]
    spread = []
    for c in ids:
        a = np.stack([r["pred"][c] for r in runs])
        spread.append(float(100.0 * (a.max(0) - a.min(0)).max()))
    dbl = [float(100.0 * np.abs(prod["pred_2x"][c] - prod["pred"][c]).max()) for c in ids]
    truth = {p.cell.cell_id: p.fc_true for p in prep}
    cond_of = {p.cell.cell_id: p.cell.cond for p in prep}

    def mean_score(preds):
        by = {}
        for c in ids:
            by.setdefault(cond_of[c], []).append(100.0 * float(np.sqrt(np.mean((np.asarray(preds[c]) - truth[c]) ** 2))))
        return float(np.mean([np.mean(v) for v in by.values()]))
    sc = [mean_score(r["pred"]) for r in runs]
    ratio = prod["g_final"] / np.maximum(prod["g_init"], 1e-300)
    q = lambda a, p: float(np.percentile(a, p))
    return dict(arm=arm_id, n_cells=len(ids), grad_norm_init_median=q(prod["g_init"], 50), grad_norm_final_median=q(prod["g_final"], 50), grad_norm_final_p95=q(prod["g_final"], 95),
                grad_norm_final_max=float(prod["g_final"].max()), grad_ratio_final_over_init_median=q(ratio, 50), grad_ratio_final_over_init_max=float(ratio.max()),
                spread_pp_median=q(spread, 50), spread_pp_p95=q(spread, 95), spread_pp_max=float(max(spread)),
                doubled_steps_change_pp_median=q(dbl, 50), doubled_steps_change_pp_max=float(max(dbl)),
                mean_cell_score_pp_by_init=sc, score_range_over_inits_pp=float(max(sc) - min(sc)),
                init_rule="zero (production) + 3 draws z ~ N(0, 0.5^2), delta ~ N(0, TAU^2) (design choice of this script)",
                production_check_max_abs_diff_pp=None)


def job_arm(task):
    cfg, out_dir, fold, k, arm_id = task
    path = os.path.join(out_dir, "units", f"f{fold}_k{k}_{arm_id}.json")
    if os.path.exists(path):
        return dict(kind="arm", fold=fold, k=k, arm=arm_id, cpu=json.load(open(path)).get("cpu_seconds", 0.0), skipped=True)
    t0, c0 = time.time(), time.process_time()
    try:
        res = _arm_unit(cfg, out_dir, fold, k, arm_id)
        res.update(wall_seconds=time.time() - t0, cpu_seconds=time.process_time() - c0)
        jdump(res, path)
        return dict(kind="arm", fold=fold, k=k, arm=arm_id, cpu=res["cpu_seconds"], wall=res["wall_seconds"], inner_cv=res["tuning"]["inner_cv_pp"], ok=True)
    except Exception as e:  # noqa: BLE001  (a failed arm is recorded, never hidden: the default then applies)
        import traceback
        err = dict(fold=fold, k=k, arm=arm_id, error=f"{type(e).__name__}: {e}", traceback=traceback.format_exc(), wall_seconds=time.time() - t0, cpu_seconds=time.process_time() - c0)
        jdump(err, os.path.join(out_dir, "units", f"ERROR_f{fold}_k{k}_{arm_id}.json"))
        return dict(kind="arm", fold=fold, k=k, arm=arm_id, cpu=err["cpu_seconds"], wall=err["wall_seconds"], ok=False, error=err["error"])


def _arm_unit(cfg, out_dir, fold, k, arm_id):
    from pinnkan import tuning
    from pinnkan.arms import ARMS, make_arm
    from pinnkan.data import prepare_many
    from pinnkan.metrics import condition_scores, score_prepared, seed_condition_scores
    D = fold_data(fold, cfg)
    spec, rule, train = D["spec"], D["rule"], D["train"]
    tb = json.load(open(os.path.join(out_dir, "units", f"tournament_f{fold}_k{k}.json")))
    ctx = make_ctx(cfg, rule, tb["chosen"])
    r = tuning.tune(arm_id, train, spec, rule, int(cfg["n_trials"]), k, fold, ctx, "cycling")
    hp = r["best_hp"]
    prep = prepare_many(D["test"], rule)
    wcells = [p.win for p in prep]
    y_last = {p.cell.cell_id: p.win.y_last for p in prep}
    per_seed_clean, per_seed_rows, nbad, arm_seed0, t_fit = [], [], [], None, []
    for sd in cfg["final_seeds"]:
        t1 = time.time()
        arm = make_arm(arm_id, spec, hp, sd, ctx).fit(train)
        preds = arm.predict(wcells)
        t_fit.append(time.time() - t1)
        cl, nb = clean_seedwise(preds, y_last)
        per_seed_clean.append(cl)
        nbad.append(nb)
        per_seed_rows.append(score_prepared(cl, prep))
        if sd == cfg["final_seeds"][0]:
            arm_seed0 = arm
            preds_seed0 = preds
    ens = ensemble_forecasts(per_seed_clean)
    ens_rows = score_prepared(ens, prep)
    cs_ens = condition_scores(ens_rows)
    cs_seed, seed_sd = seed_condition_scores(per_seed_rows)
    cell_ens = {x["cell"]: x["rmse_pp"] for x in ens_rows}
    cell_seed = {c: float(np.mean([next(x["rmse_pp"] for x in rows if x["cell"] == c) for rows in per_seed_rows])) for c in cell_ens}
    out = dict(fold=fold, k=k, arm=arm_id, backbone=tb["chosen"], n_pseudo_test_cells_scored=len(prep), n_pseudo_test_conditions_scored=len(cs_ens),
               endpoint="ensemble of final_seeds forecasts, seed-wise non-finite substitution before averaging",
               tuning=dict(inner_cv_pp=r["inner_cv_pp"], best_hp=hp, n_failed=r["n_failed"], n_trials=r["n_trials"], inner_k=k, tuning_seed=r["tuning_seed"], tpe_seed=r["tpe_seed"],
                           n_inner_conditions=r["n_inner_conditions"], median_fit_seconds=r["median_fit_seconds"], trial_values=[t["value"] for t in r["trials"]],
                           grid_edge_hits=edge_hits(ARMS[arm_id].space, hp), cond_scores_inner=r["cond_scores"]),
               cond_ens=cs_ens, cond_perseed=cs_seed, seed_sd_of_mean=seed_sd, cell_ens=cell_ens, cell_perseed=cell_seed,
               ens_le_perseed_every_cell=bool(all(cell_ens[c] <= cell_seed[c] + 1e-9 for c in cell_ens)), nonfinite_per_seed=nbad, final_seeds=list(cfg["final_seeds"]),
               refit_seconds_per_seed=t_fit, n_params=int(arm_seed0.n_params), audit=D["audit"])
    if arm_id in cfg["diagnostics"]["arms"]:
        key = [20261106, 61, fold, k, ["A1", "A2", "A9"].index(arm_id)]
        dg = inversion_diagnostic(arm_id, arm_seed0, prep, hp, key)
        prod_pred = {c: np.asarray(preds_seed0[c], float) for c in preds_seed0}
        base_run = _invert(arm_id, arm_seed0.model, spec, wcells, hp, None, None)
        finite = {c: v for c, v in prod_pred.items() if np.all(np.isfinite(v))}
        dg["production_check_max_abs_diff_pp"] = float(max(100.0 * np.abs(base_run["pred"][c] - finite[c]).max() for c in finite)) if finite else None
        out["inversion_diagnostic"] = dg
    return out


# ============================================================================================ run
def log_line(out_dir, msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(os.path.join(out_dir, "RUN.log"), "a", encoding="utf8") as fh:
        fh.write(line + "\n")


def cmd_run(args):
    cfg = json.load(open(args.config, encoding="utf8"))
    out_dir = os.path.abspath(args.out)
    smoke = bool(args.smoke)
    if smoke:
        cfg.update(folds=[0], n_trials=2, final_seeds=[0, 1], steps_scale=0.02)
        assert os.path.abspath(out_dir) != os.path.join(ROOT, "runs", "pilot_P6b") and "pilot_P6b" not in out_dir.replace("\\", "/").split("/")[-1], "smoke must not write to runs/pilot_P6b"
    else:
        assert cfg["steps_scale"] == 1.0 and cfg["n_trials"] == 20 and cfg["final_seeds"] == [0, 1, 2, 3, 4], "the real run uses the ruled settings only"
        dirty = git("status", "--porcelain", "--", SCRIPT, args.config)
        if dirty:
            raise SystemExit(f"script or config not committed (rule: commit BEFORE the first fit):\n{dirty}")
    os.makedirs(os.path.join(out_dir, "units"), exist_ok=True)
    split_path = os.path.join(ROOT, cfg["split_file"])
    meta_path = os.path.join(out_dir, "run_meta.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {"sessions": []}
    sess = dict(started=now(), started_epoch=time.time(), head_commit=git("rev-parse", "HEAD"), script_last_commit=git("log", "-1", "--format=%H", "--", SCRIPT),
                script_last_commit_time=git("log", "-1", "--format=%cI", "--", SCRIPT), script_last_commit_epoch=int(git("log", "-1", "--format=%ct", "--", SCRIPT) or 0), config_last_commit=git("log", "-1", "--format=%H", "--", args.config),
                script_sha256=sha256_file(SCRIPT), config_sha256=sha256_file(args.config), split_sha256_before=sha256_file(split_path), pinnkan_sha256=code_hashes(),
                pinnkan_dirty=git("status", "--porcelain", "--", "code/pinnkan").splitlines(), smoke=smoke, workers=int(cfg["workers"]))
    meta["sessions"].append(sess)
    jdump(meta, meta_path)
    jdump({**cfg, "config_path": args.config}, os.path.join(out_dir, "config_used.json"))
    log_line(out_dir, f"P6b run start: smoke={smoke}, folds {cfg['folds']}, arms {cfg['arms']}, inner_k {cfg['inner_k_variants']}, N={cfg['n_trials']}, seeds {cfg['final_seeds']}, workers {cfg['workers']}")
    import multiprocessing as mp
    ctx = mp.get_context("spawn")
    cpu_used = 0.0
    abort = False
    with ctx.Pool(int(cfg["workers"]), initializer=_init_worker) as pool:
        t1 = [(cfg, out_dir, f, k) for f in cfg["folds"] for k in cfg["inner_k_variants"]]
        for r in pool.imap_unordered(job_tournament, t1):
            cpu_used += r["cpu"]
            log_line(out_dir, f"tournament f{r['fold']} k{r['k']}: {r.get('chosen', 'cached')} (cpu {r['cpu']:.0f} s); CPU total {cpu_used / 3600:.3f} h")
        tasks = [(cfg, out_dir, f, k, a) for f in cfg["folds"] for k in cfg["inner_k_variants"] for a in cfg["arms"]]
        tasks.sort(key=lambda t: -ARM_COST_S[t[4]] * t[3])
        n_done = 0
        for r in pool.imap_unordered(job_arm, tasks):
            n_done += 1
            cpu_used += r["cpu"]
            tag = "ERROR " + r["error"] if not r.get("ok", r.get("skipped", False)) else (f"inner-CV {r['inner_cv']:.3f} pp" if "inner_cv" in r else "cached")
            log_line(out_dir, f"[{n_done}/{len(tasks)}] f{r['fold']} k{r['k']} {r['arm']}: {tag} (cpu {r['cpu']:.0f} s, wall {r.get('wall', 0):.0f} s); CPU total {cpu_used / 3600:.3f} h")
            if cpu_used / 3600 > float(cfg["cpu_hours_abort"]) and not smoke:
                log_line(out_dir, f"ABORT: CPU budget {cfg['cpu_hours_abort']} h exceeded; stopping (the default 'keep 2 inner folds' applies to unfinished work)")
                abort = True
                pool.terminate()
                break
    sess.update(ended=now(), ended_epoch=time.time(), cpu_hours_this_session=cpu_used / 3600, aborted=abort, split_sha256_after=sha256_file(split_path), pinnkan_sha256_end=code_hashes())
    jdump(meta, meta_path)
    log_line(out_dir, f"P6b run end: CPU {cpu_used / 3600:.3f} h, wall {(sess['ended_epoch'] - sess['started_epoch']) / 3600:.3f} h, aborted={abort}")


# ============================================================================================ aggregate
def load_units(out_dir, cfg):
    U, errors = {}, []
    for f in cfg["folds"]:
        for k in cfg["inner_k_variants"]:
            for a in cfg["arms"]:
                p = os.path.join(out_dir, "units", f"f{f}_k{k}_{a}.json")
                if os.path.exists(p):
                    U[(f, k, a)] = json.load(open(p))
                else:
                    errors.append(f"missing f{f} k{k} {a}" + (" (ERROR file exists)" if os.path.exists(os.path.join(out_dir, "units", f"ERROR_f{f}_k{k}_{a}.json")) else ""))
    return U, errors


def fmt(x, nd=4):
    return "n/a" if x is None or (isinstance(x, float) and not math.isfinite(x)) else f"{x:.{nd}f}"


def cmd_aggregate(args):
    out_dir = os.path.abspath(args.out)
    cfg = json.load(open(os.path.join(out_dir, "config_used.json"), encoding="utf8"))
    meta = json.load(open(os.path.join(out_dir, "run_meta.json")))
    arms, folds = cfg["arms"], cfg["folds"]
    k_lo, k_hi = cfg["inner_k_variants"]
    U, errors = load_units(out_dir, cfg)
    split_path = os.path.join(ROOT, cfg["split_file"])
    split_after = sha256_file(split_path)
    first_start = min(s["started_epoch"] for s in meta["sessions"])
    last_end = max((s.get("ended_epoch", 0.0) for s in meta["sessions"]), default=0.0)
    cpu_s = sum(u.get("cpu_seconds", 0.0) for u in U.values())
    for p in os.listdir(os.path.join(out_dir, "units")):
        if p.startswith("tournament_") or p.startswith("ERROR_"):
            cpu_s += json.load(open(os.path.join(out_dir, "units", p))).get("cpu_seconds", 0.0)
    rows_pc, rows_pf, summary = [], [], {"arms": {}}
    q, q_seed, ci = {}, {}, {}
    rng = np.random.default_rng(20261106)
    pooled_by = {}
    for a in arms:
        ens_k = {k: {f: U[(f, k, a)]["cond_ens"] for f in folds if (f, k, a) in U} for k in (k_lo, k_hi)}
        sd_k = {k: {f: U[(f, k, a)]["cond_perseed"] for f in folds if (f, k, a) in U} for k in (k_lo, k_hi)}
        complete = all((f, k, a) in U for f in folds for k in (k_lo, k_hi))
        pooled, nf = pooled_log_ratio(ens_k[k_lo], ens_k[k_hi])
        pooled_sd, _ = pooled_log_ratio(sd_k[k_lo], sd_k[k_hi])
        pooled_by[a] = pooled
        q[a] = median_q(pooled) if complete else float("nan")
        q_seed[a] = median_q(pooled_sd) if complete else float("nan")
        conds = sorted(pooled)
        v = np.array([pooled[c] for c in conds])
        boots = [float(np.median(v[rng.integers(0, len(v), len(v))])) for _ in range(5000)] if len(v) else []
        ci[a] = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))] if boots else [None, None]
        per_fold_q = {}
        for f in folds:
            if (f, k_lo, a) in U and (f, k_hi, a) in U:
                cs = set(U[(f, k_lo, a)]["cond_ens"]) & set(U[(f, k_hi, a)]["cond_ens"])
                per_fold_q[f] = float(np.median([math.log(U[(f, k_lo, a)]["cond_ens"][c] / U[(f, k_hi, a)]["cond_ens"][c]) for c in cs]))
        for c in conds:
            s_lo = [ens_k[k_lo][f][c] for f in ens_k[k_lo] if c in ens_k[k_lo][f] and c in ens_k[k_hi].get(f, {})]
            s_hi = [ens_k[k_hi][f][c] for f in ens_k[k_hi] if c in ens_k[k_hi][f] and c in ens_k[k_lo].get(f, {})]
            rows_pc.append(dict(arm=a, cond=c, n_folds_pseudo_test=nf[c], ln_ratio_pooled_ens=pooled[c], S_2fold_mean_ens_pp=np.mean(s_lo), S_4fold_mean_ens_pp=np.mean(s_hi),
                                ln_ratio_pooled_perseed=pooled_sd.get(c, float("nan"))))
        for f in folds:
            for k in (k_lo, k_hi):
                if (f, k, a) in U:
                    for c, s in U[(f, k, a)]["cond_ens"].items():
                        rows_pf.append(dict(arm=a, fold=f, inner_k=k, cond=c, S_ens_pp=s, S_perseed_pp=U[(f, k, a)]["cond_perseed"].get(c, float("nan"))))
        # descriptive blocks
        share = {}
        for k in (k_lo, k_hi):
            pl, _ = pooled_log_ratio({f: U[(f, k, a)]["cond_perseed"] for f in folds if (f, k, a) in U}, {f: U[(f, k, a)]["cond_ens"] for f in folds if (f, k, a) in U})
            share[k] = median_q(pl)
        summary["arms"][a] = dict(
            complete=complete, q_ens=q[a], q_ens_bootstrap95=ci[a], q_perseed_descriptive=q_seed[a], n_pooled_conditions=len(conds), per_fold_median_ln_ratio=per_fold_q,
            median_ln_perseed_over_ens={str(k): share[k] for k in share},
            mean_cross_condition_score_pp={str(k): float(np.mean([np.mean(list(U[(f, k, a)]["cond_ens"].values())) for f in folds if (f, k, a) in U])) if any((f, k, a) in U for f in folds) else None for k in (k_lo, k_hi)},
            seed_sd_of_mean_pp={str(k): float(np.mean([U[(f, k, a)]["seed_sd_of_mean"] for f in folds if (f, k, a) in U])) if any((f, k, a) in U for f in folds) else None for k in (k_lo, k_hi)},
            inner_cv_pp_by_fold={str(k): {str(f): U[(f, k, a)]["tuning"]["inner_cv_pp"] for f in folds if (f, k, a) in U} for k in (k_lo, k_hi)},
            selected_hp_by_fold={str(k): {str(f): U[(f, k, a)]["tuning"]["best_hp"] for f in folds if (f, k, a) in U} for k in (k_lo, k_hi)},
            grid_edge_share={str(k): (float(np.mean([h for f in folds if (f, k, a) in U for h in U[(f, k, a)]["tuning"]["grid_edge_hits"].values()])) if any((f, k, a) in U and U[(f, k, a)]["tuning"]["grid_edge_hits"] for f in folds) else None) for k in (k_lo, k_hi)},
            n_failed_trials={str(k): sum(U[(f, k, a)]["tuning"]["n_failed"] for f in folds if (f, k, a) in U) for k in (k_lo, k_hi)},
            nonfinite_seed_forecast_values={str(k): sum(sum(U[(f, k, a)]["nonfinite_per_seed"]) for f in folds if (f, k, a) in U) for k in (k_lo, k_hi)},
            ens_le_perseed_every_cell_all_units=bool(all(U[(f, k, a)]["ens_le_perseed_every_cell"] for f in folds for k in (k_lo, k_hi) if (f, k, a) in U)))
    verdict = rule_verdict(q, arms, int(cfg["rule_R2prime"]["min_positive_arms"]), float(cfg["rule_R2prime"]["floor_ratio"]))
    if errors:
        verdict = dict(adopt=False, n_positive=verdict["n_positive"], min_q=verdict["min_q"], threshold=verdict["threshold"],
                       reason="unfinished or failed units (" + "; ".join(errors[:6]) + (" ..." if len(errors) > 6 else "") + "): default applies (keep 2 inner folds)")
    # --- A1 against D* (descriptive, non-binding): D* by inner CV per (fold, variant), the P6 reading of J16 5.6
    from pinnkan import selectors
    a1_vs_d = {}
    if "A1" in arms:
        for k in (k_lo, k_hi):
            sel, perfold = {}, {}
            for f in folds:
                if all((f, k, a) in U for a in ("A1", "A9", "A11", "A12")):
                    d = selectors.select_comparators({a: U[(f, k, a)]["tuning"]["inner_cv_pp"] for a in ("A9", "A11", "A12")}, 8)["D*"]["arm"]
                    sel[f] = d
                    perfold[f] = {c: U[(f, k, d)]["cond_ens"][c] for c in U[(f, k, d)]["cond_ens"]}
            pl, _ = pooled_log_ratio(perfold, {f: U[(f, k, "A1")]["cond_ens"] for f in sel}) if sel else ({}, {})
            a1_vs_d[str(k)] = dict(dstar_by_fold=sel, median_ln_Dstar_over_A1=median_q(pl), share_conditions_A1_better=(float(np.mean([v > 0 for v in pl.values()])) if pl else None), n_conditions=len(pl))
    summary["A1_vs_Dstar_descriptive"] = a1_vs_d
    # --- inversion diagnostic
    diag = {}
    for a in cfg["diagnostics"]["arms"]:
        for k in (k_lo, k_hi):
            ds = [U[(f, k, a)]["inversion_diagnostic"] for f in folds if (f, k, a) in U and "inversion_diagnostic" in U[(f, k, a)]]
            if ds:
                diag[f"{a} k={k}"] = dict(n_folds=len(ds), grad_norm_final_median_of_medians=float(np.median([d["grad_norm_final_median"] for d in ds])),
                                         grad_norm_final_max=float(max(d["grad_norm_final_max"] for d in ds)), grad_norm_init_median_of_medians=float(np.median([d["grad_norm_init_median"] for d in ds])),
                                         grad_ratio_final_over_init_median=float(np.median([d["grad_ratio_final_over_init_median"] for d in ds])),
                                         grad_ratio_final_over_init_max=float(max(d["grad_ratio_final_over_init_max"] for d in ds)),
                                         spread_pp_median_of_medians=float(np.median([d["spread_pp_median"] for d in ds])), spread_pp_p95_max_over_folds=float(max(d["spread_pp_p95"] for d in ds)),
                                         spread_pp_max=float(max(d["spread_pp_max"] for d in ds)), doubled_steps_change_pp_max=float(max(d["doubled_steps_change_pp_max"] for d in ds)),
                                         score_range_over_inits_pp_max=float(max(d["score_range_over_inits_pp"] for d in ds)),
                                         production_check_max_abs_diff_pp=float(max(d["production_check_max_abs_diff_pp"] or 0.0 for d in ds)))
    summary["inversion_diagnostic"] = diag
    # --- decision file
    pin_start = meta["sessions"][0]["pinnkan_sha256"]
    pin_end = meta["sessions"][-1].get("pinnkan_sha256_end") or code_hashes()
    changed = sorted(f for f in set(pin_start) | set(pin_end) if pin_start.get(f) != pin_end.get(f))
    first_script_commit_time = meta["sessions"][0]["script_last_commit_time"]
    decision = dict(pilot="P6b", status="development, non-confirmatory; ISU is not blind (PREREG 3.4); not evidence for Samsung", rule=cfg["rule_R2prime"]["text"],
                    verdict=("ADOPT_4_INNER_FOLDS_m8_m16" if verdict["adopt"] else "KEEP_2_INNER_FOLDS"), verdict_reason=verdict["reason"],
                    q_a=q, q_a_bootstrap95_descriptive=ci, n_positive=verdict["n_positive"], min_q=verdict["min_q"], floor=-math.log(float(cfg["rule_R2prime"]["floor_ratio"])),
                    arms=arms, complete=not errors, missing_units=errors,
                    script=os.path.relpath(SCRIPT, ROOT).replace("\\", "/"), script_sha256=meta["sessions"][0]["script_sha256"], script_sha256_now=sha256_file(SCRIPT),
                    script_commit=meta["sessions"][0]["script_last_commit"], script_commit_time=first_script_commit_time, config_sha256=meta["sessions"][0]["config_sha256"],
                    config_commit=meta["sessions"][0]["config_last_commit"], head_commit_at_start=meta["sessions"][0]["head_commit"],
                    script_committed_before_first_fit=bool(meta["sessions"][0]["script_last_commit"]) and 0 < meta["sessions"][0]["script_last_commit_epoch"] <= first_start,
                    split_file=cfg["split_file"], split_sha256_before=meta["sessions"][0]["split_sha256_before"], split_sha256_after=split_after,
                    split_unchanged=bool(meta["sessions"][0]["split_sha256_before"] == split_after), started=meta["sessions"][0]["started"], ended=meta["sessions"][-1].get("ended"),
                    cpu_hours_sum_of_units=cpu_s / 3600, wall_hours=((last_end - first_start) / 3600 if last_end else None), pinnkan_files_changed_during_run=changed,
                    pinnkan_dirty_at_start=meta["sessions"][0]["pinnkan_dirty"], outer_test_scored=False)
    jdump(decision, os.path.join(out_dir, "decision.json"))
    jdump(summary, os.path.join(out_dir, "summary.json"))
    audits = {f: next(U[(f, k, a)]["audit"] for k in (k_lo, k_hi) for a in arms if (f, k, a) in U) for f in folds if any((f, k, a) in U for k in (k_lo, k_hi) for a in arms)}
    jdump(audits, os.path.join(out_dir, "fold_audit.json"))
    for name, rows in (("per_condition.csv", rows_pc), ("per_fold_condition.csv", rows_pf)):
        if rows:
            with open(os.path.join(out_dir, name), "w", newline="", encoding="utf8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
    # --- markdown tables for RESULT.md
    L = ["### Table A. Rule R2' (development data, ISU: not evidence for Samsung)", "", "| arm | q_a (ensemble endpoint) | bootstrap 95 % (descriptive) | q_a (per-seed endpoint, descriptive) | q_a > 0 |", "|---|---|---|---|---|"]
    for a in arms:
        L.append(f"| {a} | {fmt(q[a], 5)} | [{fmt(ci[a][0], 4)}, {fmt(ci[a][1], 4)}] | {fmt(q_seed[a], 5)} | {'yes' if q[a] > 0 else 'no'} |" if math.isfinite(q[a]) else f"| {a} | n/a | n/a | n/a | n/a |")
    L += ["", f"Verdict: **{decision['verdict']}**. {verdict['reason']}.", "", f"Floor -ln(1.02) = {fmt(-math.log(1.02), 5)}; arms with q > 0: {verdict['n_positive']} of {len(arms)}; min q = {fmt(verdict['min_q'], 5)}.", ""]
    L += ["### Table B. Per-fold median ln(S_2fold / S_4fold) over the fold's pseudo-test conditions (ensemble endpoint)", "", "| arm | " + " | ".join(f"fold {f}" for f in folds) + " |", "|---|" + "---|" * len(folds)]
    for a in arms:
        pf = summary["arms"][a]["per_fold_median_ln_ratio"]
        L.append(f"| {a} | " + " | ".join(fmt(pf.get(f if f in pf else str(f)), 4) for f in folds) + " |")
    L += ["", "### Table C. Mean cross-condition ensemble score (pp), mean over folds; seed SD of the cross-condition mean (pp); median ln(per-seed / ensemble) score", "",
          f"| arm | S {k_lo}-fold | S {k_hi}-fold | seed SD {k_lo} | seed SD {k_hi} | median ln(per-seed/ens) {k_lo} | {k_hi} | grid-edge share {k_lo} | {k_hi} | failed trials {k_lo}/{k_hi} | non-finite seed values {k_lo}/{k_hi} |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in arms:
        s = summary["arms"][a]
        L.append(f"| {a} | {fmt(s['mean_cross_condition_score_pp'][str(k_lo)], 3)} | {fmt(s['mean_cross_condition_score_pp'][str(k_hi)], 3)} | {fmt(s['seed_sd_of_mean_pp'][str(k_lo)], 3)} | {fmt(s['seed_sd_of_mean_pp'][str(k_hi)], 3)} | "
                 f"{fmt(s['median_ln_perseed_over_ens'][str(k_lo)], 4)} | {fmt(s['median_ln_perseed_over_ens'][str(k_hi)], 4)} | {fmt(s['grid_edge_share'][str(k_lo)], 2)} | {fmt(s['grid_edge_share'][str(k_hi)], 2)} | "
                 f"{s['n_failed_trials'][str(k_lo)]}/{s['n_failed_trials'][str(k_hi)]} | {s['nonfinite_seed_forecast_values'][str(k_lo)]}/{s['nonfinite_seed_forecast_values'][str(k_hi)]} |")
    L += ["", "### Table D. A1 against D* (inner-CV choice of A9, A11, A12 per fold and variant), ensemble endpoint, descriptive, non-binding", "", "| variant | D* by fold | median ln(S_D* / S_A1) | share of conditions where A1 is better | conditions |", "|---|---|---|---|---|"]
    for k, d in a1_vs_d.items():
        L.append(f"| {k}-fold | {', '.join(f'{f}:{v}' for f, v in d['dstar_by_fold'].items())} | {fmt(d['median_ln_Dstar_over_A1'], 4)} | {fmt(d['share_conditions_A1_better'], 3)} | {d['n_conditions']} |")
    L += ["", "### Table E. Inversion-convergence diagnostic (seed-0 refit, pseudo-test windows W = 2 weeks; no rule attached)", "",
          "| arm, variant | folds | grad norm initial (median) | grad norm final (median) | grad norm final (max) | final/initial (median) | final/initial (max) | spread over 4 inits, pp (median) | spread pp (max cell, max fold) | change when steps are doubled, pp (max) | score range over inits, pp (max) | replica vs production, pp (max) |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, d in diag.items():
        L.append(f"| {key} | {d['n_folds']} | {d['grad_norm_init_median_of_medians']:.3g} | {d['grad_norm_final_median_of_medians']:.3g} | {d['grad_norm_final_max']:.3g} | {d['grad_ratio_final_over_init_median']:.3g} | {d['grad_ratio_final_over_init_max']:.3g} | "
                 f"{d['spread_pp_median_of_medians']:.4f} | {d['spread_pp_max']:.4f} | {d['doubled_steps_change_pp_max']:.4f} | {d['score_range_over_inits_pp_max']:.4f} | {d['production_check_max_abs_diff_pp']:.2e} |")
    L += ["", "### Table F. Run facts", "", f"- CPU hours (sum over units, tournaments and error files): {cpu_s / 3600:.3f}; wall hours: {fmt(decision['wall_hours'], 3)}; units complete: {not errors}.",
          f"- split sha256 before = after: {decision['split_unchanged']} ({decision['split_sha256_before']}).", f"- script commit: {decision['script_commit']} (committed {first_script_commit_time}); script sha256 unchanged since the first fit: {decision['script_sha256'] == decision['script_sha256_now']}.",
          f"- pinnkan files whose content changed between the start and the end of the run: {changed if changed else 'none'}.", f"- tuned per fold: pseudo-train conditions = 8; pseudo-test conditions per fold: "
          + ", ".join(f"f{f}: {audits[f]['n_pseudo_test_conditions']}" for f in audits) + "."]
    with open(os.path.join(out_dir, "tables.md"), "w", encoding="utf8") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    print("\nVERDICT:", decision["verdict"], "|", verdict["reason"])


def main():
    ap = argparse.ArgumentParser(description="Pilot P6b")
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run")
    r.add_argument("--config", default=DEFAULT_CONFIG)
    r.add_argument("--out", default=os.path.join(ROOT, "runs", "pilot_P6b"))
    r.add_argument("--smoke", action="store_true")
    g = sp.add_parser("aggregate")
    g.add_argument("--out", default=os.path.join(ROOT, "runs", "pilot_P6b"))
    a = ap.parse_args()
    {"run": cmd_run, "aggregate": cmd_aggregate}[a.cmd](a)


if __name__ == "__main__":
    main()
