"""Pilot P6: physics-informed against data-only learners at the smallest m on ISU training sides (PREREG_v4 17.2 C6, section 12 rule 10; D016 judge lines 173, 320, 342, 384;
D016 proposal 5.6). The reading rule is runs/pilot_P6/RULE.md (committed before the first fit); `aggregate` applies it, nobody chooses.

DEVELOPMENT DATA (ISU), NON-CONFIRMATORY. ISU is not blind (PREREG 3.4). Nothing here is evidence for Samsung. CPU only.

Frame (as P6b, whose helpers are imported unchanged): ISU Test B, five outer folds, only the fold's training side loaded; pseudo-train = nested max-min subset of m = 8; pseudo-test = the
side's other training conditions. Tuning, backbone tournament and the inner-CV window use W = 2 weeks (run.py rule_tune at m < 32), inner_k = 2. The final refits (seeds 0-4) are scored at
every window of cfg["score_windows"] (W = 0, 2, full = 4 weeks), the way run.py scores a k list: one fit per seed, A11 and A12 refit per window (their window features differ).

Usage (from ROOT, interpreter .venv/Scripts/python.exe -P):
    python -P code/pilots/p6_driver.py run [--config code/pilots/p6_config.json] [--out runs/pilot_P6]
    python -P code/pilots/p6_driver.py aggregate [--out runs/pilot_P6]
    python -P code/pilots/p6_driver.py run --smoke --out <scratch dir>     # mechanics only: 1 fold, 2 trials, 2 seeds, steps_scale 0.02; never under runs/pilot_P6
"""
import os
import sys

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import csv
import json
import math
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, HERE)

import p6b_inner_folds as B       # noqa: E402  (helpers of the committed P6b script, imported unchanged)

SCRIPT = os.path.join(HERE, "p6_driver.py")
DEFAULT_CONFIG = os.path.join(HERE, "p6_config.json")
ARM_COST_S = B.ARM_COST_S
PHYS = ("A1", "A2", "A4")
DATA = ("A9", "A11", "A12")


# ============================================================================================ pure helpers (rule; unit-tested without torch)
def side_stat(scores_a, scores_b, stat="median"):
    """scores_*: {cond: score}. -> (stat_a, stat_b, n_common) on the conditions scored by both"""
    common = sorted(set(scores_a) & set(scores_b))
    if not common:
        return float("nan"), float("nan"), 0
    f = np.median if stat == "median" else np.mean
    return float(f([scores_a[c] for c in common])), float(f([scores_b[c] for c in common])), len(common)


def reading(sides):
    """Rule of runs/pilot_P6/RULE.md step 3-5. sides: {fold: (S_A1, S_Dstar)} (finite or nan). -> dict(n_sides, n_data_leads, n_a1_lower, verdict, reason)
    data-only leads on a side iff S(D*) <= S(A1) ('A1 not lower'); triggered iff >= 3 sides with data-only ahead; cleared iff >= 3 sides with A1 lower; else undetermined."""
    ok = {f: v for f, v in sides.items() if v is not None and all(math.isfinite(x) for x in v)}
    lead = {f: bool(v[1] <= v[0]) for f, v in ok.items()}
    nd, na = int(sum(lead.values())), int(sum(not x for x in lead.values()))
    if nd >= 3:
        verdict = "TRIGGERED"
    elif na >= 3:
        verdict = "NOT_TRIGGERED"
    else:
        verdict = "UNDETERMINED"
    return dict(n_sides=len(ok), n_data_leads=nd, n_a1_lower=na, data_leads_by_fold={str(f): lead[f] for f in lead}, verdict=verdict,
                reason=f"data-only learner not behind A1 on {nd} of {len(ok)} evaluable sides (A1 lower on {na}); rule: triggered iff >= 3 of 5 sides with data-only ahead, no margin")


# ============================================================================================ units
def window_rules(cfg, spec):
    from pinnkan.data import WindowRule
    base = WindowRule.for_spec(spec)
    return {lab: WindowRule.for_grid(spec, "full" if lab == "full" else float(lab), base) for lab in cfg["score_windows"]}


def job_arm(task):
    cfg, out_dir, fold, arm_id = task
    path = os.path.join(out_dir, "units", f"f{fold}_{arm_id}.json")
    if os.path.exists(path):
        return dict(kind="arm", fold=fold, arm=arm_id, cpu=json.load(open(path)).get("cpu_seconds", 0.0), skipped=True)
    t0, c0 = time.time(), time.process_time()
    try:
        res = _arm_unit(cfg, out_dir, fold, arm_id)
        res.update(wall_seconds=time.time() - t0, cpu_seconds=time.process_time() - c0)
        B.jdump(res, path)
        return dict(kind="arm", fold=fold, arm=arm_id, cpu=res["cpu_seconds"], wall=res["wall_seconds"], inner_cv=res["tuning"]["inner_cv_pp"], ok=True)
    except Exception as e:  # noqa: BLE001  (a failed arm is recorded, never hidden)
        import traceback
        err = dict(fold=fold, arm=arm_id, error=f"{type(e).__name__}: {e}", traceback=traceback.format_exc(), wall_seconds=time.time() - t0, cpu_seconds=time.process_time() - c0)
        B.jdump(err, os.path.join(out_dir, "units", f"ERROR_f{fold}_{arm_id}.json"))
        return dict(kind="arm", fold=fold, arm=arm_id, cpu=err["cpu_seconds"], wall=err["wall_seconds"], ok=False, error=err["error"])


def _arm_unit(cfg, out_dir, fold, arm_id):
    from pinnkan import tuning
    from pinnkan.arms import ARMS, make_arm
    from pinnkan.data import prepare_many
    from pinnkan.metrics import condition_scores, score_prepared, seed_condition_scores
    k = int(cfg["inner_k"])
    D = B.fold_data(fold, cfg)
    spec, rule, train = D["spec"], D["rule"], D["train"]
    tb = json.load(open(os.path.join(out_dir, "units", f"tournament_f{fold}_k{k}.json")))
    ctx = B.make_ctx(cfg, rule, tb["chosen"])
    r = tuning.tune(arm_id, train, spec, rule, int(cfg["n_trials"]), k, fold, ctx, "cycling")
    hp = r["best_hp"]
    rules = window_rules(cfg, spec)
    labs = list(cfg["score_windows"])
    prep = {lab: prepare_many(D["test"], rules[lab]) for lab in labs}
    wc = {lab: [p.win for p in prep[lab]] for lab in labs}
    y_last = {lab: {p.cell.cell_id: p.win.y_last for p in prep[lab]} for lab in labs}
    clean = {lab: [] for lab in labs}
    rows_seed = {lab: [] for lab in labs}
    nbad = {lab: [] for lab in labs}
    t_fit, arm_seed0 = [], None
    for sd in cfg["final_seeds"]:
        arm, nb_s = None, {}
        for lab in labs:
            if arm is None or ARMS[arm_id].family == "p3":
                t1 = time.time()
                arm = make_arm(arm_id, spec, hp, sd, dict(ctx, rule=rules[lab])).fit(train)
                t_fit.append(time.time() - t1)
            preds = arm.predict(wc[lab])
            cl, nb = B.clean_seedwise(preds, y_last[lab])
            clean[lab].append(cl)
            nbad[lab].append(nb)
            rows_seed[lab].append(score_prepared(cl, prep[lab]))
    per_w = {}
    for lab in labs:
        ens = B.ensemble_forecasts(clean[lab])
        ens_rows = score_prepared(ens, prep[lab])
        cs_ens = condition_scores(ens_rows)
        cs_seed, seed_sd = seed_condition_scores(rows_seed[lab])
        cell_ens = {x["cell"]: x["rmse_pp"] for x in ens_rows}
        cell_seed = {c: float(np.mean([next(x["rmse_pp"] for x in rows if x["cell"] == c) for rows in rows_seed[lab]])) for c in cell_ens}
        per_w[lab] = dict(cond_ens=cs_ens, cond_perseed=cs_seed, seed_sd_of_mean=seed_sd, n_cells=len(prep[lab]), n_conditions=len(cs_ens), nonfinite_per_seed=nbad[lab],
                          ens_le_perseed_every_cell=bool(all(cell_ens[c] <= cell_seed[c] + 1e-9 for c in cell_ens)))
    return dict(fold=fold, arm=arm_id, backbone=tb["chosen"], inner_k=k, score_windows=labs, per_window=per_w,
                endpoint="ensemble of final_seeds forecasts, seed-wise non-finite substitution before averaging",
                tuning=dict(inner_cv_pp=r["inner_cv_pp"], best_hp=hp, n_failed=r["n_failed"], n_trials=r["n_trials"], tuning_seed=r["tuning_seed"], tpe_seed=r["tpe_seed"],
                            n_inner_conditions=r["n_inner_conditions"], median_fit_seconds=r["median_fit_seconds"], grid_edge_hits=B.edge_hits(ARMS[arm_id].space, hp),
                            cond_scores_inner=r["cond_scores"]),
                final_seeds=list(cfg["final_seeds"]), refit_seconds=t_fit, n_params=int(getattr(arm, "n_params", 0)), audit=D["audit"])


# ============================================================================================ run
def cmd_run(args):
    cfg = json.load(open(args.config, encoding="utf8"))
    out_dir = os.path.abspath(args.out)
    smoke = bool(args.smoke)
    if smoke:
        cfg.update(folds=[0], n_trials=2, final_seeds=[0, 1], steps_scale=0.02)
        assert "pilot_P6" not in out_dir.replace("\\", "/").split("/"), "smoke must not write to runs/pilot_P6"
    else:
        assert cfg["steps_scale"] == 1.0 and cfg["final_seeds"] == [0, 1, 2, 3, 4], "the real run uses the ruled settings only"
        dirty = B.git("status", "--porcelain", "--", SCRIPT, args.config, os.path.join(ROOT, "runs", "pilot_P6", "RULE.md"))
        if dirty:
            raise SystemExit(f"driver, config or RULE.md not committed (rule: commit BEFORE the first fit):\n{dirty}")
    os.makedirs(os.path.join(out_dir, "units"), exist_ok=True)
    split_path = os.path.join(ROOT, cfg["split_file"])
    meta_path = os.path.join(out_dir, "run_meta.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {"sessions": []}
    rule_md = os.path.join(ROOT, "runs", "pilot_P6", "RULE.md")
    sess = dict(started=B.now(), started_epoch=time.time(), head_commit=B.git("rev-parse", "HEAD"), script_last_commit=B.git("log", "-1", "--format=%H", "--", SCRIPT),
                script_last_commit_time=B.git("log", "-1", "--format=%cI", "--", SCRIPT), config_last_commit=B.git("log", "-1", "--format=%H", "--", args.config),
                rule_md_last_commit=B.git("log", "-1", "--format=%H", "--", rule_md), rule_md_sha256=B.sha256_file(rule_md),
                script_sha256=B.sha256_file(SCRIPT), config_sha256=B.sha256_file(args.config), p6b_script_sha256=B.sha256_file(B.SCRIPT), split_sha256_before=B.sha256_file(split_path),
                pinnkan_sha256=B.code_hashes(), pinnkan_dirty=B.git("status", "--porcelain", "--", "code/pinnkan").splitlines(), smoke=smoke, workers=int(cfg["workers"]))
    meta["sessions"].append(sess)
    B.jdump(meta, meta_path)
    B.jdump({**cfg, "config_path": args.config}, os.path.join(out_dir, "config_used.json"))
    B.log_line(out_dir, f"P6 run start: smoke={smoke}, folds {cfg['folds']}, arms {cfg['arms']}, windows {cfg['score_windows']}, inner_k {cfg['inner_k']}, N={cfg['n_trials']}, seeds {cfg['final_seeds']}, workers {cfg['workers']}")
    import multiprocessing as mp
    ctx = mp.get_context("spawn")
    cpu_used, abort = 0.0, False
    with ctx.Pool(int(cfg["workers"]), initializer=B._init_worker) as pool:
        t1 = [(cfg, out_dir, f, int(cfg["inner_k"])) for f in cfg["folds"]]
        for r in pool.imap_unordered(B.job_tournament, t1):
            cpu_used += r["cpu"]
            B.log_line(out_dir, f"tournament f{r['fold']}: {r.get('chosen', 'cached')} (cpu {r['cpu']:.0f} s); CPU total {cpu_used / 3600:.3f} h")
        tasks = [(cfg, out_dir, f, a) for f in cfg["folds"] for a in cfg["arms"]]
        tasks.sort(key=lambda t: -ARM_COST_S[t[3]])
        n_done = 0
        for r in pool.imap_unordered(job_arm, tasks):
            n_done += 1
            cpu_used += r["cpu"]
            tag = "ERROR " + r["error"] if not r.get("ok", r.get("skipped", False)) else (f"inner-CV {r['inner_cv']:.3f} pp" if "inner_cv" in r else "cached")
            B.log_line(out_dir, f"[{n_done}/{len(tasks)}] f{r['fold']} {r['arm']}: {tag} (cpu {r['cpu']:.0f} s, wall {r.get('wall', 0):.0f} s); CPU total {cpu_used / 3600:.3f} h")
            if cpu_used / 3600 > float(cfg["cpu_hours_abort"]) and not smoke:
                B.log_line(out_dir, f"ABORT: CPU budget {cfg['cpu_hours_abort']} h exceeded; stopping (the reading is evaluated on the units that exist, RULE.md step 5)")
                abort = True
                pool.terminate()
                break
    sess.update(ended=B.now(), ended_epoch=time.time(), cpu_hours_this_session=cpu_used / 3600, aborted=abort, split_sha256_after=B.sha256_file(split_path), pinnkan_sha256_end=B.code_hashes())
    B.jdump(meta, meta_path)
    B.log_line(out_dir, f"P6 run end: CPU {cpu_used / 3600:.3f} h, wall {(sess['ended_epoch'] - sess['started_epoch']) / 3600:.3f} h, aborted={abort}")


# ============================================================================================ aggregate
def load_units(out_dir, cfg):
    U, errors = {}, []
    for f in cfg["folds"]:
        for a in cfg["arms"]:
            p = os.path.join(out_dir, "units", f"f{f}_{a}.json")
            if os.path.exists(p):
                U[(f, a)] = json.load(open(p))
            else:
                errors.append(f"missing f{f} {a}" + (" (ERROR file exists)" if os.path.exists(os.path.join(out_dir, "units", f"ERROR_f{f}_{a}.json")) else ""))
    return U, errors


def fmt(x, nd=3):
    return "n/a" if x is None or (isinstance(x, float) and not math.isfinite(x)) else f"{x:.{nd}f}"


def cmd_aggregate(args):
    from pinnkan import selectors
    out_dir = os.path.abspath(args.out)
    cfg = json.load(open(os.path.join(out_dir, "config_used.json"), encoding="utf8"))
    meta = json.load(open(os.path.join(out_dir, "run_meta.json")))
    folds, arms, labs, prim = cfg["folds"], cfg["arms"], cfg["score_windows"], cfg["primary_window"]
    U, errors = load_units(out_dir, cfg)
    split_after = B.sha256_file(os.path.join(ROOT, cfg["split_file"]))
    # D* per fold from inner-CV scores only
    dstar, comp = {}, {}
    for f in folds:
        inner = {a: U[(f, a)]["tuning"]["inner_cv_pp"] for a in DATA if (f, a) in U}
        c = selectors.select_comparators(inner, cfg["m"]) if inner else {}
        comp[f] = {"inner_cv_pp": inner, "D*": (c.get("D*") or {}).get("arm"), "complete": bool((c.get("D*") or {}).get("complete"))}
        dstar[f] = comp[f]["D*"]

    def cs(f, a, lab):
        return U[(f, a)]["per_window"][lab]["cond_ens"] if (f, a) in U else None

    def pair(f, a, b, lab, stat="median"):
        ca, cb = (cs(f, a, lab) if a else None), (cs(f, b, lab) if b else None)
        if ca is None or cb is None:
            return None
        sa, sb, n = side_stat(ca, cb, stat)
        return (sa, sb) if n else None

    summary = {"windows": {}}
    reads = {}
    rows_side = []
    for lab in labs:
        w = {}
        # primary: A1 against D*
        sides = {f: (pair(f, "A1", dstar[f], lab) if dstar[f] else None) for f in folds}
        w["primary_A1_vs_Dstar_median"] = reading(sides)
        w["sides_primary_median"] = {str(f): sides[f] for f in folds}
        w["A1_vs_Dstar_mean"] = reading({f: (pair(f, "A1", dstar[f], lab, "mean") if dstar[f] else None) for f in folds})
        # oracle best data-only by the side's own statistic
        orc = {}
        for f in folds:
            best = None
            for a in DATA:
                p = pair(f, "A1", a, lab)
                if p and (best is None or p[1] < best[1][1]):
                    best = (a, p)
            orc[f] = (best[1] if best else None, best[0] if best else None)
        w["oracle_best_data_only_median"] = reading({f: orc[f][0] for f in folds})
        w["oracle_best_data_only_arm_by_fold"] = {str(f): orc[f][1] for f in folds}
        for a in DATA:
            w[f"A1_vs_{a}_median"] = reading({f: pair(f, "A1", a, lab) for f in folds})
        # physics family (min over A1, A2, A4 of the side median) against D*
        fam = {}
        for f in folds:
            if not dstar[f]:
                fam[f] = None
                continue
            vals = {a: pair(f, a, dstar[f], lab) for a in PHYS}
            vals = {a: v for a, v in vals.items() if v}
            if not vals:
                fam[f] = None
                continue
            a_best = min(vals, key=lambda a: vals[a][0])
            fam[f] = (vals[a_best][0], vals[a_best][1])
        w["physics_family_min_vs_Dstar_median"] = reading(fam)
        # paired condition-level descriptive for the primary pair
        pc = {}
        for f in folds:
            if dstar[f] and cs(f, "A1", lab) and cs(f, dstar[f], lab):
                a1, dd = cs(f, "A1", lab), cs(f, dstar[f], lab)
                common = sorted(set(a1) & set(dd))
                lr = [math.log(dd[c] / a1[c]) for c in common]
                pc[str(f)] = dict(n=len(common), median_ln_Dstar_over_A1=float(np.median(lr)), share_A1_lower=float(np.mean([x > 0 for x in lr])))
        w["paired_conditions_A1_vs_Dstar"] = pc
        # table of side medians / means for all arms
        tab = {}
        for a in arms:
            tab[a] = {}
            for f in folds:
                if (f, a) in U:
                    v = list(U[(f, a)]["per_window"][lab]["cond_ens"].values())
                    tab[a][str(f)] = dict(median=float(np.median(v)), mean=float(np.mean(v)), n=len(v))
        w["side_table"] = tab
        summary["windows"][lab] = w
        reads[lab] = w["primary_A1_vs_Dstar_median"]
        for a in arms:
            for f in folds:
                if (f, a) in U:
                    t = tab[a][str(f)]
                    rows_side.append(dict(window=lab, fold=f, arm=a, median_pp=t["median"], mean_pp=t["mean"], n_conditions=t["n"], is_Dstar=int(dstar[f] == a)))
    prim_read = reads[prim]
    complete = not errors
    cpu_s = sum(u.get("cpu_seconds", 0.0) for u in U.values())
    for p in os.listdir(os.path.join(out_dir, "units")):
        if p.startswith("tournament_") or p.startswith("ERROR_"):
            cpu_s += json.load(open(os.path.join(out_dir, "units", p))).get("cpu_seconds", 0.0)
    first_start = min(s["started_epoch"] for s in meta["sessions"])
    last_end = max((s.get("ended_epoch", 0.0) for s in meta["sessions"]), default=0.0)
    session_wall = sum(s.get("ended_epoch", s["started_epoch"]) - s["started_epoch"] for s in meta["sessions"])
    dec = dict(pilot="P6", status="development, non-confirmatory; ISU is not blind (PREREG 3.4); not evidence for Samsung",
               rule_file="runs/pilot_P6/RULE.md",
               rule="stop rule 10 (PREREG section 12): triggered iff A1 is not lower than D* (median pseudo-test condition score) on at least 3 of the 5 ISU training sides at m = 8, W = 2 weeks; no margin",
               stop_rule_10_triggered=bool(prim_read["verdict"] == "TRIGGERED"), verdict=prim_read["verdict"], verdict_reason=prim_read["reason"],
               complete=complete, missing_units=errors, n_sides_evaluable=prim_read["n_sides"], n_sides_data_only_leads=prim_read["n_data_leads"], n_sides_A1_lower=prim_read["n_a1_lower"],
               data_leads_by_fold=prim_read["data_leads_by_fold"], Dstar_by_fold=dstar, primary_window=prim,
               descriptive_other_windows={lab: {"verdict": reads[lab]["verdict"], "n_data_leads": reads[lab]["n_data_leads"], "n_a1_lower": reads[lab]["n_a1_lower"]} for lab in labs if lab != prim},
               design_changed=False, note="the design is not changed on the pilot's size (stop rule 10); the lead tells Shlok if triggered; Shlok may stop before compute is spent")
    B.jdump(dec, os.path.join(out_dir, "decision.json"))
    B.jdump(dict(summary=summary, comparators=comp, split_sha256_before=meta["sessions"][0]["split_sha256_before"], split_sha256_after=split_after,
                 cpu_hours=cpu_s / 3600, wall_hours_first_start_to_last_end=(last_end - first_start) / 3600, wall_hours_sum_of_sessions=session_wall / 3600,
                 fold_audit=[U[(f, a)]["audit"] for f in folds for a in arms[:1] if (f, a) in U]), os.path.join(out_dir, "summary.json"))
    B.jdump([U[(f, a)]["audit"] for f in folds for a in arms[:1] if (f, a) in U], os.path.join(out_dir, "fold_audit.json"))
    with open(os.path.join(out_dir, "per_side_arm.csv"), "w", newline="", encoding="utf8") as fh:
        wr = csv.DictWriter(fh, fieldnames=["window", "fold", "arm", "median_pp", "mean_pp", "n_conditions", "is_Dstar"])
        wr.writeheader()
        wr.writerows(rows_side)
    # tables.md
    L = ["# P6 tables (generated by aggregate; development data, not evidence for Samsung)", ""]
    for lab in labs:
        w = summary["windows"][lab]
        L += [f"## Window W = {lab}" + (" (primary: g1 analogue)" if lab == prim else ""), "", "Side median of the ensemble condition score (pp); D* marked with *.", "",
              "| arm | " + " | ".join(f"fold {f}" for f in folds) + " |", "|---|" + "---|" * len(folds)]
        for a in arms:
            L.append(f"| {a} | " + " | ".join((fmt(w['side_table'][a][str(f)]['median']) + ("*" if dstar[f] == a else "")) if str(f) in w['side_table'][a] else "n/a" for f in folds) + " |")
        L += ["", "| reading | sides with data-only ahead | sides with A1 lower | verdict |", "|---|---|---|---|"]
        for key in ["primary_A1_vs_Dstar_median", "A1_vs_Dstar_mean", "oracle_best_data_only_median", "A1_vs_A9_median", "A1_vs_A11_median", "A1_vs_A12_median", "physics_family_min_vs_Dstar_median"]:
            r = w[key]
            L.append(f"| {key} | {r['n_data_leads']} of {r['n_sides']} | {r['n_a1_lower']} | {r['verdict']} |")
        L += ["", "Paired conditions, A1 against D* (ln(S_D*/S_A1) > 0 means A1 lower):", "", "| fold | D* | n | median ln(D*/A1) | share A1 lower |", "|---|---|---|---|---|"]
        for f in folds:
            p = w["paired_conditions_A1_vs_Dstar"].get(str(f))
            if p:
                L.append(f"| {f} | {dstar[f]} | {p['n']} | {fmt(p['median_ln_Dstar_over_A1'], 4)} | {fmt(p['share_A1_lower'], 3)} |")
        L.append("")
    L += ["## Inner-CV condition-mean score (pp) on the pseudo-train, and D* by fold", "", "| fold | A9 | A11 | A12 | D* |", "|---|---|---|---|---|"]
    for f in folds:
        i = comp[f]["inner_cv_pp"]
        L.append(f"| {f} | " + " | ".join(fmt(i.get(a)) for a in DATA) + f" | {dstar[f]} |")
    L += ["", "## Run facts", "", f"- units complete: {complete}; missing: {errors}", f"- CPU hours (sum over units, tournaments, error files): {cpu_s / 3600:.3f}; wall hours (first start to last end): {(last_end - first_start) / 3600:.3f}; sum of sessions: {session_wall / 3600:.3f}",
          f"- split sha256 before = after: {meta['sessions'][0]['split_sha256_before'] == split_after} ({split_after})",
          f"- failed tuning trials: {sum(U[k]['tuning']['n_failed'] for k in U)}; non-finite seed forecast values: {sum(sum(sum(U[k]['per_window'][l]['nonfinite_per_seed']) for l in labs) for k in U)}",
          f"- ensemble RMSE <= mean per-seed RMSE in every cell of every unit: {all(U[k]['per_window'][l]['ens_le_perseed_every_cell'] for k in U for l in labs)}",
          "- tuned selections: " + "; ".join(f"f{f} {a} {json.dumps(U[(f, a)]['tuning']['best_hp'])}" for f in folds for a in arms if (f, a) in U)]
    open(os.path.join(out_dir, "tables.md"), "w", encoding="utf8").write("\n".join(L) + "\n")
    print(json.dumps(dec, indent=1, default=str))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--config", default=DEFAULT_CONFIG)
    r.add_argument("--out", default=os.path.join(ROOT, "runs", "pilot_P6"))
    r.add_argument("--smoke", action="store_true")
    g = sub.add_parser("aggregate")
    g.add_argument("--out", default=os.path.join(ROOT, "runs", "pilot_P6"))
    a = ap.parse_args()
    {"run": cmd_run, "aggregate": cmd_aggregate}[a.cmd](a)


if __name__ == "__main__":
    main()
