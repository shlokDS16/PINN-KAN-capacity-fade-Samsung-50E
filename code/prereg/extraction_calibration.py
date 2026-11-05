"""D022a: calibration of the extraction audit on whole synthetic datasets. Rule: debates/D022_datasets_kan/calibration_rule_v2.md (committed before this script).

    .venv/Scripts/python.exe -P code/prereg/extraction_calibration.py --plan
    .venv/Scripts/python.exe -P code/prereg/extraction_calibration.py --proc 0 --nproc 3 --thresholds-pin <sha256> --rule-pin <sha256>      # from the FROZEN commit only
    .venv/Scripts/python.exe -P code/prereg/extraction_calibration.py --finalize --thresholds-pin <sha256> --rule-pin <sha256>
    .venv/Scripts/python.exe -P code/prereg/extraction_calibration.py --rerun --thresholds-pin <sha256> --rule-pin <sha256> --scratch <dir>  # gate auditor: 3 hash-chosen datasets, bit-identical

Unit = one synthetic dataset (30 per arm) run through the real procedure (5 outer-fold designs at m = 32 x refit seeds 0-4 = 25 laws per arm), scored with the same label function as the real
data. Guard: `guard.verify_freeze` with untracked files under code/ included, and both pins (thresholds file, rule file) equal to the files in the tree. The mtime of anything is logged, not
checked. `--smoke` runs one (dataset, fold) with tiny settings into a directory marked SMOKE (tests only; never a calibration). This build did NOT run the calibration."""
import argparse
import hashlib
import itertools
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
from pinnkan.data import samsung_cond_key  # noqa: E402
from pinnkan.specs import SPECS  # noqa: E402

SPEC = SPECS["synthetic"]
RULE_FILE = os.path.join(ROOT, "debates", "D022_datasets_kan", "calibration_rule_v2.md")
OUT_DIR = os.path.join(ROOT, "runs", "extraction_calibration")
STRATA = ("zero", "linear", "log", "quadratic", "hinge")
PAIRS = list(itertools.combinations(range(5), 2))
FOLDS, SEEDS, ARM_IDS = tuple(range(5)), tuple(range(5)), ("A15", "G15")
THR = X.load_thresholds()
CAL = THR["calibration"]
D_TOTAL = CAL["D"]
M = 32


class CalibrationGuardError(RuntimeError):
    pass


# ------------------------------------------------------------------------------------------------ truth of a dataset (rule v2 section 2)
def streams(j):
    """amplitude, laboratory-offset, hyperparameter and noise streams of dataset j"""
    return np.random.SeedSequence([20261105, zlib.crc32(f"calib2|d{j}".encode())]).spawn(4)


def stratum(j, i):
    return STRATA[(j + i) % 5]


def stratum_sign(j, i):
    return 1 if (j + i) % 2 == 0 else -1


def interaction_pair(j):
    """the interacting pair of dataset j (j = 0, 3, ..., 27), else None"""
    return PAIRS[j // CAL["interaction_every"]] if j % CAL["interaction_every"] == 0 else None


def global_hull(root=ROOT):
    """fixed truth hull per input (T in kelvin): the union of the five folds' m = 32 training identifiers (identifiers only)"""
    sub = json.load(open(os.path.join(root, "runs", "prereg", "subsets.json"), encoding="utf8"))["folds"]
    keys = sorted({c for f in sub.values() for c in f["subsets"][str(M)]})
    X_ = np.stack([subsets.parse_samsung_cond(c) for c in keys])
    X_[:, 0] += 273.15
    return X_.min(0), X_.max(0)


def amplitudes(j):
    """-> (A_i for the five inputs, A_int or None), log-uniform on the amplitude range"""
    lo, hi = np.log(CAL["amplitude_range"][0]), np.log(CAL["amplitude_range"][1])
    r = np.random.default_rng(streams(j)[0])
    a = [float(np.exp(r.uniform(lo, hi))) for _ in range(5)]
    return a, (float(np.exp(r.uniform(lo, hi))) if interaction_pair(j) is not None else None)


def dataset_truth(j, hull=None):
    """-> {truth: synth truth dict, interaction: tuple|None, info: {input name: {stratum, sign, interacting, amp}}}"""
    lo, hi = hull if hull is not None else global_hull()
    amps, a_int = amplitudes(j)
    pair = interaction_pair(j)
    truth, info = {}, {}
    for i, name in enumerate(SPEC.stress_names):
        fam, sg = stratum(j, i), stratum_sign(j, i)
        truth[i] = (fam, sg, float(lo[i]), float(hi[i]), amps[i])
        info[name] = {"stratum": fam, "sign": synth.truth_sign(fam, sg), "interacting": bool(pair is not None and i in pair), "amp": amps[i]}
    inter = None if pair is None else (pair[0], pair[1], a_int, float(lo[pair[0]]), float(hi[pair[0]]), float(lo[pair[1]]), float(hi[pair[1]]))
    return {"truth": truth, "interaction": inter, "info": info}


def majority_labs(root=ROOT):
    """cycling condition identifier -> majority laboratory (most cells; ties: first in sorted order) from the Samsung cell table (identifiers only), and the sha256 of the map"""
    import pandas as pd
    df = pd.read_csv(os.path.join(root, "data", "processed", "samsung_cells.csv"))
    df = df[df["type"] == "z"]
    cnt = {}
    for _, r in df.iterrows():
        key = samsung_cond_key("cycling", float(r["T_C"]), float(r["SOC_max"]), float(r["DoD"]), float(r["C_ch"]), float(r["C_dch"]))
        cnt.setdefault(key, {}).setdefault(str(r["lab"]), 0)
        cnt[key][str(r["lab"])] += 1
    out = {k: sorted(v.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for k, v in cnt.items()}
    return out, hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest()


def lab_offsets(j, labs):
    """one N(0, sd^2) offset per laboratory (sorted names), shared by every fold of dataset j"""
    r = np.random.default_rng(streams(j)[1])
    names = sorted(set(labs))
    return {n: float(v) for n, v in zip(names, r.normal(0.0, CAL["laboratory_offset_sd"], size=len(names)))}


def draw_hp(j, fold, arm_id):
    """uniform draw from the tuned space of PREREG 7.1 (A15: h and A1's other five dimensions; G15: the A4 space) for (dataset, fold, arm)"""
    child = streams(j)[2].spawn(10)[2 * fold + (0 if arm_id == "A15" else 1)]
    r = np.random.default_rng(child)
    hp = {}
    for name, sp in A.ARMS[arm_id].space.items():
        if sp[0] != "cat":
            raise ValueError(f"non-categorical dimension {name} in {arm_id}")
        hp[name] = sp[1][int(r.integers(len(sp[1])))]
    return hp


def generator_seed(j, fold):
    return int(streams(j)[3].spawn(5)[fold].generate_state(1)[0]) % (2 ** 31)


# ------------------------------------------------------------------------------------------------ the plan
def plan():
    return [{"d": j, "fold": f} for j in range(D_TOTAL) for f in FOLDS]


def plan_counts():
    return {"datasets": D_TOTAL, "work_items": len(plan()), "fits": D_TOTAL * len(FOLDS) * len(SEEDS) * len(ARM_IDS), "laws_per_arm_per_dataset": len(FOLDS) * len(SEEDS),
            "interaction_datasets": sum(interaction_pair(j) is not None for j in range(D_TOTAL))}


def fold_design(fold, m=M, root=ROOT):
    """training cycling conditions (first m of the pinned nested order, identifiers only) and the 19 storage conditions of the S2 split"""
    sub = json.load(open(os.path.join(root, "runs", "prereg", "subsets.json"), encoding="utf8"))["folds"][str(fold)]
    cyc = sub["subsets"][str(m)]
    s2 = json.load(open(os.path.join(root, "runs", "prereg", "samsung_splits_v2.json"), encoding="utf8"))["S2"]["folds"]
    sto = sorted({c for f in s2.values() for c in f["test_conditions"]})
    return cyc, sto


# ------------------------------------------------------------------------------------------------ one (dataset, fold)
def build_set(j, fold, tr, labmap, offs, cyc, sto, reps=2):
    design = synth.design_from_keys(cyc, sto, reps)
    cond_off = {ci: offs[labmap[k]] for ci, k in enumerate(cyc)}
    return synth.make_synthetic("GA", reps=reps, seed=generator_seed(j, fold), design=design, truth=tr["truth"], interaction=tr["interaction"], cond_offsets=cond_off)


def run_item(j, fold, steps_scale=1.0, seeds=SEEDS, skip=frozenset(), reps=2, ctx=None, root=ROOT, arm_ids=ARM_IDS, labmap=None):
    """fits every arm and seed of one (dataset, fold) and returns one record per (arm, seed). skip = set of (d, arm, fold, seed) already on disk."""
    tr = dataset_truth(j, global_hull(root))
    labmap = majority_labs(root)[0] if labmap is None else labmap
    cyc, sto = fold_design(fold, M, root)
    missing = [k for k in cyc if k not in labmap]
    if missing:
        raise CalibrationGuardError(f"no laboratory for {len(missing)} training condition(s), e.g. {missing[0]}: the Samsung cell table is incomplete (run the calibration after the cell download is complete)")
    offs = lab_offsets(j, [labmap[k] for k in cyc])
    S0 = build_set(j, fold, tr, labmap, offs, cyc, sto, reps)
    train = list(S0.cells)
    recs = []
    for arm_id in arm_ids:
        hp = draw_hp(j, fold, arm_id)
        for sd in seeds:
            if (j, arm_id, fold, sd) in skip:
                continue
            t0 = time.process_time()
            arm = A.make_arm(arm_id, SPEC, hp, sd, {"backbone": "self_limiting", "steps_scale": steps_scale, **(ctx or {})}).fit(train)
            law = X.law_record(X.arm_key(arm_id, hp), fold, sd, arm.report, SPEC, arm.model.law.cyc, arm.parent_cyc, arm.s_cyc_train, THR)
            recs.append({"d": j, "arm": arm_id, "fold": fold, "seed": sd, "hp": hp, "law": law, "cpu_s": time.process_time() - t0, "refit_diverged": bool(arm.refit_diverged)})
    return recs


# ------------------------------------------------------------------------------------------------ records on disk
def read_records(out_dir):
    """-> {(d, arm, fold, seed): record}; the first record of a key wins (de-duplication); a torn LAST line of a file is ignored, any other unreadable line is an error"""
    out = {}
    for f in sorted(os.listdir(out_dir)) if os.path.isdir(out_dir) else []:
        if not (f.startswith("records_p") and f.endswith(".jsonl")):
            continue
        lines = open(os.path.join(out_dir, f), encoding="utf8").read().split("\n")
        if lines and lines[-1] == "":
            lines = lines[:-1]
        for n, line in enumerate(lines):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                if n == len(lines) - 1:
                    continue
                raise CalibrationGuardError(f"{f}: unreadable line {n + 1} (not the last line)")
            out.setdefault((r["d"], r["arm"], r["fold"], r["seed"]), r)
    return out


def cpu_seconds(recs):
    return float(sum(r.get("cpu_s", 0.0) for r in recs.values()))


def run_cells(proc, nproc, out_dir, steps_scale=1.0, limit=None, seeds=SEEDS, log=print):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"records_p{proc}.jsonl")
    n = 0
    for idx, it in enumerate(plan()):
        if idx % nproc != proc:
            continue
        have = read_records(out_dir)
        if cpu_seconds(have) >= CAL["cpu_cap_hours"] * 3600.0:
            log(f"CPU cap of {CAL['cpu_cap_hours']} h reached: stopping")
            break
        if all((it["d"], a, it["fold"], s) in have for a in ARM_IDS for s in seeds):
            continue
        t0 = time.time()
        recs = run_item(it["d"], it["fold"], steps_scale, seeds, skip=frozenset(have))
        with open(path, "a", encoding="utf8") as fh:
            for r in recs:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
            fh.flush()
        log(f"d{it['d']} f{it['fold']}: {len(recs)} fits in {time.time() - t0:.0f} s")
        n += 1
        if limit is not None and n >= limit:
            break


# ------------------------------------------------------------------------------------------------ scoring and the verdict
def complete_datasets(recs, n_laws=None):
    """dataset ids with the full set of (arm, fold, seed) keys"""
    want = {(a, f, s) for a in ARM_IDS for f in FOLDS for s in SEEDS} if n_laws is None else n_laws
    have = {}
    for (d, a, f, s) in recs:
        have.setdefault(d, set()).add((a, f, s))
    return sorted(d for d, ks in have.items() if want <= ks)


def score_all(recs, ds, hull=None):
    """per complete dataset and arm: labels, baseline, scoring against the truth -> list of result dicts"""
    out = []
    for j in ds:
        info = dataset_truth(j, hull)["info"]
        for arm_id in ARM_IDS:
            laws = [recs[(j, arm_id, f, s)]["law"] for f in FOLDS for s in SEEDS]
            lab = X.label_law(laws, THR, calibrated=True)
            base = X.baseline_labels(laws, THR)
            sc, scb = X.score_dataset(lab, info), X.score_dataset(base, info)
            out.append({"d": j, "arm": arm_id, "E": sc["E"], "false": sc["false"], "E_baseline": scb["E"], "false_baseline": scb["false"], "events": X.recall_events(lab, info, THR),
                        "events_baseline": X.recall_events(base, info, THR), "labels": {n: {k: l[k] for k in ("label", "form", "sign", "tie_share", "n_not_retained")} for n, l in lab.items()},
                        "baseline": base, "truth": info})
    return out


def descriptive_tables(results):
    """per arm: confusion rows per (input, stratum) with exact intervals on the share of datasets with a false statement for that input; the not-retained share by amplitude band for
    non-zero, non-interacting truths; the mean tie share. Nothing here licenses anything."""
    bands = ("<0.1", "0.1-0.25", ">0.25")
    out = {}
    for arm_id in ARM_IDS:
        rows = [r for r in results if r["arm"] == arm_id]
        conf, ties, nr = {}, [], {b: [0, 0] for b in bands}
        for r in rows:
            for n, t in r["truth"].items():
                lab = r["labels"][n]
                c = conf.setdefault(f"{n}|{t['stratum']}", {"n": 0, "labels": {}, "false_statement": 0, "false_baseline": 0})
                c["n"] += 1
                key = lab["label"] + (f":{lab['form']}" if lab["form"] else "")
                c["labels"][key] = c["labels"].get(key, 0) + 1
                c["false_statement"] += int(any(f[0] == n for f in r["false"]))
                c["false_baseline"] += int(any(f[0] == n for f in r["false_baseline"]))
                ties.append(lab["tie_share"])
                if t["stratum"] != "zero" and not t["interacting"]:
                    b = "<0.1" if t["amp"] < 0.1 else ("0.1-0.25" if t["amp"] < 0.25 else ">0.25")
                    nr[b][0] += int(lab["label"] == "not_retained")
                    nr[b][1] += 1
        for c in conf.values():
            c["false_statement_ci"] = list(X.clopper_pearson(c["false_statement"], c["n"]))
        out[arm_id] = {"confusion": conf, "mean_tie_share": float(np.mean(ties)) if ties else None,
                       "false_zero_by_amplitude": {b: {"not_retained": v[0], "n": v[1], "ci": list(X.clopper_pearson(v[0], v[1]))} for b, v in nr.items()}}
    return out


def finalize(out_dir, frozen_commit, root=ROOT, lab_hash=None):
    """merge the records, score the complete datasets, compute C1-C3, write calibration.json (the hash of the file is the pin of the statistics step)"""
    recs = read_records(out_dir)
    ds = complete_datasets(recs)
    hull = global_hull(root)
    results = score_all(recs, ds, hull)
    per_arm = {a: [r for r in results if r["arm"] == a] for a in ARM_IDS}
    verdict = X.verdict(per_arm, THR) if ds else {"void": True, "reason": "no complete dataset", "contribution": False}
    cal = {"commit": frozen_commit, "rule_sha256": X.sha256_file(RULE_FILE), "thresholds_sha256": X.thresholds_sha256(), "lab_map_sha256": lab_hash if lab_hash is not None else majority_labs(root)[1], "D_completed": len(ds),
           "complete_datasets": ds, "n_records": len(recs), "cpu_seconds": cpu_seconds(recs), "written_unix": time.time(), "plan": plan_counts(), "verdict": verdict,
           "descriptive": descriptive_tables(results) if results else {}, "datasets": results}
    p = os.path.join(out_dir, X.CALIBRATION_FILE)
    with open(p, "w", encoding="utf8") as fh:
        json.dump(cal, fh, indent=1, sort_keys=True)
    return {"file": p, "sha256": X.sha256_file(p), "verdict": verdict}, cal


# ------------------------------------------------------------------------------------------------ guard, re-run check
def require_run_conditions(root=ROOT, thresholds_pin=None, rule_pin=None):
    """the calibration runs from the FROZEN commit only: verify_freeze with untracked files under code/ included, and both pins equal to the files in the tree. No other order is enforced."""
    if not thresholds_pin or not rule_pin:
        raise CalibrationGuardError("both pins (--thresholds-pin, --rule-pin) are mandatory")
    try:
        d = guard.verify_freeze(root, untracked_under=("code",))
    except guard.TestFoldAccessError as e:
        raise CalibrationGuardError(f"not the frozen commit / clean tree (untracked files under code/ included): {e}") from e
    if thresholds_pin != X.sha256_file(os.path.join(root, "code", "pinnkan", "extraction_audit.json")):
        raise CalibrationGuardError("thresholds pin does not match extraction_audit.json in this tree")
    if rule_pin != X.sha256_file(os.path.join(root, "debates", "D022_datasets_kan", "calibration_rule_v2.md")):
        raise CalibrationGuardError("rule pin does not match calibration_rule_v2.md in this tree")
    return d


def rerun_choice(cal_sha256_hex, complete, k=None):
    """the datasets of the bit-identical re-run: bytes of sha256(calibration.json) in order, index = byte mod len(complete), repeats skipped, until k are chosen"""
    k = CAL["rerun_datasets"] if k is None else k
    b = bytes.fromhex(cal_sha256_hex)
    chosen = []
    for byte in b:
        d = complete[byte % len(complete)]
        if d not in chosen:
            chosen.append(d)
        if len(chosen) == k:
            return chosen
    raise CalibrationGuardError("could not choose the re-run datasets from the hash bytes")


def _same(a, b):
    drop = lambda r: {k: v for k, v in r.items() if k != "cpu_s"}               # timing cannot be bit-identical
    return json.dumps(drop(a), sort_keys=True) == json.dumps(drop(b), sort_keys=True)


def rerun_check(out_dir, scratch, steps_scale=1.0, folds=FOLDS, seeds=SEEDS, datasets=None):
    """re-run the hash-chosen datasets into `scratch` and compare with the stored records (cpu_s excluded). -> {datasets, identical, mismatches}"""
    stored = read_records(out_dir)
    cal_hash = X.sha256_file(os.path.join(out_dir, X.CALIBRATION_FILE))
    ds = datasets if datasets is not None else rerun_choice(cal_hash, complete_datasets(stored))
    mism = []
    for j in ds:
        for f in folds:
            for r in run_item(j, f, steps_scale, seeds):
                k = (r["d"], r["arm"], r["fold"], r["seed"])
                if k not in stored or not _same(stored[k], r):
                    mism.append(list(k))
    os.makedirs(scratch, exist_ok=True)
    out = {"datasets": ds, "identical": not mism, "mismatches": mism, "calibration_sha256": cal_hash}
    json.dump(out, open(os.path.join(scratch, "rerun_check.json"), "w"), indent=1)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--proc", type=int, default=0)
    ap.add_argument("--nproc", type=int, default=1)
    ap.add_argument("--finalize", action="store_true")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--scratch", default=None)
    ap.add_argument("--thresholds-pin", default=None)
    ap.add_argument("--rule-pin", default=None)
    ap.add_argument("--smoke", default=None, help="directory: tiny run of one (dataset, fold) for tests; marked SMOKE, never a calibration")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args(argv)
    if a.plan:
        print(json.dumps(plan_counts()))
        return
    if a.smoke:
        os.makedirs(a.smoke, exist_ok=True)
        open(os.path.join(a.smoke, "SMOKE"), "w").write("smoke run: not a calibration\n")
        run_cells(a.proc, a.nproc, a.smoke, steps_scale=0.05, limit=a.limit or 1, seeds=(0,))
        return
    d = require_run_conditions(ROOT, a.thresholds_pin, a.rule_pin)
    if a.finalize:
        rec, _ = finalize(OUT_DIR, d["commit"])
        print(rec)
        return
    if a.rerun:
        print(rerun_check(OUT_DIR, a.scratch or os.path.join(OUT_DIR, "rerun")))
        return
    print("calibration from frozen commit", d["commit"])
    run_cells(a.proc, a.nproc, OUT_DIR, limit=a.limit)


if __name__ == "__main__":
    main()
