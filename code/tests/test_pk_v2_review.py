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
