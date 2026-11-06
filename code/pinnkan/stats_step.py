"""Statistics step: analysis/contrasts_<test>.json, reference.json, controls.json from run directories (formats of code/figures/README.md).

Rule (runs/prereg/TYPE1_SIGNFLIP.md, D012): for every contrast the exact one-sided sign test on L_c = ln(S_comp,c / S_A1,c) over held-out conditions
(estimand: the median), p = P(Bin(n, 1/2) >= #{L_c > m}); tier S passes m = ln 1.02, tier N passes m = -ln 1.10 but not S; interval of the median by order
statistics (coverage >= 95 %). Beside it the mean paired pp difference (comparator - A1) with a BCa interval, and the pp-scale tier of D009
(delta_S = 0.02 E, delta_N = 0.10 E, E = the comparator's training-side inner-CV score pooled by test-condition count): reported, never replacing the log tier.
Comparators chosen by inner-CV score only (never by test error). Holm over {H1a, H1b, H6} by the three N-tier p-values (levels a/3, a/2, a);
H1c tested at a only if all three reach tier S; H2 order A, C, B (PREREG_v2 9.6). Test C: Holm-2 (H4); S2: H5 one non-inferiority test; ISU / SNL as Test B
on the pool they have, not pooled with Samsung and not gatekept for H1c."""
import copy
import json
import os

import numpy as np
from scipy import stats

from . import margins as mg
from .negcontrol import MC_SEED_ROOT, mc_rng

class OutOfScopeError(RuntimeError):
    """the PREREG_v3 analysis (H1a-H6 family, H1c gate, H2 order, H3, Test C Holm-2, H5) is struck for Design R2; Design R2 runs are read by stats_v4 (run_stats_v4)"""


V3_OUT_OF_SCOPE = ("H1a", "H1b", "H1c", "H2 as a decision contrast (now Q-H)", "H3 (KAN wording against the GAMs; the G2 'KAN win')", "H4 Holm-2 on Test C (Test C is descriptive)",
                   "H5 (S2 is descriptive)", "X1 (now Q-T)", "H7 beyond the G0 pipeline check")


def _refuse_design_r2(cfgs, what):
    for c in cfgs:
        if c.get("design") == "R2" or c.get("m") is not None or c.get("k") is not None:
            raise OutOfScopeError(f"{what}: the V3 analysis is out of scope for Design R2 grid runs ({', '.join(V3_OUT_OF_SCOPE)}); use stats_step.run_stats_v4 / stats_v4")


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
        _refuse_design_r2([f["cfg"] for f in folds], "Builder")
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
        e.update(outcome=out, status="OUT OF SCOPE (H3 and the G2 'KAN win' are struck, PREREG_v4 2): history only", out_of_scope=True, level_win=lvl, tier_S_met=bool(s_met), g2_passes=g2_pass, win_blocked_by_g2=bool(s_met and g2_pass is not True),
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
        return dict(test=t, scope="OUT OF SCOPE for Design R2 (PREREG_v3 analysis kept for history; stats_v4 reads Design R2 runs)", out_of_scope=list(V3_OUT_OF_SCOPE),
                rule="exact one-sided sign test on L-m (TYPE1_SIGNFLIP.md, D012); estimand: median over conditions; pp tier of D009 beside it",
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
    out = dict(runs_checked=len(recs), passed=bool(recs and all(r["passed"] for r in recs)), max_abs_diff=(float("nan") if (not recs or any(not np.isfinite(r["max_abs_diff"]) for r in recs)) else float(max(r["max_abs_diff"] for r in recs))),
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
    """Gate G of Design R2 (PREREG_v4 10 and 11): NC-1 trips or the G0 pipeline check PC-1 (nRMSE <= 0.15) fails. PC-2 (calendar rate monotone in T) and PC-3 (A1 beats persistence at g4)
    are reported control checks and NOT gate inputs (GAP-6); a test-fold read and an unmet freeze condition are decided by the guard and the freeze, not here. A control that could not
    be evaluated is listed under `not_evaluated` (neither tripped nor cleared)."""
    neg, pos = controls.get("negative") or {}, controls.get("positive") or {}
    reasons = []
    nc1 = neg.get("nc1")
    nc1_seen = bool(nc1) and nc1.get("runs_checked", 1) > 0            # no invariance.json found = not evaluated, neither tripped nor cleared
    if nc1_seen and not nc1["passed"]:
        reasons.append("NC-1 tripped")
    pc1 = pos.get("P1_G0_nrmse_leq_0p15")
    if pc1 is False:
        reasons.append("PC-1 failed (G0 pipeline check: nRMSE > 0.15)")           # no word of the banned-claim list (C26 N1): a tripped gate is reported, not blocked by the wording check
    pending = []
    if not nc1_seen:
        pending.append("NC-1")
    if pc1 is None:
        pending.append("PC-1")
    reported = {"PC-2_calendar_rate_monotone_in_T": pos.get("P2_monotone_in_T"), "PC-3_A1_beats_persistence": pos.get("P3_passed")}
    return dict(tripped=bool(reasons), reasons=reasons, not_evaluated=pending, reported_checks=reported,
                rule="PREREG_v4 gate G: NC-1 trips or PC-1 fails; PC-2 and PC-3 are reported checks, not gate inputs; NC-2 is not a gate")


def gate_g_v3(controls):
    """V3 gate (OUT OF SCOPE, history): NC-1 trips or a positive control (P1-P3) fails. NC-2 is not a gate. A control that could not be evaluated (value None or absent) is listed under
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
    for t_, dirs_ in runs_by_test.items():
        _refuse_design_r2([_load(os.path.join(d, "config.json")) for d in dirs_], f"run_stats({t_})")
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
        write_checked_json(os.path.join(analysis_dir, "physval_11a.json"), physval.physval_11a(physval_runs), "physval_11a")          # C26 N5: the same fail-closed wording check
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


def _pp_margins(out, store, run_dirs, strict, folds):
    """PREREG_v4 9.2 (descriptive beside every tier): pooled pp margins per contrast and grid cell from the runs' margins_inputs.json (margins.pooled_margins) -> (record, summary). Every estimated
    row gets `pp_margin` and `tier_pp` (the BCa lower bound of the mean pp gain against delta_S and -delta_N); the named contrasts (P1, P2, K1, K2, secondary) get theirs in `named_tier_pp`. Runs without
    margins_inputs.json (fake grids, development) give status 'not available'; some with and some without raises."""
    if not mg.has_inputs(run_dirs):
        return None, {"status": "not available: no margins_inputs.json in the runs"}
    rec = mg.pooled_margins(run_dirs, folds=folds, strict=strict)
    for r in out.get("estimated", {}).get("rows", []):
        row = rec["contrasts"].get(f"{r['target']} vs {r['comparator']}", {}).get(mg.cell_label(r["cell"]))
        if row is not None:
            r["pp_margin"] = {k: row[k] for k in ("E_pp", "delta_S_pp", "delta_N_pp")}
            r["tier_pp"] = mg.tier_pp(r["mean_pp_ci"][0], row["delta_S_pp"], row["delta_N_pp"]) if "mean_pp_ci" in r else None
    named = {}
    for name, nm in rec["named"].items():
        t, c, cell, row = nm["target"], nm["comparator"], tuple(nm["cell"]), nm["margin"]
        st_ = store.seed_view() if name in ("K1", "K2") else store
        if row is None or not (st_.has(t, *cell) and st_.has(c, *cell)):
            continue
        _, a, b = st_.pair(t, c, cell)
        d = b - a
        lo, hi = bca_mean_ci(d, label=f"B|{name}|g{cell[0]}-{cell[1]}|BCa_mean_pp_margin") if len(d) >= 3 else (float(d.mean()), float(d.mean()))
        named[name] = {"target": t, "comparator": c, "cell": list(cell), "n": int(len(d)), "mean_pp": float(d.mean()), "mean_pp_ci": [lo, hi], "E_pp": row["E_pp"], "delta_S_pp": row["delta_S_pp"],
                       "delta_N_pp": row["delta_N_pp"], "tier_pp": mg.tier_pp(lo, row["delta_S_pp"], row["delta_N_pp"])}
    return rec, {"status": "formed", "sha256": rec["sha256"], "file": "margins.json", "named_tier_pp": named}


def _physval_v4(analysis_dir, run_dirs):
    """physval_11a.json from the g4 runs (m = 32, one per outer fold: the stress functions of A1's final refit seeds) of a Design R2 grid; the file passes through write_checked_json. Runs without
    stress_functions.json give status 'not available'."""
    from . import physval as pv
    dirs = [d for d in run_dirs if (lambda c: 32 if c.get("m") is None else int(c["m"]))(_load(os.path.join(d, "config.json"))) == 32 and os.path.exists(os.path.join(d, "stress_functions.json"))]
    if not dirs:
        return {"status": "not available: no stress_functions.json in the m = 32 runs"}
    write_checked_json(os.path.join(analysis_dir, "physval_11a.json"), pv.physval_11a(dirs), "physval_11a")
    return {"status": "written", "file": "physval_11a.json", "n_runs": len(dirs)}


class RegisteredControlError(RuntimeError):
    """a registered control of section 10 (NC-2, PC-2, PC-3) failed to compute in a strict run: controls.json is written with the failure recorded, then the step stops before contrasts_v4_B.json"""


REGISTERED = {"G3_nc2": "NC-2", "G3_pc2": "PC-2", "G3_pc3": "PC-3", "G3_controls": "NC-2/PC-2/PC-3 record"}


def _stats_gaps_v4(analysis_dir, out, store, rule, c, run_dirs, controls, negative_runs, test_c_runs, s2_runs, strict, descriptive=True):
    """G1-G8 of STATS_GAPS_REPORT.md (stats_gaps). REGISTERED controls (G3: NC-2, PC-2, PC-3; section 10) always run: a failure to compute is recorded in the returned controls and returned as
    `reg_err` (the caller stops a strict run after controls.json is written); an input that is missing marks the outcome provisional (`status.registered_controls_not_evaluated`). DESCRIPTIVE gaps
    (G1, G2, G4, G6, G7, G8; switched off by descriptive=False) are isolated: an exception or a banned sentence is written to STATS_GAPS_ERRORS.json with a warning, the record is left out.
    -> (controls with negative.nc2 and the reported checks PC-2 / PC-3, reg_err {control: message})"""
    import warnings
    from . import stats_gaps as sg
    from . import stats_v4
    from .extraction_audit import check_generated_sentences
    status, errors = {}, {}

    def gap(name, fn, check=True):
        try:
            res = fn()
            if res is not None and check:
                check_generated_sentences(res, name)
            status[name] = "not available" if res is None else "formed"
            return res
        except Exception as e:  # noqa: BLE001
            status[name] = "ERROR (see STATS_GAPS_ERRORS.json)"
            errors[name] = f"{type(e).__name__}: {e}"
            return None
    path = lambda n: os.path.join(analysis_dir, n)
    failed = lambda key: {"status": f"not evaluated: ERROR {errors[key]}", "passed": None, "gating": False}
    reg_missing = {}
    nc2 = None
    if negative_runs:
        def _nc2():
            dirs = [negative_runs] if isinstance(negative_runs, str) else list(negative_runs)
            for d in dirs:
                cf = _load(os.path.join(d, "config.json"))
                if cf.get("test", "B") != "B" or not cf.get("permute_stress"):
                    raise ValueError(f"NC-2 needs permute_stress runs of Test B: {d}")
            return sg.nc2_v4(store, stats_v4.Store.from_runs(dirs, strict=strict), rule, sg.NC2_ALPHA)
        nc2 = gap("G3_nc2", _nc2)
        if "G3_nc2" in errors:
            nc2 = failed("G3_nc2")
    else:
        status["G3_nc2"] = "not run (no negative_runs given)"
        reg_missing["NC-2"] = "no negative_runs given"
    pc2 = gap("G3_pc2", lambda: sg.pc2_v4(run_dirs))
    pc3 = gap("G3_pc3", lambda: sg.pc3_v4(store, rule, sg.NC2_ALPHA))
    pc2 = failed("G3_pc2") if "G3_pc2" in errors else pc2
    pc3 = failed("G3_pc3") if "G3_pc3" in errors else pc3
    for nm, rec, key in (("PC-2", pc2, "G3_pc2"), ("PC-3", pc3, "G3_pc3")):
        if key not in errors and rec.get("passed") is None:
            reg_missing[nm] = rec.get("status", "not evaluated")
    ctl = gap("G3_controls", lambda: sg.extend_controls(controls, nc2, pc2, pc3))
    if ctl is None:
        ctl = copy.deepcopy(controls)
        ctl["registered_controls_error"] = errors.get("G3_controls", "unknown")
    reg_err = {REGISTERED[k]: v for k, v in errors.items() if k in REGISTERED}
    if reg_err or reg_missing:                                              # a label only: no tier, state, title, count or margin changes
        rec = {**reg_missing, **{k: f"ERROR: {v}" for k, v in reg_err.items()}}
        out["status"]["registered_controls_not_evaluated"] = rec
        out["status"]["provisional"] = True
        if "outcome" in out:
            out["outcome"]["provisional"] = True
    if descriptive:
        at = gap("G1_arm_table", lambda: sg.arm_table(run_dirs, test_c_runs, s2_runs))
        if at is not None:
            write_json(path("arm_table.json"), at)
        ref = gap("G2_reference", lambda: sg.reference_record(run_dirs, test_c_runs, s2_runs) or None)
        if ref:
            write_reference(path("reference.json"), ref)
        qt = gap("G7_qt_interval", lambda: sg.qt_interval(store, rule))
        if qt is not None:
            out["secondary"]["tests"]["QT_g1"]["median_interval"] = qt
        cand = gap("G8_candidates_vs_A1", lambda: sg.candidates_vs_a1(store, rule))
        if cand is not None:
            out["candidates_vs_a1"] = cand
        ls = gap("G4_law_summary", lambda: sg.law_summary(run_dirs))
        if ls is not None and "arms" in ls:
            write_json(path("law_summary.json"), ls)
        elif ls is not None:
            status["G4_law_summary"] = ls["status"]
        rm = gap("G6_residual_map", lambda: sg.merge_residual_cells(run_dirs), check=False)
        if rm is not None:
            np.savez(path("residual_map.npz"), **rm)
    out["stats_gaps"] = {"status": status, "note": "G3 = registered controls (section 10); the others are descriptive inputs of the display items (STATS_GAPS_REPORT.md); none of them sets a tier, a state, a title, a count or a gate input"}
    if errors:
        write_json(path("STATS_GAPS_ERRORS.json"), errors)
        warnings.warn(f"statistics-step gaps with errors: {sorted(errors)}" + (" (registered controls: a strict run stops)" if reg_err else " (the confirmatory outputs are unaffected)"))
    return ctl, reg_err


def _test_c_s2(mk, strict, test_c_runs, test_c_lab_indicator_runs, s2_runs):
    """D033 D3: the descriptive Test C (A1 against A9, A10, D* at the k_full cell, n = 13) and S2 tables (plain exact, both intervals) and the Test C sentences; rule 9.8 (3): a Test C sentence
    goes into the abstract only if the lab-indicator row leaves the sign of that comparator's median ratio unchanged (a row that was not run keeps it out and marks the outcome provisional)"""
    from . import stats_rows, stats_v4
    out = {}
    if test_c_runs:
        sc = mk(test_c_runs)
        rows = stats_rows.descriptive_entries(sc, test="C")
        lab = mk(test_c_lab_indicator_runs) if test_c_lab_indicator_runs else None
        in_abs = {}
        if lab is not None:
            lrows = stats_rows.descriptive_entries(lab, test="C")
            for a in rows:
                med_p = float(np.median(sc.L("A1", a, stats_v4.G4)[1]))
                med_l = float(np.median(lab.L("A1", a, stats_v4.G4)[1])) if a in lrows else None
                in_abs[a] = stats_rows.test_c_in_abstract(med_p, med_l)
        else:
            in_abs = {a: False for a in rows}
        out["test_c"] = {"rows": rows, "sentences": stats_rows.test_c_sentences(rows), "in_abstract": in_abs, "row_lab_indicator_not_run": lab is None,
                         "rule": "PREREG_v4 9.8 rule 3: the fixed D011 sentence enters the abstract only if the lab-indicator row leaves the sign of the median ratio unchanged; otherwise Limitations; always in the Results"}
    if s2_runs:
        out["s2"] = {"rows": stats_rows.descriptive_entries(mk(s2_runs), test="S2"), "label": "descriptive (S2), plain exact, no tier word"}
    return out


def write_checked_json(path, obj, where):
    """fail closed (red-team A4, N5): no generated sentence of `obj` may contain a banned claim. On a violation nothing is written to `path`; the offending paths and patterns are recorded in
    `<path>.WORDING_VIOLATION.json` (a diagnostic, itself written without the offending text) and BannedWordingError is raised."""
    from .extraction_audit import BannedWordingError, check_generated_sentences
    try:
        check_generated_sentences(obj, where)
    except BannedWordingError as e:
        write_json(path + ".WORDING_VIOLATION.json", {"where": where, "violations": [{"path": p_, "patterns": h_} for p_, h_ in getattr(e, "violations", [])]})
        raise
    write_json(path, obj)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="statistics step: contrasts_<test>.json, reference.json, controls.json from run directories")
    ap.add_argument("--analysis-dir", required=True)
    ap.add_argument("--runs", action="append", required=True, help="TEST=dir1,dir2,... (one directory per outer fold); TEST in B, C, S2, ISU, SNL")
    ap.add_argument("--negative-run", action="append", default=None, help="permute_stress run directory (NC-2), one per Test B fold (v3_legacy: in the order of --runs B=...; r2: the g4 runs conf_samsung_B_f*_m32_nc2, paired by condition with the real g4 cell)")
    ap.add_argument("--nc1-full", default=None, help="nc1_full.json of the pre-freeze full-pipeline invariance run")
    ap.add_argument("--h7-run", default=None)
    ap.add_argument("--stress-run", default=None, help="Test B run directory holding stress_functions.json (control P2)")
    ap.add_argument("--design", choices=("r2", "v3_legacy"), default="r2", help="r2 = Design R2 (grid runs, stats_v4); v3_legacy = the PREREG_v3 analysis, history only")
    ap.add_argument("--item-f-dir", default=None, help="directory of the hashed item (f) dependence file (D018); required for --design r2")
    ap.add_argument("--row", action="append", default=None, help="NAME=dir1,dir2,... for the downgrade-row re-runs: lab_indicator, retain_all, random_subset (draws separated by ';'), lab_indicator_C (the lab-indicator re-run of Test C)")
    ap.add_argument("--item-f-sha256", default=None, help="the item (f) file hash pinned in git / FROZEN")
    ap.add_argument("--ledger-root", default=None, help="project root whose runs/prereg/SCORED.jsonl is checked: every Samsung row must carry the same item_f_sha256 (D026)")
    ap.add_argument("--audit-dir", default=None, help="NOT USED in the confirmatory run (D022b: the extraction audit is struck; passing it raises AuditGuardError). Without it the descriptive stability table is printed, no edge-level licence wording")
    ap.add_argument("--audit-thresholds-pin", default=None, help="sha256 of extraction_audit.json (mandatory with --audit-dir)")
    ap.add_argument("--calibration-sha256", default=None, help="sha256 of calibration.json (mandatory with --audit-dir)")
    ap.add_argument("--lenient", action="store_true", help="development only: skip the completeness and design checks of Store.from_runs / check_complete")
    ap.add_argument("--sign-rule", default=None, help="optional JSON override of the statistics config (sign_rule, rho_s0, graph_w, alpha, e1_prime_approved); the defaults are the registered values (w 0.78, clause e1-prime on; runs/prereg/stats_config.json) and, once FROZEN exists, any differing value is refused")
    ap.add_argument("--physval", action="store_true", help="write physval_11a.json (PREREG 11a items 1, 2, 4, 5): from the Test B fold runs (v3_legacy, opt-in) or the m = 32 grid runs (r2: always written)")
    ap.add_argument("--no-physval", action="store_true", help="r2 only: skip physval_11a.json; refused unless --lenient (11a is registered)")
    a = ap.parse_args(argv)
    runs = {}
    for item in a.runs:
        t, dirs = item.split("=", 1)
        runs[t] = dirs.split(",")
    if a.design == "r2":
        if a.no_physval and not a.lenient:
            ap.error("--no-physval is refused for a strict Design R2 run (PREREG_v4 11a is registered); it needs --lenient")
        rr = {}
        for item in (a.row or []):
            n_, v_ = item.split("=", 1)
            rr[n_] = [x.split(",") for x in v_.split(";")] if n_ == "random_subset" else v_.split(",")
        run_stats_v4(a.analysis_dir, runs["B"], json.loads(a.sign_rule) if a.sign_rule else None, item_f_dir=a.item_f_dir, row_runs=rr, h7_run=a.h7_run,
                     test_c_runs=runs.get("C"), test_c_lab_indicator_runs=rr.get("lab_indicator_C"), s2_runs=runs.get("S2"),
                     item_f_sha256=a.item_f_sha256, ledger_root=a.ledger_root, strict=not a.lenient, audit_dir=a.audit_dir, audit_thresholds_pin=a.audit_thresholds_pin, calibration_sha256=a.calibration_sha256,
                     physval=not a.no_physval, negative_runs=a.negative_run)
        return
    run_stats(a.analysis_dir, runs, a.negative_run, a.h7_run, a.stress_run, nc1_full=a.nc1_full, physval_runs=(runs.get("B") if a.physval else None))


# --------------------------------------------------------------------------------------------------- Design R2 (PREREG_v4): see stats_v4.py
def run_stats_v4(analysis_dir, run_dirs, cfg=None, item_f_dir=None, gate=None, row_runs=None, h7_run=None, item_f_sha256=None, strict=True, n_expected=None, folds=range(5), audit_dir=None, audit_thresholds_pin=None, calibration_sha256=None, frozen_commit=None, licences=False, ledger_root=None, physval=True,
                 root=None, test_c_runs=None, test_c_lab_indicator_runs=None, s2_runs=None, negative_runs=None, gaps=True):
    """Design R2 statistics from grid runs, through the downgrade rows (stats_rows.run_v4_full). `negative_runs`: the permute_stress runs of NC-2 (g4, one per outer fold, configs
    `*_m32_nc2.json`); `gaps=False` switches off the additive inputs of the display items G1-G8 (stats_gaps; the confirmatory outputs are identical with or without them). The item (f) dependence file must exist, match its hash (and `item_f_sha256` if given) and
    pre-date every outer score file (D018 2.3 (ii)); otherwise ItemFError. strict (default): every run must say design R2 and the grid must be complete (folds, cells, n, arms, selectors,
    both A10 forms; Store.check_complete). `row_runs`: {'lab_indicator': [dirs], 'retain_all': [dirs], 'random_subset': [[dirs of draw 0], [draw 1], [draw 2]]} (the re-runs of the
    rows (ii)-(iv)); a row that is not supplied is recorded as not run and the outcome is marked provisional. Gate G: NC-1 from the runs' invariance.json and PC-1 from the G0 run
    `h7_run`; an unevaluated control is listed and also makes the outcome provisional.
    D033: (F1) once FROZEN exists in `root` (default: the project root) the configuration is the pinned runs/prereg/stats_config.json and a differing `cfg` / `--sign-rule` is refused
    (stats_v4.effective_config); the config and its hash are recorded in contrasts_v4_B.json. (D5) `n_expected` defaults to the designed 40 minus n_conditions_dropped of the pinned
    blinding_exclusions.json; once FROZEN exists a different explicit value is refused. (D3) `test_c_runs`, `test_c_lab_indicator_runs` and `s2_runs` (grid-free runs of Test C and S2, k_full cell)
    add the descriptive Test C / S2 tables with both intervals and the fixed Test C sentences (rule 9.8 (3))."""
    from . import blinding, guard, stats_rows, stats_v4
    if not physval and strict:
        raise ValueError("physval = False is refused in a strict run: physval_11a.json (PREREG_v4 11a) is part of the registered analysis (--no-physval needs --lenient)")
    root = root or guard._DEFAULT_ROOT
    cfg, cfg_pin = stats_v4.effective_config(cfg, root)                     # D033 F1: first, before anything is read
    n_derived = blinding.expected_n(root, "B")
    if n_expected is None:
        n_expected = n_derived
    elif guard.is_frozen(root) and n_expected != n_derived:
        raise stats_v4.StatsConfigPinError(f"n_expected = {n_expected} differs from the {n_derived} derived from the pinned blinding_exclusions.json (D033 D5)")
    if item_f_dir is None:
        raise stats_v4.ItemFError("item_f_dir is required: the statistics step is blocked without the hashed item (f) dependence file")
    if ledger_root is None and guard.is_frozen():                          # D026: once a FROZEN exists in this tree the ledger check cannot be skipped by omission
        ledger_root = guard._DEFAULT_ROOT
    item_f = stats_v4.require_item_f(item_f_dir, run_dirs, item_f_sha256, ledger_root=ledger_root)      # D026: with ledger_root, every Samsung ledger row must carry the file's hash
    rule, c = stats_v4.resolve_config(cfg)
    store = stats_v4.Store.from_runs(run_dirs, strict=strict)
    if strict:
        store.check_complete(folds, n_expected, k_chain=not c["k_chain_struck"])
    row_runs = row_runs or {}
    mk = lambda dirs: stats_v4.Store.from_runs(dirs, strict=strict)
    controls = build_controls(real_runs=run_dirs, h7_summary=(os.path.join(h7_run, "summary.json") if h7_run else None))
    gate_ = gate if gate is not None else controls["gate_G"]
    out = stats_rows.run_v4_full(store, cfg, lab_indicator=mk(row_runs["lab_indicator"]) if row_runs.get("lab_indicator") else None,
                                 retain_all=mk(row_runs["retain_all"]) if row_runs.get("retain_all") else None,
                                 random_subset=[mk(d) for d in row_runs["random_subset"]] if row_runs.get("random_subset") else None, gate=gate_)
    prov = {"rows_not_run": out["downgrade"]["rows_not_run"], "gate_not_evaluated": list(gate_.get("not_evaluated", [])) if isinstance(gate_, dict) else []}
    prov["provisional"] = bool(prov["rows_not_run"] or prov["gate_not_evaluated"])
    out["status"] = prov
    out["config_pin"] = {**cfg_pin, "config_sha256": out["config_sha256"], "n_expected": n_expected, "n_expected_source": "40 - n_conditions_dropped['B'] of runs/prereg/blinding_exclusions.json"}
    tc = _test_c_s2(mk, strict, test_c_runs, test_c_lab_indicator_runs, s2_runs)
    if tc:
        out.update(tc)
        if "outcome" in out and "test_c" in tc:
            out["outcome"]["test_c_sentences_for_abstract"] = {a: s_ for a, s_ in tc["test_c"].get("sentences", {}).items() if tc["test_c"]["in_abstract"].get(a)}
        if "test_c" in tc and tc["test_c"]["row_lab_indicator_not_run"]:
            prov["provisional"] = True
            prov["test_c_lab_indicator_row_not_run"] = True
    if "outcome" in out:
        out["outcome"]["provisional"] = prov["provisional"]
    out["item_f"] = item_f
    pp_record, out["margins_pp"] = _pp_margins(out, store, run_dirs, strict, folds)               # PREREG_v4 9.2: pp margins per contrast and grid cell, descriptive beside every tier
    if audit_dir is None:                                                  # D022b: the law is printed in closed form, no edge family is named; the descriptive stability table is added when the runs hold extracted laws
        out["edge_wording"] = {"printed": False, "reason": "descriptive reporting only: the extracted laws are printed in closed form without named edge families (D022b)"}
        if any(os.path.exists(os.path.join(d, "extracted_laws.json")) for d in run_dirs):
            from .extraction_audit import AuditError, AuditGuardError
            try:
                out["edge_wording"]["stability"] = stats_v4.edge_level_wording(run_dirs)
            except (AuditError, AuditGuardError) as e:                         # a lenient or partial-grid run (or no g4 laws at all) must not abort: the descriptive table is recorded as unavailable (C26 B5)
                out["edge_wording"]["stability"] = {"status": f"not available: {e}"}
    elif not licences:
        from .extraction_audit import AuditGuardError
        raise AuditGuardError("D022b: the extraction audit is struck as a contribution; edge-level licences are refused (descriptive stability table only: pass no audit_dir)")
    else:
        fc = frozen_commit if frozen_commit is not None else (guard.read_freeze() or {}).get("commit")
        out["edge_wording"] = stats_v4.edge_level_wording(run_dirs, audit_dir, audit_thresholds_pin, calibration_sha256, fc, licences=True)         # raises AuditGuardError without the pins, a valid record from the FROZEN commit
    out["gate_G"] = gate_
    os.makedirs(analysis_dir, exist_ok=True)
    controls, reg_err = _stats_gaps_v4(analysis_dir, out, store, rule, c, run_dirs, controls, negative_runs, test_c_runs, s2_runs, strict, descriptive=gaps)       # G1-G8 (STATS_GAPS_REPORT.md); G3 always runs
    if gate is None:                                                       # F4: contrasts_v4_B.json carries the same reported checks as controls.json; the gate rule and its fields are unchanged
        for k_ in ("tripped", "reasons", "not_evaluated", "rule"):
            assert controls["gate_G"][k_] == out["gate_G"][k_], k_
        out["gate_G"] = {**out["gate_G"], "reported_checks": controls["gate_G"]["reported_checks"]}
    write_checked_json(os.path.join(analysis_dir, "controls.json"), controls, "controls")          # controls.json (with the Gate G diagnostic) is written first: a wording failure of the contrasts never hides a tripped gate (C26 N1, N5)
    if reg_err and strict:                                                 # a registered control (NC-2, PC-2, PC-3) failed to compute: stop before the contrasts are written
        raise RegisteredControlError(f"registered control(s) failed to compute: {reg_err}; controls.json records it, contrasts_v4_B.json is not written (re-run after the fix; this is not a re-score)")
    if physval:                                                            # N5: physval_11a.json (PREREG 11a items 1, 2, 4, 5) on the R2 path, through the same fail-closed wording check
        out["physval"] = _physval_v4(analysis_dir, run_dirs)
    if pp_record is not None:
        write_checked_json(os.path.join(analysis_dir, "margins.json"), pp_record, "margins")
    write_checked_json(os.path.join(analysis_dir, "contrasts_v4_B.json"), out, "contrasts_v4_B")
    return out
