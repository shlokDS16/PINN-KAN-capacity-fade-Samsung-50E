"""Calibrated extraction audit of the extracted laws A15 and G15 (D022a judge 05_judge_audit_revision.md, sections 2.1-2.8; PREREG_v4 7.3 item 6 and 11a item 10). One code path for both arms.

Labels are read from the partial dependence of the extracted law (never from the extractor's edge list): per law and input the retained flag, the best linear-in-x and linear-in-log(x)
residuals as fractions of the partial-dependence range, the sign of the effect and a numerical additivity test (5 x 5 mixed second differences). Over the 25 laws of one arm at g4
(5 folds x 5 seeds) an input is labelled

    not retained (below the extraction tolerance)   not retained in at least 20 of 25 laws (not a claim about the truth)
    composed: no single form                        additivity fails in more than 5 of 25 laws
    form: linear | log                              additive in >= 20 laws and one family STRICTLY wins (residual <= 0.01, the other > 0.01) in >= 20 laws; a tie counts for neither
    sign: + | -                                     additive in >= 20 laws and the same sign (magnitude > 0.01 of the range) in >= 20 laws; no tie
    not identified by the audit                     everything else (abstention; the law is printed in full)

and the labels are printed for an arm only if the arm passed the calibration condition C1 (dataset-level family-wise bound; `verdict`). The calibration (code/prereg/extraction_calibration.py,
rule debates/D022_datasets_kan/calibration_rule_v2.md) scores whole synthetic datasets with the same label function. The thresholds file is hashed (`thresholds_sha256`) and its hash is a
config key. The statistics step prints edge-level wording only through `require_calibration`; the calendar extracted law gets none."""
import hashlib
import json
import math
import os
import re

import numpy as np
import torch

HERE = os.path.dirname(__file__)
THRESHOLDS_FILE = os.path.join(HERE, "extraction_audit.json")
RULE_FILE = os.path.join(HERE, "..", "..", "debates", "D022_datasets_kan", "calibration_rule_v2.md")
CALIBRATION_FILE = "calibration.json"
ELIGIBLE = ("zero", "linear", "log")
ARM_KEYS = ("A15h1", "A15h2", "G15")


class AuditGuardError(RuntimeError):
    """edge-level wording was requested without a valid, pinned calibration (missing pins, altered file, another commit or thresholds, void or failed calibration) or for the calendar law"""


class _CalibrationRun:
    """sentinel passed only by the (inert) calibration script, which scores the licences a rule WOULD give; never by the statistics step"""
    def __repr__(self):
        return "CALIBRATION_RUN"


CALIBRATION_RUN = _CalibrationRun()


def _licensed(calibrated):
    """D022b N3: a licence word needs a VERIFIED calibration: the dict returned by `require_calibration` (given only for an arm that passed C1) or the calibration script's sentinel.
    The default is no licence; a bare True is refused so that no script can print a licence by accident."""
    if calibrated is None or calibrated is False:
        return False
    if calibrated is CALIBRATION_RUN:
        return True
    if isinstance(calibrated, dict):                                       # D022b B1: a record returned by require_calibration carries a verdict that is a dict, not void, and holds per-arm results; a bare {"verdict": True} is no calibration
        v = calibrated.get("verdict")
        return isinstance(v, dict) and v.get("void") is False and isinstance(v.get("arms"), dict) and bool(v["arms"])
    raise AuditGuardError("a licence word needs a verified calibration (the dict returned by require_calibration); a bare True is refused (D022b N3)")


class AuditError(ValueError):
    """an input the audit refuses to guess: unknown arm, missing h, a number of laws other than 25 at g4, duplicate fold-by-seed laws"""


# ------------------------------------------------------------------------------------------------ thresholds
def load_thresholds(path=THRESHOLDS_FILE):
    t = json.load(open(path, encoding="utf8"))
    need = {"cap", "eligible_families", "inputs", "laws_per_arm_g4", "min_agree_share", "tolerance_over_range", "retained_min_range", "pd_grid_points", "additivity_grid",
            "approx_rms_over_range", "approx_flag_min_share", "calibration", "wording", "banned_phrases", "future_version_wording"}
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


def rule_sha256():
    return sha256_file(RULE_FILE)


class BannedWordingError(RuntimeError):
    """a generated sentence of the statistics step contains a banned claim (fail closed); `violations` = [(path, patterns)]"""
    violations = ()


def _norm(text):
    return re.sub(r"[\s\-~]+", " ", str(text)).strip()


_CLAUSE_BREAK = re.compile(r"[,;:()]|\b(?:but|however|although|whereas|yet|while|and)\b")
NEGATION_WINDOW = 3                                                              # tokens before a form word, inside its own clause, that negate it


def _negated(low, start, negation_words, reverse_words=()):
    """is the match at `start` of the lower-cased sentence `low` negated? Only negation words within the NEGATION_WINDOW tokens before it, in the same clause (no comma, semicolon, colon,
    bracket, "but", "and", ... in between), negate it: "is not linear", "not a hinge", "cannot represent the non-monotone ...". A negation elsewhere in the sentence does not (red-team N2).
    An odd number of negating tokens negates, an even number affirms: "not unlike an exponential" and "not without a hinge" (double negation; `reverse_words` such as "unlike" count as one) are claims."""
    seg = _CLAUSE_BREAK.split(low[:start])[-1]
    toks = re.findall(r"[a-z0-9_']+", seg)[-NEGATION_WINDOW:]
    return sum(t in negation_words or t in reverse_words or t.endswith("n't") for t in toks) % 2 == 1


def banned_phrases_in(text, thr=None):
    """banned claims in `text` (D022 section 4 and PREREG 7.3 item 1; red-team A4, N2, N3) -> list of matched patterns. Stems (recover*, discover*, identified, identifiable, identifiability,
    no effect, enforced, licence words, calibration-result phrases, ...) are banned anywhere. A form word (Arrhenius, power law, exponential, quadratic, hinge, threshold, activation energy,
    non-monotone) or "shows a/the ... form" is banned in a sentence that names a law or equation (subject words) unless THAT word is itself negated (the negation word must stand within
    NEGATION_WINDOW tokens before it, in the same clause; a negation elsewhere in the sentence does not exempt it). Hyphens, line breaks and case are normalised; word boundaries (also
    against `_`) so that "unenforced" and "not_identified" do not match. The approved PREREG 11 / 11a sentences must not match (tests)."""
    thr = thr or load_thresholds()
    b = thr["banned_phrases"]
    hits = []
    norm = _norm(text)
    wb = lambda pat: r"(?<![A-Za-z_])(?:" + pat + r")(?![A-Za-z_])"
    for pat in b["stems"]:
        if re.search(wb(pat), norm, flags=re.IGNORECASE):
            hits.append(pat)
    for pat in b.get("formula_anywhere", ()):                     # an Arrhenius-type formula such as exp(-b/T) is banned in any sentence (red-team N2)
        if re.search(pat, norm, flags=re.IGNORECASE):
            hits.append(pat)
    negs, rev = set(b["negation_words"]), set(b.get("reverse_words", ()))
    for sent in re.split(r"(?<=[.!?]) ", norm):                    # a sentence ends at . ! ? only: a ";" or ":" does not separate the law named in one clause from the form claimed in the next (N2)
        low = sent.lower()
        if not any(re.search(wb(sw), low) for sw in b["subject_words"]):
            continue
        for fw in b["form_words"]:
            if fw not in hits and any(not _negated(low, m.start(), negs, rev) for m in re.finditer(wb(fw), low)):
                hits.append(fw)
        for pat in b.get("formula_patterns", ()):                 # other formulas of the banned forms (exp(...), e^x, x^2, b/T) in a sentence that names a law or equation
            if pat not in hits and re.search(pat, low, flags=re.IGNORECASE):
                hits.append(pat)
        if "shows" not in hits and any(not _negated(low, m.start(), negs, rev) for m in re.finditer(b["shows_pattern"], low)):
            hits.append("shows")
    return hits


def check_generated_sentences(obj, where="output", thr=None):
    """fail closed: raise BannedWordingError if any string value in `obj` (nested dicts / lists; dictionary keys are not sentences) contains a banned claim"""
    thr = thr or load_thresholds()
    bad = []

    def walk(o, path):
        if isinstance(o, str):
            h = banned_phrases_in(o, thr)
            if h:
                bad.append((path, h, o[:80]))
        elif isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{path}.{k}")
        elif isinstance(o, (list, tuple)):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")
    walk(obj, where)
    if bad:
        err = BannedWordingError(f"banned wording in generated sentences: {bad[:3]}")
        err.violations = [(p_, h_) for p_, h_, _ in bad]
        raise err
    return True


# ------------------------------------------------------------------------------------------------ arms
def arm_key(arm_id, hp):
    """the audit's arm key: 'G15', or 'A15h<h>' with h from the arm's hyperparameters. An unknown arm or a missing h is an error, never a silent default (D022a m3)."""
    if arm_id == "G15":
        return "G15"
    if arm_id == "A15":
        h = (hp or {}).get("h")
        if h not in (1, 2):
            raise AuditError(f"A15 without h in {{1, 2}} (got {h!r}): the audit does not default the hidden width")
        return f"A15h{int(h)}"
    raise AuditError(f"unknown arm {arm_id!r}: the extraction audit covers A15 and G15 only")


# ------------------------------------------------------------------------------------------------ design levels (descriptive statement only)
def distinct_levels(cond_ids, inputs=("T_C", "soc_mid", "dod", "c_ch", "c_dch")):
    """number of distinct values of each input among the training cycling condition identifiers (identifiers only). The paper states that every input has at least 3 training levels,
    so no level condition binds (D022a M8); the numbers are recorded, not used by the label rule."""
    from .subsets import parse_samsung_cond
    X = np.stack([parse_samsung_cond(c) for c in cond_ids])
    return {name: int(len(np.unique(np.round(X[:, i], 6)))) for i, name in enumerate(inputs)}


# ------------------------------------------------------------------------------------------------ one extracted law
def _ev(fn, rows):
    with torch.no_grad():
        return fn(torch.tensor(np.asarray(rows), dtype=torch.float32)).detach().double().numpy().reshape(len(rows), -1)[:, 0]


def _physical(spec, rows, i):
    x = spec.denorm(rows)[:, i].astype(float)
    return x + (273.15 if i == spec.t_index else 0.0)


def _fit_resid(x, y):
    """RMS residual of the least-squares line y ~ a + b x"""
    A = np.stack([np.ones_like(x), x], axis=1)
    c, *_ = np.linalg.lstsq(A, y, rcond=None)
    return float(np.sqrt(np.mean((y - A @ c) ** 2)))


def partial_dependence(fn, spec, s_train, n_grid):
    """-> per input (name): the partial dependence on n_grid points of the fold's training hull (other inputs at the hull midpoint) and the physical grid; plus the hull midpoint"""
    s = np.asarray(s_train, float)
    lo, hi = s.min(0), s.max(0)
    mid = 0.5 * (lo + hi)
    pd, xs = {}, {}
    for i, name in enumerate(spec.stress_names):
        rows = np.tile(mid, (n_grid, 1))
        rows[:, i] = np.linspace(lo[i], hi[i], n_grid)
        pd[name] = _ev(fn, rows)
        xs[name] = _physical(spec, rows, i)
    return pd, xs, lo, hi, mid


def _max_mixed(fn, lo, hi, mid, i, grid):
    """largest absolute mixed second difference of the law over the grid x grid lattice of (x_i, x_j), every j != i, the other inputs at the hull midpoint"""
    worst = 0.0
    a = np.linspace(lo[i], hi[i], grid)
    for j in range(len(mid)):
        if j == i:
            continue
        b = np.linspace(lo[j], hi[j], grid)
        rows = np.tile(mid, (grid * grid, 1))
        rows[:, i] = np.repeat(a, grid)
        rows[:, j] = np.tile(b, grid)
        F = _ev(fn, rows).reshape(grid, grid)
        worst = max(worst, float(np.max(np.abs(F[1:, 1:] - F[1:, :-1] - F[:-1, 1:] + F[:-1, :-1]))))
    return worst


def input_family(edge_families, nonzero_edges):
    if nonzero_edges == 0:
        return "zero"
    if nonzero_edges == 1:
        return next(f for f in edge_families if f != "zero")
    return "composed"


def law_record(arm, fold, seed, report, spec, sym_cyc, parent_cyc, s_train, thr=None):
    """one fold-by-seed law -> {arm, fold, seed, h, outer_families, inputs: {name: per-input quantities}}. arm = the audit key (arm_key); report = SymbolicArm.report;
    sym_cyc / parent_cyc = the extracted and the parent cyclic maps (callables on normalised stress rows). Same function for A15 and G15 (D022a m5)."""
    thr = thr or load_thresholds()
    if arm not in ARM_KEYS:
        raise AuditError(f"unknown arm key {arm!r} (expected one of {ARM_KEYS})")
    layers = report["cyclic"]["layers"]
    first = layers[0]["edges"]
    outer = layers[1]["edges"] if len(layers) > 1 else None
    h = len(first) if outer is not None else 1
    if arm.startswith("A15h") and int(arm[4:]) != h:
        raise AuditError(f"arm key {arm} disagrees with the extracted network (h = {h})")
    outer_fams = [e["family"] for row in outer for e in row] if outer is not None else []
    tol, n_grid = thr["tolerance_over_range"], thr["pd_grid_points"]
    pd, xs, lo, hi, mid = partial_dependence(sym_cyc, spec, s_train, n_grid)
    pd_par = partial_dependence(parent_cyc, spec, s_train, n_grid)[0] if parent_cyc is not None else None
    out = {}
    for i, name in enumerate(spec.stress_names):
        y, x = pd[name], xs[name]
        rng = float(np.ptp(y))
        retained = bool(rng > thr["retained_min_range"])
        edges = [first[j][i] for j in range(len(first))]
        nz = [e for e in edges if e["family"] != "zero"]
        dom = max(nz, key=lambda e: e.get("range", 0.0)) if nz else None
        margin = None
        if dom is not None and dom.get("bic_table"):
            others = [v[0] for k, v in dom["bic_table"].items() if k != dom["family"]]
            if others:
                margin = float(min(others) - dom["bic_table"][dom["family"]][0])
        rec = {"retained": retained, "range": rng, "family": input_family([e["family"] for e in edges], len(nz)), "edge_families": [e["family"] for e in edges], "bic_margin": margin}
        if retained:
            r_lin, r_log = _fit_resid(x, y) / rng, _fit_resid(np.log(np.maximum(x, 1e-12)), y) / rng
            d = float(y[-1] - y[0])
            mixed = _max_mixed(sym_cyc, lo, hi, mid, i, thr["additivity_grid"])
            lin_ok, log_ok = r_lin <= tol, r_log <= tol
            rec.update(r_lin=r_lin, r_log=r_log, form=("tie" if (lin_ok and log_ok) else "linear" if lin_ok else "log" if log_ok else "none"),
                       sign=(0 if abs(d) <= tol * rng else (1 if d > 0 else -1)), sign_raw=(0 if abs(d) < 1e-9 else (1 if d > 0 else -1)), max_mixed=mixed, additive=bool(mixed <= tol * rng))
        else:
            rec.update(r_lin=None, r_log=None, form="none", sign=0, sign_raw=0, max_mixed=0.0, additive=True)          # not retained: nothing to be additive about
        a = None
        if pd_par is not None:
            u, v = y - y.mean(), pd_par[name] - pd_par[name].mean()
            pr = float(np.ptp(pd_par[name]))
            a = bool(pr > 0 and float(np.sqrt(np.mean((u - v) ** 2))) / pr > thr["approx_rms_over_range"])
        rec["approx"] = a                                                  # extraction-loss flag: compared with the arm's OWN parent (symmetric; D022a m1)
        out[name] = rec
    return {"arm": arm, "fold": int(fold), "seed": int(seed), "h": h, "outer_families": outer_fams, "inputs": out}


# ------------------------------------------------------------------------------------------------ the label rule (judge 2.3)
def _need(n, thr):
    return int(math.ceil(thr["min_agree_share"] * n - 1e-9))


def check_laws(laws, thr=None, n_expected=None):
    """exactly 25 distinct (fold, seed) laws of one arm family at g4; otherwise an error (D022a m3). n_expected overrides the count for unit and smoke tests only."""
    thr = thr or load_thresholds()
    n = thr["laws_per_arm_g4"] if n_expected is None else n_expected
    if len(laws) != n:
        raise AuditError(f"{len(laws)} laws for the arm, expected exactly {n} (5 folds x 5 seeds at g4): a missing or extra law is an error, never a silent skip")
    if len({(l["fold"], l["seed"]) for l in laws}) != n:
        raise AuditError("duplicate (fold, seed) laws in one arm")
    arms = {l["arm"] for l in laws}
    if not arms <= set(ARM_KEYS) or (("G15" in arms) and len(arms) > 1):
        raise AuditError(f"laws of unknown or mixed arms {sorted(arms)}")
    return n


def label_input(name, laws, thr=None, calibrated=False, n_expected=None):
    """label of one input from the 25 laws of one arm -> dict(label, form, sign, counts, reasons). `calibrated` = the arm passed C1; without it nothing is licensed."""
    thr = thr or load_thresholds()
    N = check_laws(laws, thr, n_expected)
    need = _need(N, thr)
    recs = [l["inputs"][name] for l in laws]
    n_not_ret = sum(not r["retained"] for r in recs)
    n_nonadd = sum(not r["additive"] for r in recs)
    wins = {f: sum(r["form"] == f for r in recs) for f in ("linear", "log")}
    ties = sum(r["form"] == "tie" for r in recs)
    votes = {1: sum(r["sign"] == 1 for r in recs), -1: sum(r["sign"] == -1 for r in recs)}
    F = max(wins, key=lambda f: (wins[f], f == "linear"))
    margins = [r["bic_margin"] for r in recs if r["bic_margin"] is not None]
    approx = [bool(r["approx"]) for r in recs if r["approx"] is not None]
    out = {"input": name, "n_laws": N, "need": need, "n_not_retained": n_not_ret, "n_nonadditive": n_nonadd, "wins": wins, "tie_share": ties / N, "sign_votes": {"+": votes[1], "-": votes[-1]},
           "bic_margin_median": (float(np.median(margins)) if margins else None), "extraction_loss": bool(approx and np.mean(approx) > thr["approx_flag_min_share"]), "form": None, "sign": 0, "reasons": [], "licensed": False}
    why = out["reasons"]
    form_ok = (N - n_nonadd) >= need and wins[F] >= need                      # (a) additive in >= 20, (b)+(c) one family strictly wins in >= 20 (two families cannot both reach 20 of 25)
    sign_ok = (N - n_nonadd) >= need and max(votes.values()) >= need and votes[1] != votes[-1]
    if name in thr.get("never_licensed_inputs", ()):                           # D022b N1(a), permanent: no temperature statement from the cycling law (laboratory is aliased with temperature)
        form_ok = sign_ok = False
        out["never_licensed"] = True
    if not _licensed(calibrated):
        out["label"] = "not_identified"
        why.append("no verified calibration: no label is printed (D022b: the audit is struck; descriptive reporting only)")
        return out
    out["licensed"] = True                                                      # set only after _licensed() passed; label_text and results_sentence refuse a form / sign label without it (D022b B1)
    if n_not_ret >= need:
        out["label"] = "not_retained"
    elif n_nonadd > N - need:
        out["label"] = "composed"
        why.append(f"additivity fails in {n_nonadd} of {N} laws")
    elif form_ok:
        out["label"], out["form"] = "form", F
        out["sign"] = (1 if votes[1] > votes[-1] else -1) if sign_ok else 0           # a form label implies the sign label
    elif sign_ok:
        out["label"], out["sign"] = "sign", (1 if votes[1] > votes[-1] else -1)
    else:
        out["label"] = "not_identified"
        if max(wins.values()) < need:
            why.append(f"no family strictly wins in {need} of {N} laws (strict wins {wins}, ties {ties})")
        if max(votes.values()) < need:
            why.append(f"no sign in {need} of {N} laws")
    return out


def label_law(laws, thr=None, calibrated=False, n_expected=None):
    thr = thr or load_thresholds()
    return {name: label_input(name, laws, thr, calibrated, n_expected) for name in thr["inputs"]}


def label_text(lab, thr=None):
    thr = thr or load_thresholds()
    w = thr["wording"]["labels"]
    if lab["label"] in ("form", "sign") and lab.get("licensed") is not True:
        raise AuditGuardError("a form or sign label text needs a label produced under a verified calibration (D022b B1)")
    if lab["label"] == "form":
        return w["form"].format(family=lab["form"])
    if lab["label"] == "sign":
        return w["sign"].format(sign="+" if lab["sign"] > 0 else "-")
    return w[lab["label"]]


def results_sentence(labels, arm, thr=None):
    """the fixed Results sentence (11a item 10): counts of licensed forms, of signs licensed without a form, of inputs not identified (composed included) and of inputs not retained"""
    thr = thr or load_thresholds()
    if any(l["label"] in ("form", "sign") and l.get("licensed") is not True for l in labels.values()):
        raise AuditGuardError("the Results sentence counts licensed forms and signs: it needs labels produced under a verified calibration (D022b B1)")
    n = len(labels)
    j = sum(l["label"] == "form" for l in labels.values())
    s = sum(l["label"] == "sign" for l in labels.values())
    p = sum(l["label"] == "not_retained" for l in labels.values())
    a = n - j - s - p
    w = thr["wording"]
    return {"results": thr["future_version_wording"]["results_sentence"].format(n=n, law=w["law_names"][arm], j=j, s=s, a=a, p=p), "counts": {"n": n, "form": j, "sign": s, "not_identified": a, "not_retained": p}}


def stability_table(laws, thr=None, n_expected=None):
    """the descriptive per-input table that is printed when an arm fails C1 (no label, no licence word): family votes, sign votes, tie share"""
    thr = thr or load_thresholds()
    N = check_laws(laws, thr, n_expected)
    rows = []
    for name in thr["inputs"]:
        recs = [l["inputs"][name] for l in laws]
        if name in thr.get("never_licensed_inputs", ()):                       # permanent T ban (D022b N1(a), red-team minor): temperature appears only under its fixed label, no counts
            rows.append({"input": name, "display": thr["wording"]["temperature_label"], "note": thr["wording"]["temperature_note"]})
            continue
        fams = {}
        for r in recs:
            fams[r["family"]] = fams.get(r["family"], 0) + 1
        rows.append({"input": name, "extracted_edge_family_counts": fams, "sign_votes": {"+": sum(r["sign_raw"] == 1 for r in recs), "-": sum(r["sign_raw"] == -1 for r in recs)},
                     "tie_share": sum(r["form"] == "tie" for r in recs) / N, "not_retained_share": sum(not r["retained"] for r in recs) / N,
                     "additive_share": sum(r["additive"] for r in recs) / N, "note": None})
    return rows


def audit_arm(laws, arm, calibrated=False, thr=None, n_expected=None):
    """full audit of one arm ('A15' or 'G15'): labels, table, sentences. The same function for both arms; without C1 only the descriptive stability table is returned."""
    thr = thr or load_thresholds()
    check_laws(laws, thr, n_expected)
    if not _licensed(calibrated):
        return {"labels_printed": False, "stability_table": stability_table(laws, thr, n_expected), "caption": thr["wording"]["stability_table_caption"]}
    lab = label_law(laws, thr, calibrated, n_expected)
    table = []
    for name, l in lab.items():
        row = {"arm": arm, "input": name, "label": (thr["wording"]["temperature_label"] if l.get("never_licensed") else label_text(l, thr)), "form_wins": l["wins"], "tie_share": l["tie_share"], "sign_votes": l["sign_votes"], "n_not_retained": l["n_not_retained"],
               "notes": ([thr["future_version_wording"]["not_identified_input"]] if l["label"] in ("composed", "not_identified") else []) + ([thr["wording"]["approx_input"]] if (l["extraction_loss"] and l["label"] != "not_retained") else [])}
        row["appendix"] = {"bic_margin_median": l["bic_margin_median"], "bic_caveat": thr["wording"]["bic_caveat"]}
        table.append(row)
    return {"labels_printed": True, "labels": lab, "table": table, "sentences": results_sentence(lab, arm, thr), "scope_sentence": thr["future_version_wording"]["scope_sentence"]}


def collect_laws(run_dirs, m=32, thr=None):
    """fold-by-seed law records from the `extracted_laws.json` of the g4 grid runs (m = 32). Exactly 25 laws per arm, otherwise AuditError."""
    thr = thr or load_thresholds()
    laws = {"A15": [], "G15": []}
    for d in run_dirs:
        cfg = json.load(open(os.path.join(d, "config.json"), encoding="utf8"))
        p = os.path.join(d, "extracted_laws.json")
        if (cfg.get("m") if cfg.get("m") is not None else 32) != m or not os.path.exists(p):
            continue
        for rr in json.load(open(p, encoding="utf8"))["laws"]:
            laws["G15" if rr["arm"] == "G15" else "A15"].append(rr)
    for arm, ls in laws.items():
        if ls:
            check_laws(ls, thr)
    return laws


# ------------------------------------------------------------------------------------------------ scoring of a calibration dataset (rule v2 section 4)
def clopper_pearson(k, n, alpha=0.05):
    """two-sided exact interval (descriptive rows)"""
    from scipy.stats import beta
    if n == 0:
        return (float("nan"), float("nan"))
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def clopper_pearson_upper(k, n, alpha=0.05):
    """one-sided exact upper limit at level 1 - alpha (C1)"""
    from scipy.stats import beta
    if n == 0:
        return float("nan")
    return 1.0 if k == n else float(beta.ppf(1 - alpha, k + 1, n - k))


def false_statements(lab, truth):
    """printed statements of one input that are false (rule v2 4.1). lab = {label, form, sign} (an audit label or a baseline label); truth = {stratum, sign, interacting}."""
    bad = []
    if lab.get("form") is not None and (lab["form"] != truth["stratum"] or truth["interacting"]):
        bad.append("form")
    if lab.get("sign") and lab["sign"] != truth["sign"]:
        bad.append("sign")
    return bad


def baseline_labels(laws, thr=None, n_expected=None):
    """the stability-only baseline (rule v2 4.4): a form when >= 20 of the 25 laws carry the same extracted edge family (linear or log), a sign when >= 20 agree on the finite-difference sign"""
    thr = thr or load_thresholds()
    N = check_laws(laws, thr, n_expected)
    need = _need(N, thr)
    out = {}
    for name in thr["inputs"]:
        recs = [l["inputs"][name] for l in laws]
        fam = {f: sum(r["family"] == f for r in recs) for f in ("linear", "log")}
        sg = {1: sum(r["sign_raw"] == 1 for r in recs), -1: sum(r["sign_raw"] == -1 for r in recs)}
        F = max(fam, key=lambda f: (fam[f], f == "linear"))
        s = max(sg, key=sg.get)
        out[name] = {"form": F if fam[F] >= need else None, "sign": s if sg[s] >= need else 0}
    return out


def score_dataset(labels, truth):
    """-> {E: 0|1, false: [(input, kind)]} for a dict of labels {input: {form, sign, ...}} against truth {input: {stratum, sign, interacting}}"""
    bad = [(name, k) for name in truth for k in false_statements(labels[name], truth[name])]
    return {"E": int(bool(bad)), "false": bad}


def recall_events(labels, truth, thr=None):
    """(dataset, input) events of C2: many-level inputs with a linear or log truth that is not in an interaction -> list of 0/1 (the audit licensed the correct form)"""
    thr = thr or load_thresholds()
    return [int(labels[n].get("form") == truth[n]["stratum"]) for n in thr["calibration"]["recall_inputs"] if truth[n]["stratum"] in ("linear", "log") and not truth[n]["interacting"]]


def verdict(per_arm, thr=None):
    """C1-C3 per arm and the overall contribution flag. per_arm: {arm: [dataset result dicts {d, E, E_baseline, events, events_baseline}]}. Void when fewer than D_min datasets are complete."""
    thr = thr or load_thresholds()
    c = thr["calibration"]
    out = {"arms": {}, "thresholds": {"max_upper_limit": c["max_upper_limit"], "min_recall": c["min_recall"], "alpha": c["alpha"], "D_min": c["D_min"]}}
    ok_all, failed = True, []
    for arm, rows in per_arm.items():
        D = len(rows)
        if D < c["D_min"]:
            out["void"] = True
            out["reason"] = f"{arm}: {D} complete datasets, fewer than D_min = {c['D_min']}"
            out["contribution"] = False
            return out
        k = sum(r["E"] for r in rows)
        kb = sum(r["E_baseline"] for r in rows)
        ev = [e for r in rows for e in r["events"]]
        evb = [e for r in rows for e in r["events_baseline"]]
        up, upb = clopper_pearson_upper(k, D, c["alpha"]), clopper_pearson_upper(kb, D, c["alpha"])
        rec = (sum(ev) / len(ev)) if ev else float("nan")
        res = {"D": D, "false_datasets": k, "upper_limit": up, "C1": bool(up <= c["max_upper_limit"]),
               "recall_events": len(ev), "recall_correct": int(sum(ev)), "recall": rec, "recall_ci": list(clopper_pearson(int(sum(ev)), len(ev))), "C2": bool(ev and rec >= c["min_recall"]),
               "baseline_false_datasets": kb, "baseline_upper_limit": upb, "baseline_C1": bool(upb <= c["max_upper_limit"]), "C3": bool(upb > c["max_upper_limit"]),
               "baseline_recall": (sum(evb) / len(evb)) if evb else float("nan")}
        out["arms"][arm] = res
        for key, name in (("C1", "calibration"), ("C2", "usefulness"), ("C3", "necessity")):
            if not res[key]:
                ok_all = False
                failed.append((arm, name))
    out["void"] = False
    out["contribution"] = bool(ok_all)
    out["failed_conditions"] = failed
    out["failure_sentences"] = [thr["future_version_wording"]["failure"][n] for n in sorted({n for _, n in failed}, key=("calibration", "usefulness", "necessity").index)]
    return out


# ------------------------------------------------------------------------------------------------ the guard of the statistics step
def require_calibration(directory, thresholds_pin, calibration_sha256, frozen_commit, thr=None):
    """the guard of the statistics step: edge-level law wording needs the calibration record. thresholds_pin and calibration_sha256 are MANDATORY arguments; the file must hash to
    calibration_sha256, carry the FROZEN commit, the thresholds hash in force (= the pin) and the rule hash in force, and hold a non-void verdict. Returns the calibration dict."""
    if not thresholds_pin:
        raise AuditGuardError("audit_thresholds_pin is mandatory when edge-level wording is requested")
    if not calibration_sha256:
        raise AuditGuardError("calibration_sha256 is mandatory when edge-level wording is requested")
    if not frozen_commit:
        raise AuditGuardError("no FROZEN commit: edge-level wording needs a verified freeze to compare the calibration commit with")
    p = os.path.join(directory, CALIBRATION_FILE)
    if not os.path.exists(p):
        raise AuditGuardError(f"no calibration record in {directory}: the statistics step does not print edge-level law wording (it prints the law only)")
    if sha256_file(p) != calibration_sha256:
        raise AuditGuardError("calibration.json does not hash to the supplied calibration_sha256 (altered, or another file)")
    cal = json.load(open(p, encoding="utf8"))
    cur = thresholds_sha256()
    if thresholds_pin != cur or cal.get("thresholds_sha256") != cur:
        raise AuditGuardError("the calibration was made with other thresholds than the ones pinned and in force (extraction_audit.json hash)")
    if cal.get("rule_sha256") != rule_sha256():
        raise AuditGuardError("the calibration was made with another rule file than calibration_rule_v2.md in force")
    if cal.get("commit") != frozen_commit:
        raise AuditGuardError(f"the calibration record's commit {str(cal.get('commit'))[:10]} is not the FROZEN commit {frozen_commit[:10]}")
    v = cal.get("verdict")
    if not v or v.get("void"):
        raise AuditGuardError("the calibration is void (fewer than the minimum number of complete datasets): section 5 of the judge file applies, no edge-level wording")
    return cal


# ------------------------------------------------------------------------------------------------ D021 regression
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
