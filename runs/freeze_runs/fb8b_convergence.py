"""FB-8b (PREREG_v4 section 237 'Dry run and fallbacks', C27 / D023 A8): inversion convergence share of A1 and A9 on TRAINING-SIDE windows.
Lead, 2026-11-06, at the freeze candidate commit. Not confirmatory, not pinned, untracked.

FB-8 timing mode fits only and runs no inversion, so this script supplies the convergence share the prereg asks FB-8 to log.
For each primary config conf_samsung_B_f{fold}_m{m} (m 8 and 32): the training side only (role 'train', no outer fold is built),
the same inner folds as tuning (tuning.inner_folds, seed 1000 + fold), the tuning window (k = 2 for m < 32, k_full for m = 32),
default hyperparameters, fit on the other inner folds, then the production arm.predict on the held-out inner fold's windows.
Only counts are written (inversion.drain_log -> n_inverted, n_nonconverged, gnorm_max, nonfinite). Predictions are discarded.
Usage: python -P runs/freeze_runs/fb8b_convergence.py <fold> [<fold> ...]
"""
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

from pinnkan import inversion, run, tuning                      # noqa: E402
from pinnkan.arms import ARMS, default_hp, make_arm            # noqa: E402
from pinnkan.data import WindowRule, prepare_many              # noqa: E402

ARMS_REQ = ("A1", "A9")
OUT = os.path.join(ROOT, "runs", "freeze_runs", "fb8b")
os.makedirs(OUT, exist_ok=True)
CONF = os.path.join(ROOT, "runs", "prereg", "confirmatory_configs")


def one(fold, m):
    cfg_in = json.load(open(os.path.join(CONF, f"conf_samsung_B_f{fold}_m{m}.json"), encoding="utf8"))
    cfg = run.validate_config(cfg_in, ROOT)
    D = run.build_data(cfg, ROOT, "train", runs_dir=os.path.join(ROOT, "runs"))
    assert D["test"] is None
    spec, train, tk = D["spec"], D["train"], cfg["target_kind"]
    wk = cfg["window"]
    rule = WindowRule.for_spec(spec, k_cycling=wk.get("k_cycling"), k_storage=wk.get("k_storage"), W=wk.get("W"), shift=wk.get("shift", 0))
    rule_tune = WindowRule.for_grid(spec, 2 if int(m) < 32 else "full", rule)
    ctx = {"backbone": cfg["backbone"] if cfg["backbone"] != "tournament" else "self_limiting", "steps_scale": cfg["steps_scale"], "rule": rule_tune, "extra_twin_raw": None,
           "oracle": cfg["oracle_throughput"], "per_cell_factor": cfg["per_cell_factor"], "lab_indicator": bool(cfg["lab_indicator"]),
           "a10_drop_soc100_storage": bool(cfg["a10_drop_soc100_storage"]), "symbolic": dict(cfg["symbolic"] or {}), "a10_starts": cfg.get("a10_starts", 8), "pinn": cfg["pinn"]}
    k_in = int(cfg["inner_k"])
    fold_of = tuning.inner_folds(train, k_in, 1000 + fold, spec, tk)
    res = {}
    for a in ARMS_REQ:
        recs, t0 = [], time.time()
        for f in range(k_in):
            val = [c for c in train if c.kind == tk and fold_of.get(c.cond) == f]
            tr = [c for c in train if not (c.kind == tk and fold_of.get(c.cond) == f)]
            if not val:
                continue
            arm = make_arm(a, spec, default_hp(a) if ARMS[a].tuned else {}, 1000 + fold, ctx).fit(tr)
            prep = prepare_many(val, rule_tune, oracle=bool(ctx["oracle"]))
            inversion.LOG.clear()
            inversion.TAG.clear()
            inversion.TAG.update({"arm": a, "k": "fb8b", "seed": 1000 + fold})
            if prep:
                arm.predict([p.win for p in prep])                 # predictions discarded: counts only
            recs += [dict(r, inner_fold=f) for r in inversion.drain_log()]
        pooled = inversion.pooled_convergence(recs)
        pooled.update(gnorm_max=max((float(r.get("gnorm_max", 0.0)) for r in recs), default=0.0),
                      nonfinite=int(sum(int(r.get("nonfinite", 0)) for r in recs)), seconds=round(time.time() - t0, 1), inner_k=k_in)
        res[a] = pooled
        print(f"fold {fold} m {m} {a}: {pooled}", flush=True)
    return res


if __name__ == "__main__":
    for fold in [int(x) for x in sys.argv[1:]]:
        out = {"fold": fold, "commit_note": "see runs/freeze_runs/logs/queue.log HEAD", "inversion_config_sha256": inversion.config_sha256(),
               "by_m": {str(m): one(fold, m) for m in (8, 32)}}
        with open(os.path.join(OUT, f"fb8b_f{fold}.json"), "w", encoding="utf8", newline="\n") as fh:
            json.dump(out, fh, indent=1)
