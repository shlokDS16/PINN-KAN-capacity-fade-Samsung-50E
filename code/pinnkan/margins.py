"""margins.json inputs (PREREG_v2 9.2): E = comparator's training-side inner-CV condition-mean score per outer fold, pooled by test-condition
count; delta_S = 0.02 E, delta_N = 0.10 E (pp); log-scale margins ln(1.02) and -ln(1.10) need no E. Written after tuning ends and before any final
refit is applied to a test condition (the runner enforces the order).

Pooled over the five outer folds, per contrast and grid cell (PREREG_v4 9.2, 9.10): `pooled_margins` (below) forms the pp margins of the whole grid from the per-run `margins_inputs.json`
(and `comparators.json` for D* and AG); `python -m pinnkan.margins --runs d1,d2,... --out runs/prereg/margins.json` writes the file; the statistics step writes the same record to its
analysis directory and attaches the margins to the estimated rows. No margin value is a number chosen by hand: every E comes from a training-side inner-CV score."""
import hashlib
import json
import os

import numpy as np

LOG_MARGIN_S = float(np.log(1.02))
LOG_MARGIN_N = float(-np.log(1.10))


def pooled_E(per_fold):
    """per_fold: list of (n_test_conditions, E_fold) -> E pooled by test-condition count"""
    n = np.array([p[0] for p in per_fold], float)
    e = np.array([p[1] for p in per_fold], float)
    return float((n * e).sum() / n.sum())


def margin_record(per_fold):
    E = pooled_E(per_fold)
    return {"E_pp": E, "delta_S_pp": 0.02 * E, "delta_N_pp": 0.10 * E, "per_fold": [list(map(float, p)) for p in per_fold],
            "log_margin_S": LOG_MARGIN_S, "log_margin_N": LOG_MARGIN_N}


def write_margins(path, contrasts):
    """contrasts: {name: per_fold list} -> writes json with a content hash"""
    body = {k: margin_record(v) for k, v in sorted(contrasts.items())}
    h = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    with open(path, "w", encoding="utf8") as fh:
        json.dump({"contrasts": body, "sha256": h}, fh, indent=1)
    return h


# ------------------------------------------------------------------------------------------------ pooled pp-scale margins per contrast and grid cell (PREREG_v4 9.2)
class MarginsError(RuntimeError):
    """the pp-scale margins cannot be formed as 9.2 prescribes: inputs missing from some runs, a comparator missing in some folds, or margins_inputs.json written after a test score"""


SENSITIVITY_S = (0.0, 0.05)                    # PREREG_v4 9.2 sensitivity rows (relative to E): delta_S in {0, 0.05}, delta_N in {0.05, 0.15}
SENSITIVITY_N = (0.05, 0.15)
INPUTS_FILE = "margins_inputs.json"
# (target, comparator) pairs whose pp margin is formed at every grid cell where both arms run: the estimated tables of the statistics step (A1 against each comparator; D* and AG resolve
# per fold) and the chain contrasts K1 (A15 against A1) and K2 (A15 against G15)
CONTRAST_PAIRS = tuple(("A1", c) for c in ("D*", "A9", "AG", "A2", "A10", "A10P", "A13")) + (("A15", "A1"), ("A15", "G15"))
NAMED = {"P1": ("A1", "D*", (8, "2")), "P2": ("A1", "A9", (8, "2")), "K1": ("A15", "A1", (32, "full")), "K2": ("A15", "G15", (32, "full")),
         "QA10_g1": ("A1", "A10", (8, "2")), "QA10P_g1": ("A1", "A10P", (8, "2")), "QA10_g4": ("A1", "A10", (32, "full")), "QA10P_g4": ("A1", "A10P", (32, "full")),
         "QH_g1": ("A1", "A2", (8, "2")), "QH_g4": ("A1", "A2", (32, "full")), "QT_g1": ("A1", "A13", (8, "2"))}


def cell_label(cell):
    return f"m{int(cell[0])}_k{cell[1]}"


def _sha_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _run_inputs(d, strict):
    """-> dict(cfg, labels, mi, comp, sha) of one grid run directory; the order rule: margins_inputs.json must not be newer than any condition_scores file (the scores are written after the refits)"""
    cfg = json.load(open(os.path.join(d, "config.json"), encoding="utf8"))
    met = json.load(open(os.path.join(d, "metrics.json"), encoding="utf8"))
    p = os.path.join(d, INPUTS_FILE)
    if not os.path.exists(p):
        raise MarginsError(f"{d}: no {INPUTS_FILE}")
    mi = json.load(open(p, encoding="utf8"))
    cp = os.path.join(d, "comparators.json")
    comp = json.load(open(cp, encoding="utf8")) if os.path.exists(cp) else {}
    if strict:
        scores = [os.path.getmtime(os.path.join(d, f)) for f in os.listdir(d) if f.startswith("condition_scores") and f.endswith(".json")]
        if scores and os.path.getmtime(p) > min(scores):
            raise MarginsError(f"{d}: {INPUTS_FILE} is newer than a condition-scores file: the margins must exist before any test condition is scored (PREREG_v4 9.2)")
    return dict(cfg=cfg, labels=list(met.get("k_labels") or ["full"]), mi=mi, comp=comp, sha=_sha_file(p))


def _resolve(comparator, mi, comp, where):
    """-> (arm, E, n_test) of the comparator in one run, or None when it did not run. D* and AG are the arm selected from inner-CV scores in this fold (comparators.json): the margin uses the
    SELECTED arm's own E"""
    arm = comparator
    if comparator in ("D*", "AG"):
        if comparator not in comp:
            return None
        arm = comp[comparator]["arm"]
    e = mi["per_arm_E_by_fold"].get(f"E_{arm}")
    if not e:
        return None
    n_test, E = e[0]
    if comparator in ("D*", "AG") and comp[comparator].get("score") is not None and abs(float(comp[comparator]["score"]) - float(E)) > 1e-9 * max(1.0, abs(float(E))):
        raise MarginsError(f"{where}: the selector {comparator} score {comp[comparator]['score']} differs from E_{arm} = {E} of {INPUTS_FILE}")
    return arm, float(E), int(n_test)


def margin_row(per_fold):
    """per_fold: [(fold, comparator arm, n_test, E)] -> E pooled by test-condition count, delta_S = 0.02 E, delta_N = 0.10 E and the 9.2 sensitivity margins; a non-finite E gives no margin"""
    pairs = [(n, E) for _, _, n, E in per_fold]
    row = {"per_fold": [{"fold": int(f), "comparator_arm": a, "n_test_conditions": int(n), "E_pp": float(E)} for f, a, n, E in per_fold], "log_margin_S": LOG_MARGIN_S, "log_margin_N": LOG_MARGIN_N}
    if not all(np.isfinite(E) for _, E in pairs):
        row.update(E_pp=None, delta_S_pp=None, delta_N_pp=None, sensitivity=None, note="a non-finite inner-CV score in at least one fold: no pp margin is formed")
        return row
    E = pooled_E(pairs)
    row.update(E_pp=E, delta_S_pp=0.02 * E, delta_N_pp=0.10 * E, note=None,
               sensitivity={"delta_S_pp": {repr(x): x * E for x in SENSITIVITY_S}, "delta_N_pp": {repr(x): x * E for x in SENSITIVITY_N}})
    return row


def pooled_margins(run_dirs, folds=range(5), strict=True):
    """PREREG_v4 9.2: E = the comparator's training-side inner-CV condition-mean score at the grid cell, per outer fold, pooled by test-condition count; delta_S = 0.02 E, delta_N = 0.10 E
    (pp, descriptive beside every tier). Formed from the `margins_inputs.json` of the grid runs (written after tuning and before any test score; checked by file times when strict) and the
    run's `comparators.json` (D*, AG per fold). The inner-CV score is computed once per (outer fold, m): the cells (m, k) of one m share E. Every contrast pair is formed at every cell where
    the comparator and the target arm run; a comparator present in some but not all folds of an m raises (it would pool a subset). -> record with `contrasts[<target> vs <comparator>]
    [m<m>_k<k>]`, `named` (P1, P2, K1, K2 and the secondary tests) and a content hash."""
    runs = {}
    for d in run_dirs:
        r = _run_inputs(d, strict)
        cfg = r["cfg"]
        m = 32 if cfg.get("m") is None else int(cfg["m"])
        key = (m, int(cfg["fold"]))
        if key in runs:
            raise MarginsError(f"two runs for (m = {m}, fold {cfg['fold']})")
        runs[key] = dict(r, dir=d)
    want = sorted(int(f) for f in folds)
    out = {"contrasts": {}, "inputs_sha256": {f"m{m}_fold{f}": r["sha"] for (m, f), r in sorted(runs.items())},
           "definition": "PREREG_v4 9.2: pp margins delta_S = 0.02 E and delta_N = 0.10 E from training-side inner-CV scores, pooled by test-condition count; descriptive beside every tier, never a gate"}
    for m in sorted({m for m, _ in runs}):
        got = sorted(f for mm, f in runs if mm == m)
        if got != want:
            raise MarginsError(f"m = {m}: margins_inputs of folds {got} instead of {want}")
        label_sets = {tuple(runs[(m, f)]["labels"]) for f in got}
        if len(label_sets) != 1:
            raise MarginsError(f"m = {m}: the runs disagree on the k labels {sorted(label_sets)}")
        ks = list(label_sets.pop())
        for target, comparator in CONTRAST_PAIRS:
            tgt = [f for f in got if f"E_{target}" in runs[(m, f)]["mi"]["per_arm_E_by_fold"]]
            res = {f: _resolve(comparator, runs[(m, f)]["mi"], runs[(m, f)]["comp"], f"m = {m}, fold {f}") for f in got}
            have = [f for f in got if res[f] is not None]
            if not have or not tgt:
                continue
            if len(have) != len(got) or len(tgt) != len(got):
                raise MarginsError(f"m = {m}: {target} vs {comparator} is present in folds {sorted(set(have) & set(tgt))} of {got}: the margin would pool a subset of the folds")
            row = margin_row([(f, res[f][0], res[f][2], res[f][1]) for f in got])
            for k in ks:
                out["contrasts"].setdefault(f"{target} vs {comparator}", {})[cell_label((m, k))] = dict(row, cell=[m, k])
    out["named"] = {n: {"target": t, "comparator": c, "cell": list(cell), "margin": out["contrasts"].get(f"{t} vs {c}", {}).get(cell_label(cell))} for n, (t, c, cell) in NAMED.items()}
    out["sha256"] = hashlib.sha256(json.dumps({k: out[k] for k in ("contrasts", "inputs_sha256", "named")}, sort_keys=True).encode()).hexdigest()
    return out


def write_pooled(path, record):
    with open(path, "w", encoding="utf8") as fh:
        json.dump(record, fh, indent=1)
    return record["sha256"]


def tier_pp(lower_bound_pp, delta_S, delta_N):
    """descriptive pp tier beside the log-scale tier (PREREG_v4 9.2): the BCa lower bound of the mean pp gain against delta_S (tier S) and -delta_N (tier N); None without a margin"""
    if delta_S is None or delta_N is None:
        return None
    return "S" if lower_bound_pp > delta_S else ("N" if lower_bound_pp > -delta_N else "-")


def has_inputs(run_dirs):
    """True when every run has margins_inputs.json, False when none has; a mixture raises"""
    flags = [os.path.exists(os.path.join(d, INPUTS_FILE)) for d in run_dirs]
    if any(flags) and not all(flags):
        raise MarginsError("some runs have margins_inputs.json and others do not")
    return bool(flags) and all(flags)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="pooled pp-scale margins (PREREG_v4 9.2) from the grid runs: writes margins.json (e.g. runs/prereg/margins.json)")
    ap.add_argument("--runs", required=True, help="comma-separated Test B grid run directories (5 outer folds x m in 8, 16, 32)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lenient", action="store_true", help="development only: skip the file-time order check")
    a = ap.parse_args(argv)
    print(write_pooled(a.out, pooled_margins(a.runs.split(","), strict=not a.lenient)))


if __name__ == "__main__":
    main()
