"""P6b (D020 judge section 4): unit tests for rule R2', the ensemble endpoint, the pooled log ratio and the fold frame. No model is fitted.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_p6b_rule.py -q"""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "pilots"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

import p6b_inner_folds as P

ARMS = ["A1", "A2", "A4", "A9", "A11", "A12"]
FLOOR = -math.log(1.02)


def test_rule_adopts_five_of_six_with_floor_respected():
    q = dict(zip(ARMS, [0.05, 0.02, 0.01, 0.03, 0.04, -0.015]))
    assert P.rule_verdict(q, ARMS)["adopt"] is True


def test_rule_keeps_when_only_four_positive():
    q = dict(zip(ARMS, [0.05, 0.02, 0.01, 0.03, -0.001, -0.002]))
    assert P.rule_verdict(q, ARMS)["adopt"] is False


def test_rule_keeps_when_one_arm_below_the_floor_even_if_five_positive():
    q = dict(zip(ARMS, [0.05, 0.02, 0.01, 0.03, 0.04, FLOOR - 1e-6]))
    v = P.rule_verdict(q, ARMS)
    assert v["adopt"] is False and v["n_positive"] == 5


def test_rule_floor_is_strict():
    q = dict(zip(ARMS, [0.05, 0.02, 0.01, 0.03, 0.04, FLOOR]))
    assert P.rule_verdict(q, ARMS)["adopt"] is False          # min q must be strictly greater than -ln(1.02)


def test_rule_zero_is_not_positive():
    q = dict(zip(ARMS, [0.05, 0.02, 0.01, 0.03, 0.0, 0.0]))
    assert P.rule_verdict(q, ARMS)["adopt"] is False


def test_rule_incomplete_or_nonfinite_means_default():
    q = dict(zip(ARMS, [0.05] * 6))
    q["A11"] = float("nan")
    assert P.rule_verdict(q, ARMS)["adopt"] is False
    del q["A11"]
    assert P.rule_verdict(q, ARMS)["adopt"] is False


def test_rule_all_positive():
    assert P.rule_verdict({a: 0.01 for a in ARMS}, ARMS)["adopt"] is True


def test_ensemble_never_worse_than_mean_of_seed_rmse():
    rng = np.random.default_rng(0)
    truth = rng.uniform(0.7, 1.0, 12)
    seeds = [{"c": truth + rng.normal(0, 0.02, 12)} for _ in range(5)]
    ens = P.ensemble_forecasts(seeds)["c"]
    rm = lambda p: np.sqrt(np.mean((p - truth) ** 2))
    assert rm(ens) <= np.mean([rm(s["c"]) for s in seeds]) + 1e-12


def test_ensemble_equals_single_fit_when_seeds_agree():
    f = np.linspace(0.95, 0.8, 7)
    ens = P.ensemble_forecasts([{"c": f.copy()} for _ in range(5)])["c"]
    assert np.allclose(ens, f)


def test_nonfinite_is_replaced_seedwise_before_averaging():
    ylast = {"c": 0.9}
    a = {"c": np.array([0.88, np.nan, 0.84])}
    b = {"c": np.array([0.86, 0.85, 0.82])}
    ca, na = P.clean_seedwise(a, ylast)
    cb, nb = P.clean_seedwise(b, ylast)
    assert na == 1 and nb == 0
    ens = P.ensemble_forecasts([ca, cb])["c"]
    assert np.allclose(ens, [0.87, (0.9 + 0.85) / 2, 0.83]) and np.all(np.isfinite(ens))


def test_pooled_log_ratio_means_over_folds_in_which_condition_is_pseudo_test():
    a = {0: {"x": 2.0, "y": 3.0}, 1: {"x": 4.0}}
    b = {0: {"x": 1.0, "y": 3.0}, 1: {"x": 1.0}}
    pooled, nf = P.pooled_log_ratio(a, b)
    assert nf == {"x": 2, "y": 1}
    assert pooled["x"] == pytest.approx((math.log(2.0) + math.log(4.0)) / 2) and pooled["y"] == pytest.approx(0.0)
    assert P.median_q(pooled) == pytest.approx(np.median([pooled["x"], pooled["y"]]))


def test_edge_hits_flags_ends_of_ordered_grids_only():
    from pinnkan.arms import ARMS as A
    h = P.edge_hits(A["A1"].space, {"h": 4, "grid": 12, "l2": 1e-5, "sparsity": 0.0, "lam_res": 1e-3, "placement": "record_end"})
    assert h == {"h": False, "grid": True, "l2": True, "sparsity": True, "lam_res": True}
    h = P.edge_hits(A["A12"].space, {"n_est": 300, "lr": 0.299, "leaves": 4, "mcs": 30, "l2": 0.1, "feat": "raw", "storage": "in"})
    assert h["lr"] is True and h["leaves"] is True and h["n_est"] is False and h["l2"] is False and "feat" not in h


def test_fold_frame_has_8_pseudo_train_conditions_and_no_outer_test_overlap():
    if not os.path.exists(os.path.join(ROOT, "data", "processed", "isu_capacity.csv")):
        pytest.skip("ISU processed data not on disk")
    import json
    cfg = json.load(open(os.path.join(ROOT, "code", "pilots", "p6b_config.json")))
    for f in (0, 3):
        D = P.fold_data(f, cfg)
        a = D["audit"]
        assert a["n_pseudo_train_conditions"] == 8 and len(D["kept"]) == 8
        assert a["intersection_conditions_with_outer_test"] == 0 and a["intersection_cells_with_outer_test"] == 0 and a["test_fold_scored"] is False
        assert a["n_pseudo_test_conditions"] + 8 == a["n_training_conditions"] or a["n_pseudo_test_conditions"] + 8 <= a["n_training_conditions"]
        assert D["rule"].W == 2.0 and a["window_W"] == 2.0 and a["fold_hash_ok"]
        assert not ({c.cond for c in D["train"]} & {c.cond for c in D["test"]})
