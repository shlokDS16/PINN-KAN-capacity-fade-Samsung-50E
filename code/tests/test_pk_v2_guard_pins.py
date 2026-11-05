"""build_v2 follow-up: FROZEN pins subsets.json and symbolic_library.json; verification refuses on any difference. D026: the item (f) file and its record are no longer pinned (the five item (f) configs are, see test_pk_d026_item_f.py)."""
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import pytest

from pinnkan import guard, stats_v4 as v4
from pk_freeze import make_freeze


def _pin_root(tmp_path, monkeypatch):
    payload = make_freeze(tmp_path, monkeypatch)
    root = str(tmp_path)
    (tmp_path / "code" / "pinnkan").mkdir(parents=True)
    shutil.copy(os.path.join(ROOT, "runs", "prereg", "subsets.json"), tmp_path / "runs" / "prereg" / "subsets.json")
    (tmp_path / "code" / "pinnkan" / "symbolic_library.json").write_text(json.dumps({"max_coeffs_per_edge": 3}))
    payload["pins"] = {}
    for name, rel in guard.PIN_FILES.items():
        payload["pins"][name] = {"file": rel, "sha256": guard.sha256_file(os.path.join(root, rel))}
    json.dump(payload, open(tmp_path / "runs" / "prereg" / "FROZEN", "w"))
    return root, payload


def test_pin_names_and_item_f_file_names():
    assert set(guard.PIN_FILES) == {"subsets", "symbolic_library"}                       # D026 action 1: item_f and item_f_record left the pins
    assert guard.ITEM_F_FILE == v4.ITEM_F_FILE and guard.ITEM_F_HASH == v4.ITEM_F_HASH


def test_verification_passes_with_every_pin_in_place_and_without_pins_keeps_the_old_behaviour(tmp_path, monkeypatch):
    root, payload = _pin_root(tmp_path, monkeypatch)
    assert guard.verify_freeze(root)["pins"].keys() == guard.PIN_FILES.keys()
    del payload["pins"]
    json.dump(payload, open(tmp_path / "runs" / "prereg" / "FROZEN", "w"))
    assert "pins" not in guard.verify_freeze(root)


@pytest.mark.parametrize("name", list(guard.PIN_FILES))
def test_tampering_with_a_pinned_file_refuses(tmp_path, monkeypatch, name):
    root, _ = _pin_root(tmp_path, monkeypatch)
    fp = os.path.join(root, guard.PIN_FILES[name])
    with open(fp, "a") as fh:
        fh.write(" ")
    with pytest.raises(guard.TestFoldAccessError, match="differs"):
        guard.verify_freeze(root)
    assert not guard.is_valid_freeze(root)
    with pytest.raises(guard.TestFoldAccessError):
        guard.require_frozen("score", root)


@pytest.mark.parametrize("name", list(guard.PIN_FILES))
def test_a_missing_pinned_file_refuses(tmp_path, monkeypatch, name):
    root, _ = _pin_root(tmp_path, monkeypatch)
    os.remove(os.path.join(root, guard.PIN_FILES[name]))
    with pytest.raises(guard.TestFoldAccessError, match="absent"):
        guard.verify_freeze(root)


def test_build_freeze_payload_pins_the_two_files_and_refuses_when_one_is_missing(tmp_path, monkeypatch):
    root, _ = _pin_root(tmp_path, monkeypatch)
    shutil.copy(os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json"), tmp_path / "runs" / "prereg" / "samsung_splits_v2.json")
    p = guard.build_freeze_payload(root, [("samsung", "B")], [], prereg_file="runs/prereg/PREREG_v2.md")
    assert set(p["pins"]) == set(guard.PIN_FILES) and all(len(e["sha256"]) == 64 for e in p["pins"].values())
    assert p["pins"]["subsets"]["sha256"] == guard.sha256_file(os.path.join(root, "runs", "prereg", "subsets.json"))
    os.remove(os.path.join(root, guard.PIN_FILES["symbolic_library"]))
    with pytest.raises(guard.TestFoldAccessError, match="cannot pin symbolic_library"):
        guard.build_freeze_payload(root, [("samsung", "B")], [], prereg_file="runs/prereg/PREREG_v2.md", require_pins=True,
                                   item_f_config_paths=_five_item_f_configs(tmp_path))
    q = guard.build_freeze_payload(root, [("samsung", "B")], [], prereg_file="runs/prereg/PREREG_v2.md", item_f_config_paths=_five_item_f_configs(tmp_path))          # default: listed, and a FROZEN built so is refused
    assert q["pins_missing"] == ["symbolic_library"] and "symbolic_library" not in q["pins"] and len(q["item_f_config_sha256s"]) == 5
    json.dump({**q, "commit": "a" * 40}, open(tmp_path / "runs" / "prereg" / "FROZEN", "w"))
    with pytest.raises(guard.TestFoldAccessError, match="without the pins"):
        guard.verify_freeze(root, check_git=False)


def _five_item_f_configs(tmp_path):
    out = []
    for f in range(5):
        p = tmp_path / f"if_cfg{f}.json"
        p.write_text(json.dumps({"run_id": f"item_f_{f}", "dataset": "samsung", "test": "B", "fold": f, "mode": "inner", "m": 8}))
        out.append(str(p))
    return out
