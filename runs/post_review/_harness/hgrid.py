"""Item 6 (D048): discrete h(y) scale grid for A2 and A1, and the inner-fold choice over the grid ("learned per fold" only in the sense of a discrete choice). POST-HOC, EXPLORATORY.
law.overrides(Y0=, gamma=) is the frozen context manager (law.py:40); ctx['backbone'] sets the form."""
import os

import numpy as np

import harness as H
from pinnkan import law, tuning
from pinnkan.arms import TOURNAMENT_HP
from pinnkan.metrics import condition_scores

# member -> (backbone, overrides); order = simplicity order of the extended tournament (constant, then Y0 descending, then gamma ascending)
H_MEMBERS = {"const": ("constant", {}), "sl4": ("self_limiting", {"Y0": 4.0}), "sl2": ("self_limiting", {"Y0": 2.0}), "sl1": ("self_limiting", {"Y0": 1.0}), "sl0.5": ("self_limiting", {"Y0": 0.5}),
             "acc0.15": ("accelerating", {"gamma": 0.15}), "acc0.3": ("accelerating", {"gamma": 0.3}), "acc0.6": ("accelerating", {"gamma": 0.6})}
FROZEN_MEMBER = {"constant": "const", "self_limiting": "sl1", "accelerating": "acc0.3"}      # frozen defaults: Y0 = 1, gamma = 0.3
VARIANTS = [f"{arm}_{k}" for arm in ("A2", "A1") for k in H_MEMBERS] + ["TOURN"]


def build(variant, f, m):
    if variant == "TOURN":
        return {"custom": tournament}
    arm, key = variant.split("_", 1)
    bb, ov = H_MEMBERS[key]
    Hd = H.load_fold(f, m)
    cm = (lambda: law.overrides(**ov))
    if arm == "A2":
        return dict(arm_name="A2", config={"member": key, "backbone": bb, "overrides": ov, "hyperparameters": "A2 as tuned (tuning_A2.json)"}, diag=False, cm=cm,
                    make_fit=lambda spec, hp, sd, ctx: H.make_arm("A2", spec, hp["A2"], sd, dict(ctx, backbone=bb)))
    if FROZEN_MEMBER[Hd["backbone"]] == key:
        return None             # this member is the fold's frozen backbone: A1 as frozen (the L0 reference rerun of item 2 reproduces it)
    return dict(arm_name="A1", config={"member": key, "backbone": bb, "overrides": ov, "hyperparameters": "A1 as tuned (tuning_A1.json)"}, diag=True, cm=cm,
                make_fit=lambda spec, hp, sd, ctx: H.A1x(spec, hp["A1"], sd, dict(ctx, backbone=bb)))


def tournament(exp, variant, f, m):
    """the frozen backbone tournament (tuning.py:118-132: A2 at TOURNAMENT_HP on the inner folds of the TRAINING conditions, simplest member within one SE of the best) extended to the 8 members.
    Also the distribution of the retention loss at the last scored check-up of the held-out cells (descriptive; those are the labels the frozen scoring already read)."""
    jd = H.job_dir(exp, variant, f, m)
    H.assert_out(os.path.join(jd, "x"))
    os.makedirs(jd, exist_ok=True)
    Hd = H.load_fold(f, m)
    cfg, ctx, spec, train = Hd["cfg"], Hd["ctx"], Hd["spec"], Hd["train"]
    rule_tune, inner_k, tk = ctx["rule"], cfg["inner_k"], cfg["target_kind"]
    seed = 1000 + int(f)
    fold_of = tuning.inner_folds(train, inner_k, seed, spec, tk)
    table = {}
    for key, (bb, ov) in H_MEMBERS.items():
        with law.overrides(**ov):
            rows, _ = tuning.cv_rows("A2", TOURNAMENT_HP, train, fold_of, inner_k, spec, rule_tune, seed, dict(ctx, backbone=bb), tk)
        v = np.array(list(condition_scores(rows).values()))
        table[key] = {"mean_pp": float(v.mean()) if len(v) else float("nan"), "se_pp": float(v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else 0.0, "n_conditions": int(len(v))}
    ok = {k: r for k, r in table.items() if np.isfinite(r["mean_pp"])}
    best = min(ok, key=lambda k: ok[k]["mean_pp"])
    thr = ok[best]["mean_pp"] + ok[best]["se_pp"]
    chosen = next(k for k in H_MEMBERS if k in ok and ok[k]["mean_pp"] <= thr)
    frozen = json.load(open(os.path.join(Hd["src"], "backbone_tournament.json"), encoding="utf8"))
    chk = {}
    for bb, key in FROZEN_MEMBER.items():
        fr = frozen["table"][bb]
        chk[key] = {"frozen_mean_pp": fr["mean_pp"], "harness_mean_pp": table[key]["mean_pp"], "abs_diff": abs(fr["mean_pp"] - table[key]["mean_pp"])}
    kp = H.KSEL[m]
    last = []
    for p in Hd["KC"][kp]["prep"]:
        last.append(float(spec.y_scale * (1.0 - p.fc_true[-1])))
    last = np.array(last)
    yd = {"n_cells": int(last.size), "y_s_last_checkup_quantiles_0_25_50_75_100": [float(x) for x in np.quantile(last, [0, 0.25, 0.5, 0.75, 1.0])],
          "y_s_unit": f"spec.y_scale (= {spec.y_scale}) x (1 - retention); Y0 = 1 in these units", "share_y_s_above_0.5": float(np.mean(last > 0.5)), "share_y_s_above_1": float(np.mean(last > 1.0))}
    H.wjson(os.path.join(jd, "tournament.json"), {"fold": f, "m": m, "inner_k": inner_k, "order_simplest_first": list(H_MEMBERS), "table": table, "best": best, "chosen": chosen,
                                                   "rule": "simplest member (order above) whose inner-CV mean is within one SE of the best member's mean; training conditions only; A2 at TOURNAMENT_HP",
                                                   "frozen_tournament_choice": frozen["chosen"], "frozen_members_reproduced": chk, "last_checkup_y_distribution": yd})
    H.wjson(os.path.join(jd, "condition_scores.json"), {"_note": "marker file; the tournament holds no outer-test score"})
    return jd


import json  # noqa: E402
