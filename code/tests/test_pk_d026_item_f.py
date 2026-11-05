"""D026 (item (f) under retention blinding): implementer actions 1-6 of debates/D026_item_f_blinding/02_judge.md.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_d026_item_f.py -q
1 pins, 2 stats_v4.build_item_f (one refusal test per writer condition), 3 guard.require_item_f_record before build_data, 4 item_f_sha256 in the ledger, 5 smoke test, 6 concordance row.
Every freeze lives in a TEMPORARY root with git stubbed; the real runs/prereg/FROZEN is never created and no Samsung data is read."""
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "tests"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

from pinnkan import data, guard, run, stats_v4 as v4
from pk_freeze import FAKE_COMMIT, make_freeze

CFG_BASE = {"dataset": "samsung", "test": "B", "mode": "inner", "m": 8, "subset": "maxmin", "arms": ["A1", "A9", "A11", "A12"], "window": {"k_cycling": 4, "k_storage": 2},
            "diagnostics": False, "refit_timing": False, "steps_scale": 1.0, "backbone": "self_limiting"}


# ------------------------------------------------------------------------------------------------ helpers
def _cfg_in(fold, **over):
    return {**CFG_BASE, "run_id": f"item_f_f{fold}", "fold": fold, **over}


def _hash(cfg_in):
    return guard.canonical_config_hash({**run.DEFAULTS, **cfg_in})


def _jd(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w", encoding="utf8"))


def _conds(n=8):
    return [f"T{35 if i % 2 else 23}|SOCmax0.{i + 1}|DoD0.25|Cch0.5|Cdch1.0" for i in range(n)]


def fake_run(runs_dir, fold, mode_effective="inner", dstar="A9", cfg_over=None, tamper_hash=False, scores_shift=0.0):
    """a minimal item (f) run directory in the layout run.py writes (no model is fitted)"""
    cfg_in = _cfg_in(fold, **(cfg_over or {}))
    d = os.path.join(runs_dir, cfg_in["run_id"])
    cfg = {**run.DEFAULTS, **cfg_in, "mode_effective": mode_effective, "blinded_samsung_pre_freeze": mode_effective != "inner",
           "config_sha256": ("0" * 64 if tamper_hash else _hash(cfg_in)), "config_input": cfg_in}
    _jd(os.path.join(d, "config.json"), cfg)
    rng = np.random.default_rng(100 + fold)
    conds = _conds()
    a1 = {c: float(3.0 + rng.uniform(-1, 1) + scores_shift) for c in conds}
    ds = {c: float(a1[c] * np.exp(rng.normal(0.05, 0.3))) for c in conds}
    other = {c: float(a1[c] * np.exp(rng.normal(0.1, 0.3))) for c in conds}
    arm = lambda sc, hp: {"inner_cv_pp": float(np.mean(list(sc.values()))), "cond_scores": sc, "best_hp": hp}
    _jd(os.path.join(d, "tuning_done.json"), {"backbone": "self_limiting", "arms": {"A1": arm(a1, {"h": 2}), "A9": arm(ds, {"width": 32}), "A11": arm(other, {"nu": 2.5}), "A12": arm(other, {"leaves": 21})},
                                              "budget": {"n_trials": 20, "inner_k": 2}})
    _jd(os.path.join(d, "inner_folds.json"), {c: i % 2 for i, c in enumerate(conds)})
    _jd(os.path.join(d, "comparators.json"), {"D*": {"arm": dstar, "score": 1.0, "table": {}, "complete": True}})
    _jd(os.path.join(d, "train_condition_meta.json"), {c: {"n_cells": 2, "labs": {}, "lab": ("HM" if i < 4 else "INT")} for i, c in enumerate(conds)})
    return d


def freeze_root(tmp_path, monkeypatch, cfg_ins=None, head=None, **kw):
    """temporary root with a valid FROZEN pinning the item (f) config hashes of folds 0-4 (or of `cfg_ins`)"""
    cfg_ins = cfg_ins if cfg_ins is not None else [_cfg_in(f) for f in range(5)]
    payload = make_freeze(tmp_path, monkeypatch, head=head, **kw)
    payload["item_f_config_sha256s"] = [_hash(c) for c in cfg_ins]
    json.dump(payload, open(tmp_path / "runs" / "prereg" / "FROZEN", "w"))
    return str(tmp_path), payload


def five_runs(tmp_path, **kw):
    runs = str(tmp_path / "runs")
    return [fake_run(runs, f, **kw) for f in range(5)]


def valid_state(tmp_path, monkeypatch):
    root, payload = freeze_root(tmp_path, monkeypatch)
    dirs = five_runs(tmp_path)
    rec = v4.build_item_f(root, dirs)
    return root, payload, dirs, rec


# ------------------------------------------------------------------------------------------------ action 1: pins
def test_a1_item_f_files_are_not_pinned_and_the_five_configs_are(tmp_path, monkeypatch):
    assert "item_f" not in guard.PIN_FILES and "item_f_record" not in guard.PIN_FILES
    root, _ = freeze_root(tmp_path, monkeypatch)
    shutil.copy(os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json"), tmp_path / "runs" / "prereg" / "samsung_splits_v2.json")
    os.makedirs(tmp_path / "code" / "pinnkan")
    shutil.copy(os.path.join(ROOT, "runs", "prereg", "subsets.json"), tmp_path / "runs" / "prereg" / "subsets.json")
    (tmp_path / "code" / "pinnkan" / "symbolic_library.json").write_text("{}")
    paths = []
    for f in range(5):
        p = tmp_path / f"c{f}.json"
        p.write_text(json.dumps(_cfg_in(f)))
        paths.append(str(p))
    # the payload builds with no item (f) file anywhere under the root, and with require_pins
    pay = guard.build_freeze_payload(root, [("samsung", "B")], [], prereg_file="runs/prereg/PREREG_v2.md", require_pins=True, item_f_config_paths=paths)
    assert set(pay["pins"]) == {"subsets", "symbolic_library"} and pay["pins_missing"] == []
    assert pay["item_f_config_sha256s"] == [_hash(_cfg_in(f)) for f in range(5)]
    # it refuses without the item (f) configs, or with fewer or duplicate ones
    for bad in (None, paths[:4], paths[:4] + [paths[0]]):
        with pytest.raises(guard.TestFoldAccessError, match="item \\(f\\) configs"):
            guard.build_freeze_payload(root, [("samsung", "B")], [], prereg_file="runs/prereg/PREREG_v2.md", require_pins=True, item_f_config_paths=bad)
    q = guard.build_freeze_payload(root, [("samsung", "B")], [], prereg_file="runs/prereg/PREREG_v2.md", item_f_config_paths=paths[:2])
    assert q["pins_missing"] == ["item_f_configs"]                                      # listed; a FROZEN built so is refused, and the message no longer names the item (f) file
    json.dump({**q, "commit": FAKE_COMMIT}, open(tmp_path / "runs" / "prereg" / "FROZEN", "w"))
    with pytest.raises(guard.TestFoldAccessError, match="item \\(f\\) run configs") as ei:
        guard.verify_freeze(root, check_git=False)
    assert "dependence file" not in str(ei.value) and "item (f) file" not in str(ei.value)


def test_a1_the_real_item_f_configs_are_g1_inner_configs_for_folds_0_to_4():
    from pinnkan import inversion
    d = os.path.join(ROOT, "runs", "item_f", "configs")
    files = sorted(os.listdir(d))
    assert len(files) == 5
    cfgs = [json.load(open(os.path.join(d, f), encoding="utf8")) for f in files]
    assert sorted(c["fold"] for c in cfgs) == [0, 1, 2, 3, 4] and len({c["run_id"] for c in cfgs}) == 5
    for c in cfgs:
        assert (c["dataset"], c["test"], c["mode"], c["m"], c["subset"]) == ("samsung", "B", "inner", 8, "maxmin")
        assert c["arms"] == ["A1", "A9", "A11", "A12"] and c["window"] == {"k_cycling": 4, "k_storage": 2}
        assert c["diagnostics"] is False and c["refit_timing"] is False and c.get("steps_scale", 1.0) == 1.0
        assert c["inversion_config_sha256"] == inversion.config_sha256()               # a stale constant would raise ConfigError at run time
    assert len({_hash(c) for c in cfgs}) == 5


# ------------------------------------------------------------------------------------------------ action 2: build_item_f, one refusal per condition
def test_a2_build_item_f_writes_the_file_and_the_record(tmp_path, monkeypatch):
    root, payload, dirs, rec = valid_state(tmp_path, monkeypatch)
    base = tmp_path / "runs" / "item_f"
    assert (base / v4.ITEM_F_FILE).is_file() and (base / v4.ITEM_F_HASH).is_file()
    r = json.load(open(base / v4.ITEM_F_HASH))
    assert r["frozen_commit"] == FAKE_COMMIT and r["folds"] == [0, 1, 2, 3, 4] and r["contrast"] == ["D*", "A1"]
    assert r["cell"] == {"dataset": "samsung", "test": "B", "m": 8, "k": "2", "subset": "maxmin"}
    assert [x["fold"] for x in r["runs"]] == [0, 1, 2, 3, 4] and [x["run_id"] for x in r["runs"]] == [f"item_f_f{f}" for f in range(5)]
    for x in r["runs"]:
        assert set(x["artifacts"]) == set(guard.ITEM_F_ARTIFACTS) and x["config_sha256"] in payload["item_f_config_sha256s"]
        assert x["artifacts"]["tuning_done.json"] == guard.sha256_file(str(tmp_path / "runs" / x["run_id"] / "tuning_done.json"))
    assert r["sha256"] == guard.sha256_file(str(base / v4.ITEM_F_FILE)) and r["d_star_by_fold"] == {str(f): "A9" for f in range(5)}
    assert v4.require_item_f(str(base), dirs)["contrast"] == ["D*", "A1"]
    with pytest.raises(v4.ItemFError, match="append-only"):
        v4.build_item_f(root, dirs)                                                      # a second write is refused


def test_a2_refuses_without_a_valid_freeze(tmp_path, monkeypatch):
    five_runs(tmp_path)
    with pytest.raises(v4.ItemFError, match="freeze is invalid"):
        v4.build_item_f(str(tmp_path), [str(tmp_path / "runs" / f"item_f_f{f}") for f in range(5)])      # no FROZEN at all


def test_a2_refuses_when_head_is_not_the_frozen_commit(tmp_path, monkeypatch):
    root, _ = freeze_root(tmp_path, monkeypatch, head="b" * 40)
    with pytest.raises(v4.ItemFError, match="HEAD is not the FROZEN commit"):
        v4.build_item_f(root, five_runs(tmp_path))
    assert not (tmp_path / "runs" / "item_f").exists()


def test_a2_refuses_when_a_run_is_not_inner(tmp_path, monkeypatch):
    root, _ = freeze_root(tmp_path, monkeypatch)
    dirs = five_runs(tmp_path)
    fake_run(str(tmp_path / "runs"), 3, mode_effective="timing")                         # a pre-freeze Samsung request is downgraded to timing
    with pytest.raises(v4.ItemFError, match="mode_effective 'timing'"):
        v4.build_item_f(root, dirs)


def test_a2_refuses_a_config_hash_that_is_not_pinned(tmp_path, monkeypatch):
    cfgs = [_cfg_in(f) for f in range(5)]
    cfgs[2] = _cfg_in(2, n_trials=21)                                                    # FROZEN pins a different config for fold 2
    root, _ = freeze_root(tmp_path, monkeypatch, cfg_ins=cfgs)
    with pytest.raises(v4.ItemFError, match="not among the FROZEN item_f_config_sha256s"):
        v4.build_item_f(root, five_runs(tmp_path))
    # a config.json whose recorded hash was edited away from its recorded input is caught as well
    tmp2 = tmp_path / "second"
    tmp2.mkdir()
    root2, _ = freeze_root(tmp2, monkeypatch)
    dirs = [fake_run(str(tmp2 / "runs"), f, tamper_hash=(f == 1)) for f in range(5)]
    with pytest.raises(v4.ItemFError, match="does not match the recorded config input"):
        v4.build_item_f(root2, dirs)


@pytest.mark.parametrize("which", ["four", "duplicate_fold", "fold5"])
def test_a2_refuses_when_the_folds_are_not_exactly_0_to_4(tmp_path, monkeypatch, which):
    cfgs = [_cfg_in(f) for f in range(5)] + [_cfg_in(5), _cfg_in(0, run_id="dup")]
    root, _ = freeze_root(tmp_path, monkeypatch, cfg_ins=cfgs)
    runs = str(tmp_path / "runs")
    dirs = [fake_run(runs, f) for f in range(5)]
    if which == "four":
        dirs = dirs[:4]
    elif which == "fold5":
        dirs = dirs[:4] + [fake_run(runs, 5)]
    else:
        dirs = dirs[:4] + [fake_run(runs, 0, cfg_over={"run_id": "dup"})]
    with pytest.raises(v4.ItemFError, match="not exactly 0-4"):
        v4.build_item_f(root, dirs)


def test_a2_refuses_when_the_ledger_holds_a_samsung_row(tmp_path, monkeypatch):
    root, _ = freeze_root(tmp_path, monkeypatch)
    dirs = five_runs(tmp_path)
    guard.record_scoring("c" * 64, "x", FAKE_COMMIT, root, dataset="samsung", item_f_sha256="d" * 64)
    with pytest.raises(v4.ItemFError, match="Samsung row"):
        v4.build_item_f(root, dirs)


def test_a2_refuses_when_a_row_of_unknown_dataset_is_in_the_ledger(tmp_path, monkeypatch):
    root, _ = freeze_root(tmp_path, monkeypatch)
    dirs = five_runs(tmp_path)
    guard.record_scoring("c" * 64, "x", FAKE_COMMIT, root)                               # a legacy row: dataset not stated
    with pytest.raises(v4.ItemFError, match="Samsung row"):
        v4.build_item_f(root, dirs)


def test_a2_an_isu_ledger_row_does_not_block_the_writer(tmp_path, monkeypatch):
    root, _ = freeze_root(tmp_path, monkeypatch)
    dirs = five_runs(tmp_path)
    guard.record_scoring("c" * 64, "x", FAKE_COMMIT, root, dataset="isu")
    v4.build_item_f(root, dirs)


def test_a2_refuses_when_a_samsung_condition_scores_file_exists_anywhere_under_runs(tmp_path, monkeypatch):
    root, _ = freeze_root(tmp_path, monkeypatch)
    dirs = five_runs(tmp_path)
    other = tmp_path / "runs" / "nested" / "some_run"
    _jd(str(other / "config.json"), {"dataset": "samsung"})
    _jd(str(other / "condition_scores_k0.json"), {})
    with pytest.raises(v4.ItemFError, match="Samsung condition_scores"):
        v4.build_item_f(root, dirs)
    shutil.rmtree(tmp_path / "runs" / "nested")
    nocfg = tmp_path / "runs" / "orphan"                                                 # scores of unknown provenance count as Samsung
    _jd(str(nocfg / "condition_scores.json"), {})
    with pytest.raises(v4.ItemFError, match="Samsung condition_scores"):
        v4.build_item_f(root, dirs)
    shutil.rmtree(nocfg)
    syn = tmp_path / "runs" / "figdemo"                                                  # a synthetic or demo run (SYNTHETIC marker) is not a Samsung score
    _jd(str(syn / "config.json"), {"dataset": "samsung", "synthetic": True})
    _jd(str(syn / "condition_scores.json"), {})
    open(syn / "SYNTHETIC", "w").write("synthetic")
    _jd(str(tmp_path / "runs" / "isu_run" / "config.json"), {"dataset": "isu"})
    _jd(str(tmp_path / "runs" / "isu_run" / "condition_scores.json"), {})
    v4.build_item_f(root, dirs)


def test_a2_refuses_a_run_that_is_not_the_g1_cell_and_an_unestimable_report(tmp_path, monkeypatch):
    cfgs = [_cfg_in(f) for f in range(5)]
    cfgs[0] = _cfg_in(0, m=16)
    root, _ = freeze_root(tmp_path, monkeypatch, cfg_ins=cfgs)
    runs = str(tmp_path / "runs")
    dirs = [fake_run(runs, 0, cfg_over={"m": 16})] + [fake_run(runs, f) for f in range(1, 5)]
    with pytest.raises(v4.ItemFError, match="not the g1 cell"):
        v4.build_item_f(root, dirs)
    tmp2 = tmp_path / "second"
    tmp2.mkdir()
    root2, _ = freeze_root(tmp2, monkeypatch)
    dirs2 = five_runs(tmp2)
    for d in dirs2:                                                                      # one laboratory only: no estimate, nothing is written
        meta = json.load(open(os.path.join(d, "train_condition_meta.json")))
        json.dump({c: {**v, "lab": "HM"} for c, v in meta.items()}, open(os.path.join(d, "train_condition_meta.json"), "w"))
    with pytest.raises(v4.ItemFError, match="cannot be formed"):
        v4.build_item_f(root2, dirs2)
    assert not (tmp2 / "runs" / "item_f").exists()


# ------------------------------------------------------------------------------------------------ action 3: require_item_f_record before build_data
class _Reached(Exception):
    pass


def _samsung_confirmatory_cfg():
    return {"run_id": "g1_f0", "dataset": "samsung", "test": "B", "fold": 0, "mode": "confirmatory", "m": 8, "arms": ["A1"], "window": {"k_cycling": 4, "k_storage": 2},
            "inversion_config_sha256": run.inversion.config_sha256()}


@pytest.fixture
def mocked_split(monkeypatch):
    calls = []

    def fake(*a, **k):
        calls.append((a, k))
        raise _Reached()
    monkeypatch.setattr(run, "load_split", fake)
    monkeypatch.setattr(data, "load_split", fake)
    return calls


def _scorer_state(tmp_path, monkeypatch):
    cfg = _samsung_confirmatory_cfg()
    root, payload = freeze_root(tmp_path, monkeypatch, config_hashes=[_hash(cfg)])
    dirs = five_runs(tmp_path)
    v4.build_item_f(root, dirs)
    return root, cfg, dirs


def test_a3_the_gate_passes_on_a_complete_record_and_then_build_data_is_reached(tmp_path, monkeypatch, mocked_split):
    root, cfg, _ = _scorer_state(tmp_path, monkeypatch)
    sha = guard.require_item_f_record(root)
    assert sha == guard.sha256_file(str(tmp_path / "runs" / "item_f" / v4.ITEM_F_FILE))
    with pytest.raises(_Reached):
        run.run(cfg, root=root, runs_dir=str(tmp_path / "runs"))
    assert len(mocked_split) == 1


def _break_absent(root, tmp):
    os.remove(tmp / "runs" / "item_f" / v4.ITEM_F_HASH)


def _break_record_absent_dir(root, tmp):
    shutil.rmtree(tmp / "runs" / "item_f")


def _break_file_hash(root, tmp):
    with open(tmp / "runs" / "item_f" / v4.ITEM_F_FILE, "a") as fh:
        fh.write(" ")


def _edit_record(tmp, fn):
    p = tmp / "runs" / "item_f" / v4.ITEM_F_HASH
    r = json.load(open(p))
    fn(r)
    json.dump(r, open(p, "w"))


def _break_frozen_commit(root, tmp):
    _edit_record(tmp, lambda r: r.update(frozen_commit="e" * 40))


def _break_folds(root, tmp):
    _edit_record(tmp, lambda r: r.update(folds=[0, 1, 2, 3], runs=r["runs"][:4]))


def _break_artifact(root, tmp):
    with open(tmp / "runs" / "item_f_f2" / "inner_folds.json", "a") as fh:
        fh.write(" ")


def _break_artifact_missing(root, tmp):
    os.remove(tmp / "runs" / "item_f_f4" / "comparators.json")


def _break_config_hash(root, tmp):
    _edit_record(tmp, lambda r: r["runs"][1].update(config_sha256="9" * 64))


def _break_artifact_list(root, tmp):
    _edit_record(tmp, lambda r: r["runs"][0]["artifacts"].pop("train_condition_meta.json"))


@pytest.mark.parametrize("breaker,match", [(_break_absent, "absent"), (_break_record_absent_dir, "absent"), (_break_file_hash, "differs from the hash"), (_break_frozen_commit, "frozen_commit"),
                                           (_break_folds, "exactly 0-4"), (_break_artifact, "inner_folds.json"), (_break_artifact_missing, "comparators.json"),
                                           (_break_config_hash, "item_f_config_sha256s"), (_break_artifact_list, "does not list exactly")])
def test_a3_every_refusal_stops_before_load_split_and_before_a_run_folder_exists(tmp_path, monkeypatch, mocked_split, breaker, match):
    root, cfg, _ = _scorer_state(tmp_path, monkeypatch)
    breaker(root, tmp_path)
    with pytest.raises(guard.TestFoldAccessError, match=match):
        run.run(cfg, root=root, runs_dir=str(tmp_path / "runs"))
    assert mocked_split == [] and not (tmp_path / "runs" / cfg["run_id"]).exists()
    assert guard.GUARD_LOG and guard.GUARD_LOG[-1]["what"] == "item (f) record" and guard.GUARD_LOG[-1]["verified"] is False


def test_a3_isu_and_snl_confirmatory_runs_do_not_call_the_gate(tmp_path, monkeypatch):
    from test_pk_review_fixes import _confirmatory_cfg, mini_isu
    root, p, h = mini_isu(tmp_path)
    cfg = _confirmatory_cfg()
    make_freeze(tmp_path, monkeypatch, splits={"isu:B": {"file_sha256": data.sha256_file(p), "fold_hash": h}}, config_hashes=[_hash(cfg)])

    def boom(*a, **k):
        raise AssertionError("require_item_f_record must not run for ISU / SNL")
    monkeypatch.setattr(guard, "require_item_f_record", boom)
    d = run.run(cfg, root=root, runs_dir=str(tmp_path / "runs"))
    assert os.path.exists(os.path.join(d, "condition_scores.json"))
    row = json.loads(open(os.path.join(root, "runs", "prereg", "SCORED.jsonl")).read().splitlines()[0])
    assert row["dataset"] == "isu" and "item_f_sha256" not in row


# ------------------------------------------------------------------------------------------------ action 4: item_f_sha256 in the ledger rows
def test_a4_a_samsung_scoring_row_must_carry_the_hash_and_it_is_written(tmp_path):
    root = str(tmp_path)
    os.makedirs(tmp_path / "runs" / "prereg")
    with pytest.raises(guard.TestFoldAccessError, match="item_f_sha256"):
        guard.record_scoring("a" * 64, "r", FAKE_COMMIT, root, dataset="samsung")
    assert not (tmp_path / "runs" / "prereg" / "SCORED.jsonl").exists()
    guard.record_scoring("a" * 64, "r", FAKE_COMMIT, root, dataset="samsung", item_f_sha256="b" * 64)
    assert guard.read_ledger(root) == [{"config_sha256": "a" * 64, "run_id": "r", "commit": FAKE_COMMIT, "dataset": "samsung", "item_f_sha256": "b" * 64}]


def test_a4_run_py_hands_the_verified_hash_to_the_ledger():
    src = open(os.path.join(ROOT, "code", "pinnkan", "run.py"), encoding="utf8").read()
    assert "item_f_sha = guard.require_item_f_record(root, runs_dir)" in src
    assert "guard.record_scoring(chash, run_id, git_info(root)[\"commit\"], root, dataset=ds, item_f_sha256=item_f_sha)" in src
    assert src.index("require_item_f_record(root, runs_dir)") < src.index("D = build_data(cfg, root, role)")


def _ledger_state(tmp_path, monkeypatch, rows):
    root, payload, dirs, rec = valid_state(tmp_path, monkeypatch)
    for i, r in enumerate(rows):
        guard.record_scoring(f"{i}" * 64, f"s{i}", FAKE_COMMIT, root, **r)
    return root, dirs, rec["sha256"]


def test_a4_the_statistics_step_accepts_rows_that_all_carry_the_file_hash(tmp_path, monkeypatch):
    root, dirs, sha = _ledger_state(tmp_path, monkeypatch, [])
    h = str(tmp_path / "runs" / "item_f")
    for i in range(3):
        guard.record_scoring(f"{i}" * 64, f"s{i}", FAKE_COMMIT, root, dataset="samsung", item_f_sha256=sha)
    guard.record_scoring("9" * 64, "isu", FAKE_COMMIT, root, dataset="isu")              # other datasets carry no hash and are not looked at
    assert v4.require_item_f(h, dirs, sha, ledger_root=root)["contrast"] == ["D*", "A1"]
    assert v4.require_item_f(h, dirs, None, ledger_root=root)["contrast"] == ["D*", "A1"]


def test_a4_a_row_without_the_hash_fails(tmp_path, monkeypatch):
    root, dirs, sha = _ledger_state(tmp_path, monkeypatch, [])
    h = str(tmp_path / "runs" / "item_f")
    guard.record_scoring("1" * 64, "s1", FAKE_COMMIT, root, dataset="samsung", item_f_sha256=sha)
    with open(os.path.join(root, "runs", "prereg", "SCORED.jsonl"), "a") as fh:         # a row written by hand or by older code, without the hash
        fh.write(json.dumps({"config_sha256": "2" * 64, "run_id": "s2", "commit": FAKE_COMMIT, "dataset": "samsung"}) + "\n")
    with pytest.raises(v4.ItemFError, match="same item_f_sha256"):
        v4.require_item_f(h, dirs, sha, ledger_root=root)


def test_a4_mismatched_hashes_fail(tmp_path, monkeypatch):
    root, dirs, sha = _ledger_state(tmp_path, monkeypatch, [])
    h = str(tmp_path / "runs" / "item_f")
    guard.record_scoring("1" * 64, "s1", FAKE_COMMIT, root, dataset="samsung", item_f_sha256=sha)
    guard.record_scoring("2" * 64, "s2", FAKE_COMMIT, root, dataset="samsung", item_f_sha256="f" * 64)
    with pytest.raises(v4.ItemFError, match="same item_f_sha256"):
        v4.require_item_f(h, dirs, sha, ledger_root=root)


def test_a4_rows_that_agree_with_each_other_but_not_with_the_file_or_the_pin_fail(tmp_path, monkeypatch):
    root, dirs, sha = _ledger_state(tmp_path, monkeypatch, [])
    h = str(tmp_path / "runs" / "item_f")
    for i in range(2):
        guard.record_scoring(f"{i}" * 64, f"s{i}", FAKE_COMMIT, root, dataset="samsung", item_f_sha256="f" * 64)
    with pytest.raises(v4.ItemFError, match="differs from the item"):
        v4.require_item_f(h, dirs, None, ledger_root=root)


def test_a4_no_samsung_row_fails_when_the_ledger_is_demanded_and_the_mtime_check_stays(tmp_path, monkeypatch):
    root, dirs, sha = _ledger_state(tmp_path, monkeypatch, [])
    h = str(tmp_path / "runs" / "item_f")
    with pytest.raises(v4.ItemFError, match="no Samsung row"):
        v4.require_item_f(h, dirs, sha, ledger_root=root)
    guard.record_scoring("1" * 64, "s1", FAKE_COMMIT, root, dataset="samsung", item_f_sha256=sha)
    p = os.path.join(h, v4.ITEM_F_FILE)                                                  # the secondary mtime check still refuses a file newer than an outer score
    json.dump({"condition": 1}, open(os.path.join(dirs[0], "condition_scores.json"), "w"))
    os.utime(os.path.join(dirs[0], "condition_scores.json"), (os.path.getmtime(p) - 100, os.path.getmtime(p) - 100))
    with pytest.raises(v4.ItemFError, match="written after an outer score"):
        v4.require_item_f(h, dirs, sha, ledger_root=root)


def test_a4_run_stats_v4_and_its_cli_carry_the_ledger_root():
    import inspect
    from pinnkan import stats_step
    assert "ledger_root" in inspect.signature(stats_step.run_stats_v4).parameters
    assert "--ledger-root" in inspect.getsource(stats_step.main)


# ------------------------------------------------------------------------------------------------ action 5: smoke test with real (synthetic-data) inner runs
def test_a5_smoke_four_arm_inner_runs_to_build_item_f_to_the_report(tmp_path, monkeypatch):
    synth_cfg = lambda f: {"run_id": f"item_f_smoke_f{f}", "dataset": "synthetic", "test": "B", "fold": f, "mode": "inner", "m": 8, "subset": "maxmin", "arms": ["A1", "A9", "A11", "A12"],
                           "n_trials": 1, "inner_k": 2, "steps_scale": 0.04, "seeds": [0], "diagnostics": False, "refit_timing": False,
                           "synthetic": {"kind": "G0", "n_cyc_cond": 16, "n_sto_cond": 4, "reps": 2, "seed": 3}}
    cfgs = [synth_cfg(f) for f in range(5)]
    root, payload = freeze_root(tmp_path, monkeypatch, cfg_ins=cfgs)
    runs = str(tmp_path / "runs")
    dirs = [run.run(c, root=root, runs_dir=runs) for c in cfgs]
    for d in dirs:
        assert json.load(open(os.path.join(d, "config.json")))["mode_effective"] == "inner" and not os.path.exists(os.path.join(d, "condition_scores.json"))
        meta_p = os.path.join(d, "train_condition_meta.json")                            # the synthetic data have one laboratory; two are needed for a sign correlation between laboratories
        meta = json.load(open(meta_p))
        json.dump({c: {**v, "lab": ("HM" if i % 2 else "INT")} for i, (c, v) in enumerate(sorted(meta.items()))}, open(meta_p, "w"))
    cell = {"dataset": "synthetic", "test": "B", "m": 8, "k": "2", "subset": "maxmin"}
    rec = v4.build_item_f(root, dirs, cell=cell)
    assert rec["folds"] == [0, 1, 2, 3, 4] and len(rec["runs"]) == 5 and rec["frozen_commit"] == FAKE_COMMIT
    rep = v4.require_item_f(str(tmp_path / "runs" / "item_f"), dirs)
    assert rep["contrast"] == ["D*", "A1"] and rep["n_observations"] == 5 * 8 and "exceeds_rho_s0" in rep and rep["groups"].startswith("inner fold")
    assert guard.sha256_file(str(tmp_path / "runs" / "item_f" / v4.ITEM_F_FILE)) == rec["sha256"]


# ------------------------------------------------------------------------------------------------ action 6: concordance row
def test_a6_concordance_compares_best_hp_and_condition_scores_with_the_confirmatory_g1_run(tmp_path):
    runs_a, runs_b = str(tmp_path / "a"), str(tmp_path / "b")
    a = [fake_run(runs_a, f) for f in range(5)]
    b = [fake_run(runs_b, f) for f in range(5)]                                          # identical in every respect
    out = v4.item_f_concordance(a, b)
    assert out["n_folds"] == 5 and out["n_folds_dstar_differs"] == 0 and out["reopen_flag"] is False
    r = out["rows"][0]
    assert r["dstar_agree"] and r["arms"]["A1"]["best_hp_equal"] and r["arms"]["A1"]["max_abs_diff_pp"] == 0.0 and r["arms"]["D*"]["n_conditions_common"] == 8 and r["arms"]["A1"]["spearman"] == pytest.approx(1.0)
    # a different D* in one fold, a different tuned setting and shifted scores in another: reported, flag still off (re-open needs more than one fold)
    b2 = [fake_run(runs_b + "2", f, dstar=("A12" if f == 1 else "A9"), scores_shift=(0.5 if f == 2 else 0.0)) for f in range(5)]
    td = os.path.join(b2[3], "tuning_done.json")
    t = json.load(open(td))
    t["arms"]["A1"]["best_hp"] = {"h": 3}
    json.dump(t, open(td, "w"))
    out = v4.item_f_concordance(a, b2)
    by = {r["fold"]: r for r in out["rows"]}
    assert out["n_folds_dstar_differs"] == 1 and by[1]["dstar_agree"] is False and by[1]["arms"]["D*"]["arm_confirmatory"] == "A12" and out["reopen_flag"] is False
    assert by[2]["arms"]["A1"]["max_abs_diff_pp"] == pytest.approx(0.5) and by[3]["arms"]["A1"]["best_hp_equal"] is False and by[0]["arms"]["A1"]["best_hp_equal"] is True
    # a different D* in two folds trips the D026 re-open flag
    b3 = [fake_run(runs_b + "3", f, dstar=("A12" if f in (1, 4) else "A9")) for f in range(5)]
    assert v4.item_f_concordance(a, b3)["reopen_flag"] is True and v4.item_f_concordance(a, b3)["n_folds_dstar_differs"] == 2


def test_a4_once_a_frozen_exists_the_statistics_step_checks_the_ledger_without_being_asked(tmp_path, monkeypatch):
    from pinnkan import stats_step
    root, dirs, sha = _ledger_state(tmp_path, monkeypatch, [])
    h = str(tmp_path / "runs" / "item_f")
    monkeypatch.setattr(guard, "_DEFAULT_ROOT", root)
    with pytest.raises(v4.ItemFError, match="no Samsung row"):                          # FROZEN exists in the (temporary) default root, the ledger holds no Samsung row
        stats_step.run_stats_v4(str(tmp_path / "an"), dirs, item_f_dir=h, item_f_sha256=sha)
