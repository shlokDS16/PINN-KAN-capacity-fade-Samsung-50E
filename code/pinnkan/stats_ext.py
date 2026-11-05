"""Sensitivity rows of PREREG_v3 9.8 that are computed from a confirmatory run's own outputs (no refit): written to analysis/sensitivity_<test>.json by the statistics step.

    (a) lab-stratified bootstrap (conditions resampled within laboratory strata, stratum = the condition's majority laboratory) and the post-stratified mean
    (b) mean paired difference (comparator - A1, pp) and median log ratio per laboratory and per stage, with n
    (c) leave-one-laboratory-out: the contrast without the conditions of one laboratory (exact sign test at the entry's own Holm level; descriptive)
    (d) two-stage bootstrap: conditions are resampled, then the scored cells inside each sampled condition; weights by scored cells
    (e) pp-scale row: already in every contrast entry (`tier_pp`, `E_pp`, `delta_S_pp`, `delta_N_pp`)
    (j) margin sensitivities: delta_S in {0, 0.05}, delta_N in {0.05, 0.15} (relative), on the log scale as m = ln(1 + delta) and on the pp scale as delta * E

Inputs per outer-fold run directory: `cell_scores.json` (cell -> condition, mean-over-seeds cell RMSE) and `condition_meta.json` (condition -> scored cells, laboratory and
stage counts; identifiers only). A run without them gives a row marked "not available" (never an error, never a guess). Every Monte Carlo step uses
`negcontrol.mc_rng(label)` with a fixed label (NEGCONTROL_RULING 5.2); the labels are listed in the output.
Majority laboratory of a condition = the laboratory with most scored cells (ties: alphabetical first); majority stage likewise; a condition without lab information
falls in the stratum "" (a single stratum: rows (a) and (c) then equal the primary analysis)."""
import json
import os

import numpy as np

from . import labmap
from .negcontrol import mc_rng
from .stats_step import LOG_N, LOG_S, median_order_ci, sign_p

B_BOOT = 10000
MARGINS_S = (0.0, 0.05)
MARGINS_N = (0.05, 0.15)


def _load(p):
    return json.load(open(p, encoding="utf8")) if os.path.exists(p) else None


def majority(counts):
    """key with the most cells (ties: alphabetical first); '' when empty"""
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def condition_strata(folds):
    """cond -> dict(lab, stage, n_cells) from the folds' condition_meta.json, or None when any fold lacks it"""
    out = {}
    for f in folds:
        m = _load(os.path.join(f["dir"], "condition_meta.json"))
        if m is None:
            return None
        for c, e in m.items():
            out[c] = dict(lab=labmap.lab_of(c, e["lab"]), stage=majority(e["stage"]), n_cells=int(e["n_cells"]), labs=e["lab"], stages=e["stage"])
    return out


def cell_pairs(folds, comp_by_fold):
    """cond -> (A1 cell RMSEs, comparator cell RMSEs) paired by cell, or None when a fold lacks cell_scores.json"""
    out = {}
    for f, a in zip(folds, comp_by_fold):
        cs = _load(os.path.join(f["dir"], "cell_scores.json"))
        if cs is None or "A1" not in cs or a not in cs:
            return None
        by = {}
        for cid, r in cs["A1"].items():
            if cid in cs[a]:
                by.setdefault(r["cond"], []).append((r["rmse_pp"], cs[a][cid]["rmse_pp"]))
        for c, v in by.items():
            arr = np.array(v, float)
            out[c] = (arr[:, 0], arr[:, 1])
    return out


def _tier(L, level, mS=LOG_S, mN=LOG_N):
    return "S" if sign_p(L, mS) <= level else ("N" if sign_p(L, mN) <= level else "-")


def margin_rows(entry, level):
    """(j): tiers at the alternative margins; `level` = the Holm level of the entry (None for an untested entry: the family level 0.025 is then used, descriptive)"""
    lvl = level if level is not None else 0.025
    L = np.array(list(entry["L_by_cond"].values()))
    d = np.array(list(entry["d_by_cond"].values()))
    E = entry["E_pp"]
    blo = entry["mean_pp_ci95"][0]
    rows = []
    for dS in MARGINS_S:
        for dN in MARGINS_N:
            tier_log = _tier(L, lvl, np.log(1.0 + dS), -np.log(1.0 + dN))
            tier_pp = "S" if blo > dS * E else ("N" if blo > -dN * E else "-")
            rows.append(dict(delta_S=dS, delta_N=dN, tier_log=tier_log, tier_pp=tier_pp, p_S=sign_p(L, np.log(1.0 + dS)), p_N=sign_p(L, -np.log(1.0 + dN))))
    return dict(level=lvl, rows=rows, mean_pp=float(d.mean()))


def lab_stage_rows(entry, strata, level):
    """(b) and (c): per laboratory and per stage, and leave-one-lab-out"""
    lvl = level if level is not None else 0.025
    conds = list(entry["L_by_cond"])
    L = np.array([entry["L_by_cond"][c] for c in conds])
    d = np.array([entry["d_by_cond"][c] for c in conds])
    lab = np.array([strata[c]["lab"] for c in conds])
    stg = np.array([strata[c]["stage"] for c in conds])

    def block(key):
        out = {}
        for v in sorted(set(key)):
            m = key == v
            out[v] = dict(n=int(m.sum()), mean_pp=float(d[m].mean()), median_L=float(np.median(L[m])), n_wins=int((L[m] > 0).sum()))
        return out
    loo = {}
    for v in sorted(set(lab)):
        m = lab != v
        if m.sum() < 3:
            loo[v] = dict(n=int(m.sum()), note="fewer than 3 conditions left")
            continue
        lo, hi, _ = median_order_ci(L[m])
        loo[v] = dict(n=int(m.sum()), median_L=float(np.median(L[m])), median_ci95=[lo, hi], tier=_tier(L[m], lvl), level=lvl, mean_pp=float(d[m].mean()))
    return dict(per_lab=block(lab), per_stage=block(stg), leave_one_lab_out=loo)


def lab_stratified_bootstrap(entry, strata, label, B=None):
    """(a): conditions resampled within laboratory strata (stratum sizes fixed); percentile 95 % intervals for the median log ratio and for the mean pp difference; the
    post-stratified mean = mean of the laboratory means (every laboratory counts equally) beside the plain mean (conditions equally)"""
    B = B or B_BOOT
    conds = list(entry["L_by_cond"])
    L = np.array([entry["L_by_cond"][c] for c in conds])
    d = np.array([entry["d_by_cond"][c] for c in conds])
    lab = np.array([strata[c]["lab"] for c in conds])
    rng = mc_rng(label)
    groups = [np.flatnonzero(lab == v) for v in sorted(set(lab))]
    med, mean_d = np.empty(B), np.empty(B)
    for b in range(B):
        idx = np.concatenate([g[rng.integers(0, len(g), len(g))] for g in groups])
        med[b], mean_d[b] = np.median(L[idx]), d[idx].mean()
    post_L = float(np.mean([L[g].mean() for g in groups]))
    post_d = float(np.mean([d[g].mean() for g in groups]))
    return dict(label=label, B=B, n_strata=len(groups), strata_sizes={v: int(len(g)) for v, g in zip(sorted(set(lab)), groups)},
                median_L=float(np.median(L)), median_L_ci95=[float(np.quantile(med, 0.025)), float(np.quantile(med, 0.975))],
                mean_pp=float(d.mean()), mean_pp_ci95=[float(np.quantile(mean_d, 0.025)), float(np.quantile(mean_d, 0.975))],
                post_stratified_mean_L=post_L, post_stratified_mean_pp=post_d, plain_mean_L=float(L.mean()))


def two_stage_bootstrap(entry, pairs, strata, label, B=None):
    """(d): resample the conditions, then the scored cells inside each sampled condition (the same cell indices for both arms); condition score = mean of the resampled cell
    RMSEs; statistic = median log ratio over the resampled conditions (unweighted) and the log ratio of the cell-count-weighted mean scores (weights = scored cells)"""
    B = B or B_BOOT
    conds = [c for c in entry["L_by_cond"] if c in pairs]
    if len(conds) < 3:
        return dict(label=label, note="fewer than 3 conditions with cell scores")
    A = [pairs[c][0] for c in conds]
    Cc = [pairs[c][1] for c in conds]
    n = len(conds)
    nc = np.array([len(a) for a in A])
    rng = mc_rng(label)
    med, wl = np.empty(B), np.empty(B)
    for b in range(B):
        ci = rng.integers(0, n, n)
        s1, sc = np.empty(n), np.empty(n)
        for j, k in enumerate(ci):
            ii = rng.integers(0, nc[k], nc[k])
            s1[j], sc[j] = A[k][ii].mean(), Cc[k][ii].mean()
        w = nc[ci].astype(float)
        med[b] = np.median(np.log(sc / s1))
        wl[b] = np.log(np.sum(w * sc) / np.sum(w * s1))
    L0 = np.array([np.log(np.mean(Cc[j]) / np.mean(A[j])) for j in range(n)])
    return dict(label=label, B=B, n_conditions=n, cells_per_condition_median=float(np.median(nc)),
                median_L=float(np.median(L0)), median_L_ci95=[float(np.quantile(med, 0.025)), float(np.quantile(med, 0.975))],
                weighted_log_ratio=float(np.log(np.sum(nc * [np.mean(c) for c in Cc]) / np.sum(nc * [np.mean(a) for a in A]))),
                weighted_log_ratio_ci95=[float(np.quantile(wl, 0.025)), float(np.quantile(wl, 0.975))])


def sensitivity_for_test(contrasts, folds, test):
    """-> dict for analysis/sensitivity_<test>.json from the contrasts of one test and its fold records (as `stats_step.load_fold`)"""
    strata = condition_strata(folds)
    out = dict(test=test, rows="PREREG 9.8 (a)-(e), (j); descriptive: they change no tier", entries={}, mc_labels=[],
               availability=dict(condition_meta=strata is not None, cell_scores=all(os.path.exists(os.path.join(f["dir"], "cell_scores.json")) for f in folds)))
    for key, e in contrasts["contrasts"].items():
        if e.get("hyp") not in ("H1a", "H1b", "H6", "H1c", "H2", "H3", "H4a", "H4b", "H5"):
            continue
        lvl = e.get("holm_level")
        row = dict(hyp=e["hyp"], comp=e["comp"], level=lvl, margins=margin_rows(e, lvl))
        if strata is not None and set(e["L_by_cond"]) <= set(strata):
            row.update(lab_stage_rows(e, strata, lvl))
            lab1 = f"{test}|{e['hyp']}|{e['comp']}|SENS_lab_strat_boot"
            out["mc_labels"].append(lab1)
            row["lab_stratified_bootstrap"] = lab_stratified_bootstrap(e, strata, lab1)
            pairs = cell_pairs(folds, e["comp_by_fold"])
            if pairs is not None:
                lab2 = f"{test}|{e['hyp']}|{e['comp']}|SENS_two_stage_boot"
                out["mc_labels"].append(lab2)
                row["two_stage_bootstrap"] = two_stage_bootstrap(e, pairs, strata, lab2)
            else:
                row["two_stage_bootstrap"] = "not available: a fold run has no cell_scores.json"
        else:
            row["lab_rows"] = "not available: a fold run has no condition_meta.json (or it misses conditions)"
        out["entries"][key] = row
    return out
