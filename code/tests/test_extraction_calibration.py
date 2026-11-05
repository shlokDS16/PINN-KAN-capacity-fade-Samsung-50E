"""D022 A2: calibration script (plan, seeds, guard, finalize), the config pins of the audit files and the statistics-step guard for edge-level wording. The calibration itself is NOT run
here (A4 runs it from the FROZEN commit); only a smoke dataset with tiny settings."""
import hashlib
import importlib.util
import json
import os
import sys
import time
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

from pinnkan import extraction_audit as X
from pinnkan import guard, run, stats_step as ss, stats_v4 as v4
from test_pk_v2_review import _grid_runs, _item_f_before

spec_ = importlib.util.spec_from_file_location("extraction_calibration", os.path.join(ROOT, "code", "prereg", "extraction_calibration.py"))
C = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(C)
INPUTS = X.load_thresholds()["inputs"]


# ------------------------------------------------------------------------------------------------ the plan
def test_plan_counts_assignment_table_and_minimum_edges_per_cell():
    assert C.plan_counts() == {"datasets": 240, "fits": 600, "by_block": {"additive": 360, "curved": 180, "noadd": 60}}
    n = C.edges_per_cell()
    assert len(n) == 5 * 2 * 3 * 3 and min(n.values()) == max(n.values()) == 20                      # exactly the 20 synthetic edges per (input, m, arm, truth family) the rule requires
    for j in range(12):
        tf = C.truth_families("additive", j)
        assert [f for f, _ in tf] == [C.FAM[(j + i) % 3] for i in range(5)] and [s for _, s in tf] == [1 if (j + i) % 2 == 0 else -1 for i in range(5)]
    assert all(f in C.CURVE for f, _ in C.truth_families("curved", 3))
    assert [c["arms"] for c in C.plan() if c["block"] == "noadd"][0] == ["A15h2"]


def test_dataset_seeds_follow_the_rule_and_are_unique():
    s = C.dataset_seed("additive", 2, 8, 5)
    assert s == int(np.random.SeedSequence([20261105, zlib.crc32(b"calib|additive|f2|m8|j5")]).generate_state(1)[0]) == C.dataset_seed("additive", 2, 8, 5)
    assert len({c["seed"] for c in C.plan()}) == 240


def test_fold_design_uses_the_pinned_subsets_and_the_s2_storage_identifiers():
    cyc, sto = C.fold_design(0, 8)
    sub = json.load(open(os.path.join(ROOT, "runs", "prereg", "subsets.json")))["folds"]["0"]["subsets"]["8"]
    assert cyc == sub and len(sto) == 19 and len(C.fold_design(3, 32)[0]) == 32


# ------------------------------------------------------------------------------------------------ guard
def test_the_calibration_refuses_to_run_off_the_frozen_commit_or_after_an_outer_score(tmp_path, monkeypatch):
    with pytest.raises(C.CalibrationGuardError, match="frozen"):
        C.require_run_conditions(str(tmp_path))
    monkeypatch.setattr(guard, "verify_freeze", lambda root=None, check_git=True: {"commit": "x"})
    assert C.require_run_conditions(str(tmp_path)) == {"commit": "x"}
    (tmp_path / "runs" / "prereg").mkdir(parents=True)
    (tmp_path / "runs" / "prereg" / "SCORED.jsonl").write_text("")
    assert C.require_run_conditions(str(tmp_path))
    (tmp_path / "runs" / "prereg" / "SCORED.jsonl").write_text('{"x": 1}\n')
    with pytest.raises(C.CalibrationGuardError, match="outer score"):
        C.require_run_conditions(str(tmp_path))


def test_finalize_refuses_an_incomplete_calibration(tmp_path):
    with pytest.raises(C.CalibrationGuardError, match="incomplete"):
        C.finalize(str(tmp_path))


def test_a_smoke_dataset_has_the_record_schema_and_finalize_writes_a_hashed_table(tmp_path):
    out = str(tmp_path / "smoke")
    C.main(["--smoke", out, "--limit", "1"])
    assert os.path.exists(os.path.join(out, "SMOKE"))
    recs = [json.loads(l) for l in open(os.path.join(out, "records_p0.jsonl"))]
    assert len(recs) == 3 * 5 and {r["arm"] for r in recs} == {"A15h1", "A15h2", "G15"} and {r["input"] for r in recs} == set(INPUTS)
    tf = C.truth_families("additive", 0)
    for r in recs:
        i = list(INPUTS).index(r["input"])
        assert r["block"] == "additive" and r["truth"] == tf[i][0] and r["chosen"] in ("zero", "linear", "log", "composed") and r["sign"] in (-1, 0, 1)
    rec, cal = C.finalize(out, require_complete=False)
    assert rec["thresholds_sha256"] == X.thresholds_sha256() and cal["rule_sha256"] == C.rule_sha256() and cal["plan"]["fits"] == 600 and cal["cells_below_minimum_n"]
    assert os.path.exists(os.path.join(out, X.CALIBRATION_HASH))
    assert C.rule_sha256() == hashlib.sha256(open(C.RULE_FILE, "rb").read()).hexdigest()


# ------------------------------------------------------------------------------------------------ config pins and run output
CFG = {"dataset": "synthetic", "arms": ["A15"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.05, "seeds": [0, 1], "mode": "confirmatory", "diagnostics": False,
       "symbolic": {"cap": 2}, "synthetic": {"kind": "G0", "n_cyc_cond": 16, "n_sto_cond": 6, "reps": 2, "seed": 3}}


def test_the_audit_thresholds_and_the_rule_file_hashes_are_config_keys_that_must_match(tmp_path):
    with pytest.raises(run.ConfigError, match="extraction_audit_sha256"):
        run.run({**CFG, "run_id": "a", "extraction_audit_sha256": "0" * 64}, runs_dir=str(tmp_path))
    with pytest.raises(run.ConfigError, match="calibration_rule_sha256"):
        run.run({**CFG, "run_id": "b", "calibration_rule_sha256": "0" * 64}, runs_dir=str(tmp_path))
    with pytest.raises(run.ConfigError, match="required"):
        run.run({"run_id": "c", "dataset": "isu", "test": "B", "fold": 0, "mode": "confirmatory", "arms": ["A15"]}, runs_dir=str(tmp_path))
    d = run.run({**CFG, "run_id": "ok", "extraction_audit_sha256": X.thresholds_sha256(), "calibration_rule_sha256": C.rule_sha256()}, runs_dir=str(tmp_path))
    cfg = json.load(open(os.path.join(d, "config.json")))
    assert cfg["extraction_audit_sha256"] == X.thresholds_sha256() and cfg["calibration_rule_sha256"] == C.rule_sha256()                  # part of the hashed config
    el = json.load(open(os.path.join(d, "extracted_laws.json")))
    assert len(el["laws"]) == 2 and {l["seed"] for l in el["laws"]} == {0, 1} and el["levels"]["T_C"] >= 2 and el["extraction_audit_sha256"] == X.thresholds_sha256()
    assert all(l["arm"].startswith("A15h") for l in el["laws"])
    d2 = run.run({**CFG, "run_id": "none", "arms": ["R2"]}, runs_dir=str(tmp_path))
    assert not os.path.exists(os.path.join(d2, "extracted_laws.json"))


# ------------------------------------------------------------------------------------------------ the statistics-step guard
def _with_laws(dirs):
    for d in dirs:
        cfg = json.load(open(os.path.join(d, "config.json")))
        if cfg["m"] != 32:
            continue
        one = {"family": "linear", "sign": 1, "bic_margin": 4.0, "edge_families": ["linear"], "additive": True, "approx": False}
        laws = [{"arm": "A15h1", "fold": cfg["fold"], "seed": s, "h": 1, "outer_families": [], "inputs": {n: dict(one) for n in INPUTS}} for s in range(5)]
        laws += [dict(l, arm="G15") for l in laws]
        json.dump({"m": 32, "fold": cfg["fold"], "laws": laws, "levels": {"T_C": 3, "soc_mid": 6, "dod": 5, "c_ch": 5, "c_dch": 6}}, open(os.path.join(d, "extracted_laws.json"), "w"))


def _calibration(cdir, rate=0.0):
    cells = {}
    for arm in ("A15h1", "G15"):
        for n in INPUTS:
            cells[f"{n}|32|{arm}"] = {"n": {t: 20 for t in X.ELIGIBLE}, "false_family_rate": {t: rate for t in X.ELIGIBLE}, "sign_error_rate": 0.0}
    X.write_calibration_record(cdir, {"cells": cells})
    old = time.time() - 9000
    os.utime(os.path.join(cdir, X.CALIBRATION_FILE), (old, old))
    h = os.path.join(cdir, X.CALIBRATION_HASH)
    r = json.load(open(h))
    r["written_unix"] = old
    json.dump(r, open(h, "w"))


def test_the_statistics_step_prints_edge_wording_only_with_a_valid_calibration_table(tmp_path):
    tmp = str(tmp_path)
    os.makedirs(tmp + "/g")
    dirs = _grid_runs(tmp + "/g")
    _with_laws(dirs)
    fdir, sha = _item_f_before(tmp, dirs)
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    assert out["edge_wording"]["printed"] is False and "without named edge families" in out["edge_wording"]["reason"]            # default: the law only
    with pytest.raises(X.AuditGuardError, match="no calibration table"):
        ss.run_stats_v4(os.path.join(tmp, "an2"), dirs, item_f_dir=fdir, audit_dir=os.path.join(tmp, "nocal"))
    cdir = os.path.join(tmp, "cal")
    _calibration(cdir)
    out = ss.run_stats_v4(os.path.join(tmp, "an3"), dirs, item_f_dir=fdir, audit_dir=cdir)
    ew = out["edge_wording"]
    assert ew["printed"] and set(ew["arms"]) == {"A15", "G15"} and ew["discussion_sentence"].startswith("Readable means")
    assert ew["arms"]["A15"]["sentences"]["results"] == "Of the 5 inputs of the extracted KAN law, the training design identified the form of 5 and the sign of 0; 0 were ambiguous and are reported without a named form."
    assert ew["arms"]["G15"]["sentences"]["results"].startswith("Of the 5 inputs of the extracted additive law,")
    lab = ew["arms"]["A15"]["labels"]
    assert lab["T_C"]["label"] == "identified" and lab["T_C"]["levels"] == 3 and lab["T_C"]["n_laws"] == 25
    # a calibration with a high false-family rate abstains (the law is still printed)
    cdir2 = os.path.join(tmp, "cal2")
    _calibration(cdir2, rate=0.3)
    out2 = ss.run_stats_v4(os.path.join(tmp, "an4"), dirs, item_f_dir=fdir, audit_dir=cdir2)
    assert out2["edge_wording"]["arms"]["A15"]["sentences"]["counts"]["identified"] == 0
    # a calibration written after an outer score file exists is refused
    cdir3 = os.path.join(tmp, "cal3")
    _calibration(cdir3)
    time.sleep(0.05)
    X.write_calibration_record(cdir3, json.load(open(os.path.join(cdir, X.CALIBRATION_FILE))))
    with pytest.raises(X.AuditGuardError, match="after an outer score"):
        ss.run_stats_v4(os.path.join(tmp, "an5"), dirs, item_f_dir=fdir, audit_dir=cdir3)
