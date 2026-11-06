"""D033 coder batch (debates/D033_signoff/01_judge.md, "Coder action list"): one group of tests per item.
F1/D1 registered statistics configuration and its pin, D2 ties, F2 number source of the abstract brackets, F6 non-finite NC-1, F7 invariance of the build path, F8 NC-2 permutation,
D3 Test C / S2 tables, D5 n_expected, M3 the 'whereas' joiner.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_d033_coder.py -q"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pandas as pd
import pytest

from pinnkan import blinding, guard, metrics, negcontrol, synth
from pinnkan import graph_test as gt
from pinnkan import stats_rows as R
from pinnkan import stats_step as ss
from pinnkan import stats_v4 as v4
from pinnkan.data import WindowRule, prepare_many, window_capped_cells
from pinnkan.specs import SPECS
from test_pk_v2_review import _grid_runs, _item_f_before
from test_pk_v2_stats import CONDS, make_store

SPEC = SPECS["synthetic"]


# ================================================================================================ F1 / D1: the registered configuration and its pin
def test_stats_config_file_is_the_default_config_and_is_pinned():
    pinned = {k: v for k, v in json.load(open(os.path.join(ROOT, v4.STATS_CONFIG_REL), encoding="utf8")).items() if not k.startswith("_")}
    assert pinned == v4.DEFAULT_CONFIG == {"sign_rule": "betabin", "rho_s0": 0.03, "graph_w": 0.78, "alpha": 0.025, "e1_prime_approved": True, "k_chain_struck": False,
                                           "sensitivity_rhos": [0.0, 0.01, 0.02, 0.03, 0.05]}
    assert v4.DEFAULT_CONFIG["graph_w"] == gt.W_ALT
    assert guard.PIN_FILES["stats_config"] == "runs/prereg/stats_config.json"


def test_resolve_config_and_run_v4_default_give_the_levels_0195_0055_and_the_counts_30_32():
    rule, c = v4.resolve_config()
    assert c["graph_w"] == 0.78 and c["e1_prime_approved"] is True
    assert rule.crit(40, 0.025 * c["graph_w"]) == 30 and rule.crit(40, 0.025 * (1 - c["graph_w"])) == 32
    pr = v4.run_v4(make_store(), cfg=None)["primary"]
    assert pr["initial_levels"]["P1N"] == pytest.approx(0.0195) and pr["initial_levels"]["K1"] == pytest.approx(0.0055)
    assert rule.crit(40, pr["initial_levels"]["P1N"]) == 30 and rule.crit(40, pr["initial_levels"]["K1"]) == 32
    out = v4.run_v4(make_store(), cfg=None)
    assert out["config"]["graph_w"] == 0.78 and out["config"]["e1_prime_approved"] is True and len(out["config_sha256"]) == 64
    assert out["config_sha256"] == v4.config_sha256(v4.resolve_config()[1])


def test_P2_S_P3_S_and_a_failing_most_test_give_e1_prime_by_default():
    out = v4.run_v4(make_store(P1g1=np.log(1.6), A9g1=np.log(1.1)), cfg=None)               # law share below half of the total: d_c < 0 for every condition
    t = out["primary"]["tiers"]
    assert t["P1"] == "S" and t["P2"] and t["P3"] and not out["most_test"]["most"]
    o = out["outcome"]
    assert o["extent_clause"] == "e1'" and "most of the advantage came from the physics law" not in o["abstract_sentence"]
    assert "the same network without the physics law was 10.0 % worse, and the advantage was larger with 8 than with 32 cycling conditions" in o["abstract_sentence"]
    assert v4.extent_clause({"P1": "S", "P2": True, "P3": True}, most=False, e1_prime_approved=True) == "e1'"
    assert v4.extent_clause({"P1": "S", "P2": True, "P3": True}, most=True, e1_prime_approved=True) == "e1"


def _frozen_root(tmp_path, cfg_text=None, pin=True):
    root = tmp_path / "froz"
    (root / "runs" / "prereg").mkdir(parents=True)
    src = os.path.join(ROOT, v4.STATS_CONFIG_REL)
    cfgp = root / "runs" / "prereg" / "stats_config.json"
    cfgp.write_text(cfg_text if cfg_text is not None else open(src, encoding="utf8").read())
    fr = {"commit": "a" * 40, "prereg_sha256": "0" * 64, "splits": {}, "config_sha256s": []}
    if pin:
        fr["pins"] = {"stats_config": {"file": "runs/prereg/stats_config.json", "sha256": guard.sha256_file(str(cfgp))}}
    (root / "runs" / "prereg" / "FROZEN").write_text(json.dumps(fr))
    return str(root)


def test_after_FROZEN_a_differing_config_or_sign_rule_is_refused(tmp_path):
    root = _frozen_root(tmp_path)
    cfg, pin = v4.effective_config(None, root)
    assert pin["frozen"] and pin["pinned"] and cfg["graph_w"] == 0.78 and cfg["e1_prime_approved"] is True and len(pin["file_sha256"]) == 64
    assert v4.effective_config({"graph_w": 0.78, "sign_rule": "betabin", "rho_s0": 0.03}, root)[0]["graph_w"] == 0.78           # the same values are accepted
    for bad in ({"graph_w": 0.5}, {"e1_prime_approved": False}, {"rho_s0": 0.02}, {"sign_rule": "plain"}, {"alpha": 0.05}, {"k_chain_struck": True, "graph_w": 1.0}):
        with pytest.raises(v4.StatsConfigPinError, match="differs"):
            v4.effective_config(bad, root)
    # before FROZEN nothing is enforced (development runs may use other values)
    nofrozen = tmp_path / "plain"
    nofrozen.mkdir()
    assert v4.effective_config({"graph_w": 0.5}, str(nofrozen))[0] == {"graph_w": 0.5}
    # an unpinned file refuses even with cfg=None
    with pytest.raises(v4.StatsConfigPinError):
        v4.effective_config(None, _frozen_root(tmp_path / "a", pin=False))
    r2 = _frozen_root(tmp_path / "b")
    with open(os.path.join(r2, v4.STATS_CONFIG_REL), "a") as fh:
        fh.write(" ")
    with pytest.raises(v4.StatsConfigPinError, match="pinned hash"):
        v4.effective_config(None, r2)


def test_run_stats_v4_and_its_cli_refuse_an_override_after_FROZEN_and_record_the_config_otherwise(tmp_path, monkeypatch):
    tmp = str(tmp_path)
    os.makedirs(tmp + "/g")
    dirs = _grid_runs(tmp + "/g")
    fdir, sha = _item_f_before(tmp, dirs)
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha)                      # unfrozen tree: the registered defaults
    rec = json.load(open(os.path.join(tmp, "an", "contrasts_v4_B.json")))
    assert rec["config"]["graph_w"] == 0.78 and rec["config"]["e1_prime_approved"] is True and rec["config_sha256"] == v4.config_sha256(v4.resolve_config()[1]) == out["config_sha256"]
    assert rec["config_pin"]["config_sha256"] == rec["config_sha256"] and rec["config_pin"]["frozen"] is False and rec["config_pin"]["n_expected"] == 40
    root = _frozen_root(tmp_path)
    monkeypatch.setattr(guard, "_DEFAULT_ROOT", root)
    with pytest.raises(v4.StatsConfigPinError, match="graph_w"):
        ss.run_stats_v4(os.path.join(tmp, "an2"), dirs, {"graph_w": 0.5}, item_f_dir=fdir, item_f_sha256=sha)
    with pytest.raises(v4.StatsConfigPinError, match="e1_prime_approved"):
        ss.main(["--analysis-dir", tmp + "/cli", "--runs", "B=" + ",".join(dirs), "--design", "r2", "--item-f-dir", fdir, "--item-f-sha256", sha, "--sign-rule", '{"e1_prime_approved": false}'])
    assert not os.path.exists(os.path.join(tmp, "an2", "contrasts_v4_B.json"))
    with pytest.raises(v4.StatsConfigPinError, match="n_expected"):
        ss.run_stats_v4(os.path.join(tmp, "an3"), dirs, item_f_dir=fdir, item_f_sha256=sha, n_expected=39)


# ================================================================================================ D2: ties are not positive, n is not reduced
def test_ties_in_every_user_of_the_sign_rule():
    r = v4.SignRule("betabin", 0.03)
    L = np.array([0.5] * 30 + [0.0] * 10)
    assert v4.node(r, L, 0.0, "x")["positives"] == 30 and v4.node(r, L, 0.0, "x")["n"] == 40
    assert R._positives_reach(r, L, 0.0, 0.0195)                                                                  # 30 of 40 at 0.0195 (the frozen count)
    assert not R._positives_reach(r, np.array([0.5] * 29 + [0.0] * 11), 0.0, 0.025)
    assert v4.PLAIN.test(np.array([v4.LOG_S] * 5 + [1.0] * 35), v4.LOG_S)[:2] == (35, 40)                         # L exactly at the margin is not positive


# ================================================================================================ F2: the brackets come from the analysis that set the tier
def test_the_red_team_probe_prints_a_positive_X_from_the_row_that_made_the_state(tmp_path):
    primary = make_store(P1g1=np.log(1.3))                                                                         # A1 better than D* by ln 1.3 in the primary analysis
    row = make_store(P1g1=-np.log(1.3))                                                                            # the lab-indicator re-run: D* better than A1 by ln 1.3
    with pytest.raises(v4.BracketSignError):                                                                       # the probe as the red team ran it: no source, a reverse-S state
        v4.run_v4(primary, row_tiers={"P1": "reverse S"})
    out = R.run_v4_full(primary, lab_indicator=row, B=300)
    o = out["outcome"]
    assert out["effective_tiers"]["P1"] == "reverse S" and o["P"] == "P-" and o["number_sources"]["P1"] == "lab_indicator"
    assert "was 23.1 % lower than that of the physics-informed network (95 % interval [23.1, 23.1]; n = 40)" in o["abstract_sentence"]
    assert "was -" not in o["abstract_sentence"]
    assert out["downgrade"]["number_sources"]["P1"] == "lab_indicator"


def test_K_minus_through_a_row_prints_the_rows_Z_and_interval():
    primary = make_store(K2=0.25)                                                                                  # K+ in the primary analysis
    row = make_store(K2=-0.25)                                                                                     # retain-every-check-up: the additive law beats the extracted law
    with pytest.raises(v4.BracketSignError):
        v4.run_v4(primary, row_tiers={"K2": "reverse S"})
    out = R.run_v4_full(primary, retain_all=row, B=300)
    o = out["outcome"]
    assert out["effective_tiers"]["K2"] == "reverse S" and o["K"] == "K-" and o["number_sources"]["K2"] == "retain_all" and o["P"] == "P+"
    assert "predicted held-out conditions 22.1 % more accurately than the law extracted from its Kolmogorov-Arnold network (95 % interval [22.1, 22.1])" in o["abstract_sentence"]


def test_P0_through_a_row_prints_the_rows_interval_not_the_primary_one():
    primary = make_store(P1g1=0.3)                                                                                 # primary: every condition favours A1: interval [25.9, 25.9]
    row = make_store(P1g1=np.array([0.3] * 20 + [-0.3] * 20))                                                      # row: tier none
    out = R.run_v4_full(primary, lab_indicator=row, B=300)
    o = out["outcome"]
    assert out["primary"]["tiers"]["P1"] == "S" and out["effective_tiers"]["P1"] == "none" and o["P"] == "P0" and o["number_sources"]["P1"] == "lab_indicator"
    assert "could not be distinguished from that of the best tuned data-driven learner (95 % interval [-35.0, 25.9]; n = 40)" in o["abstract_sentence"]
    assert "[25.9, 25.9]" not in o["abstract_sentence"]


def test_number_source_is_the_primary_if_lowest_else_the_first_row_in_the_order_i_to_iv():
    store = make_store()
    first = v4.run_v4(store)
    rule = v4.resolve_config()[0]
    detail = {"P1": "d"}
    rows = {"lab_stratified": {"P1": "N", "K2": "S", "P2": True}, "lab_indicator": {"P1": "N", "K2": "none"}, "retain_all": {"P1": "none"}, "random_subset": {"P1": "none"}}
    stores = {"lab_indicator": make_store(), "retain_all": make_store(), "random_subset": make_store()}
    src = R.number_sources(first, rows, stores, detail, rule)
    assert src["P1"]["kind"] == "retain_all"                                                                       # lowest tier 'none' first appears in row (iii)
    assert src["K2"]["kind"] == "lab_indicator" and src["K2"]["store"] is stores["lab_indicator"]
    assert src["P2"]["kind"] == "primary"                                                                          # the primary tier is True and no row is lower
    rows2 = {"lab_stratified": {"P1": "N"}, "lab_indicator": {"P1": "N"}}
    assert R.number_sources(first, rows2, stores, detail, rule)["P1"] == {"kind": "lab_stratified", "alpha": 0.025, "detail": detail}
    assert R.number_sources(first, {"lab_stratified": {"P1": "S"}}, stores, detail, rule)["P1"] == {"kind": "primary"}


def test_row_i_numbers_are_the_weighted_median_with_the_two_sided_95_percent_bootstrap_interval():
    store = make_store(P1g1=np.linspace(0.05, 0.6, 40))
    conds, L, _ = store.L("A1", "D*", (8, "2"))
    b = R.lab_stratified_bounds(L, [store.lab[c] for c in conds], [0.025], "B|lab-stratified|P1", B=400)
    src = {"kind": "lab_stratified", "alpha": 0.025, "detail": {"P1": b}}
    num = v4.primary_numbers(store, v4.resolve_config()[0], {"P1": "S"}, None, {"P1": src})
    assert num["X"] == pytest.approx(v4.pct_reduction(b["point"])) and num["sources"]["P1"] == "lab_stratified"
    assert num["interval_P1"] == (pytest.approx(v4.pct_reduction(b["lower"]["0.025"])), pytest.approx(v4.pct_reduction(b["upper"]["0.025"])))
    assert num["n"] == 40
    with pytest.raises(v4.BracketSignError):                                                                       # the printed sign must follow the state
        v4.primary_numbers(store, v4.resolve_config()[0], {"P1": "reverse S"}, None, {"P1": src})


def test_qualifier_sentences_follow_the_same_source_rule():
    primary = make_store(A2g1=0.3)                                                                                 # Q-H: A1 better than the hard ODE by 0.3
    row = make_store(A2g1=-0.3)                                                                                    # the row: the hard ODE better
    out = R.run_v4_full(primary, lab_indicator=row, B=300)
    q = out["qualifier_sentences"]["QH_g1"]
    assert out["secondary"]["tests"]["QH_g1"]["tier"] == "reverse S" and out["qualifier_number_sources"]["QH_g1"] == "lab_indicator"
    assert q.startswith("the hard ODE with the same law had a median condition error 25.9 % lower than the soft-residual network (95 % interval [25.9, 25.9]")
    with pytest.raises(v4.BracketSignError):
        v4.run_v4(primary, row_tiers={"QH_g1": "reverse S"})


# ================================================================================================ M3: the 'whereas' joiner only for P-/K+
def test_whereas_is_written_for_P_minus_K_plus_only():
    base = dict(P1="reverse S", P2=False, P3=False, K1=True, QH_g1="none", QA10_g1="none")
    num = {"X": 20.0, "Y": 5.0, "Z": 10.0, "W": 3.0, "interval_P1": (10.0, 30.0), "interval_K2": (5.0, 15.0), "n": 40}
    kplus = v4.assemble_outcome({**base, "K2": "S"}, num)["abstract_sentence"]
    keq = v4.assemble_outcome({**base, "K2": "none"}, num)["abstract_sentence"]
    kminus = v4.assemble_outcome({**base, "K2": "reverse S"}, num)["abstract_sentence"]
    assert ", whereas a closed-form stress law" in kplus
    assert "whereas" not in keq and ", and a closed-form stress law extracted from its Kolmogorov-Arnold network predicted held-out conditions no more than 10 % worse" in keq
    assert "whereas" not in kminus and ", while an equally simplified additive stress law" in kminus


# ================================================================================================ F6: non-finite predictions fail NC-1 at any position
@pytest.fixture(scope="module")
def g2():
    S = synth.make_synthetic("G2", n_cyc_cond=14, n_sto_cond=6, reps=2, seed=3)
    return synth.split_conditions(S.cells, 0.3, 3)


def _const_predict(windows):
    return {w.cell_id: np.full(len(w.t_fc), 0.9) for w in windows}


@pytest.mark.parametrize("where", ["first", "middle", "last"])
@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_nc1_fails_on_a_non_finite_prediction_at_any_cell(g2, where, bad):
    _, te = g2
    rule = WindowRule.for_spec(SPEC)
    ids = sorted(w.cell.cell_id for w in prepare_many(te, rule))
    target = {"first": ids[0], "middle": ids[len(ids) // 2], "last": ids[-1]}[where]
    base = _const_predict([p.win for p in prepare_many(te, rule)])
    clean = negcontrol.check_invariance(_const_predict, te, rule, SPEC)
    assert clean["passed"] and clean["max_abs_diff"] == 0.0 and not clean["non_finite"]
    poisoned = {k: v.copy() for k, v in base.items()}
    poisoned[target][-1] = bad
    # non-finite only in the re-prediction under scrambled labels
    seq = iter([base, poisoned])
    r = negcontrol.check_invariance(lambda w: next(seq), te, rule, SPEC)
    assert not r["passed"] and r["non_finite"] and np.isnan(r["max_abs_diff"])
    # non-finite in the base AND the re-prediction (NaN in both runs: the difference is NaN or 0, the prediction is still not finite)
    r2 = negcontrol.check_invariance(_const_predict, te, rule, SPEC, base_preds=poisoned)
    assert not r2["passed"] and r2["non_finite"]
    r3 = negcontrol.check_invariance(lambda w: poisoned, te, rule, SPEC, base_preds=poisoned)
    assert not r3["passed"] and r3["non_finite"] and r3["n_rows"] > 0


def test_nc1_summarise_never_drops_a_nan_and_the_python_max_pitfall_is_closed():
    rec = {f"A|{i}": dict(passed=True, max_abs_diff=0.0, n_rows=3) for i in range(3)}
    rec["A|3"] = dict(passed=False, max_abs_diff=float("nan"), n_rows=3)
    s = negcontrol.summarise(rec)
    assert not s["passed"] and np.isnan(s["max_abs_diff"])
    assert max([0.0, float("nan")]) == 0.0                                                                         # the pitfall itself, for the record
    rec2 = {"A|0": dict(passed=True, max_abs_diff=0.0, n_rows=3), "A|1": dict(passed=True, max_abs_diff=float("nan"), n_rows=3)}
    assert np.isnan(negcontrol.summarise(rec2)["max_abs_diff"])                                                    # even an inconsistent record shows the NaN
    st = ss.nc1_from_runs([])
    assert st["passed"] is False and np.isnan(st["max_abs_diff"])


def _pred_csv(d, preds, phases=("outer_test_kfull", "inner_oof")):
    os.makedirs(d, exist_ok=True)
    rows = []
    for ph in phases:
        for i, p in enumerate(preds[ph]):
            rows.append(dict(phase=ph, arm="A1", seed=0, cell_id=f"c{i}", cond=f"k{i}", t=float(i), pred_retention=p))
    pd.DataFrame(rows).to_csv(os.path.join(d, "predictions.csv"), index=False)
    for f in ("tuning_done.json", "margins_inputs.json"):
        json.dump({"x": 1}, open(os.path.join(d, f), "w"))


@pytest.mark.parametrize("variant", ["clean", "nan_first", "nan_middle", "nan_last", "inf", "nan_both", "inf_both", "nan_inner"])
def test_compare_runs_fails_closed_on_non_finite_predictions(tmp_path, variant):
    clean = {"outer_test_kfull": [0.9, 0.8, 0.7, 0.6, 0.5], "inner_oof": [0.9, 0.8, 0.7]}
    a, b = {k: list(v) for k, v in clean.items()}, {k: list(v) for k, v in clean.items()}
    spec = {"nan_first": (b, "outer_test_kfull", 0, np.nan), "nan_middle": (b, "outer_test_kfull", 2, np.nan), "nan_last": (b, "outer_test_kfull", 4, np.nan), "inf": (b, "outer_test_kfull", 3, np.inf),
            "nan_inner": (b, "inner_oof", 2, np.nan)}
    if variant in spec:
        t, ph, i, v = spec[variant]
        t[ph][i] = v
    if variant in ("nan_both", "inf_both"):
        v = np.nan if variant == "nan_both" else np.inf
        a["outer_test_kfull"][3] = b["outer_test_kfull"][3] = v
    _pred_csv(str(tmp_path / "a"), a)
    _pred_csv(str(tmp_path / "b"), b)
    r = negcontrol.compare_runs(str(tmp_path / "a"), str(tmp_path / "b"), outer_phase="full")
    assert r["passed"] is (variant == "clean")
    if variant != "clean":
        assert r["n_non_finite_predictions"] > 0


# ================================================================================================ F7: invariance of the real-data build path (cut points, anchoring, cap, labels)
def _fake_samsung_root(tmp_path, scramble=None):
    """a pipeline table of 3 conditions x 3 cycling cells, ET-free (first check-up is the reference), 12 check-ups each except two short cells (5 and 3 check-ups); `scramble` = {cell_id: first
    index to garble} replaces the capacity after that index by garbage (the upstream, pre-build form of NC-1)"""
    rows = []
    n_of = {}
    for tp, (T, smax, dod, cch, cdch) in enumerate([(23, 0.8, 0.5, 0.5, 1.0), (35, 0.8, 0.6, 1.0, 2.0), (45, 0.6, 0.3, 0.5, 1.0)], start=1):
        for cell in (1, 2, 3):
            cid = f"TP_z{tp:02d}_0{cell}_s2"
            n = 12
            if (tp, cell) == (2, 3):
                n = 5
            if (tp, cell) == (3, 3):
                n = 3
            n_of[cid] = n
            q = 3.0 * (1.0 - 0.01 * np.arange(n) - 0.002 * np.random.default_rng([5, tp, cell]).random(n))          # one stream per cell: the scramble cannot shift other cells' draws
            if scramble and cid in scramble:
                q = q.copy()
                q[scramble[cid]:] = 3.0 * np.random.default_rng([6, tp, cell]).uniform(0.3, 1.2, n - scramble[cid])
            for i in range(n):
                rows.append(dict(cell_id=cid, kind="CU", serial=f"TP_z{tp:02d}_0{cell}", stage=2, file_idx=i + 1, qc_pass=True, type="z", T_C=T, SOC_max=smax, DoD=dod, C_ch=cch, C_dch=cdch,
                                 cell=cell, tp=tp, lab="HM" if tp < 3 else "INT", elapsed_days=7.0 * i, q_mean_ah=float(q[i]), efc_est_cum=20.0 * i))
    d = tmp_path / ("scr" if scramble else "clean") / "data" / "processed"
    d.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(d / "samsung_checkups.csv", index=False)
    return str(d.parent.parent), n_of


def test_scrambling_post_window_capacities_before_the_loader_leaves_training_data_and_windows_byte_identical(tmp_path):
    from pinnkan import data as D
    rule = WindowRule.for_spec(SPECS["samsung"], k_cycling=4, k_storage=2)
    _, n_of = _fake_samsung_root(tmp_path / "x")
    test_conds = {"T35|SOCmax0.8|DoD0.6|Cch1|Cdch2", "T45|SOCmax0.6|DoD0.3|Cch0.5|Cdch1"}
    # window end per cell under the rule (identifiers and counts only): garble everything after it, for the test cells only
    garble = {cid: rule.window_end(type("C", (), {"kind": "cycling", "n": n})()) + 1 for cid, n in n_of.items() if cid.split("_")[1] in ("z02", "z03")}
    root_a, _ = _fake_samsung_root(tmp_path / "a")
    root_b, _ = _fake_samsung_root(tmp_path / "b", scramble=garble)
    keep_train = lambda cid, cond, kind, no: cond not in test_conds
    keep_test = lambda cid, cond, kind, no: cond in test_conds
    tr_a, tr_b = D._load_samsung(root_a, keep=keep_train), D._load_samsung(root_b, keep=keep_train)
    assert [c.cell_id for c in tr_a] == [c.cell_id for c in tr_b] and len(tr_a) == 3
    for a, b in zip(tr_a, tr_b):
        for f in ("raw", "t", "ret", "efc", "fc_ok"):
            assert getattr(a, f).tobytes() == getattr(b, f).tobytes()                                              # training data byte-identical
        assert (a.cond, a.lab, a.stage, a.meta) == (b.cond, b.lab, b.stage, b.meta)
    te_a, te_b = D._load_samsung(root_a, keep=keep_test), D._load_samsung(root_b, keep=keep_test)
    assert [c.cell_id for c in te_a] == [c.cell_id for c in te_b] and len(te_a) == 6
    assert window_capped_cells(te_a, rule) == window_capped_cells(te_b, rule) and len(window_capped_cells(te_a, rule)) == 2          # the D025 cap list: same cells
    assert any(c.n == 3 for c in te_a) and any(c.n == 5 for c in te_a)                                             # the two short-record cells are in the test set
    for a, b in zip(te_a, te_b):
        assert a.t.tobytes() == b.t.tobytes() and a.efc.tobytes() == b.efc.tobytes() and a.raw.tobytes() == b.raw.tobytes() and a.fc_ok.tobytes() == b.fc_ok.tobytes()
        assert (a.cond, a.lab, a.stage) == (b.cond, b.lab, b.stage)
        w = rule.window_end(a)
        assert a.ret[: w + 1].tobytes() == b.ret[: w + 1].tobytes()                                               # reference anchoring and the window labels
        assert not np.array_equal(a.ret[w + 1:], b.ret[w + 1:]) or a.n - 1 <= w                                    # the scramble really changed the labels after the window
    pa, pb = prepare_many(te_a, rule), prepare_many(te_b, rule)
    assert [p.cell.cell_id for p in pa] == [p.cell.cell_id for p in pb] and len(pa) == 5                          # the 3-check-up cell is unscored in both (no window of 3 points)
    for a, b in zip(pa, pb):
        assert a.win.t_win.tobytes() == b.win.t_win.tobytes() and a.win.y_win.tobytes() == b.win.y_win.tobytes() and a.win.efc_win.tobytes() == b.win.efc_win.tobytes()
        assert a.win.t_fc.tobytes() == b.win.t_fc.tobytes() and a.win.efc_curve.t.tobytes() == b.win.efc_curve.t.tobytes() and a.win.efc_curve.e.tobytes() == b.win.efc_curve.e.tobytes()
        assert a.win.efc_curve.tail == b.win.efc_curve.tail and a.w_idx == b.w_idx


def test_qc_flags_are_causal_so_window_labels_cannot_move_but_check_ups_after_the_window_can_be_dropped():
    """finding (F7): data/samsung_checkups.flag_outliers is causal (the flag of a check-up never changes when LATER capacities change), so the window, the anchoring and the training sides cannot depend
    on post-window labels through the QC. A post-window garbage value can, however, be flagged and dropped upstream of build_data, which changes the retained record length n and with it the
    D025 window (min(k, n - 2)) of a short cell and the forecast set of any cell. NC-1 (scramble after build_data) holds the retained set fixed by construction; this is reported, not fixed."""
    from data.samsung_checkups import flag_outliers
    n = 8
    x = 7.0 * np.arange(n)
    q = 3.0 * (1.0 - 0.01 * np.arange(n))
    valid = np.ones(n, bool)
    clean = flag_outliers(x, q, valid)
    q2 = q.copy()
    q2[5:] = [3.9, 0.9, 3.5]                                                                                       # garbage after check-up 4
    scr = flag_outliers(x, q2, valid)
    assert np.array_equal(clean[:5], scr[:5]) and not clean.any()                                                  # causal: nothing up to the cut moves
    assert scr[5:].any()                                                                                           # but later check-ups can be dropped, shortening the retained record
    rule = WindowRule.for_spec(SPECS["samsung"], k_cycling=4, k_storage=2)
    mk = lambda n_: type("C", (), {"kind": "cycling", "n": n_})()
    assert rule.window_end(mk(int((~clean).sum()))) != rule.window_end(mk(int((~scr).sum()))) or int((~scr).sum()) >= 6


def test_synthetic_short_record_cells_are_capped_unscored_and_pass_nc1(g2):
    tr, te = g2
    te_s = synth.shorten_cells(te, [4, 3])
    assert [c.n for c in te_s if c.kind == "cycling"][:2] == [4, 3] and te_s[0].t.shape == te_s[0].ret.shape == te_s[0].efc.shape == te_s[0].fc_ok.shape
    rule = WindowRule.for_spec(SPEC, k_cycling=4, k_storage=2)
    assert len(window_capped_cells(te_s, rule)) >= 1 and len(prepare_many(te_s, rule)) == len(prepare_many(te, rule)) - 1       # the 3-point cell has no window of 3 points
    r = negcontrol.check_invariance(_const_predict, te_s, rule, SPEC)
    assert r["passed"] and r["max_abs_diff"] == 0.0 and r["forecast_sets_equal"]
    assert synth.shorten_cells(te, None) is te
    with pytest.raises(ValueError):
        synth.shorten_cells(te, [99])


# ================================================================================================ F8: NC-2 permutes the stress vector only
def test_permute_stress_keeps_throughput_times_retention_and_window_and_is_a_derangement_in_train_and_in_test():
    S = synth.make_synthetic("G0", n_cyc_cond=12, n_sto_cond=4, reps=2, seed=4)
    tr, te = synth.split_conditions(S.cells, 0.3, 4)
    rule = WindowRule.for_spec(SPEC)
    for cells, seed in ((tr, 0), (te, 1000)):
        P = metrics.permute_stress(cells, SPEC, seed)
        assert [c.cell_id for c in P] == [c.cell_id for c in cells]
        donor = {}
        for c, p in zip(cells, P):
            for f in ("t", "ret", "efc", "fc_ok"):
                assert getattr(c, f).tobytes() == getattr(p, f).tobytes()                                          # each cell's own throughput, times, retention, forecast mask
            assert c.cond == p.cond and c.kind == p.kind
            if c.kind == "cycling":
                assert not np.allclose(p.raw, c.raw)
                donor[c.cond] = p.meta["stress_permuted_from"]
                a, b = prepare_many([c], rule), prepare_many([p], rule)
                assert a[0].w_idx == b[0].w_idx and a[0].win.t_win.tobytes() == b[0].win.t_win.tobytes() and a[0].win.efc_win.tobytes() == b[0].win.efc_win.tobytes()
                assert a[0].win.y_win.tobytes() == b[0].win.y_win.tobytes() and a[0].win.t_fc.tobytes() == b[0].win.t_fc.tobytes() and a[0].fc_true.tobytes() == b[0].fc_true.tobytes()
                assert a[0].win.efc_curve.tail == b[0].win.efc_curve.tail and a[0].win.efc_curve.e.tobytes() == b[0].win.efc_curve.e.tobytes()          # the causal throughput curve is the cell's own
            else:
                assert p is c
        assert all(k != v for k, v in donor.items()) and sorted(donor) == sorted(donor.values())                   # a derangement of the conditions within this set
        assert set(donor.values()) <= {c.cond for c in cells}                                                      # donors come from the same set (train from train, test from test)
        # the stress vectors are a permutation of the set's own vectors
        mine = sorted(tuple(np.round(c.raw, 9)) for c in cells if c.kind == "cycling")
        moved = sorted(tuple(np.round(p.raw, 9)) for p in P if p.kind == "cycling")
        assert mine == moved


# ================================================================================================ D3: Test C / S2 tables, both plain intervals; wired into run_stats_v4
def _test_c_run(tmp, name, a9=0.3, a10=-0.2, n=13):
    d = os.path.join(tmp, name)
    os.makedirs(d)
    json.dump({"m": None, "fold": 0, "design": "R2", "inner_k": 2}, open(os.path.join(d, "config.json"), "w"))
    json.dump({"k_full": 4}, open(os.path.join(d, "metrics.json"), "w"))
    json.dump({"D*": {"arm": "A9", "complete": True}}, open(os.path.join(d, "comparators.json"), "w"))
    conds = CONDS[:n]
    lv = lambda v: np.full(n, v) if np.isscalar(v) else np.asarray(v, float)
    sc = {"A1": {c: 2.0 for c in conds}, "A9": {c: 2.0 * np.exp(v) for c, v in zip(conds, lv(a9))}, "A10": {c: 2.0 * np.exp(v) for c, v in zip(conds, lv(a10))}}
    sc["A10P"] = dict(sc["A10"])
    json.dump(sc, open(os.path.join(d, "condition_scores.json"), "w"))
    return d


def test_descriptive_entries_print_the_plain_95_and_the_1_minus_0p05_over_9_intervals():
    for n, rank_sim, rank_95 in ((13, 2, 3), (19, 4, 5)):
        L = np.sort(np.random.default_rng(n).normal(0.2, 0.3, n))
        tab = {"A1": {f"c{i}": 2.0 for i in range(n)}, "A9": {f"c{i}": 2.0 * np.exp(L[i]) for i in range(n)}}
        rows = R.descriptive_entries(v4.Store({(32, "full"): tab}), arms=("A9",), test="C")
        r = rows["A9"]
        assert r["ratio_ci_simultaneous_rank"] == rank_sim and r["ratio_ci_95_rank"] == rank_95
        assert r["ratio_ci_simultaneous"] == [pytest.approx(np.exp(-L[n - rank_sim])), pytest.approx(np.exp(-(L[rank_sim - 1])))]                  # [L(r), L(n + 1 - r)] of the sorted log ratios
        assert r["ratio_ci"] == r["ratio_ci_95"] and r["ratio_ci_simultaneous_coverage"] > r["ratio_ci_95_coverage"]
        assert r["ratio_ci_simultaneous"][1] / r["ratio_ci_simultaneous"][0] > r["ratio_ci_95"][1] / r["ratio_ci_95"][0]


def test_run_stats_v4_writes_the_test_c_table_and_applies_rule_9_8_3(tmp_path):
    tmp = str(tmp_path)
    os.makedirs(tmp + "/g")
    dirs = _grid_runs(tmp + "/g")
    fdir, sha = _item_f_before(tmp, dirs)
    c_run = _test_c_run(tmp, "C", a9=0.3, a10=-0.2)
    c_lab_same = _test_c_run(tmp, "Clab", a9=0.1, a10=-0.1)                                                        # same signs
    c_lab_flip = _test_c_run(tmp, "Clab2", a9=-0.1, a10=-0.1)                                                      # A9 sign flips
    s2 = _test_c_run(tmp, "S2", n=19)
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha, test_c_runs=[c_run], test_c_lab_indicator_runs=[c_lab_flip], s2_runs=[s2])
    tc = out["test_c"]
    assert tc["rows"]["A9"]["n"] == 13 and tc["rows"]["A9"]["ratio_ci_simultaneous_rank"] == 2 and tc["rows"]["A9"]["ratio_ci_95_rank"] == 3
    assert set(tc["sentences"]) == {"A10", "D*"} or set(tc["sentences"]) >= {"A10"}
    assert tc["in_abstract"]["A9"] is False and tc["in_abstract"]["A10"] is True and tc["in_abstract"]["A10P"] is True       # A9's sign flips under the lab-indicator row; A10's does not
    assert out["s2"]["rows"]["A9"]["n"] == 19 and out["s2"]["rows"]["A9"]["ratio_ci_simultaneous_rank"] == 4
    assert "on a held-out combination of temperature and laboratory" in tc["sentences"]["A10"] and "temperature and laboratory cannot be separated" in tc["sentences"]["A10"]
    assert set(out["outcome"]["test_c_sentences_for_abstract"]) == {a for a in tc["sentences"] if tc["in_abstract"].get(a)} and "A10" in out["outcome"]["test_c_sentences_for_abstract"]
    rec = json.load(open(os.path.join(tmp, "an", "contrasts_v4_B.json")))
    assert rec["test_c"]["rows"]["A10"]["ratio_ci_95_rank"] == 3 and rec["s2"]["rows"]["A10"]["n"] == 19
    # the lab-indicator row is missing: nothing enters the abstract and the outcome is provisional
    out2 = ss.run_stats_v4(os.path.join(tmp, "an2"), dirs, item_f_dir=fdir, item_f_sha256=sha, test_c_runs=[c_run])
    assert out2["test_c"]["row_lab_indicator_not_run"] and not any(out2["test_c"]["in_abstract"].values()) and out2["status"]["provisional"] and out2["outcome"]["test_c_sentences_for_abstract"] == {}
    assert R.test_c_in_abstract(0.3, 0.1) and not R.test_c_in_abstract(0.3, -0.1) and not R.test_c_in_abstract(0.3, None) and not R.test_c_in_abstract(0.0, 0.0)
    assert c_lab_same


# ================================================================================================ D5: n_expected from the pinned blinding_exclusions.json
def _exclusion_file(tmp_path, dropped_b):
    rec = json.load(open(os.path.join(ROOT, "runs", "prereg", "blinding_exclusions.json"), encoding="utf8"))
    rec["n_conditions_dropped"] = {"B": dropped_b, "S2": 0}
    rec["sha256"] = blinding.body_sha256(rec)
    root = tmp_path / f"bl{dropped_b}"
    (root / "runs" / "prereg").mkdir(parents=True)
    json.dump(rec, open(root / "runs" / "prereg" / "blinding_exclusions.json", "w"))
    return str(root)


def test_n_expected_is_40_minus_the_pinned_dropped_conditions_and_39_is_accepted_only_then(tmp_path):
    assert blinding.expected_n(ROOT, "B") == 40                                                                    # the pinned file of this tree drops no condition
    r39 = _exclusion_file(tmp_path, 1)
    assert blinding.expected_n(r39, "B") == 39 and blinding.expected_n(r39, "S2") == 19
    d = str(tmp_path / "g39")
    os.makedirs(d)
    runs = _grid_runs(d, drop_cond=True)                                                                           # fold 0 has 7 conditions: A1 has 39 conditions
    st = v4.Store.from_runs(runs, strict=True)
    with pytest.raises(v4.IncompleteStoreError, match="expected 40"):
        st.check_complete(n_expected=blinding.expected_n(ROOT, "B"))
    assert st.check_complete(n_expected=blinding.expected_n(r39, "B"))
    # an edited exclusions file (hash mismatch) is refused
    bad = json.load(open(os.path.join(r39, "runs", "prereg", "blinding_exclusions.json")))
    bad["n_conditions_dropped"]["B"] = 0
    json.dump(bad, open(os.path.join(r39, "runs", "prereg", "blinding_exclusions.json"), "w"))
    with pytest.raises(blinding.BlindingExclusionError):
        blinding.expected_n(r39, "B")
    # no file, tree not frozen: the designed number; no file but pinned in FROZEN: error
    nofile = tmp_path / "nofile"
    (nofile / "runs" / "prereg").mkdir(parents=True)
    assert blinding.expected_n(str(nofile), "B") == 40
    (nofile / "runs" / "prereg" / "FROZEN").write_text(json.dumps({"commit": "a" * 40, "prereg_sha256": "0" * 64, "splits": {}, "config_sha256s": [], "pins": {"blinding_exclusions": {"file": "x", "sha256": "0"}}}))
    with pytest.raises(blinding.BlindingExclusionError):
        blinding.expected_n(str(nofile), "B")


def test_run_stats_v4_derives_n_expected_from_the_exclusions_file(tmp_path, monkeypatch):
    tmp = str(tmp_path)
    os.makedirs(tmp + "/g")
    dirs = _grid_runs(tmp + "/g", drop_cond=True)                                                                  # 39 conditions in every cell
    fdir, sha = _item_f_before(tmp, dirs)
    with pytest.raises(v4.IncompleteStoreError, match="expected 40"):
        ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    out = ss.run_stats_v4(os.path.join(tmp, "an39"), dirs, item_f_dir=fdir, item_f_sha256=sha, root=_exclusion_file(tmp_path, 1))
    assert out["config_pin"]["n_expected"] == 39
