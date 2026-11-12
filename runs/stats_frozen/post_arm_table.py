"""D046: post-freeze recompute of the descriptive G1 arm table (Table 1 inputs), which failed in the frozen step with
TypeError (np.mean over None values of n_params / n_train_used / fit seconds for arms that record none).
The frozen code is not edited: this script copies stats_gaps._pool_blocks with one change (a None-valued count field
gives None instead of raising) and calls the frozen arm_table with it. Descriptive only; sets no tier, state, title,
count or gate input. Run from the main checkout:
  .venv/Scripts/python.exe -P runs/stats_frozen/post_arm_table.py
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
from pinnkan import stats_gaps as sg  # noqa: E402

R = os.path.join(ROOT, "runs")


def _mean_or_none(vals):
    return None if any(v is None for v in vals) else float(np.mean(vals))


def _range_or_none(vals):
    return None if any(v is None for v in vals) else [min(vals), max(vals)]


def pool_blocks_tolerant(blocks):
    res = {}
    for a in sorted({a for b in blocks for a in b}):
        bb = [b[a] for b in blocks if a in b]
        n = np.array([x["n_conditions"] for x in bb], float)
        if not n.sum():
            continue
        w = n / n.sum()
        sd = np.array([np.nan if x.get("seed_sd_of_mean") is None else float(x["seed_sd_of_mean"]) for x in bb])
        per_seed = [x.get("primary_pp_per_seed") for x in bb]
        npar = [x.get("n_params") for x in bb]
        ntr = [x.get("n_train_used") for x in bb]
        fs = [x.get("fit_seconds_one_fit") for x in bb]
        res[a] = dict(mean_pp=float(np.sum(w * [x["primary_pp"] for x in bb])),
                      mean_pp_per_seed=(float(np.sum(w * per_seed)) if all(v is not None for v in per_seed) else None),
                      seed_sd_pp=float(np.sqrt(np.sum((w * sd) ** 2))) if not np.isnan(sd).any() else None,
                      seed_sd_pp_upper_bound=float(np.sum(w * sd)) if not np.isnan(sd).any() else None,
                      n_conditions=int(n.sum()), n_folds=len(bb),
                      n_params=_mean_or_none(npar), n_params_range=_range_or_none(npar),
                      n_train_used=_mean_or_none(ntr), n_train_used_range=_range_or_none(ntr),
                      fit_seconds=_mean_or_none(fs),
                      fit_seconds_ensemble=(float(np.mean([x["fit_seconds_ensemble"] for x in bb]))
                                            if all(x.get("fit_seconds_ensemble") is not None for x in bb) else None))
    return res


def main():
    B = [os.path.join(R, f"conf_samsung_B_f{f}_m{m}") for f in range(5) for m in (8, 16, 32)]
    C = [os.path.join(R, "conf_samsung_C_f0")]
    S2 = [os.path.join(R, f"conf_samsung_S2_f{f}") for f in range(5)]
    sg._pool_blocks = pool_blocks_tolerant
    at = sg.arm_table(B, C, S2)
    at["post_freeze_note"] = "D046: recomputed after the frozen step with a None-tolerant copy of _pool_blocks; descriptive only"
    out = os.path.join(R, "stats_frozen", "post", "arm_table.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf8") as fh:
        json.dump(at, fh, indent=1)
    print("written", out)


if __name__ == "__main__":
    main()
