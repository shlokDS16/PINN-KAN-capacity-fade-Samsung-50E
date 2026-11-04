"""pinnkan: tuning driver, margins, metrics and the run writer.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_tuning_run.py -q"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest
import torch

torch.set_num_threads(1)

from pinnkan import guard, margins, metrics, run, synth, tuning
from pinnkan.data import WindowRule, prepare_many
from pinnkan.specs import SPECS

SPEC = SPECS["synthetic"]


@pytest.fixture(scope="module")
def g0():
    S = synth.make_synthetic("G0", n_cyc_cond=16, n_sto_cond=6, reps=2, seed=3)
    return synth.split_conditions(S.cells, 0.25, 3)


# ------------------------------------------------------------------------------------------------ inner folds, budget
def test_inner_folds_group_by_condition_and_stratify_by_temperature(g0):
    tr, te = g0
    fo = tuning.inner_folds(tr, 3, 1000, SPEC)
    cyc_conds = {c.cond for c in tr if c.kind == "cycling"}
    assert set(fo) == cyc_conds                                     # storage conditions are never partitioned
    assert set(fo.values()) == {0, 1, 2}
    temp = {c.cond: c.raw[0] for c in tr if c.kind == "cycling"}
    for T in set(temp.values()):
        sizes = np.bincount([fo[c] for c in cyc_conds if temp[c] == T], minlength=3)
        assert sizes.max() - sizes.min() <= 2                       # roughly balanced inside each temperature stratum
    assert fo == tuning.inner_folds(tr, 3, 1000, SPEC) and fo != tuning.inner_folds(tr, 3, 1001, SPEC)
    cond_cells = {}
    for c in tr:
        cond_cells.setdefault(c.cond, set()).add(fo.get(c.cond))
    assert all(len(v) == 1 for v in cond_cells.values())            # all replicates of a condition share a fold


def test_budget_rule():
    assert tuning.choose_budget({"A2": 5.0, "A1": 12.0, "A9": 2.0})["n_trials"] == 40
    assert tuning.choose_budget({"A2": 5.0, "A1": 25.0})["n_trials"] == 20
    b = tuning.choose_budget({"A2": 35.0, "A1": 10.0})
    assert (b["n_trials"], b["inner_k"]) == (10, 2)
    assert tuning.choose_budget({"A2": 5.0, "A1": 95.0})["inner_k"] == 2


def test_margins_pooled_by_test_condition_count():
    assert np.isclose(margins.pooled_E([(8, 1.0), (8, 2.0), (4, 4.0)]), (8 + 16 + 16) / 20)
    r = margins.margin_record([(10, 2.0)])
    assert np.isclose(r["delta_S_pp"], 0.04) and np.isclose(r["delta_N_pp"], 0.2)
    assert np.isclose(np.exp(margins.LOG_MARGIN_S), 1.02) and np.isclose(np.exp(-margins.LOG_MARGIN_N), 1.10)


# ------------------------------------------------------------------------------------------------ metrics
def test_metrics_condition_then_cell_averaging_and_nonfinite_rule(g0):
    tr, te = g0
    prep = prepare_many(te, WindowRule.for_spec(SPEC))
    preds = {p.cell.cell_id: p.fc_true + 0.01 for p in prep}        # 1 pp error everywhere
    rows = metrics.score_prepared(preds, prep)
    assert all(abs(r["rmse_pp"] - 1.0) < 1e-9 for r in rows) and abs(metrics.primary_score(rows) - 1.0) < 1e-9
    bad = {p.cell.cell_id: np.full(len(p.fc_true), np.nan) for p in prep}
    rows = metrics.score_prepared(bad, prep)
    assert sum(r["n_nonfinite"] for r in rows) == sum(len(p.fc_true) for p in prep)
    pers = metrics.score_prepared({p.cell.cell_id: np.full(len(p.fc_true), p.win.y_last) for p in prep}, prep)
    assert np.allclose([r["rmse_pp"] for r in rows], [r["rmse_pp"] for r in pers])     # non-finite scored with the persistence error
    assert np.isclose(metrics.r2_pooled({p.cell.cell_id: p.fc_true for p in prep}, prep), 1.0)
    cs, sd = metrics.seed_condition_scores([rows, pers])
    assert sd == 0.0 and set(cs) == {p.cell.cond for p in prep}
    lr = metrics.log_ratio({"a": 2.0, "b": 1.0}, {"a": 1.0, "b": 1.0})
    assert np.isclose(lr["a"], np.log(2)) and lr["b"] == 0.0


# ------------------------------------------------------------------------------------------------ tuning
def test_tune_uses_training_cells_only_and_is_deterministic(g0):
    tr, te = g0
    rule = WindowRule.for_spec(SPEC)
    ctx = {"backbone": "self_limiting", "steps_scale": 0.05, "rule": rule}
    a = tuning.tune("A2", tr, SPEC, rule, 3, 2, 0, ctx)
    b = tuning.tune("A2", tr, SPEC, rule, 3, 2, 0, ctx)
    assert a["best_hp"] == b["best_hp"] and np.isclose(a["inner_cv_pp"], b["inner_cv_pp"])
    assert a["tpe_seed"] == 0 and a["tuning_seed"] == 1000 and len(a["trials"]) == 3 and np.isfinite(a["inner_cv_pp"])
    train_ids = {c.cell_id for c in tr}
    assert {r["cell"] for r in a["rows"]} <= train_ids
    assert not ({r["cell"] for r in a["rows"]} & {c.cell_id for c in te})
    c = tuning.tune("A2", tr, SPEC, rule, 3, 2, 1, ctx)                   # a different outer fold changes the sampler seed
    assert c["tpe_seed"] == 1 and c["tuning_seed"] == 1001
    r2 = tuning.tune("R2", tr, SPEC, rule, 0, 2, 0, ctx)
    assert r2["trials"] == [] and np.isfinite(r2["inner_cv_pp"])


def test_backbone_tournament_prefers_simplest_within_one_se(g0):
    tr, te = g0
    rule = WindowRule.for_spec(SPEC)
    r = tuning.backbone_tournament(tr, SPEC, rule, 2, 0, {"backbone": "self_limiting", "steps_scale": 0.15, "rule": rule})
    assert r["chosen"] in ("constant", "self_limiting", "accelerating") and set(r["table"]) == {"constant", "self_limiting", "accelerating"}
    order = ["constant", "self_limiting", "accelerating"]
    best = r["table"][r["best"]]
    ok = [b for b in order if r["table"][b]["mean_pp"] <= best["mean_pp"] + best["se_pp"]]
    assert r["chosen"] == ok[0]


# ------------------------------------------------------------------------------------------------ run writer
CFG_SYN = {"dataset": "synthetic", "arms": ["A2", "A9", "R1", "R2"], "n_trials": 2, "inner_k": 2, "steps_scale": 0.05, "seeds": [0, 1],
           "synthetic": {"kind": "G0", "n_cyc_cond": 16, "n_sto_cond": 6, "reps": 2, "seed": 3}}


def test_run_writer_inner_mode_record(tmp_path):
    d = run.run({**CFG_SYN, "run_id": "t_inner", "mode": "inner", "backbone": "tournament"}, runs_dir=str(tmp_path))
    for f in ("config.json", "env.json", "git.json", "split.json", "manifest.json", "seeds.json", "guard.json", "tuning_done.json", "timings.json", "metrics.json",
              "predictions.csv", "RUN.log", "backbone_tournament.json", "tuning_A2.json"):
        assert os.path.isfile(os.path.join(d, f)), f
    git = json.load(open(os.path.join(d, "git.json")))
    assert len(git["commit"]) == 40 and "dirty_files" in git
    env = json.load(open(os.path.join(d, "env.json")))
    assert env["torch_threads"] == 1 and not env["cuda_available"]
    pred = open(os.path.join(d, "predictions.csv")).read()
    assert "inner_oof" in pred and "outer_test" not in pred
    m = json.load(open(os.path.join(d, "metrics.json")))
    assert set(m["inner_cv_pp"]) == set(CFG_SYN["arms"]) and all(np.isfinite(v) for v in m["inner_cv_pp"].values())
    with pytest.raises(FileExistsError):
        run.run({**CFG_SYN, "run_id": "t_inner", "mode": "inner"}, runs_dir=str(tmp_path))


def test_run_writer_confirmatory_orders_tuning_before_any_test_scoring(tmp_path):
    d = run.run({**CFG_SYN, "run_id": "t_conf", "mode": "confirmatory"}, runs_dir=str(tmp_path))
    mt = lambda f: os.path.getmtime(os.path.join(d, f))
    assert mt("tuning_done.json") <= mt("margins_inputs.json") <= mt("margins.json") <= mt("condition_scores.json")
    m = json.load(open(os.path.join(d, "metrics.json")))
    assert set(m["outer_test"]) == set(CFG_SYN["arms"]) and m["outer_test"]["A2"]["n_conditions"] == 4
    cs = json.load(open(os.path.join(d, "condition_scores.json")))
    assert set(cs["A2"]) == set(cs["R1"])
    assert m["outer_test"]["A2"]["primary_pp"] < m["outer_test"]["R1"]["primary_pp"]       # P3 positive control shape: structured arm beats persistence
    assert "outer_test" in open(os.path.join(d, "predictions.csv")).read()


@pytest.mark.skipif(guard.is_frozen(), reason="real FROZEN flag exists")
@pytest.mark.parametrize("ds,test", [("isu", "B"), ("snl", "B"), ("samsung", "B")])
def test_run_confirmatory_on_real_data_is_refused_before_freeze(tmp_path, ds, test):
    with pytest.raises(guard.TestFoldAccessError):
        run.run({"run_id": "t_refuse", "dataset": ds, "test": test, "fold": 0, "mode": "confirmatory", "arms": ["R1"]}, runs_dir=str(tmp_path))
    assert not os.path.exists(os.path.join(tmp_path, "t_refuse", "predictions.csv"))


def test_run_writer_on_isu_training_fold_never_builds_test_cells(tmp_path):
    cfg = {"run_id": "t_isu", "dataset": "isu", "test": "B", "fold": 0, "mode": "inner", "arms": ["R1", "R2", "A2"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.05,
           "backbone": "self_limiting"}
    d = run.run(cfg, runs_dir=str(tmp_path))
    sp = json.load(open(os.path.join(ROOT, "runs", "splits", "isu_testB.json")))["folds"]["0"]
    test_cells = set(sp["test_cells"])
    pred = open(os.path.join(d, "predictions.csv")).read().splitlines()[1:]
    used = {l.split(",")[3] for l in pred}
    assert used and not (used & test_cells)
    split = json.load(open(os.path.join(d, "split.json")))
    assert split["fold_hash_ok"] is True
    assert guard.GUARD_LOG and all(g.get("allowed", False) or g.get("role") == "train" for g in guard.GUARD_LOG if "role" in g)


@pytest.mark.skipif(guard.is_frozen(), reason="real FROZEN flag exists")
def test_samsung_run_is_blinded_before_the_freeze(tmp_path):
    cfg = {"run_id": "t_sam", "dataset": "samsung", "test": "B", "fold": 0, "mode": "inner", "arms": ["R1", "A2"], "steps_scale": 0.05}
    d = run.run(cfg, runs_dir=str(tmp_path))
    c = json.load(open(os.path.join(d, "config.json")))
    assert c["mode_effective"] == "timing" and c["blinded_samsung_pre_freeze"] is True
    assert not os.path.exists(os.path.join(d, "predictions.csv")) and not os.path.exists(os.path.join(d, "tuning_A2.json"))
    m = json.load(open(os.path.join(d, "metrics.json")))
    assert m["blinded"] is True and set(m) <= {"blinded", "mode", "note"}                 # no retention-derived number
    t = json.load(open(os.path.join(d, "timings.json")))
    assert t["A2"]["fit_seconds"] >= 0 and t["A2"]["n_params"] > 0


def test_twins_from_condition_identifiers():
    assert run.twins_from_conditions(["T35|SOCmax0.8|DoD0.5|Cch0.9|Cdch1.1", "T23|SOC0.5"]) == [(35.0, 0.55)]
