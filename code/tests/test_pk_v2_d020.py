"""build_v2, D020 coder rows: five-seed ensemble endpoint (K1 / K2 per-seed), inner folds at m in {8, 16} as a config value (default 2; 4 only on an adopt decision), tournament per (fold, m).
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_v2_d020.py -q"""
import hashlib
import json
import os
import sys
from types import SimpleNamespace

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest
import torch

torch.set_num_threads(1)

from pinnkan import arms as A
from pinnkan import data as D
from pinnkan import metrics, negcontrol, run, semi, stats_rows as R, stats_v4 as v4, synth, tuning
from pinnkan.specs import SPECS
from test_pk_v2_stats import CONDS, FOLD, LABS, make_store

SPEC = SPECS["synthetic"]


def _prep(n_cells=6, n_fc=5, seed=0):
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n_cells):
        win = SimpleNamespace(y_last=0.95, t_fc=np.arange(1, n_fc + 1) * 30.0)
        cell = SimpleNamespace(cell_id=f"c{i}", cond=f"k{i % 3}")
        out.append(SimpleNamespace(cell=cell, win=win, fc_true=0.95 - 0.01 * np.arange(1, n_fc + 1) + 0.002 * rng.standard_normal(n_fc)))
    return out


# ------------------------------------------------------------------------------------------------ ensemble scoring
def test_ensemble_rmse_is_at_most_the_mean_per_seed_rmse_cell_by_cell():
    prep = _prep()
    rng = np.random.default_rng(1)
    seeds = [{p.cell.cell_id: p.fc_true + 0.01 * rng.standard_normal(len(p.fc_true)) for p in prep} for _ in range(5)]
    ens = metrics.ensemble_rows(seeds, prep)
    per = [metrics.score_prepared(s, prep) for s in seeds]
    for i, r in enumerate(ens):
        assert r["rmse_pp"] <= np.mean([rows[i]["rmse_pp"] for rows in per]) + 1e-12
    cs_e, _ = metrics.ensemble_condition_scores(seeds, prep)
    cs_s, _ = metrics.seed_condition_scores(per)
    assert all(cs_e[c] <= cs_s[c] + 1e-12 for c in cs_e) and any(cs_e[c] < cs_s[c] - 1e-9 for c in cs_e)


def test_ensemble_equals_the_per_seed_score_for_one_seed_or_agreeing_seeds():
    prep = _prep()
    pred = {p.cell.cell_id: p.fc_true + 0.004 for p in prep}
    e1 = metrics.ensemble_rows([pred], prep)
    e5 = metrics.ensemble_rows([pred] * 5, prep)
    s1 = metrics.score_prepared(pred, prep)
    for a, b, c in zip(e1, e5, s1):
        assert a["rmse_pp"] == b["rmse_pp"] == c["rmse_pp"]
    cs_e, _ = metrics.ensemble_condition_scores([pred] * 5, prep)
    cs_s, _ = metrics.seed_condition_scores([s1] * 5)
    assert cs_e == pytest.approx(cs_s)


def test_non_finite_forecasts_are_replaced_seed_wise_before_averaging_and_counted_per_seed():
    prep = _prep(n_cells=2, n_fc=4)
    good = {p.cell.cell_id: p.fc_true.copy() for p in prep}
    bad = {k: v.copy() for k, v in good.items()}
    bad["c0"][1] = np.nan
    bad["c0"][3] = np.inf
    ens = metrics.ensemble_rows([good, good, bad], prep)
    r0 = next(r for r in ens if r["cell"] == "c0")
    expect = np.stack([good["c0"], good["c0"], np.where(np.isfinite(bad["c0"]), bad["c0"], 0.95)]).mean(0)       # persistence = last window retention 0.95
    assert np.allclose(r0["_pred"], expect) and np.isfinite(r0["_pred"]).all()
    assert r0["n_nonfinite_by_seed"] == [0, 0, 2] and r0["n_nonfinite"] == 2
    assert next(r for r in ens if r["cell"] == "c1")["n_nonfinite_by_seed"] == [0, 0, 0]
    per = [metrics.score_prepared(s, prep) for s in (good, good, bad)]
    assert [next(r for r in rows if r["cell"] == "c0")["n_nonfinite"] for rows in per] == [0, 0, 2]          # the per-seed rule is itself seed-wise (already so before D020)


# ------------------------------------------------------------------------------------------------ which arms are seed-dependent
@pytest.fixture(scope="module")
def g0():
    S = synth.make_synthetic("G0", n_cyc_cond=14, n_sto_cond=6, reps=2, seed=4)
    return synth.split_conditions(S.cells, 0.25, 4)


def test_a11_is_deterministic_and_a10_and_a12_are_seed_dependent(g0):
    tr, te = g0
    base = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    pw = [p.win for p in D.prepare_many([c for c in te if c.kind == "cycling"], base)]
    hp11 = {"nu": 2.5, "noise_lo": 1e-4, "fs": "full"}
    o = [A.make_arm("A11", SPEC, hp11, s, {"rule": base}).fit(tr).predict(pw) for s in (0, 1, 2)]
    assert all(np.array_equal(o[0][k], o[i][k]) for i in (1, 2) for k in o[0])                         # A11: no seed-dependent step (GP, no restarts, deterministic subsampling)
    hp12 = {"n_est": 60, "lr": 0.1, "leaves": 6, "mcs": 8, "l2": 1.0}
    o12 = [A.make_arm("A12", SPEC, hp12, s, {"rule": base}).fit(tr).predict(pw) for s in (0, 1)]
    assert any(not np.array_equal(o12[0][k], o12[1][k]) for k in o12[0])                              # LightGBM row / column subsampling
    form = semi.SemiForm(SPEC)
    s0, s1 = form.starts(8, 0), form.starts(8, 1)
    assert any(not np.array_equal(a, b) for a, b in zip(s0, s1))                                       # A10: the multi-start points depend on the seed -> ensembled like every seeded arm
    r2 = [A.make_arm("R2", SPEC, {}, s, {"rule": base}).fit(tr).predict(pw) for s in (0, 1)]
    assert all(np.array_equal(r2[0][k], r2[1][k]) for k in r2[0])


# ------------------------------------------------------------------------------------------------ run writer
CFG = {"dataset": "synthetic", "arms": ["A2", "A9", "R2"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.05, "seeds": [0, 1, 2], "mode": "confirmatory", "diagnostics": False,
       "synthetic": {"kind": "G0", "n_cyc_cond": 16, "n_sto_cond": 6, "reps": 2, "seed": 3}}


def test_run_writes_ensemble_and_per_seed_scores_and_predictions(tmp_path):
    d = run.run({**CFG, "run_id": "e"}, runs_dir=str(tmp_path))
    ens = json.load(open(os.path.join(d, "condition_scores.json")))
    sd = json.load(open(os.path.join(d, "condition_scores_seed.json")))
    assert set(ens) == set(sd) == set(CFG["arms"])
    for a in ens:
        assert all(ens[a][c] <= sd[a][c] + 1e-9 for c in ens[a])                         # RMSE of the mean forecast <= mean of the per-seed RMSEs, condition-wise
    assert ens["R2"] == sd["R2"] and any(ens["A9"][c] < sd["A9"][c] - 1e-12 for c in ens["A9"])      # deterministic arm: equal; seeded arm: lower
    preds = open(os.path.join(d, "predictions.csv")).read().splitlines()
    assert any(",A9,ens," in l for l in preds) and any(",A9,0," in l for l in preds)
    m = json.load(open(os.path.join(d, "metrics.json")))["outer_test"]["A9"]
    assert m["primary_pp"] == pytest.approx(m["primary_pp_ensemble"]) and m["primary_pp_ensemble"] <= m["primary_pp_per_seed"] + 1e-12
    assert len(m["n_nonfinite_by_seed"]) == 3 and m["fit_seconds_ensemble"] >= m["fit_seconds_one_fit"] > 0
    assert json.load(open(os.path.join(d, "config.json")))["endpoint"] == "ensemble"


def test_endpoint_per_seed_reproduces_the_v3_rule_and_bad_values_raise(tmp_path):
    d = run.run({**CFG, "run_id": "ps", "endpoint": "per_seed"}, runs_dir=str(tmp_path))
    assert json.load(open(os.path.join(d, "condition_scores.json"))) == json.load(open(os.path.join(d, "condition_scores_seed.json")))
    with pytest.raises(run.ConfigError):
        run.run({**CFG, "run_id": "bad", "endpoint": "mean"}, runs_dir=str(tmp_path))


def test_nc1_invariance_holds_for_the_ensemble(g0):
    tr, te = g0
    base = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    cyc = [c for c in te if c.kind == "cycling"]
    arms = [A.make_arm("A9", SPEC, A.default_hp("A9"), s, {"rule": base, "backbone": "self_limiting", "steps_scale": 0.05}).fit(tr) for s in (0, 1)]
    p0 = D.prepare_many(cyc, base)
    p1 = D.prepare_many(negcontrol.scramble_cells(cyc, base, SPEC), base)
    e0 = metrics.ensemble_rows([a.predict([p.win for p in p0]) for a in arms], p0)
    e1 = metrics.ensemble_rows([a.predict([p.win for p in p1]) for a in arms], p1)
    assert all(np.array_equal(a["_pred"], b["_pred"]) for a, b in zip(e0, e1))               # the ensemble forecast does not move when post-window labels are scrambled
    for a in arms:
        assert negcontrol.check_invariance(a.predict, cyc, base, SPEC)["passed"]


# ------------------------------------------------------------------------------------------------ statistics: K chain per-seed
def test_k1_k2_read_per_seed_scores_and_the_p_chain_reads_the_ensemble():
    store = make_store()
    ens = {k: {a: dict(v) for a, v in t.items()} for k, t in store.tables.items()}
    seed = {k: {a: dict(v) for a, v in t.items()} for k, t in store.tables.items()}
    for c in CONDS:                                        # per-seed: A15 clearly worse than A1 at g4 (K1 fails there); in the ensemble tables nothing changes
        seed[(32, "full")]["A15"][c] = 2.0 * np.exp(0.5)
        seed[(32, "full")]["G15"][c] = seed[(32, "full")]["A15"][c] * np.exp(0.25)
        seed[(8, "2")]["D*"][c] = 2.0                       # per-seed P1 would be nothing (descriptive only)
    s = v4.Store(ens, LABS, FOLD, 4, seed_tables=seed)
    out = v4.run_v4(s)
    assert out["primary"]["tiers"]["P1"] == "S" and out["primary"]["tiers"]["K1"] is False        # P1 from the ensemble tables, K1 from the per-seed tables
    d = out["per_seed_descriptive"]
    assert d["available"] and d["P1"]["positives"]["S"] == 0 and d["A1_scores_both_chains"]["g4"]["ensemble_mean_pp"] == pytest.approx(2.0)
    assert "ensemble" in out["endpoint_note"] and "per-seed" in out["endpoint_note"]
    t = R.row_tiers(out, s, v4.resolve_config()[0])
    assert t["K1"] is False and t["P1"] == "S"
    plain = v4.run_v4(v4.Store(ens, LABS, FOLD, 4))                                                 # no seed tables: the single set is used for both chains
    assert plain["primary"]["tiers"]["K1"] is True and plain["per_seed_descriptive"]["available"] is False


def test_store_from_runs_reads_the_seed_files(tmp_path):
    from test_pk_v2_stats import _fake_run
    tmp = str(tmp_path)
    cs = {"A1": {c: 2.0 for c in CONDS[:8]}, "A9": {c: 2.5 for c in CONDS[:8]}}
    sc = {"A1": {c: 2.1 for c in CONDS[:8]}, "A9": {c: 2.6 for c in CONDS[:8]}}
    d = _fake_run(tmp, "r", 8, 0, ["full"], {"full": cs}, {"D*": {"arm": "A9"}})
    json.dump(sc, open(os.path.join(d, "condition_scores_seed.json"), "w"))
    st = v4.Store.from_runs([d])
    assert st.scores("A1", 8, "full")[CONDS[0]] == 2.0 and st.seed_view().scores("A1", 8, "full")[CONDS[0]] == 2.1 and st.seed_view().scores("D*", 8, "full")[CONDS[0]] == 2.6


# ------------------------------------------------------------------------------------------------ C2: inner folds as a config value
def test_inner_k_for_m_branches():
    assert [tuning.inner_k_for_m(m) for m in (8, 16, 32)] == [2, 2, 3]
    assert [tuning.inner_k_for_m(m, thin_folds=4) for m in (8, 16, 32)] == [4, 4, 3]
    assert [tuning.inner_k_for_m(m, partial=True, thin_folds=4) for m in (8, 16, 32)] == [2, 2, 2]          # the Partial plan overrides
    assert tuning.inner_k_for_m(None) == 3 and tuning.inner_k_for_m(None, partial=True) == 2


CFGI = {"dataset": "synthetic", "arms": ["R2"], "n_trials": 1, "steps_scale": 0.05, "seeds": [0], "mode": "inner", "diagnostics": False,
        "synthetic": {"kind": "G0", "n_cyc_cond": 20, "n_sto_cond": 6, "reps": 2, "seed": 3}}


def test_four_inner_folds_need_an_adopt_decision(tmp_path):
    for bad in ({"inner_k_thin": 3}, {"inner_k_thin": 4}, {"inner_k_thin": 4, "p6b_decision": str(tmp_path / "nope.json")}):
        with pytest.raises(run.ConfigError):
            run.run({**CFGI, "run_id": "x", "m": 8, **bad}, runs_dir=str(tmp_path))
    no = tmp_path / "no.json"
    no.write_text(json.dumps({"adopt": False}))
    with pytest.raises(run.ConfigError):
        run.run({**CFGI, "run_id": "x", "m": 8, "inner_k_thin": 4, "p6b_decision": str(no)}, runs_dir=str(tmp_path))
    yes = tmp_path / "yes.json"
    yes.write_text(json.dumps({"adopt": True}))
    d = run.run({**CFGI, "run_id": "four", "m": 8, "inner_k_thin": 4, "p6b_decision": str(yes)}, runs_dir=str(tmp_path))
    c = json.load(open(os.path.join(d, "config.json")))
    assert c["inner_k"] == 4 and c["p6b_decision_sha256"] == hashlib.sha256(yes.read_bytes()).hexdigest()
    assert json.load(open(os.path.join(d, "tuning_R2.json")))["inner_k"] == 4
    d32 = run.run({**CFGI, "run_id": "m32", "m": 32, "inner_k_thin": 4, "p6b_decision": str(yes)}, runs_dir=str(tmp_path))
    assert json.load(open(os.path.join(d32, "config.json")))["inner_k"] == 3                     # m = 32 keeps 3
    d2 = run.run({**CFGI, "run_id": "default", "m": 8}, runs_dir=str(tmp_path))
    assert json.load(open(os.path.join(d2, "config.json")))["inner_k"] == 2


def test_partial_plan_returns_the_thin_cells_to_two_folds(tmp_path, monkeypatch):
    yes = tmp_path / "yes.json"
    yes.write_text(json.dumps({"adopt": True}))
    monkeypatch.setattr(tuning, "choose_budget", lambda med: {"n_trials": 1, "inner_k": 2, "rule": "Partial plan (test)"})
    d = run.run({**CFGI, "run_id": "partial", "arms": ["A2", "R2"], "m": 8, "inner_k_thin": 4, "p6b_decision": str(yes), "auto_budget": True}, runs_dir=str(tmp_path))
    assert json.load(open(os.path.join(d, "tuning_A2.json")))["inner_k"] == 2 and json.load(open(os.path.join(d, "budget_rule.json")))["inner_k"] == 2          # the tuned folds, not the requested config


def test_tournament_runs_per_fold_and_m_on_the_thinned_side_with_the_cells_inner_folds(tmp_path, monkeypatch):
    seen = []
    orig = tuning.backbone_tournament

    def spy(cells, spec, rule, inner_k, outer_fold, ctx, target_kind="cycling"):
        seen.append((len({c.cond for c in cells if c.kind == "cycling"}), inner_k))
        return orig(cells, spec, rule, inner_k, outer_fold, ctx, target_kind)
    monkeypatch.setattr(tuning, "backbone_tournament", spy)
    yes = tmp_path / "yes.json"
    yes.write_text(json.dumps({"adopt": True}))
    cfg = {**CFGI, "arms": ["A2"], "backbone": "tournament", "synthetic": {"kind": "G0", "n_cyc_cond": 28, "n_sto_cond": 6, "reps": 2, "seed": 3}}
    run.run({**cfg, "run_id": "t8", "m": 8, "inner_k_thin": 4, "p6b_decision": str(yes)}, runs_dir=str(tmp_path))
    run.run({**cfg, "run_id": "t16", "m": 16}, runs_dir=str(tmp_path))
    run.run({**cfg, "run_id": "t32", "m": 32}, runs_dir=str(tmp_path))
    assert seen == [(8, 4), (16, 2), (21, 3)]                                    # synthetic training side has 21 cycling conditions: m = 32 is the unthinned side
