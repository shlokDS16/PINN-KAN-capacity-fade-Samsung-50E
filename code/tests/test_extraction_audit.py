"""D022 A2: identifiability audit of the extracted laws (PREREG_v4 7.3 item 6): label rule, identifiable parameters, calibration tables, D021 regression, one code path, guard.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_extraction_audit.py -q"""
import glob
import json
import os
import shutil
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest
import torch

torch.set_num_threads(1)

from pinnkan import arms as A
from pinnkan import extraction_audit as X
from pinnkan import symbolic as S
from pinnkan import synth
from pinnkan.specs import SPECS

THR = X.load_thresholds()
INPUTS = THR["inputs"]
SPEC = SPECS["synthetic"]


def _law(arm="A15h1", fold=0, seed=0, fam="linear", sign=1, additive=True, approx=False, zero_inputs=()):
    return {"arm": arm, "fold": fold, "seed": seed, "h": 1, "outer_families": [],
            "inputs": {n: {"family": ("zero" if n in zero_inputs else fam), "sign": (0 if n in zero_inputs else sign), "bic_margin": 5.0, "edge_families": [fam], "additive": additive, "approx": approx} for n in INPUTS}}


def _laws(n=25, **kw):
    return [_law(fold=i // 5, seed=i % 5, **kw) for i in range(n)]


def _cell_perfect(arm="A15h1", m=32, rate=0.0, sign_err=0.0, n=20):
    """a calibration cell for every input with the given false-family rate (all truth families get n synthetic edges)"""
    cells = {}
    for name in INPUTS:
        wrong = int(round(rate * 2 * n))                    # for F: edges of the two other truths that chose F
        cells[f"{name}|{m}|{arm}"] = {"n": {t: n for t in X.ELIGIBLE}, "false_family_rate": {F: rate for F in X.ELIGIBLE}, "sign_error_rate": sign_err, "confusion": {}, "sign": {}}
    return cells


# ------------------------------------------------------------------------------------------------ thresholds, pin
def test_thresholds_file_matches_the_frozen_cap_and_is_hashed():
    assert THR["cap"] == S.library_file_cap() == 2 and tuple(THR["eligible_families"]) == ("zero", "linear", "log")
    assert X.thresholds_sha256() == X.sha256_file(X.THRESHOLDS_FILE) and len(X.thresholds_sha256()) == 64
    for k, v in (("pruned_min_share", 0.8), ("identified_min_share", 0.8), ("min_levels_identified", 3), ("max_false_family_rate", 0.1), ("max_sign_error_rate", 0.1),
                 ("min_synthetic_edges_per_truth_family", 20), ("approx_rms_over_range", 0.1)):
        assert THR[k] == v                                      # D022 judge 2.2a item 3
    assert set(THR["inputs"]) == set(SPEC.stress_names)


# ------------------------------------------------------------------------------------------------ identifiable parameters, levels
def test_an_input_with_L_levels_never_receives_more_than_L_minus_1_identifiable_parameters():
    for L in range(1, 9):
        for fam in ("zero", "linear", "log"):
            k = X.identifiable_parameters(fam, L)
            assert k <= max(L - 1, 0) and (k == 0 if fam == "zero" or L == 1 else k == 1)
    assert X.identifiable_parameters("linear", 2) == 1 and X.identifiable_parameters("linear", 3) == 1 and X.identifiable_parameters("zero", 5) == 0


def test_design_levels_of_the_real_folds_are_three_temperatures_from_identifiers_only():
    sp = json.load(open(os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json")))["B"]["folds"]
    sub = json.load(open(os.path.join(ROOT, "runs", "prereg", "subsets.json")))["folds"]
    for f in sp:
        for ids in (sp[f]["train_cycling_conditions"], sub[f]["subsets"]["8"]):
            lv = X.distinct_levels(ids)
            assert lv["T_C"] == 3 and all(1 <= v <= len(ids) for v in lv.values())


# ------------------------------------------------------------------------------------------------ label rule
def test_pruned_needs_80_percent_zero_laws():
    laws = [_law(fold=i // 5, seed=i % 5, zero_inputs=("dod",) if i < 20 else ()) for i in range(25)]       # 20 of 25
    lab = X.label_law(laws, {n: 5 for n in INPUTS}, {}, 32, "A15h1")
    assert lab["dod"]["label"] == "pruned"
    laws = [_law(fold=i // 5, seed=i % 5, zero_inputs=("dod",) if i < 19 else ()) for i in range(25)]       # 19 of 25 = 76 %
    assert X.label_law(laws, {n: 5 for n in INPUTS}, {}, 32, "A15h1")["dod"]["label"] != "pruned"


def test_identified_requires_all_four_conditions_and_abstains_otherwise():
    lv = {n: 5 for n in INPUTS}
    cal = _cell_perfect()
    ok = X.label_law(_laws(), lv, cal, 32, "A15h1")["dod"]
    assert ok["label"] == "identified" and ok["family"] == "linear" and X.label_text(ok) == "identified: linear" and ok["identifiable_parameters"] == 1
    # (i) L_e = 2: never 'identified: <family>', at most 'sign identified'
    lv2 = dict(lv, dod=2)
    two = X.label_law(_laws(), lv2, cal, 32, "A15h1")["dod"]
    assert two["label"] == "sign" and two["sign"] == 1 and "L_e = 2" in " ".join(two["reasons"])
    assert X.label_law(_laws(), dict(lv, dod=1), cal, 32, "A15h1")["dod"]["label"] == "sign"
    # (ii) family unstable (60 % linear, 40 % log) but the sign is stable: sign identified
    mixed = [_law(fold=i // 5, seed=i % 5, fam="linear" if i % 5 < 3 else "log") for i in range(25)]
    assert X.label_law(mixed, lv, cal, 32, "A15h1")["dod"]["label"] == "sign"
    # sign unstable as well: ambiguous
    flip = [_law(fold=i // 5, seed=i % 5, fam="linear" if i % 5 < 3 else "log", sign=1 if i % 2 else -1) for i in range(25)]
    assert X.label_law(flip, lv, cal, 32, "A15h1")["dod"]["label"] == "ambiguous"
    # (iii) calibration: false-family rate above 0.10, missing cell, too few synthetic edges
    assert X.label_law(_laws(), lv, _cell_perfect(rate=0.15), 32, "A15h1")["dod"]["label"] in ("ambiguous", "sign") and X.label_law(_laws(), lv, _cell_perfect(rate=0.10), 32, "A15h1")["dod"]["label"] == "identified"
    assert X.label_law(_laws(), lv, {}, 32, "A15h1")["dod"]["label"] == "ambiguous"
    assert X.label_law(_laws(), lv, _cell_perfect(n=19), 32, "A15h1")["dod"]["label"] == "ambiguous"
    assert X.label_law(_laws(), lv, _cell_perfect(), 8, "A15h1")["dod"]["label"] == "ambiguous"              # wrong m: the cell is not the matching one
    # sign calibration too bad: ambiguous even with a stable sign
    assert X.label_law(_laws(), lv, _cell_perfect(rate=0.5, sign_err=0.2), 32, "A15h1")["dod"]["label"] == "ambiguous"
    # (iv) not additive: composed
    comp = X.label_law(_laws(additive=False), lv, cal, 32, "A15h1")["dod"]
    assert comp["label"] == "composed" and X.label_text(comp) == "composed: no single form" and "not additive" in " ".join(comp["reasons"])
    # the 80 % thresholds are inclusive at 20 of 25
    edge = [_law(fold=i // 5, seed=i % 5, fam="linear" if i < 20 else "log") for i in range(25)]
    assert X.label_law(edge, lv, cal, 32, "A15h1")["dod"]["label"] == "identified"
    edge = [_law(fold=i // 5, seed=i % 5, fam="linear" if i < 19 else "log") for i in range(25)]
    assert X.label_law(edge, lv, cal, 32, "A15h1")["dod"]["label"] != "identified"


def test_approximation_flag_and_the_input_sentences():
    lv = {n: 5 for n in INPUTS}
    lab = X.label_law(_laws(approx=True), lv, _cell_perfect(), 32, "A15h1")["dod"]
    assert lab["approximate"] and "the cap-2 form is an approximation of a curved learned effect" in X.input_notes(lab)
    amb = X.label_law(_laws(), lv, {}, 32, "A15h1")["dod"]
    assert "the training design does not identify the form of this effect" in X.input_notes(amb) and not amb["approximate"]


def test_fixed_results_sentence_and_counts():
    lv = {"T_C": 3, "soc_mid": 5, "dod": 2, "c_ch": 5, "c_dch": 5}
    laws = [_law(fold=i // 5, seed=i % 5, zero_inputs=("c_dch",)) for i in range(25)]
    cal = {k: v for k, v in _cell_perfect().items() if not k.startswith("soc_mid")}                       # no calibration cell for soc_mid
    lab = X.label_law(laws, lv, cal, 32, "A15h1")
    s = X.results_sentence(lab, "A15")
    assert s["counts"] == {"n": 5, "identified": 2, "sign": 1, "ambiguous": 1, "pruned": 1}               # T and c_ch identified; dod (L = 2) sign only; soc_mid ambiguous; c_dch pruned
    assert s["results"] == "Of the 5 inputs of the extracted KAN law, the training design identified the form of 2 and the sign of 1; 1 were ambiguous and are reported without a named form."
    assert X.results_sentence(lab, "G15")["results"].startswith("Of the 5 inputs of the extracted additive law,") and s["pruned"].startswith("1 of the 5 inputs were pruned")
    assert THR["wording"]["discussion_sentence"].startswith("Readable means that the extracted law is a short closed form")


def test_audit_arm_table_has_the_required_columns_and_the_bic_caveat():
    lv = {n: 5 for n in INPUTS}
    out = X.audit_arm(_laws(arm="G15"), lv, _cell_perfect(arm="G15"), 32, "G15")
    assert len(out["table"]) == 5
    row = out["table"][0]
    assert {"arm", "input", "levels", "eligible_families", "identifiable_parameters", "chosen_family", "bic_margin_median", "share_family", "share_sign", "label", "notes", "bic_caveat"} <= set(row)
    assert row["eligible_families"] == ["zero", "linear", "log"] and "KAN's grid" in row["bic_caveat"] and out["sentences"]["counts"]["identified"] == 5


# ------------------------------------------------------------------------------------------------ calibration tables
def test_calibration_rates_and_exact_intervals():
    recs = []
    for t in X.ELIGIBLE:
        for j in range(20):
            chosen = t
            if t == "log" and j < 3:
                chosen = "linear"                       # 3 of 20 log truths read as linear
            recs.append({"arm": "G15", "m": 32, "input": "dod", "truth": t, "truth_sign": 1, "chosen": chosen, "sign": 1 if not (t == "linear" and j < 2) else -1})
    recs.append({"arm": "G15", "m": 32, "input": "dod", "truth": "quadratic", "truth_sign": 1, "chosen": "linear", "sign": 1})        # curved rows never enter the rates
    c = X.calibration_tables(recs)["dod|32|G15"]
    assert c["n"] == {"zero": 20, "linear": 20, "log": 20}
    assert c["false_family_rate"]["linear"] == pytest.approx(3 / 40) and c["false_family_rate"]["zero"] == 0.0 and c["false_family_rate"]["log"] == pytest.approx(0.0)
    assert c["sign_error_rate"] == pytest.approx(2 / 40) and c["sign_n"] == 40
    lo, hi = c["false_family_ci"]["linear"]
    assert lo < 3 / 40 < hi
    assert X.clopper_pearson(0, 20)[0] == 0.0 and X.clopper_pearson(20, 20)[1] == 1.0 and X.clopper_pearson(5, 20) == pytest.approx((0.0866, 0.4910), abs=1e-3)


# ------------------------------------------------------------------------------------------------ D021 regression and one code path
def test_audit_reproduces_the_D021_false_structure_counts_on_the_D021_seeds():
    files = glob.glob(os.path.join(ROOT, "runs", "D021_cap_synth", "pipeline_p*.jsonl"))
    assert files
    recs = [json.loads(l) for f in files for l in open(f, encoding="utf8")]
    assert X.false_structure_counts(recs, 3, "A15h1", 32) == (37, 40) and X.false_structure_counts(recs, 3, "G15", 32) == (37, 40)
    for arm in ("A15h1", "A15h2", "G15"):
        for m in (32, 8):
            assert X.false_structure_counts(recs, 2, arm, m) == (0, 40)                                    # cap 2: no 3-coefficient form exists
    assert X.false_structure_counts(recs, 3, "A15h1", 8)[0] == 32


def test_a15_and_g15_go_through_one_code_path_and_the_extraction_is_cap_2():
    S0 = synth.make_synthetic("G0", n_cyc_cond=12, n_sto_cond=5, reps=2, seed=3)
    tr, _ = synth.split_conditions(S0.cells, 0.25, 3)
    ctx = {"backbone": "self_limiting", "steps_scale": 0.15, "symbolic": {"cap": 2}}
    laws = {}
    for key, arm_id, over in (("A15h1", "A15", {"h": 1}), ("A15h2", "A15", {"h": 2}), ("G15", "G15", {})):
        arm = A.make_arm(arm_id, SPEC, {**A.default_hp(arm_id), **over}, 0, ctx).fit(tr)
        assert arm.report["cap"] == 2
        laws[key] = X.law_record(key, 0, 0, arm.report, SPEC, arm.model.law.cyc, arm.parent_cyc, arm.s_cyc_train)
    assert laws["A15h1"]["h"] == 1 and laws["A15h2"]["h"] == 2 and laws["G15"]["h"] == 1 and laws["G15"]["outer_families"] == []
    for rec in laws.values():
        assert set(rec["inputs"]) == set(INPUTS)
        for r in rec["inputs"].values():
            assert r["family"] in ("zero", "linear", "log", "composed") and r["sign"] in (-1, 0, 1) and isinstance(r["approx"], bool)
            assert all(f in ("zero", "linear", "log") for f in r["edge_families"])                 # cap 2: no 3-coefficient family can appear
    assert X.audit_arm([laws["G15"]], {n: 4 for n in INPUTS}, {}, 32, "G15")["labels"].keys() == X.audit_arm([laws["A15h1"]], {n: 4 for n in INPUTS}, {}, 32, "A15")["labels"].keys()
    assert X.label_law.__module__ == X.audit_arm.__module__ == "pinnkan.extraction_audit"


# ------------------------------------------------------------------------------------------------ synthetic truths on the real design
def test_truth_effects_and_the_synthetic_generator_on_a_given_design():
    x = np.linspace(1.0, 5.0, 11)
    for fam in ("linear", "log", "hinge"):
        e = X_truth(fam, 1, x)
        assert e[0] == pytest.approx(-0.5) and e[-1] == pytest.approx(0.5)
        assert np.allclose(X_truth(fam, -1, x), -e)
    q = X_truth("quadratic", 1, x)
    assert q[0] == pytest.approx(0.5) and q[-1] == pytest.approx(0.5) and q[5] == pytest.approx(-0.5)
    assert np.all(X_truth("zero", 1, x) == 0)
    sp = json.load(open(os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json")))
    ids = sp["B"]["folds"]["0"]["train_cycling_conditions"]
    sto = sorted({c for f in sp["S2"]["folds"].values() for c in f["test_conditions"]})
    design = synth.design_from_keys(ids, sto, 2)
    assert len(design[0]) == 32 and len(design[1]) == 19
    T = {0: ("linear", 1, 296.15, 318.15), 1: ("zero", 1, 0.2, 0.9), 2: ("log", -1, 0.05, 0.6), 3: ("linear", -1, 0.2, 1.0), 4: ("zero", 1, 0.2, 2.0)}
    S0 = synth.make_synthetic("GA", reps=2, seed=1, design=design, truth=T)
    cyc = [c for c in S0.cells if c.kind == "cycling"]
    assert len({c.cond for c in cyc}) == 32 and len(cyc) == 64 and len({c.cond for c in S0.cells if c.kind == "storage"}) == 19
    raw = np.array([c.raw for c in cyc])
    f = np.asarray(S0.log_rate_cyc(raw)).ravel() - S0.params["c_cyc"]
    ref = sum(synth.truth_effect(fam, sg, raw[:, i] + (273.15 if i == 0 else 0.0), lo, hi) for i, (fam, sg, lo, hi) in T.items())
    assert np.allclose(f, ref)


def X_truth(fam, sign, x):
    return synth.truth_effect(fam, sign, x, 1.0, 5.0)


# ------------------------------------------------------------------------------------------------ the guard
def test_edge_wording_needs_the_calibration_table_hashed_before_any_outer_score(tmp_path):
    cdir = str(tmp_path / "cal")
    runs = tmp_path / "run"
    runs.mkdir()
    sc = runs / "condition_scores.json"
    sc.write_text("{}")
    with pytest.raises(X.AuditGuardError, match="no calibration table"):
        X.require_calibration(cdir, [str(runs)])
    rec = X.write_calibration_record(cdir, {"cells": {"dod|32|G15": {"n": {}}}})
    old = time.time() - 5000
    os.utime(os.path.join(cdir, X.CALIBRATION_FILE), (old, old))
    h = os.path.join(cdir, X.CALIBRATION_HASH)
    r = json.load(open(h))
    r["written_unix"] = old
    json.dump(r, open(h, "w"))
    assert X.require_calibration(cdir, [str(runs)], X.thresholds_sha256()) == {"dod|32|G15": {"n": {}}}
    with pytest.raises(X.AuditGuardError, match="other thresholds"):
        X.require_calibration(cdir, [str(runs)], "0" * 64)
    os.utime(sc, (old - 100, old - 100))
    with pytest.raises(X.AuditGuardError, match="after an outer score"):
        X.require_calibration(cdir, [str(runs)])
    os.utime(sc, (time.time(), time.time()))
    r["thresholds_sha256"] = "1" * 64
    json.dump(r, open(h, "w"))
    with pytest.raises(X.AuditGuardError, match="other thresholds"):
        X.require_calibration(cdir, [str(runs)])
    r["thresholds_sha256"] = X.thresholds_sha256()
    json.dump(r, open(h, "w"))
    with open(os.path.join(cdir, X.CALIBRATION_FILE), "w") as fh:
        json.dump({"cells": {}}, fh)
    with pytest.raises(X.AuditGuardError, match="altered"):
        X.require_calibration(cdir, [str(runs)])
