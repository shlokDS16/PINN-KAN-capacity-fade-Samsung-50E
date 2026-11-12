"""Builds runs/post_review/RESULTS_SUMMARY.md and runs/post_review/RESULTS_SUMMARY.json from the files under runs/post_review/<exp>/ and the frozen run files. POST-HOC, EXPLORATORY (D048).
Every number in the markdown is computed here from a results file; nothing is typed in. No interpretation is written. Plain python + numpy (no torch).
Usage: python -P summarize.py"""
import glob
import json
import math
import os
import sys

import numpy as np

MAIN = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
WT = r"C:\Users\Shlok\Downloads\PINN KAN battery paper-frozen"
OUT = os.path.join(MAIN, "runs", "post_review")
RUNS = os.path.join(MAIN, "runs")
KSEL = {8: "2", 32: "full"}
GN = {8: "g1", 32: "g4"}
FOLDS = range(5)
SUMMARY = {}


def J(p):
    return json.load(open(p, encoding="utf8"))


# ---------------------------------------------------------------- frozen references
def frozen_scores(f, m, arm, endpoint="ens"):
    d = os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}")
    k = KSEL[m]
    if endpoint == "ens":
        name = "condition_scores.json" if k == "full" else f"condition_scores_k{k}.json"
    else:
        name = "condition_scores_seed.json" if k == "full" else f"condition_scores_seed_k{k}.json"
    return J(os.path.join(d, name))[arm]


def dstar_arm(f, m):
    return J(os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}", "comparators.json"))["D*"]["arm"]


def ref_all(m, arm, endpoint="ens"):
    out = {}
    for f in FOLDS:
        out.update(frozen_scores(f, m, arm, endpoint))
    return out


def dstar_all(m, endpoint="ens"):
    out = {}
    for f in FOLDS:
        out.update(frozen_scores(f, m, dstar_arm(f, m), endpoint))
    return out


# ---------------------------------------------------------------- variant files
def jd(exp, variant, f, m):
    return os.path.join(OUT, exp, f"{variant}_f{f}_m{m}")


def has(exp, variant, f, m):
    return os.path.exists(os.path.join(jd(exp, variant, f, m), "condition_scores.json"))


def variant_scores(exp, variant, m, arm, endpoint="ens", fallback=None):
    """-> (cond->score over the 5 folds, list of folds substituted by fallback(f) (a dict) or missing)"""
    out, subs, missing = {}, [], []
    for f in FOLDS:
        if has(exp, variant, f, m):
            name = "condition_scores_ens_k%s.json" % KSEL[m] if endpoint == "ens" else "condition_scores_seed_k%s.json" % KSEL[m]
            out.update(J(os.path.join(jd(exp, variant, f, m), name))[arm])
        elif fallback is not None:
            out.update(fallback(f))
            subs.append(f)
        else:
            missing.append(f)
    return out, subs, missing


def ms(d):
    v = np.array(list(d.values()), float)
    return (float(np.median(v)), float(np.mean(v)), len(v)) if len(v) else (float("nan"), float("nan"), 0)


def pair(a, b):
    """a, b dict cond->score. -> median ln(a/b), mean ln(a/b), n a better (<), n a worse (>), n ties, n"""
    c = sorted(set(a) & set(b))
    if not c:
        return (float("nan"),) * 2 + (0, 0, 0, 0)
    L = np.array([math.log(a[x] / b[x]) for x in c])
    return float(np.median(L)), float(np.mean(L)), int((L < 0).sum()), int((L > 0).sum()), int((L == 0).sum()), len(c)


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "n/a"
    return f"{x:.{nd}f}"


def md_table(headers, rows):
    s = "| " + " | ".join(headers) + " |\n|" + "|".join(["---"] * len(headers)) + "|\n"
    for r in rows:
        s += "| " + " | ".join(str(x) for x in r) + " |\n"
    return s


def perf_rows(entries, m, a1, ds):
    """entries: list of (label, cond->score, note). -> rows [label, n, median, mean, vs A1 (median ln ratio; better/worse), vs D* (...), note]"""
    rows = []
    for lab, sc, note in entries:
        md, mn, n = ms(sc)
        p1, p2 = pair(sc, a1), pair(sc, ds)
        rows.append([lab, n, fmt(md), fmt(mn), f"{fmt(p1[0])} ; {p1[2]}/{p1[3]}/{p1[4]}", f"{fmt(p2[0])} ; {p2[2]}/{p2[3]}/{p2[4]}", note])
    return rows


PH = ["variant", "n cond", "median RMSE pp", "mean RMSE pp", "vs A1 frozen: median ln ratio ; better/worse/tie", "vs D* frozen: median ln ratio ; better/worse/tie", "note"]
KEYDOC = ("Score = condition RMSE in percentage points (the frozen primary endpoint: cell RMSE over the forecast set, averaged within condition; ensemble of the five seeds unless stated). "
          "g1 = m 8 training conditions scored at k = 2; g4 = m 32 scored at k = full; 40 held-out conditions over the five outer folds. 'ln ratio' = ln(variant / reference) per condition, "
          "negative = the variant has the lower error; better/worse/tie = number of conditions with ln ratio below / above / equal to 0. No test or interval is computed here.")


def sub_note(subs, missing):
    s = []
    if subs:
        s.append(f"folds {subs} = frozen-equal setting (scores of the reference rerun L0)")
    if missing:
        s.append(f"MISSING folds {missing}")
    return "; ".join(s)


# ---------------------------------------------------------------- diagnostics
def diag_agg(exp, variant, m, fallback_variant=None):
    """medians over (fold, seed) of the per-fit diagnostics and the law-readout condition scores (mean over seeds per condition)"""
    res = {k: [] for k in ("res_share", "F_minus_law_rms_pp", "heldout_rel_R_median", "heldout_abs_R_median", "lam_final", "delta_sd_over_tau", "train_res_msq", "train_data_mse", "inversion_nonconverged")}
    law = {}
    for f in FOLDS:
        v = variant if has(exp, variant, f, m) else fallback_variant
        p = os.path.join(jd(exp, v, f, m), "diagnostics.json") if v else None
        if not p or not os.path.exists(p):
            continue
        dd = J(p)
        for d in dd:
            for k in res:
                if k in d:
                    res[k].append(d[k])
        conds = dd[0]["law_cond_scores"].keys()
        for c in conds:
            law[c] = float(np.mean([d["law_cond_scores"][c] for d in dd]))
    out = {k: (float(np.median(v)) if v else float("nan")) for k, v in res.items()}
    out["n_fits"] = len(res["res_share"])
    out["law_median"], out["law_mean"], out["law_n"] = ms(law) if law else (float("nan"),) * 2 + (0,)
    out["law_scores"] = law
    return out


# ---------------------------------------------------------------- checks
def checks():
    rows = []
    for m in (8, 32):
        mx, n = 0.0, 0
        for f in FOLDS:
            if has("item2_lambda", "L0", f, m):
                a = J(os.path.join(jd("item2_lambda", "L0", f, m), f"condition_scores_ens_k{KSEL[m]}.json"))["A1"]
                b = frozen_scores(f, m, "A1")
                for c in b:
                    mx = max(mx, abs(a[c] - b[c]))
                    n += 1
        rows.append(["A1 reference rerun L0 vs frozen A1 (ensemble, all conditions)", GN[m], n, f"{mx:.3e}"])
    for m in (8, 32):
        mx, n = 0.0, 0
        for f in FOLDS:
            for arm_n, exp, v in (("A2", "item6_h", None),):
                pass
        rows.append([])
    rows = [r for r in rows if r]
    V0 = sorted(glob.glob(os.path.join(OUT, "_harness", "V0_f*_m*.json")))
    for p in V0:
        d = J(p)
        rows.append([f"V0 outer-test predictions, fold {d['fold']} m {d['m']}, seed 0, k in (0, 2, full): " + ", ".join(f"{a}:{v['max_abs_diff']:.1e}" for a, v in d["arms"].items()), "", "", "all pass" if all(v["pass"] for v in d["arms"].values()) else "FAIL"])
    return rows


# ---------------------------------------------------------------- item 2
def item2(out):
    exp = "item2_lambda"
    S = {}
    out.append("## Item 2 - residual weight lambda (A1)\n")
    out.append("Variants: L0 = A1 rerun at the tuned lambda (identity check); Lfix = lambda fixed at 1e-2, 1e-1, 1, 10 in training and in the test-time inversion, every other hyperparameter as tuned "
               "(at the frozen, low lambda; this is not the best attainable error at a higher lambda); Lbalance = gradient-norm balancing (new exploratory training rule, simplification of the idea of "
               "Wang, Teng and Perdikaris; lambda updated every 10 steps by 0.9 lambda + 0.1 ||g_data|| / ||g_res||, clamp [1e-3, 1e2], frozen warm-up ramp, starts at the tuned lambda); "
               "Lanneal = lambda annealed log-linearly from 1e-3 to 1 over all steps (inversion at lambda = 1). Seeds 0-4, same folds, windows, backbone and other hyperparameters as the frozen A1 of each fold.\n")
    out.append(KEYDOC + "\n")
    tuned = {(f, m): J(os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}", "tuning_done.json"))["arms"]["A1"]["best_hp"]["lam_res"] for f in FOLDS for m in (8, 32)}
    out.append("Tuned lambda of the frozen A1 by outer fold (m 8 | m 32): " + "; ".join(f"f{f}: {tuned[(f, 8)]:g} | {tuned[(f, 32)]:g}" for f in FOLDS) +
               ". A fixed-lambda variant equal to the tuned value of a fold is not rerun; that fold's scores are those of L0 (marked in the note column).\n")
    names = [("L0", "L0 reference rerun"), ("Lfix1e-2", "lambda 1e-2"), ("Lfix1e-1", "lambda 1e-1"), ("Lfix1", "lambda 1"), ("Lfix10", "lambda 10"), ("Lbalance", "gradient-norm balancing"), ("Lanneal", "annealing 1e-3 to 1")]
    for m in (8, 32):
        a1, ds = ref_all(m, "A1"), dstar_all(m)
        ents = [("A1 as frozen (tuned lambda)", a1, "reference"), ("D* as frozen (inner-CV choice of A9/A11/A12)", ds, "reference")]
        L0fb = lambda f, m=m: J(os.path.join(jd(exp, "L0", f, m), f"condition_scores_ens_k{KSEL[m]}.json"))["A1"] if has(exp, "L0", f, m) else {}
        for v, lab in names:
            sc, subs, miss = variant_scores(exp, v, m, "A1", "ens", fallback=(L0fb if v.startswith("Lfix") else None))
            ents.append((lab, sc, sub_note(subs, miss)))
        out.append(f"### Table 2{'a' if m == 8 else 'b'}. {GN[m]} (m {m}, k {KSEL[m]}): condition RMSE and paired differences\n")
        out.append(md_table(PH, perf_rows(ents, m, a1, ds)))
        S[GN[m]] = {e[0]: {"n": ms(e[1])[2], "median": ms(e[1])[0], "mean": ms(e[1])[1]} for e in ents}
    out.append("### Table 2c. Residual and law-consistency diagnostics (medians over fold x seed fits; law readout over the 40 conditions)\n")
    out.append("res_share = lambda x train residual mean square / (train data MSE + lambda x train residual mean square) at the end of training; F-law gap = RMS (pp) of the F forecast minus the forecast of the "
               "law A1 learned, read out in closed form from its own window (hard-ODE readout, no F, no z); rel |R| = median over held-out forecast points of |dF/dt - law rhs| / |law rhs| at the inferred latents; "
               "law readout = condition RMSE (pp) of that closed-form law forecast (mean over the five seeds per condition).\n")
    rows = []
    for m in (8, 32):
        for v, lab in names:
            fb = "L0" if v.startswith("Lfix") else None
            d = diag_agg(exp, v, m, fb)
            rows.append([GN[m], lab, d["n_fits"], f"{d['lam_final']:.3g}", fmt(d["res_share"], 4), f"{d['train_res_msq']:.3g}", f"{d['train_data_mse']:.3g}", fmt(d["F_minus_law_rms_pp"]), fmt(d["heldout_rel_R_median"], 4), fmt(d["law_median"]), fmt(d["law_mean"]),
                         fmt(d["delta_sd_over_tau"]), int(d["inversion_nonconverged"]) if np.isfinite(d["inversion_nonconverged"]) else "n/a"])
            S.setdefault("diag", {})[f"{GN[m]}|{v}"] = {k: val for k, val in d.items() if k != "law_scores"}
    out.append(md_table(["cell", "variant", "fits", "lambda (final, median)", "res_share", "train res MS", "train data MSE", "F-law gap RMS pp", "rel |R| median", "law readout median RMSE pp", "law readout mean RMSE pp",
                         "delta SD/tau", "non-converged inversions (median per fit)"], rows))
    # step 0: inner-CV profile over lambda from the stored TPE trials
    out.append("### Table 2d. Inner-CV profile over lambda from the stored tuning trials (frozen files tuning_A1.json; TPE samples unevenly: a profile, not a controlled comparison)\n")
    rows = []
    for m in (8, 32):
        prof = {}
        for f in FOLDS:
            t = J(os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}", "tuning_A1.json"))["trials"]
            for tr in t:
                if tr.get("state") == "COMPLETE" and tr.get("value") is not None:
                    prof.setdefault(tr["params"]["lam_res"], []).append(tr["value"])
        for lam in sorted(prof):
            v = np.array(prof[lam])
            rows.append([GN[m], f"{lam:g}", len(v), fmt(float(v.min())), fmt(float(np.median(v)))])
    out.append(md_table(["cell", "lambda", "trials (5 folds pooled)", "best inner-CV pp", "median inner-CV pp"], rows))
    SUMMARY["item2"] = S


# ---------------------------------------------------------------- item 3
def item3(out):
    exp = "item3_zc"
    S = {}
    out.append("## Item 3 - prior weight on the per-cell latent z_c (A1 and A9)\n")
    out.append("Variants: z prior weight w in {10, 100, 1e4} (w = 1 is the frozen model) applied in the training loss and in the test-time inversion; A1 with its tuned hyperparameters (frozen backbone, lambda), "
               "A9 (data-only solution network with z_c, no law) with its tuned hyperparameters. Read as sensitivity of the window-inference channel: z_c is the only channel through which the window "
               "enters the A1 forecast F(t, s, z_c) (delta_c acts only inside the residual of the inversion), so a large w removes window conditioning of F, not only per-cell flexibility. "
               "The law readout of A1 is in Table 3b.\n")
    out.append(KEYDOC + "\n")
    for m in (8, 32):
        a1, ds, a9 = ref_all(m, "A1"), dstar_all(m), ref_all(m, "A9")
        ents = [("A1 as frozen (w = 1)", a1, "reference"), ("A9 as frozen (w = 1)", a9, "reference"), ("D* as frozen", ds, "reference")]
        for w, ws in (("10", "10"), ("100", "100"), ("10000", "1e4")):
            for pre, arm, lab in (("Z1", "A1", "A1"), ("Z9", "A9", "A9")):
                sc, subs, miss = variant_scores(exp, f"{pre}_w{w}", m, arm, "ens")
                ents.append((f"{lab}, w = {ws}", sc, sub_note(subs, miss)))
        out.append(f"### Table 3{'a' if m == 8 else 'a2'}. {GN[m]} (m {m}, k {KSEL[m]}): condition RMSE and paired differences\n")
        out.append(md_table(PH, perf_rows(ents, m, a1, ds)))
        S[GN[m]] = {e[0]: {"n": ms(e[1])[2], "median": ms(e[1])[0], "mean": ms(e[1])[1]} for e in ents}
    out.append("### Table 3b. A1 diagnostics by z weight (reference row = L0 of item 2 at w = 1); law readout = closed-form forecast of the law A1 learned (no F, no z_c)\n")
    rows = []
    for m in (8, 32):
        for lab, e, v in (("w = 1 (L0)", "item2_lambda", "L0"), ("w = 10", exp, "Z1_w10"), ("w = 100", exp, "Z1_w100"), ("w = 1e4", exp, "Z1_w10000")):
            d = diag_agg(e, v, m)
            rows.append([GN[m], lab, d["n_fits"], fmt(d["res_share"], 4), fmt(d["F_minus_law_rms_pp"]), fmt(d["heldout_rel_R_median"], 4), fmt(d["law_median"]), fmt(d["law_mean"]), fmt(d["delta_sd_over_tau"]), fmt(d["train_data_mse"] ** 0.5 * 100, 3)])
            S.setdefault("diag", {})[f"{GN[m]}|{lab}"] = {k: val for k, val in d.items() if k != "law_scores"}
    out.append(md_table(["cell", "z weight", "fits", "res_share", "F-law gap RMS pp", "rel |R| median", "law readout median RMSE pp", "law readout mean RMSE pp", "delta SD/tau", "train data RMSE (y units x 100, median)"], rows))
    SUMMARY["item3"] = S


# ---------------------------------------------------------------- item 5
def item5(out):
    exp = "item5_cap"
    S = {}
    out.append("## Item 5 - extraction library cap (A15 and G15)\n")
    out.append("Frozen: per-edge cap of 2 coefficients (zero, linear, log eligible). Variants: cap 3 (every family of the frozen library eligible: quadratic, power, exponential, Arrhenius, hinge added; same BIC rule and "
               "tolerance); the untruncated ceiling (every edge kept as its spline, A15 only; equals the parent KAN to float tolerance, then the same end-to-end refit). Hyperparameters as tuned at cap 2; seeds 0-4; "
               "parent plus refit = the steps of one A1 fit. Two endpoints are shown: the five-seed ensemble (frozen condition_scores.json) and the per-seed mean of condition RMSE (the endpoint of the frozen K chain). "
               "'within 10 %' = number of conditions with ln(variant / A1) <= ln 1.10 (a descriptive count, not the frozen K1 test).\n")
    out.append(KEYDOC + "\n")
    for m in (8, 32):
        for ep in ("ens", "seed"):
            a1, ds = ref_all(m, "A1", ep), dstar_all(m, ep)
            ents = [("A1 as frozen", a1, "reference"), ("D* as frozen", ds, "reference"), ("A15 cap 2 (frozen)", ref_all(m, "A15", ep), "frozen"), ("G15 cap 2 (frozen)", ref_all(m, "G15", ep), "frozen")]
            for v, arm, lab in (("A15_cap3", "A15", "A15 cap 3"), ("G15_cap3", "G15", "G15 cap 3"), ("A15_untrunc", "A15", "A15 untruncated")):
                sc, subs, miss = variant_scores(exp, v, m, arm, ep)
                ents.append((lab, sc, sub_note(subs, miss)))
            rows = perf_rows(ents, m, a1, ds)
            for r, e in zip(rows, ents):
                p = pair(e[1], a1)
                c = sorted(set(e[1]) & set(a1))
                r.append(int(sum(math.log(e[1][x] / a1[x]) <= math.log(1.10) for x in c)) if c else "n/a")
            out.append(f"### Table 5{'a' if m == 8 else 'b'}{'' if ep == 'ens' else ' (per-seed endpoint)'}. {GN[m]}: {'ensemble endpoint' if ep == 'ens' else 'per-seed endpoint'}\n")
            out.append(md_table(PH + ["conditions within 10 % of A1"], rows))
            S.setdefault(GN[m] + "|" + ep, {k: {"median": ms(sc)[0], "mean": ms(sc)[1]} for k, sc, _ in ents})
    out.append("### Table 5c. K2-style: A15 variants against G15 at the same cap (per-seed endpoint, ln(A15 / G15) per condition)\n")
    rows = []
    for m in (8, 32):
        for lab, a, g in (("cap 3", ("A15_cap3", "A15"), ("G15_cap3", "G15")), ("A15 untruncated vs G15 cap 3", ("A15_untrunc", "A15"), ("G15_cap3", "G15"))):
            A, _, _ = variant_scores(exp, a[0], m, a[1], "seed")
            G, _, _ = variant_scores(exp, g[0], m, g[1], "seed")
            p = pair(A, G)
            rows.append([GN[m], lab, p[5], fmt(p[0]), f"{p[2]}/{p[3]}/{p[4]}"])
        A, G = ref_all(m, "A15", "seed"), ref_all(m, "G15", "seed")
        p = pair(A, G)
        rows.append([GN[m], "cap 2 (frozen)", p[5], fmt(p[0]), f"{p[2]}/{p[3]}/{p[4]}"])
    out.append(md_table(["cell", "pair", "n cond", "median ln(A15/G15)", "A15 better/worse/tie"], rows))
    out.append("### Table 5d. Law size, training BIC, families and fit (extras.json of each job; medians over fold x seed laws)\n")
    rows = []
    for m in (8, 32):
        for v in ("A15_cap3", "G15_cap3", "A15_untrunc"):
            ex = []
            for f in FOLDS:
                p = os.path.join(jd(exp, v, f, m), "extras.json")
                if os.path.exists(p):
                    ex += J(p)
            if not ex:
                rows.append([GN[m], v, 0, "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"])
                continue
            fam = {}
            for e in ex:
                for k, c in e["family_counts"].items():
                    fam[k] = fam.get(k, 0) + c
            rows.append([GN[m], v, len(ex), f"{np.median([e['n_coefs'] for e in ex]):.0f}", fmt(float(np.nanmedian([e["train_bic"] for e in ex])), 1), f"{np.median([e['n_quadratic_edges'] for e in ex]):.0f}",
                         f"{np.median([e['n_hinge_edges'] for e in ex]):.0f}", f"{int(sum(e['refit_diverged'] for e in ex))} diverged; {int(sum(bool(e.get('predict_failure')) for e in ex))} inversion failures scored as persistence", ", ".join(f"{k}:{c}" for k, c in sorted(fam.items()))])
        for arm in ("A15", "G15"):
            ex = []
            for f in FOLDS:
                p = os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}", "extracted_laws.json")
                if os.path.exists(p):
                    ex.append(J(p))
            rows.append([GN[m], f"{arm} cap 2 (frozen): files extracted_laws.json", len(ex), "see file", "see file", "-", "-", "-", "-"])
    out.append(md_table(["cell", "variant", "laws", "median n coefficients", "median train BIC", "median quadratic edges", "median hinge edges", "refits diverged; failed inversions (non-finite forecast, persistence rule)", "edge families (total over laws)"], rows))
    SUMMARY["item5"] = S


# ---------------------------------------------------------------- item 6
def item6(out):
    exp = "item6_h"
    S = {}
    members = ["const", "sl4", "sl2", "sl1", "sl0.5", "acc0.15", "acc0.3", "acc0.6"]
    desc = {"const": "constant", "sl4": "self-limiting Y0 4", "sl2": "self-limiting Y0 2", "sl1": "self-limiting Y0 1 (frozen scale)", "sl0.5": "self-limiting Y0 0.5", "acc0.15": "accelerating gamma 0.15",
            "acc0.3": "accelerating gamma 0.3 (frozen scale)", "acc0.6": "accelerating gamma 0.6"}
    frozen_m = {"constant": "const", "self_limiting": "sl1", "accelerating": "acc0.3"}
    out.append("## Item 6 - discrete grid for the state factor h(y)\n")
    out.append("Grid (8 members): constant; self-limiting 1/(1 + y/Y0) with Y0 in {4, 2, 1, 0.5}; accelerating exp(gamma y) with gamma in {0.15, 0.3, 0.6} (y in the model's y_s units). Applied with the frozen context manager "
               "law.overrides. A2 (law only, h binds fully) is refit with its tuned hyperparameters for all 8 members; A1 (tuned hyperparameters, tuned lambda) for the members that differ from the fold's frozen "
               "backbone (the member equal to the fold's frozen backbone is A1 as frozen). 'Inner-fold choice' = the frozen backbone tournament (A2 at default settings on the inner folds of the training "
               "conditions, simplest member within one SE of the best) extended to the 8 members, simplicity order constant, Y0 4, 2, 1, 0.5, gamma 0.15, 0.3, 0.6; the held-out score of the chosen member is read "
               "from the grid runs. This is a discrete choice from the explored grid, not a learned h.\n")
    out.append(KEYDOC + "\n")
    tour = {(f, m): J(os.path.join(jd(exp, "TOURN", f, m), "tournament.json")) for f in FOLDS for m in (8, 32) if os.path.exists(os.path.join(jd(exp, "TOURN", f, m), "tournament.json"))}
    for m in (8, 32):
        a1, ds, a2f = ref_all(m, "A1"), dstar_all(m), ref_all(m, "A2")
        for arm in ("A2", "A1"):
            ents = [("A1 as frozen", a1, "reference"), ("D* as frozen", ds, "reference")]
            if arm == "A2":
                ents.insert(1, ("A2 as frozen (fold's tournament backbone)", a2f, "reference"))
            for mem in members:
                if arm == "A1":
                    def fb(f, m=m, mem=mem):
                        bb = J(os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}", "tuning_done.json"))["backbone"]
                        return frozen_scores(f, m, "A1") if frozen_m[bb] == mem else None
                    out_sc, miss = {}, []
                    subs = []
                    for f in FOLDS:
                        if has(exp, f"A1_{mem}", f, m):
                            out_sc.update(J(os.path.join(jd(exp, f"A1_{mem}", f, m), f"condition_scores_ens_k{KSEL[m]}.json"))["A1"])
                        else:
                            r = fb(f)
                            if r is not None:
                                out_sc.update(r)
                                subs.append(f)
                            else:
                                miss.append(f)
                    ents.append((f"A1, {desc[mem]}", out_sc, sub_note(subs, miss).replace("frozen-equal setting (scores of the reference rerun L0)", "= the fold's frozen backbone (A1 as frozen)")))
                else:
                    sc, subs, miss = variant_scores(exp, f"A2_{mem}", m, "A2", "ens")
                    ents.append((f"A2, {desc[mem]}", sc, sub_note(subs, miss)))
            out.append(f"### Table 6{'a' if m == 8 else 'b'}{'' if arm == 'A2' else '-A1'}. {GN[m]} (m {m}, k {KSEL[m]}): {arm} over the h grid\n")
            out.append(md_table(PH, perf_rows(ents, m, a1, ds)))
            S[f"{GN[m]}|{arm}"] = {e[0]: {"median": ms(e[1])[0], "mean": ms(e[1])[1], "n": ms(e[1])[2]} for e in ents}
        # inner-fold choice
        ch = {f: tour[(f, m)]["chosen"] for f in FOLDS if (f, m) in tour}
        if len(ch) == 5:
            for arm in ("A2", "A1"):
                sc = {}
                for f in FOLDS:
                    mem = ch[f]
                    if arm == "A2":
                        sc.update(J(os.path.join(jd(exp, f"A2_{mem}", f, m), f"condition_scores_ens_k{KSEL[m]}.json"))["A2"])
                    else:
                        bb = J(os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}", "tuning_done.json"))["backbone"]
                        if frozen_m[bb] == mem:
                            sc.update(frozen_scores(f, m, "A1"))
                        else:
                            sc.update(J(os.path.join(jd(exp, f"A1_{mem}", f, m), f"condition_scores_ens_k{KSEL[m]}.json"))["A1"])
                S[f"{GN[m]}|{arm}|inner_fold_choice"] = {"median": ms(sc)[0], "mean": ms(sc)[1]}
                p1, p2 = pair(sc, a1), pair(sc, ds)
                out.append(f"Inner-fold choice at {GN[m]}, {arm}: median {fmt(ms(sc)[0])} pp, mean {fmt(ms(sc)[1])} pp; vs A1 frozen median ln ratio {fmt(p1[0])} (better/worse/tie {p1[2]}/{p1[3]}/{p1[4]}); vs D* {fmt(p2[0])} ({p2[2]}/{p2[3]}/{p2[4]}). "
                           f"Chosen member by fold: " + ", ".join(f"f{f}: {ch[f]}" for f in FOLDS) + ".\n")
    out.append("### Table 6c. Inner-CV tournament over the 8 members (A2 at default settings; mean inner-CV RMSE pp, training conditions only) and the frozen tournament choice\n")
    rows = []
    for (f, m), t in sorted(tour.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        rows.append([GN[m], f, ", ".join(f"{k} {t['table'][k]['mean_pp']:.2f}" for k in members), t["chosen"], t["frozen_tournament_choice"],
                     f"{max(v['abs_diff'] for v in t['frozen_members_reproduced'].values()):.1e}"])
    out.append(md_table(["cell", "fold", "inner-CV mean RMSE pp by member", "chosen (8-member rule)", "frozen choice (3-member)", "max abs diff to frozen tournament table (3 frozen members)"], rows))
    out.append("### Table 6d. Retention loss at the last scored check-up of the held-out cells (y_s = y_scale x (1 - retention); h's reference scale is Y0 = 1)\n")
    rows = []
    for (f, m), t in sorted(tour.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        y = t["last_checkup_y_distribution"]
        rows.append([GN[m], f, y["n_cells"], ", ".join(f"{x:.3f}" for x in y["y_s_last_checkup_quantiles_0_25_50_75_100"]), fmt(y["share_y_s_above_0.5"]), fmt(y["share_y_s_above_1"])])
    out.append(md_table(["cell", "fold", "scored cells", "y_s at last check-up: min, Q1, median, Q3, max", "share y_s > 0.5", "share y_s > 1"], rows))
    SUMMARY["item6"] = S


# ---------------------------------------------------------------- item 7
def item7(out):
    exp = "item7_nc2"
    d0 = os.path.join(OUT, exp)
    out.append("## Item 7 - NC-2 over stress-permutation draws\n")
    if not os.path.isdir(d0):
        out.append("NOT RUN (no files).\n")
        return
    sys.path.insert(0, os.path.join(WT, "code"))
    os.environ["PINNKAN_ROOT"] = WT
    from pinnkan import stats_v4  # frozen sign rule
    rule = stats_v4.SignRule("betabin", 0.03)
    plain = stats_v4.PLAIN
    real = ref_all(32, "A1")
    out.append("Variant F (full pipeline repeated per draw and outer fold: backbone tournament, A1 tuning N = 40 on the permuted training side, five refits, ensemble forecast of the permuted test side, m 32, k full). "
               "L_c = ln(S_permuted,c / S_real,c) paired by condition against A1 on real stress at g4 (frozen condition scores). The sign test is the frozen design-effect rule (Beta-binomial, rho_s0 = 0.03, "
               "one-sided, alpha 0.025; ties not positive, n not reduced) applied unchanged; 'plain' = independent-conditions exact sign test (descriptive). The frozen NC-2 result (28 of 40, p 0.054) is draw 0 of the original run "
               "and stays as frozen; this table only adds draws. A randomisation p-value over S draws cannot go below 1/(S + 1).\n")
    donor = os.path.join(d0, "DONOR_CHECK.json")
    if os.path.exists(donor):
        dc = J(donor)
        out.append(f"Donor identity check (draw 0 of the wrapped permutation equals the frozen metrics.permute_stress for all five folds, train and test sides): {dc['all_identical']} (file DONOR_CHECK.json).\n")
    rows, allL, ks, ps = [], {}, [], []
    draws = sorted({int(os.path.basename(p).split("_f")[0][4:]) for p in glob.glob(os.path.join(d0, "draw*_f*"))})
    for s in draws:
        sc = {}
        miss = []
        for f in FOLDS:
            p = os.path.join(d0, f"draw{s}_f{f}", "condition_scores.json")
            if os.path.exists(p):
                sc.update(J(p)["A1"])
            else:
                miss.append(f)
        if miss:
            rows.append([s, "incomplete", f"missing folds {miss}", "", "", "", ""])
            continue
        conds = sorted(real)
        L = np.array([math.log(sc[c] / real[c]) for c in conds])
        pos, n, p = rule.test(L, 0.0)
        pl, nl, pp_ = plain.test(L, 0.0)
        allL[s] = L
        rows.append([s, f"{pos}/{n}", f"{p:.4f}", f"{pl}/{nl}; {pp_:.4f}", fmt(float(np.median(L))), fmt(float(np.exp(np.median(L)) - 1) * 100, 1), fmt(float(np.mean(list(sc.values()))))])
        if s >= 1:
            ks.append(pos)
            ps.append(p)
    out.append(md_table(["draw (0 = frozen stream rerun)", "k positive / n", "p (frozen rule, rho 0.03)", "plain exact: k/n; p", "median L", "median relative increase %", "mean permuted RMSE pp"], rows))
    SUMMARY["item7"] = {"draws": draws, "k": ks, "p": ps}
    if 0 in allL:
        mx, n = 0.0, 0
        for f in FOLDS:
            fz = J(os.path.join(RUNS, f"conf_samsung_B_f{f}_m32_nc2", "condition_scores.json"))["A1"]
            dd = J(os.path.join(d0, f"draw0_f{f}", "condition_scores.json"))["A1"] if os.path.exists(os.path.join(d0, f"draw0_f{f}", "condition_scores.json")) else {}
            for c in fz:
                if c in dd:
                    mx, n = max(mx, abs(fz[c] - dd[c])), n + 1
        out.append(f"Reproduction check: draw 0 of this harness against the frozen NC-2 runs (conf_samsung_B_f*_m32_nc2): {n} conditions, max abs difference in condition RMSE {mx:.3e} pp.\n")
        SUMMARY["item7"]["draw0_max_abs_diff"] = mx
    if ks:
        ks_a, ps_a = np.array(ks), np.array(ps)
        out.append(f"Distribution over the {len(ks)} new draws: k positive min {ks_a.min()}, median {np.median(ks_a):g}, max {ks_a.max()}; p min {ps_a.min():.4f}, median {np.median(ps_a):.4f}, max {ps_a.max():.4f}; "
                   f"draws with p <= 0.025: {int((ps_a <= 0.025 * (1 + 1e-9)).sum())} of {len(ks)}; draws with k >= 30: {int((ks_a >= 30).sum())} of {len(ks)}. "
                   f"Frozen draw: k 28, p 0.0539 (controls.json).\n")
        Lm = np.mean([allL[s] for s in allL if s >= 1], axis=0)
        pos, n, p = rule.test(Lm, 0.0)
        out.append(f"Seed-averaged line (mean of L_c over the {len(ks)} new draws, then the same sign test): {pos}/{n}, p {p:.4f}; median of the averaged L {np.median(Lm):.3f}.\n")
        SUMMARY["item7"]["averaged"] = {"k": int(pos), "n": int(n), "p": float(p)}


def main():
    out = ["# Post-review exploratory results (D048)\n",
           "POST-HOC, EXPLORATORY. Nothing here changes a confirmatory result (state P0, K=, M1-M3 false, NC-2 FAIL, title T5). Every variant that was run is listed, favourable or not. "
           "Generated by runs/post_review/_harness/summarize.py from the result files under runs/post_review/<exp>/ and the frozen run files of runs/conf_samsung_B_f*_m*/; no number is typed in and no "
           "arm is interpreted here. Statistics (intervals, tests, multiplicity) belong to the statistician: only descriptive medians, means, paired log ratios and counts are given.\n"]
    out.append("## Run integrity checks\n")
    out.append(md_table(["check", "cell", "n", "max abs difference / result"], checks()))
    for fn in (item2, item3, item5, item6, item7):
        try:
            fn(out)
        except Exception as e:  # noqa: BLE001
            import traceback
            out.append(f"\n**SUMMARY ERROR in {fn.__name__}: {type(e).__name__}: {e}**\n```\n{traceback.format_exc()}\n```\n")
    fails = glob.glob(os.path.join(OUT, "**", "FAILED.txt"), recursive=True)
    out.append("## Failed jobs\n")
    out.append("\n".join(f"- {os.path.relpath(p, OUT)}" for p in fails) if fails else "no job failed in its final attempt\n")
    first = glob.glob(os.path.join(OUT, "**", "FAILED_attempt1*.txt"), recursive=True)
    if first:
        out.append("\nFirst attempts that failed and were rerun after a wrapper fix (records kept on disk): " + "; ".join(os.path.relpath(os.path.dirname(p), OUT) for p in first) +
                   ". Cause: the frozen latent inversion raised LinAlgError on a diverged refit (non-finite parameters); the wrapper now returns non-finite forecasts for that fit, which are scored with the persistence error and counted "
                   "(frozen rule, PREREG_v4 6); the count is in Table 5d.\n")
    out.append("\n## Not run\n")
    out.append("- Item 8 (SNL Test B replication): not run, see snl/BLINDING_CHECK.md (SNL is labelled not blind in PREREG_v4 and was explored in pilots P1/P2 before its split).\n"
               "- Decided before results: re-tuning at higher lambda, pairwise symbolic terms, learned or spline h, any conformal method.\n"
               "- Not requested of this run: horizon-wise errors from stored predictions (item 1), seed-spread coverage (item 4), rho sweep (item 9).\n")
    open(os.path.join(OUT, "RESULTS_SUMMARY.md"), "w", encoding="utf8").write("\n".join(out))
    json.dump(SUMMARY, open(os.path.join(OUT, "RESULTS_SUMMARY.json"), "w", encoding="utf8"), indent=1, default=str)
    print("written", os.path.join(OUT, "RESULTS_SUMMARY.md"))


if __name__ == "__main__":
    main()

