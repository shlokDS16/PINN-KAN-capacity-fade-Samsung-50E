"""Item 7 (D048): NC-2 over further stress-permutation draws. POST-HOC, EXPLORATORY; the frozen NC-2 (28 of 40, p 0.054, FAIL) is not changed.
Variant F of STATS_PLAN (faithful): for each draw s and outer fold f the whole frozen NC-2 pipeline (run.py `_run`, permute_stress config conf_samsung_B_f{f}_m32_nc2) is repeated on stress
vectors permuted by draw s: backbone tournament and A1 tuning (N = 40, inner_k 3, same seeds) on the permuted training side, five refits, ensemble forecast of the permuted test side.
The permutation stream is [20261107, 31, fold(+1000 for test)] in the frozen code (metrics.permute_stress); the draw index is appended to the entropy list for s >= 1. Draw 0 is the frozen
stream (identity check in `check_donors`, and a full draw-0 rerun as the pipeline reproduction check).

python -P nc2.py check                -> donor identity check (all five folds, train and test side), writes runs/post_review/item7_nc2/DONOR_CHECK.json
python -P nc2.py run <workers> <draws>   e.g. 'run 5 0' or 'run 11 1-10'
"""
import copy
import dataclasses
import json
import multiprocessing as mp
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

import harness as H  # noqa: E402
from pinnkan import guard, metrics, run, tuning  # noqa: E402
from pinnkan.arms import make_arm  # noqa: E402
from pinnkan.data import WindowRule, prepare_many  # noqa: E402

EXP = "item7_nc2"


def permute_draw(cells, spec, seed, draw):
    """metrics.permute_stress (code/pinnkan/metrics.py) with the draw index appended to the entropy list when draw >= 1 (draw 0 = the frozen stream)"""
    ent = [20261107, 31, int(seed)] + ([int(draw)] if draw else [])
    rng = np.random.default_rng(ent)
    conds = sorted({c.cond for c in cells if c.kind == "cycling"})
    donor = dict(zip(conds, [conds[i] for i in rng.permutation(len(conds))]))
    if len(conds) > 1:
        for _ in range(100):
            if all(donor[c] != c for c in conds):
                break
            donor = dict(zip(conds, [conds[i] for i in rng.permutation(len(conds))]))
    raw_of = {c.cond: c.raw for c in cells if c.kind == "cycling"}
    out = []
    for c in cells:
        if c.kind != "cycling":
            out.append(c)
            continue
        n = copy.copy(c)
        n.raw = raw_of[donor[c.cond]].copy()
        n.meta = {**c.meta, "stress_permuted_from": donor[c.cond]}
        out.append(n)
    return out, donor


def load_nc2(f):
    d = os.path.join(H.RUNS, f"conf_samsung_B_f{f}_m32_nc2")
    cfg_in = json.load(open(os.path.join(d, "config.json"), encoding="utf8"))["config_input"]
    cfg = run.validate_config(cfg_in, H.WT)
    guard.require_item_f_record(H.WT, H.RUNS)
    D = run.build_data(cfg, H.WT, "test", H.RUNS)
    return cfg, D, d


def check_donors():
    out = {"rule": "permute_draw(draw 0) must equal the frozen metrics.permute_stress for the same cells and seed: the same donor of every cycling condition and the same raw stress vectors", "folds": {}}
    ok_all = True
    for f in range(5):
        cfg, D, _ = load_nc2(f)
        spec = D["spec"]
        rec = {}
        for side, cells, seed in (("train", D["train"], f), ("test", D["test"], f + 1000)):
            a = metrics.permute_stress(cells, spec, seed)
            b, _donor = permute_draw(cells, spec, seed, 0)
            same = all(x.cell_id == y.cell_id and np.array_equal(x.raw, y.raw) and x.meta.get("stress_permuted_from") == y.meta.get("stress_permuted_from") for x, y in zip(a, b))
            c1, _ = permute_draw(cells, spec, seed, 1)
            n_diff = int(sum(not np.array_equal(x.raw, y.raw) for x, y in zip(b, c1)))
            rec[side] = {"identical_to_frozen": bool(same), "n_cells": len(a), "draw1_cells_with_different_stress_vector": n_diff}
            ok_all &= bool(same)
        out["folds"][str(f)] = rec
    out["all_identical"] = bool(ok_all)
    H.wjson(os.path.join(H.OUT, EXP, "DONOR_CHECK.json"), out)
    print(json.dumps(out)[:600])
    return ok_all


def job(draw, f):
    jd = os.path.join(H.OUT, EXP, f"draw{draw}_f{f}")
    if os.path.exists(os.path.join(jd, "condition_scores.json")):
        return "skip"
    H.assert_out(os.path.join(jd, "x"))
    os.makedirs(jd, exist_ok=True)
    t0 = time.time()
    log = open(os.path.join(jd, "RUN.log"), "a", encoding="utf8")

    def L(msg):
        log.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        log.flush()
    cfg, D, src = load_nc2(f)
    spec = D["spec"]
    train, donors_tr = permute_draw(D["train"], spec, f, draw)
    test, donors_te = permute_draw(D["test"], spec, f + 1000, draw)
    H.wjson(os.path.join(jd, "config.json"), {"exp": EXP, "draw": draw, "fold": f, "variant": "F (faithful: full re-tuning on the permuted data)", "frozen_config": src, "permutation_entropy_train": [20261107, 31, f] + ([draw] if draw else []),
                                              "permutation_entropy_test": [20261107, 31, f + 1000] + ([draw] if draw else []), "role": "POST-HOC EXPLORATORY (D048)", "donors_train": donors_tr, "donors_test": donors_te})
    H.wjson(os.path.join(jd, "git.json"), H.git_record())
    H.wjson(os.path.join(jd, "env.json"), H.env_record())
    wk = cfg["window"]
    rule = WindowRule.for_spec(spec, k_cycling=wk.get("k_cycling"), k_storage=wk.get("k_storage"), W=wk.get("W"), shift=wk.get("shift", 0))
    rule_test = dataclasses.replace(rule, min_fc_points=int(cfg["min_fc_points"]))
    rule_tune = WindowRule.for_grid(spec, 2 if int(cfg["m"]) < 32 else "full", rule)
    ctx = {"backbone": "self_limiting", "steps_scale": cfg["steps_scale"], "rule": rule_tune, "extra_twin_raw": None, "oracle": cfg["oracle_throughput"], "per_cell_factor": cfg["per_cell_factor"],
           "lab_indicator": bool(cfg["lab_indicator"]), "a10_drop_soc100_storage": bool(cfg["a10_drop_soc100_storage"]), "symbolic": dict(cfg["symbolic"] or {}), "a10_starts": cfg.get("a10_starts", 8), "pinn": cfg["pinn"]}
    tk = cfg["target_kind"]
    tb = tuning.backbone_tournament(train, spec, rule_tune, cfg["inner_k"], f, ctx, tk)
    ctx["backbone"] = tb["chosen"]
    H.wjson(os.path.join(jd, "backbone_tournament.json"), tb)
    L(f"tournament chosen {tb['chosen']}")
    r = tuning.tune("A1", train, spec, rule_tune, cfg["n_trials"], cfg["inner_k"], f, ctx, tk, tpe_seed=cfg["tpe_seed"])
    H.wjson(os.path.join(jd, "tuning_A1.json"), {k: v for k, v in r.items() if k != "rows"})
    L(f"tuned A1 inner-CV {r['inner_cv_pp']:.3f} pp, best {r['best_hp']}, tuning {time.time() - t0:.0f} s")
    pk = prepare_many(test, rule_test, oracle=cfg["oracle_throughput"])
    wc = [p.win for p in pk]
    per_seed = []
    fit_secs = []
    for sd in cfg["seeds"]:
        tf = time.time()
        arm = make_arm("A1", spec, r["best_hp"], sd, dict(ctx, rule=rule_test)).fit(train)
        fit_secs.append(time.time() - tf)
        per_seed.append(arm.predict(wc))
        L(f"seed {sd}: fit {fit_secs[-1]:.1f} s")
    rows_seed = [metrics.score_prepared(p, pk) for p in per_seed]
    ens_rows = metrics.ensemble_rows(per_seed, pk)
    cs = metrics.condition_scores(ens_rows)
    H.write_predictions(os.path.join(jd, "predictions.csv.gz"), "post_review_nc2", "A1", rows_seed, ens_rows)
    csd, sd_ = metrics.seed_condition_scores(rows_seed)
    H.wjson(os.path.join(jd, "condition_scores_seed.json"), {"A1": csd})
    H.wjson(os.path.join(jd, "metrics.json"), {"arm": "A1", "endpoint": "ensemble", "fit_seconds": fit_secs, "wall_seconds": time.time() - t0, "primary_pp_ens": float(np.mean(list(cs.values()))),
                                                 "tuning_inner_cv_pp": r["inner_cv_pp"], "best_hp": r["best_hp"], "backbone": tb["chosen"]})
    H.wjson(os.path.join(jd, "condition_scores.json"), {"A1": cs})
    L(f"done in {time.time() - t0:.0f} s")
    log.close()
    return "ok"


def work(task):
    draw, f = task
    t0 = time.time()
    try:
        return task, job(draw, f), time.time() - t0
    except Exception as e:  # noqa: BLE001
        jd = os.path.join(H.OUT, EXP, f"draw{draw}_f{f}")
        os.makedirs(jd, exist_ok=True)
        with open(os.path.join(jd, "FAILED.txt"), "w", encoding="utf8") as fh:
            fh.write(traceback.format_exc())
        return task, f"FAILED {type(e).__name__}: {e}", time.time() - t0


if __name__ == "__main__":
    if sys.argv[1] == "check":
        sys.exit(0 if check_donors() else 1)
    nw = int(sys.argv[2])
    a, _, b = sys.argv[3].partition("-")
    draws = list(range(int(a), int(b or a) + 1))
    tasks = [(d, f) for d in draws for f in range(5)]
    print(f"{EXP}: {len(tasks)} jobs, {nw} workers", flush=True)
    t0 = time.time()
    with mp.get_context("spawn").Pool(nw) as pool:
        for task, st, secs in pool.imap_unordered(work, tasks, chunksize=1):
            print(f"[{time.time() - t0:7.0f}s] draw{task[0]} f{task[1]}: {st} ({secs:.0f} s)", flush=True)
    H.shas_for(os.path.join(H.OUT, EXP))
    print("done", flush=True)
