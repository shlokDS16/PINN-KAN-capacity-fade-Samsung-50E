"""Generates the confirmatory configuration set (PREREG_v4 section 7, 15, 17.2 C14, 18 steps 2 and 2b) and the five item (f) configs (D026), reproducibly.

    .venv/Scripts/python.exe -P code/prereg/make_confirmatory_configs.py            # writes runs/prereg/confirmatory_configs/*.json (+ MANIFEST.json) and runs/item_f/configs/*.json
    .venv/Scripts/python.exe -P code/prereg/make_confirmatory_configs.py --check    # exits 1 if a file on disk differs from what this script produces

One config per outer fold and arm group of the Design R2 grid on Samsung (each run = one outer fold at one training-subset size m, all arms of that cell; the arms of a cell are in one run because D* and AG
are selected from the inner-CV scores of the candidates of the same (fold, m), 7.1):

  Test B grid   folds 0-4 x m in {8, 16, 32}: 15 configs. Arms by m (7.1): every m: A1 A2 A4 A9 A10 A10P A11 A12 A12R R1 R2; m = 8 adds A13 (g1, Q-T) and A15 G15 (g1, descriptive);
                m = 32 adds A5 (interaction GAM, m = 32 only), A13 (g4, descriptive) and A15 G15 (g4, confirmatory). D* = best of A9 A11 A12, AG = best of A4 A5 (A4 below m = 32).
  Test C        fold 0 (13 held-out 35 C conditions), full training (m not set): A1 A9 A10 A10P A11 A12 (A1 against A9, A10 both forms and D*).
  S2            folds 0-4 (storage): A1 A9 A10 A10P.
  NC-2          Test B folds 0-4 at m = 32 (g4), permute_stress: A1 only (A9 is optional in 7.1 and not run).
Not in this set (not pre-registered as one run per fold): the four downgrade-row re-runs (9.8 rule 2), the other sensitivity rows, Test A, S3, ISU/SNL replication; the config hash of every confirmatory run on
real data must be in FROZEN `config_sha256s` (guard.check_config_frozen), so any such re-run needs its config generated and pinned before the freeze.

Every config: dataset samsung, mode confirmatory, steps_scale 1, no overwrite, auto_budget off, window {k_cycling 4, k_storage 2} (FB-6; freeze_shakedown/RESULT.md), n_trials 20 (FB-8 may change it:
change N below and regenerate), backbone tournament (7: one tournament per (outer fold, m)), inversion_config_sha256 (D023), and for A15 / G15 `extraction_audit_sha256` and `calibration_rule_sha256` (run.py).
The five item (f) configs are the g1 config (m = 8) of the same fold with only run_id, mode = inner, arms = A1 A9 A11 A12, diagnostics = false and refit_timing = false changed (D026 02_judge.md).
Seeds, the MC seed root and the sampler seeds are fixed in code (`run.py`, `negcontrol.MC_SEED_ROOT`). No data is read here."""
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
COMMON = ["A1", "A2", "A4", "A9", "A10", "A10P", "A11", "A12", "A12R", "R1", "R2"]
ARMS_BY_M = {8: COMMON + ["A13", "A15", "G15"], 16: list(COMMON), 32: COMMON + ["A5", "A13", "A15", "G15"]}
ITEM_F_ARMS = ["A1", "A9", "A11", "A12"]
ITEM_F_DIFFERENCES = {"run_id", "mode", "arms", "diagnostics", "refit_timing"}


def _arms(arms):
    return sorted(arms, key=lambda a: (a[0], int("".join(ch for ch in a if ch.isdigit()) or 0), a))      # A..., G15, R1, R2


def make_config(run_id, test, fold, arms, m=None, **extra):
    c = {"run_id": run_id, "dataset": "samsung", "test": test, "fold": int(fold), "mode": "confirmatory"}
    if m is not None:
        c.update(m=int(m), subset="maxmin")
    c.update(arms=_arms(arms), window=dict(WINDOW), steps_scale=1.0, n_trials=N_TRIALS, backbone=BACKBONE, inversion_config_sha256=inversion.config_sha256())
    if {"A15", "G15"} & set(arms):
        c["extraction_audit_sha256"] = extraction_audit.thresholds_sha256()
        c["calibration_rule_sha256"] = extraction_audit.sha256_file(RULE_FILE)
    c.update(extra)
    return c


def confirmatory_configs():
    """-> {file name: config dict}: Test B grid, Test C, S2, NC-2"""
    out = {}
    for f in range(5):
        for m in (8, 16, 32):
            rid = f"conf_samsung_B_f{f}_m{m}"
            out[rid + ".json"] = make_config(rid, "B", f, ARMS_BY_M[m], m=m)
    out["conf_samsung_C_f0.json"] = make_config("conf_samsung_C_f0", "C", 0, ["A1", "A9", "A10", "A10P", "A11", "A12"])
    for f in range(5):
        rid = f"conf_samsung_S2_f{f}"
        out[rid + ".json"] = make_config(rid, "S2", f, ["A1", "A9", "A10", "A10P"])
    for f in range(5):
        rid = f"conf_samsung_B_f{f}_m32_nc2"
        out[rid + ".json"] = make_config(rid, "B", f, ["A1"], m=32, permute_stress=True)
    return out


def item_f_configs(conf=None):
    """-> {file name: config dict}: the g1 config (Test B, m = 8) of each fold with only the D026 differences"""
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


def manifest(conf, item_f):
    rows = []
    for kind, d in (("confirmatory", conf), ("item_f", item_f)):
        for name, c in d.items():
            rows.append({"kind": kind, "file": name, "run_id": c["run_id"], "test": c["test"], "fold": c["fold"], "m": c.get("m"), "arms": c["arms"], "config_sha256": canonical_hash(c),
                         "file_sha256": hashlib.sha256(render(c).encode("utf8")).hexdigest()})
    return {"note": "generated by code/prereg/make_confirmatory_configs.py (reproducible); config_sha256 = guard.canonical_config_hash(DEFAULTS merged with the file); these are the hashes FROZEN pins in "
                    "config_sha256s (kind confirmatory) and item_f_config_sha256s (kind item_f)", "n_trials": N_TRIALS, "window": WINDOW, "backbone": BACKBONE, "files": rows}


def planned():
    """-> {absolute path: text} of every file this script owns"""
    conf = confirmatory_configs()
    item_f = item_f_configs(conf)
    files = {os.path.join(CONF_DIR, n): render(c) for n, c in conf.items()}
    files[os.path.join(CONF_DIR, "MANIFEST.json")] = json.dumps(manifest(conf, item_f), indent=1) + "\n"
    files.update({os.path.join(ITEM_F_DIR, n): render(c) for n, c in item_f.items()})
    return files


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="do not write; exit 1 if a file differs")
    a = ap.parse_args(argv)
    files = planned()
    if a.check:
        bad = [p for p, t in files.items() if not os.path.isfile(p) or open(p, encoding="utf8", newline="").read() != t]
        stale = [os.path.join(d, f) for d in (CONF_DIR, ITEM_F_DIR) if os.path.isdir(d) for f in os.listdir(d) if f.endswith(".json") and os.path.join(d, f) not in files]
        for p in bad + stale:
            print("DIFFERS" if p in bad else "STALE", p)
        return 1 if (bad or stale) else 0
    for d in (CONF_DIR, ITEM_F_DIR):
        os.makedirs(d, exist_ok=True)
    for p, t in files.items():
        with open(p, "w", encoding="utf8", newline="") as fh:
            fh.write(t)
    print(f"wrote {len(files)} files: {len(confirmatory_configs())} confirmatory, 5 item (f), MANIFEST.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
