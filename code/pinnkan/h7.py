"""H7 identifiability driver (PREREG_v3 section 13): generators G0-G2 x draws x arms A1, A2, A4, A8. Synthetic only.

Per draw: generate the dataset (truth never from a fit), compute the additive-GAM class floor of the TRUE log-rate surface before any fit (validity rule: a G2
draw discriminates only if the floor exceeds 0.15), hold out cycling conditions, tune every arm on the training conditions only (`n_trials` x `inner_k`, equal for
all arms; pilot effort 8 x 2 in the prereg), refit at the tuned settings, then evaluate on the fixed 500-point Latin hypercube inside the convex hull of the
training cycling design: nRMSE = RMSE(estimated - true log-rate) / range(true) (level included; centred value alongside) and the forecast RMSE on the held-out
conditions. Output: <run>/summary.json and <run>/surfaces_<gen>.npz (lhs raw stress, f_true and f_<arm>, centred, shape (draws, 500)).
Rates compared: log r_cyc of the structured arms (log_cyc + f) and, for the free G, log(G(y=0) / nu) at the design throughput (approximate, see free.log_rate_surface).

Batch (PREREG_v3 section 13; build_v1 RESULT section 7). Every (generator, draw) unit is written to <run>/draws/<gen>_<draw>.json (+ .npz with the surfaces) as soon as it
is finished; a rerun skips finished units (resumable after a crash), `shard=(k, n)` lets up to three processes share the 60 units, and `aggregate` builds summary.json,
surfaces_<gen>.npz and the verdicts of section 13 when every unit exists. The data-only learners A11 and A12 have no log-rate surface: they enter with the forecast RMSE
only (positive control P1 on G0). New per-draw metric: Kendall tau (tau-b) between the variance-based first-order importances of the five stress inputs, estimated surface vs
true surface on the same 500 hull points (`variance_importance`); it is diagnostic (the prereg gives it no threshold)."""
import json
import os

import numpy as np
import torch
from scipy import stats as sps

from . import free, synth, tuning
from .arms import make_arm
from .data import WindowRule, prepare_many
from .metrics import primary_score, score_prepared
from .pinn import _hull_sample
from .specs import SPECS

SPEC = SPECS["synthetic"]
ARMS_H7 = ("A1", "A2", "A4", "A8")
LEARNERS = ("A11", "A12")                       # data-only learners: forecast RMSE only
BATCH_ARMS = {"G0": ARMS_H7 + LEARNERS, "G1": ARMS_H7, "G2": ARMS_H7}      # P1 (G0) needs A11/A12; G1 and G2 carry the four arms of section 13
P1_ARMS = ("A1", "A2")                           # the structured arms of positive control P1 (prereg 10: "structured arms recover ... and beat A11/A12")
PASS_NRMSE, FAIL_NRMSE, FREE_RATIO, FLOOR_VALID, KAN_OVER_GAM_G0 = 0.15, 0.30, 0.67, 0.15, 1.10


def additive_floor(f_true, raw):
    """RMSE of the best additive cubic fit of the true surface / its range (computed before any model is fitted)"""
    s = SPEC.norm(raw)
    A = np.column_stack([np.ones(len(s))] + [s[:, j] ** p for j in range(s.shape[1]) for p in (1, 2, 3)])
    coef, *_ = np.linalg.lstsq(A, f_true, rcond=None)
    return float(np.sqrt(np.mean((A @ coef - f_true) ** 2)) / (f_true.max() - f_true.min()))


def surface(arm, raw):
    if arm.arm_id == "A8":
        return free.log_rate_surface(arm.model, SPEC, raw)
    law = arm.model.law
    with torch.no_grad():
        return (law.log_cyc + law.cyc(torch.tensor(SPEC.norm(raw), dtype=torch.float32))).numpy()


def variance_importance(f, raw, bins=10):
    """First-order variance importance S_j = Var_j(E[f | x_j]) / Var(f) of each stress input, estimated on the shared hull sample by `bins` equal-count bins of the raw
    input (the same estimator for the true and every estimated surface, so the tau compares like with like)."""
    f = np.asarray(f, float)
    raw = np.asarray(raw, float)
    v = f.var()
    out = []
    for j in range(raw.shape[1]):
        groups = np.array_split(np.argsort(raw[:, j], kind="stable"), bins)
        means = np.array([f[g].mean() for g in groups])
        w = np.array([len(g) for g in groups], float)
        grand = float(np.sum(w * means) / w.sum())
        out.append(float(np.sum(w * (means - grand) ** 2) / w.sum() / v) if v > 0 else 0.0)
    return out


def kendall_importance(f_est, f_true, raw):
    """-> (Kendall tau-b between the variance importances of the estimated and the true surface, importances_est, importances_true); tau is NaN when an importance vector is constant"""
    a, b = variance_importance(f_est, raw), variance_importance(f_true, raw)
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return float("nan"), a, b
    return float(sps.kendalltau(a, b).statistic), a, b


def run_unit(g, i, arms, n_trials, inner_k, steps_scale, backbone, design):
    """one draw of one generator -> (record, {name: centred surface (500,)}, lhs). Identical numerics to the earlier loop of run_h7."""
    rule = WindowRule.for_spec(SPEC)
    ctx = {"backbone": backbone, "steps_scale": steps_scale, "rule": rule}
    S = synth.make_synthetic(g, seed=i, backbone=backbone, **design)
    tr, te = synth.split_conditions(S.cells, 0.25, i)
    X = np.stack([SPEC.norm(c.raw) for c in tr if c.kind == "cycling"])
    lhs = SPEC.denorm(_hull_sample(X, 500, 12345))
    f_true = S.log_rate_cyc(lhs)
    floor = additive_floor(f_true, lhs)
    rng_t = float(f_true.max() - f_true.min())
    rec = dict(gen=g, draw=i, additive_floor=floor, additive_floor_discriminates=bool(floor > FLOOR_VALID), nrmse={}, nrmse_centred={}, kendall_tau={}, importance={"true": variance_importance(f_true, lhs)},
               forecast_pp={}, best_hp={})
    surfaces = {"true": f_true - f_true.mean()}
    prep = prepare_many([c for c in te if c.kind == "cycling"], rule)
    for a in arms:
        r = tuning.tune(a, tr, SPEC, rule, n_trials, inner_k, i, ctx)
        arm = make_arm(a, SPEC, r["best_hp"], 0, ctx).fit(tr)
        if a not in LEARNERS:
            f = surface(arm, lhs)
            rec["nrmse"][a] = float(np.sqrt(np.mean((f - f_true) ** 2)) / rng_t)
            fc, ft = f - f.mean(), f_true - f_true.mean()
            rec["nrmse_centred"][a] = float(np.sqrt(np.mean((fc - ft) ** 2)) / rng_t)
            tau, imp, _ = kendall_importance(f, f_true, lhs)
            rec["kendall_tau"][a], rec["importance"][a] = tau, imp
            surfaces[a] = fc
        rec["forecast_pp"][a] = primary_score(score_prepared(arm.predict([p.win for p in prep]), prep))
        rec["best_hp"][a] = r["best_hp"]
    return rec, surfaces, lhs


def _unit_paths(out_dir, g, i):
    d = os.path.join(out_dir, "draws")
    return os.path.join(d, f"{g}_{i:02d}.json"), os.path.join(d, f"{g}_{i:02d}.npz")


def run_h7(out_dir, gens=("G0", "G1", "G2"), n_draws=20, arms=ARMS_H7, n_trials=8, inner_k=2, steps_scale=1.0, backbone="self_limiting", design=None, shard=(0, 1), arms_by_gen=None):
    """Resumable, shardable driver. Without `arms_by_gen` every generator runs `arms`; the confirmatory batch passes `arms_by_gen="batch"` (BATCH_ARMS) or a dict.
    Finished units are skipped. When every unit exists the summary is built (`aggregate`), otherwise the return value says how many units are missing."""
    if arms_by_gen == "batch":
        arms_by_gen = BATCH_ARMS
    os.makedirs(os.path.join(out_dir, "draws"), exist_ok=True)
    open(os.path.join(out_dir, "SYNTHETIC"), "w").write("H7 generators: invented ageing laws\n")
    design = design or dict(n_cyc_cond=32, n_sto_cond=19, reps=3)
    k, n = shard
    units = [(g, i) for g in gens for i in range(n_draws)]
    for j, (g, i) in enumerate(units):
        if j % n != k:
            continue
        pj, pz = _unit_paths(out_dir, g, i)
        if os.path.exists(pj):
            continue
        a_g = tuple((arms_by_gen or {}).get(g, arms))
        rec, surfaces, lhs = run_unit(g, i, a_g, n_trials, inner_k, steps_scale, backbone, design)
        np.savez(pz, lhs=lhs, **{f"f_{k_}": v for k_, v in surfaces.items()})
        with open(pj, "w", encoding="utf8") as fh:          # written last: the json marks a finished unit
            json.dump(rec, fh, indent=1)
    meta = dict(synthetic=True, thresholds=dict(pass_=PASS_NRMSE, fail=FAIL_NRMSE), n_draws=n_draws, gens=list(gens), n_trials=n_trials, inner_k=inner_k, steps_scale=steps_scale,
                design=design, arms=list(arms), arms_by_gen={g: list(v) for g, v in (arms_by_gen or {}).items()})
    return aggregate(out_dir, meta, units)


def aggregate(out_dir, meta, units=None):
    """summary.json + surfaces_<gen>.npz from the finished unit files; adds the section-13 verdicts when every unit exists"""
    gens = meta["gens"]
    units = units or [(g, i) for g in gens for i in range(meta["n_draws"])]
    missing = [u for u in units if not os.path.exists(_unit_paths(out_dir, *u)[0])]
    if missing:
        return dict(complete=False, n_missing=len(missing), n_units=len(units))
    draws = []
    for g in gens:
        F, lhs_saved = {}, None
        for i in range(meta["n_draws"]):
            pj, pz = _unit_paths(out_dir, g, i)
            draws.append(json.load(open(pj, encoding="utf8")))
            z = np.load(pz)
            lhs_saved = z["lhs"]
            for key in z.files:
                if key.startswith("f_"):
                    F.setdefault(key[2:], []).append(z[key])
        np.savez(os.path.join(out_dir, f"surfaces_{g}.npz"), lhs=lhs_saved, **{f"f_{k}": np.stack(v) for k, v in F.items()})
    summ = dict(meta, draws=draws, complete=True)
    summ["verdicts"] = verdicts(summ)
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf8") as fh:
        json.dump(summ, fh, indent=1)
    return summ


# ------------------------------------------------------------------------------------------------ verdicts of PREREG_v3 section 13 (from per-draw records)
def _paired(draws, gen, a, b, key, alt):
    """paired one-sided Wilcoxon over the draws that carry both values; alt 'less' tests value(a) < value(b). -> (p, n, median a, median b)"""
    A = np.array([d[key][a] for d in draws if d["gen"] == gen and a in d[key] and b in d[key]], float)
    B = np.array([d[key][b] for d in draws if d["gen"] == gen and a in d[key] and b in d[key]], float)
    if len(A) == 0:
        return float("nan"), 0, float("nan"), float("nan")
    if len(A) < 2 or np.allclose(A, B):
        return 1.0, len(A), float(np.median(A)), float(np.median(B))
    return float(sps.wilcoxon(A, B, alternative=alt).pvalue), len(A), float(np.median(A)), float(np.median(B))


def _med(draws, gen, a, key="nrmse"):
    v = [d[key][a] for d in draws if d["gen"] == gen and a in d[key]]
    return float(np.median(v)) if v else float("nan")


def verdicts(summ):
    """Thresholds of section 13 (J section 6), from the per-draw records. Pass line: median nRMSE <= 0.15, fail > 0.30 (per arm and generator). Structured vs free: median
    nRMSE <= 0.67 x the free-G (A8) median AND paired one-sided Wilcoxon p < 0.05 (G1, G2; arms A1, A2, A4); 'structured' generically only if the GAM (A4) also meets it.
    G2: validity = median additive-GAM class floor of the TRUE surface > 0.15 (else KAN superiority cannot be claimed from G2 and the H3 'win' is unavailable); 'passes' =
    valid AND KAN meets the pass line AND KAN lower than the additive GAM (paired one-sided Wilcoxon p < 0.05). On G0 KAN not above GAM by more than 10 % (ratio of medians).
    Kendall tau is diagnostic."""
    dr = summ["draws"]
    gens = sorted({d["gen"] for d in dr})
    out = {"n_draws": {g: sum(d["gen"] == g for d in dr) for g in gens}, "alpha_wilcoxon": 0.05}
    out["recovery"] = {}
    for g in gens:
        out["recovery"][g] = {}
        for a in sorted({k for d in dr if d["gen"] == g for k in d["nrmse"]}):
            m = _med(dr, g, a)
            out["recovery"][g][a] = dict(median_nrmse=m, status="pass" if m <= PASS_NRMSE else ("fail" if m > FAIL_NRMSE else "between"))
    out["structured_vs_free"] = {}
    for g in ("G1", "G2"):
        if g not in gens or not any("A8" in d["nrmse"] for d in dr if d["gen"] == g):
            continue
        row = {}
        for a in ("A1", "A2", "A4"):
            p, n, ma, mb = _paired(dr, g, a, "A8", "nrmse", "less")
            row[a] = dict(median_ratio=ma / mb if mb else float("nan"), p_wilcoxon=p, n=n, meets=bool(ma <= FREE_RATIO * mb and p < 0.05))
        row["structured_generic"] = bool(row["A1"]["meets"] and row["A4"]["meets"])
        out["structured_vs_free"][g] = row
    if "G2" in gens:
        fl = [d["additive_floor"] for d in dr if d["gen"] == "G2"]
        p, n, mk, mg = _paired(dr, "G2", "A1", "A4", "nrmse", "less")
        g2 = dict(median_additive_floor=float(np.median(fl)), valid=bool(np.median(fl) > FLOOR_VALID), kan_median_nrmse=mk, gam_median_nrmse=mg, p_kan_lower_than_gam=p, n=n,
                  kan_lower_than_gam=bool(mk < mg and p < 0.05), kan_meets_pass_line=bool(mk <= PASS_NRMSE))
        g2["passes"] = bool(g2["valid"] and g2["kan_meets_pass_line"] and g2["kan_lower_than_gam"])
        out["G2"] = g2
    if "G0" in gens:
        ma, mb = _med(dr, "G0", "A1"), _med(dr, "G0", "A4")
        out["G0_kan_vs_gam"] = dict(kan=ma, gam=mb, ratio=ma / mb if mb else float("nan"), ok=bool(ma <= KAN_OVER_GAM_G0 * mb))
        out["P1"] = p1_positive_control(dr)
    if "G1" in gens:
        out["hard_vs_soft_G1"] = hard_vs_soft(dr, "G1")
    out["kendall_tau_median"] = {}
    for g in gens:
        out["kendall_tau_median"][g] = {}
        for a in sorted({k for d in dr if d["gen"] == g for k in d["kendall_tau"]}):
            v = [d["kendall_tau"][a] for d in dr if d["gen"] == g and a in d["kendall_tau"]]
            out["kendall_tau_median"][g][a] = float(np.nanmedian(v)) if np.isfinite(v).any() else float("nan")
    out["residual_map_claim"] = "not available: PREREG 13 requires a rank-correlation threshold set by the statistician before optional G3 runs; none exists, so Fig. 7 carries no claim"
    return out


def p1_positive_control(draws, gen="G0"):
    """Positive control P1 (prereg 10): on G0 each structured arm (A1, A2) recovers the log-rate surface with median nRMSE <= 0.15 and beats BOTH learners A11 and A12 on the
    forecast RMSE (paired one-sided Wilcoxon p < 0.05 over the draws). passed=None (not evaluated) when the learners are not in the run."""
    have = {k for d in draws if d["gen"] == gen for k in d["forecast_pp"]}
    if not set(LEARNERS) <= have:
        return dict(passed=None, reason="A11/A12 are not in this H7 run: use arms_by_gen='batch' (G0 needs the learners)")
    comp = {}
    for a in P1_ARMS:
        row = dict(median_nrmse=_med(draws, gen, a), recovers=bool(_med(draws, gen, a) <= PASS_NRMSE))
        for L in LEARNERS:
            p, n, ma, mb = _paired(draws, gen, a, L, "forecast_pp", "less")
            row[f"vs_{L}"] = dict(p_wilcoxon=p, n=n, median_arm=ma, median_learner=mb, beats=bool(p < 0.05 and ma < mb))
        comp[a] = row
    ok = all(c["recovers"] and all(c[f"vs_{L}"]["beats"] for L in LEARNERS) for c in comp.values())
    return dict(passed=bool(ok), arms=comp, n_draws=sum(d["gen"] == gen for d in draws))


def hard_vs_soft(draws, gen="G1"):
    """H2 contrast on synthetic data (prereg 13): paired over the draws, L_i = ln(forecast RMSE of A2 / forecast RMSE of A1) (positive: the soft PINN is better); exact sign
    tests at ln 1.02 and +-ln 1.10 as in H2 (level 0.025; descriptive here) and the paired Wilcoxon"""
    from .stats_step import ALPHA, LOG_N, LOG_S, median_order_ci, sign_p
    pairs = [(d["forecast_pp"]["A2"], d["forecast_pp"]["A1"]) for d in draws if d["gen"] == gen and "A1" in d["forecast_pp"] and "A2" in d["forecast_pp"]]
    if len(pairs) < 3:
        return dict(n=len(pairs), outcome="not evaluated")
    L = np.log(np.array([a / b for a, b in pairs]))
    pA, pC = sign_p(L, LOG_S), sign_p(-L, LOG_S)
    out = "A" if pA <= ALPHA else ("C" if pC <= ALPHA else ("B" if sign_p(L, LOG_N) <= ALPHA and sign_p(-L, LOG_N) <= ALPHA else "unresolved"))
    lo, hi, _ = median_order_ci(L)
    p_w = float(sps.wilcoxon(L, alternative="greater").pvalue) if not np.allclose(L, 0) else 1.0
    return dict(n=len(L), median_L=float(np.median(L)), median_ci95=[lo, hi], n_soft_better=int((L > 0).sum()), p_A=pA, p_C=pC, p_wilcoxon_soft_better=p_w, outcome=out, descriptive=True)


def g2_status(summary_path):
    """-> the G2 verdict dict for the H3 'win' condition (key 'passes'), read from summary.json"""
    summ = json.load(open(summary_path, encoding="utf8"))
    v = summ.get("verdicts") or verdicts(summ)
    return v.get("G2", {"passes": False, "reason": "no G2 draws in the H7 summary"})
