"""D023 check: which test-time inversion makes the per-cell latents of A1 and A9 converged and start-independent?

DEVELOPMENT DATA (ISU training sides), NON-CONFIRMATORY. No Samsung label, no ISU outer-test fold. CPU only. Production code is imported, never edited.
Rule and design: debates/D023_inversion/01_proposal.md section 7 (committed before the first fit of the main run).

Per outer fold f in 0..4 of runs/splits/isu_testB.json: pseudo-train = the m = 8 max-min subset, pseudo-test = the fold's other training conditions, window W = 2 weeks
(identical to P6b: code/pilots/p6b_inner_folds.fold_data). Arms A1, A9, A2 refit with seed 0 and the P6b 2-fold configuration and tournament backbone
(runs/pilot_P6b/units/f<f>_k2_<arm>.json, tournament_f<f>_k2.json). Each arm's own causal inversion objective (window points + A1's residual over the horizon +
priors; exactly the production loss, written per cell) is minimised by:
  O0  production: Adam lr 0.05, A1 200 / A9 150 / A2 300 steps, float32, start at the prior mode (budget doubled by continuing the same optimiser)
  O1  Adam, float64, lr 0.05 cosine-decayed to 5e-4, cap 4000 steps (doubled: a fresh 8000-step run)
  O2  block-diagonal damped Newton (Levenberg-Marquardt per cell; exact per-cell Hessian by autograd; the objective is a sum of per-cell terms), float64,
      cap 100 iterations (doubled: 200)
  O3  O2 from a fixed start set S_A (prior mode, prior mode +- 1 prior sd along every latent axis), per-cell selection by the objective; stability compared with
      the selection from S_B (prior mode + 4 seeded draws z ~ N(0, 1), delta ~ N(0, TAU^2))
Start spread for O0-O2: prior mode + 3 seeded draws z ~ N(0, 0.5^2), delta ~ N(0, TAU^2) (as P6b).

Usage (ROOT, .venv/Scripts/python.exe -P):
  python -P code/pilots/d023_inversion_check.py run --folds 0 1 2 [--out runs/check_D023_inversion]
  python -P code/pilots/d023_inversion_check.py aggregate [--out runs/check_D023_inversion]
  python -P code/pilots/d023_inversion_check.py run --smoke --out <scratch>      # mechanics only: 1 fold, tiny caps; never under runs/
"""
import os
import sys

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import copy
import dataclasses
import json
import subprocess
import time
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, HERE)

P6B = os.path.join(ROOT, "runs", "pilot_P6b")
CFG = {"dataset": "isu", "test": "B", "m": 8, "subset": "maxmin", "window_W_weeks": 2.0, "steps_scale": 1.0, "split_file": "runs/splits/isu_testB.json"}
ARMS = ["A1", "A9", "A2"]
PROD = {"A1": 200, "A9": 150, "A2": 300}
CAPS = {"O1": 4000, "O2": 100}
CPU_ABORT_H = 0.70          # per process; the run is then incomplete and the verdict defaults to NONE
TOL = 1e-6                  # converged iff ||grad_c|| <= TOL * (1 + |f_c|)

RULE = {  # D023 proposal section 7; copied here so that `aggregate` applies it mechanically
    "order": ["O2", "O1", "O3"],
    "arms_gated": ["A1", "A9"],
    "a_conv_share_min": 0.99,
    "b_budget_p99_max_pp": 0.1, "b_budget_max_pp": 1.0,
    "c_spread_median_max_pp": 0.1, "c_spread_p95_max_pp": 1.0,
    "d_objective_median_delta_max": 0.0,
    "e_A2_change_p99_max_pp": 0.05,
}


def jdump(obj, path):
    def default(o):
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        raise TypeError(type(o))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf8") as fh:
        json.dump(obj, fh, indent=1, default=default)
    os.replace(tmp, path)


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


# ============================================================================================ per-cell objectives (= production losses, written per cell)
def to64(b):
    import torch
    rep = {f.name: getattr(b, f.name).double() for f in dataclasses.fields(b) if isinstance(getattr(b, f.name), torch.Tensor) and getattr(b, f.name).is_floating_point()}
    return dataclasses.replace(b, **rep)


def problem(arm_id, model, spec, wcells, hp, dtype, seed=0, n_col=16):
    """-> dict(fun(P) -> per-cell objective (C,), predict(P) -> {cell: retention array}, p, C, prior_mode P0, scale per coordinate)"""
    import torch
    from pinnkan import law as _law
    from pinnkan import pinn as _pinn
    from pinnkan.hard import split_by_cell
    from pinnkan.law import SIGMA, batch_forecast_query, batch_from_windows, retention_from_y
    m = copy.deepcopy(model)
    if dtype == "f64":
        m = m.double()
    for q in m.parameters():
        q.requires_grad_(False)
    bw, bq = batch_from_windows(spec, wcells), batch_forecast_query(spec, wcells)
    if dtype == "f64":
        bw, bq = to64(bw), to64(bq)
    dt = torch.float64 if dtype == "f64" else torch.float32
    C = bw.C

    def to_pred(y):
        return {k: retention_from_y(spec, v) for k, v in split_by_cell(bq, y).items()}

    def cell_sum(v):
        return torch.zeros(C, dtype=dt).index_add(0, bw.obs_cell, v)

    if arm_id == "A1":
        lam = float(hp.get("lam_res", 1.0))
        u = torch.tensor(np.stack([np.random.default_rng([int(seed), zlib.crc32(cid.encode())]).random(n_col) for cid in bw.ids]), dtype=dt)
        tc = bw.t_end.unsqueeze(1) + u * (m.col_t_max - bw.t_end).clamp_min(0.0).unsqueeze(1)
        to_n = spec.t_scale / spec.efc_scale
        nu = torch.stack([torch.tensor(bw.curves[c].rate(tc[c].detach().numpy() * spec.t_scale) * to_n, dtype=dt) for c in range(C)])
        cc = torch.arange(C).unsqueeze(1).expand(C, n_col).reshape(-1)
        tc, nu = tc.reshape(-1), nu.reshape(-1)
        zd = m.zdim

        def fun(P):
            z, delta = P[:, :zd], P[:, zd]
            F = m.F(bw.obs_t, bw.s[bw.obs_cell], z[bw.obs_cell])
            A_cal, A_cyc = m.law.amplitudes(bw.s, bw.is_cyc, delta)
            R = m.residual(tc, bw.s[cc], z[cc], A_cal[cc], A_cyc[cc], nu).reshape(C, n_col)
            return (cell_sum((F - bw.obs_y) ** 2) + lam * m.pts_per_cell / n_col * (R ** 2).sum(1)) / SIGMA ** 2 + delta ** 2 / _pinn.TAU ** 2 + (z ** 2).sum(1)

        def predict(P):
            with torch.no_grad():
                return to_pred(m.F(bq.obs_t, bq.s[bq.obs_cell], P[:, :zd][bq.obs_cell]))
        p, sd = zd + 1, [1.0] * zd + [_pinn.TAU]
    elif arm_id == "A9":
        zd = m.zdim

        def fun(P):
            return cell_sum((m.F(bw.obs_t, bw.s[bw.obs_cell], P[bw.obs_cell]) - bw.obs_y) ** 2) / SIGMA ** 2 + (P ** 2).sum(1)

        def predict(P):
            with torch.no_grad():
                return to_pred(m.F(bq.obs_t, bq.s[bq.obs_cell], P[bq.obs_cell]))
        p, sd = zd, [1.0] * zd
    elif arm_id == "A2":
        def fun(P):
            return cell_sum((m.predict_y(bw, P[:, 0]) - bw.obs_y) ** 2) / SIGMA ** 2 + P[:, 0] ** 2 / _law.TAU ** 2

        def predict(P):
            with torch.no_grad():
                return to_pred(m.predict_y(bq, P[:, 0]))
        p, sd = 1, [_law.TAU]
    else:
        raise ValueError(arm_id)
    ref_only = (torch.bincount(bw.obs_cell, minlength=C) <= 1).numpy()
    return dict(fun=fun, predict=predict, p=p, C=C, dt=dt, sd=np.array(sd), ids=list(bw.ids), ref_only=ref_only)


# ============================================================================================ optimisers
def grad_of(pr, P):
    import torch
    Pv = P.detach().clone().requires_grad_(True)
    f = pr["fun"](Pv)
    g = torch.autograd.grad(f.sum(), Pv)[0]
    return f.detach(), g.detach()


def adam(pr, P0, steps, lr, schedule=None, eta_min=None, continue_steps=0):
    """Adam on all cells at once (per-element updates: identical to the production loops on [z, delta]); returns P after `steps` and after steps + continue_steps"""
    import torch
    P = P0.detach().clone().requires_grad_(True)
    opt = torch.optim.Adam([P], lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=eta_min) if schedule == "cosine" else None
    for _ in range(steps):
        opt.zero_grad()
        pr["fun"](P).sum().backward()
        opt.step()
        if sch is not None:
            sch.step()
    P1 = P.detach().clone()
    for _ in range(continue_steps):
        opt.zero_grad()
        pr["fun"](P).sum().backward()
        opt.step()
    return P1, P.detach().clone()


def newton(pr, P0, iters):
    """per-cell damped Newton (Levenberg-Marquardt). The objective is a sum of per-cell terms, so the Hessian is block diagonal; block (c) column j = d g_c / d P_cj."""
    import torch
    P = P0.detach().clone()
    C, p = P.shape
    lam = torch.full((C,), 1e-3, dtype=P.dtype)
    n_it = 0
    for it in range(iters):
        Pv = P.clone().requires_grad_(True)
        f = pr["fun"](Pv)
        g = torch.autograd.grad(f.sum(), Pv, create_graph=True)[0]
        H = torch.stack([torch.autograd.grad(g[:, j].sum(), Pv, retain_graph=(j < p - 1))[0] for j in range(p)], dim=2).detach()
        H = 0.5 * (H + H.transpose(1, 2))
        f, g = f.detach(), g.detach()
        conv = g.norm(dim=1) <= TOL * (1.0 + f.abs())
        n_it = it
        if bool(conv.all()):
            break
        ev = torch.linalg.eigvalsh(H)
        scale = H.diagonal(dim1=1, dim2=2).abs().mean(1).clamp_min(1e-12)
        active = ~conv
        for _ in range(25):
            shift = torch.maximum(lam * scale, (-ev[:, 0]).clamp_min(0.0) + 1e-9 * scale)
            A = H + shift[:, None, None] * torch.eye(p, dtype=P.dtype)
            step = -torch.linalg.solve(A, g.unsqueeze(2))[:, :, 0]
            step = torch.where(active[:, None], step, torch.zeros_like(step))
            f_new = pr["fun"](P + step).detach()
            ok = active & torch.isfinite(f_new) & (f_new <= f)
            P = torch.where(ok[:, None], P + step, P)
            lam = torch.where(ok, (lam / 3.0).clamp_min(1e-12), torch.where(active, lam * 10.0, lam))
            active = active & ~ok
            if not bool(active.any()):
                break
    f, g = grad_of(pr, P)
    return P, n_it + 1


def hessian_eigs(pr, P):
    import torch
    Pv = P.detach().clone().requires_grad_(True)
    f = pr["fun"](Pv)
    g = torch.autograd.grad(f.sum(), Pv, create_graph=True)[0]
    p = P.shape[1]
    H = torch.stack([torch.autograd.grad(g[:, j].sum(), Pv, retain_graph=(j < p - 1))[0] for j in range(p)], dim=2).detach()
    return torch.linalg.eigvalsh(0.5 * (H + H.transpose(1, 2))).numpy()


# ============================================================================================ one (fold, arm) unit
def starts(pr, key, kind):
    import torch
    C, p, sd = pr["C"], pr["p"], pr["sd"]
    out = [np.zeros((C, p))]
    if kind == "spread":            # as P6b: z ~ N(0, 0.5^2), delta ~ N(0, TAU^2)
        for j in range(3):
            r = np.random.default_rng(list(key) + [j])
            out.append(r.normal(0.0, 1.0, size=(C, p)) * np.where(sd == 1.0, 0.5, sd))
    elif kind == "SA":              # prior mode +- 1 prior sd along each axis
        for j in range(p):
            for s in (1.0, -1.0):
                a = np.zeros((C, p))
                a[:, j] = s * sd[j]
                out.append(a)
    elif kind == "SB":
        for j in range(4):
            r = np.random.default_rng(list(key) + [100 + j])
            out.append(r.normal(0.0, 1.0, size=(C, p)) * sd)
    return [torch.tensor(a, dtype=pr["dt"]) for a in out]


def maxabs_pp(pa, pb, ids):
    return np.array([100.0 * float(np.max(np.abs(np.asarray(pa[c]) - np.asarray(pb[c])))) for c in ids])


def spread_pp(preds, ids):
    return np.array([100.0 * float(np.max(np.ptp(np.stack([np.asarray(q[c]) for q in preds]), axis=0))) for c in ids])


def score(preds, prep):
    from pinnkan.metrics import condition_scores, score_prepared
    cs = condition_scores(score_prepared(preds, prep))
    return float(np.mean(list(cs.values())))


def unit(fold, arm_id, out_dir, smoke=False):
    import torch
    import p6b_inner_folds as P
    from pinnkan.arms import make_arm
    from pinnkan.data import prepare_many
    t0, c0 = time.time(), time.process_time()
    D = P.fold_data(fold, CFG)
    spec, rule, train = D["spec"], D["rule"], D["train"]
    tb = json.load(open(os.path.join(P6B, "units", f"tournament_f{fold}_k2.json")))
    hp = json.load(open(os.path.join(P6B, "units", f"f{fold}_k2_{arm_id}.json")))["tuning"]["best_hp"]
    ctx = P.make_ctx(dict(CFG, steps_scale=0.05 if smoke else 1.0), rule, tb["chosen"])
    arm = make_arm(arm_id, spec, hp, 0, ctx).fit(train)
    prep = prepare_many(D["test"], rule)
    if smoke:
        prep = prep[:12]
    wcells = [p.win for p in prep]
    prod_pred = arm.predict(wcells)                                   # the production code path itself
    caps = {"O0": 3 if smoke else PROD[arm_id], "O1": 20 if smoke else CAPS["O1"], "O2": 4 if smoke else CAPS["O2"]}
    key = [20261106, 23, fold, ARMS.index(arm_id)]
    pr32 = problem(arm_id, arm.model, spec, wcells, hp, "f32")
    pr64 = problem(arm_id, arm.model, spec, wcells, hp, "f64")
    ids, keep = pr64["ids"], ~pr64["ref_only"]
    f64 = lambda Pm: pr64["fun"](torch.as_tensor(Pm, dtype=torch.float64)).detach().numpy()
    res = {"fold": fold, "arm": arm_id, "hp": hp, "backbone": tb["chosen"], "n_cells": len(ids), "n_ref_only": int((~keep).sum()), "p": pr64["p"], "caps": caps,
           "audit": D["audit"], "ids": ids}
    out = {}
    # ---- O0 production replica (float32 Adam lr 0.05, continued for the doubled budget)
    runs = []
    for j, S in enumerate(starts(pr32, key, "spread")):
        P1, P2 = adam(pr32, S, caps["O0"], 0.05, continue_steps=caps["O0"])
        runs.append((P1, P2))
    pm = runs[0]
    preds = [pr32["predict"](r[0]) for r in runs]
    out["O0"] = dict(f=f64(pm[0].double()), g=grad_of(pr64, pm[0].double())[1].norm(dim=1).numpy(), budget=maxabs_pp(preds[0], pr32["predict"](pm[1]), ids),
                     spread=spread_pp(preds, ids), score=score(preds[0], prep), replica_vs_production_pp=float(maxabs_pp(preds[0], prod_pred, ids).max()), P=pm[0].double())
    # ---- O1 Adam float64, cosine-decayed lr, cap and a fresh doubled run
    preds, P1s = [], []
    for j, S in enumerate(starts(pr64, key, "spread")):
        P1, _ = adam(pr64, S, caps["O1"], 0.05, schedule="cosine", eta_min=5e-4)
        P1s.append(P1)
        preds.append(pr64["predict"](P1))
        if time.process_time() - c0 > CPU_ABORT_H * 3600 / 3:
            raise RuntimeError("cpu guard (unit share) reached in O1")
    P2, _ = adam(pr64, starts(pr64, key, "spread")[0], 2 * caps["O1"], 0.05, schedule="cosine", eta_min=5e-4)
    f, g = grad_of(pr64, P1s[0])
    out["O1"] = dict(f=f.numpy(), g=g.norm(dim=1).numpy(), conv=(g.norm(dim=1) <= TOL * (1 + f.abs())).numpy(), budget=maxabs_pp(preds[0], pr64["predict"](P2), ids),
                     spread=spread_pp(preds, ids), score=score(preds[0], prep), P=P1s[0])
    # ---- O2 damped Newton from the spread starts; doubled cap from the prior mode
    preds, Ps, its = [], [], []
    for S in starts(pr64, key, "spread"):
        Pn, n = newton(pr64, S, caps["O2"])
        Ps.append(Pn)
        its.append(n)
        preds.append(pr64["predict"](Pn))
    P2, _ = newton(pr64, starts(pr64, key, "spread")[0], 2 * caps["O2"])
    f, g = grad_of(pr64, Ps[0])
    ev = hessian_eigs(pr64, Ps[0])
    out["O2"] = dict(f=f.numpy(), g=g.norm(dim=1).numpy(), conv=(g.norm(dim=1) <= TOL * (1 + f.abs())).numpy(), budget=maxabs_pp(preds[0], pr64["predict"](P2), ids),
                     spread=spread_pp(preds, ids), score=score(preds[0], prep), iters=its, P=Ps[0],
                     hess_min=ev[:, 0], hess_max=ev[:, -1])
    # ---- O3 multi-start O2 with per-cell selection by the objective; S_A against S_B
    sel = {}
    for kind in ("SA", "SB"):
        Ps_k = [Ps[0]] + [newton(pr64, S, caps["O2"])[0] for S in starts(pr64, key, kind)[1:]]
        F = np.stack([f64(Pk) for Pk in Ps_k])
        best = F.argmin(0)
        Psel = torch.stack([Ps_k[best[c]][c] for c in range(pr64["C"])])
        sel[kind] = dict(P=Psel, f=F.min(0), pred=pr64["predict"](Psel), best_index=best, f_range=F.max(0) - F.min(0))
    out["O3"] = dict(f=sel["SA"]["f"], spread=maxabs_pp(sel["SA"]["pred"], sel["SB"]["pred"], ids), score=score(sel["SA"]["pred"], prep),
                     share_not_prior_mode=float(np.mean(sel["SA"]["best_index"] != 0)), f_range_SA_median=float(np.median(sel["SA"]["f_range"])), P=sel["SA"]["P"],
                     changed_vs_O2_pp=maxabs_pp(sel["SA"]["pred"], preds[0], ids))
    # ---- changes against production (A2 criterion e) and per-cell objective deltas
    for k in ("O1", "O2", "O3"):
        out[k]["change_vs_O0_pp"] = maxabs_pp(pr64["predict"](out[k]["P"]), out["O0"] and pr32["predict"](out["O0"]["P"].float()), ids)
        out[k]["f_minus_O0"] = np.asarray(out[k]["f"]) - np.asarray(out["O0"]["f"])
    for k in out:
        out[k].pop("P", None)
        for a in list(out[k]):
            if isinstance(out[k][a], np.ndarray) and out[k][a].shape == (len(ids),):
                out[k][a] = out[k][a][keep]          # k = 0-like cells (one window point) are set to the prior by production; excluded from every criterion
    res.update(methods=out, cpu_seconds=time.process_time() - c0, wall_seconds=time.time() - t0)
    jdump(res, os.path.join(out_dir, "units", f"f{fold}_{arm_id}.json"))
    return res["cpu_seconds"]


def cmd_run(a):
    import torch
    torch.set_num_threads(1)
    os.makedirs(os.path.join(a.out, "units"), exist_ok=True)
    if not a.smoke:
        assert os.path.abspath(a.out).startswith(os.path.join(ROOT, "runs")), "main run writes under runs/"
        meta = {"head": git("rev-parse", "HEAD"), "script_last_commit": git("log", "-1", "--format=%H %cI", "--", "code/pilots/d023_inversion_check.py"),
                "dirty_script": git("status", "--short", "code/pilots/d023_inversion_check.py"), "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "folds": a.folds}
        assert meta["dirty_script"] == "", "commit the script (and the rule) before the main run"
        jdump(meta, os.path.join(a.out, f"meta_folds_{'_'.join(map(str, a.folds))}.json"))
    c0 = time.process_time()
    folds = a.folds[:1] if a.smoke else a.folds
    for fold in folds:
        for arm_id in ARMS:
            if os.path.exists(os.path.join(a.out, "units", f"f{fold}_{arm_id}.json")):
                continue
            if time.process_time() - c0 > CPU_ABORT_H * 3600:
                print("CPU guard reached; stopping (incomplete)", flush=True)
                return
            try:
                cpu = unit(fold, arm_id, a.out, smoke=a.smoke)
                print(f"fold {fold} {arm_id} done, {cpu:.0f} cpu-s", flush=True)
            except Exception as e:  # noqa: BLE001
                import traceback
                jdump({"fold": fold, "arm": arm_id, "error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()}, os.path.join(a.out, "units", f"ERROR_f{fold}_{arm_id}.json"))
                print(f"fold {fold} {arm_id} ERROR {e}", flush=True)


def cmd_aggregate(a):
    U = {}
    for fold in range(5):
        for arm_id in ARMS:
            p = os.path.join(a.out, "units", f"f{fold}_{arm_id}.json")
            if os.path.exists(p):
                U[(fold, arm_id)] = json.load(open(p))
    complete = len(U) == 15
    cat = lambda arm, meth, key: np.concatenate([np.asarray(U[(f, arm)]["methods"][meth][key], float) for f in range(5) if (f, arm) in U])
    q = lambda v, p: float(np.percentile(v, p)) if len(v) else float("nan")
    table, checks = {}, {}
    for arm in ARMS:
        for meth in ("O0", "O1", "O2", "O3"):
            row = {}
            if not any((f, arm) in U for f in range(5)):
                continue
            sp = cat(arm, meth, "spread")
            row.update(spread_median=q(sp, 50), spread_p95=q(sp, 95), spread_max=float(sp.max()))
            if meth in ("O0", "O1", "O2"):
                b = cat(arm, meth, "budget")
                row.update(budget_median=q(b, 50), budget_p99=q(b, 99), budget_max=float(b.max()))
                g = cat(arm, meth, "g")
                row.update(grad_median=q(g, 50), grad_max=float(g.max()))
            if meth in ("O1", "O2"):
                row["conv_share"] = float(cat(arm, meth, "conv").mean())
            if meth == "O3":
                row["share_not_prior_mode"] = [U[(f, arm)]["methods"]["O3"]["share_not_prior_mode"] for f in range(5) if (f, arm) in U]
            if meth != "O0":
                row["f_minus_O0_median"] = q(cat(arm, meth, "f_minus_O0"), 50)
                ch = cat(arm, meth, "change_vs_O0_pp")
                row.update(change_vs_O0_median=q(ch, 50), change_vs_O0_p99=q(ch, 99), change_vs_O0_max=float(ch.max()))
            if meth == "O2":
                hm, hx = cat(arm, meth, "hess_min"), cat(arm, meth, "hess_max")
                row.update(hess_min_median=q(hm, 50), share_hess_min_nonpos=float(np.mean(hm <= 0)), cond_median=q(hx / np.maximum(hm, 1e-300), 50))
            row["score_pp_by_fold_descriptive"] = [U[(f, arm)]["methods"][meth]["score"] for f in range(5) if (f, arm) in U]
            table[f"{arm}|{meth}"] = row
    R = RULE
    verdict = "NONE"
    for meth in R["order"]:
        ok = complete
        why = []
        base = "O2" if meth == "O3" else meth
        for arm in R["arms_gated"]:
            t, tb = table[f"{arm}|{meth}"], table[f"{arm}|{base}"]
            cond = {"a": tb["conv_share"] >= R["a_conv_share_min"],
                    "b": tb["budget_p99"] <= R["b_budget_p99_max_pp"] and tb["budget_max"] <= R["b_budget_max_pp"],
                    "c": t["spread_median"] <= R["c_spread_median_max_pp"] and t["spread_p95"] <= R["c_spread_p95_max_pp"],
                    "d": t["f_minus_O0_median"] <= R["d_objective_median_delta_max"]}
            why.append({arm: cond})
            ok = ok and all(cond.values())
        e = table[f"A2|{meth}"]["change_vs_O0_p99"] <= R["e_A2_change_p99_max_pp"]
        why.append({"A2_e": e})
        ok = ok and e
        checks[meth] = {"pass": bool(ok), "conditions": why}
        if ok:
            verdict = f"ADOPT_{meth}"
            break
    res = {"complete": complete, "units": len(U), "verdict": verdict, "checks": checks, "rule": R, "table": table,
           "cpu_hours": float(sum(u["cpu_seconds"] for u in U.values()) / 3600.0),
           "replica_vs_production_pp_max": {arm: max(U[(f, arm)]["methods"]["O0"]["replica_vs_production_pp"] for f in range(5) if (f, arm) in U) for arm in ARMS},
           "note": "development data (ISU training sides); the scores are descriptive and carry no rule"}
    jdump(res, os.path.join(a.out, "decision.json"))
    print(json.dumps({"verdict": verdict, "complete": complete, "cpu_hours": res["cpu_hours"]}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "aggregate"])
    ap.add_argument("--out", default=os.path.join(ROOT, "runs", "check_D023_inversion"))
    ap.add_argument("--folds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    a.out = os.path.abspath(a.out)
    if a.smoke:
        assert not a.out.startswith(os.path.join(ROOT, "runs")), "the smoke test never writes under runs/"
    cmd_run(a) if a.cmd == "run" else cmd_aggregate(a)


if __name__ == "__main__":
    main()
