"""Statistics step: analysis/contrasts_<test>.json, reference.json, controls.json from run directories (formats of code/figures/README.md).

Rule (runs/prereg/TYPE1_SIGNFLIP.md, D012): for every contrast the exact one-sided sign test on L_c = ln(S_comp,c / S_A1,c) over held-out conditions
(estimand: the median), p = P(Bin(n, 1/2) >= #{L_c > m}); tier S passes m = ln 1.02, tier N passes m = -ln 1.10 but not S; interval of the median by order
statistics (coverage >= 95 %). Beside it the mean paired pp difference (comparator - A1) with a BCa interval, and the pp-scale tier of D009
(delta_S = 0.02 E, delta_N = 0.10 E, E = the comparator's training-side inner-CV score pooled by test-condition count): reported, never replacing the log tier.
Comparators chosen by inner-CV score only (never by test error). Holm over {H1a, H1b, H6} by the three N-tier p-values (levels a/3, a/2, a);
H1c tested at a only if all three reach tier S; H2 order A, C, B (PREREG_v2 9.6). Test C: Holm-2 (H4); S2: H5 one non-inferiority test; ISU / SNL as Test B
on the pool they have, not pooled with Samsung and not gatekept for H1c."""
import json
import os

import numpy as np
from scipy import stats

from . import margins as mg
from .negcontrol import MC_SEED_ROOT, mc_rng

ALPHA = 0.025
LOG_S, LOG_N = float(np.log(1.02)), float(-np.log(1.10))
POOLS = {"B": ("A3", "A4", "A5", "A7"), "ISU": ("A4", "A5", "A7"), "SNL": ("A4", "A5", "A7")}


def sign_p(L, m):
    """exact one-sided sign test of median(L) > m: P(Bin(n, .5) >= #{L > m})"""
    L = np.asarray(L, float)
    return float(stats.binom.sf(int((L > m).sum()) - 1, len(L), 0.5))


def median_order_ci(x, conf=0.95):
    x = np.sort(np.asarray(x, float))
    n, a, l = len(x), 1 - conf, 1
    for k in range(1, n // 2 + 1):
        if stats.binom.cdf(k - 1, n, 0.5) <= a / 2:
            l = k
        else:
            break
    return float(x[l - 1]), float(x[n - l]), l


def bca_mean_ci(x, B=10000, label="bca", alpha=0.05):
    """BCa interval of the mean over resampled conditions. RNG: SeedSequence([20261105, crc32(label)]) (NEGCONTROL_RULING 5.2); `label` is a fixed string such as "B|H1a|A9|BCa_mean_pp"."""
    x = np.asarray(x, float)
    n = len(x)
    if n < 3 or np.allclose(x, x[0]):
        return float(x.mean()), float(x.mean())
    rng = mc_rng(label)
    boot = np.sort(x[rng.integers(0, n, (B, n))].mean(1))
    th = x.mean()
    z0 = stats.norm.ppf(np.clip((boot < th).mean(), 1.0 / (B + 1), 1 - 1.0 / (B + 1)))
    jk = (x.sum() - x) / (n - 1)
    d = jk.mean() - jk
    den = 6.0 * (np.sum(d ** 2) ** 1.5)
    acc = float(np.sum(d ** 3) / den) if den > 0 else 0.0
    out = []
    for q in (alpha / 2, 1 - alpha / 2):
        zq = stats.norm.ppf(q)
        p = stats.norm.cdf(z0 + (z0 + zq) / (1 - acc * (z0 + zq)))
        out.append(float(np.quantile(boot, np.clip(p, 0, 1))))
    return out[0], out[1]


def _load(p):
    return json.load(open(p, encoding="utf8"))


def load_fold(run_dir):
    """one outer fold: condition scores per arm, inner-CV E per arm, number of test conditions"""
    met = _load(os.path.join(run_dir, "metrics.json"))
    cfg = _load(os.path.join(run_dir, "config.json"))
    p = os.path.join(run_dir, "condition_scores.json")
    if os.path.exists(p):
        sc, src = _load(p), "outer_test"
    else:      # training-fold runs (mode inner): out-of-fold inner-CV condition scores; the contrast is then NOT a confirmatory result
        td = _load(os.path.join(run_dir, "tuning_done.json"))
        sc, src = {a: v["cond_scores"] for a, v in td["arms"].items()}, "inner_cv_training_conditions"
    return {"dir": run_dir, "scores": sc, "inner": met["inner_cv_pp"], "n": len(sc["A1"]), "cfg": cfg, "source": src}


class Builder:
    def __init__(self, folds, test, alpha=ALPHA, g2=None):
        """g2: the G2 verdict dict of the H7 batch (h7.g2_status; key 'passes'), needed for the H3 'win' wording; None = H7 batch not available"""
        self.folds, self.test, self.alpha, self.g2 = folds, test, alpha, g2
        self.mc_labels = []
        self.arms = set.intersection(*[set(f["scores"]) for f in folds])
        self.conds = sorted(c for f in folds for c in f["scores"]["A1"])
        self.s1 = {c: f["scores"]["A1"][c] for f in folds for c in f["scores"]["A1"]}

    def best_by_inner(self, cands):
        """per fold the candidate with the lowest inner-CV score (training side only)"""
        return [min((a for a in cands if a in f["inner"]), key=lambda a: f["inner"][a]) for f in self.folds]

    def entry(self, label, hyp, comp_by_fold):
        S = {}
        for f, a in zip(self.folds, comp_by_fold):
            for c, v in f["scores"][a].items():
                S[c] = v
        conds = sorted(S)
        s1 = np.array([self.s1[c] for c in conds])
        sc = np.array([S[c] for c in conds])
        L = np.log(sc / s1)
        d = sc - s1
        lo, hi, _ = median_order_ci(L)
        lab = f"{self.test}|{hyp}|{max(set(comp_by_fold), key=comp_by_fold.count)}|BCa_mean_pp"
        self.mc_labels.append(lab)
        blo, bhi = bca_mean_ci(d, label=lab)
        E = mg.pooled_E([(f["n"], f["inner"][a]) for f, a in zip(self.folds, comp_by_fold)])
        dS, dN = 0.02 * E, 0.10 * E
        pS, pN = sign_p(L, LOG_S), sign_p(L, LOG_N)
        mode = max(set(comp_by_fold), key=comp_by_fold.count)
        e = dict(label=label, comp=mode, comp_by_fold=list(comp_by_fold), hyp=hyp, n=len(L), L_by_cond={c: float(v) for c, v in zip(conds, L)},
                 d_by_cond={c: float(v) for c, v in zip(conds, d)},
                 median_L=float(np.median(L)), median_ci95=[lo, hi], mean_L=float(L.mean()), n_wins=int((L > 0).sum()), mean_pp=float(d.mean()),
                 mean_pp_ci95=[blo, bhi], rel_reduction_median=float(1 - np.exp(-np.median(L))), p_S=pS, p_N=pN, tier=None, status="",
                 E_pp=E, delta_S_pp=dS, delta_N_pp=dN)
        e["tier_pp"] = "S" if blo > dS else ("N" if blo > -dN else "-")        # BCa 95 % (two-sided) lower bound against the pp margins of D009
        return e

    @staticmethod
    def set_tier(e, level, status, test_S=True):
        e["holm_level"] = level
        e["tier"] = "S" if (test_S and e["p_S"] <= level) else ("N" if e["p_N"] <= level else "-")
        e["status"] = status
        e["tier_pp_differs"] = bool(e["tier_pp"] != e["tier"])
        return e

    def h3(self, h1b):
        """H3 (PREREG 2 and 9.7), Test B only: KAN wording against the GAMs, comparator = the inner-CV-best of {A4, A5} per fold.
        win   = tier S (ln 1.02, exact sign test) against that arm at the Holm level assigned to H1b in the family AND the H7 gate G2 passes (h7.g2_status);
        worse = reverse tier S (level 0.025);  tie = TOST (both one-sided sign tests at +-ln 1.10, level 0.025);  otherwise unresolved. Order: win, worse, tie, unresolved.
        A tier-S result with G2 not passed or not evaluated is reported (`win_blocked_by_g2`) and the KAN wording 'win' is not available."""
        sel = self.best_by_inner([a for a in ("A4", "A5") if a in self.arms])
        e = self.entry("best of A4, A5 (inner-CV) vs A1", "H3", sel)
        L = np.array(list(e["L_by_cond"].values()))
        lvl = h1b["holm_level"]
        s_met = sign_p(L, LOG_S) <= lvl
        g2_pass = None if self.g2 is None else bool(self.g2.get("passes"))
        p_worse = sign_p(-L, LOG_S)
        tie = sign_p(L, LOG_N) <= self.alpha and sign_p(-L, LOG_N) <= self.alpha
        if s_met and g2_pass is True:
            out = "win"
        elif p_worse <= self.alpha:
            out = "worse"
        elif tie:
            out = "tie"
        else:
            out = "unresolved"
        e.update(outcome=out, status="derived: KAN wording against the GAMs", level_win=lvl, tier_S_met=bool(s_met), g2_passes=g2_pass, win_blocked_by_g2=bool(s_met and g2_pass is not True),
                 p_worse=p_worse, tie_tost=bool(tie), g2=self.g2)
        return e

    def build(self):
        t = self.test
        fam = {}
        if t in ("B", "ISU", "SNL"):
            pool = [a for a in POOLS[t] if a in self.arms]
            fam["H1a"] = self.entry("A9 vs A1", "H1a", ["A9"] * len(self.folds))
            fam["H1b"] = self.entry("best pool arm (inner-CV) vs A1", "H1b", self.best_by_inner(pool))
            h6 = "A10"
            fam["H6"] = self.entry("A10 vs A1" + ("" if t == "B" else " (cyclic analogue)"), "H6", [h6] * len(self.folds))
            order = sorted(("H1a", "H1b", "H6"), key=lambda k: fam[k]["p_N"])
            for lev, k in zip((self.alpha / 3, self.alpha / 2, self.alpha), order):
                self.set_tier(fam[k], lev, "primary family")
            gate = all(fam[k]["tier"] == "S" for k in ("H1a", "H1b", "H6"))
            h1c_sel = self.best_by_inner([a for a in ("A11", "A12") if a in self.arms]) if {"A11", "A12"} & self.arms else None
            for a in ("A11", "A12"):
                if a in self.arms:
                    e = self.entry(f"{a} vs A1", "H1c", [a] * len(self.folds))
                    sel = h1c_sel is not None and a == max(set(h1c_sel), key=h1c_sel.count)
                    if t == "B" and gate and sel:
                        self.set_tier(e, self.alpha, "key secondary, gate open")
                    elif t != "B":
                        self.set_tier(e, self.alpha, "secondary (not gatekept on this dataset, not blind)")
                    else:
                        e["status"] = "secondary, not tested (gate closed)" if sel or not gate else "secondary, not the inner-CV-best comparator"
                    fam[f"H1c_{a}"] = e
            if "A2" in self.arms:
                e = self.entry("A2 vs A1 (hard ODE, decision contrast)", "H2", ["A2"] * len(self.folds))
                L = np.array(list(e["L_by_cond"].values()))
                pA, pC = sign_p(L, LOG_S), sign_p(-L, LOG_S)
                if gate and pA <= self.alpha:
                    out = "A"
                elif pC <= self.alpha:
                    out = "C"
                elif sign_p(L, LOG_N) <= self.alpha and sign_p(-L, LOG_N) <= self.alpha:
                    out = "B"
                else:
                    out = "unresolved"
                e.update(outcome=out, status="decision contrast", p_A=pA, p_C=pC)
                fam["H2"] = e
            for key, a, hyp, st in (("X1", "A13", "X1", "descriptive"),):
                if a in self.arms:
                    e = self.entry(f"{a} vs A1 (cycling cells only)", hyp, [a] * len(self.folds))
                    e["status"] = st
                    fam[key] = e
            if t == "B" and {"A4", "A5"} & self.arms:
                fam["H3"] = self.h3(fam["H1b"])
            for a in pool:
                e = self.entry(f"{a} vs A1", "H1b-pool", [a] * len(self.folds))
                e["status"] = "pool arm, descriptive"
                fam[f"pool_{a}"] = e
            for a in ("R1", "R2"):
                if a in self.arms:
                    e = self.entry(f"{a} vs A1", "ref", [a] * len(self.folds))
                    e["status"] = "reference"
                    fam[f"ref_{a}"] = e
        elif t == "C":
            sel = self.best_by_inner([a for a in ("A11", "A12") if a in self.arms])
            h4a = self.entry("best data-only (inner-CV) vs A1", "H4a", sel)
            h4b = self.entry("A10 vs A1", "H4b", ["A10"] * len(self.folds))
            lv = sorted([("H4a", h4a["p_N"]), ("H4b", h4b["p_S"])], key=lambda z: z[1])
            levels = {lv[0][0]: self.alpha / 2, lv[1][0]: self.alpha}
            self.set_tier(h4a, levels["H4a"], "secondary, Holm-2 inside Test C (tier N)")
            h4b_tier = "S" if h4b["p_S"] <= levels["H4b"] else ("N" if h4b["p_N"] <= levels["H4b"] else "-")
            h4b.update(holm_level=levels["H4b"], tier=h4b_tier, status="secondary, Holm-2 inside Test C (tier S)", tier_pp_differs=bool(h4b["tier_pp"] != h4b_tier))
            fam["H4a"], fam["H4b"] = h4a, h4b
            for a in sorted(self.arms - {"A1"}):
                e = self.entry(f"{a} vs A1", "C-desc", [a] * len(self.folds))
                e["status"] = "descriptive"
                fam[f"vs_{a}"] = e
        elif t == "S2":
            sel = self.best_by_inner([a for a in ("A3", "A9", "A10") if a in self.arms])
            e = self.entry("best of A3, A9, A10 (inner-CV) vs A1", "H5", sel)
            e.update(holm_level=self.alpha, tier="N" if e["p_N"] <= self.alpha else "-", status="secondary, one non-inferiority test (storage sentence allowed iff N)")
            e["tier_pp_differs"] = bool(e["tier_pp"] != e["tier"])
            fam["H5"] = e
            for a in sorted(self.arms - {"A1"}):
                x = self.entry(f"{a} vs A1", "S2-desc", [a] * len(self.folds))
                x["status"] = "descriptive"
                fam[f"vs_{a}"] = x
        else:
            raise ValueError(t)
        return dict(test=t, rule="exact one-sided sign test on L-m (TYPE1_SIGNFLIP.md, D012); estimand: median over conditions; pp tier of D009 beside it",
                    alpha=self.alpha, margins=dict(S=LOG_S, N=LOG_N), n=len(self.conds), n_folds=len(self.folds), contrasts=fam,
                    comparator_rule="inner-CV score on the training side of each outer fold; never the outer-test error",
                    synthetic=any(f["cfg"].get("dataset") == "synthetic" for f in self.folds), source=sorted({f["source"] for f in self.folds}),
                    mc_seed_root=MC_SEED_ROOT, mc_labels=list(self.mc_labels))


def build_contrasts(test, run_dirs, alpha=ALPHA, g2=None):
    return Builder([load_fold(d) for d in run_dirs], test, alpha, g2).build()


# --------------------------------------------------------------------------------------------------- reference quantities (training sides only)
def reference_values(prepared_train):
    """R_LOO (replicate spread) and R_WARP (window-aware replicate predictor) in pp: median over training conditions with >= 2 replicates of the condition mean
    of cell RMSEs, same window and forecast set as the endpoint. R_WARP: the form (additive / multiplicative) with the lower median (ties: additive). STATS_RULING 1.2."""
    byc = {}
    for p in prepared_train:
        byc.setdefault(p.cell.cond, []).append(p)

    def mloss(others, t):
        v = [1.0 - np.interp(t, q.cell.t, q.cell.ret) for q in others if q.cell.t[-1] >= t]
        return np.mean(v) if v else np.nan

    def cond_values(mode):
        vals = []
        for cond, ps in byc.items():
            if len(ps) < 2:
                continue
            rm = []
            for j, pj in enumerate(ps):
                others = [q for i, q in enumerate(ps) if i != j]
                tf = pj.win.t_fc
                m_f = np.array([mloss(others, t) for t in tf])
                if mode == "loo":
                    pred = 1.0 - m_f
                else:
                    tw = pj.win.t_win[1:]
                    mw = np.array([mloss(others, t) for t in tw])
                    lw = 1.0 - pj.win.y_win[1:]
                    ok = ~np.isnan(mw)
                    if mode == "add":
                        off = (lw[ok][-1] - mw[ok][-1]) if ok.any() else 0.0
                        pred = 1.0 - np.clip(m_f + off, 0.0, None)
                    else:
                        den = float(np.sum(mw[ok] ** 2))
                        k = float(np.clip(np.sum(lw[ok] * mw[ok]) / den, 0.25, 4.0)) if den > 1e-12 else 1.0
                        pred = 1.0 - k * m_f
                good = ~np.isnan(pred)
                if good.any():
                    rm.append(100.0 * float(np.sqrt(np.mean((pred[good] - pj.fc_true[good]) ** 2))))
            if rm:
                vals.append(float(np.mean(rm)))
        return float(np.median(vals)) if vals else float("nan"), len(vals)

    loo, n = cond_values("loo")
    add, _ = cond_values("add")
    mult, _ = cond_values("mult")
    warp, form = (add, "additive") if add <= mult or np.isnan(mult) else (mult, "multiplicative")
    return dict(R_LOO=loo, R_WARP=warp, R_WARP_form=form, R_WARP_add=add, R_WARP_mult=mult, n_conditions=n, aggregate="median over training conditions with >= 2 replicates")


def write_reference(path, per_test):
    with open(path, "w", encoding="utf8") as fh:
        json.dump(dict(definition="training-side replicate spread (descriptive, never a margin)", values=per_test), fh, indent=1)


# --------------------------------------------------------------------------------------------------- controls (prereg section 10)
def exact_two_sided_p(k, n):
    """exact two-sided sign-test p: min(1, 2 min(tail)); k = number of positives"""
    return float(min(1.0, 2.0 * min(stats.binom.sf(k - 1, n, 0.5), stats.binom.cdf(k, n, 0.5))))


def nc2(real_runs, permuted_runs, alpha=ALPHA, sign_rule=None):
    """NC-2 (interpretive, not gating; Test B only): L_c = ln(S_A1,permuted,c / S_A1,real,c) paired by condition on the same held-out conditions;
    one-sided sign test of median(L) > 0 at 0.025 under the confirmatory rule (D018: Beta-binomial design effect, rho_s0 = 0.03, 30 of 40; `sign_rule=stats_v4.PLAIN` gives the
    plain exact 27 of 40 of the withdrawn D014 text); plus descriptive rows. NEGCONTROL_RULING section 3."""
    def merged(dirs):
        out = {}
        for d in dirs:
            for arm, sc in _load(os.path.join(d, "condition_scores.json")).items():
                out.setdefault(arm, {}).update(sc)
        return out
    R, P = merged(real_runs), merged(permuted_runs)
    cfgs = [_load(os.path.join(d, "config.json")) for d in permuted_runs]
    if any(c.get("test") != "B" for c in cfgs) or not all(c.get("permute_stress") for c in cfgs):
        raise ValueError("NC-2 needs permute_stress runs of Test B")
    if set(R["A1"]) != set(P["A1"]):
        raise ValueError("NC-2 pairs the same held-out conditions: the real and the permuted run score different condition sets")
    conds = sorted(R["A1"])
    L = np.array([np.log(P["A1"][c] / R["A1"][c]) for c in conds])
    k = int((L > 0).sum())
    lo, hi, _ = median_order_ci(L)
    from . import stats_v4                                     # lazy: stats_v4 imports this module
    rule = sign_rule if sign_rule is not None else stats_v4.resolve_config()[0]
    _, _, p = rule.test(L, 0.0)
    desc = {"scores_under_permutation_mean_pp": {a: float(np.mean(list(P[a].values()))) for a in sorted(P)},
            "scores_real_mean_pp": {a: float(np.mean(list(R[a].values()))) for a in sorted(R)}}
    if "A9" in R and "A9" in P:
        desc["mean_L_A9_over_A1_real"] = float(np.mean([np.log(R["A9"][c] / R["A1"][c]) for c in conds]))
        desc["mean_L_A9_over_A1_permuted"] = float(np.mean([np.log(P["A9"][c] / P["A1"][c]) for c in conds]))
    return dict(test="B", n=len(conds), k_positive=k, median_L=float(np.median(L)), rel_increase_median=float(np.exp(np.median(L)) - 1.0), median_ci95=[lo, hi],
                p_one_sided_exact=sign_p(L, 0.0), p_one_sided=p, sign_rule=rule.describe(), crit_positives=rule.crit(len(L), alpha), p_two_sided_exact=exact_two_sided_p(k, len(L)), alpha=alpha,
                passed=bool(p <= alpha * (1 + 1e-9)),
                wording=("pass licenses: 'the accuracy of the learned law depends on the stress dependence it learns'; fail removes it (competing explanation E1)"),
                L_by_cond={c: float(v) for c, v in zip(conds, L)}, descriptive=desc, gating=False)


def nc1_from_runs(real_runs, full_pipeline_json=None):
    """NC-1 (gate G): every confirmatory run's invariance.json must show passed with max |diff| = 0; optional full-pipeline check (nc1_full.json)"""
    recs = []
    for d in real_runs:
        p = os.path.join(d, "invariance.json")
        if os.path.exists(p):
            recs.append(_load(p))
    out = dict(runs_checked=len(recs), passed=bool(recs and all(r["passed"] for r in recs)), max_abs_diff=float(max((r["max_abs_diff"] for r in recs), default=float("nan"))),
               n_rows=int(sum(r["n_rows"] for r in recs)), gating=True)
    if full_pipeline_json:
        f = _load(full_pipeline_json)
        out["full_pipeline"] = dict(passed=bool(f["passed"]), max_abs_diff_outer=f["max_abs_diff_outer"], identical_records=f["identical_records"])
        out["passed"] = bool(out["passed"] and f["passed"])
    return out


def build_controls(negative_runs=None, contrasts_B=None, stress_functions=None, h7_summary=None, real_runs=None, nc1_full=None):
    """negative.nc1 (gate G) from the invariance.json of the confirmatory runs; negative.nc2 (interpretive) from the permute_stress runs against the real Test B runs;
    positive P1 from the H7 summary (G0), P2 from stress_functions.json, P3 from contrasts_B"""
    out = {"negative": None, "positive": {}}
    if real_runs or negative_runs:
        neg = {}
        if real_runs:
            neg["nc1"] = nc1_from_runs(real_runs, nc1_full)
        if negative_runs and real_runs:
            neg["nc2"] = nc2(real_runs, negative_runs)
        out["negative"] = neg
    pos = out["positive"]
    if h7_summary:
        from . import h7 as _h7
        hs = _load(h7_summary)
        g0 = [d for d in hs["draws"] if d["gen"] == "G0"]
        if g0:
            pos["P1_G0_nrmse_leq_0p15"] = bool(all(np.median([d["nrmse"][a] for d in g0]) <= 0.15 for a in ("A1", "A2") if a in g0[0]["nrmse"]))
            p1 = _h7.p1_positive_control(hs["draws"])          # PREREG 10 (P1): recovery AND A1, A2 beat both learners (paired Wilcoxon p < 0.05); None = learners not in the run
            pos["P1_full"] = p1
            pos["P1_passed"] = p1["passed"]
    if stress_functions:
        r = np.array(_load(stress_functions)["storage_rate"]["mean"])          # [nT x nSOC], T ascending
        pos["P2_monotone_in_T"] = bool(np.all(np.diff(r, axis=0) > 0))
    if contrasts_B:
        c = _load(contrasts_B)["contrasts"].get("ref_R1")
        if c:
            pos["P3_A1_beats_R1_median_L"] = c["median_L"]
            pos["P3_passed"] = bool(sign_p(list(c["L_by_cond"].values()), 0.0) <= ALPHA)         # PREREG 10 (P3): A1 beats persistence with margin 0 (exact one-sided sign test, 0.025)
    out["gate_G"] = gate_g(out)
    return out


def gate_g(controls):
    """Outcome row G (PREREG 11): NC-1 trips or a positive control fails. NC-2 is not a gate. A control that could not be evaluated (value None or absent) is listed under
    `not_evaluated`: the gate is then neither tripped nor cleared, and the freeze checklist must not treat it as passed."""
    neg, pos = controls.get("negative") or {}, controls.get("positive") or {}
    reasons = []
    if neg.get("nc1") and not neg["nc1"]["passed"]:
        reasons.append("NC-1 tripped")
    required = {"P1": "P1_passed", "P2": "P2_monotone_in_T", "P3": "P3_passed"}
    for name, key in required.items():
        if pos.get(key) is False:
            reasons.append(f"positive control {name} failed")
    pending = [n for n, k in required.items() if pos.get(k) is None]
    if not neg.get("nc1"):
        pending.append("NC-1")
    return dict(tripped=bool(reasons), reasons=reasons, not_evaluated=pending, rule="PREREG 11 row G: NC-1 trips, or a positive control (P1-P3) fails; NC-2 failing is not a gate")


def write_json(path, obj):
    with open(path, "w", encoding="utf8") as fh:
        json.dump(obj, fh, indent=1)


def reference_from_runs(dirs):
    """median over outer folds of the training-side reference quantities written by the run writer (None when a run is blinded / has none)"""
    vals = [_load(os.path.join(d, "reference_values.json")) for d in dirs if os.path.exists(os.path.join(d, "reference_values.json"))]
    if not vals:
        return None
    return dict(R_LOO=float(np.median([v["R_LOO"] for v in vals])), R_WARP=float(np.median([v["R_WARP"] for v in vals])), n_folds=len(vals))


def run_stats(analysis_dir, runs_by_test, negative_run=None, h7_run=None, stress_run=None, reference_by_test=None, nc1_full=None, physval_runs=None):
    """runs_by_test: {'B': [fold run dirs], 'C': [...], 'S2': [...], 'ISU': [...], 'SNL': [...]} -> writes analysis_dir/contrasts_<test>.json, sensitivity_<test>.json (PREREG 9.8
    rows computed from the runs' own outputs), controls.json (+ reference.json) and, with `physval_runs` (fold run directories of Test B), physval_11a.json (PREREG 11a).
    `h7_run` (directory of the H7 batch with summary.json) supplies the G2 gate of the H3 'win' and the positive control P1."""
    from . import physval, stats_ext
    os.makedirs(analysis_dir, exist_ok=True)
    out = {}
    g2 = None
    if h7_run and os.path.exists(os.path.join(h7_run, "summary.json")):
        from . import h7 as _h7
        g2 = _h7.g2_status(os.path.join(h7_run, "summary.json"))
    for t, dirs in runs_by_test.items():
        folds = [load_fold(d) for d in dirs]
        c = Builder(folds, t, ALPHA, g2).build()
        write_json(os.path.join(analysis_dir, f"contrasts_{t}.json"), c)
        write_json(os.path.join(analysis_dir, f"sensitivity_{t}.json"), stats_ext.sensitivity_for_test(c, folds, t))
        out[t] = c
    if physval_runs:
        write_json(os.path.join(analysis_dir, "physval_11a.json"), physval.physval_11a(physval_runs))
    if reference_by_test is None:
        ref = {t: reference_from_runs(d) for t, d in runs_by_test.items()}
        reference_by_test = {t: v for t, v in ref.items() if v}
    if reference_by_test:
        write_reference(os.path.join(analysis_dir, "reference.json"), reference_by_test)
    neg = [negative_run] if isinstance(negative_run, str) else (list(negative_run) if negative_run else None)
    ctl = build_controls(neg, os.path.join(analysis_dir, "contrasts_B.json") if "B" in runs_by_test else None,
                         os.path.join(stress_run, "stress_functions.json") if stress_run and os.path.exists(os.path.join(stress_run, "stress_functions.json")) else None,
                         os.path.join(h7_run, "summary.json") if h7_run else None, real_runs=runs_by_test.get("B"), nc1_full=nc1_full)
    write_json(os.path.join(analysis_dir, "controls.json"), ctl)
    if any(_load(os.path.join(d, "config.json")).get("dataset") == "synthetic" for ds in runs_by_test.values() for d in ds):
        open(os.path.join(analysis_dir, "SYNTHETIC"), "w").write("analysis of synthetic runs\n")
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="statistics step: contrasts_<test>.json, reference.json, controls.json from run directories")
    ap.add_argument("--analysis-dir", required=True)
    ap.add_argument("--runs", action="append", required=True, help="TEST=dir1,dir2,... (one directory per outer fold); TEST in B, C, S2, ISU, SNL")
    ap.add_argument("--negative-run", action="append", default=None, help="permute_stress run directory (NC-2), one per Test B fold, in the order of --runs B=...")
    ap.add_argument("--nc1-full", default=None, help="nc1_full.json of the pre-freeze full-pipeline invariance run")
    ap.add_argument("--h7-run", default=None)
    ap.add_argument("--stress-run", default=None, help="Test B run directory holding stress_functions.json (control P2)")
    ap.add_argument("--physval", action="store_true", help="also write physval_11a.json (PREREG 11a items 1, 2, 4, 5) from the Test B fold runs")
    a = ap.parse_args(argv)
    runs = {}
    for item in a.runs:
        t, dirs = item.split("=", 1)
        runs[t] = dirs.split(",")
    run_stats(a.analysis_dir, runs, a.negative_run, a.h7_run, a.stress_run, nc1_full=a.nc1_full, physval_runs=(runs.get("B") if a.physval else None))


# --------------------------------------------------------------------------------------------------- Design R2 (PREREG_v4): see stats_v4.py
def run_stats_v4(analysis_dir, run_dirs, cfg=None, item_f_dir=None, gate=None, row_tiers=None):
    """Design R2 statistics from grid runs. The item (f) dependence file must exist, match its hash and pre-date every outer score file (D018 2.3 (ii)); otherwise ItemFError."""
    from . import stats_v4
    if item_f_dir is None:
        raise stats_v4.ItemFError("item_f_dir is required: the statistics step is blocked without the hashed item (f) dependence file")
    item_f = stats_v4.require_item_f(item_f_dir, run_dirs)
    store = stats_v4.Store.from_runs(run_dirs)
    out = stats_v4.run_v4(store, cfg, gate, row_tiers)
    out["item_f"] = item_f
    os.makedirs(analysis_dir, exist_ok=True)
    write_json(os.path.join(analysis_dir, "contrasts_v4_B.json"), out)
    return out
