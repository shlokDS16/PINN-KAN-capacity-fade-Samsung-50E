"""Descriptive (no test, no tier, no p-value) post-freeze items for the Paper 7 domain review.
Reads run outputs only (diagnostics.json, tuning_*.json, metrics.json, predictions.csv, window.csv, arm_table.json, reference.json).
Run: MAIN/.venv/Scripts/python.exe -P descriptive_post.py   (CPU, one thread). Writes descriptive_post.json next to itself."""
import json, os
import numpy as np, pandas as pd

MAIN = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
RUNS = os.path.join(MAIN, "runs")
OUT = os.path.join(RUNS, "stats_frozen", "descriptive_post")
J = lambda p: json.load(open(p, encoding="utf8"))
FOLDS = range(5)


# ---------------------------------------------------------------- 1. preregistered diagnostics
def item1():
    rows = []
    runs = [(f"conf_samsung_B_f{f}_m{m}", "B", f, m) for m in (8, 16, 32) for f in FOLDS] + [("conf_samsung_C_f0", "C", 0, None)] + \
           [(f"conf_samsung_S2_f{f}", "S2", f, None) for f in range(4)]
    for name, test, f, m in runs:
        p = os.path.join(RUNS, name)
        if not os.path.exists(os.path.join(p, "diagnostics.json")):
            continue
        d = J(os.path.join(p, "diagnostics.json"))
        r = {"run": name, "test": test, "fold": f, "m": m, "arms": {}}
        for a, v in d["arms"].items():
            e = dict(v)
            tf = os.path.join(p, f"tuning_{a}.json")
            if os.path.exists(tf):
                e["tuning_best_hp_lam_res"] = J(tf).get("best_hp", {}).get("lam_res")
            r["arms"][a] = e
        inv = d["inversion"]
        r["inversion_primary"] = inv.get("primary", {})
        r["inversion_inner_cv"] = inv.get("inner_cv")
        r["inversion_nonconverged_by_call"] = inv.get("nonconverged_by_call")
        r["lam_res_edge_share_over_arms"] = d.get("lam_res_edge_share_over_arms")
        r["basin_and_start_spread_max_over_arm_cells"] = {
            "max_start_spread_pp": max((x["start_spread_pp"]["max"] for x in inv.get("per_arm_cell", []) if x.get("start_spread_pp")), default=None),
            "max_share_forecast_differs_gt_1pp": max((x["basin"]["share_forecast_differs_gt_1pp"] for x in inv.get("per_arm_cell", []) if x.get("basin")), default=None),
            "max_cap_doubling_change_pp": max((x["cap_doubling_change_pp"]["max"] for x in inv.get("per_arm_cell", []) if x.get("cap_doubling_change_pp")), default=None)}
        rows.append(r)
    return rows


def summarise1(rows):
    S = {}
    for test, mm in (("B", None), ("B", 8), ("B", 16), ("B", 32), ("C", None), ("S2", None)):
        sel = [r for r in rows if r["test"] == test and (mm is None or r["m"] == mm)]
        key = test + (f"_m{mm}" if mm else ("_all_m" if test == "B" else ""))
        S[key] = {"n_runs": len(sel), "arms": {}}
        for a in ("A1", "A4", "A13", "A15", "G15", "A2", "A9"):
            ent = S[key]["arms"].setdefault(a, {})
            lam = [r["arms"][a]["lam_res"] for r in sel if a in r["arms"] and "lam_res" in r["arms"][a]]
            if lam:
                vals, cnt = np.unique(lam, return_counts=True)
                ent.update({"n_runs_with_lam": len(lam), "lam_counts": {str(v): int(c) for v, c in zip(vals, cnt)},
                            "n_at_lower_edge_flag": int(sum(1 for r in sel if a in r["arms"] and r["arms"][a].get("lam_res_at_lower_edge"))),
                            "n_at_upper_edge_flag": int(sum(1 for r in sel if a in r["arms"] and r["arms"][a].get("lam_res_at_upper_edge")))})
            rat = [r["arms"][a]["delta_sd_over_tau"] for r in sel if a in r["arms"] and "delta_sd_over_tau" in r["arms"][a]]
            if rat:
                nf = sum(1 for r in sel if a in r["arms"] and r["arms"][a].get("delta_sd_flag_outside_0p5_2"))
                ent.update({"delta_sd_over_tau_min": float(min(rat)), "delta_sd_over_tau_median": float(np.median(rat)), "delta_sd_over_tau_max": float(max(rat)),
                            "n_ratio": len(rat), "n_flagged_outside_0p5_2": int(nf), "n_inside_0p5_2": int(len(rat) - nf)})
            clip = [r["arms"][a]["clip_fraction"] for r in sel if a in r["arms"] and "clip_fraction" in r["arms"][a]]
            if clip:
                ent.update({"clip_fraction_min": float(min(clip)), "clip_fraction_mean": float(np.mean(clip)), "clip_fraction_max": float(max(clip)), "n_clip": len(clip)})
        ninv = nnc = 0
        minshare = 1.0
        byarm = {}
        for r in sel:
            for k, v in r["inversion_primary"].items():
                ninv += v["n_inverted"]
                nnc += v["n_nonconverged"]
                if v["n_inverted"]:
                    minshare = min(minshare, v["convergence_share"])
                b = byarm.setdefault(k.split("|")[0], [0, 0])
                b[0] += v["n_inverted"]
                b[1] += v["n_nonconverged"]
        S[key]["inversion_primary_outer"] = {"n_inverted": ninv, "n_nonconverged": nnc, "share_converged": (1 - nnc / ninv) if ninv else None,
                                             "min_run_arm_k_share": minshare, "by_arm": {a: {"n_inverted": b[0], "n_nonconverged": b[1]} for a, b in sorted(byarm.items())}}
        ic = [r["inversion_inner_cv"] for r in sel if r["inversion_inner_cv"]]
        if ic:
            S[key]["inversion_inner_cv"] = {"n_inverted": int(sum(x["n_inverted"] for x in ic)), "n_nonconverged": int(sum(x["n_nonconverged"] for x in ic))}
        S[key]["max_over_runs"] = {k_: max((r["basin_and_start_spread_max_over_arm_cells"][k_] or 0) for r in sel) for k_ in
                                   ("max_start_spread_pp", "max_share_forecast_differs_gt_1pp", "max_cap_doubling_change_pp")}
    return S


# ---------------------------------------------------------------- 2. error by horizon
ARMS_H = ["A1", "D*", "A9", "A10", "R1"]


def horizon():
    out = {}
    for g, (m, k) in {"g1": (8, "2"), "g4": (32, "full")}.items():
        acc = {a: {} for a in ARMS_H}
        dstar = {}
        for f in FOLDS:
            mt = J(os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}", "metrics.json"))
            ds = mt["comparators"]["D*"]
            dstar[f] = ds
            bk = mt["outer_test_by_k"][k]
            for a in ARMS_H:
                src = ds if a == "D*" else a
                for h, v in bk[src]["horizon_rmse_pp"].items():
                    acc[a].setdefault(int(h), []).append((f, v["rmse_pp"], v["n"]))
        res = {}
        for a in ARMS_H:
            res[a] = {}
            for h in sorted(acc[a]):
                L = acc[a][h]
                n = sum(x[2] for x in L)
                res[a][str(h)] = {"pooled_rmse_pp_nweighted": float(np.sqrt(sum(x[2] * x[1] ** 2 for x in L) / n)), "mean_of_fold_rmse_pp": float(np.mean([x[1] for x in L])),
                                  "n_forecast_points": int(n), "n_folds": len(L)}
        out[g] = {"cell": f"m={m}, k={k}", "dstar_arm_by_fold": dstar, "by_arm": res,
                  "pooling": "per run the writer's horizon_rmse_pp[h] = RMSE over cells having an h-th post-window check-up (n = those cells), seed-ensemble; pooled here as sqrt(sum n*rmse^2/sum n) over the 5 folds; mean of fold RMSE also given; no condition weighting; descriptive"}
    return out


# ---------------------------------------------------------------- shared loader
def load_pred(f, m, phase, arm):
    p = pd.read_csv(os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}", "predictions.csv"), usecols=["phase", "arm", "seed", "cell_id", "cond", "t", "pred_retention", "true_retention"])
    p = p[(p.phase == phase) & (p.arm == arm)]
    return p[p.seed == p.seed.min()]  # R1 is deterministic; one seed's rows


def q(s):
    return {"min": float(s.min()), "q25": float(s.quantile(.25)), "median": float(s.median()), "q75": float(s.quantile(.75)), "max": float(s.max())}


# ---------------------------------------------------------------- 3. size context
def size_context():
    out = {}
    for g, (m, ph) in {"g1": (8, "outer_test_k2"), "g4": (32, "outer_test_kfull")}.items():
        recs = []
        for f in FOLDS:
            p = load_pred(f, m, ph, "R1")
            win = pd.read_csv(os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}", "window.csv"))
            for cid, d in p.groupby("cell_id"):
                d = d.sort_values("t")
                w = win[win.cell_id == cid].sort_values("t")
                t_ref = float(w.t.iloc[0])
                recs.append(dict(fold=f, cell=cid, cond=d.cond.iloc[0], n_fc=len(d), t_first=float(d.t.min()) - t_ref, t_last=float(d.t.max()) - t_ref,
                                 y_final=float(d.true_retention.iloc[-1]), y_win=float(d.pred_retention.iloc[0])))
        df = pd.DataFrame(recs)
        df["fade_ref_pp"] = (1 - df.y_final) * 100
        df["fade_after_window_pp"] = (df.y_win - df.y_final) * 100
        out[g] = {"n_scored_cells": int(len(df)), "n_conditions": int(df.cond.nunique()), "n_forecast_points_per_cell": q(df.n_fc),
                  "days_from_reference_to_first_forecast": q(df.t_first), "days_from_reference_to_last_checkup": q(df.t_last),
                  "forecast_span_days_first_to_last": q(df.t_last - df.t_first),
                  "observed_retention_at_last_checkup_pct": q(df.y_final * 100), "observed_fade_reference_to_last_checkup_pp": q(df.fade_ref_pp),
                  "observed_fade_window_end_to_last_checkup_pp": q(df.fade_after_window_pp),
                  "n_cells_with_last_retention_le_0.80": int((df.y_final <= 0.80).sum()),
                  "note": "days measured from the reference check-up (first row of window.csv, t = reference); EFC is not in the run outputs read (not computed)"}
    ref = J(os.path.join(RUNS, "stats_frozen", "analysis", "reference.json"))
    out["reference_floor"] = ref["values"]
    out["reference_floor_definition"] = ref["definition"]
    return out


# ---------------------------------------------------------------- 4. A10 vs A1 numbers
def a10_vs_a1():
    a = J(os.path.join(RUNS, "stats_frozen", "post", "arm_table.json"))
    out = {}
    for lab, cell in (("g1", "8|2"), ("g4", "32|full")):
        c = a["cells"][cell]
        out[lab] = {"key": f"cells['{cell}'][arm]['mean_pp']", "A1": c["A1"]["mean_pp"], "A10": c["A10"]["mean_pp"], "A10P": c["A10P"]["mean_pp"], "R1": c["R1"]["mean_pp"], "R2": c["R2"]["mean_pp"],
                    "A1_n_params_mean": c["A1"]["n_params"], "A10_n_params": c["A10"]["n_params"], "A1_fit_seconds": c["A1"]["fit_seconds"], "A10_fit_seconds": c["A10"]["fit_seconds"],
                    "n_conditions": c["A1"]["n_conditions"]}
    for lab in ("test_c", "s2"):
        out[lab] = {"key": f"{lab}[arm]['mean_pp']", "A1": a[lab]["A1"]["mean_pp"], "A10": a[lab]["A10"]["mean_pp"], "A10P": a[lab]["A10P"]["mean_pp"], "n_conditions": a[lab]["A1"]["n_conditions"]}
    return out


# ---------------------------------------------------------------- 5. EXPLORATORY sqrt(t) through the window
def sqrt_baseline():
    out = {}
    for g, (m, k) in {"g1": (8, "2"), "g4": (32, "full")}.items():
        ph = "outer_test_k" + k
        kk = {"2": 2, "full": 4}[k]
        rows = []
        bad_last = bad_first = bad_k = 0
        for f in FOLDS:
            win = pd.read_csv(os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}", "window.csv"))
            p1 = load_pred(f, m, ph, "R1")
            for cid, d in p1.groupby("cell_id"):
                d = d.sort_values("t")
                w = win[win.cell_id == cid].sort_values("t")
                t0, y0 = float(w.t.iloc[0]), float(w.retention.iloc[0])
                post = w.iloc[1:]
                ke = int((post.t < d.t.iloc[0]).sum())  # window = post-reference points before the first forecast check-up
                wp = post.iloc[:ke]
                bad_k += int(ke < 1 or ke > kk)
                bad_last += int(abs(wp.retention.iloc[-1] - d.pred_retention.iloc[0]) > 1e-9)  # R1's carried value must equal the last window point
                x = np.sqrt(wp.t.values.astype(float) - t0)
                b = float(np.sum(x * (y0 - wp.retention.values)) / np.sum(x * x))  # LS of (y0 - y) = b sqrt(t - t0), through the origin; fitted on window points only
                pred = y0 - b * np.sqrt(d.t.values.astype(float) - t0)
                e = (pred - d.true_retention.values) * 100
                e1 = (d.pred_retention.values - d.true_retention.values) * 100
                rows.append(dict(fold=f, cell=cid, cond=d.cond.iloc[0], k_eff=ke, b=b, rmse_sqrt=float(np.sqrt(np.mean(e ** 2))), rmse_R1=float(np.sqrt(np.mean(e1 ** 2))), n_fc=len(d)))
        df = pd.DataFrame(rows)
        cs = df.groupby("cond")[["rmse_sqrt", "rmse_R1"]].mean()
        out[g] = {"cell": f"folds 0-4 of m={m} runs, k={k} (baseline and R1 use no trained model, so do not depend on m)", "n_cells": int(len(df)), "n_conditions": int(len(cs)),
                  "mean_condition_rmse_pp_sqrt": float(cs.rmse_sqrt.mean()), "mean_condition_rmse_pp_R1_recomputed": float(cs.rmse_R1.mean()),
                  "median_condition_rmse_pp_sqrt": float(cs.rmse_sqrt.median()), "median_condition_rmse_pp_R1": float(cs.rmse_R1.median()),
                  "worst_condition_rmse_pp_sqrt": float(cs.rmse_sqrt.max()), "worst_condition_rmse_pp_R1": float(cs.rmse_R1.max()),
                  "n_conditions_sqrt_lt_R1": int((cs.rmse_sqrt < cs.rmse_R1).sum()),
                  "validation": {"cells_checked": int(len(df)), "R1_value_not_equal_last_window_point": bad_last, "k_eff_outside_[1,k]": bad_k},
                  "k_eff_counts": {str(a): int(v) for a, v in df.k_eff.value_counts().items()}, "n_cells_b_negative": int((df.b < 0).sum()), "b_median": float(df.b.median())}
        out[g]["_cell_rows"] = rows
    return out


def main():
    r1 = item1()
    res = {"labels": {"item5": "EXPLORATORY, post hoc, not preregistered; descriptive; no test, no tier"}, "item1_per_run": r1, "item1_summary": summarise1(r1), "item2_horizon": horizon(),
           "item3_size_context": size_context(), "item4_a10_vs_a1": a10_vs_a1(), "item5_exploratory_sqrt": sqrt_baseline()}
    json.dump(res, open(os.path.join(OUT, "descriptive_post.json"), "w", encoding="utf8"), indent=1, default=float)
    print("ok")


if __name__ == "__main__":
    main()
