"""pinnkan: test-fold guard and common data interface. Run from ROOT:
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_guard_data.py -q
The real flag file runs/prereg/FROZEN is never created here; tests that need a frozen state use a temporary root."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pandas as pd
import pytest

from pinnkan import guard, data
from pinnkan.data import Cell, EFCCurve, WindowRule, prepare, window_rule_from_counts
from pinnkan.specs import SPECS

REAL_FROZEN = guard.is_frozen()


# ------------------------------------------------------------------------------------------------ guard
def test_guard_refuses_without_flag_and_passes_with_it(tmp_path):
    with pytest.raises(guard.TestFoldAccessError):
        guard.require_frozen("unit test", root=str(tmp_path))
    os.makedirs(tmp_path / "runs" / "prereg")
    (tmp_path / "runs" / "prereg" / "FROZEN").write_text("frozen by test")
    assert guard.require_frozen("unit test", root=str(tmp_path)) is True
    assert guard.guard_role("train", "x", root=str(tmp_path / "nowhere")) is True     # training role never needs the flag
    with pytest.raises(guard.TestFoldAccessError):
        guard.guard_role("test", "x", root=str(tmp_path / "nowhere"))


def _mini_isu_root(tmp_path):
    """a miniature ISU-style dataset + split in a temporary root (6 conditions x 2 cells)"""
    os.makedirs(tmp_path / "data" / "processed")
    os.makedirs(tmp_path / "runs" / "splits")
    cond = pd.DataFrame({"group": range(1, 7), "charge_c": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0], "discharge_c": [0.5, 1.0, 1.5, 2.0, 1.0, 0.5], "dod_pct": [30, 40, 50, 60, 70, 80]})
    cond.to_csv(tmp_path / "data" / "processed" / "isu_conditions.csv", index=False)
    rows = []
    for g in range(1, 7):
        for r in (1, 2):
            for w in range(0, 12):
                rows.append((f"G{g}C{r}", g, float(w), 1.0 - 0.01 * g * w ** 0.8, 0.3))
    pd.DataFrame(rows, columns=["cell", "group", "week", "retention", "capacity_ah"]).to_csv(tmp_path / "data" / "processed" / "isu_capacity.csv", index=False)
    folds = {"0": {"test_conditions": [5, 6], "test_cells": ["G5C1", "G5C2", "G6C1", "G6C2"], "train_conditions": [1, 2, 3, 4]}}
    import hashlib
    h = hashlib.sha256(json.dumps(folds, sort_keys=True).encode()).hexdigest()
    json.dump({"dataset": "ISU", "test": "B", "n_folds": 1, "folds": folds, "sha256_of_folds": h}, open(tmp_path / "runs" / "splits" / "isu_testB.json", "w"))
    return str(tmp_path)


def test_load_split_train_role_never_contains_test_cells(tmp_path):
    root = _mini_isu_root(tmp_path)
    sv = data.load_split("isu", "B", 0, role="train", root=root)
    assert sv.test_cells is None
    ids = {c.cell_id for c in sv.train}
    assert ids == {f"G{g}C{r}" for g in (1, 2, 3, 4) for r in (1, 2)}
    assert not (set(sv.train_conditions) & {"5", "6"})
    assert sv.hash_ok


def test_load_split_test_role_is_guarded(tmp_path):
    root = _mini_isu_root(tmp_path)
    with pytest.raises(guard.TestFoldAccessError):
        data.load_split("isu", "B", 0, role="test", root=root)
    os.makedirs(tmp_path / "runs" / "prereg", exist_ok=True)
    (tmp_path / "runs" / "prereg" / "FROZEN").write_text("x")
    sv = data.load_split("isu", "B", 0, role="test", root=root)
    assert {c.cell_id for c in sv.test_cells} == {"G5C1", "G5C2", "G6C1", "G6C2"}
    assert not ({c.cell_id for c in sv.test_cells} & {c.cell_id for c in sv.train})


@pytest.mark.skipif(REAL_FROZEN, reason="real FROZEN flag exists: the refusal cannot be tested against the real root")
@pytest.mark.parametrize("ds,test", [("isu", "B"), ("snl", "B"), ("samsung", "B"), ("samsung", "C"), ("samsung", "S2")])
def test_real_datasets_refuse_test_role_before_freeze(ds, test):
    with pytest.raises(guard.TestFoldAccessError):
        data.load_split(ds, test, 0, role="test")


@pytest.mark.parametrize("ds", ["isu", "snl"])
def test_real_train_view_disjoint_from_test(ds):
    sp = json.load(open(os.path.join(ROOT, "runs", "splits", f"{ds}_testB.json")))
    all_cells = set()
    tot = 0
    for f in sp["folds"]:
        sv = data.load_split(ds, "B", int(f), role="train")
        tc = set(sp["folds"][f]["test_cells"])
        assert not ({c.cell_id for c in sv.train} & tc)
        assert not ({c.cond for c in sv.train} & {str(x) for x in sp["folds"][f]["test_conditions"]})
        assert sv.hash_ok
        all_cells |= {c.cell_id for c in sv.train} | tc
        tot += 1
        if tot == 2:
            break
    assert len(all_cells) > 0


def test_samsung_train_view_through_guard():
    sp = json.load(open(os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json")))
    for test, fold in (("B", 0), ("B", 3), ("C", 0), ("S2", 1)):
        sv = data.load_split("samsung", test, fold, role="train")
        fd = sp[test]["folds"][str(fold)]
        assert not ({c.cell_id for c in sv.train} & set(fd["test_cells"]))
        assert not ({c.cond for c in sv.train} & set(fd["test_conditions"]))
        assert sv.hash_ok and sv.fold_hash_stored == sp[test]["sha256_of_folds"]
        for c in sv.train:
            assert c.kind in ("cycling", "storage") and c.t[0] == 0.0 and abs(c.ret[0] - 1.0) < 1e-9 and np.all(np.diff(c.t) >= 0)
            assert c.efc[0] == 0.0 and np.all(c.efc >= 0)
            if c.kind == "storage":
                assert c.meta["cell_no"] <= 3 and c.efc.max() == 0.0


def test_samsung_condition_keys_match_split_identifiers():
    sp = json.load(open(os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json")))
    known = set()
    for f in sp["B"]["folds"].values():
        known |= set(f["test_conditions"]) | set(f["train_cycling_conditions"])
    for k in ("S2",):
        for f in sp[k]["folds"].values():
            known |= set(f["test_conditions"])
    sv = data.load_split("samsung", "B", 0, role="train")
    cyc = {c.cond for c in sv.train if c.kind == "cycling"}
    assert cyc <= set(sp["B"]["folds"]["0"]["train_cycling_conditions"])
    assert all(c.cond in known or c.kind == "storage" for c in sv.train)


# ------------------------------------------------------------------------------------------------ throughput curve, window rule
def test_efc_curve_value_rate_and_causal_tail():
    t = np.array([0.0, 10.0, 20.0, 40.0])
    e = np.array([0.0, 5.0, 20.0, 30.0])
    full = EFCCurve(t, e)
    assert np.isclose(full.value(15.0), 12.5) and np.isclose(full.rate(15.0), 1.5) and np.isclose(full.rate(5.0), 0.5)
    assert np.isclose(full.tail, 30.0 / 40.0) and np.isclose(full.value(60.0), 30.0 + 0.75 * 20.0)
    caus = EFCCurve(t, e, upto=2)                      # window ends at t = 20: mean window rate 1.0 afterwards
    assert np.isclose(caus.value(30.0), 30.0) and np.isclose(caus.rate(30.0), 1.0)
    assert np.isclose(caus.value(10.0), 5.0)           # logged inside the window


def _cell(n=12, kind="cycling", ret=None):
    t = np.arange(n, dtype=float) * 7
    ret = np.linspace(1.0, 0.8, n) if ret is None else ret
    fc = np.ones(n, bool)
    fc[0] = False
    return Cell("c1", "samsung", kind, "k", np.array([23, 0.5, 0.2, 0.5, 1.0]), t, ret, t * 0.1, fc)


def test_window_forecast_split_count_rule_and_causality():
    rule = WindowRule.for_spec(SPECS["samsung"], k_cycling=4)
    p = prepare(_cell(), rule)
    assert len(p.win.t_win) == 5 and p.win.t_win[-1] == 28.0           # reference + k = 4 check-ups
    assert len(p.win.t_fc) == 7 and np.all(p.win.t_fc > p.win.t_win[-1])
    assert np.isclose(p.win.efc_curve.value(70.0), 2.8 + 0.1 * 42)       # window mean rate after the window
    po = prepare(_cell(), rule, oracle=True)
    assert np.isclose(po.win.efc_curve.value(70.0), 7.0)
    assert not hasattr(p.win, "fc_true")                                # the model-visible object carries no forecast label


def test_forecast_set_excludes_non_checkups_and_truncates_at_life():
    c = _cell(12, ret=np.array([1, .99, .98, .97, .96, .95, .9, .8, .69, .6, .5, .4]))
    c.fc_ok[6] = False                                                  # e.g. an AT or a failed QC point
    rule = WindowRule.for_spec(SPECS["samsung"], k_cycling=4)
    assert prepare(c, rule).win.t_fc.tolist() == [35.0, 49.0, 56.0, 63.0, 70.0, 77.0]
    rule2 = WindowRule(k_cycling=4, k_storage=2, life_level=0.70)
    p = prepare(c, rule2)
    assert p.win.t_fc.tolist() == [35.0, 49.0, 56.0]                    # ends at (and includes) the first point below 70 % (index 8, t = 56)
    assert p.fc_true[-1] < 0.70


def test_cells_that_cannot_be_scored_are_dropped():
    rule = WindowRule.for_spec(SPECS["samsung"], k_cycling=4)
    assert prepare(_cell(5), rule) is None                              # no forecast point
    assert prepare(_cell(12), WindowRule(k_cycling=1, k_storage=1)) is None   # window of 2 points < min_window_points 3


def test_window_rule_from_counts_matches_prereg_example():
    assert window_rule_from_counts([8, 15]) == (4, None)               # n_med 11.5 -> round(3.83) = 4
    assert window_rule_from_counts([8, 10, 10, 11], [7, 7, 8]) == (3, 2)


def test_time_window_rule_isu_style():
    c = _cell(10)
    c.t = np.arange(10, dtype=float)
    rule = WindowRule.for_spec(SPECS["isu"], W=4.0)
    p = prepare(c, rule)
    assert p.win.t_win.tolist() == [0.0, 1.0, 2.0, 3.0, 4.0]
