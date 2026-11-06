"""C13: blinding exclusions (PREREG_v4 3.3(11)): the identifier-only file, its hash, the scorer's exclusion list in data.load_split, the sensitivity option, the pin, the split copy."""
import json
import os
import shutil
import sys
from types import SimpleNamespace

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import pandas as pd
import pytest

from pinnkan import blinding, data, guard

SPLITS = os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json")
COPY = os.path.join(ROOT, "runs", "splits", "samsung_splits_v2.json")
FILE = os.path.join(ROOT, blinding.EXCLUSIONS_REL)
CELLS = os.path.join(ROOT, blinding.CELLS_REL)


def test_the_committed_file_is_verified_names_the_expected_cells_and_was_made_from_the_pinned_split():
    rec = blinding.load_record(ROOT)
    assert rec["excluded"] == {"B": {"0": ["TP_z18_01_s2"], "1": ["TP_z24_01_s1"], "2": ["TP_z02_01_s2", "TP_z02_02_s2"]}, "S2": {"4": ["TP_k03_01_s2"]}}
    assert "C" not in rec["excluded"] and rec["other_tests_informational"] == {"A": {"0": ["TP_z02_01_s2", "TP_z24_01_s1"], "1": ["TP_z02_02_s2", "TP_z18_01_s2"]}}
    assert rec["splits_sha256"] == blinding.sha256_file(SPLITS) == blinding.sha256_file(COPY) and rec["n_conditions_dropped"] == {"B": 0, "S2": 0}
    assert {c["cell_id"] for c in rec["kind_b_cells"]} == {"TP_k03_01_s2", "TP_z18_01_s2", "TP_z02_01_s2", "TP_z02_02_s2", "TP_z24_01_s1"}
    assert len({c for fs in rec["excluded"]["B"].values() for c in fs}) == 4                                       # four z-type outer-test cells of Test B: n >= 36 (PREREG 9.3 reduced n)
    assert not any(k in rec for k in ("capacity", "retention", "values"))


def test_the_split_copy_is_byte_identical_and_the_loader_finds_it_first():
    assert open(SPLITS, "rb").read() == open(COPY, "rb").read()
    assert data.split_path(ROOT, "samsung", "B") == COPY


def test_the_file_is_rebuilt_reproducibly_by_the_script(tmp_path):
    sys.path.insert(0, os.path.join(ROOT, "code", "prereg"))
    import make_blinding_exclusions as M
    out = str(tmp_path / "x.json")
    M.main(["--out", out])
    assert json.load(open(out)) == json.load(open(FILE))


def test_an_edited_file_is_refused(tmp_path):
    rec = json.load(open(FILE))
    rec["excluded"]["B"]["0"] = []
    p = str(tmp_path / "e.json")
    json.dump(rec, open(p, "w"))
    with pytest.raises(blinding.BlindingExclusionError, match="content hash"):
        blinding.load_record(path=p)


def test_a_condition_left_without_a_scored_cell_is_listed_as_dropped(tmp_path):
    sp = {"B": {"folds": {"0": {"test_cells": ["TP_z01_01_s1", "TP_z02_01_s1", "TP_z02_02_s1"]}}}}
    json.dump(sp, open(tmp_path / "s.json", "w"))
    pd.DataFrame({"cell_id": ["TP_z01_01_s1", "TP_z02_01_s1", "TP_z02_02_s1"], "type": "z", "T_C": 23, "SOC_max": [0.8, 0.8, 0.8], "DoD": [0.2, 0.3, 0.3], "C_ch": 1, "C_dch": 1}).to_csv(tmp_path / "c.csv", index=False)
    rec = blinding.build_record(str(tmp_path / "s.json"), str(tmp_path / "c.csv"), kind_b=(("TP_z01_01_s1", "x"), ("TP_z02_01_s1", "y")))
    f = rec["per_fold"]["B"]["0"]
    assert f["conditions_dropped"] == ["T23|SOCmax0.8|DoD0.2|Cch1|Cdch1"] and f["conditions"]["T23|SOCmax0.8|DoD0.3|Cch1|Cdch1"]["scored_cells_left"] == 1 and rec["n_conditions_dropped"] == {"B": 1}
    with pytest.raises(blinding.BlindingExclusionError, match="not in the design table"):
        blinding.build_record(str(tmp_path / "s.json"), str(tmp_path / "c.csv"), kind_b=(("TP_nope_s1", "x"),))


# ------------------------------------------------------------------------------------------------ the scorer's list in data.load_split
def _tree(tmp_path, with_file=True):
    root = tmp_path / "tree"
    (root / "runs" / "splits").mkdir(parents=True)
    (root / "runs" / "prereg").mkdir(parents=True)
    shutil.copyfile(COPY, root / "runs" / "splits" / "samsung_splits_v2.json")
    if with_file:
        shutil.copyfile(FILE, root / "runs" / "prereg" / "blinding_exclusions.json")
    return str(root)


@pytest.fixture
def fake_samsung(monkeypatch):
    """the design table as the cell universe: every cell has its condition; _load_samsung applies `keep` as the real loader does"""
    df = pd.read_csv(CELLS, usecols=["cell_id", "type", "T_C", "SOC_max", "DoD", "C_ch", "C_dch", "cell"])

    def fake(root, retain_all=False, throughput="analytic", include_at=False, keep=None, throughput_fallback="none", include_storage_0406=False):
        out = []
        for r in df.itertuples():
            kind = "cycling" if r.type == "z" else "storage"
            cond = data.samsung_cond_key(kind, float(r.T_C), float(r.SOC_max), float(r.DoD), float(r.C_ch), float(r.C_dch))
            if keep is None or keep(r.cell_id, cond, kind, int(r.cell)):
                out.append(SimpleNamespace(cell_id=r.cell_id, kind=kind, cond=cond))
        return out
    monkeypatch.setattr(data, "_load_samsung", fake)
    monkeypatch.setattr(data, "apply_subset", lambda train, *a, **k: (train, None))
    monkeypatch.setattr(guard, "require_frozen", lambda *a, **k: None)
    monkeypatch.setattr(guard, "require_item_f_record", lambda *a, **k: None)
    monkeypatch.setattr(data, "_input_manifest", lambda root, ds: [])
    monkeypatch.setattr(guard, "guard_role", lambda *a, **k: None)
    monkeypatch.setattr(guard, "pinned_split", lambda *a, **k: None)
    monkeypatch.setattr(guard, "read_freeze", lambda root=None: None)


def test_the_scorer_withholds_the_excluded_cells_of_the_outer_test_side_for_every_confirmatory_test(tmp_path, fake_samsung):
    root = _tree(tmp_path)
    cases = [("B", 0, {"TP_z18_01_s2"}), ("B", 1, {"TP_z24_01_s1"}), ("B", 2, {"TP_z02_01_s2", "TP_z02_02_s2"}), ("B", 3, set()), ("B", 4, set()), ("S2", 4, {"TP_k03_01_s2"}), ("S2", 0, set()), ("C", 0, set())]
    for test, fold, want in cases:
        sv = data.load_split("samsung", test, fold, role="test", root=root)
        ids = {c.cell_id for c in sv.test_cells}
        assert not (ids & want) and sv.blinding_excluded == sorted(want), (test, fold)
        full = data.load_split("samsung", test, fold, role="test", root=root, score_blinded_cells=True)           # the 9.9 (i) sensitivity row scores them
        assert want <= {c.cell_id for c in full.test_cells} and full.blinding_excluded == []
        assert len(full.test_cells) - len(sv.test_cells) == len(want)


def test_training_sides_keep_the_exposed_cells_where_they_are_training_cells(tmp_path, fake_samsung):
    root = _tree(tmp_path)
    sv = data.load_split("samsung", "B", 1, role="test", root=root)                                              # TP_z24_01_s1 is a Test B fold 1 test cell; in fold 0 it is a training cell
    assert "TP_z24_01_s1" not in {c.cell_id for c in sv.train}
    sv0 = data.load_split("samsung", "B", 0, role="train", root=root)
    assert "TP_z24_01_s1" in {c.cell_id for c in sv0.train} and sv0.test_cells is None


def test_a_missing_file_refuses_when_frozen_pins_it_and_a_split_mismatch_refuses(tmp_path, fake_samsung, monkeypatch):
    root = _tree(tmp_path, with_file=False)
    assert data.load_split("samsung", "B", 1, role="test", root=root).blinding_excluded == []                   # a tree whose FROZEN does not pin the file and has none: no exclusion
    monkeypatch.setattr(guard, "read_freeze", lambda root=None: {"pins": {"blinding_exclusions": {"file": blinding.EXCLUSIONS_REL, "sha256": "x"}}})
    with pytest.raises(blinding.BlindingExclusionError, match="pinned in FROZEN but absent"):
        data.load_split("samsung", "B", 1, role="test", root=root)
    root2 = _tree(tmp_path / "two")
    rec = json.load(open(os.path.join(root2, blinding.EXCLUSIONS_REL)))
    rec["splits_sha256"] = "0" * 64
    rec["sha256"] = blinding.body_sha256(rec)
    json.dump(rec, open(os.path.join(root2, blinding.EXCLUSIONS_REL), "w"))
    with pytest.raises(blinding.BlindingExclusionError, match="another split file"):
        data.load_split("samsung", "B", 1, role="test", root=root2)


def test_the_file_is_a_freeze_pin_and_the_runner_default_scores_nothing_extra():
    assert guard.PIN_FILES["blinding_exclusions"] == "runs/prereg/blinding_exclusions.json"
    from pinnkan import run
    assert run.DEFAULTS["score_blinded_cells"] is False
    assert blinding.excluded_cells(ROOT, "A", 0) == set()                                                         # Test A is not a confirmatory test: nothing is withheld
