"""Frozen laboratory map of the Samsung cycling conditions (D024 section 4; PREREG 9.1 and 9.8).

One map for every consumer: `runs/prereg/lab_map.json`, written once from the design table `data/processed/samsung_cells.csv` (all cells of a condition,
regardless of QC, scoring or blinding exclusions) by the rule

    majority laboratory = the laboratory with most cells in the condition;
    an exact tie goes to the laboratory with more cycling cells in the whole design (HM 69, INT 60, SIE 18);
    if still tied, alphabetical.

Result: HM 17 / INT 19 / SIE 4 conditions; the only exact tie (T23|SOCmax0.8|DoD0.25|Cch0.2|Cdch1.4: HM 3, INT 3) is HM. Consumers (`extraction_calibration.majority_labs`,
`metrics.train_condition_meta`, `stats_ext.condition_strata`) read this file instead of counting cells of their own (a count over training or scored cells could flip
a stratum after a blinding exclusion or a QC drop). Conditions that are not in the file (ISU, SNL, synthetic) keep the local majority with an alphabetical tie-break.
Build:  .venv/Scripts/python.exe -P -m pinnkan.labmap --write   (from ROOT/code on sys.path)
"""
from __future__ import annotations

import hashlib
import json
import os

import pandas as pd

from . import ROOT as _ROOT

LAB_MAP_REL = os.path.join("runs", "prereg", "lab_map.json")
CELLS_REL = os.path.join("data", "processed", "samsung_cells.csv")
_CACHE: dict = {}


def map_sha256(conditions: dict) -> str:
    return hashlib.sha256(json.dumps(conditions, sort_keys=True).encode()).hexdigest()


def build_lab_map(cells: pd.DataFrame) -> dict:
    """cells: the Samsung cell table (columns type, lab, T_C, SOC_max, DoD, C_ch, C_dch). -> dict as written to lab_map.json"""
    from .data import samsung_cond_key
    z = cells[cells["type"] == "z"]
    design_lab = {str(k): int(v) for k, v in z.groupby("lab").size().items()}
    cnt: dict = {}
    for r in z.itertuples():
        key = samsung_cond_key("cycling", float(r.T_C), float(r.SOC_max), float(r.DoD), float(r.C_ch), float(r.C_dch))
        e = cnt.setdefault(key, {})
        e[str(r.lab)] = e.get(str(r.lab), 0) + 1
    conditions = {k: sorted(v.items(), key=lambda kv: (-kv[1], -design_lab[kv[0]], kv[0]))[0][0] for k, v in cnt.items()}
    mixed = {k: v for k, v in cnt.items() if len(v) > 1}
    ties = [k for k, v in mixed.items() if sorted(v.values(), reverse=True)[0] == sorted(v.values(), reverse=True)[1]]
    return {"rule": "most cells in the condition (design table, all cells); exact tie -> laboratory with more cycling cells in the whole design; then alphabetical",
            "design_cycling_cells_by_lab": design_lab, "n_conditions": len(conditions),
            "conditions_by_lab": {k: int(v) for k, v in pd.Series(list(conditions.values())).value_counts().sort_index().items()},
            "exact_ties": ties, "mixed_conditions_cell_counts": mixed, "conditions": dict(sorted(conditions.items())), "conditions_sha256": map_sha256(dict(sorted(conditions.items())))}


def write_lab_map(root: str | None = None) -> dict:
    root = root or _ROOT
    cells_path = os.path.join(root, CELLS_REL)
    m = build_lab_map(pd.read_csv(cells_path))
    m["source"] = CELLS_REL
    m["source_sha256"] = hashlib.sha256(open(cells_path, "rb").read()).hexdigest()
    out = os.path.join(root, LAB_MAP_REL)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf8") as f:
        json.dump(m, f, indent=1, sort_keys=True)
    _CACHE.clear()
    return m


def load_lab_map(root: str | None = None, required: bool = False):
    """(condition -> lab, sha256 of the map), or ({}, "") when the file is absent and not required. The recorded hash is verified."""
    p = os.path.join(root or _ROOT, LAB_MAP_REL)
    if not os.path.isfile(p):
        if required:
            raise FileNotFoundError(f"{LAB_MAP_REL} does not exist: write it with `python -P -m pinnkan.labmap --write`")
        return {}, ""
    key = (p, os.path.getmtime(p))
    if key not in _CACHE:
        m = json.load(open(p, encoding="utf8"))
        if map_sha256(m["conditions"]) != m["conditions_sha256"]:
            raise ValueError(f"{LAB_MAP_REL}: conditions do not match their recorded sha256")
        _CACHE[key] = (dict(m["conditions"]), m["conditions_sha256"])
    return _CACHE[key]


def lab_of(cond: str, counts: dict, root: str | None = None) -> str:
    """frozen laboratory of a condition when it is in the map, else the local majority of `counts` (ties alphabetical)"""
    mp, _ = load_lab_map(root)
    if cond in mp:
        return mp[cond]
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if counts else ""


if __name__ == "__main__":
    import sys
    if "--write" in sys.argv:
        r = write_lab_map()
        print(json.dumps({k: r[k] for k in ("n_conditions", "conditions_by_lab", "exact_ties", "design_cycling_cells_by_lab", "conditions_sha256")}, indent=1))
    else:
        print("use --write")
