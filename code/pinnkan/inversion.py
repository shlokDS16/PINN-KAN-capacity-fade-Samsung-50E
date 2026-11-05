"""Test-time latent inversion: ONE routine for every inverting arm (D023 judge sections 2-3; PREREG_v4 7.5).

    invert_latents(fun, P0)   per-cell Levenberg-Marquardt Newton, float64, started at the prior mode, stopped per cell by ||g_c|| <= TOL (1 + |f_c|) or at CAP iterations; accepted steps
                              never raise a cell's objective; a non-converged cell keeps its last accepted iterate and is COUNTED (not dropped, not re-run, no multi-start); no randomness.

    pinn_problem   A1, A4, A5, A13, A15, G15 : window points + A1's residual over (window end, t_max] with per-cell seeded collocation draws + priors on (z, delta)
    data_problem   A9                         : window points + prior on z
    hard_problem   A2 (and the backbone tournament) : window points + prior on delta

Each problem returns a dict with the per-cell objective `fun(P)` (C,), the prior mode `P0` (C, p), `p`, `C`, the cells whose window holds the reference point only (`ref_only`: they keep
the prior mode, k = 0 rule), and `split(P)` -> the arm's latents. The z-prior weight is `Z_PRIOR_WEIGHT` = 1: the weight of the training loss (fit_pinn: (z^2).sum()/n against the mean data
term; fit_data_only: the same), so the test-time objective is the posterior of the model that was fitted. It is a constant, not a tuned value; the argument `z_weight` exists only for the
descriptive sensitivity row (vi) (weights 4 and 16, inference only, no refit).

The constants live in ONE frozen config object (`CONFIG`); `config_dict()` / `config_sha256()` are what the config hash pins. Nothing here reads a label after the window."""
import copy
import dataclasses
import hashlib
import json
import zlib

import numpy as np
import torch


@dataclasses.dataclass(frozen=True)
class InversionConfig:
    tol: float = 1e-6              # converged iff ||grad_c|| <= tol (1 + |f_c|)
    cap: int = 100                 # iterations
    lam0: float = 1e-3             # initial LM damping (relative to the mean |diagonal| of the cell's Hessian)
    lam_min: float = 1e-12
    lam_up: float = 10.0           # damping after a rejected step
    lam_down: float = 3.0          # damping division after an accepted step
    max_backtrack: int = 25        # damping increases tried per iteration
    eig_floor: float = 1e-9        # positive-definiteness shift floor (relative)
    dtype: str = "float64"
    z_prior_weight: float = 1.0
    n_col: int = 16                # collocation points per cell for A1's residual over the horizon


CONFIG = InversionConfig()
Z_PRIOR_WEIGHT = CONFIG.z_prior_weight
TOL, CAP = CONFIG.tol, CONFIG.cap
_DT = torch.float64

TAG = {}                           # set by the run writer around each predict call: {"arm": ..., "k": ..., "seed": ...}; copied into every log record
LOG = []                           # one dict per inversion call (arm, n_cells, n_nonconverged, ...); drained by run.py into diagnostics.json


def config_dict():
    return dataclasses.asdict(CONFIG)


def config_sha256():
    return hashlib.sha256(json.dumps(config_dict(), sort_keys=True).encode()).hexdigest()


@dataclasses.dataclass
class InversionResult:
    P: torch.Tensor                # (C, p) final iterate
    f: torch.Tensor                # (C,) final objective
    gnorm: torch.Tensor            # (C,) final gradient norm
    converged: torch.Tensor        # (C,) bool
    n_iter: int


def _grad_hess(fun, P, p):
    Pv = P.clone().requires_grad_(True)
    f = fun(Pv)
    g = torch.autograd.grad(f.sum(), Pv, create_graph=True)[0]
    H = torch.stack([torch.autograd.grad(g[:, j].sum(), Pv, retain_graph=(j < p - 1))[0] for j in range(p)], dim=2).detach()
    return f.detach(), g.detach(), 0.5 * (H + H.transpose(1, 2))


def _fg(fun, P):
    Pv = P.clone().requires_grad_(True)
    f = fun(Pv)
    g = torch.autograd.grad(f.sum(), Pv)[0]
    return f.detach(), g.detach()


def invert_latents(fun, P0, config=CONFIG, cap=None):
    """Per-cell damped Newton (Levenberg-Marquardt) on the exact per-cell Hessian. `fun(P)` maps (C, p) float64 latents to the (C,) per-cell objective, a sum of per-cell terms (so the
    Hessian is block diagonal). Start P0 (the prior mode). Accepted steps never raise a cell's objective; a cell whose damped step cannot lower it stays where it is."""
    cfg = config
    cap = cfg.cap if cap is None else int(cap)
    P = P0.detach().clone().to(_DT)
    C, p = P.shape
    lam = torch.full((C,), cfg.lam0, dtype=_DT)
    eye = torch.eye(p, dtype=_DT)
    n_it = 0
    for it in range(cap):
        f, g, H = _grad_hess(fun, P, p)
        conv = g.norm(dim=1) <= cfg.tol * (1.0 + f.abs())
        if bool(conv.all()):
            break
        n_it += 1
        ev = torch.linalg.eigvalsh(H)
        scale = H.diagonal(dim1=1, dim2=2).abs().mean(1).clamp_min(1e-12)
        active = ~conv
        for _ in range(cfg.max_backtrack):
            shift = torch.maximum(lam * scale, (-ev[:, 0]).clamp_min(0.0) + cfg.eig_floor * scale)
            A = H + shift[:, None, None] * eye
            step = -torch.linalg.solve(A, g.unsqueeze(2))[:, :, 0]
            step = torch.where(active[:, None], step, torch.zeros_like(step))
            f_new = fun(P + step).detach()
            ok = active & torch.isfinite(f_new) & (f_new <= f)
            P = torch.where(ok[:, None], P + step, P)
            lam = torch.where(ok, (lam / cfg.lam_down).clamp_min(cfg.lam_min), torch.where(active, lam * cfg.lam_up, lam))
            active = active & ~ok
            if not bool(active.any()):
                break
    f, g = _fg(fun, P)
    gn = g.norm(dim=1)
    return InversionResult(P, f, gn, gn <= cfg.tol * (1.0 + f.abs()), n_it)


def log_result(arm, res, ref_only=None, extra=None):
    keep = torch.ones(res.P.shape[0], dtype=torch.bool) if ref_only is None else torch.as_tensor(~np.asarray(ref_only))
    n = int(keep.sum())
    rec = {"arm": TAG.get("arm", arm), "kind": arm, "k": TAG.get("k"), "seed": TAG.get("seed"), "n_cells": int(res.P.shape[0]), "n_inverted": n, "n_nonconverged": int((~res.converged & keep).sum()), "convergence_share": (float((res.converged & keep).sum()) / n) if n else 1.0,
           "gnorm_max": float(res.gnorm[keep].max()) if n else 0.0, "n_iter": int(res.n_iter), "nonfinite": int((~torch.isfinite(res.P)).any(1).sum())}
    if extra:
        rec.update(extra)
    LOG.append(rec)
    return rec


def drain_log():
    out = list(LOG)
    LOG.clear()
    return out


def pooled_convergence(records):
    """pooled convergence share and counts over logged inversions"""
    n = sum(r["n_inverted"] for r in records)
    bad = sum(r["n_nonconverged"] for r in records)
    return {"n_inverted": n, "n_nonconverged": bad, "convergence_share": (1.0 - bad / n) if n else 1.0, "n_calls": len(records)}


# ------------------------------------------------------------------------------------------------ per-arm problems (the production per-cell losses, written per cell)
def _to64_batch(b):
    rep = {f.name: getattr(b, f.name).double() for f in dataclasses.fields(b) if isinstance(getattr(b, f.name), torch.Tensor) and getattr(b, f.name).is_floating_point()}
    return dataclasses.replace(b, **rep)


def _freeze64(model):
    m = copy.deepcopy(model).double()
    for q in m.parameters():
        q.requires_grad_(False)
    return m


def _ref_only(bw):
    return (torch.bincount(bw.obs_cell, minlength=bw.C) <= 1).numpy()


def pinn_problem(m, bw, bq, lam, seed, n_col=CONFIG.n_col, z_weight=None):
    """A1 family. The objective per cell: (sum of squared window errors + lam * pts_per_cell / n_col * sum of squared residuals at the cell's collocation points) / SIGMA^2
    + (delta - mu)^2 / TAU^2 + z_weight * |z|^2, with mu the (indicator) prior mean of delta; the collocation draws are seeded by (seed, cell id)."""
    from . import pinn as _pinn
    from .law import SIGMA
    zw = Z_PRIOR_WEIGHT if z_weight is None else float(z_weight)
    mm = _freeze64(m)
    bw, bq = _to64_batch(bw), (None if bq is None else _to64_batch(bq))
    spec, C, zd = m.spec, bw.C, m.zdim
    mu = (mm.prior_mean(bw.ind).detach() if (m.beta is not None and bw.ind is not None) else torch.zeros(C, dtype=_DT))
    u = torch.tensor(np.stack([np.random.default_rng([int(seed), zlib.crc32(cid.encode())]).random(n_col) for cid in bw.ids]), dtype=_DT)
    tc = bw.t_end.unsqueeze(1) + u * (mm.col_t_max - bw.t_end).clamp_min(0.0).unsqueeze(1)
    to_n = spec.t_scale / spec.efc_scale
    nu = torch.stack([torch.tensor(bw.curves[c].rate(tc[c].numpy() * spec.t_scale) * to_n, dtype=_DT) for c in range(C)])
    cc = torch.arange(C).unsqueeze(1).expand(C, n_col).reshape(-1)
    tc, nu = tc.reshape(-1), nu.reshape(-1)
    pts = mm.pts_per_cell
    tau = _pinn.TAU

    def fun(P):
        z, delta = P[:, :zd], P[:, zd]
        F = mm.F(bw.obs_t, bw.s[bw.obs_cell], z[bw.obs_cell])
        A_cal, A_cyc = mm.law.amplitudes(bw.s, bw.is_cyc, delta)
        R = mm.residual(tc, bw.s[cc], z[cc], A_cal[cc], A_cyc[cc], nu).reshape(C, n_col)
        data = torch.zeros(C, dtype=_DT).index_add(0, bw.obs_cell, (F - bw.obs_y) ** 2)
        return (data + lam * pts / n_col * (R ** 2).sum(1)) / SIGMA ** 2 + (delta - mu) ** 2 / tau ** 2 + zw * (z ** 2).sum(1)

    P0 = torch.cat([torch.zeros(C, zd, dtype=_DT), mu[:, None]], dim=1)

    def predict(P):
        from .hard import split_by_cell
        from .law import retention_from_y
        with torch.no_grad():
            y = mm.F(bq.obs_t, bq.s[bq.obs_cell], P[:, :zd][bq.obs_cell])
        return {k: retention_from_y(spec, v) for k, v in split_by_cell(bq, y).items()}
    return {"fun": fun, "P0": P0, "p": zd + 1, "C": C, "ref_only": _ref_only(bw), "ids": list(bw.ids), "predict": predict, "sd": np.array([1.0] * zd + [tau]), "kind": "pinn",
            "split": lambda P: (P[:, :zd], P[:, zd])}


def data_problem(m, bw, bq, z_weight=None):
    """A9: sum of squared window errors / SIGMA^2 + z_weight * |z - z_prior_mean|^2 (the training loss weights z the same way)."""
    from .law import SIGMA
    zw = Z_PRIOR_WEIGHT if z_weight is None else float(z_weight)
    mm = _freeze64(m)
    bw, bq = _to64_batch(bw), (None if bq is None else _to64_batch(bq))
    spec, C, zd = m.spec, bw.C, m.zdim
    zmu = (torch.as_tensor(mm.z_prior(bw.ind)).detach() * torch.ones(C, zd, dtype=_DT)) if (m.B is not None and bw.ind is not None) else torch.zeros(C, zd, dtype=_DT)

    def fun(P):
        data = torch.zeros(C, dtype=_DT).index_add(0, bw.obs_cell, (mm.F(bw.obs_t, bw.s[bw.obs_cell], P[bw.obs_cell]) - bw.obs_y) ** 2)
        return data / SIGMA ** 2 + zw * ((P - zmu) ** 2).sum(1)

    def predict(P):
        from .hard import split_by_cell
        from .law import retention_from_y
        with torch.no_grad():
            y = mm.F(bq.obs_t, bq.s[bq.obs_cell], P[bq.obs_cell])
        return {k: retention_from_y(spec, v) for k, v in split_by_cell(bq, y).items()}
    return {"fun": fun, "P0": zmu.clone(), "p": zd, "C": C, "ref_only": _ref_only(bw), "ids": list(bw.ids), "predict": predict, "sd": np.array([1.0] * zd), "kind": "data", "split": lambda P: (P, None)}


def hard_problem(m, bw, bq=None):
    """A2: sum of squared window errors / SIGMA^2 + (delta - mu)^2 / TAU^2 (TAU read at call time: sensitivity row (m) is A2-only)."""
    from . import law as _law
    from .law import SIGMA
    mm = _freeze64(m)
    bw = _to64_batch(bw)
    C = bw.C
    mu = (mm.prior_mean(bw.ind).detach() if (m.beta is not None and bw.ind is not None) else torch.zeros(C, dtype=_DT))
    tau = _law.TAU

    def fun(P):
        d = P[:, 0]
        data = torch.zeros(C, dtype=_DT).index_add(0, bw.obs_cell, (mm.predict_y(bw, d) - bw.obs_y) ** 2)
        return data / SIGMA ** 2 + (d - mu) ** 2 / tau ** 2

    bq64 = None if bq is None else _to64_batch(bq)

    def predict(P):
        from .hard import split_by_cell
        from .law import retention_from_y
        with torch.no_grad():
            y = mm.predict_y(bq64, P[:, 0])
        return {k: retention_from_y(m.spec, v) for k, v in split_by_cell(bq64, y).items()}
    return {"fun": fun, "P0": mu[:, None].clone(), "p": 1, "C": C, "ref_only": _ref_only(bw), "ids": list(bw.ids), "sd": np.array([tau]), "kind": "hard", "predict": predict if bq is not None else None,
            "split": lambda P: (None, P[:, 0])}


def solve(prob, arm, cap=None, P0=None, config=CONFIG, log=True):
    """run the routine on a problem; cells with a reference-only window keep the prior mode (k = 0 rule). -> (InversionResult with P overwritten for those cells)"""
    start = prob["P0"] if P0 is None else P0
    res = invert_latents(prob["fun"], start, config, cap)
    ro = torch.as_tensor(prob["ref_only"])
    if bool(ro.any()):
        res.P[ro] = prob["P0"][ro]
    if log:
        log_result(arm, res, prob["ref_only"])
    return res
