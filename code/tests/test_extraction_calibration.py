"""D022a: calibration script (dataset-level design, strata, seeds, hyperparameter draws, laboratory aliasing, scoring, C1-C3, resume, CPU cap, guard, bit-identical re-run), the config pins of the
audit files and the statistics-step guard for edge-level wording. The calibration itself is NOT run here (it runs from the FROZEN commit); only one (dataset, fold) with tiny settings."""
import ast
import hashlib
import importlib.util
import json
import os
import sys
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

from pinnkan import arms as A
from pinnkan import extraction_audit as X
from pinnkan import guard, run, stats_step as ss, synth
from test_pk_v2_review import _grid_runs, _item_f_before

spec_ = importlib.util.spec_from_file_location("extraction_calibration", os.path.join(ROOT, "code", "prereg", "extraction_calibration.py"))
C = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(C)
THR = X.load_thresholds()
INPUTS = THR["inputs"]


@pytest.fixture
def labmap(monkeypatch):
    """a laboratory for every cycling condition of the five folds (the real cell table is incomplete while the download runs); tests never depend on untracked data"""
    sub = json.load(open(os.path.join(ROOT, "runs", "prereg", "subsets.json")))["folds"]
    keys = sorted({c for f in sub.values() for c in f["subsets"]["32"]})
    lm = {k: ("HM", "INT", "SIE")[i % 3] for i, k in enumerate(keys)}
    monkeypatch.setattr(C, "majority_labs", lambda root=C.ROOT: (lm, "h" * 8))
    return lm


# ------------------------------------------------------------------------------------------------ the plan, strata, interactions, amplitudes
def test_plan_counts_and_work_items():
    assert C.plan_counts() == {"datasets": 30, "work_items": 150, "fits": 1500, "laws_per_arm_per_dataset": 25, "interaction_datasets": 10}
    assert C.plan()[0] == {"d": 0, "fold": 0} and C.plan()[-1] == {"d": 29, "fold": 4}


def test_strata_rotation_each_input_meets_each_stratum_six_times_and_signs_alternate():
    for i in range(5):
        got = [C.stratum(j, i) for j in range(30)]
        assert {s: got.count(s) for s in C.STRATA} == {s: 6 for s in C.STRATA}
        assert all(C.stratum(j, i) == C.STRATA[(j + i) % 5] and C.stratum_sign(j, i) == (1 if (j + i) % 2 == 0 else -1) for j in range(30))
    assert C.STRATA == ("zero", "linear", "log", "quadratic", "hinge")


def test_ten_interaction_datasets_cover_the_ten_input_pairs_once_each():
    ds = [j for j in range(30) if C.interaction_pair(j) is not None]
    assert ds == list(range(0, 30, 3)) and sorted(C.interaction_pair(j) for j in ds) == sorted(__import__("itertools").combinations(range(5), 2))
    for j in range(30):
        info = C.dataset_truth(j)["info"]
        inter = [n for n, v in info.items() if v["interacting"]]
        assert len(inter) == (2 if j in ds else 0) and (C.dataset_truth(j)["interaction"] is None) == (j not in ds)


def test_amplitudes_are_log_uniform_in_the_range_deterministic_and_interaction_amplitude_only_where_needed():
    allamp = []
    for j in range(30):
        a, ai = C.amplitudes(j)
        assert (ai is None) == (C.interaction_pair(j) is None) and C.amplitudes(j) == (a, ai)
        allamp += a + ([ai] if ai is not None else [])
    assert min(allamp) >= 0.05 and max(allamp) <= 0.5 and 0.1 < float(np.median(allamp)) < 0.25 and np.log(allamp).std() > 0.3         # spans weak to the PREREG 13 value
    assert C.amplitudes(1) != C.amplitudes(2)


def test_global_hull_is_the_union_of_the_folds_training_identifiers_with_temperature_in_kelvin():
    lo, hi = C.global_hull()
    assert lo.shape == hi.shape == (5,) and np.all(lo < hi) and lo[0] > 273.0
    tr = C.dataset_truth(1)["truth"]
    assert tr[0][:2] == ("linear", -1) and tr[0][2] == pytest.approx(lo[0]) and tr[0][3] == pytest.approx(hi[0]) and tr[0][4] == C.amplitudes(1)[0][0]


# ------------------------------------------------------------------------------------------------ seeds, hyperparameters, laboratories
def test_seed_streams_follow_the_rule_and_differ_between_datasets():
    base = np.random.SeedSequence([20261105, zlib.crc32(b"calib2|d5")]).spawn(4)
    s = C.streams(5)
    assert [x.generate_state(2).tolist() for x in s] == [x.generate_state(2).tolist() for x in base]
    assert C.streams(5)[0].generate_state(1)[0] != C.streams(6)[0].generate_state(1)[0]
    gs = [C.generator_seed(5, f) for f in range(5)]
    assert len(set(gs)) == 5 and gs == [C.generator_seed(5, f) for f in range(5)] and all(0 <= g < 2 ** 31 for g in gs)


def test_hyperparameter_draws_come_from_the_tuned_spaces_per_dataset_fold_and_arm():
    seen = {"A15": [], "G15": []}
    for j in range(30):
        for f in range(5):
            for arm in ("A15", "G15"):
                hp = C.draw_hp(j, f, arm)
                assert set(hp) == set(A.ARMS[arm].space) and all(hp[k] in A.ARMS[arm].space[k][1] for k in hp)
                seen[arm].append(hp)
    assert {hp["h"] for hp in seen["A15"]} == {1, 2} and all("h" not in hp and "sparsity" not in hp for hp in seen["G15"]) and set(seen["G15"][0]) == {"grid", "l2", "lam_res", "placement"}
    assert C.draw_hp(3, 2, "A15") == C.draw_hp(3, 2, "A15")                                       # independent of call order
    assert len({json.dumps(C.draw_hp(3, f, "A15"), sort_keys=True) for f in range(5)}) > 1
    assert len({hp["grid"] for hp in seen["A15"]}) == 5                                              # the whole grid of A1 is sampled
    assert 0.3 < np.mean([hp["h"] == 1 for hp in seen["A15"]]) < 0.7


def test_laboratory_offsets_are_normal_015_per_laboratory_and_shared_by_the_folds():
    allv = []
    for j in range(30):
        o = C.lab_offsets(j, ["HM", "INT", "SIE", "HM"])
        assert list(o) == ["HM", "INT", "SIE"] and C.lab_offsets(j, ["SIE", "HM", "INT"]) == o
        allv += list(o.values())
    assert 0.1 < np.std(allv) < 0.2 and abs(np.mean(allv)) < 0.1


def test_majority_laboratory_of_a_condition_from_the_cell_table(tmp_path):
    d = tmp_path / "data" / "processed"
    d.mkdir(parents=True)
    rows = ["type,lab,T_C,SOC_max,DoD,C_ch,C_dch"]
    rows += ["z,HM,35,0.55,0.25,0.5,1", "z,INT,35,0.55,0.25,0.5,1", "z,INT,35,0.55,0.25,0.5,1"]            # INT is the majority
    rows += ["z,SIE,10,0.8,0.1,0.5,1", "z,HM,10,0.8,0.1,0.5,1"]                                           # tie: first in sorted order
    rows += ["k,HM,23,0.5,0,0,0"]                                                                          # storage: ignored
    (d / "samsung_cells.csv").write_text("\n".join(rows) + "\n")
    from pinnkan import labmap
    with pytest.raises(FileNotFoundError):
        C.majority_labs(str(tmp_path))                                  # the frozen file is required
    labmap.write_lab_map(str(tmp_path))
    m, h = C.majority_labs(str(tmp_path))
    assert m == {"T35|SOCmax0.55|DoD0.25|Cch0.5|Cdch1": "INT", "T10|SOCmax0.8|DoD0.1|Cch0.5|Cdch1": "HM"} and h == hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest()
    with pytest.raises(C.CalibrationGuardError, match="no laboratory"):
        C.run_item(0, 0, 0.05, (0,), labmap={})


def test_laboratory_offsets_enter_the_synthetic_data_by_the_conditions_majority_laboratory(labmap):
    cyc, sto = C.fold_design(0)
    tr = C.dataset_truth(2)
    offs = C.lab_offsets(2, [labmap[k] for k in cyc])
    zero = {k: 0.0 for k in offs}
    a = C.build_set(2, 0, tr, labmap, zero, cyc, sto)
    b = C.build_set(2, 0, tr, labmap, offs, cyc, sto)
    assert len(a.cells) == len(b.cells) == 2 * 32 + 19
    for ca, cb in zip(a.cells, b.cells):
        if ca.kind == "cycling":
            ci = int(a.cond_of[ca.cell_id][1:])
            assert cb.meta["delta_true"] - ca.meta["delta_true"] == pytest.approx(offs[labmap[cyc[ci]]])
        else:
            assert cb.meta["delta_true"] == ca.meta["delta_true"]
    assert len({offs[labmap[k]] for k in cyc}) == 3                                                    # all three laboratories carry a different offset (aliasing with temperature as designed)


# ------------------------------------------------------------------------------------------------ one (dataset, fold) with tiny settings, bit-identical re-run
def test_a_dataset_fold_has_the_record_schema_and_reruns_bit_identically(labmap):
    r1 = C.run_item(0, 0, 0.05, (0,))
    r2 = C.run_item(0, 0, 0.05, (0,))
    assert [(r["arm"], r["fold"], r["seed"], r["d"]) for r in r1] == [("A15", 0, 0, 0), ("G15", 0, 0, 0)]
    for r in r1:
        assert r["hp"] == C.draw_hp(0, 0, r["arm"]) and r["law"]["arm"] == X.arm_key(r["arm"], r["hp"]) and set(r["law"]["inputs"]) == set(INPUTS) and r["cpu_s"] > 0
        json.dumps(r)
    assert all(C._same(a, b) for a, b in zip(r1, r2))                                                    # same fits twice: identical records (cpu_s excluded)
    assert json.dumps(r1[0]["law"], sort_keys=True) == json.dumps(r2[0]["law"], sort_keys=True)
    skipped = C.run_item(0, 0, 0.05, (0,), skip=frozenset({(0, "A15", 0, 0)}))
    assert [r["arm"] for r in skipped] == ["G15"]


def test_rerun_choice_uses_the_hash_bytes_and_skips_repeats():
    comp = list(range(30))
    assert C.rerun_choice("00ff0001" + "00" * 28, comp) == [0, 15, 1]                                  # bytes 0, 255, 0 (repeat), 1
    assert C.rerun_choice("00ff0001" + "00" * 28, comp) == C.rerun_choice("00ff0001" + "00" * 28, comp)
    assert len(set(C.rerun_choice(hashlib.sha256(b"x").hexdigest(), comp))) == 3
    assert C.rerun_choice(hashlib.sha256(b"x").hexdigest(), [4, 7, 9, 11]) and all(d in [4, 7, 9, 11] for d in C.rerun_choice(hashlib.sha256(b"x").hexdigest(), [4, 7, 9, 11]))
    with pytest.raises(C.CalibrationGuardError):
        C.rerun_choice("00" * 32, comp)


def test_rerun_check_detects_a_changed_record(labmap, tmp_path):
    out = str(tmp_path / "cal")
    C.run_cells(0, 1, out, steps_scale=0.05, limit=1, seeds=(0,))
    open(os.path.join(out, X.CALIBRATION_FILE), "w").write("{}")
    ok = C.rerun_check(out, str(tmp_path / "scratch"), steps_scale=0.05, folds=(0,), seeds=(0,), datasets=[0])
    assert ok["identical"] is True and ok["mismatches"] == [] and os.path.exists(os.path.join(tmp_path, "scratch", "rerun_check.json"))
    p = os.path.join(out, "records_p0.jsonl")
    rows = [json.loads(l) for l in open(p)]
    rows[0]["law"]["inputs"]["dod"]["range"] += 1e-9
    open(p, "w").write("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    bad = C.rerun_check(out, str(tmp_path / "scratch2"), steps_scale=0.05, folds=(0,), seeds=(0,), datasets=[0])
    assert bad["identical"] is False and bad["mismatches"] == [[0, "A15", 0, 0]]


# ------------------------------------------------------------------------------------------------ records, resume, CPU cap
def _rec(d, arm, f, s, cpu=1.0, law=None):
    return {"d": d, "arm": arm, "fold": f, "seed": s, "hp": {}, "law": law or {}, "cpu_s": cpu, "refit_diverged": False}


def test_records_are_deduplicated_and_a_torn_last_line_is_tolerated(tmp_path):
    d = str(tmp_path)
    open(os.path.join(d, "records_p0.jsonl"), "w").write(json.dumps(_rec(0, "A15", 0, 0, 1.0)) + "\n" + json.dumps(_rec(0, "A15", 0, 0, 9.0)) + "\n" + '{"d": 1, "arm": "A1')
    open(os.path.join(d, "records_p1.jsonl"), "w").write(json.dumps(_rec(0, "A15", 0, 0, 5.0)) + "\n" + json.dumps(_rec(0, "G15", 0, 0, 2.0)) + "\n")
    got = C.read_records(d)
    assert set(got) == {(0, "A15", 0, 0), (0, "G15", 0, 0)} and got[(0, "A15", 0, 0)]["cpu_s"] == 1.0 and C.cpu_seconds(got) == 3.0       # first record wins; torn line ignored
    open(os.path.join(d, "records_p2.jsonl"), "w").write('{"broken\n' + json.dumps(_rec(2, "A15", 0, 0)) + "\n")
    with pytest.raises(C.CalibrationGuardError, match="unreadable line 1"):
        C.read_records(d)


def test_run_cells_resumes_skips_finished_items_and_stops_at_the_cpu_cap(tmp_path, monkeypatch):
    calls = []

    def fake(j, f, steps_scale=1.0, seeds=C.SEEDS, skip=frozenset(), **kw):
        calls.append((j, f))
        return [_rec(j, a, f, s, cpu=1.0) for a in C.ARM_IDS for s in seeds if (j, a, f, s) not in skip]
    monkeypatch.setattr(C, "run_item", fake)
    d = str(tmp_path)
    C.run_cells(0, 1, d, limit=2, log=lambda *a: None)
    assert calls == [(0, 0), (0, 1)] and len(C.read_records(d)) == 20
    C.run_cells(0, 1, d, limit=1, log=lambda *a: None)
    assert calls[-1] == (0, 2) and len(C.read_records(d)) == 30                                       # items on disk are not repeated
    C.run_cells(1, 2, d, limit=1, log=lambda *a: None)                                              # process 1 of 2 takes the odd work items
    assert calls[-1] == (0, 1) or calls[-1] == (0, 3)
    n0 = len(calls)
    monkeypatch.setitem(C.CAL, "cpu_cap_hours", 30 / 3600.0)                                            # 30 s of recorded CPU are on disk: at the cap nothing more runs
    C.run_cells(0, 1, d, log=lambda *a: None)
    assert len(calls) == n0


# ------------------------------------------------------------------------------------------------ scoring on records (fake laws)
def _inp(retained=True, form="none", sign=0, additive=True, family="composed"):
    return {"retained": retained, "range": 0.3 if retained else 0.0, "family": family, "edge_families": [family], "bic_margin": 3.0, "r_lin": 0.0 if retained else None, "r_log": 0.1 if retained else None,
            "form": form if retained else "none", "sign": sign if retained else 0, "sign_raw": sign if retained else 0, "max_mixed": 0.0 if additive else 0.1, "additive": additive, "approx": False}


def _fake_law(j, arm, f, s, mode):
    info = C.dataset_truth(j)["info"]
    inputs = {}
    for n in INPUTS:
        t = info[n]
        if mode == "naive":
            inputs[n] = _inp(True, "linear", 1, True, "linear")
        elif t["interacting"]:
            inputs[n] = _inp(True, "none", 0, False, "linear")                                  # interacting: not additive (the audit abstains), a stable-looking edge family (the baseline names it)
        elif t["stratum"] == "zero":
            inputs[n] = _inp(False, family="zero")
        elif t["stratum"] in ("linear", "log"):
            inputs[n] = _inp(True, t["stratum"], t["sign"], True, t["stratum"])
        elif t["stratum"] == "quadratic":
            inputs[n] = _inp(True, "none", 0, True, "composed")
        else:
            inputs[n] = _inp(True, "none", t["sign"], True, "composed")
    return {"arm": "G15" if arm == "G15" else "A15h1", "fold": f, "seed": s, "h": 1, "outer_families": [], "inputs": inputs}


def _write_fake(out, datasets, mode="oracle", cpu=2.0):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "records_p0.jsonl"), "w") as fh:
        for j in datasets:
            for a in C.ARM_IDS:
                for f in C.FOLDS:
                    for s in C.SEEDS:
                        fh.write(json.dumps(_rec(j, a, f, s, cpu, _fake_law(j, a, f, s, mode))) + "\n")


def test_finalize_oracle_laws_pass_c1_c2_c3_and_the_record_is_pinned_by_its_hash(tmp_path):
    out = str(tmp_path / "cal")
    _write_fake(out, range(30))
    rec, cal = C.finalize(out, "c" * 40, lab_hash="h")
    v = cal["verdict"]
    assert v["void"] is False and cal["D_completed"] == 30 and cal["commit"] == "c" * 40 and cal["cpu_seconds"] == 30 * 50 * 2.0 and cal["lab_map_sha256"] == "h"
    for arm in ("A15", "G15"):
        r = v["arms"][arm]
        assert r["false_datasets"] == 0 and r["C1"] and r["C2"] and r["recall"] == 1.0
        # the stability-only baseline names a form for every stable edge family, also on the interacting inputs: false statements in the 10 interaction datasets
        assert r["baseline_false_datasets"] == 10 and r["baseline_C1"] is False and r["C3"] is True
    assert v["contribution"] is True and cal["rule_sha256"] == X.rule_sha256() == hashlib.sha256(open(C.RULE_FILE, "rb").read()).hexdigest() and cal["thresholds_sha256"] == X.thresholds_sha256()
    assert rec["sha256"] == X.sha256_file(os.path.join(out, X.CALIBRATION_FILE))
    got = X.require_calibration(out, X.thresholds_sha256(), rec["sha256"], "c" * 40)
    assert got["verdict"]["contribution"] is True
    with pytest.raises(X.AuditGuardError, match="not the FROZEN commit"):
        X.require_calibration(out, X.thresholds_sha256(), rec["sha256"], "d" * 40)
    desc = cal["descriptive"]["A15"]
    assert desc["confusion"]["dod|linear"]["n"] == 6 and "false_statement_ci" in desc["confusion"]["dod|linear"] and set(desc["false_zero_by_amplitude"]) == {"<0.1", "0.1-0.25", ">0.25"}
    assert sum(len(v) for v in [cal["datasets"]]) == 60


def test_finalize_a_labeller_that_always_names_a_linear_form_fails_c1_and_withdraws_the_contribution(tmp_path):
    out = str(tmp_path / "cal")
    _write_fake(out, range(30), mode="naive")
    _, cal = C.finalize(out, "c" * 40, lab_hash="h")
    v = cal["verdict"]
    assert all(v["arms"][a]["C1"] is False and v["arms"][a]["false_datasets"] == 30 for a in C.ARM_IDS) and v["contribution"] is False
    assert THR["future_version_wording"]["failure"]["calibration"] in v["failure_sentences"]


def test_at_least_22_complete_datasets_are_required(tmp_path):
    out = str(tmp_path / "c21")
    _write_fake(out, range(21))
    _, cal = C.finalize(out, "c" * 40, lab_hash="h")
    assert cal["verdict"]["void"] is True and cal["D_completed"] == 21 and cal["verdict"]["contribution"] is False
    with pytest.raises(X.AuditGuardError, match="void"):
        X.require_calibration(out, X.thresholds_sha256(), X.sha256_file(os.path.join(out, X.CALIBRATION_FILE)), "c" * 40)
    out2 = str(tmp_path / "c22")
    _write_fake(out2, range(22))
    assert C.finalize(out2, "c" * 40, lab_hash="h")[1]["verdict"]["void"] is False
    out3 = str(tmp_path / "partial")                                                                    # an incomplete dataset (one missing fit) is not counted
    _write_fake(out3, range(22))
    lines = open(os.path.join(out3, "records_p0.jsonl")).read().splitlines()
    open(os.path.join(out3, "records_p0.jsonl"), "w").write("\n".join(lines[:-1]) + "\n")
    cal3 = C.finalize(out3, "c" * 40, lab_hash="h")[1]
    assert cal3["D_completed"] == 21 and cal3["verdict"]["void"] is True


def test_the_cpu_cap_stops_the_run_and_the_verdict_uses_the_complete_datasets(tmp_path):
    out = str(tmp_path / "cap")
    _write_fake(out, range(25))
    cal = C.finalize(out, "c" * 40, lab_hash="h")[1]
    assert cal["D_completed"] == 25 and cal["verdict"]["void"] is False and cal["verdict"]["arms"]["A15"]["D"] == 25


# ------------------------------------------------------------------------------------------------ the guard
def test_the_calibration_refuses_to_run_without_pins_off_the_frozen_commit_or_with_other_files(tmp_path, monkeypatch):
    thr, rule = X.thresholds_sha256(), X.rule_sha256()
    with pytest.raises(C.CalibrationGuardError, match="both pins"):
        C.require_run_conditions(str(tmp_path), None, rule)
    with pytest.raises(C.CalibrationGuardError, match="both pins"):
        C.require_run_conditions(str(tmp_path), thr, None)
    with pytest.raises(C.CalibrationGuardError, match="frozen"):
        C.require_run_conditions(str(tmp_path), thr, rule)
    seen = {}

    def fake(root=None, check_git=True, untracked_under=()):
        seen["u"] = untracked_under
        return {"commit": "x"}
    monkeypatch.setattr(guard, "verify_freeze", fake)
    with pytest.raises(FileNotFoundError):
        C.require_run_conditions(str(tmp_path), thr, rule)                                                # the pins are compared with the files of THIS tree (the temporary root has none)
    assert seen["u"] == ("code",)                                                                         # untracked files under code/ are part of the check
    assert C.require_run_conditions(C.ROOT, thr, rule) == {"commit": "x"}
    with pytest.raises(C.CalibrationGuardError, match="thresholds pin"):
        C.require_run_conditions(C.ROOT, "0" * 64, rule)
    with pytest.raises(C.CalibrationGuardError, match="rule pin"):
        C.require_run_conditions(C.ROOT, thr, "0" * 64)


def test_verify_freeze_can_include_untracked_files_under_code(tmp_path, monkeypatch):
    prereg = tmp_path / "runs" / "prereg"
    prereg.mkdir(parents=True)
    (prereg / "PREREG_x.md").write_text("x")
    (prereg / "FROZEN").write_text(json.dumps({"commit": "abc", "prereg_file": "runs/prereg/PREREG_x.md", "prereg_sha256": guard.sha256_file(str(prereg / "PREREG_x.md")), "splits": {}, "config_sha256s": []}))
    out = {"status": ""}

    def fake_git(root, *args):
        if args[0] == "rev-parse":
            return "abc"
        return out["status"] if "--untracked-files=all" in args else ""
    monkeypatch.setattr(guard, "_git", fake_git)
    assert guard.verify_freeze(str(tmp_path))["commit"] == "abc"                                          # default behaviour unchanged
    out["status"] = "?? code/new_file.py"
    assert guard.verify_freeze(str(tmp_path))["commit"] == "abc"
    with pytest.raises(guard.TestFoldAccessError, match="untracked files under code"):
        guard.verify_freeze(str(tmp_path), untracked_under=("code",))
    out["status"] = "?? code/pinnkan/__pycache__/x.cpython-314.pyc\n?? code/a.pyc"
    assert guard.verify_freeze(str(tmp_path), untracked_under=("code",))["commit"] == "abc"


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
    d = run.run({**CFG, "run_id": "ok", "extraction_audit_sha256": X.thresholds_sha256(), "calibration_rule_sha256": X.rule_sha256()}, runs_dir=str(tmp_path))
    cfg = json.load(open(os.path.join(d, "config.json")))
    assert cfg["extraction_audit_sha256"] == X.thresholds_sha256() and cfg["calibration_rule_sha256"] == X.rule_sha256()                  # part of the hashed config
    el = json.load(open(os.path.join(d, "extracted_laws.json")))
    assert len(el["laws"]) == 2 and {l["seed"] for l in el["laws"]} == {0, 1} and el["levels"]["T_C"] >= 2 and el["extraction_audit_sha256"] == X.thresholds_sha256()
    assert all(l["arm"] in ("A15h1", "A15h2") and set(l["inputs"]["dod"]) >= {"retained", "r_lin", "r_log", "form", "sign", "additive", "approx"} for l in el["laws"])
    d2 = run.run({**CFG, "run_id": "none", "arms": ["R2"]}, runs_dir=str(tmp_path))
    assert not os.path.exists(os.path.join(d2, "extracted_laws.json"))


# ------------------------------------------------------------------------------------------------ the statistics-step guard
def _with_laws(dirs, g15_c1_fail=False, drop=None):
    for d in dirs:
        cfg = json.load(open(os.path.join(d, "config.json")))
        if cfg["m"] != 32:
            continue
        laws = []
        for s in range(5):
            for arm in ("A15h1", "G15"):
                laws.append({"arm": arm, "fold": cfg["fold"], "seed": s, "h": 1, "outer_families": [], "inputs": {n: _inp(True, "linear", 1, True, "linear") for n in INPUTS}})
        if drop and cfg["fold"] == 0:
            laws = laws[:-1]
        json.dump({"m": 32, "fold": cfg["fold"], "laws": laws, "levels": {"T_C": 3, "soc_mid": 6, "dod": 5, "c_ch": 5, "c_dch": 6}}, open(os.path.join(d, "extracted_laws.json"), "w"))


def _calibration(cdir, commit="c" * 40, g15_c1=True):
    v = {"void": False, "contribution": bool(g15_c1), "failure_sentences": [] if g15_c1 else [THR["future_version_wording"]["failure"]["calibration"]],
         "arms": {"A15": {"C1": True, "C2": True, "C3": True}, "G15": {"C1": g15_c1, "C2": True, "C3": True}}}
    os.makedirs(cdir, exist_ok=True)
    cal = {"commit": commit, "thresholds_sha256": X.thresholds_sha256(), "rule_sha256": X.rule_sha256(), "verdict": v}
    p = os.path.join(cdir, X.CALIBRATION_FILE)
    json.dump(cal, open(p, "w"), sort_keys=True)
    return X.sha256_file(p)


def test_the_statistics_step_prints_edge_wording_only_with_pinned_calibration_from_the_frozen_commit(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "read_freeze", lambda root=None: None)                                   # the tree under test has no FROZEN file whatever the repository state
    tmp = str(tmp_path)
    os.makedirs(tmp + "/g")
    dirs = _grid_runs(tmp + "/g")
    _with_laws(dirs)
    fdir, sha = _item_f_before(tmp, dirs)
    thr, C40 = X.thresholds_sha256(), "c" * 40
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    assert out["edge_wording"]["printed"] is False and "without named edge families" in out["edge_wording"]["reason"]            # default: the law only
    st = out["edge_wording"]["stability"]                                                                  # D022b: descriptive stability table, no licence word, no calibration number
    assert st["descriptive_only"] and st["contribution"] is False and st["caption"].startswith("descriptive; not evidence") and set(st["arms"]) == {"A15", "G15"}
    txt = json.dumps(out["edge_wording"])
    assert all(w not in txt for w in ("identified:", "form: ", "sign: ", "verdict", "upper_limit")) and st["arms"]["A15"]["labels_printed"] is False
    assert {r["input"]: r for r in st["arms"]["A15"]["stability_table"]}["T_C"]["note"] == "temperature and laboratory cannot be separated"
    cdir = os.path.join(tmp, "cal")
    csha = _calibration(cdir)
    with pytest.raises(X.AuditGuardError, match="D022b"):                                                  # the confirmatory path refuses every edge-level licence
        ss.run_stats_v4(os.path.join(tmp, "an0"), dirs, item_f_dir=fdir, item_f_sha256=sha, audit_dir=cdir, frozen_commit=C40, audit_thresholds_pin=thr, calibration_sha256=csha)
    kw = dict(item_f_dir=fdir, item_f_sha256=sha, audit_dir=cdir, frozen_commit=C40, licences=True)               # the future-version path (kept, not used)
    with pytest.raises(X.AuditGuardError, match="audit_thresholds_pin is mandatory"):
        ss.run_stats_v4(os.path.join(tmp, "an1"), dirs, calibration_sha256=csha, **kw)
    with pytest.raises(X.AuditGuardError, match="calibration_sha256 is mandatory"):
        ss.run_stats_v4(os.path.join(tmp, "an2"), dirs, audit_thresholds_pin=thr, **kw)
    with pytest.raises(X.AuditGuardError, match="not the FROZEN commit"):
        ss.run_stats_v4(os.path.join(tmp, "an3"), dirs, audit_thresholds_pin=thr, calibration_sha256=csha, **{**kw, "frozen_commit": "d" * 40})
    with pytest.raises(X.AuditGuardError, match="no FROZEN commit"):
        ss.run_stats_v4(os.path.join(tmp, "an3b"), dirs, audit_thresholds_pin=thr, calibration_sha256=csha, **{**kw, "frozen_commit": None})            # tmp tree has no FROZEN file
    from pinnkan import stats_v4
    with pytest.raises(X.BannedWordingError, match="identified"):                                          # the future-version Results sentence contains a banned word: the statistics step cannot print it
        ss.run_stats_v4(os.path.join(tmp, "an4"), dirs, audit_thresholds_pin=thr, calibration_sha256=csha, **kw)
    ew = stats_v4.edge_level_wording(dirs, cdir, thr, csha, C40, licences=True)
    assert ew["printed"] and ew["contribution"] is True and set(ew["arms"]) == {"A15", "G15"} and ew["discussion_sentence"].startswith("Readable means")
    a = ew["arms"]["A15"]
    assert a["labels_printed"] and a["sentences"]["results"] == "Of the 5 inputs of the extracted KAN law, the audit licensed the form of 4 and the sign of 0; 1 were not identified and 0 were not retained by the extraction."
    assert a["labels"]["T_C"]["label"] == "not_identified" and a["labels"]["T_C"]["never_licensed"] and a["labels"]["dod"]["label"] == "form" and a["labels"]["dod"]["n_laws"] == 25 and ew["arms"]["G15"]["sentences"]["results"].startswith("Of the 5 inputs of the extracted additive law,")
    # an arm that failed C1 prints no label: the descriptive stability table only, and the fixed failure sentence
    csha2 = _calibration(os.path.join(tmp, "cal2"), g15_c1=False)
    bad = stats_v4.edge_level_wording(dirs, os.path.join(tmp, "cal2"), thr, csha2, C40, licences=True)
    assert bad["arms"]["A15"]["labels_printed"] is True and bad["arms"]["G15"]["labels_printed"] is False and "labels" not in bad["arms"]["G15"] and bad["contribution"] is False
    assert bad["failure_sentences"] == [THR["future_version_wording"]["failure"]["calibration"]] and len(bad["arms"]["G15"]["stability_table"]) == 5


def test_exactly_25_laws_per_arm_at_g4_are_required_by_the_statistics_step(tmp_path):
    tmp = str(tmp_path)
    os.makedirs(tmp + "/g")
    dirs = _grid_runs(tmp + "/g")
    _with_laws(dirs, drop=True)                                                                           # fold 0 lacks one law (G15 seed 4)
    cdir = os.path.join(tmp, "cal")
    csha = _calibration(cdir)
    from pinnkan import stats_v4
    with pytest.raises(X.AuditError, match="expected exactly 25"):
        stats_v4.edge_level_wording(dirs, cdir, X.thresholds_sha256(), csha, "c" * 40)


def test_calendar_law_edge_wording_is_refused(tmp_path):
    from pinnkan import stats_v4
    cdir = str(tmp_path / "cal")
    csha = _calibration(cdir)
    with pytest.raises(X.AuditGuardError, match="calendar extracted law gets no edge-level wording"):
        stats_v4.edge_level_wording([], cdir, X.thresholds_sha256(), csha, "c" * 40, law="calendar")


def test_label_sentence_and_audit_functions_are_called_only_from_edge_level_wording():
    guarded = {"label_law", "label_input", "label_text", "results_sentence", "audit_arm", "stability_table", "require_calibration", "collect_laws"}
    users = {}
    for fn in ("stats_step.py", "stats_v4.py", "stats_rows.py", "stats_ext.py", "stats_sim.py"):
        p = os.path.join(ROOT, "code", "pinnkan", fn)
        if not os.path.exists(p):
            continue
        tree = ast.parse(open(p, encoding="utf8").read())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Attribute) and sub.attr in guarded:
                        users.setdefault(f"{fn}:{node.name}", set()).add(sub.attr)
            if isinstance(node, ast.ImportFrom) and node.module and node.module.endswith("extraction_audit") and node.col_offset == 0:
                users.setdefault(f"{fn}:<module>", set()).add("import")
    assert set(users) == {"stats_v4.py:edge_level_wording"}, users
    assert {"audit_arm", "require_calibration", "collect_laws"} <= users["stats_v4.py:edge_level_wording"]


def test_the_calibration_script_is_inert_under_the_d022b_fallback():
    with pytest.raises(C.CalibrationGuardError, match="D022b"):
        C.main(["--thresholds-pin", X.thresholds_sha256(), "--rule-pin", X.rule_sha256()])
    with pytest.raises(C.CalibrationGuardError, match="D022b"):
        C.main(["--finalize"])
    assert C.__doc__.startswith("INERT (D022b")
