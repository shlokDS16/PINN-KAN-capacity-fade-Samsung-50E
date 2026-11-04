"""H7 identifiability driver (PREREG_v2 section 13): generators G0-G2 x draws x arms A1, A2, A4, A8. Synthetic only.

Per draw: generate the dataset (truth never from a fit), compute the additive-GAM class floor of the TRUE log-rate surface before any fit (validity rule: a G2
draw discriminates only if the floor exceeds 0.15), hold out cycling conditions, tune every arm on the training conditions only (`n_trials` x `inner_k`, equal for
all arms; pilot effort 8 x 2 in the prereg), refit at the tuned settings, then evaluate on the fixed 500-point Latin hypercube inside the convex hull of the
training cycling design: nRMSE = RMSE(estimated - true log-rate) / range(true) (level included; centred value alongside) and the forecast RMSE on the held-out
conditions. Output: <run>/summary.json and <run>/surfaces_<gen>.npz (lhs raw stress, f_true and f_<arm>, centred, shape (draws, 500)).
Rates compared: log r_cyc of the structured arms (log_cyc + f) and, for the free G, log(G(y=0) / nu) at the design throughput (approximate, see free.log_rate_surface)."""
import json
import os

import numpy as np
import torch

from . import free, synth, tuning
from .arms import make_arm
from .data import WindowRule, prepare_many
from .metrics import primary_score, score_prepared
from .pinn import _hull_sample
from .specs import SPECS

SPEC = SPECS["synthetic"]
ARMS_H7 = ("A1", "A2", "A4", "A8")


def additive_floor(f_true, raw):
    """RMSE of the best additive cubic fit of the true surface / its range (computed before any model is fitted)"""
    s = SPEC.norm(raw)
    A = np.column_stack([np.ones(len(s))] + [s[:, j] ** p for j in range(s.shape[1]) for p in (1, 2, 3)])
    coef, *_ = np.linalg.lstsq(A, f_true, rcond=None)
    return float(np.sqrt(np.mean((A @ coef - f_true) ** 2)) / (f_true.max() - f_true.min()))


def surface(arm, raw):
    if arm.arm_id == "A8":
        return free.log_rate_surface(arm.model, SPEC, raw)
    law = arm.model.law
    with torch.no_grad():
        return (law.log_cyc + law.cyc(torch.tensor(SPEC.norm(raw), dtype=torch.float32))).numpy()


def run_h7(out_dir, gens=("G0", "G1", "G2"), n_draws=20, arms=ARMS_H7, n_trials=8, inner_k=2, steps_scale=1.0, backbone="self_limiting", design=None):
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "SYNTHETIC"), "w").write("H7 generators: invented ageing laws\n")
    design = design or dict(n_cyc_cond=32, n_sto_cond=19, reps=3)
    rule = WindowRule.for_spec(SPEC)
    ctx = {"backbone": backbone, "steps_scale": steps_scale, "rule": rule}
    draws, surf = [], {}
    lhs_saved = None
    for g in gens:
        F = {k: [] for k in ("true",) + tuple(arms)}
        for i in range(n_draws):
            S = synth.make_synthetic(g, seed=i, backbone=backbone, **design)
            tr, te = synth.split_conditions(S.cells, 0.25, i)
            X = np.stack([SPEC.norm(c.raw) for c in tr if c.kind == "cycling"])
            lhs = SPEC.denorm(_hull_sample(X, 500, 12345))
            f_true = S.log_rate_cyc(lhs)
            floor = additive_floor(f_true, lhs)
            rng_t = float(f_true.max() - f_true.min())
            rec = dict(gen=g, draw=i, additive_floor=floor, additive_floor_discriminates=bool(floor > 0.15), nrmse={}, nrmse_centred={}, forecast_pp={}, best_hp={})
            F["true"].append(f_true - f_true.mean())
            prep = prepare_many([c for c in te if c.kind == "cycling"], rule)
            for a in arms:
                r = tuning.tune(a, tr, SPEC, rule, n_trials, inner_k, i, ctx)
                arm = make_arm(a, SPEC, r["best_hp"], 0, ctx).fit(tr)
                f = surface(arm, lhs)
                rec["nrmse"][a] = float(np.sqrt(np.mean((f - f_true) ** 2)) / rng_t)
                fc = f - f.mean()
                ft = f_true - f_true.mean()
                rec["nrmse_centred"][a] = float(np.sqrt(np.mean((fc - ft) ** 2)) / rng_t)
                rec["forecast_pp"][a] = primary_score(score_prepared(arm.predict([p.win for p in prep]), prep))
                rec["best_hp"][a] = r["best_hp"]
                F[a].append(fc)
            draws.append(rec)
            lhs_saved = lhs
        surf[g] = {k: np.stack(v) for k, v in F.items()}
        np.savez(os.path.join(out_dir, f"surfaces_{g}.npz"), lhs=lhs_saved, **{f"f_{k}": v for k, v in surf[g].items()})
    summ = dict(synthetic=True, thresholds=dict(pass_=0.15, fail=0.30), n_draws=n_draws, arms=list(arms), gens=list(gens), n_trials=n_trials, inner_k=inner_k,
                steps_scale=steps_scale, design=design, draws=draws)
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf8") as fh:
        json.dump(summ, fh, indent=1)
    return summ
