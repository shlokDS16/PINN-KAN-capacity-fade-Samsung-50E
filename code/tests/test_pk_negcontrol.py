"""pinnkan: negative control of runs/prereg/NEGCONTROL_RULING.md (D014): NC-1 label invariance (gate G), NC-2 permuted stress (interpretive), seed rule, no use of the
forecast-set extent.   .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_negcontrol.py -q"""
import json
import os
import re
import sys
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "tests"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest
import torch
from scipy import stats

torch.set_num_threads(1)

from pinnkan import arms, metrics, negcontrol, run, stats_step as st, synth, tuning
from pinnkan.data import Cell, WindowRule, prepare_many
from pinnkan.specs import SPECS

SPEC = SPECS["synthetic"]


@pytest.fixture(scope="module")
def g2():
    S = synth.make_synthetic("G2", n_cyc_cond=14, n_sto_cond=6, reps=2, seed=3)
    return synth.split_conditions(S.cells, 0.3, 3)


# ------------------------------------------------------------------------------------------------ seed rule
def test_mc_rng_follows_the_registered_rule():
    a = negcontrol.mc_rng("B|H1a|A9|BCa_mean_pp").random(4)
    b = np.random.default_rng(np.random.SeedSequence([20261105, zlib.crc32(b"B|H1a|A9|BCa_mean_pp")])).random(4)
    assert np.array_equal(a, b) and not np.array_equal(a, negcontrol.mc_rng("B|H1b|A5|BCa_mean_pp").random(4))
    assert negcontrol.MC_SEED_ROOT == 20261105 and run.DEFAULTS["mc_seed_root"] == 20261105


def test_bca_uses_the_labelled_stream_and_contrasts_record_the_labels(tmp_path):
    x = np.random.default_rng(0).normal(0.2, 1.0, 40)
    assert st.bca_mean_ci(x, B=2000, label="x") == st.bca_mean_ci(x, B=2000, label="x") and st.bca_mean_ci(x, B=2000, label="x") != st.bca_mean_ci(x, B=2000, label="y")
    from test_pk_emit_stats import make_fold, scores_for
    conds = [f"c{i:02d}" for i in range(20)]
    sc = scores_for(conds, {"A9": 0.3, "A10": 0.2, "A4": 0.1})
    c = st.build_contrasts("B", [make_fold(tmp_path, "f", sc, {a: 2.0 for a in sc})])
    assert c["mc_seed_root"] == 20261105 and "B|H1a|A9|BCa_mean_pp" in c["mc_labels"] and len(set(c["mc_labels"])) == len(c["mc_labels"])


def test_seed_root_is_in_seeds_json_and_the_config_hash(tmp_path):
    d = run.run({"run_id": "s", "dataset": "synthetic", "mode": "inner", "arms": ["R1"], "n_trials": 1, "inner_k": 2, "synthetic": {"n_cyc_cond": 8, "n_sto_cond": 4, "reps": 2, "seed": 2}},
                runs_dir=str(tmp_path))
    sj = json.load(open(os.path.join(d, "seeds.json")))
    assert sj["mc_seed_root"] == 20261105 and "crc32" in sj["mc_seed_rule"] and "permutation_test_rng_seed" not in sj
    from pinnkan import guard
    h1 = guard.canonical_config_hash({**run.DEFAULTS, "arms": ["R1"]})
    h2 = guard.canonical_config_hash({**run.DEFAULTS, "arms": ["R1"], "mc_seed_root": 1})
    assert h1 != h2                                                                          # the root is part of the config hash
    with pytest.raises(run.ConfigError):
        run.run({"run_id": "s2", "dataset": "synthetic", "mode": "inner", "arms": ["R1"], "mc_seed_root": 1}, runs_dir=str(tmp_path))
    assert not hasattr(metrics, "signflip_p_two_sided")


# ------------------------------------------------------------------------------------------------ NC-1
def test_scramble_leaves_window_and_training_alone_and_keeps_forecast_sets(g2):
    tr, te = g2
    rule = WindowRule.for_spec(SPEC)
    sc = negcontrol.scramble_cells(te, rule, SPEC)
    for c, n in zip(te, sc):
        w = rule.window_end(c)
        assert np.array_equal(c.ret[: w + 1], n.ret[: w + 1]) and not np.allclose(c.ret[w + 1:], n.ret[w + 1:]) and n.ret.min() >= 0 and n.ret.max() <= 1.1
        assert np.array_equal(c.t, n.t) and np.array_equal(c.efc, n.efc)
    sc2 = negcontrol.scramble_cells(te, rule, SPEC)
    assert all(np.array_equal(a.ret, b.ret) for a, b in zip(sc, sc2))                         # deterministic (registered stream)
    pa, pb = prepare_many(te, rule), prepare_many(sc, rule)
    assert all(np.array_equal(a.win.t_fc, b.win.t_fc) and np.array_equal(a.win.y_win, b.win.y_win) for a, b in zip(pa, pb))


def test_scramble_keeps_the_life_level_forecast_set():
    isu = SPECS["isu"]
    t = np.arange(0.0, 30.0)
    ret = 1.0 - 0.012 * t
    c = Cell("c1", "isu", "cycling", "1", np.array([1.0, 1.0, 50.0]), t, ret, t * 5.0, np.concatenate([[False], np.ones(29, bool)]))
    rule = WindowRule.for_spec(isu, W=4.0)
    for k in range(8):                                                                          # several garbage draws via different cell ids
        c2 = Cell(f"c{k}", "isu", "cycling", "1", c.raw, t, ret, c.efc, c.fc_ok)
        s = negcontrol.scramble_cells([c2], rule, isu)[0]
        a, b = prepare_many([c2], rule)[0], prepare_many([s], rule)[0]
        assert np.array_equal(a.win.t_fc, b.win.t_fc) and b.fc_true[-1] < 0.7 <= b.fc_true[:-1].min()


@pytest.mark.parametrize("aid", ["R1", "R2", "A2", "A9", "A10", "A11", "A12", "A1"])
def test_clean_arms_pass_nc1_bit_identically(aid, g2):
    tr, te = g2
    rule = WindowRule.for_spec(SPEC)
    ctx = {"rule": rule, "backbone": "self_limiting", "steps_scale": 0.04, "a10_starts": 2}
    arm = arms.make_arm(aid, SPEC, arms.default_hp(aid), 0, ctx).fit(tr)
    r = negcontrol.check_invariance(arm.predict, te, rule, SPEC)
    assert r["passed"] and r["max_abs_diff"] == 0.0 and r["n_rows"] > 0 and r["forecast_sets_equal"]


def test_a_deliberate_leak_is_caught(g2):
    """leak B of the ruling: the predictor's window is one check-up longer than the forecast set assumes, so it sees a post-window label"""
    tr, te = g2
    rule = WindowRule.for_spec(SPEC)
    leaky = WindowRule(k_cycling=rule.k_cycling + 1, k_storage=rule.k_storage + 1, min_window_points=rule.min_window_points, min_fc_points=1)
    arm = arms.make_arm("R2", SPEC, {}, 0, {"rule": rule, "backbone": "self_limiting"}).fit(tr)
    ok = negcontrol.check_invariance(arm.predict, te, rule, SPEC)
    bad = negcontrol.check_invariance(arm.predict, te, rule, SPEC, predict_rule=leaky)
    assert ok["passed"] and not bad["passed"] and bad["max_abs_diff"] > 1e-3 and bad["forecast_sets_equal"]
    arm2 = arms.make_arm("A2", SPEC, arms.default_hp("A2"), 0, {"rule": rule, "backbone": "self_limiting", "steps_scale": 0.04}).fit(tr)
    assert not negcontrol.check_invariance(arm2.predict, te, rule, SPEC, predict_rule=leaky)["passed"]


CFG = {"dataset": "synthetic", "mode": "confirmatory", "n_trials": 1, "inner_k": 2, "steps_scale": 0.03, "seeds": [0, 1], "backbone": "self_limiting", "arms": ["A2", "A9", "R1", "R2"],
       "synthetic": {"kind": "G2", "n_cyc_cond": 14, "n_sto_cond": 6, "reps": 2, "seed": 7}}


def test_every_confirmatory_run_writes_invariance_json_and_trips_gate_g_on_failure(tmp_path, monkeypatch):
    d = run.run({**CFG, "run_id": "ok"}, runs_dir=str(tmp_path))
    inv = json.load(open(os.path.join(d, "invariance.json")))
    assert inv["passed"] and inv["max_abs_diff"] == 0.0 and inv["tolerance"] == 0.0 and set(inv["per_arm_seed"]) == {f"{a}|{s}" for a in CFG["arms"] for s in (0, 1)}
    monkeypatch.setattr(negcontrol, "check_invariance", lambda *a, **k: dict(passed=False, max_abs_diff=0.3, n_rows=10, forecast_sets_equal=True))
    with pytest.raises(negcontrol.InvarianceError):
        run.run({**CFG, "run_id": "tripped"}, runs_dir=str(tmp_path))
    assert os.path.exists(tmp_path / "tripped" / "GATE_G_TRIPPED") and json.load(open(tmp_path / "tripped" / "invariance.json"))["passed"] is False


def test_nc1_full_pipeline_on_synthetic(tmp_path):
    d = run.run({**CFG, "run_id": "nc1", "mode": "nc1_full", "arms": ["A2", "A9", "R2"]}, runs_dir=str(tmp_path))
    res = json.load(open(os.path.join(d, "nc1_full.json")))
    assert res["passed"] and res["max_abs_diff_outer"] == 0.0 and res["max_abs_diff_inner_oof"] == 0.0 and all(res["identical_records"].values()) and res["n_outer_rows"] > 0
    a = json.load(open(tmp_path / "nc1_clean" / "metrics.json"))["outer_test"]["A2"]["primary_pp"]
    b = json.load(open(tmp_path / "nc1_scrambled" / "metrics.json"))["outer_test"]["A2"]["primary_pp"]
    assert a != b                                                                               # the scrambled labels really changed the scores while predictions stayed bit-identical
    with pytest.raises(run.ConfigError):
        run.run({"run_id": "x", "dataset": "isu", "mode": "nc1_full"}, runs_dir=str(tmp_path))


# ------------------------------------------------------------------------------------------------ NC-2
def _pair(tmp_path, name, real, perm, test="B"):
    out = []
    for tag, sc, cfg in (("real", real, {"dataset": "synthetic", "test": "B"}), ("perm", perm, {"dataset": "synthetic", "test": test, "permute_stress": True})):
        d = tmp_path / f"{name}_{tag}"
        os.makedirs(d)
        json.dump(sc, open(d / "condition_scores.json", "w"))
        json.dump(cfg, open(d / "config.json", "w"))
        out.append(str(d))
    return out


def test_nc2_exact_one_sided_sign_test_paired_by_condition(tmp_path):
    conds = [f"c{i:02d}" for i in range(40)]
    real = {"A1": {c: 2.0 for c in conds}, "A9": {c: 2.4 for c in conds}}
    perm = {"A1": {c: 2.0 * (1.5 if i < 27 else 0.8) for i, c in enumerate(conds)}, "A9": {c: 2.5 for c in conds}, "R1": {c: 9.0 for c in conds}}
    r, p = _pair(tmp_path, "t", real, perm)
    n = st.nc2([r], [p])
    assert n["n"] == 40 and n["k_positive"] == 27 and n["passed"] and n["gating"] is False                  # 27 of 40 is the threshold of the ruling
    assert np.isclose(n["p_one_sided_exact"], stats.binom.sf(26, 40, 0.5)) and n["p_one_sided_exact"] <= 0.025
    assert np.isclose(n["median_L"], np.log(1.5)) and np.isclose(n["rel_increase_median"], 0.5)
    assert n["descriptive"]["mean_L_A9_over_A1_real"] > 0 and "R1" in n["descriptive"]["scores_under_permutation_mean_pp"]
    perm26 = {"A1": {c: 2.0 * (1.5 if i < 26 else 0.8) for i, c in enumerate(conds)}}
    r2, p2 = _pair(tmp_path, "u", real, perm26)
    assert not st.nc2([r2], [p2])["passed"]
    assert np.isclose(st.exact_two_sided_p(27, 40), min(1.0, 2 * stats.binom.sf(26, 40, 0.5))) and st.exact_two_sided_p(20, 40) == 1.0


def test_nc2_is_test_b_only_and_pairs_identical_condition_sets(tmp_path):
    conds = [f"c{i}" for i in range(10)]
    sc = {"A1": {c: 2.0 for c in conds}}
    r, p = _pair(tmp_path, "c", sc, sc, test="C")
    with pytest.raises(ValueError, match="Test B"):
        st.nc2([r], [p])
    r, p = _pair(tmp_path, "d", sc, {"A1": {c: 2.0 for c in conds[:9]}})
    with pytest.raises(ValueError, match="same held-out conditions"):
        st.nc2([r], [p])
    with pytest.raises(run.ConfigError, match="Test B only"):
        run.run({"run_id": "pc", "dataset": "isu", "test": "C", "permute_stress": True, "mode": "inner", "arms": ["R1"]}, runs_dir=str(tmp_path))


# ------------------------------------------------------------------------------------------------ no arm uses the extent of its forecast set
ALL_ARMS = ["R1", "R2", "A1", "A2", "A3", "A4", "A5", "A7", "A8", "A9", "A10", "A11", "A12", "A13", "A14"]


@pytest.mark.parametrize("aid", ALL_ARMS)
def test_no_arm_depends_on_the_extent_of_its_forecast_set(aid, g2):
    """ISU/SNL forecast sets stop at the 70 % crossing, so len(t_fc) and t_fc[-1] encode when a cell dies. Predictions at a check-up must be the same (to float32 rounding) whether later
    times are queried or not, for every arm. (NC-1 itself compares IDENTICAL query lists and is bit-exact.)"""
    tr, te = g2
    base = WindowRule(k_cycling=4, k_storage=2, life_level=None)
    cut = WindowRule(k_cycling=4, k_storage=2, life_level=0.88)
    pc, pf = prepare_many(te, cut), prepare_many(te, base)
    assert any(len(a.win.t_fc) < len(b.win.t_fc) for a, b in zip(pc, pf))
    ctx = {"rule": base, "backbone": "self_limiting", "steps_scale": 0.03, "a10_starts": 2}
    arm = arms.make_arm(aid, SPEC, arms.default_hp(aid), 0, ctx).fit(tr)
    a, b = arm.predict([p.win for p in pc]), arm.predict([p.win for p in pf])
    w0 = pf[0].win.__class__(**{**pf[0].win.__dict__, "t_fc": pf[0].win.t_fc[:1]})                      # the first cell queried at ONE time, the others as before
    one = arm.predict([w0] + [p.win for p in pf[1:]])
    for p in pc:
        n = len(p.win.t_fc)
        # equal up to float32 rounding of a differently sized matmul (a batch of other row counts sums in another order): 1e-6 in retention, i.e. 1e-4 pp
        assert np.allclose(a[p.cell.cell_id], b[p.cell.cell_id][:n], rtol=0, atol=1e-6), aid
    assert np.allclose(one[pf[0].cell.cell_id], b[pf[0].cell.cell_id][:1], rtol=0, atol=1e-6), aid


def test_model_modules_do_not_read_the_extent_of_t_fc():
    forbidden = re.compile(r"t_fc\[-1\]|t_fc\.max|t_fc\.min|t_fc\.shape|t_fc\.size|np\.(?:max|min)\(\s*\w+\.t_fc|max\(\s*\w+\.t_fc")
    allowed_len = re.compile(r"np\.(?:full|zeros)\(len\(w\.t_fc\)")                                      # R1 output and the unused label placeholder are shaped like the query
    for f in ("arms.py", "hard.py", "pinn.py", "free.py", "baselines.py", "semi.py", "law.py"):
        src = open(os.path.join(ROOT, "code", "pinnkan", f), encoding="utf8").read()
        assert not forbidden.search(src), f
        for m in re.finditer(r"len\([^)]*t_fc[^)]*\)", src):
            assert allowed_len.search(src[max(0, m.start() - 20): m.end() + 20]), (f, m.group(0))
    # the one artefact that reads t_fc[-1] (emit.superposition) runs after scoring and is an output, not an input of any fit or predict step
    assert "t_fc[-1]" in open(os.path.join(ROOT, "code", "pinnkan", "emit.py"), encoding="utf8").read()
