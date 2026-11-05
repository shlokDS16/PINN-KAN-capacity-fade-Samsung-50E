"""Frozen laboratory map (D024 section 4): rule, file, consumers. Identifiers and counts only.

Run:  .venv/Scripts/python.exe -P -m pytest code/tests/test_labmap.py -q   (from ROOT)
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import pandas as pd
import pytest

from pinnkan import labmap, metrics, stats_ext
from pinnkan.data import Cell, samsung_cond_key

COLS = "type,lab,T_C,SOC_max,DoD,C_ch,C_dch"


def _cells(tmp_path, rows):
    d = tmp_path / "data" / "processed"
    d.mkdir(parents=True)
    (d / "samsung_cells.csv").write_text(COLS + "\n" + "\n".join(rows) + "\n")
    return str(tmp_path)


def test_rule_majority_then_design_laboratory_size_then_alphabetical(tmp_path):
    rows = (["z,INT,35,0.5,0.2,0.5,1"] * 3 + ["z,HM,35,0.5,0.2,0.5,1"]                                   # clear majority INT
            + ["z,SIE,23,0.8,0.1,0.5,1"] * 2 + ["z,HM,23,0.8,0.1,0.5,1"] * 2                              # exact tie SIE / HM; HM has more cycling cells in the design
            + ["z,HM,45,0.8,0.3,0.5,1"] * 3 + ["z,INT,45,0.8,0.3,0.5,1"] * 2                              # padding so that HM is the largest design laboratory
            + ["k,SIE,23,0.5,0,0,0"] * 9)                                                                  # storage cells never count
    m = labmap.write_lab_map(_cells(tmp_path, rows))
    c = m["conditions"]
    assert c["T35|SOCmax0.5|DoD0.2|Cch0.5|Cdch1"] == "INT"
    assert c["T23|SOCmax0.8|DoD0.1|Cch0.5|Cdch1"] == "HM"                       # tie -> laboratory with more cycling cells in the design (HM 6, INT 5, SIE 2)
    assert m["exact_ties"] == ["T23|SOCmax0.8|DoD0.1|Cch0.5|Cdch1"] and m["design_cycling_cells_by_lab"] == {"HM": 6, "INT": 5, "SIE": 2}
    assert m["conditions_sha256"] == labmap.map_sha256(c)


def test_alphabetical_only_when_design_sizes_tie(tmp_path):
    rows = ["z,SIE,23,0.8,0.1,0.5,1", "z,HM,23,0.8,0.1,0.5,1"]
    assert list(labmap.write_lab_map(_cells(tmp_path, rows))["conditions"].values()) == ["HM"]


def test_a_changed_cell_count_does_not_change_the_frozen_map(tmp_path):
    root = _cells(tmp_path, ["z,SIE,23,0.8,0.1,0.5,1", "z,SIE,23,0.8,0.1,0.5,1", "z,HM,23,0.8,0.1,0.5,1"])
    m = labmap.write_lab_map(root)
    key = "T23|SOCmax0.8|DoD0.1|Cch0.5|Cdch1"
    assert labmap.load_lab_map(root)[0][key] == "SIE"
    pd.DataFrame([dict(type="z", lab="HM", T_C=23, SOC_max=0.8, DoD=0.1, C_ch=0.5, C_dch=1)] * 5).to_csv(os.path.join(root, "data", "processed", "samsung_cells.csv"), index=False)
    mp, sha = labmap.load_lab_map(root)                                        # the table changed (HM now has 5 more cells); the frozen file did not
    assert mp[key] == "SIE" and sha == m["conditions_sha256"]
    p = os.path.join(root, labmap.LAB_MAP_REL)
    tampered = json.load(open(p))
    tampered["conditions"][key] = "HM"
    json.dump(tampered, open(p, "w"))
    with pytest.raises(ValueError, match="sha256"):
        labmap._CACHE.clear()
        labmap.load_lab_map(root)                                              # re-read -> hash check fails


def test_load_requires_the_file_only_when_asked(tmp_path):
    assert labmap.load_lab_map(str(tmp_path)) == ({}, "")
    with pytest.raises(FileNotFoundError):
        labmap.load_lab_map(str(tmp_path), required=True)


def _mini_root_with_map(tmp_path, cond, lab):
    d = tmp_path / "runs" / "prereg"
    d.mkdir(parents=True)
    conds = {cond: lab}
    json.dump({"conditions": conds, "conditions_sha256": labmap.map_sha256(conds)}, open(d / "lab_map.json", "w"))
    return str(tmp_path)


def test_consumers_read_the_frozen_file_not_their_own_counts(tmp_path, monkeypatch):
    cond = samsung_cond_key("cycling", 23.0, 0.8, 0.25, 0.2, 1.4)
    root = _mini_root_with_map(tmp_path, cond, "INT")                           # frozen: INT although the counts below say HM
    monkeypatch.setattr(labmap, "_ROOT", root)
    labmap._CACHE.clear()
    import numpy as np
    cells = [Cell(f"c{i}", "samsung", "cycling", cond, np.zeros(5), np.zeros(2), np.ones(2), np.zeros(2), np.zeros(2, bool), lab="HM", stage="2") for i in range(3)]
    assert metrics.train_condition_meta(cells)[cond]["lab"] == "INT" and metrics.train_condition_meta(cells)[cond]["labs"] == {"HM": 3}
    fold = tmp_path / "fold"
    fold.mkdir()
    json.dump({cond: {"n_cells": 3, "lab": {"HM": 3}, "stage": {"2": 3}}, "c_other": {"n_cells": 3, "lab": {"SIE": 2, "HM": 1}, "stage": {"1": 3}}}, open(fold / "condition_meta.json", "w"))
    st = stats_ext.condition_strata([{"dir": str(fold)}])
    assert st[cond]["lab"] == "INT" and st[cond]["labs"] == {"HM": 3}
    assert st["c_other"]["lab"] == "SIE"                                        # not in the map (non-Samsung or synthetic): local majority
    labmap._CACHE.clear()


@pytest.mark.skipif(not (os.path.exists(os.path.join(ROOT, labmap.LAB_MAP_REL)) and os.path.exists(os.path.join(ROOT, labmap.CELLS_REL))), reason="lab map or cell table absent")
def test_frozen_map_of_the_real_design():
    m = json.load(open(os.path.join(ROOT, labmap.LAB_MAP_REL)))
    assert m["conditions_by_lab"] == {"HM": 17, "INT": 19, "SIE": 4} and m["n_conditions"] == 40
    assert m["design_cycling_cells_by_lab"] == {"HM": 69, "INT": 60, "SIE": 18}
    assert m["exact_ties"] == ["T23|SOCmax0.8|DoD0.25|Cch0.2|Cdch1.4"] and m["conditions"][m["exact_ties"][0]] == "HM"
    assert len(m["mixed_conditions_cell_counts"]) == 3
    rebuilt = labmap.build_lab_map(pd.read_csv(os.path.join(ROOT, labmap.CELLS_REL)))
    assert rebuilt["conditions"] == m["conditions"]
    mp, sha = labmap.load_lab_map(ROOT, required=True)
    assert sha == "629358d675771bc076180c158b626aee15ff6a2247cadf2e2bc81d702d03f687"
