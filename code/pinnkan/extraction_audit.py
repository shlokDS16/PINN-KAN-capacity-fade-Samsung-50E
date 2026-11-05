"""Identifiability audit of the extracted laws A15 and G15 (D022 judge 2.2; PREREG_v4 7.3 item 6 and 11a item 10). One code path for both arms.

For every extracted law (arm, outer fold, seed) the audit records, per input: the family the law carries, the sign of the effect, the BIC margin of the chosen family on the
extraction grid, the additivity of the law in that input and whether the cap-2 form approximates a curved learned effect. Over the fold-by-seed laws of one arm it labels each
input (pruned | identified: <family> | sign identified | composed: no single form | ambiguous) by the rule of `extraction_audit.json`, which needs

    L_e   the number of distinct training levels of the input (identifiers only), so that an input with L levels carries at most L - 1 identifiable shape parameters
          (the additive constant is confounded with the law level) and with L_e = 2 never gets "identified: <family>";
    the calibration of the pipeline on design-matched synthetic truths (code/prereg/extraction_calibration.py, rule debates/D022_datasets_kan/calibration_rule.md):
          false-family rate and sign-error rate per (input, m, arm) cell.

No input is named with a family unless all conditions hold; every other case abstains. The thresholds file is hashed (`thresholds_sha256`) and its hash is a config key.
The statistics step prints edge-level wording only through `require_calibration` (calibration output hashed before any outer score)."""
import hashlib
import json
import math
import os

import numpy as np
import torch

THRESHOLDS_FILE = os.path.join(os.path.dirname(__file__), "extraction_audit.json")
CALIBRATION_FILE, CALIBRATION_HASH = "calibration.json", "calibration_hash.json"
ELIGIBLE = ("zero", "linear", "log")


class AuditGuardError(RuntimeError):
    """edge-level wording was requested without a valid calibration table (missing, altered, or written after an outer score)"""


# ------------------------------------------------------------------------------------------------ thresholds
def load_thresholds(path=THRESHOLDS_FILE):
    t = json.load(open(path, encoding="utf8"))
    need = {"cap", "eligible_families", "inputs", "pruned_min_share", "identified_min_share", "additive_min_share", "min_levels_identified", "max_false_family_rate",
            "sign_min_share", "max_sign_error_rate", "min_synthetic_edges_per_truth_family", "approx_rms_over_range", "approx_flag_min_share", "wording"}
    if not need <= set(t):
        raise ValueError(f"extraction_audit.json lacks {sorted(need - set(t))}")
    if tuple(t["eligible_families"]) != ELIGIBLE:
        raise ValueError("eligible families must be {zero, linear, log} (cap 2)")
    return t


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def thresholds_sha256(path=THRESHOLDS_FILE):
    return sha256_file(path)


# ------------------------------------------------------------------------------------------------ design levels and identifiable parameters
def distinct_levels(cond_ids, inputs=("T_C", "soc_mid", "dod", "c_ch", "c_dch")):
    """number of distinct values of each input among the training cycling condition identifiers (D022: from subsets.json, identifiers only)"""
    from .subsets import parse_samsung_cond
    X = np.stack([parse_samsung_cond(c) for c in cond_ids])
    return {name: int(len(np.unique(np.round(X[:, i], 6)))) for i, name in enumerate(inputs)}


def identifiable_parameters(family, levels):
    """shape parameters an input with `levels` distinct training values can identify for a family: 0 for zero, else min(1, L - 1) under cap 2 (a linear or log form has one shape
    parameter, the slope; the additive constant is confounded with the law level). Never more than L - 1."""
    if family == "zero":
        return 0
    return int(max(0, min(1, levels - 1)))


# ------------------------------------------------------------------------------------------------ one extracted law
def _signs_and_pd(fn, spec, s_train, n_grid):
    """sign of the effect of every input (finite difference of the cyclic map over the input's training-hull range, other inputs at the hull midpoint) and its partial dependence
    (mean over the training stress rows with the input set to the grid value)"""
    s = np.asarray(s_train, float)
    lo, hi = s.min(0), s.max(0)
    mid = 0.5 * (lo + hi)
    signs, pds = {}, {}
    with torch.no_grad():
        for i, name in enumerate(spec.stress_names):
            a, b = mid.copy(), mid.copy()
            a[i], b[i] = lo[i], hi[i]
            v = fn(torch.tensor(np.stack([b, a]), dtype=torch.float32))
            d = float(v[0] - v[1])
            signs[name] = 0 if abs(d) < 1e-9 else (1 if d > 0 else -1)
            grid = np.linspace(lo[i], hi[i], n_grid) if hi[i] > lo[i] else np.array([lo[i]])
            vals = []
            for g in grid:
                rows = s.copy()
                rows[:, i] = g
                vals.append(float(fn(torch.tensor(rows, dtype=torch.float32)).mean()))
            pds[name] = np.array(vals)
    return signs, pds


def input_family(edge_families, nonzero_edges):
    if nonzero_edges == 0:
        return "zero"
    if nonzero_edges == 1:
        return next(f for f in edge_families if f != "zero")
    return "composed"


def law_record(arm, fold, seed, report, spec, sym_cyc, parent_cyc, s_train, thr=None):
    """one fold-by-seed law -> {input: {family, sign, margin, edge_families, additive, approx}}. report = SymbolicArm.report; sym_cyc / parent_cyc = the extracted and the parent cyclic maps."""
    thr = thr or load_thresholds()
    layers = report["cyclic"]["layers"]
    first = layers[0]["edges"]
    outer = layers[1]["edges"] if len(layers) > 1 else None
    h = len(first) if outer is not None else 1
    outer_fams = [e["family"] for row in outer for e in row] if outer is not None else []
    additive = bool(h == 1 or all(f in ("linear", "zero") for f in outer_fams))          # judge 2.2a (iv), read literally: h = 1, or every outer edge linear/zero
    signs, pd_sym = _signs_and_pd(sym_cyc, spec, s_train, thr["pd_grid_points"])
    pd_par = _signs_and_pd(parent_cyc, spec, s_train, thr["pd_grid_points"])[1] if parent_cyc is not None else None
    out = {}
    for i, name in enumerate(spec.stress_names):
        edges = [first[j][i] for j in range(len(first))]
        fams = [e["family"] for e in edges]
        nz = [e for e in edges if e["family"] != "zero"]
        dom = max(nz, key=lambda e: e.get("range", 0.0)) if nz else None
        margin = None
        if dom is not None and dom.get("bic_table"):
            others = [v[0] for k, v in dom["bic_table"].items() if k != dom["family"]]
            if others:
                margin = float(min(others) - dom["bic_table"][dom["family"]][0])
        approx = None
        if pd_par is not None:
            a, b = pd_sym[name] - pd_sym[name].mean(), pd_par[name] - pd_par[name].mean()
            rng = float(np.ptp(pd_par[name]))
            approx = bool(rng > 0 and float(np.sqrt(np.mean((a - b) ** 2))) / rng > thr["approx_rms_over_range"])
        out[name] = {"family": input_family(fams, len(nz)), "sign": signs[name], "bic_margin": margin, "edge_families": fams, "additive": additive, "approx": approx}
    return {"arm": arm, "fold": int(fold), "seed": int(seed), "h": h, "outer_families": outer_fams, "inputs": out}


# ------------------------------------------------------------------------------------------------ calibration tables
def clopper_pearson(k, n, alpha=0.05):
    from scipy.stats import beta
    if n == 0:
        return (float("nan"), float("nan"))
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def calibration_tables(records):
    """records: dicts {arm, m, input, truth, truth_sign, chosen, sign} of the additive block (truth in zero|linear|log). -> {"input|m|arm": cell} with
    n per truth family, confusion counts of the chosen family and of the sign (exact 95 % intervals), the false-family rate per eligible family and the sign-error rate"""
    cells = {}
    for r in records:
        if r["truth"] not in ELIGIBLE:
            continue
        c = cells.setdefault(f"{r['input']}|{r['m']}|{r['arm']}", {"n": {t: 0 for t in ELIGIBLE}, "confusion": {t: {} for t in ELIGIBLE}, "sign": {"correct": 0, "wrong": 0, "zero": 0}})
        c["n"][r["truth"]] += 1
        c["confusion"][r["truth"]][r["chosen"]] = c["confusion"][r["truth"]].get(r["chosen"], 0) + 1
        if r["truth"] != "zero":
            k = "zero" if r["sign"] == 0 else ("correct" if r["sign"] == r["truth_sign"] else "wrong")
            c["sign"][k] += 1
    for c in cells.values():
        c["false_family_rate"], c["false_family_ci"] = {}, {}
        for F in ELIGIBLE:
            den = sum(c["n"][t] for t in ELIGIBLE if t != F)
            num = sum(c["confusion"][t].get(F, 0) for t in ELIGIBLE if t != F)
            c["false_family_rate"][F] = (num / den) if den else float("nan")
            c["false_family_ci"][F] = list(clopper_pearson(num, den))
        sn = c["sign"]["correct"] + c["sign"]["wrong"] + c["sign"]["zero"]
        c["sign_error_rate"] = ((c["sign"]["wrong"] + c["sign"]["zero"]) / sn) if sn else float("nan")      # a zero sign on a nonzero truth is not a correct sign
        c["sign_n"] = sn
        c["sign_error_ci"] = list(clopper_pearson(c["sign"]["wrong"] + c["sign"]["zero"], sn))
    return cells


def _cell_ok(cell, thr):
    return bool(cell) and all(cell["n"][t] >= thr["min_synthetic_edges_per_truth_family"] for t in ELIGIBLE)


# ------------------------------------------------------------------------------------------------ the label rule
def label_input(name, laws, levels, calibration, m, arm_key, thr=None):
    """label of one input from the fold-by-seed laws of one arm. -> dict(label, family, reasons, shares, ...). Abstention is the default."""
    thr = thr or load_thresholds()
    N = len(laws)
    recs = [l["inputs"][name] for l in laws]
    share_zero = sum(r["family"] == "zero" for r in recs) / N
    fam_counts = {}
    for r in recs:
        fam_counts[r["family"]] = fam_counts.get(r["family"], 0) + 1
    nonzero = {f: c for f, c in fam_counts.items() if f not in ("zero", "composed")}
    modal, modal_n = (max(nonzero.items(), key=lambda kv: kv[1]) if nonzero else (None, 0))
    share_family = modal_n / N
    sign_counts = {1: sum(r["sign"] == 1 for r in recs), -1: sum(r["sign"] == -1 for r in recs)}
    share_sign = max(sign_counts.values()) / N
    share_add = sum(r["additive"] for r in recs) / N
    approx_share = np.mean([bool(r["approx"]) for r in recs if r["approx"] is not None]) if any(r["approx"] is not None for r in recs) else None
    L = int(levels[name])
    cell = (calibration or {}).get(f"{name}|{m}|{arm_key}")
    cal_ok = _cell_ok(cell, thr)
    margins = [r["bic_margin"] for r in recs if r["bic_margin"] is not None]
    out = {"input": name, "n_laws": N, "levels": L, "share_zero": share_zero, "modal_family": modal, "share_family": share_family, "share_sign": share_sign, "share_additive": share_add,
           "median_bic_margin": (float(np.median(margins)) if margins else None), "identifiable_parameters": (identifiable_parameters(modal, L) if modal else 0),
           "calibration_cell": ({"n": cell["n"], "false_family_rate": cell["false_family_rate"], "sign_error_rate": cell["sign_error_rate"]} if cell else None),
           "approximate": bool(approx_share is not None and approx_share > thr["approx_flag_min_share"]), "reasons": []}
    why = out["reasons"]
    if share_zero >= thr["pruned_min_share"]:
        out["label"] = "pruned"
        return out
    cond_i = L >= thr["min_levels_identified"]
    cond_ii = modal is not None and share_family >= thr["identified_min_share"]
    cond_iii = bool(cond_ii and cal_ok and cell["false_family_rate"][modal] <= thr["max_false_family_rate"])
    cond_iv = share_add >= thr["additive_min_share"]
    if not cond_i:
        why.append(f"L_e = {L} < {thr['min_levels_identified']}: the label can be at most 'sign identified'")
    if not cond_ii:
        why.append("no family is chosen in the required share of the fold-by-seed laws")
    if cond_ii and not cal_ok:
        why.append("the calibration cell is missing or has fewer than the required synthetic edges per truth family")
    if cond_ii and cal_ok and not cond_iii:
        why.append(f"calibrated false-family rate {cell['false_family_rate'][modal]:.2f} exceeds {thr['max_false_family_rate']}")
    if cond_i and cond_ii and cond_iii:
        if cond_iv:
            out["label"], out["family"] = "identified", modal
            return out
        out["label"] = "composed"
        why.append("the law is not additive in this input")
        return out
    sign_ok = bool(share_sign >= thr["sign_min_share"] and cal_ok and cell["sign_error_rate"] <= thr["max_sign_error_rate"] and max(sign_counts, key=sign_counts.get) != 0)
    if sign_ok:
        out["label"], out["sign"] = "sign", max(sign_counts, key=sign_counts.get)
        return out
    out["label"] = "ambiguous"
    return out


def label_law(laws, levels, calibration, m, arm_key, thr=None):
    thr = thr or load_thresholds()
    return {name: label_input(name, laws, levels, calibration, m, arm_key, thr) for name in thr["inputs"]}


def label_text(lab, thr=None):
    thr = thr or load_thresholds()
    w = thr["wording"]["labels"]
    if lab["label"] == "identified":
        return w["identified"].format(family=lab["family"])
    return w[{"pruned": "pruned", "sign": "sign", "composed": "composed", "ambiguous": "ambiguous"}[lab["label"]]]


def results_sentence(labels, arm, thr=None):
    """the fixed Results sentence (11a item 10): counts of identified forms, identified signs and ambiguous inputs (composed inputs count with the ambiguous: no named form), plus the
    pruned sentence"""
    thr = thr or load_thresholds()
    n = len(labels)
    j = sum(l["label"] == "identified" for l in labels.values())
    s = sum(l["label"] == "sign" for l in labels.values())
    p = sum(l["label"] == "pruned" for l in labels.values())
    a = n - j - s - p
    w = thr["wording"]
    law = w["law_names"][arm]
    return {"results": w["results_sentence"].format(n=n, law=law, j=j, s=s, a=a), "pruned": w["pruned_sentence"].format(p=p, n=n), "counts": {"n": n, "identified": j, "sign": s, "ambiguous": a, "pruned": p}}


def input_notes(lab, thr=None):
    """sentences attached to an input in the Results: ambiguous / composed inputs, and the approximation flag"""
    thr = thr or load_thresholds()
    w = thr["wording"]
    notes = []
    if lab["label"] in ("ambiguous", "composed"):
        notes.append(w["ambiguous_input"])
    if lab["approximate"] and lab["label"] != "pruned":
        notes.append(w["approx_input"])
    return notes


def audit_arm(laws, levels, calibration, m, arm, thr=None):
    """full audit of one arm ('A15' or 'G15' family key for the sentence; the calibration key is the arm variant, e.g. A15h2): labels, edge table, sentences"""
    thr = thr or load_thresholds()
    arm_key = laws[0]["arm"]
    lab = label_law(laws, levels, calibration, m, arm_key, thr)
    table = []
    for name, l in lab.items():
        table.append({"arm": arm_key, "input": name, "levels": l["levels"], "eligible_families": list(thr["eligible_families"]), "identifiable_parameters": l["identifiable_parameters"],
                      "chosen_family": l["modal_family"], "bic_margin_median": l["median_bic_margin"], "share_family": l["share_family"], "share_sign": l["share_sign"],
                      "label": label_text(l, thr), "notes": input_notes(l, thr), "bic_caveat": thr["wording"]["bic_caveat"]})
    return {"labels": lab, "table": table, "sentences": results_sentence(lab, arm, thr)}


# ------------------------------------------------------------------------------------------------ D021 regression and the guard
def false_structure_counts(records, cap, arm, m, kind="G0", seeds=range(10), linear_inputs=("T_C", "dod", "c_ch", "c_dch")):
    """D021 false structure: a 3-coefficient family on an input whose truth is linear. records = the D021 pipeline records (runs/D021_cap_synth/pipeline_p*.jsonl).
    -> (bad, total) over the linear-truth inputs of the given arm, m and seeds"""
    three = ("quadratic", "power", "exponential", "arrhenius", "hinge")
    bad = n = 0
    for r in records:
        if r["kind"] != kind or r["arm"] != arm or r["m"] != m or r["seed"] not in set(seeds):
            continue
        for k in linear_inputs:
            n += 1
            bad += int(any(f in three for f in r["caps"][str(cap)]["families_first_layer"][k]))
    return bad, n


def write_calibration_record(directory, calibration):
    """write calibration.json and its hash record (sha256 + write time); the calibration run calls this before any outer score exists"""
    import time
    os.makedirs(directory, exist_ok=True)
    p = os.path.join(directory, CALIBRATION_FILE)
    with open(p, "w", encoding="utf8") as fh:
        json.dump(calibration, fh, indent=1, sort_keys=True)
    rec = {"file": CALIBRATION_FILE, "sha256": sha256_file(p), "written_unix": time.time(), "thresholds_sha256": thresholds_sha256()}
    with open(os.path.join(directory, CALIBRATION_HASH), "w", encoding="utf8") as fh:
        json.dump(rec, fh, indent=1)
    return rec


def require_calibration(directory, run_dirs, thresholds_pin=None):
    """the guard of the statistics step: edge-level law wording needs the calibration table; it must exist, match its hash record, carry the thresholds hash in force (and the pinned
    one if given) and be older than every outer score file (condition_scores*.json) of the runs. Returns the calibration cells."""
    p, h = os.path.join(directory, CALIBRATION_FILE), os.path.join(directory, CALIBRATION_HASH)
    if not (os.path.exists(p) and os.path.exists(h)):
        raise AuditGuardError(f"no calibration table in {directory}: the statistics step does not print edge-level law wording (it prints the law only)")
    rec = json.load(open(h, encoding="utf8"))
    if rec["sha256"] != sha256_file(p):
        raise AuditGuardError("calibration table differs from its hash record (altered after hashing)")
    cur = thresholds_sha256()
    if rec.get("thresholds_sha256") != cur or (thresholds_pin is not None and thresholds_pin != cur):
        raise AuditGuardError("the calibration was made with other thresholds than the ones in force (extraction_audit.json hash)")
    scores = []
    for d in run_dirs:
        if os.path.isdir(d):
            scores += [os.path.getmtime(os.path.join(d, f)) for f in os.listdir(d) if f.startswith("condition_scores") and f.endswith(".json")]
    if scores and not (os.path.getmtime(p) < min(scores) and rec["written_unix"] < min(scores)):
        raise AuditGuardError("the calibration table was written after an outer score file existed")
    return json.load(open(p, encoding="utf8"))["cells"]
