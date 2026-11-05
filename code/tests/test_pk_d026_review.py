"""D026 code review fixes (debates/D026_item_f_blinding/04_code_review.md: I1, m1, m2, m3, m4). Temporary roots only; no Samsung data is read."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import pytest

from pinnkan import data, guard, stats_v4 as v4
from pk_freeze import FAKE_COMMIT, make_freeze


def test_i1_load_split_samsung_test_role_calls_the_item_f_gate(monkeypatch):
    calls = []
    monkeypatch.setattr(guard, "guard_role", lambda *a, **k: None)
    monkeypatch.setattr(guard, "require_frozen", lambda *a, **k: None)

    def gate(root, runs_dir):
        calls.append(runs_dir)
        raise guard.TestFoldAccessError("refused: no record")
    monkeypatch.setattr(guard, "require_item_f_record", gate)
    built = []
    monkeypatch.setattr(data, "_load_samsung", lambda *a, keep=None, **k: built.append(keep) or [])
    monkeypatch.setattr(data, "apply_subset", lambda train, *a, **k: (train, {}))
    with pytest.raises(guard.TestFoldAccessError, match="no record"):
        data.load_split("samsung", "B", 0, role="test", runs_dir="RUNS")
    assert calls == ["RUNS"] and len(built) == 1          # only the training side was built; the test side never was


def test_i1_isu_test_role_does_not_call_the_gate(monkeypatch):
    monkeypatch.setattr(guard, "guard_role", lambda *a, **k: None)
    monkeypatch.setattr(guard, "require_frozen", lambda *a, **k: None)
    monkeypatch.setattr(guard, "require_item_f_record", lambda *a, **k: (_ for _ in ()).throw(AssertionError("gate called for ISU")))
    monkeypatch.setattr(data, "_load_isu", lambda *a, keep=None, **k: [])
    monkeypatch.setattr(data, "apply_subset", lambda train, *a, **k: (train, {}))
    sv = data.load_split("isu", "B", 0, role="test")
    assert sv.test_cells == []


def _scores_dir(base, name, dataset, marker):
    d = os.path.join(base, *name.split("/"))
    os.makedirs(d, exist_ok=True)
    json.dump({"dataset": dataset}, open(os.path.join(d, "config.json"), "w"))
    open(os.path.join(d, "condition_scores.json"), "w").write("{}")
    if marker:
        open(os.path.join(d, "SYNTHETIC"), "w").write("x")
    return d


def test_m1_marker_does_not_exempt_a_samsung_config_outside_the_figure_demos(tmp_path):
    runs = str(tmp_path)
    bad = _scores_dir(runs, "some_samsung_run", "samsung", True)
    _scores_dir(runs, "figdemo_SYNTHETIC/test_B", "samsung", True)
    _scores_dir(runs, "synth_run", "synthetic", True)
    assert v4._samsung_scores_under(runs) == [bad]


def test_m2_record_scoring_refuses_a_row_without_dataset(tmp_path):
    with pytest.raises(guard.TestFoldAccessError, match="dataset"):
        guard.record_scoring("a" * 64, "x", FAKE_COMMIT, str(tmp_path))


def test_m2_stats_ledger_check_counts_a_row_without_dataset_as_samsung(tmp_path):
    d = str(tmp_path / "itemf")
    v4.write_item_f(d, {"x": 1})
    p = os.path.join(str(tmp_path), guard.SCORED_REL)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "a", encoding="utf8").write(json.dumps({"config_sha256": "c" * 64, "run_id": "x", "commit": FAKE_COMMIT}) + chr(10))
    with pytest.raises(v4.ItemFError):
        v4.require_item_f(d, [], ledger_root=str(tmp_path))


def test_m3_run_py_re_appends_the_verified_record_after_the_log_clear():
    src = open(os.path.join(ROOT, "code", "pinnkan", "run.py"), encoding="utf8").read()
    i = src.index("guard.GUARD_LOG.clear()")
    assert '"item (f) record", "verified": True' in src[i:i + 400]


def test_m4_a_pinned_freeze_without_five_item_f_configs_refuses(tmp_path, monkeypatch):
    payload = make_freeze(tmp_path, monkeypatch)
    payload["pins"] = {}
    payload["item_f_config_sha256s"] = ["a" * 64] * 5                                   # five entries but not distinct
    json.dump(payload, open(tmp_path / "runs" / "prereg" / "FROZEN", "w"))
    with pytest.raises(guard.TestFoldAccessError, match="five distinct"):
        guard.verify_freeze(str(tmp_path))
    payload["item_f_config_sha256s"] = [f"{i}" * 64 for i in range(5)]
    json.dump(payload, open(tmp_path / "runs" / "prereg" / "FROZEN", "w"))
    guard.verify_freeze(str(tmp_path))
