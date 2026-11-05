"""D022 A2/A4: calibration of the extraction audit on design-matched synthetic truths. Rule: debates/D022_datasets_kan/calibration_rule.md (committed before this script).

    .venv/Scripts/python.exe -P code/prereg/extraction_calibration.py --plan                 # prints the plan (counts), runs nothing
    .venv/Scripts/python.exe -P code/prereg/extraction_calibration.py --proc 0 --nproc 3    # A4: from the FROZEN commit only
    .venv/Scripts/python.exe -P code/prereg/extraction_calibration.py --finalize            # merges the records, writes calibration.json and its hash record

Guard: a calibration run needs `guard.verify_freeze` (HEAD = frozen commit, clean tree), no outer score (`runs/prereg/SCORED.jsonl`), and the rule file hash. `--smoke` runs a few
datasets with tiny settings into a temporary directory marked SMOKE (tests only; never a calibration). This build did NOT run the calibration."""
import argparse
import hashlib
import json
import os
import sys
import time
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(1)

from pinnkan import arms as A  # noqa: E402
from pinnkan import extraction_audit as X  # noqa: E402
from pinnkan import guard, subsets, synth  # noqa: E402
from pinnkan.specs import SPECS  # noqa: E402

SPEC = SPECS["synthetic"]
RULE_FILE = os.path.join(ROOT, "debates", "D022_datasets_kan", "calibration_rule.md")
OUT_DIR = os.path.join(ROOT, "runs", "extraction_calibration")
FAM = ("zero", "linear", "log")
CURVE = ("quadratic", "hinge")
BLOCKS = {"additive": 12, "curved": 6, "noadd": 6}            # datasets per (fold, m): rule section 2
FOLDS, MS = tuple(range(5)), (32, 8)
ARMS = {"A15h1": ("A15", {"h": 1}), "A15h2": ("A15", {"h": 2}), "G15": ("G15", {})}
INPUT_INDEX = {n: i for i, n in enumerate(SPEC.stress_names)}


class CalibrationGuardError(RuntimeError):
    pass


# ------------------------------------------------------------------------------------------------ the plan (rule section 2)
def truth_families(block, j):
    """[(family, sign)] for the five inputs of dataset j: additive FAM[(j + i) mod 3], curved CURVE[(j + i) mod 2]; sign + if (j + i) is even, else -"""
    out = []
    for i in range(5):
        fam = FAM[(j + i) % 3] if block == "additive" else CURVE[(j + i) % 2]
        out.append((fam, 1 if (j + i) % 2 == 0 else -1))
    return out


def dataset_seed(block, fold, m, j):
    return int(np.random.SeedSequence([20261105, zlib.crc32(f"calib|{block}|f{fold}|m{m}|j{j}".encode())]).generate_state(1)[0])


def plan():
    out = []
    for block, S in BLOCKS.items():
        for fold in FOLDS:
            for m in MS:
                for j in range(S):
                    out.append({"block": block, "fold": fold, "m": m, "j": j, "arms": (["A15h2"] if block == "noadd" else list(ARMS)), "seed": dataset_seed(block, fold, m, j)})
    return out


def plan_counts():
    p = plan()
    return {"datasets": len(p), "fits": sum(len(x["arms"]) for x in p), "by_block": {b: sum(len(x["arms"]) for x in p if x["block"] == b) for b in BLOCKS}}


def edges_per_cell():
    """synthetic edges per (input, m, arm, truth family) of the additive block over all folds: rule section 2 requires >= 20"""
    n = {}
    for x in plan():
        if x["block"] != "additive":
            continue
        for i, (fam, _) in enumerate(truth_families("additive", x["j"])):
            for a in x["arms"]:
                n[(SPEC.stress_names[i], x["m"], a, fam)] = n.get((SPEC.stress_names[i], x["m"], a, fam), 0) + 1
    return n


# ------------------------------------------------------------------------------------------------ one dataset
def fold_design(fold, m, root=ROOT):
    """training cycling conditions (first m of the pinned nested order, identifiers only) and the 19 storage conditions of the S2 split"""
    sub = json.load(open(os.path.join(root, "runs", "prereg", "subsets.json"), encoding="utf8"))["folds"][str(fold)]
    cyc = sub["subsets"][str(m)]
    s2 = json.load(open(os.path.join(root, "runs", "prereg", "samsung_splits_v2.json"), encoding="utf8"))["S2"]["folds"]
    sto = sorted({c for f in s2.values() for c in f["test_conditions"]})
    return cyc, sto


def hull(cyc_keys):
    X_ = np.stack([subsets.parse_samsung_cond(c) for c in cyc_keys])
    X_[:, 0] += 273.15
    return X_.min(0), X_.max(0)


def build_dataset(spec_cell, cyc_keys, sto_keys, reps=2):
    """-> (SynthSet, truth list). Truth of the additive / curved block per the table; the non-additive block is the project's kind G2 on the same design."""
    design = synth.design_from_keys(cyc_keys, sto_keys, reps)
    seed = spec_cell["seed"]
    if spec_cell["block"] == "noadd":
        return synth.make_synthetic("G2", reps=reps, seed=seed % (2 ** 31), design=design), None
    lo, hi = hull(cyc_keys)
    tf = truth_families(spec_cell["block"], spec_cell["j"])
    truth = {i: (fam, sg, float(lo[i]), float(hi[i])) for i, (fam, sg) in enumerate(tf)}
    return synth.make_synthetic("GA", reps=reps, seed=seed % (2 ** 31), design=design, truth=truth), tf


def effect_error(sym_cyc, spec, s_train, i, truth_i, n=41):
    """centred RMS of the extracted effect of input i against the truth effect, over the input's hull (partial dependences), divided by the range of the truth effect"""
    fam, sg, lo, hi = truth_i
    _, pd = X._signs_and_pd(sym_cyc, spec, s_train, n)
    s = np.asarray(s_train, float)
    grid = np.linspace(s[:, i].min(), s[:, i].max(), n)
    raw = np.zeros((n, spec.d))
    raw[:, i] = spec.denorm(np.tile(grid[:, None], (1, spec.d)))[:, i]
    x = raw[:, i] + (273.15 if i == spec.t_index else 0.0)
    t = synth.truth_effect(fam, sg, x, lo, hi)
    a = pd[spec.stress_names[i]] - pd[spec.stress_names[i]].mean()
    b = t - t.mean()
    return float(np.sqrt(np.mean((a - b) ** 2)) / max(np.ptp(t), 1e-12))


def run_dataset(spec_cell, cyc_keys, sto_keys, steps_scale=1.0, reps=2):
    """fits every arm of the cell on the synthetic training cells and returns one record per (arm, input). Pipeline = arms.SymbolicArm (cap from the library file)."""
    S0, tf = build_dataset(spec_cell, cyc_keys, sto_keys, reps)
    train = list(S0.cells)
    lo, hi = hull(cyc_keys)
    records = []
    for key in spec_cell["arms"]:
        arm_id, over = ARMS[key]
        arm = A.make_arm(arm_id, SPEC, {**A.default_hp(arm_id), **over}, spec_cell["j"], {"backbone": "self_limiting", "steps_scale": steps_scale}).fit(train)
        law = X.law_record(key, spec_cell["fold"], spec_cell["j"], arm.report, SPEC, arm.model.law.cyc, arm.parent_cyc, arm.s_cyc_train)
        for i, name in enumerate(SPEC.stress_names):
            r = law["inputs"][name]
            rec = {"block": spec_cell["block"], "fold": spec_cell["fold"], "m": spec_cell["m"], "j": spec_cell["j"], "arm": key, "input": name, "chosen": r["family"], "sign": r["sign"],
                   "bic_margin": r["bic_margin"], "additive": r["additive"], "outer_families": law["outer_families"], "refit_diverged": bool(arm.refit_diverged)}
            if tf is not None:
                rec.update(truth=tf[i][0], truth_sign=tf[i][1] if tf[i][0] != "zero" else 0)
                if spec_cell["block"] == "curved":
                    rec["effect_error"] = effect_error(arm.model.law.cyc, SPEC, arm.s_cyc_train, i, (tf[i][0], tf[i][1], float(lo[i]), float(hi[i])))
            records.append(rec)
    return records


# ------------------------------------------------------------------------------------------------ guard, run, finalize
def rule_sha256():
    return hashlib.sha256(open(RULE_FILE, "rb").read()).hexdigest()


def require_run_conditions(root=ROOT):
    """A4: the calibration runs from the FROZEN commit only, before any outer score"""
    try:
        d = guard.verify_freeze(root)
    except guard.TestFoldAccessError as e:
        raise CalibrationGuardError(f"not the frozen commit / clean tree: {e}") from e
    sc = os.path.join(root, guard.SCORED_REL)
    if os.path.isfile(sc) and os.path.getsize(sc) > 0:
        raise CalibrationGuardError("an outer score already exists (runs/prereg/SCORED.jsonl): the calibration must be made and hashed before any outer score")
    return d


def run_cells(proc, nproc, out_dir, steps_scale=1.0, limit=None, log=print):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"records_p{proc}.jsonl")
    done = set()
    if os.path.exists(path):
        done = {(r["block"], r["fold"], r["m"], r["j"]) for r in (json.loads(l) for l in open(path, encoding="utf8"))}
    cells = [c for i, c in enumerate(plan()) if i % nproc == proc]
    n = 0
    for c in cells:
        if (c["block"], c["fold"], c["m"], c["j"]) in done:
            continue
        cyc, sto = fold_design(c["fold"], c["m"])
        t0 = time.time()
        recs = run_dataset(c, cyc, sto, steps_scale)
        with open(path, "a", encoding="utf8") as fh:
            for r in recs:
                fh.write(json.dumps(r) + "\n")
        log(f"{c['block']} f{c['fold']} m{c['m']} j{c['j']}: {len(recs)} edges in {time.time() - t0:.0f} s")
        n += 1
        if limit is not None and n >= limit:
            break


def finalize(out_dir, require_complete=True):
    """merge the per-process records, build the calibration tables, write calibration.json with its hash record (extraction_audit.write_calibration_record)"""
    recs = []
    for f in sorted(os.listdir(out_dir)):
        if f.startswith("records_p") and f.endswith(".jsonl"):
            recs += [json.loads(l) for l in open(os.path.join(out_dir, f), encoding="utf8")]
    have = {(r["block"], r["fold"], r["m"], r["j"]) for r in recs}
    want = {(c["block"], c["fold"], c["m"], c["j"]) for c in plan()}
    if require_complete and have != want:
        raise CalibrationGuardError(f"calibration incomplete: {len(want - have)} of {len(want)} datasets missing")
    add = [r for r in recs if r["block"] == "additive"]
    cells = X.calibration_tables(add)
    short = {k: v["n"] for k, v in cells.items() if min(v["n"].values()) < X.load_thresholds()["min_synthetic_edges_per_truth_family"]}
    curved = {}
    for r in recs:
        if r["block"] == "curved":
            c = curved.setdefault(f"{r['input']}|{r['m']}|{r['arm']}|{r['truth']}", {"n": 0, "chosen": {}, "effect_error": []})
            c["n"] += 1
            c["chosen"][r["chosen"]] = c["chosen"].get(r["chosen"], 0) + 1
            c["effect_error"].append(r["effect_error"])
    noadd = {}
    for r in recs:
        if r["block"] == "noadd":
            c = noadd.setdefault(f"{r['m']}", {"laws": 0, "outer_linear_or_zero": 0, "families": {}})
            if r["input"] == SPEC.stress_names[0]:
                c["laws"] += 1
                c["outer_linear_or_zero"] += int(all(f in ("linear", "zero") for f in r["outer_families"]))
            c["families"][r["chosen"]] = c["families"].get(r["chosen"], 0) + 1
    cal = {"cells": cells, "cells_below_minimum_n": short, "curved_report_only": curved, "non_additive_h2": noadd, "n_records": len(recs), "rule_sha256": rule_sha256(),
           "thresholds_sha256": X.thresholds_sha256(), "commit": guard._git(ROOT, "rev-parse", "HEAD"), "plan": plan_counts()}
    return X.write_calibration_record(out_dir, cal), cal


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--proc", type=int, default=0)
    ap.add_argument("--nproc", type=int, default=1)
    ap.add_argument("--finalize", action="store_true")
    ap.add_argument("--smoke", default=None, help="directory: tiny run of a few datasets for tests; marked SMOKE, never a calibration")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args(argv)
    if a.plan:
        print(json.dumps(plan_counts()), "min edges per cell:", min(edges_per_cell().values()))
        return
    if a.smoke:
        os.makedirs(a.smoke, exist_ok=True)
        open(os.path.join(a.smoke, "SMOKE"), "w").write("smoke run: not a calibration\n")
        run_cells(a.proc, a.nproc, a.smoke, steps_scale=0.05, limit=a.limit or 1)
        return
    d = require_run_conditions()
    if a.finalize:
        rec, _ = finalize(OUT_DIR)
        print(rec)
        return
    print("calibration from frozen commit", d["commit"])
    run_cells(a.proc, a.nproc, OUT_DIR, limit=a.limit)


if __name__ == "__main__":
    main()
