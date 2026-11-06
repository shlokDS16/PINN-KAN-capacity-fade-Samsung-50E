"""Generates every pre-registered real-data run configuration (PREREG_v4 sections 7, 9.8, 9.9, 15, 17.2 C14, 18 steps 2 and 2b) and the five item (f) configs (D026), reproducibly.

    .venv/Scripts/python.exe -P code/prereg/make_confirmatory_configs.py            # writes runs/prereg/confirmatory_configs/** (+ MANIFEST.json) and runs/item_f/configs/*.json
    .venv/Scripts/python.exe -P code/prereg/make_confirmatory_configs.py --check    # exits 1 if a file on disk differs from what this script produces

The config hash of every confirmatory run on real data must be in FROZEN `config_sha256s` (guard.check_config_frozen), so all groups below are generated before the freeze.

GROUPS (directory under runs/prereg/confirmatory_configs/; MANIFEST.json lists every file with its group and canonical hash)
  primary       (root)  one run = one outer fold at one training-subset size m, all arms of that cell (D* and AG are selected from the inner-CV scores of the candidates of the same (fold, m), 7.1):
                  Test B grid  folds 0-4 x m in {8, 16, 32}, k = "grid" (cells k in {0, 2, "full"}): 15. Arms by m (7.1): every m: A1 A2 A4 A9 A10 A10P A11 A12 A12R R1 R2; m = 8 adds A13 (g1) and
                  A15 G15 (g1, descriptive); m = 32 adds A5 (m = 32 only), A13 (g4, descriptive) and A15 G15 (g4, confirmatory).
                  Test C fold 0 (full training, m not set): A1 A9 A10 A10P A11 A12.   S2 folds 0-4: A1 A9 A10 A10P.   NC-2 Test B folds 0-4 at m = 32, permute_stress: A1.
  rows          the four automatic-downgrade rows (9.8 rule 2) that need a re-run, cells g1 = (m 8, k 2) and g4 = (m 32, k full) only, k named explicitly:
                  (ii) lab-and-stage indicator, Test B folds 0-4 at g1 and g4, arms of every gated and secondary contrast at the cell (g1: A1 A2 A9 A10 A10P A11 A12 A13; g4: A1 A2 A9 A10 A10P A11 A12
                       A15 G15; stats_rows.row_tiers reads exactly these), and Test C (the Test C abstract rule 9.8 rule 3);
                  (iii) retain-every-check-up (retain_all), the same arms and cells as (ii);
                  (iv) random subset at g1 only: 3 seeded random nested subsets (subset_draw 0-2) in place of max-min, A1 and the D* candidates (A9 A11 A12), 5 folds.
  sensitivity   9.9 rows with a re-run (reported, no consequence) at g1 and g4, 5 folds. The arm list of these rows is not fixed by the PREREG: A1 A9 A11 A12 A10 A10P (P1, P2, D*, Q-A10) is an
                assumption of this script, except where the row names its arms. (i): include_at, include_storage_0406, min_fc_points 3, oracle_throughput, backbone self_limiting,
                score_blinded_cells (all at g1 and g4), windows k_full - 1 = 3 and k_full + 2 = 6 (g4 only); (k) clip 10 / 50 and warm-up 0.2 / 0.6 for P2 (arms A1 A9; warm-up acts on A1 only);
                (l) delta scope total (A1); (m) A2-only tournament sensitivity Y0 {0.5, 2}, gamma {0.15, 0.6}, TAU {0.075, 0.3}, one change at a time (A2).
  exploratory   Test A folds 0-2 (A1 A2 A9) and S3 (A1 A9 A10 A10P; the PREREG names no arms for S3, the S2 arms are assumed).
  replication   optional ISU descriptive replication (3.4 (ii)): Test B folds 0-4 at the scarce analogue (m 8, W = 2 weeks) and the g4 analogue (m 32, W = full = 4 weeks), A1 A9 A11 A12 A10.
Not generated (see runs/prereg/CODER_BATCH_REPORT.md, "needs a strike decision"): rows the code cannot run as written, SNL, A14.

Every Samsung config: dataset samsung, throughput zyk (FB-5 met: analytic throughput rejected, ZYK-logged throughput applies to every cycling cell), mode confirmatory, steps_scale 1, no overwrite,
window {k_cycling 4, k_storage 2} (FB-6), n_trials 20 (FB-8 may change it: edit N_TRIALS and regenerate), backbone tournament (7), inversion_config_sha256 (D023), and for A15 / G15
`extraction_audit_sha256` and `calibration_rule_sha256`. The five item (f) configs are the g1 config (m = 8, k grid) of the same fold with only run_id, mode = inner, arms = A1 A9 A11 A12,
diagnostics = false and refit_timing = false changed (D026 02_judge.md). Seeds, the MC seed root and the sampler seeds are fixed in code. No data is read here."""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))

from pinnkan import extraction_audit, guard, inversion  # noqa: E402
from pinnkan.run import DEFAULTS  # noqa: E402

CONF_DIR = os.path.join(ROOT, "runs", "prereg", "confirmatory_configs")
ITEM_F_DIR = os.path.join(ROOT, "runs", "item_f", "configs")
RULE_FILE = os.path.join(ROOT, "debates", "D022_datasets_kan", "calibration_rule_v2.md")
WINDOW = {"k_cycling": 4, "k_storage": 2}                  # FB-6 counts; every Samsung grid config carries them
N_TRIALS = 20                                              # FB-8 timing run (runs/freeze_shakedown/RESULT.md): 20 unless the freeze-commit timing run changes it
BACKBONE = "tournament"                                    # PREREG_v4 7: the state factor is chosen once per (outer fold, m)
THROUGHPUT = "zyk"                                         # FB-5 met: ZYK-logged throughput for every cycling cell
COMMON = ["A1", "A2", "A4", "A9", "A10", "A10P", "A11", "A12", "A12R", "R1", "R2"]
ARMS_BY_M = {8: COMMON + ["A13", "A15", "G15"], 16: list(COMMON), 32: COMMON + ["A5", "A13", "A15", "G15"]}
ITEM_F_ARMS = ["A1", "A9", "A11", "A12"]
ITEM_F_DIFFERENCES = {"run_id", "mode", "arms", "diagnostics", "refit_timing"}
CELLS = {"g1": {"m": 8, "k": [2]}, "g4": {"m": 32, "k": ["full"]}}
ROW_ARMS = {"g1": ["A1", "A2", "A9", "A10", "A10P", "A11", "A12", "A13"], "g4": ["A1", "A2", "A9", "A10", "A10P", "A11", "A12", "A15", "G15"]}
SENS_ARMS = ["A1", "A9", "A11", "A12", "A10", "A10P"]
RANDSUB_ARMS = ["A1", "A9", "A11", "A12"]
GROUP_DIRS = {"primary": "", "rows": "rows", "sensitivity": "sensitivity", "exploratory": "exploratory", "replication": "replication"}


def _arms(arms):
    return sorted(arms, key=lambda a: (a[0], int("".join(ch for ch in a if ch.isdigit()) or 0), a))      # A..., G15, R1, R2


def make_config(run_id, test, fold, arms, m=None, k=None, **extra):
    c = {"run_id": run_id, "dataset": "samsung", "test": test, "fold": int(fold), "mode": "confirmatory"}
    if m is not None:
        c.update(m=int(m), subset="maxmin")
    if k is not None:
        c["k"] = k
    c.update(arms=_arms(arms), window=dict(WINDOW), steps_scale=1.0, n_trials=N_TRIALS, backbone=BACKBONE, throughput=THROUGHPUT, inversion_config_sha256=inversion.config_sha256())
    if {"A15", "G15"} & set(arms):
        c["extraction_audit_sha256"] = extraction_audit.thresholds_sha256()
        c["calibration_rule_sha256"] = extraction_audit.sha256_file(RULE_FILE)
    c.update(extra)
    return c


def cell_config(run_id, fold, arms, cell, **extra):
    """a Test B config for one grid cell only (g1 or g4): m and the named k"""
    return make_config(run_id, "B", fold, arms, m=CELLS[cell]["m"], k=list(CELLS[cell]["k"]), **extra)


def primary_configs():
    out = {}
    for f in range(5):
        for m in (8, 16, 32):
            rid = f"conf_samsung_B_f{f}_m{m}"
            out[rid + ".json"] = make_config(rid, "B", f, ARMS_BY_M[m], m=m, k="grid")
    out["conf_samsung_C_f0.json"] = make_config("conf_samsung_C_f0", "C", 0, ["A1", "A9", "A10", "A10P", "A11", "A12"])
    for f in range(5):
        rid = f"conf_samsung_S2_f{f}"
        out[rid + ".json"] = make_config(rid, "S2", f, ["A1", "A9", "A10", "A10P"])
    for f in range(5):
        rid = f"conf_samsung_B_f{f}_m32_nc2"
        out[rid + ".json"] = make_config(rid, "B", f, ["A1"], m=32, permute_stress=True)
    return out


def row_configs():
    out = {}
    for f in range(5):
        for cell in ("g1", "g4"):
            for tag, key in (("labind", "lab_indicator"), ("retain", "retain_all")):
                rid = f"row_{tag}_B_f{f}_{cell}"
                out[rid + ".json"] = cell_config(rid, f, ROW_ARMS[cell], cell, **{key: True})
        for d in range(3):
            rid = f"row_randsub_B_f{f}_d{d}_g1"
            out[rid + ".json"] = cell_config(rid, f, RANDSUB_ARMS, "g1", subset="random", subset_draw=d)
    out["row_labind_C_f0.json"] = make_config("row_labind_C_f0", "C", 0, ["A1", "A9", "A10", "A10P", "A11", "A12"], lab_indicator=True)
    return out


def sensitivity_configs():
    out = {}
    variants = [("at", {"include_at": True}), ("st0406", {"include_storage_0406": True}), ("fc3", {"min_fc_points": 3}), ("oracle", {"oracle_throughput": True}),
                ("selflim", {"backbone": "self_limiting"}), ("blinded", {"score_blinded_cells": True})]
    for f in range(5):
        for cell in ("g1", "g4"):
            for tag, kw in variants:
                rid = f"sens_{tag}_B_f{f}_{cell}"
                out[rid + ".json"] = cell_config(rid, f, SENS_ARMS, cell, **kw)
            for tag, pinn in (("clip10", {"clip": 10}), ("clip50", {"clip": 50}), ("warm02", {"warmup": 0.2}), ("warm06", {"warmup": 0.6})):
                rid = f"sens_{tag}_B_f{f}_{cell}"
                out[rid + ".json"] = cell_config(rid, f, ["A1", "A9"], cell, pinn=dict(pinn))
            rid = f"sens_deltatotal_B_f{f}_{cell}"
            out[rid + ".json"] = cell_config(rid, f, ["A1"], cell, law_overrides={"delta_scope": "total"})
            for tag, lo in (("Y05", {"Y0": 0.5}), ("Y2", {"Y0": 2.0}), ("g015", {"gamma": 0.15}), ("g06", {"gamma": 0.6}), ("tau0075", {"tau": 0.075}), ("tau03", {"tau": 0.3})):
                rid = f"sens_a2_{tag}_B_f{f}_{cell}"
                out[rid + ".json"] = cell_config(rid, f, ["A2"], cell, law_overrides=dict(lo))
        for tag, kc in (("kfull_m1", WINDOW["k_cycling"] - 1), ("kfull_p2", WINDOW["k_cycling"] + 2)):
            rid = f"sens_{tag}_B_f{f}_g4"
            c = cell_config(rid, f, SENS_ARMS, "g4")
            c["window"] = {"k_cycling": kc, "k_storage": WINDOW["k_storage"]}
            out[rid + ".json"] = c
    return out


def exploratory_configs():
    out = {}
    for f in range(3):
        rid = f"expl_samsung_A_f{f}"
        out[rid + ".json"] = make_config(rid, "A", f, ["A1", "A2", "A9"])
    out["expl_samsung_S3_f0.json"] = make_config("expl_samsung_S3_f0", "S3", 0, ["A1", "A9", "A10", "A10P"])
    return out


def replication_configs():
    """optional ISU replication (3.4 (ii)): scarce analogue (m 8, W = 2 weeks) and the g4 analogue (m 32, W = full = 4 weeks); no window dict (time window), arms A1 A9 A11 A12 A10"""
    out = {}
    for f in range(5):
        for cell in ("g1", "g4"):
            rid = f"repl_isu_B_f{f}_{cell}"
            out[rid + ".json"] = {"run_id": rid, "dataset": "isu", "test": "B", "fold": f, "mode": "confirmatory", "m": CELLS[cell]["m"], "subset": "maxmin", "k": list(CELLS[cell]["k"]),
                                  "arms": _arms(["A1", "A9", "A11", "A12", "A10"]), "steps_scale": 1.0, "n_trials": N_TRIALS, "backbone": BACKBONE, "inversion_config_sha256": inversion.config_sha256()}
    return out


def groups():
    return {"primary": primary_configs(), "rows": row_configs(), "sensitivity": sensitivity_configs(), "exploratory": exploratory_configs(), "replication": replication_configs()}


def confirmatory_configs():
    """every non-item-(f) config: {relative path (forward slashes): config}"""
    out = {}
    for g, d in groups().items():
        for n, c in d.items():
            out[(GROUP_DIRS[g] + "/" + n).lstrip("/")] = c
    return out


def item_f_configs(conf=None):
    """-> {file name: config dict}: the g1 config (Test B, m = 8, k grid) of each fold with only the D026 differences"""
    conf = conf or confirmatory_configs()
    out = {}
    for f in range(5):
        c = dict(conf[f"conf_samsung_B_f{f}_m8.json"])
        rid = f"item_f_samsung_B_g1_f{f}"
        c.update(run_id=rid, mode="inner", arms=list(ITEM_F_ARMS), diagnostics=False, refit_timing=False)
        out[rid + ".json"] = c
    return out


def canonical_hash(cfg):
    return guard.canonical_config_hash({**DEFAULTS, **cfg})


def render(cfg):
    return json.dumps(cfg, indent=1) + "\n"


def manifest(grp, item_f):
    rows = []
    for g, d in grp.items():
        for name, c in d.items():
            rel = (GROUP_DIRS[g] + "/" + name).lstrip("/")
            rows.append(_row(g, rel, c))
    for name, c in item_f.items():
        rows.append(_row("item_f", name, c))
    return {"note": "generated by code/prereg/make_confirmatory_configs.py (reproducible); config_sha256 = guard.canonical_config_hash(DEFAULTS merged with the file); FROZEN pins the groups primary, rows, "
                    "sensitivity, exploratory and replication in config_sha256s (path relative to runs/prereg/confirmatory_configs/) and group item_f in item_f_config_sha256s (path relative to runs/item_f/configs/)",
            "n_trials": N_TRIALS, "window": WINDOW, "backbone": BACKBONE, "throughput": THROUGHPUT, "counts": {g: sum(1 for r in rows if r["group"] == g) for g in list(grp) + ["item_f"]}, "files": rows}


def _row(group, rel, c):
    return {"group": group, "file": rel, "run_id": c["run_id"], "dataset": c["dataset"], "test": c["test"], "fold": c["fold"], "m": c.get("m"), "k": c.get("k"), "arms": c["arms"],
            "config_sha256": canonical_hash(c), "file_sha256": hashlib.sha256(render(c).encode("utf8")).hexdigest()}


def planned():
    """-> {absolute path: text} of every file this script owns"""
    grp = groups()
    conf = {}
    for g, d in grp.items():
        for n, c in d.items():
            conf[(GROUP_DIRS[g] + "/" + n).lstrip("/")] = c
    item_f = item_f_configs(conf)
    files = {os.path.join(CONF_DIR, *rel.split("/")): render(c) for rel, c in conf.items()}
    files[os.path.join(CONF_DIR, "MANIFEST.json")] = json.dumps(manifest(grp, item_f), indent=1) + "\n"
    files.update({os.path.join(ITEM_F_DIR, n): render(c) for n, c in item_f.items()})
    return files


def _existing():
    out = []
    for base in (CONF_DIR, ITEM_F_DIR):
        for dp, _, fs in os.walk(base):
            out += [os.path.join(dp, f) for f in fs if f.endswith(".json")]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="do not write; exit 1 if a file differs")
    a = ap.parse_args(argv)
    files = planned()
    if a.check:
        bad = [p for p, t in files.items() if not os.path.isfile(p) or open(p, encoding="utf8", newline="").read() != t]
        stale = [p for p in _existing() if p not in files]
        for p in bad + stale:
            print("DIFFERS" if p in bad else "STALE", p)
        return 1 if (bad or stale) else 0
    for p in _existing():
        if p not in files:
            os.remove(p)                                                    # a file this script no longer owns
    for p, t in files.items():
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf8", newline="") as fh:
            fh.write(t)
    print(f"wrote {len(files)} files: " + ", ".join(f"{g} {len(d)}" for g, d in groups().items()) + ", item_f 5, MANIFEST.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
