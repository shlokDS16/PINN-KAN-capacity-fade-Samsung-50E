"""Fixes of the independent review of build_v2 (runs/build_v2/CODE_REVIEW.md): one test per finding.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_v2_review.py -q"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

from pinnkan import stats_rows as R
from pinnkan import stats_v4 as v4
from test_pk_v2_stats import CONDS, FOLD, LABS, make_store


# ------------------------------------------------------------------------------------------------ I1
def test_I1_the_T9_clause_takes_W_only_from_forms_that_are_reverse_S():
    store = make_store(A10g1=-0.5)                                  # both forms better than A1 by exp(0.5)
    store.tables[(8, "2")]["A10P"] = {c: 2.0 * np.exp(0.1) for c in CONDS}        # the as-published form is WORSE than A1: not reverse S, its effect is negative
    out = v4.run_v4(store)
    o = out["outcome"]
    assert o["M2"] and out["secondary"]["tests"]["QA10_g1"]["reverse_S"]["A10"]["rejected"] and not out["secondary"]["tests"]["QA10_g1"]["reverse_S"]["A10P"]["rejected"]
    assert o["abstract_sentence"].endswith("was 39.3 % more accurate still at this cell (95 % interval [39.3, 39.3]).")
    assert "-" not in o["abstract_sentence"].split("semi-empirical model was")[1]            # no negative effect printed


# ------------------------------------------------------------------------------------------------ I2
def test_I2_most_is_recomputed_under_the_downgrade_rows():
    good = make_store(P1g1=np.log(1.3), A9g1=np.log(1.2))            # d_c > 0 for every condition
    bad = make_store(P1g1=np.log(1.6), A9g1=np.log(1.1))             # same P1 / P2 / P3 outcomes, but the law share is below half of the total: d_c < 0
    rule = v4.resolve_config()[0]
    out = v4.run_v4(good)
    assert out["most_test"]["most"]
    assert R.row_tiers(out, good, rule)["most"] is True and R.row_tiers(out, bad, rule)["most"] is False
    assert R.row_tiers(out, bad, rule, cells="g1")["most"] is False              # row (iv) covers it too
    full = R.run_v4_full(good, {"e1_prime_approved": True}, retain_all=bad, B=500)
    assert full["downgrade"]["lowest_over_rows"]["most"] is False and full["most_test"]["most"] is False
    assert full["outcome"]["extent_clause"] == "e1'" and "most of the advantage" not in full["outcome"]["abstract_sentence"]
    lab = R.lab_stratified_tiers(out, good, B=500)[0]
    assert lab["most"] is True
    labs = {c: ("A" if i < 32 else "B") for i, c in enumerate(CONDS)}
    store = make_store(P1g1=np.log(1.3), A9g1=np.array([np.log(1.2)] * 32 + [np.log(1.01)] * 8))
    store.lab = labs
    assert R.lab_stratified_tiers(v4.run_v4(store), store, B=500)[0]["most"] is not None
