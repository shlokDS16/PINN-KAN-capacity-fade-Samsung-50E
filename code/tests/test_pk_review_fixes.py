"""pinnkan: one test per fix of runs/build_v1/CODE_REVIEW.md (M1-M4, m2-m8, D013 configurability). m1 (QC outlier rule) is documented, not fixed.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_review_fixes.py -q
Every freeze here lives in a TEMPORARY root with git stubbed; the real runs/prereg/FROZEN is never created."""
import hashlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "tests"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pandas as pd
import pytest
import torch

torch.set_num_threads(1)

from pinnkan import arms, data, guard, hard, law, metrics, pinn, run, synth, tuning
from pinnkan.data import EFCCurve, SplitIntegrityError, WindowRule, prepare_many
from pinnkan.specs import SPECS
from pk_freeze import make_freeze

SPEC = SPECS["synthetic"]


# ------------------------------------------------------------------------------------------------ helpers
def _digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()


def mini_isu(tmp_path, train_conditions=(1, 2, 3, 4), test_conditions=(5, 6), tamper=False):
    os.makedirs(tmp_path / "data" / "processed", exist_ok=True)
    os.makedirs(tmp_path / "runs" / "splits", exist_ok=True)
    pd.DataFrame({"group": range(1, 7), "charge_c": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0], "discharge_c": [0.5, 1.0, 1.5, 2.0, 1.0, 0.5],
                  "dod_pct": [30, 40, 50, 60, 70, 80]}).to_csv(tmp_path / "data" / "processed" / "isu_conditions.csv", index=False)
    rows = [(f"G{g}C{r}", g, float(w), 1.0 - 0.01 * g * w ** 0.8, 0.3) for g in range(1, 7) for r in (1, 2) for w in range(12)]
    pd.DataFrame(rows, columns=["cell", "group", "week", "retention", "capacity_ah"]).to_csv(tmp_path / "data" / "processed" / "isu_capacity.csv", index=False)
    folds = {"0": {"test_conditions": list(test_conditions), "test_cells": [f"G{g}C{r}" for g in test_conditions for r in (1, 2)], "train_conditions": list(train_conditions)}}
    h = _digest(folds)
    if tamper:
        folds["0"]["test_conditions"] = [6]                       # edited after the hash was written
    p = tmp_path / "runs" / "splits" / "isu_testB.json"
    json.dump({"dataset": "ISU", "test": "B", "n_folds": 1, "folds": folds, "sha256_of_folds": h}, open(p, "w"))
    return str(tmp_path), str(p), h


# ------------------------------------------------------------------------------------------------ M1
def test_m1_regenerated_split_raises_instead_of_warning(tmp_path):
    root, _, _ = mini_isu(tmp_path, tamper=True)
    with pytest.raises(SplitIntegrityError):
        data.load_split("isu", "B", 0, role="train", root=root)


def test_m1_hash_pinned_at_freeze_is_enforced(tmp_path, monkeypatch):
    root, p, h = mini_isu(tmp_path)
    make_freeze(tmp_path, monkeypatch, splits={"isu:B": {"file_sha256": data.sha256_file(p), "fold_hash": "0" * 64}})
    with pytest.raises(SplitIntegrityError):
        data.load_split("isu", "B", 0, role="train", root=root)                         # even the training role
    make_freeze(tmp_path, monkeypatch, splits={"isu:B": {"file_sha256": "1" * 64, "fold_hash": h}})
    with pytest.raises(SplitIntegrityError):
        data.load_split("isu", "B", 0, role="train", root=root)
    make_freeze(tmp_path, monkeypatch, splits={"isu:B": {"file_sha256": data.sha256_file(p), "fold_hash": h}})
    assert data.load_split("isu", "B", 0, role="train", root=root).pinned is True
    make_freeze(tmp_path, monkeypatch, splits={})                                       # no pin for this split after the freeze: fail closed
    with pytest.raises(guard.TestFoldAccessError):
        data.load_split("isu", "B", 0, role="train", root=root)


def test_m1_loaded_training_conditions_must_be_listed_in_the_split(tmp_path):
    root, _, _ = mini_isu(tmp_path, train_conditions=(1, 2, 3))                            # condition 4 is on disk but not in the split's training set
    with pytest.raises(SplitIntegrityError):
        data.load_split("isu", "B", 0, role="train", root=root)


def test_m1_missing_training_conditions_are_reported(tmp_path):
    root, _, _ = mini_isu(tmp_path, train_conditions=(1, 2, 3, 4, 9))
    assert data.load_split("isu", "B", 0, role="train", root=root).missing_train_conditions == ["9"]


# ------------------------------------------------------------------------------------------------ M2
def test_m2_freeze_verification_failures(tmp_path, monkeypatch):
    root = str(tmp_path)
    os.makedirs(tmp_path / "runs" / "prereg")
    (tmp_path / "runs" / "prereg" / "FROZEN").write_text("frozen")                         # a bare file is no longer a freeze
    with pytest.raises(guard.TestFoldAccessError):
        guard.verify_freeze(root)
    assert not guard.is_valid_freeze(root)
    (tmp_path / "runs" / "prereg" / "FROZEN").write_text(json.dumps({"commit": "x"}))
    with pytest.raises(guard.TestFoldAccessError):
        guard.verify_freeze(root)
    make_freeze(tmp_path, monkeypatch)
    assert guard.verify_freeze(root)["commit"] == "a" * 40
    make_freeze(tmp_path, monkeypatch, head="b" * 40)
    with pytest.raises(guard.TestFoldAccessError, match="frozen commit"):
        guard.verify_freeze(root)
    make_freeze(tmp_path, monkeypatch, dirty=" M code/pinnkan/law.py")
    with pytest.raises(guard.TestFoldAccessError, match="differ"):
        guard.verify_freeze(root)
    make_freeze(tmp_path, monkeypatch)
    (tmp_path / "runs" / "prereg" / "PREREG_v2.md").write_text("edited after the freeze")
    with pytest.raises(guard.TestFoldAccessError, match="prereg"):
        guard.verify_freeze(root)


def test_m2_nothing_in_the_package_writes_the_flag_file():
    src = "".join(open(os.path.join(ROOT, "code", "pinnkan", f), encoding="utf8").read() for f in os.listdir(os.path.join(ROOT, "code", "pinnkan")) if f.endswith(".py"))
    assert 'open(frozen_path' not in src and "FROZEN_REL), \"w" not in src
    assert not os.path.exists(guard.frozen_path())


def _confirmatory_cfg(**kw):
    return {"run_id": "c1", "dataset": "isu", "test": "B", "fold": 0, "mode": "confirmatory", "arms": ["R1", "R2"], "seeds": [0], "backbone": "self_limiting", **kw}


def test_m2_confirmatory_on_real_layout_requires_everything(tmp_path, monkeypatch):
    root, p, h = mini_isu(tmp_path)
    runs = str(tmp_path / "runs")
    cfg = _confirmatory_cfg()
    chash = guard.canonical_config_hash({**run.DEFAULTS, **cfg})
    make_freeze(tmp_path, monkeypatch, splits={"isu:B": {"file_sha256": data.sha256_file(p), "fold_hash": h}}, config_hashes=[chash])
    with pytest.raises(run.ConfigError, match="steps_scale"):
        run.run({**cfg, "steps_scale": 0.5, "run_id": "c0"}, root=root, runs_dir=runs)
    with pytest.raises(run.ConfigError, match="overwrite"):
        run.run({**cfg, "overwrite": True, "run_id": "c0"}, root=root, runs_dir=runs)
    with pytest.raises(guard.TestFoldAccessError, match="frozen configs"):
        run.run({**cfg, "arms": ["R1"], "run_id": "c0"}, root=root, runs_dir=runs)       # a config that was not pinned
    assert not os.path.exists(os.path.join(runs, "c0"))                                 # refused before a run folder exists
    d = run.run(cfg, root=root, runs_dir=runs)
    m = json.load(open(os.path.join(d, "metrics.json")))
    assert m["outer_test"]["R1"]["n_conditions"] == 2
    ledger = open(os.path.join(root, "runs", "prereg", "SCORED.jsonl")).read().splitlines()
    assert len(ledger) == 1 and json.loads(ledger[0])["config_sha256"] == chash
    with pytest.raises(guard.TestFoldAccessError, match="already scored"):
        run.run({**cfg, "run_id": "c2"}, root=root, runs_dir=runs)                       # the same frozen config is not scored twice
    assert os.path.exists(os.path.join(d, "condition_scores.json"))


def test_m2_scored_run_folder_is_never_replaced(tmp_path):
    d = tmp_path / "runs" / "x"
    os.makedirs(d)
    (d / "condition_scores.json").write_text("{}")
    with pytest.raises(run.ScoredRunError):
        run.run({"run_id": "x", "dataset": "synthetic", "mode": "inner", "arms": ["R1"], "overwrite": True}, runs_dir=str(tmp_path / "runs"))


def test_m2_build_freeze_payload_returns_dict_without_writing(tmp_path, monkeypatch):
    root, p, h = mini_isu(tmp_path)
    make_freeze(tmp_path, monkeypatch)
    os.remove(tmp_path / "runs" / "prereg" / "FROZEN")
    (tmp_path / "runs" / "prereg" / "PREREG_v3.md").write_text("prereg v3 freeze candidate")      # guard.PREREG_DEFAULT is v3 since build_v1 section 7
    cfgp = tmp_path / "cfg.json"
    cfgp.write_text(json.dumps(_confirmatory_cfg()))
    pay = guard.build_freeze_payload(root, [("isu", "B")], [str(cfgp)])
    assert pay["prereg_file"].endswith("PREREG_v3.md")
    assert pay["splits"]["isu:B"] == {"file_sha256": data.sha256_file(p), "fold_hash": h} and len(pay["config_sha256s"]) == 1
    assert not os.path.exists(tmp_path / "runs" / "prereg" / "FROZEN")


# ------------------------------------------------------------------------------------------------ M3
def test_m3_target_kind_is_derived_from_the_test_name():
    assert run.TARGET_BY_TEST == {"B": "cycling", "C": "cycling", "A": "cycling", "S2": "storage", "S3": "storage"}
    with pytest.raises(run.ConfigError, match="contradicts"):
        run.run({"run_id": "m3", "dataset": "isu", "test": "S2", "target_kind": "cycling", "mode": "inner", "arms": ["R1"]}, runs_dir="unused")


def test_m3_tuning_on_storage_conditions_and_assertion():
    S = synth.make_synthetic("G0", n_cyc_cond=8, n_sto_cond=6, reps=2, seed=3)
    rule = WindowRule.for_spec(SPEC)
    ctx = {"backbone": "self_limiting", "steps_scale": 0.05, "rule": rule}
    r = tuning.tune("A2", S.cells, SPEC, rule, 2, 2, 0, ctx, target_kind="storage")
    scored = {row["cell"] for row in r["rows"]}
    assert scored and all(c.kind == "storage" for c in S.cells if c.cell_id in scored)
    storage_only = [c for c in S.cells if c.kind == "storage"]
    with pytest.raises(AssertionError):
        tuning.inner_folds(storage_only, 2, 0, SPEC, target_kind="cycling")           # no cycling cells to partition: the task would silently differ


# ------------------------------------------------------------------------------------------------ M4
def test_m4_permute_stress_moves_every_vector_and_keeps_labels():
    S = synth.make_synthetic("G0", n_cyc_cond=10, n_sto_cond=4, reps=2, seed=4)
    P = metrics.permute_stress(S.cells, SPEC, 0)
    assert metrics.permute_stress(S.cells, SPEC, 0)[0].raw.tolist() == P[0].raw.tolist()
    donor = {c.cond: p.meta.get("stress_permuted_from") for c, p in zip(S.cells, P) if c.kind == "cycling"}
    assert all(k != v for k, v in donor.items()) and sorted(donor) == sorted(donor.values())
    for c, p in zip(S.cells, P):
        assert np.array_equal(c.t, p.t) and np.array_equal(c.ret, p.ret) and c.cond == p.cond          # window and forecast data untouched
        if c.kind == "storage":
            assert np.array_equal(c.raw, p.raw) and p is c
        else:
            assert np.allclose(p.efc, SPEC.efc_rate(p.raw) * p.t)                                       # design throughput follows the stress vector
            assert not np.allclose(p.raw, c.raw)
    tr, te = synth.split_conditions(S.cells, 0.3, 4)
    assert {c.cond for c in metrics.permute_stress(te, SPEC, 1000)} == {c.cond for c in te}              # permutation inside the test set only


def test_m4_metrics_are_wired_and_negative_control_runs_end_to_end(tmp_path):
    cfg = {"run_id": "nc", "dataset": "synthetic", "mode": "confirmatory", "arms": ["A1", "A9", "R2"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.05, "seeds": [0, 1],
           "permute_stress": True, "synthetic": {"kind": "G0", "n_cyc_cond": 16, "n_sto_cond": 6, "reps": 2, "seed": 3}}
    d = run.run(cfg, runs_dir=str(tmp_path))
    m = json.load(open(os.path.join(d, "metrics.json")))
    a1 = m["outer_test"]["A1"]
    for k in ("r2_pooled", "mape_pct_mean", "horizon_rmse_pp", "rul", "n_train_used", "mae_pp_mean"):
        assert k in a1, k
    assert "1" in a1["horizon_rmse_pp"] and a1["rul"]["level"] == 0.8
    assert "negative_control" not in m and "permuted_stress_run" in m and m["nc1_invariance_passed"] is True            # D014: no score-contrast criteria in the run record
    assert json.load(open(os.path.join(d, "invariance.json")))["passed"] is True
    assert json.load(open(os.path.join(d, "config.json")))["permute_stress"] is True


# ------------------------------------------------------------------------------------------------ m2
@pytest.fixture(scope="module")
def g0():
    S = synth.make_synthetic("G0", seed=1)
    return synth.split_conditions(S.cells, 0.25, 1)


@pytest.mark.parametrize("aid", ["R1", "R2", "A2", "A9", "A10", "A11", "A12", "A1"])
def test_m2_forecast_does_not_depend_on_where_the_query_list_ends(aid, g0):
    """ISU/SNL forecast sets end at the 70 % crossing, so the length of t_fc encodes a label. Predictions at a check-up time must not depend on the later times queried."""
    tr, te = g0
    cut = WindowRule(k_cycling=4, k_storage=2, life_level=0.88)
    full = WindowRule(k_cycling=4, k_storage=2, life_level=None)
    pc, pf = prepare_many(te, cut), prepare_many(te, full)
    assert any(len(a.win.t_fc) < len(b.win.t_fc) for a, b in zip(pc, pf))         # the cut really shortens some lists
    ctx = {"rule": full, "backbone": "self_limiting", "steps_scale": 0.04, "a10_starts": 2}
    arm = arms.make_arm(aid, SPEC, arms.default_hp(aid), 0, ctx).fit(tr)
    a, b = arm.predict([p.win for p in pc]), arm.predict([p.win for p in pf])
    for p in pc:
        n = len(p.win.t_fc)
        assert np.allclose(a[p.cell.cell_id], b[p.cell.cell_id][:n], atol=1e-5), aid


# ------------------------------------------------------------------------------------------------ m3, m4 (loader)
def _samsung_csv(tmp_path, with_et_cells, efc_cells=None):
    os.makedirs(tmp_path / "data" / "processed", exist_ok=True)
    rows = []
    for cid, has_et in with_et_cells.items():
        base = {"cell_id": cid, "serial": cid[:-3], "type": "z", "T_C": 23.0, "SOC_max": 0.7, "DoD": 0.2, "C_ch": 0.5, "C_dch": 1.0, "lab": "INT", "stage": 1, "cell": 1, "tp": 3,
                "qc_pass": True}
        seq = ([("ET", 1, 0.0, 5.0)] if has_et else []) + [("CU", 3, 7.0, 4.9), ("CU", 5, 14.0, 4.8), ("exCU", 6, 21.0, 4.7), ("CU", 7, 21.0, 4.6)]
        for i, (k, fi, day, q) in enumerate(seq):
            e = (efc_cells or {}).get(cid, [np.nan] * 10)[i] if efc_cells else day * 2.0
            rows.append({**base, "kind": k, "file_idx": fi, "elapsed_days": day, "q_mean_ah": q, "retention": 99.0, "efc_est_cum": e})
    pd.DataFrame(rows).to_csv(tmp_path / "data" / "processed" / "samsung_checkups.csv", index=False)
    return str(tmp_path)


def test_m3_one_reference_rule_for_all_cells(tmp_path):
    root = _samsung_csv(tmp_path, {"TP_z01_01_s1": True, "TP_z02_01_s1": False})
    cells = data._load_samsung(root)
    assert {c.meta["reference"] for c in cells} == {"first_CU"}                           # ET exists for only one cell: nobody uses ET
    for c in cells:
        assert c.ret[0] == 1.0 and np.isclose(c.ret[1], 4.8 / 4.9)                       # recomputed from q_mean of the first CU, not the pipeline's per-cell column
    both = data._load_samsung(_samsung_csv(tmp_path, {"TP_z01_01_s1": True, "TP_z02_01_s1": True}))
    assert {c.meta["reference"] for c in both} == {"ET"} and all(np.isclose(c.ret[1], 4.9 / 5.0) and not c.fc_ok[0] for c in both)


def test_m4_efc_forward_filled_monotone_and_zero_width_intervals_handled(tmp_path):
    efc = {"TP_z01_01_s1": [10.0, np.nan, 30.0, 25.0, 40.0]}                             # a gap and a decrease
    root = _samsung_csv(tmp_path, {"TP_z01_01_s1": False}, efc_cells=efc)
    c = data._load_samsung(root)[0]
    assert np.all(np.diff(c.efc) >= 0) and c.efc[0] == 0.0 and c.efc[1] == 0.0 and c.meta["efc_decreases_fixed"] >= 1      # gap filled forward, not zeroed
    cur = EFCCurve(np.array([0.0, 7.0, 7.0, 14.0]), np.array([0.0, 3.0, 3.0, 8.0]))       # two check-ups on the same day
    assert np.all(np.isfinite(cur.rate(np.array([3.0, 7.0, 10.0])))) and np.isclose(cur.rate(10.0), 5.0 / 7.0)


# ------------------------------------------------------------------------------------------------ m5
def test_m5_inversion_is_independent_of_batch_composition(g0):
    tr, te = g0
    b = pinn.fit_pinn(law.batch_from_cells(SPEC, tr), SPEC, {"map": "gam", "grid": 3, "l2": 1e-4, "lam_res": 1.0}, "self_limiting", 0, steps=60)
    prep = prepare_many(te, WindowRule.for_spec(SPEC))
    wc = [p.win for p in prep]
    one = pinn.predict_pinn(b, SPEC, wc[:1], 1.0, 0)[0]
    shuffled = pinn.predict_pinn(b, SPEC, list(reversed(wc)), 1.0, 0)[0]
    assert np.allclose(one[wc[0].cell_id], shuffled[wc[0].cell_id], atol=1e-3)


# ------------------------------------------------------------------------------------------------ m6
def test_m6_training_set_asymmetry_is_recorded(g0):
    tr, te = g0
    rule = WindowRule.for_spec(SPEC, shift=-1)                  # k_sto = 1: storage cells have 2 window points < 3 and drop out of A11/A12 only
    ctx = {"rule": rule, "backbone": "self_limiting", "steps_scale": 0.04}
    a2 = arms.make_arm("A2", SPEC, arms.default_hp("A2"), 0, ctx).fit(tr)
    a11 = arms.make_arm("A11", SPEC, arms.default_hp("A11"), 0, ctx).fit(tr)
    n_sto = sum(c.kind == "storage" for c in tr)
    assert a2.n_train_used == len(tr) and a11.n_train_used == len(tr) - n_sto


def test_m6_run_metrics_report_scorable_cell_count(tmp_path):
    d = run.run({"run_id": "m6", "dataset": "synthetic", "mode": "inner", "arms": ["R1"], "n_trials": 1, "inner_k": 2,
                 "synthetic": {"n_cyc_cond": 8, "n_sto_cond": 4, "reps": 2, "seed": 2}, "window": {"shift": -1}}, runs_dir=str(tmp_path))
    m = json.load(open(os.path.join(d, "metrics.json")))
    assert m["n_train_scorable_cells"] < m["n_train_cells"]


# ------------------------------------------------------------------------------------------------ m7
def test_m7_failed_trials_are_redrawn_up_to_a_cap(monkeypatch, g0):
    tr, te = g0
    rule = WindowRule.for_spec(SPEC)
    ctx = {"backbone": "self_limiting", "steps_scale": 0.03, "rule": rule}
    real = tuning.cv_rows
    calls = {"n": 0}

    def flaky(*a, **k):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise RuntimeError("arm-specific failure")
        return real(*a, **k)
    monkeypatch.setattr(tuning, "cv_rows", flaky)
    r = tuning.tune("A2", tr, SPEC, rule, 4, 2, 0, ctx)
    assert r["n_failed"] == 2 and sum(t["state"] == "COMPLETE" for t in r["trials"]) == 4          # N valid trials, as for every other arm
    monkeypatch.setattr(tuning, "cv_rows", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("always")))
    with pytest.raises(RuntimeError, match="failed tuning trials"):
        tuning.tune("A2", tr, SPEC, rule, 4, 2, 0, ctx)


# ------------------------------------------------------------------------------------------------ m8
def test_m8_snl_inner_folds_are_stratified_by_temperature():
    sv = data.load_split("snl", "B", 0, role="train")
    fo = tuning.inner_folds(sv.train, 3, 1000, SPECS["snl"])
    temp = {c.cond: c.raw[3] for c in sv.train}
    assert len(set(temp.values())) == 3
    for T in set(temp.values()):
        sizes = np.bincount([fo[c] for c in fo if temp[c] == T], minlength=3)
        assert sizes.max() - sizes.min() <= 1 or sizes.sum() < 3


def test_m8_budget_is_fixed_before_tuning(tmp_path, monkeypatch):
    monkeypatch.setattr(tuning, "choose_budget", lambda med: {"n_trials": 2, "inner_k": 2, "rule": "stub"})
    d = run.run({"run_id": "bud", "dataset": "synthetic", "mode": "inner", "arms": ["A2"], "auto_budget": True, "n_trials": 20, "inner_k": 3, "steps_scale": 0.03,
                 "synthetic": {"n_cyc_cond": 8, "n_sto_cond": 4, "reps": 2, "seed": 2}}, runs_dir=str(tmp_path))
    mt = lambda f: os.path.getmtime(os.path.join(d, f))
    assert mt("budget_rule.json") <= mt("tuning_A2.json") <= mt("tuning_done.json")
    assert json.load(open(os.path.join(d, "tuning_done.json")))["budget"] == {"n_trials": 2, "inner_k": 2}


def test_m8_log_ratio_requires_identical_condition_sets():
    with pytest.raises(ValueError):
        metrics.log_ratio({"a": 1.0, "b": 2.0}, {"a": 1.0})
    assert metrics.log_ratio({"a": 2.0}, {"a": 1.0})["a"] == pytest.approx(np.log(2))


def test_m8_lightgbm_setting_matches_documentation():
    src = open(os.path.join(ROOT, "code", "pinnkan", "baselines.py"), encoding="utf8").read()
    readme = open(os.path.join(ROOT, "code", "README.md"), encoding="utf8").read()
    assert "mono=True" in src and "monotone constraint on the horizon" in readme


# ------------------------------------------------------------------------------------------------ D013: PINN training options stay configurable
def test_d013_clip_and_warmup_are_configurable_and_reach_the_fit(monkeypatch, g0):
    tr, te = g0
    seen = {}
    real = arms.fit_pinn

    def spy(*a, **k):
        seen.update(k)
        return real(*a, **k)
    monkeypatch.setattr(arms, "fit_pinn", spy)
    ctx = {"rule": WindowRule.for_spec(SPEC), "backbone": "self_limiting", "steps_scale": 0.03, "pinn": {"clip": 0, "warmup": 0.0, "lr": 1e-3}}
    arms.make_arm("A1", SPEC, arms.default_hp("A1"), 0, ctx).fit(tr)
    assert seen["clip"] == 0 and seen["warmup"] == 0.0 and seen["lr"] == 1e-3
    seen.clear()
    arms.make_arm("A1", SPEC, arms.default_hp("A1"), 0, {**ctx, "pinn": {}}).fit(tr)
    assert "clip" not in seen                                                          # defaults live in fit_pinn (GRAD_CLIP, warmup 0.4)
    assert pinn.GRAD_CLIP == 20.0
    assert run.DEFAULTS["pinn"] == {}


# ------------------------------------------------------------------------------------------------ D013 C1-C4, C7
@pytest.mark.parametrize("which", ["A1", "A2", "A9"])
def test_d013_c1_clip_is_applied_in_every_gradient_trained_fit(which, monkeypatch, g0):
    tr, te = g0
    b = law.batch_from_cells(SPEC, tr)
    calls = []
    real = torch.nn.utils.clip_grad_norm_
    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_", lambda p, m, *a, **k: (calls.append(m), real(p, m, *a, **k))[1])
    fit = {"A1": lambda **k: pinn.fit_pinn(b, SPEC, {"map": "gam", "grid": 3}, "self_limiting", 0, steps=7, **k),
           "A2": lambda **k: hard.fit_hard(b, SPEC, {"map": "gam", "grid": 3}, "self_limiting", 0, steps=7, **k),
           "A9": lambda **k: pinn.fit_data_only(b, SPEC, {"width": 8, "depth": 2}, 0, steps=7, **k)}[which]
    m = fit()
    assert calls == [20.0] * 7 and 0.0 <= m.clip_fraction <= 1.0
    calls.clear()
    fit(clip=0)
    assert calls == []                                                   # configurable off (D013 keeps clip / warm-up configurable)
    assert law.GRAD_CLIP == 20.0 and pinn.GRAD_CLIP is law.GRAD_CLIP


def test_d013_c1_clip_option_reaches_a2_and_a9_through_ctx(monkeypatch, g0):
    tr, te = g0
    seen = {}
    for name, key in (("fit_hard", "A2"), ("fit_data_only", "A9")):
        real = getattr(arms, name)
        monkeypatch.setattr(arms, name, (lambda r: (lambda *a, **k: (seen.setdefault(k.get("clip"), []).append(1), r(*a, **k))[1]))(real))
        arms.make_arm(key, SPEC, arms.default_hp(key), 0, {"steps_scale": 0.02, "backbone": "self_limiting", "pinn": {"clip": 7.0}}).fit(tr)
    assert 7.0 in seen and len(seen[7.0]) == 2


def test_d013_c2_snl_interaction_pairs_follow_the_design_rule():
    s = SPECS["snl"]
    names = list(s.stress_names)
    assert len(s.interaction_pairs) == 7
    partners = {n for pr in s.interaction_pairs for n in pr}
    assert partners == {"temp_c", "discharge_c", "is_LFP", "is_NCA", "is_NMC"}          # no charge rate, no DoD
    assert ("temp_c", "discharge_c") in s.interaction_pairs
    m = law.build_stress_map("igam", s, {"grid": 3, "igrid": 3})
    assert len(m.pairs) == 7 and all(names[i] != "charge_c" and names[i] != "dod" for pr in m.pairs for i in pr)
    assert len(SPECS["isu"].interaction_pairs) == 3 and len(SPECS["samsung"].interaction_pairs) == 3
    assert arms.ARMS["A5"].dims == 5


def test_d013_c3_lam_res_grid_has_the_lower_precaution_value():
    for a in ("A1", "A3", "A4", "A5", "A7", "A13", "A14"):
        assert arms.ARMS[a].space["lam_res"][1] == [1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0]
    assert arms.ARMS["A1"].dims == 6                                                   # dimension count unchanged


def test_d013_c4_run_refuses_when_cuda_is_visible(monkeypatch, tmp_path):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    with pytest.raises(run.DeviceError):
        run.run({"run_id": "gpu", "dataset": "synthetic", "mode": "inner", "arms": ["R1"]}, runs_dir=str(tmp_path))
    assert not os.path.exists(tmp_path / "gpu")
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "-1"


def test_d013_c7_diagnostics_in_the_run_record(tmp_path):
    cfg = {"run_id": "diag", "dataset": "synthetic", "mode": "inner", "arms": ["A1", "A2", "A9", "R1"], "n_trials": 2, "inner_k": 2, "steps_scale": 0.04,
           "backbone": "tournament", "synthetic": {"n_cyc_cond": 10, "n_sto_cond": 4, "reps": 2, "seed": 2}}
    d = run.run(cfg, runs_dir=str(tmp_path))
    dg = json.load(open(os.path.join(d, "diagnostics.json")))
    assert os.path.exists(os.path.join(d, "backbone_tournament.json"))                 # tournament table
    a1 = dg["arms"]["A1"]
    assert a1["lam_res"] in dg["lam_res_grid"] and isinstance(a1["lam_res_at_lower_edge"], bool) and 0.0 <= a1["clip_fraction"] <= 1.0
    assert a1["delta_sd"] >= 0 and np.isclose(a1["delta_sd_over_tau"], a1["delta_sd"] / 0.15) and isinstance(a1["delta_sd_flag_outside_0p5_2"], bool)
    assert 0.0 <= dg["arms"]["A9"]["clip_fraction"] <= 1.0 and "delta_sd" not in dg["arms"]["A9"] and "R1" not in dg["arms"]
    assert dg["lam_res_edge_share_over_arms"] in (0.0, 1.0)
