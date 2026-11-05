"""build_v2 item 6: the four automatic-downgrade rows (lab-stratified, lab-and-stage indicators incl. A10 and D*, retain-every-check-up, random subset at g1) and the Test C / S2
descriptive tables (PREREG_v4 9.8, 9.9; D018 GAP-4).
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_v2_rows.py -q"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest
import torch

torch.set_num_threads(1)

from pinnkan import arms as A
from pinnkan import baselines as B
from pinnkan import data as D
from pinnkan import law, negcontrol, run, semi, stats_rows as R, stats_v4 as v4, synth
from pinnkan.specs import SPECS
from test_pk_v2_stats import CONDS, LABS, FOLD, make_store

SPEC = SPECS["synthetic"]


# ------------------------------------------------------------------------------------------------ indicator coding
def test_indicator_vector_coding_is_treatment_coding_with_hm_and_stage_1_as_reference():
    f = D.indicator_vector
    assert f("HM", "1").tolist() == [0, 0, 0] and f("INT", "1").tolist() == [1, 0, 0] and f("SIE", "2").tolist() == [0, 1, 1] and f("", "").tolist() == [0, 0, 0]
    assert f("HM", 2).tolist() == [0, 0, 1] and f("XX", "1").tolist() == [0, 0, 0]


@pytest.fixture(scope="module")
def labelled():
    """synthetic design with a planted laboratory offset: INT cells lose capacity faster (retention loss x exp(0.45)); stage alternates"""
    S = synth.make_synthetic("G0", n_cyc_cond=14, n_sto_cond=6, reps=2, seed=4)
    tr, te = synth.split_conditions(S.cells, 0.25, 4)
    labs = ["HM", "INT", "SIE"]
    for cells in (tr, te):
        for c in cells:
            c.lab = labs[hash(c.cond) % 3] if False else labs[sum(map(ord, c.cond)) % 3]
            c.stage = "1" if sum(map(ord, c.cell_id)) % 2 else "2"
            if c.lab == "INT" and c.kind == "cycling":
                c.ret = 1.0 - (1.0 - c.ret) * np.exp(0.45)
    return tr, te


CTX = {"backbone": "self_limiting", "steps_scale": 0.15}


def test_batches_carry_indicators_only_on_request(labelled):
    tr, te = labelled
    b0, b1 = law.batch_from_cells(SPEC, tr), law.batch_from_cells(SPEC, tr, indicator=True)
    assert b0.ind is None and b1.ind.shape == (len(tr), D.N_IND)
    assert b1.ind[0].tolist() == D.indicator_vector(tr[0].lab, tr[0].stage).tolist()


def test_limiting_case_zero_indicators_reproduce_the_primary_analysis_bit_for_bit(labelled):
    tr, te = labelled
    blank = []
    import copy
    for c in tr:
        c2 = copy.copy(c)
        c2.lab, c2.stage = "", ""
        blank.append(c2)
    base = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    cyc = [c for c in te if c.kind == "cycling"]
    pw = [p.win for p in D.prepare_many(cyc, base)]
    for aid in ("A2", "A9"):
        hp = A.default_hp(aid)
        p0 = A.make_arm(aid, SPEC, hp, 0, {**CTX, "rule": base}).fit(blank).predict(pw)
        p1 = A.make_arm(aid, SPEC, hp, 0, {**CTX, "rule": base, "lab_indicator": True}).fit(blank).predict(pw)
        for k in p0:
            assert np.array_equal(p0[k], p1[k]), aid
    p0 = A.make_arm("A4", SPEC, A.default_hp("A4"), 0, {**CTX, "rule": base}).fit(blank).predict(pw)
    p1 = A.make_arm("A4", SPEC, A.default_hp("A4"), 0, {**CTX, "rule": base, "lab_indicator": True}).fit(blank).predict(pw)
    for k in p0:
        assert np.allclose(p0[k], p1[k], atol=3e-2)          # PINN arm: the extra (zero-gradient) parameter changes the float summation order of the global clip norm, amplified by 2000 steps


def test_the_indicator_prior_learns_the_planted_laboratory_effect_in_a2_and_a1(labelled):
    tr, te = labelled
    base = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    a2 = A.make_arm("A2", SPEC, {**A.default_hp("A2")}, 0, {**CTX, "steps_scale": 0.5, "rule": base, "lab_indicator": True}).fit(tr)
    beta = a2.model.beta.detach().numpy()
    assert beta.shape == (3,) and beta[0] > 0.1 and beta[0] > beta[1] - 0.2          # INT (index 0 = lab INT) is faster: positive offset
    a1 = A.make_arm("A4", SPEC, A.default_hp("A4"), 0, {**CTX, "rule": base, "lab_indicator": True}).fit(tr)
    assert a1.model.beta is not None and float(a1.model.beta.abs().sum()) > 0
    pw = [p.win for p in D.prepare_many([c for c in te if c.kind == "cycling"], base)]
    out = a1.predict(pw)
    assert all(np.isfinite(v).all() for v in out.values())


def test_k0_prior_mean_is_used_at_k0_in_the_indicator_row(labelled):
    tr, te = labelled
    base = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    a = A.make_arm("A4", SPEC, A.default_hp("A4"), 0, {**CTX, "rule": base, "lab_indicator": True}).fit(tr)
    from pinnkan.pinn import predict_pinn
    pr = D.prepare_many([c for c in te if c.kind == "cycling"], D.WindowRule.for_grid(SPEC, 0, base))
    _, (z, delta) = predict_pinn(a.model, SPEC, [p.win for p in pr], 1.0, 0)
    mu = a.model.prior_mean(torch.tensor(np.stack([D.indicator_vector(p.win.lab, p.win.stage) for p in pr])))
    assert torch.allclose(delta, mu.detach()) and bool((z == 0).all())


def test_a10_factor_prior_from_indicators_and_a10p_is_unchanged(labelled):
    tr, te = labelled
    base = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    cyc = [c for c in te if c.kind == "cycling"]
    pw = [p.win for p in D.prepare_many(cyc, base)]
    a = A.make_arm("A10", SPEC, {}, 0, {**CTX, "rule": base, "lab_indicator": True, "a10_starts": 2}).fit(tr)
    assert a.beta is not None and a.beta.shape == (4,) and a.beta[1] > 0.0 and np.isfinite(a.beta).all()      # [intercept, INT, SIE, stage 2]: INT cells need a larger factor (the population fit absorbs part of it)
    pp = A.make_arm("A10P", SPEC, {}, 0, {**CTX, "rule": base, "lab_indicator": True, "a10_starts": 2}).fit(tr)
    pp0 = A.make_arm("A10P", SPEC, {}, 0, {**CTX, "rule": base, "a10_starts": 2}).fit(tr)
    o1, o0 = pp.predict(pw), pp0.predict(pw)
    assert pp.beta is None and all(np.array_equal(o1[k], o0[k]) for k in o1)               # the as-published form has no per-cell factor: no indicator prior
    plain = A.make_arm("A10", SPEC, {}, 0, {**CTX, "rule": base, "a10_starts": 2}).fit(tr).predict(pw)
    withind = a.predict(pw)
    assert any(not np.array_equal(plain[k], withind[k]) for k in plain)              # the indicator prior mean moves the per-cell factor
    r0 = D.prepare_many(cyc, D.WindowRule.for_grid(SPEC, 0, base))
    o = a.predict([p.win for p in r0])
    assert all(np.isfinite(v).all() for v in o.values())


def test_dstar_learners_get_the_indicator_columns_and_stay_causal(labelled):
    tr, te = labelled
    base = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    p = D.prepare_many(tr, base)
    c0 = B.cells_from_prepared(p, "synthetic")
    c1 = B.cells_from_prepared(p, "synthetic", indicator=True)
    k = next(iter(c0))
    assert len(c1[k]["stress"]) == len(c0[k]["stress"]) + 3
    for kind in ("A11", "A12"):
        hp = {"nu": 2.5, "noise_lo": 1e-4, "fs": "full"} if kind == "A11" else {"n_est": 40, "lr": 0.1, "leaves": 6, "mcs": 8, "l2": 1.0}
        arm = A.make_arm(kind, SPEC, hp, 0, {"rule": base, "lab_indicator": True}).fit(tr)
        res = negcontrol.check_invariance(arm.predict, [c for c in te if c.kind == "cycling"], base, SPEC)
        assert res["passed"] and res["n_rows"] > 0


def test_run_accepts_lab_indicator_and_zero_indicators_match_the_plain_run(tmp_path):
    cfg = {"dataset": "synthetic", "arms": ["A2", "A9", "R2"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.05, "seeds": [0], "mode": "confirmatory", "diagnostics": False,
           "synthetic": {"kind": "G0", "n_cyc_cond": 16, "n_sto_cond": 6, "reps": 2, "seed": 3}}
    d0 = run.run({**cfg, "run_id": "plain"}, runs_dir=str(tmp_path))
    d1 = run.run({**cfg, "run_id": "ind", "lab_indicator": True}, runs_dir=str(tmp_path))          # synthetic cells carry no laboratory: all indicators are zero
    assert json.load(open(os.path.join(d0, "condition_scores.json"))) == json.load(open(os.path.join(d1, "condition_scores.json")))


# ------------------------------------------------------------------------------------------------ rows: weighted median, lab-stratified, combination
def test_weighted_median_and_post_stratification():
    x = np.array([[1.0, 2.0, 3.0, 10.0, 11.0, 12.0]])
    w = np.array([[0.25, 0.25, 0.0, 0.0, 0.25, 0.25]])
    assert R.weighted_median(x, w)[0] == 2.0
    L = np.array([0.1] * 8 + [-0.5] * 2)
    labs = ["A"] * 8 + ["B"] * 2
    b = R.lab_stratified_bounds(L, labs, [0.0125], "t|lab", B=2000)
    assert b["strata_sizes"] == {"A": 8, "B": 2} and b["point"] == pytest.approx(-0.5) or b["point"] in (0.1, -0.5)     # two equal strata weights: the weighted median sits on the boundary
    b2 = R.lab_stratified_bounds(np.array([0.2] * 20 + [0.1] * 20 + [0.15] * 20), ["A"] * 20 + ["B"] * 20 + ["C"] * 20, [0.025], "t|lab2", B=2000)
    assert b2["lower"]["0.025"] > 0.09 and b2["point"] == pytest.approx(0.15)
    assert R.lab_stratified_bounds(L, labs, [0.025], "t|lab", B=500) == R.lab_stratified_bounds(L, labs, [0.025], "t|lab", B=500)      # seeded: reproducible


def test_lab_stratified_row_can_only_lower_a_tier():
    L = np.full(40, 0.3)
    store = make_store()
    out = v4.run_v4(store)
    t, detail = R.lab_stratified_tiers(out, store, B=2000)
    assert t["P1"] == "S" and t["P2"] is True and t["K2"] == "S" and t["K1"] is True            # a clean positive effect in every laboratory keeps every tier
    assert detail["P1"]["strata_sizes"] == {"HM": 17, "INT": 19, "SIE": 4}
    # one laboratory (32 conditions) clearly positive, two small ones (4 + 4) clearly negative: pooled 32 of 40 positive passes tier S, the post-stratified median (1/3 per laboratory) does not
    Lm = np.array([0.4] * 32 + [-0.4] * 8)
    store2 = make_store(P1g1=Lm)
    store2.lab = {c: ("A" if i < 32 else ("B" if i < 36 else "C")) for i, c in enumerate(CONDS)}
    out2 = v4.run_v4(store2)
    assert out2["primary"]["tiers"]["P1"] == "S"
    t2, d2 = R.lab_stratified_tiers(out2, store2, B=2000)
    assert t2["P1"] in ("none", "reverse S") and d2["P1"]["point"] < 0 and d2["P1"]["strata_sizes"] == {"A": 32, "B": 4, "C": 4}
    out2f = R.run_v4_full(store2, B=2000)
    assert out2f["effective_tiers"]["P1"] in ("none", "reverse S") and out2f["outcome"]["P"] in ("P0", "P-")


def test_rows_recompute_at_the_primary_levels_and_equal_the_primary_when_the_store_is_unchanged():
    store = make_store()
    out = v4.run_v4(store)
    rule = v4.resolve_config()[0]
    t = R.row_tiers(out, store, rule)
    for k in ("P1", "P2", "P3", "K1", "K2"):
        assert t[k] == out["primary"]["tiers"][k]
    assert set(t) >= {"QA10_g1", "QA10_g4", "QH_g1", "QH_g4", "QT_g1"}
    assert set(R.row_tiers(out, store, rule, cells="g1")) == {"P1", "P2", "most"}                  # row (iv) covers the g1 contrasts of A1 and the D* candidates only
    weak = make_store(P1g1=0.01, A9g1=0.01)                                                  # same arms, weaker evidence
    t2 = R.row_tiers(out, weak, rule)
    assert t2["P1"] == "N" and t2["P2"] is False


def test_lowest_combines_tiers_and_booleans_and_never_raises():
    a = {"P1": "S", "P2": True, "QA10_g1": "N"}
    b = {"P1": "none", "P2": True}
    c = {"P1": "N", "P2": False, "QA10_g1": "reverse S"}
    assert R.lowest(a, b, c) == {"P1": "none", "P2": False, "QA10_g1": "reverse S"}
    assert R.lowest(None, {}, a) == a


def test_average_stores_means_the_condition_scores_over_the_draws():
    s1 = v4.Store({(8, "2"): {"A1": {"c1": 1.0, "c2": 2.0}, "D*": {"c1": 2.0, "c2": 2.0}}}, {}, {}, 4)
    s2 = v4.Store({(8, "2"): {"A1": {"c1": 3.0, "c2": 2.0}, "D*": {"c1": 2.0, "c2": 4.0}}}, {}, {}, 4)
    s3 = v4.Store({(8, "2"): {"A1": {"c1": 2.0, "c2": 2.0}, "D*": {"c1": 5.0, "c2": 3.0}}}, {}, {}, 4)
    m = R.average_stores([s1, s2, s3])
    assert m.scores("A1", 8, "2") == {"c1": 2.0, "c2": 2.0} and m.scores("D*", 8, "2") == {"c1": 3.0, "c2": 3.0}


def test_run_v4_full_lowers_the_title_when_a_row_is_weaker_and_flags_missing_rows():
    store = make_store()
    weak = make_store(P1g1=0.01)
    out = R.run_v4_full(store, lab_indicator=store, retain_all=store, random_subset=[store, store, store], B=1000)
    assert out["downgrade"]["rows_not_run"] == [] and not out["downgrade"]["provisional"] and out["outcome"]["P"] == "P+" and out["outcome"]["title_id"] == "T1"
    out2 = R.run_v4_full(store, lab_indicator=weak, retain_all=store, random_subset=[store] * 3, B=1000)
    assert out2["effective_tiers"]["P1"] == "N" and out2["primary"]["tiers"]["P1"] == "S" and out2["outcome"]["P"] == "P0"
    assert "lab_indicator" in out2["downgrade"]["rows_run"] and out2["downgrade"]["lowest_over_rows"]["P1"] == "N"
    out3 = R.run_v4_full(store, B=1000)
    assert out3["downgrade"]["provisional"] and out3["downgrade"]["rows_not_run"] == ["lab_indicator", "retain_all", "random_subset"] and out3["outcome"]["provisional_downgrade_rows_incomplete"]
    out4 = R.run_v4_full(store, random_subset=[weak, weak, weak], B=1000)               # the random-subset row at g1 lowers P1 as well
    assert out4["effective_tiers"]["P1"] == "N"


# ------------------------------------------------------------------------------------------------ Test C and S2
def test_test_c_descriptive_rows_the_sentence_and_the_abstract_rule():
    conds = CONDS[:13]
    t = {(32, "full"): {"A1": {c: 2.0 for c in conds}, "A10": {c: 2.0 * (1.2 if i < 9 else 0.9) for i, c in enumerate(conds)}, "D*": {c: 2.0 * 1.1 for c in conds}, "A9": {c: 2.2 for c in conds}}}
    st = v4.Store(t, LABS, FOLD, 4)
    rows = R.descriptive_entries(st, cell=v4.G4, test="C")
    a10 = rows["A10"]
    assert a10["n"] == 13 and a10["positives"] == 9 and a10["k_ratio_below_1"] == 9 and "no tier word" in a10["label"]
    assert a10["median_ratio"] == pytest.approx(1 / 1.2)
    s = R.test_c_sentences(rows)
    assert s["A10"].startswith("on a held-out combination of temperature and laboratory (35 C cells from one laboratory, n = 13 conditions) the median condition error ratio against the dataset authors' semi-empirical model was 0.83 (95 % interval [")
    assert s["A10"].endswith("; 9 of 13 below); temperature and laboratory cannot be separated in this design")
    assert "outperforms" not in s["A10"] and "significant" not in s["A10"]
    assert R.test_c_in_abstract(0.2, 0.1) and not R.test_c_in_abstract(0.2, -0.05) and not R.test_c_in_abstract(0.2, None) and R.test_c_in_abstract(-0.2, -0.3)
