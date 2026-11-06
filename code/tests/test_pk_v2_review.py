"""Fixes of the independent review of build_v2 (runs/build_v2/CODE_REVIEW.md): one test per finding.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_v2_review.py -q"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

from pinnkan import stats_rows as R
from pinnkan import stats_v4 as v4
from test_pk_v2_stats import CONDS, FOLD, LABS, make_store


# ------------------------------------------------------------------------------------------------ I1
def test_I1_the_T9_clause_takes_W_only_from_forms_that_are_reverse_S():
    store = make_store(A10g1=-0.5)                                  # both forms better than A1 by exp(0.5)
    store.tables[(8, "2")]["A10P"] = {c: 2.0 * np.exp(0.1) for c in CONDS}        # the as-published form is WORSE than A1: not reverse S, its effect is negative
    out = v4.run_v4(store)
    o = out["outcome"]
    assert o["M2"] and out["secondary"]["tests"]["QA10_g1"]["reverse_S"]["A10"]["rejected"] and not out["secondary"]["tests"]["QA10_g1"]["reverse_S"]["A10P"]["rejected"]
    assert o["abstract_sentence"].endswith("was 39.3 % more accurate still at this cell (95 % interval [39.3, 39.3]).")
    assert "-" not in o["abstract_sentence"].split("semi-empirical model was")[1]            # no negative effect printed


# ------------------------------------------------------------------------------------------------ I2
def test_I2_most_is_recomputed_under_the_downgrade_rows():
    good = make_store(P1g1=np.log(1.3), A9g1=np.log(1.2))            # d_c > 0 for every condition
    bad = make_store(P1g1=np.log(1.6), A9g1=np.log(1.1))             # same P1 / P2 / P3 outcomes, but the law share is below half of the total: d_c < 0
    rule = v4.resolve_config()[0]
    out = v4.run_v4(good)
    assert out["most_test"]["most"]
    assert R.row_tiers(out, good, rule)["most"] is True and R.row_tiers(out, bad, rule)["most"] is False
    assert R.row_tiers(out, bad, rule, cells="g1")["most"] is False              # row (iv) covers it too
    full = R.run_v4_full(good, {"e1_prime_approved": True}, retain_all=bad, B=500)
    assert full["downgrade"]["lowest_over_rows"]["most"] is False and full["most_test"]["most"] is False
    assert full["outcome"]["extent_clause"] == "e1'" and "most of the advantage" not in full["outcome"]["abstract_sentence"]
    lab = R.lab_stratified_tiers(out, good, B=500)[0]
    assert lab["most"] is True
    labs = {c: ("A" if i < 32 else "B") for i, c in enumerate(CONDS)}
    store = make_store(P1g1=np.log(1.3), A9g1=np.array([np.log(1.2)] * 32 + [np.log(1.01)] * 8))
    store.lab = labs
    assert R.lab_stratified_tiers(v4.run_v4(store), store, B=500)[0]["most"] is not None


# ------------------------------------------------------------------------------------------------ I3
def test_I3_missing_k_arms_raise_unless_chain_k_is_struck_by_config():
    store = make_store(k_chain=False)
    with pytest.raises(v4.ChainKMissingError):
        v4.run_v4(store)
    out = v4.run_v4(store, {"k_chain_struck": True})["primary"]
    assert out["k_chain_struck"] and out["initial_levels"]["P1N"] == pytest.approx(0.025) and out["initial_levels"]["K1"] == 0.0
    ok = v4.run_v4(make_store())["primary"]
    assert not ok["k_chain_struck"] and ok["initial_levels"]["P1N"] == pytest.approx(0.0195) and ok["initial_levels"]["K1"] == pytest.approx(0.0055)
    partial = make_store()
    del partial.tables[(32, "full")]["G15"]
    with pytest.raises(v4.ChainKMissingError):
        v4.run_v4(partial)


# ------------------------------------------------------------------------------------------------ I4 and the matched budget of A15 / G15
def test_I4_config_symbolic_reaches_the_arm_and_a_cap_that_disagrees_with_the_library_file_refuses_to_start(tmp_path, monkeypatch):
    from pinnkan import arms as A, run, symbolic as S
    base = {"dataset": "synthetic", "arms": ["A15"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.04, "seeds": [0], "mode": "inner", "diagnostics": False,
            "synthetic": {"kind": "G0", "n_cyc_cond": 12, "n_sto_cond": 5, "reps": 2, "seed": 3}}
    monkeypatch.setattr(S, "library_file_cap", lambda path=S.LIB_FILE: 3)
    with pytest.raises(run.ConfigError, match="disagrees"):
        run.run({**base, "run_id": "bad", "symbolic": {"cap": 2}}, runs_dir=str(tmp_path))
    with pytest.raises(run.ConfigError, match="unknown symbolic"):
        run.run({**base, "run_id": "bad2", "symbolic": {"capp": 3}}, runs_dir=str(tmp_path))
    seen = []
    orig = S.resolve_cap
    monkeypatch.setattr(S, "resolve_cap", lambda cap=None: (seen.append(cap), orig(cap))[1])
    run.run({**base, "run_id": "ok", "symbolic": {"cap": 3, "refit_frac": 0.25}}, runs_dir=str(tmp_path))
    assert seen and all(c == 3 for c in seen)                            # the config value is what the arm resolved
    assert json.load(open(os.path.join(tmp_path, "ok", "config.json")))["symbolic"] == {"cap": 3, "refit_frac": 0.25}      # and it is part of the hashed config


def test_matched_budget_a15_g15_use_no_more_optimisation_steps_than_one_a1_fit(monkeypatch):
    from pinnkan import arms as A, data as D, pinn, symbolic as S, synth
    from pinnkan.specs import SPECS
    SPEC = SPECS["synthetic"]
    S0 = synth.make_synthetic("G0", n_cyc_cond=10, n_sto_cond=4, reps=2, seed=4)
    tr, _ = synth.split_conditions(S0.cells, 0.25, 4)
    calls = []
    orig = A.fit_pinn
    monkeypatch.setattr(A, "fit_pinn", lambda *a, **k: (calls.append(k.get("steps")), orig(*a, **k))[1])
    ctx = {"backbone": "self_limiting", "steps_scale": 0.05, "symbolic": {"cap": 3}}
    a1 = A.make_arm("A1", SPEC, A.default_hp("A1"), 0, ctx).fit(tr)
    n_a1 = calls[-1]
    for aid in ("A15", "G15"):
        calls.clear()
        arm = A.make_arm(aid, SPEC, A.default_hp(aid), 0, ctx).fit(tr)
        assert len(calls) == 2 and sum(calls) == n_a1 == arm.total_steps
    calls.clear()
    A.make_arm("A15", SPEC, A.default_hp("A15"), 0, {**ctx, "symbolic": {"cap": 3, "refit_frac": 0.25}}).fit(tr)
    assert sum(calls) == n_a1 and calls[1] < calls[0]


# ------------------------------------------------------------------------------------------------ I6, M9
def _grid_runs(tmp, skip=None, extra=None, design="R2", seed_files=True, comp_complete=True, k_full=4, drop_cond=None):
    """a complete fake Design R2 grid: 5 folds x m in (8, 16, 32), k labels per k_full, 8 conditions per fold"""
    dirs = []
    labels = ["0", "full"] if k_full == 2 else ["0", "2", "full"]
    for f in range(5):
        conds = CONDS[8 * f:8 * f + 8]
        if drop_cond and f == 0:
            conds = conds[:-1]
        for m in (8, 16, 32):
            d = os.path.join(tmp, f"f{f}_m{m}")
            os.makedirs(d)
            json.dump({"m": m, "fold": f, "design": design, "inner_k": 2}, open(os.path.join(d, "config.json"), "w"))
            json.dump({"k_labels": labels, "k_primary": "full", "k_full": k_full}, open(os.path.join(d, "metrics.json"), "w"))
            json.dump({"D*": {"arm": "A9", "complete": comp_complete}, "AG": {"arm": "A4", "complete": True}}, open(os.path.join(d, "comparators.json"), "w"))
            for kl in labels:
                suf = "" if kl == "full" else f"_k{kl}"
                sc = {a: {c: 2.0 * (1.0 + 0.05 * i) for c in conds} for i, a in enumerate(["A1", "A9", "A4", "A2", "A10", "A10P", "A13", "A15", "G15"])}
                if skip and (m, kl, f) == skip[:3]:
                    del sc[skip[3]]
                json.dump(sc, open(os.path.join(d, f"condition_scores{suf}.json"), "w"))
                if seed_files and not (extra == "partial_seed" and f == 2):
                    json.dump(sc, open(os.path.join(d, f"condition_scores_seed{suf}.json"), "w"))
                json.dump({c: {"n_cells": 3, "lab": {LABS[c]: 3}, "stage": {"1": 3}} for c in conds}, open(os.path.join(d, f"condition_meta{suf}.json"), "w"))
            dirs.append(d)
    if extra == "legacy":
        open(os.path.join(dirs[0], "OUT_OF_SCOPE_V3_LEGACY"), "w").write("x")
    return dirs


def test_I6_a_complete_grid_passes_and_every_gap_is_named(tmp_path):
    ok = _grid_runs(str(tmp_path / "ok"), ) if os.makedirs(str(tmp_path / "ok")) is None else None
    st = v4.Store.from_runs(ok, strict=True)
    assert st.check_complete()
    cases = {
        "missing arm": (dict(skip=(8, "2", 3, "A10P")), "arm A10P"),
        "missing cell": (dict(skip=(32, "full", 4, "A15")), "arm A15"),
        "n 39": (dict(drop_cond=True), "A1 has 39 conditions"),
        "selector incomplete": (dict(comp_complete=False), "incomplete candidate set"),
    }
    for name, (kw, needle) in cases.items():
        d = str(tmp_path / name.replace(" ", "_"))
        os.makedirs(d)
        runs = _grid_runs(d, **kw)
        with pytest.raises(v4.IncompleteStoreError, match=needle):
            v4.Store.from_runs(runs, strict=True).check_complete()
    d = str(tmp_path / "folds")
    os.makedirs(d)
    runs = [r for r in _grid_runs(d) if "f4_m8" not in r]
    with pytest.raises(v4.IncompleteStoreError, match="folds"):
        v4.Store.from_runs(runs, strict=True).check_complete()
    d = str(tmp_path / "cell")
    os.makedirs(d)
    runs = [r for r in _grid_runs(d) if "_m16" not in r]
    with pytest.raises(v4.IncompleteStoreError, match=r"cell \(16"):
        v4.Store.from_runs(runs, strict=True).check_complete()
    # k_full = 2 merges the k = 2 cell: the grid has 6 cells and the check follows
    d = str(tmp_path / "kf2")
    os.makedirs(d)
    assert v4.Store.from_runs(_grid_runs(d, k_full=2), strict=True).check_complete()


def test_M9_runs_of_another_design_legacy_markers_and_mixed_score_kinds_are_refused(tmp_path):
    for name, kw in (("legacy", dict(extra="legacy")), ("v3", dict(design="V3_legacy")), ("partial", dict(extra="partial_seed"))):
        d = str(tmp_path / name)
        os.makedirs(d)
        with pytest.raises(v4.IncompleteStoreError):
            v4.Store.from_runs(_grid_runs(d, **kw))
    d = str(tmp_path / "none")
    os.makedirs(d)
    assert v4.Store.from_runs(_grid_runs(d, seed_files=False)).seed_tables is None                  # all or none
    d = str(tmp_path / "nodesign")
    os.makedirs(d)
    runs = _grid_runs(d)
    for r in runs:
        c = json.load(open(os.path.join(r, "config.json")))
        del c["design"]
        json.dump(c, open(os.path.join(r, "config.json"), "w"))
    v4.Store.from_runs(runs)                                                                       # tolerated when not strict (old fake runs)
    with pytest.raises(v4.IncompleteStoreError):
        v4.Store.from_runs(runs, strict=True)


# ------------------------------------------------------------------------------------------------ I5, M5
def _item_f_before(tmp, dirs):
    import time
    fdir = os.path.join(tmp, "prereg")
    v4.write_item_f(fdir, {"rho_fold": 0.0})
    old = time.time() - 5000
    os.utime(os.path.join(fdir, v4.ITEM_F_FILE), (old, old))
    h = os.path.join(fdir, v4.ITEM_F_HASH)
    rec = json.load(open(h))
    rec["written_unix"] = old
    json.dump(rec, open(h, "w"))
    for d in dirs:
        json.dump({"passed": True, "max_abs_diff": 0.0, "n_rows": 5, "per_arm_seed": {}}, open(os.path.join(d, "invariance.json"), "w"))
    return fdir, rec["sha256"]


def test_I5_run_stats_v4_goes_through_the_rows_the_gate_and_marks_the_result_provisional(tmp_path):
    from pinnkan import stats_step as ss
    tmp = str(tmp_path)
    os.makedirs(tmp + "/g")
    dirs = _grid_runs(tmp + "/g")
    fdir, sha = _item_f_before(tmp, dirs)
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, {"k_chain_struck": False}, item_f_dir=fdir, item_f_sha256=sha) if False else None
    # complete grid but the scores are constant ratios: the K arms exist, so chain K is evaluated
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    assert out["status"]["provisional"] and set(out["status"]["rows_not_run"]) == {"lab_indicator", "retain_all", "random_subset"} and out["status"]["gate_not_evaluated"] == ["PC-1"]
    assert out["downgrade"]["rows_run"] == ["lab_stratified"] and out["outcome"]["provisional"] is True and out["outcome"]["provisional_downgrade_rows_incomplete"] is True
    assert out["gate_G"]["tripped"] is False and os.path.isfile(os.path.join(tmp, "an", "controls.json"))
    # all three re-run rows supplied (here: the same runs): rows run; PC-1 still unevaluated, so still provisional for that reason only
    out2 = ss.run_stats_v4(os.path.join(tmp, "an2"), dirs, item_f_dir=fdir, row_runs={"lab_indicator": dirs, "retain_all": dirs, "random_subset": [dirs, dirs, dirs]})
    assert out2["status"]["rows_not_run"] == [] and out2["status"]["gate_not_evaluated"] == ["PC-1"] and out2["status"]["provisional"]
    # NC-1 tripped in one run: gate G, no title, no claim
    json.dump({"passed": False, "max_abs_diff": 1e-3, "n_rows": 5, "per_arm_seed": {}}, open(os.path.join(dirs[0], "invariance.json"), "w"))
    out3 = ss.run_stats_v4(os.path.join(tmp, "an3"), dirs, item_f_dir=fdir)
    assert out3["gate_G"]["tripped"] and out3["outcome"]["gate_G"] and out3["outcome"]["title"] is None


def test_I5_cli_routes_design_r2_through_the_same_function(tmp_path):
    from pinnkan import stats_step as ss
    tmp = str(tmp_path)
    os.makedirs(tmp + "/g")
    dirs = _grid_runs(tmp + "/g")
    fdir, sha = _item_f_before(tmp, dirs)
    ss.main(["--analysis-dir", tmp + "/cli", "--runs", "B=" + ",".join(dirs), "--design", "r2", "--item-f-dir", fdir, "--item-f-sha256", sha, "--row", "retain_all=" + ",".join(dirs)])
    out = json.load(open(tmp + "/cli/contrasts_v4_B.json"))
    assert out["downgrade"]["rows_run"] == ["lab_stratified", "retain_all"] and out["status"]["provisional"]


def test_M5_item_f_hash_can_be_pinned_outside_the_file_system_and_inner_folds_come_from_the_run(tmp_path):
    tmp = str(tmp_path)
    os.makedirs(tmp + "/g")
    dirs = _grid_runs(tmp + "/g")
    fdir, sha = _item_f_before(tmp, dirs)
    assert v4.require_item_f(fdir, dirs, sha) == {"rho_fold": 0.0}
    with pytest.raises(v4.ItemFError, match="pinned"):
        v4.require_item_f(fdir, dirs, "0" * 64)
    # inner_folds.json is written by the run and read by item_f_from_runs
    from pinnkan import run
    d = run.run({"dataset": "synthetic", "run_id": "if", "arms": ["A9", "R2"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.04, "seeds": [0], "mode": "inner", "diagnostics": False,
                 "synthetic": {"kind": "G0", "n_cyc_cond": 16, "n_sto_cond": 6, "reps": 2, "seed": 3}}, runs_dir=tmp)
    fo = json.load(open(os.path.join(d, "inner_folds.json")))
    td = json.load(open(os.path.join(d, "tuning_done.json")))
    assert set(fo) == set(td["arms"]["A9"]["cond_scores"]) and set(fo.values()) == {0, 1}


# ------------------------------------------------------------------------------------------------ I7
def test_I7_mean_against_median_rule_adds_mean_bca_and_worst_condition_when_the_signs_disagree():
    L = np.array([0.3] * 25 + [-3.0] * 15)                          # median log ratio > 0 (A1 better) but the mean pp difference < 0 (a few conditions where A1 is far worse)
    out = v4.run_v4(make_store(P1g1=L))
    mm = out["mean_vs_median"]
    r = mm["contrasts"]["P1"]
    assert r["disagree"] and r["median_L"] > 0 and r["mean_pp"] < 0 and "P1" in mm["triggered"] and r["mean_pp_ci"] is not None
    assert r["worst_condition_pp"]["target"] == pytest.approx(2.0) and r["worst_condition_pp"]["comparator"] == pytest.approx(2.0 * np.exp(0.3))
    add = [a for a in mm["abstract_additions"] if a.startswith("For P1 ")][0]
    assert "mean paired difference was -" in add and "95 % BCa interval [" in add and "worst-condition error" in add
    assert out["outcome"]["abstract_additions"] == mm["abstract_additions"]
    clean = v4.run_v4(make_store())["mean_vs_median"]
    assert clean["triggered"] == [] and clean["abstract_additions"] == [] and {"P1", "P2", "K1", "K2", "QH_g1", "QT_g1", "QA10_g1:A10", "QA10_g1:A10P"} <= set(clean["contrasts"])


# ------------------------------------------------------------------------------------------------ minors
CFGM = {"dataset": "synthetic", "arms": ["A2", "A9", "R2"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.04, "seeds": [0, 1], "mode": "confirmatory", "diagnostics": False,
        "synthetic": {"kind": "G0", "n_cyc_cond": 16, "n_sto_cond": 6, "reps": 2, "seed": 3}}


def test_M1_reported_fit_time_is_the_fit_alone(tmp_path):
    from pinnkan import run
    d = run.run({**CFGM, "run_id": "m1", "k": "grid", "window": {"k_cycling": 4}}, runs_dir=str(tmp_path))
    t = json.load(open(os.path.join(d, "timings.json")))["A9"]
    assert 0 < t["refit_seed0_seconds"] < t["refit_seed0_total_seconds"]            # the total includes predict at three k and the NC-1 re-predicts
    m = json.load(open(os.path.join(d, "metrics.json")))["outer_test"]["A9"]
    assert m["fit_seconds_one_fit"] == pytest.approx(np.mean([t["refit_seed0_seconds"], t["refit_seed1_seconds"]]))


def test_M3_a_real_data_grid_run_needs_the_counted_window(tmp_path):
    from pinnkan import run
    with pytest.raises(run.ConfigError, match="k_cycling"):
        run.run({"run_id": "m3", "dataset": "samsung", "test": "B", "fold": 0, "mode": "inner", "arms": ["R2"], "m": 8}, runs_dir=str(tmp_path))
    with pytest.raises(run.ConfigError, match="k_cycling"):
        run.run({"run_id": "m3b", "dataset": "samsung", "test": "B", "fold": 0, "mode": "inner", "arms": ["R2"], "k": "grid", "window": {"k_cycling": 4}}, runs_dir=str(tmp_path))


def test_M4_auto_budget_is_refused_in_a_real_data_confirmatory_run_and_sym_arms_count_for_the_partial_plan(tmp_path):
    from pinnkan import run, tuning
    with pytest.raises(run.ConfigError, match="auto_budget"):
        run.run({"run_id": "m4", "dataset": "isu", "test": "B", "fold": 0, "mode": "confirmatory", "arms": ["R1"], "auto_budget": True}, runs_dir=str(tmp_path))
    assert tuning.choose_budget({"A15": 95.0, "A2": 5.0})["inner_k"] == 2 and tuning.choose_budget({"A15": 50.0, "A2": 5.0})["n_trials"] == 20


def test_M2_p6b_decision_hash_must_be_in_the_hashed_config_and_the_pinned_subsets_file_is_checked(tmp_path, monkeypatch):
    from pinnkan import run
    import hashlib
    yes = tmp_path / "yes.json"
    yes.write_text(json.dumps({"adopt": True}))
    base = {"dataset": "synthetic", "arms": ["R2"], "n_trials": 1, "steps_scale": 0.04, "seeds": [0], "mode": "inner", "diagnostics": False, "m": 8,
            "synthetic": {"kind": "G0", "n_cyc_cond": 20, "n_sto_cond": 6, "reps": 2, "seed": 3}}
    with pytest.raises(run.ConfigError, match="p6b_decision_sha256"):
        run.run({**base, "run_id": "a", "inner_k_thin": 4, "p6b_decision": str(yes)}, runs_dir=str(tmp_path))
    with pytest.raises(run.ConfigError, match="p6b_decision_sha256"):
        run.run({**base, "run_id": "b", "inner_k_thin": 4, "p6b_decision": str(yes), "p6b_decision_sha256": "0" * 64}, runs_dir=str(tmp_path))
    run.run({**base, "run_id": "c", "inner_k_thin": 4, "p6b_decision": str(yes), "p6b_decision_sha256": hashlib.sha256(yes.read_bytes()).hexdigest()}, runs_dir=str(tmp_path))
    # the pinned subsets file of the repository agrees with the selector for the real split ids (identifiers only)
    from pinnkan import subsets
    pin = json.load(open(os.path.join(ROOT, "runs", "prereg", "subsets.json")))
    sp = json.load(open(os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json")))["B"]["folds"]
    for f in ("0", "3"):
        order = subsets.order_for_ids(sp[f]["train_cycling_conditions"])
        assert pin["folds"][f]["subsets"]["8"] == order[:8]


def test_M6_nc1_full_scrambles_after_each_k_window(tmp_path):
    from pinnkan import negcontrol, run
    cfg = {**CFGM, "arms": ["A2", "R2"], "run_id": "m6", "mode": "nc1_full", "k": "grid", "window": {"k_cycling": 3}}
    d = run.run(cfg, runs_dir=str(tmp_path))
    r = json.load(open(os.path.join(d, "nc1_full.json")))
    assert r["passed"] and set(r["per_k"]) == {"0", "2", "full"} and all(p["n_outer_rows"] > 0 for p in r["per_k"].values())
    assert set(r["scrambled_runs"]) == {"0", "2", "full"}
    # the k = 0 scramble touches labels the k_full scramble leaves alone
    from pinnkan import data as D, synth
    from pinnkan.specs import SPECS
    SPEC = SPECS["synthetic"]
    S = synth.make_synthetic("G0", n_cyc_cond=6, n_sto_cond=2, reps=1, seed=1)
    cell = next(c for c in S.cells if c.kind == "cycling")
    base = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    s0 = negcontrol.scramble_cells([cell], D.WindowRule.for_grid(SPEC, 0, base), SPEC)[0]
    sf = negcontrol.scramble_cells([cell], base, SPEC)[0]
    assert not np.array_equal(s0.ret[1:4], cell.ret[1:4]) and np.array_equal(sf.ret[1:4], cell.ret[1:4])


def test_M7_a9_latent_is_forced_to_the_prior_mean_at_k0(g0_cells=None):
    import torch
    from pinnkan import arms as A, data as D, synth
    from pinnkan.pinn import predict_data_only
    from pinnkan.specs import SPECS
    SPEC = SPECS["synthetic"]
    S = synth.make_synthetic("G0", n_cyc_cond=10, n_sto_cond=4, reps=2, seed=4)
    tr, te = synth.split_conditions(S.cells, 0.25, 4)
    base = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    arm = A.make_arm("A9", SPEC, A.default_hp("A9"), 0, {"rule": base, "steps_scale": 0.05, "backbone": "self_limiting"}).fit(tr)
    pw0 = [p.win for p in D.prepare_many([c for c in te if c.kind == "cycling"], D.WindowRule.for_grid(SPEC, 0, base))]
    seen = {}
    orig = torch.optim.Adam

    class Spy(orig):
        def __init__(self, params, *a, **k):
            params = list(params)
            seen["z"] = params[0]
            super().__init__(params, *a, **k)
    torch.optim.Adam = Spy
    try:
        out = predict_data_only(arm.model, SPEC, pw0)
    finally:
        torch.optim.Adam = orig
    zero = predict_data_only(arm.model, SPEC, pw0)
    assert all(np.array_equal(out[k], zero[k]) for k in out)
    # explicit: forecasts at k = 0 equal the network evaluated at z = 0
    from pinnkan.law import batch_forecast_query, retention_from_y
    bq = batch_forecast_query(SPEC, pw0)
    with torch.no_grad():
        F = arm.model.model.F(bq.obs_t, bq.s[bq.obs_cell], torch.zeros(bq.C, arm.model.model.zdim)[bq.obs_cell]) if hasattr(arm.model, "model") else arm.model.F(bq.obs_t, bq.s[bq.obs_cell], torch.zeros(bq.C, arm.model.zdim)[bq.obs_cell])
    ref = retention_from_y(SPEC, F.numpy())
    got = np.concatenate([out[w.cell_id] for w in pw0])
    assert np.allclose(got, ref, atol=1e-6)
