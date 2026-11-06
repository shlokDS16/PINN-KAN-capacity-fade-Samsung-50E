"""Pre-freeze exposure exclusions of the Samsung confirmatory tests (PREREG_v4 3.3(11), pin 2b, section 17.2 C13). Identifiers only: no capacity or retention value is read here.

Rule (fixed before any score): a cell of kind (b) of `runs/prereg/BLINDING_LOG.md` (capacity values displayed on a terminal during development) that is an OUTER-TEST cell of a confirmatory
test (Test B, Test C, S2) is excluded from the scoring of that test for every arm and every grid cell; it stays in training wherever it is a training cell. A condition keeps its equal
weight with its remaining scored cells; a condition left with no scored cell is dropped and n is reduced. Kind (a) exposures (the pipeline parse and QC of 163 check-ups of 19 cells) carry
no exclusion. The sensitivity row of 9.9 (i) scores the excluded cells (`score_blinded_cells`).

`runs/prereg/blinding_exclusions.json` is written by `code/prereg/make_blinding_exclusions.py` from the split file and the design table (`samsung_cells.csv`: cell identifiers and design
parameters), pinned in FROZEN (guard.PIN_FILES) and applied by `data.load_split` when test cells are released."""
import hashlib
import json
import os

import pandas as pd

from . import ROOT as _ROOT

EXCLUSIONS_REL = os.path.join("runs", "prereg", "blinding_exclusions.json")
CELLS_REL = os.path.join("data", "processed", "samsung_cells.csv")
CONFIRMATORY_TESTS = ("B", "C", "S2")
# kind (b) of the blinding log (capacity values shown on a terminal before the freeze); the cell identifier is <serial>_s<stage> as in the split files
KIND_B_CELLS = (("TP_k03_01_s2", "BL 2026-11-04 22:40 (lead, P0 probe): TP_k03_01, stage 2"),
                ("TP_z18_01_s2", "BL 2026-11-04 22:40 (lead, P0 probe): TP_z18_01, stage 2"),
                ("TP_z02_01_s2", "BL 2026-11-05 03:15 (lead, QC flags): TP_z02_01_s2"),
                ("TP_z02_02_s2", "BL 2026-11-05 03:15 (lead, QC flags): TP_z02_02_s2"),
                ("TP_z24_01_s1", "BL 2026-11-05 ~04:00 (builder agent, grep): TP_z24_01_s1"))


class BlindingExclusionError(RuntimeError):
    """the exclusion file is missing where it is pinned, altered, or made from another split file"""


def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    with open(path, "rb") as fh:
        return _sha_bytes(fh.read())


def body_sha256(rec):
    return _sha_bytes(json.dumps({k: v for k, v in rec.items() if k != "sha256"}, sort_keys=True).encode())


def _cond_key(row):
    from .data import samsung_cond_key
    kind = "cycling" if row["type"] == "z" else "storage"
    return samsung_cond_key(kind, float(row["T_C"]), float(row["SOC_max"]), float(row["DoD"]), float(row["C_ch"]), float(row["C_dch"]))


def build_record(splits_path, cells_csv, kind_b=KIND_B_CELLS):
    """-> the record of blinding_exclusions.json: per confirmatory test and outer fold the excluded cells, their conditions, the scored cells that remain and the conditions that would be dropped"""
    sp = json.load(open(splits_path, encoding="utf8"))
    cells = pd.read_csv(cells_csv, usecols=["cell_id", "type", "T_C", "SOC_max", "DoD", "C_ch", "C_dch"]).set_index("cell_id")
    ids = [c for c, _ in kind_b]
    missing = [c for c in ids if c not in cells.index]
    if missing:
        raise BlindingExclusionError(f"kind (b) cells not in the design table: {missing}")
    cond_of = {cid: _cond_key(cells.loc[cid]) for cid in cells.index}
    rec = {"rule": "PREREG_v4 3.3(11): a kind (b) cell that is an outer-test cell of a confirmatory test is excluded from its scoring for every arm and grid cell; it stays in training; a condition with no scored cell left is dropped and n is reduced",
           "kind_a": "pipeline parse and QC of 163 check-ups of 19 cells (BL 2026-11-05 00:09): disclosed (3.3(10)(a)), no exclusion",
           "kind_b_cells": [{"cell_id": c, "condition": cond_of[c], "log_row": why} for c, why in kind_b],
           "source_splits": os.path.basename(splits_path), "splits_sha256": sha256_file(splits_path), "cells_table": CELLS_REL.replace("\\", "/"),
           "confirmatory_tests": list(CONFIRMATORY_TESTS), "excluded": {}, "per_fold": {}, "other_tests_informational": {}}
    for test, blk in sp.items():
        for f, fd in sorted((blk.get("folds") or {}).items(), key=lambda kv: int(kv[0])):
            tcs = [str(c) for c in fd.get("test_cells", [])]
            hit = sorted(c for c in ids if c in set(tcs))
            if not hit:
                continue
            if test not in CONFIRMATORY_TESTS:
                rec["other_tests_informational"].setdefault(test, {})[f] = hit
                continue
            rec["excluded"].setdefault(test, {})[f] = hit
            by_cond = {}
            for c in tcs:
                by_cond.setdefault(cond_of[c], []).append(c)
            rows = {}
            for c in hit:
                k = cond_of[c]
                left = [x for x in by_cond[k] if x not in hit]
                rows[k] = {"test_cells_in_condition": len(by_cond[k]), "excluded": sorted(x for x in by_cond[k] if x in hit), "scored_cells_left": len(left)}
            rec["per_fold"].setdefault(test, {})[f] = {"conditions": rows, "conditions_dropped": sorted(k for k, v in rows.items() if v["scored_cells_left"] == 0),
                                                        "n_test_conditions": len(by_cond)}
    rec["n_conditions_dropped"] = {t: sum(len(v["conditions_dropped"]) for v in fs.values()) for t, fs in rec["per_fold"].items()}
    rec["sha256"] = body_sha256(rec)
    return rec


def load_record(root=None, path=None):
    """-> the verified record (the body must hash to its own `sha256`)"""
    root = root or _ROOT
    p = path or os.path.join(root, EXCLUSIONS_REL)
    rec = json.load(open(p, encoding="utf8"))
    if rec.get("sha256") != body_sha256(rec):
        raise BlindingExclusionError(f"{p}: the content hash does not match (edited file)")
    return rec


def excluded_cells(root, test, fold, splits_sha256=None):
    """the outer-test cells excluded from scoring in (test, fold): a set of cell ids. Samsung confirmatory tests only; empty otherwise. The file is required when FROZEN pins it (verify_freeze checks its
    hash); a tree whose FROZEN does not pin it (older freezes, test trees) and has no file excludes nothing. With a file, it must have been made from the split file in use."""
    if test not in CONFIRMATORY_TESTS:
        return set()
    from . import guard
    p = os.path.join(root, EXCLUSIONS_REL)
    pinned = "blinding_exclusions" in ((guard.read_freeze(root) or {}).get("pins") or {})
    if not os.path.isfile(p):
        if pinned:
            raise BlindingExclusionError(f"{EXCLUSIONS_REL} is pinned in FROZEN but absent")
        return set()
    rec = load_record(root, p)
    if splits_sha256 is not None and rec["splits_sha256"] != splits_sha256:
        raise BlindingExclusionError("blinding_exclusions.json was made from another split file than the one in use")
    return set(rec["excluded"].get(test, {}).get(str(int(fold)), []))
