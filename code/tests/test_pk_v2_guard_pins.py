"""build_v2 follow-up: FROZEN pins subsets.json, symbolic_library.json and the item (f) dependence file; verification refuses on any difference."""
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
    v4.write_item_f(str(tmp_path / "runs" / "prereg"), {"rho_fold": 0.01})
    payload["pins"] = {}
    for name, rel in guard.PIN_FILES.items():
        payload["pins"][name] = {"file": rel, "sha256": guard.sha256_file(os.path.join(root, rel))}
    json.dump(payload, open(tmp_path / "runs" / "prereg" / "FROZEN", "w"))
    return root, payload


def test_pin_names_match_stats_v4_file_names():
    assert os.path.basename(guard.PIN_FILES["item_f"]) == v4.ITEM_F_FILE and os.path.basename(guard.PIN_FILES["item_f_record"]) == v4.ITEM_F_HASH


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


def test_build_freeze_payload_pins_the_three_files_and_refuses_when_one_is_missing(tmp_path, monkeypatch):
    root, _ = _pin_root(tmp_path, monkeypatch)
    shutil.copy(os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json"), tmp_path / "runs" / "prereg" / "samsung_splits_v2.json")
    p = guard.build_freeze_payload(root, [("samsung", "B")], [], prereg_file="runs/prereg/PREREG_v2.md")
    assert set(p["pins"]) == set(guard.PIN_FILES) and all(len(e["sha256"]) == 64 for e in p["pins"].values())
    assert p["pins"]["subsets"]["sha256"] == guard.sha256_file(os.path.join(root, "runs", "prereg", "subsets.json"))
    os.remove(os.path.join(root, guard.PIN_FILES["item_f"]))
    with pytest.raises(guard.TestFoldAccessError, match="cannot pin item_f"):
        guard.build_freeze_payload(root, [("samsung", "B")], [], prereg_file="runs/prereg/PREREG_v2.md", require_pins=True)
    q = guard.build_freeze_payload(root, [("samsung", "B")], [], prereg_file="runs/prereg/PREREG_v2.md")          # default: listed, and a FROZEN built so is refused
    assert q["pins_missing"] == ["item_f"] and "item_f" not in q["pins"]
    json.dump({**q, "commit": "a" * 40}, open(tmp_path / "runs" / "prereg" / "FROZEN", "w"))
    with pytest.raises(guard.TestFoldAccessError, match="without the pins"):
        guard.verify_freeze(root, check_git=False)
