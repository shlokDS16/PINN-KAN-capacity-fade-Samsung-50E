"""Inputs of the display items that the Design R2 statistics step did not produce (code/figures/ALIGN_V4_REPORT.md section 3, gaps G1-G8; code/pinnkan/STATS_GAPS_REPORT.md).

No-regression rule: every pre-existing output of `run_stats_v4` (contrasts_v4_B.json, controls.json gate fields, margins.json, physval_11a.json) is byte-identical with and without the new
inputs once the new keys are removed; then one block of unit tests per gap on a synthetic store (invented numbers; no Samsung, ISU or SNL file is read).
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_stats_gaps_g1_g8.py -q"""
import copy
import json
import os
import sys
import time
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np
import pytest

from pinnkan import emit, physval, semi, stats_gaps as sg, stats_step as ss
from pinnkan import extraction_audit as X
from pinnkan import graph_test as gt
from pinnkan import stats_v4 as v4
from test_pk_v2_stats import CONDS, FOLD, LABS, make_store

G1, G4 = v4.G1, v4.G4
RULE = v4.resolve_config()[0]
SOC = list(np.arange(0, 101, 5.0))
T_GRID = [10, 23, 45]
ARM_MU = {"A1": 0.0, "A9": 0.40, "A11": 0.20, "A12": 0.25, "A4": 0.10, "A5": 0.12, "A2": 0.03, "A10": 0.20, "A10P": 0.15, "A13": 0.06, "R1": 0.70, "R2": 0.50, "A15": 0.0, "G15": 0.20}


def _dump(obj, path):
    with open(path, "w", encoding="utf8") as fh:
        json.dump(obj, fh, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))


# ------------------------------------------------------------------------------------------------ the synthetic grid (invented numbers)
def _stress_functions(rng, n_members=3, bad_soc=None):
    soc = np.array(SOC)
    base = 1.0 + 0.02 * soc
    rate = np.stack([[base * (T / 23.0) ** 2 * (1 + 0.01 * rng.normal(size=len(soc))) for T in T_GRID] for _ in range(n_members)])        # members x nT x nSOC, increasing in T
    if bad_soc is not None:
        j = int(np.argmin(abs(soc - bad_soc)))
        rate[0, 2, j] = rate[0, 1, j] * 0.5                                                                                              # one member: 45 C below 23 C at one SOC
    E = 60 + rng.normal(size=(n_members, len(soc)))
    a = 1.0 + 0.5 * soc / 100 + 0.01 * rng.normal(size=(n_members, len(soc)))
    sel = [5, 50, 80, 100]
    lr = np.stack([np.log(rate[:, :, int(np.argmin(abs(soc - s)))]) for s in sel], 1)                                                    # members x n_sel x nT
    band = lambda m: dict(mean=np.mean(m, 0).tolist(), lo=np.min(m, 0).tolist(), hi=np.max(m, 0).tolist())
    members = {"E_kJmol": E.tolist(), "a_pp500": a.tolist(), "storage_rate": rate.tolist(), "arrhenius_ln_rate": lr.tolist()}
    cyc = {}
    for name, x in (("T", np.linspace(5, 50, 46)), ("soc_mid", np.linspace(10, 90, 41)), ("dod", np.linspace(0, 80, 41)), ("c_ch", np.linspace(0, 1.2, 49)), ("c_dch", np.linspace(0, 2.2, 45))):
        mem = np.stack([(x - x.mean()) / (np.ptp(x) or 1) + 0.01 * rng.normal(size=len(x)) for _ in range(n_members)])
        members[f"cyclic.{name}"] = mem.tolist()
        cyc[name] = dict(x=x.tolist(), A1=band(mem), A4=dict(mean=(0.9 * mem.mean(0)).tolist()), A10=dict(mean=(1.1 * mem.mean(0)).tolist()))
    return dict(n_members=n_members, calendar=dict(soc=SOC, E_kJmol=band(E), a_pp500=band(a), A10_E_kJmol=61.0), storage_rate=dict(T_C=T_GRID, soc=SOC, **band(rate)),
                arrhenius=dict(soc=sel, T_C=T_GRID, ln_rate=band(lr)), cyclic=cyc, members=members, a_pp500_definition="calendar loss after 500 d at 25 C (pp, backbone applied), no cycling")


def _law_forms(rng, fold, lhs):
    hull = rng.uniform(-0.8, 0.8, (40, 5))
    coef = np.array([0.5, 1.0, -0.4, 0.8, 0.3])
    laws = []
    for arm, scale in (("A15h2", 1.0), ("G15", 1.2)):
        for sd in range(5):
            lr = lhs @ coef * scale + 0.05 * (fold + 1) * rng.normal(size=len(lhs))
            laws.append(dict(arm=arm, fold=fold, seed=sd, h=2, n_coefs=12 + sd, n_params=2600 + fold, train_bic=100.0 + 10 * fold + sd, closed_form=[f"cyclic layer 0 edge 0<-1: linear [{sd}.0, 0.1]"],
                             cyclic=[{"layer": 0, "edges": [[{"display": "temperature"}, {"family": "linear", "theta": [1.0, 0.0]}]]}], calendar=None,
                             pd={v: (0.1 * rng.normal(size=11)).tolist() for v in ("soc_mid", "dod", "c_ch", "c_dch")}, log_rate_on_lhs=lr.tolist()))
    return dict(m=32, fold=fold, lhs=dict(seed=1, n=len(lhs), space="s", points=lhs.tolist()), pd_grid={v: np.linspace(0, 1, 11).tolist() for v in ("soc_mid", "dod", "c_ch", "c_dch")},
                train_hull_points=hull.tolist(), laws=laws)


def make_grid(tmp, seed=3, bad_soc=None, with_extras=True):
    """a complete fake Design R2 grid (5 folds x m in (8, 16, 32), k in 0 / 2 / full, 40 conditions, random log ratios so that no score ties) with every file the new inputs read"""
    rng = np.random.default_rng(seed)
    lhs = emit.lhs_points()
    base = {c: float(np.exp(rng.normal(0, 0.3))) * 2.0 for c in CONDS}
    dirs = []
    for f in range(5):
        conds = [c for c in CONDS if FOLD[c] == f]
        for m in (8, 16, 32):
            d = os.path.join(tmp, f"f{f}_m{m}")
            os.makedirs(d)
            _dump({"m": m, "fold": f, "design": "R2", "test": "B", "dataset": "synthetic", "inner_k": 2}, os.path.join(d, "config.json"))
            _dump({"D*": {"arm": "A11" if f % 2 == 0 else "A12", "complete": True}, "AG": {"arm": "A4", "complete": True}}, os.path.join(d, "comparators.json"))
            by_k = {}
            for kl in ("0", "2", "full"):
                suf = "" if kl == "full" else f"_k{kl}"
                arms = [a for a in ARM_MU if not (kl == "0" and a in ("R1", "R2")) and not (a in ("A15", "G15") and not (m == 32 and kl == "full"))]
                sc = {a: {c: float(base[c] * (1.3 if kl == "0" else 1.0) * np.exp(ARM_MU[a] + rng.normal(0, 0.1))) for c in conds} for a in arms}
                _dump(sc, os.path.join(d, f"condition_scores{suf}.json"))
                _dump({c: {"n_cells": 3, "lab": {LABS[c]: 3}, "stage": {"1": 3}} for c in conds}, os.path.join(d, f"condition_meta{suf}.json"))
                by_k[kl] = {a: dict(primary_pp=float(np.mean(list(sc[a].values()))), primary_pp_per_seed=float(np.mean(list(sc[a].values()))) + 0.01, seed_sd_of_mean=0.05 + 0.01 * f,
                                    n_conditions=len(conds), n_params=100 * (1 + f), n_train_used=m + f, fit_seconds_one_fit=2.0 + f, fit_seconds_ensemble=10.0 + 5 * f) for a in arms}
            _dump({"k_labels": ["0", "2", "full"], "k_primary": "full", "k_full": 4, "outer_test": by_k["full"], "outer_test_by_k": by_k}, os.path.join(d, "metrics.json"))
            _dump({"R_LOO": 0.5 + 0.01 * f, "R_WARP": 0.6 + 0.01 * f, "n_conditions": len(conds)}, os.path.join(d, "reference_values.json"))
            if m == 32 and with_extras:
                _dump(_stress_functions(rng, bad_soc=bad_soc if f == 0 else None), os.path.join(d, "stress_functions.json"))
                _dump({"points_T_SOCpct": [[T, s] for T in T_GRID for s in (20.0, 50.0, 80.0)]}, os.path.join(d, "storage_hull.json"))
                _dump(_law_forms(rng, f, lhs), os.path.join(d, "extracted_law_forms.json"))
                ids = [f"cell{f}_{i}" for i in range(2 * len(conds))]
                np.savez(os.path.join(d, "residual_cells.npz"), cell_id=np.array(ids), cond=np.array([c for c in conds for _ in (0, 1)]), T=np.where(np.arange(len(ids)) % 2, 45.0, 23.0),
                         soc_mid=rng.uniform(20, 90, len(ids)), c_ch=rng.uniform(0.1, 1.1, len(ids)), absR=np.abs(rng.normal(0.1, 0.05, (len(ids), 5, 6))))
                np.savez(os.path.join(d, "residual_map.npz"), train_T_SOC=np.array([[23.0, 50.0], [45.0, 60.0]]), train_cch_T=np.array([[0.5, 23.0], [0.7, 45.0]]))
            dirs.append(d)
    return dirs


def _item_f(tmp, dirs):
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


def make_negative(tmp, store_dirs, shift=0.25, noise=0.05, seed=5, drop_cond=False):
    """five permute_stress runs (A1 only) at g4: S_A1,permuted = S_A1,real * exp(shift + noise)"""
    rng = np.random.default_rng(seed)
    real = v4.Store.from_runs(store_dirs).scores("A1", *G4)
    out = []
    for f in range(5):
        d = os.path.join(tmp, f"nc2_f{f}")
        os.makedirs(d)
        conds = [c for c in CONDS if FOLD[c] == f]
        if drop_cond and f == 0:
            conds = conds[:-1]
        _dump({"m": 32, "fold": f, "design": "R2", "test": "B", "permute_stress": True, "arms": ["A1"]}, os.path.join(d, "config.json"))
        _dump({"A1": {c: float(real[c] * np.exp(shift + noise * rng.normal())) for c in conds}}, os.path.join(d, "condition_scores.json"))
        _dump({}, os.path.join(d, "metrics.json"))
        out.append(d)
    return out


@pytest.fixture(scope="module")
def grid(tmp_path_factory):
    tmp = str(tmp_path_factory.mktemp("gaps"))
    os.makedirs(tmp + "/g")
    dirs = make_grid(tmp + "/g")
    fdir, sha = _item_f(tmp, dirs)
    neg = make_negative(tmp, dirs)
    return dict(tmp=tmp, dirs=dirs, fdir=fdir, sha=sha, neg=neg)


@pytest.fixture(scope="module")
def runs_with_and_without(grid):
    tmp = grid["tmp"]
    kw = dict(item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], physval=True)
    base = ss.run_stats_v4(os.path.join(tmp, "an_base"), grid["dirs"], gaps=False, **kw)
    new = ss.run_stats_v4(os.path.join(tmp, "an_new"), grid["dirs"], negative_runs=grid["neg"], **kw)
    return dict(base=base, new=new, an_base=os.path.join(tmp, "an_base"), an_new=os.path.join(tmp, "an_new"))


def _canon(obj):
    return json.dumps(obj, sort_keys=True, default=str, indent=1)


# ------------------------------------------------------------------------------------------------ the no-regression rule
def strip_contrasts(o):
    """remove exactly the keys that stats_gaps adds to contrasts_v4_B.json"""
    o = copy.deepcopy(o)
    o["secondary"]["tests"]["QT_g1"].pop("median_interval", None)
    o.pop("candidates_vs_a1", None)
    o.pop("stats_gaps", None)
    st = o["status"]
    st.pop("strict", None)                                                                  # M-3: the output records its mode and the commit
    st.pop("head", None)
    st.pop("require_registered", None)                                                      # n-3
    st.pop("frozen", None)
    st.pop("registered_controls_failed_needs_rescore", None)                                # n-4: a record, no flag
    if st.pop("registered_controls_not_evaluated", None) is not None:                      # F1: a label; the other flags decide what the provisional flag was
        st["provisional"] = bool(st["rows_not_run"] or st["gate_not_evaluated"] or st.get("test_c_lab_indicator_row_not_run"))
        if "outcome" in o:
            o["outcome"]["provisional"] = st["provisional"]
    o["gate_G"]["reported_checks"] = {"PC-2_calendar_rate_monotone_in_T": None, "PC-3_A1_beats_persistence": None}          # F4
    return o


def strip_controls(c):
    """remove exactly the keys that stats_gaps adds to controls.json (negative.nc2, positive.P2 / P3 and their details) and restore the two reported checks to the value they had (None)"""
    c = copy.deepcopy(c)
    (c.get("negative") or {}).pop("nc2", None)
    for k in ("P2_monotone_in_T", "PC2_detail", "P3_passed", "PC3_detail", "P3_A1_beats_R1_median_L"):
        c["positive"].pop(k, None)
    c["gate_G"]["reported_checks"] = {"PC-2_calendar_rate_monotone_in_T": None, "PC-3_A1_beats_persistence": None}
    return c


def strip_physval(p):
    p = copy.deepcopy(p)
    for k in ("a_of_soc", "arrhenius_ln_rate", "partial_dependence_overlays"):
        p.pop(k, None)
    return p


def test_the_pre_existing_outputs_are_byte_identical_once_the_new_keys_are_stripped(runs_with_and_without):
    r = runs_with_and_without
    assert _canon(strip_contrasts(r["new"])) == _canon(strip_contrasts(r["base"]))
    for name, strip in (("contrasts_v4_B.json", strip_contrasts), ("controls.json", strip_controls), ("physval_11a.json", strip_physval)):
        a, b = json.load(open(os.path.join(r["an_base"], name))), json.load(open(os.path.join(r["an_new"], name)))
        assert _canon(strip(b)) == _canon(strip(a)), name                  # physval_11a.json: its new keys are produced by physval itself (G5), so the base run has them too
    assert os.path.exists(os.path.join(r["an_base"], "margins.json")) == os.path.exists(os.path.join(r["an_new"], "margins.json"))          # the fake grid has no margins_inputs.json: both say 'not available'
    assert r["base"]["margins_pp"] == r["new"]["margins_pp"]
    base_files = set(os.listdir(r["an_base"]))
    assert base_files <= set(os.listdir(r["an_new"])) and {"arm_table.json", "reference.json", "law_summary.json", "residual_map.npz"} <= set(os.listdir(r["an_new"])) - base_files


def test_the_gate_and_every_tier_state_title_count_and_margin_are_untouched(runs_with_and_without):
    b, n = runs_with_and_without["base"], runs_with_and_without["new"]
    for key in ("effective_tiers", "outcome", "primary", "secondary_tiers", "gate_G", "margins_pp", "status", "config_pin", "downgrade", "most_test", "dependence_sensitivity", "plain_descriptive", "estimated", "test_c", "s2"):
        if key in b:
            nk, bk = n[key], b[key]
            if key == "status":                                                          # F1: the label of a registered control that was not evaluated (base: no negative runs)
                nk, bk = {k: v for k, v in nk.items() if k != "registered_controls_not_evaluated"}, {k: v for k, v in bk.items() if k != "registered_controls_not_evaluated"}
            if key != "gate_G":
                assert _canon(nk) == _canon(bk), key
    ctl_b = json.load(open(os.path.join(runs_with_and_without["an_base"], "controls.json")))
    ctl_n = json.load(open(os.path.join(runs_with_and_without["an_new"], "controls.json")))
    for k in ("tripped", "reasons", "not_evaluated", "rule"):
        assert ctl_n["gate_G"][k] == ctl_b["gate_G"][k]
    assert ctl_n["negative"]["nc1"] == ctl_b["negative"]["nc1"] and ctl_n["positive"].get("P1_passed") == ctl_b["positive"].get("P1_passed")
    assert {k: v for k, v in n["gate_G"].items() if k != "reported_checks"} == {k: v for k, v in b["gate_G"].items() if k != "reported_checks"}          # F4: the gate rule and its fields are unchanged
    assert n["gate_G"]["reported_checks"] == ctl_n["gate_G"]["reported_checks"] and all(v is not None for v in ctl_n["gate_G"]["reported_checks"].values())
    assert n["gate_G"]["tripped"] is False and n["gate_G"]["not_evaluated"] == ["PC-1"]


def test_no_gap_reported_an_error_and_the_new_sentences_pass_the_wording_check(runs_with_and_without):
    r = runs_with_and_without
    st = r["new"]["stats_gaps"]["status"]
    assert not [k for k, v in st.items() if v.startswith("ERROR")], st
    assert not os.path.exists(os.path.join(r["an_new"], "STATS_GAPS_ERRORS.json"))
    for name in ("arm_table.json", "reference.json", "law_summary.json", "controls.json", "physval_11a.json", "contrasts_v4_B.json"):
        assert X.check_generated_sentences(json.load(open(os.path.join(r["an_new"], name))), name) is True


def test_gaps_off_writes_none_of_the_new_files(runs_with_and_without):
    base = os.listdir(runs_with_and_without["an_base"])
    assert not {"arm_table.json", "reference.json", "law_summary.json", "residual_map.npz"} & set(base)


# ------------------------------------------------------------------------------------------------ G1 arm_table
def test_g1_arm_table_pools_the_folds_by_condition_count(grid, runs_with_and_without):
    t = json.load(open(os.path.join(runs_with_and_without["an_new"], "arm_table.json")))
    assert set(t["cells"]) == {f"{m}|{k}" for m in (8, 16, 32) for k in ("0", "2", "full")}
    row = t["cells"]["32|full"]["A1"]
    mets = [json.load(open(os.path.join(d, "metrics.json")))["outer_test_by_k"]["full"]["A1"] for d in grid["dirs"] if d.endswith("_m32")]
    w = np.array([x["n_conditions"] for x in mets], float)
    w /= w.sum()
    assert row["mean_pp"] == pytest.approx(float(np.sum(w * [x["primary_pp"] for x in mets])))
    assert row["seed_sd_pp"] == pytest.approx(float(np.sqrt(np.sum((w * [x["seed_sd_of_mean"] for x in mets]) ** 2))))
    assert row["seed_sd_pp_upper_bound"] == pytest.approx(float(np.sum(w * [x["seed_sd_of_mean"] for x in mets]))) and row["seed_sd_pp_upper_bound"] >= row["seed_sd_pp"]
    assert row["n_conditions"] == 40 and row["n_folds"] == 5 and row["n_params"] == pytest.approx(300.0) and row["n_params_range"] == [100, 500] and row["n_train_used"] == pytest.approx(34.0)
    assert row["fit_seconds"] == pytest.approx(4.0) and set(row) >= {"mean_pp", "seed_sd_pp", "n_conditions", "n_params", "n_train_used", "fit_seconds"}
    assert "R1" not in t["cells"]["8|0"] and "R1" in t["cells"]["8|2"] and "A15" in t["cells"]["32|full"] and "A15" not in t["cells"]["32|2"]
    assert t["test_c"] == {} and t["s2"] == {}


def test_g1_test_c_and_s2_come_from_the_plain_outer_test_block(tmp_path):
    ds = []
    for i, (n, mean) in enumerate(((13, 3.0),)):
        d = tmp_path / f"c{i}"
        d.mkdir()
        _dump({"m": None, "fold": 0}, d / "config.json")
        _dump({"outer_test": {"A1": dict(primary_pp=mean, seed_sd_of_mean=0.1, n_conditions=n, n_params=10, n_train_used=27, fit_seconds_one_fit=3.0)}}, d / "metrics.json")
        ds.append(str(d))
    t = sg.arm_table([], ds, ds)
    assert t["test_c"]["A1"]["mean_pp"] == 3.0 and t["test_c"]["A1"]["n_conditions"] == 13 and t["s2"]["A1"]["seed_sd_pp"] == pytest.approx(0.1) and t["cells"] == {}


# ------------------------------------------------------------------------------------------------ G2 reference
def test_g2_reference_is_the_median_over_the_g4_runs_and_decides_nothing(runs_with_and_without):
    ref = json.load(open(os.path.join(runs_with_and_without["an_new"], "reference.json")))
    assert ref["values"]["B"] == {"R_LOO": pytest.approx(0.52), "R_WARP": pytest.approx(0.62), "n_folds": 5} and "decides nothing" not in json.dumps(ref) and "never a margin" in ref["definition"]


def test_g2_without_reference_values_nothing_is_written(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    _dump({"m": 32, "fold": 0}, d / "config.json")
    assert sg.reference_record([str(d)]) == {}


# ------------------------------------------------------------------------------------------------ G3 NC-2, PC-2, PC-3
def _two_stores(k_pos, n=40, ties=0):
    """real A1 = 2.0; permuted A1 = 2.0 exp(L) with k_pos positive, `ties` exact ties (L = 0, not positive) and the rest negative"""
    conds = CONDS[:n]
    L = np.array([0.3] * k_pos + [0.0] * ties + [-0.3] * (n - k_pos - ties))
    real = v4.Store({G4: {"A1": {c: 2.0 for c in conds}, "A9": {c: 2.2 for c in conds}}}, LABS, FOLD)
    neg = v4.Store({G4: {"A1": {c: 2.0 * float(np.exp(l)) for c, l in zip(conds, L)}}}, LABS, FOLD)
    return real, neg


def test_nc2_is_the_design_effect_sign_test_30_of_40_at_0p025():
    for k, passed in ((29, False), (30, True), (35, True)):
        r = sg.nc2_v4(*_two_stores(k), RULE)
        assert r["k_positive"] == k and r["n"] == 40 and r["crit_positives"] == 30 and r["passed"] is passed and r["alpha"] == 0.025 and r["gating"] is False
    r = sg.nc2_v4(*_two_stores(30), RULE)
    assert r["p_one_sided"] == pytest.approx(gt.betabin_p(30, 40, 0.03)) and r["plain_exact_descriptive"]["p"] == pytest.approx(gt.betabin_p(30, 40, 0.0))
    assert r["plain_exact_descriptive"]["positives"] == 30 and "sign test with a fixed design effect" in r["sign_rule"]


def test_nc2_ties_are_not_positive_and_n_is_not_reduced():
    r = sg.nc2_v4(*_two_stores(29, ties=3), RULE)
    assert r["k_positive"] == 29 and r["n"] == 40 and r["passed"] is False
    r = sg.nc2_v4(*_two_stores(30, ties=10), RULE)
    assert r["n"] == 40 and r["passed"] is True


def test_nc2_descriptive_rows_and_arms_not_run_under_permutation():
    r = sg.nc2_v4(*_two_stores(35), RULE)
    d = r["descriptive"]
    assert d["L_A9_over_A1_real"]["median"] == pytest.approx(np.log(2.2 / 2.0)) and d["L_A9_over_A1_permuted"] is None
    assert d["scores_mean_pp"]["permuted"]["A9"] is None and d["scores_mean_pp"]["real"]["A1"] == 2.0 and d["scores_mean_pp"]["permuted"]["A1"] > 2.0


def test_nc2_refuses_unpaired_conditions_and_other_folds():
    real, neg = _two_stores(35)
    neg.tables[G4]["A1"].pop(CONDS[0])
    with pytest.raises(ValueError, match="same held-out conditions"):
        sg.nc2_v4(real, neg, RULE)
    real, neg = _two_stores(35)
    real.notes["cell_folds"] = {G4: {0, 1, 2, 3, 4}}
    neg.notes["cell_folds"] = {G4: {0, 1, 2}}
    with pytest.raises(ValueError, match="outer folds"):
        sg.nc2_v4(real, neg, RULE)


def test_nc2_in_the_run_matches_the_hand_computed_test_and_a_wrong_run_is_recorded_not_fatal(grid, runs_with_and_without):
    ctl = json.load(open(os.path.join(runs_with_and_without["an_new"], "controls.json")))
    nc2 = ctl["negative"]["nc2"]
    real = v4.Store.from_runs(grid["dirs"]).scores("A1", *G4)
    perm = v4.Store.from_runs(grid["neg"]).scores("A1", *G4)
    L = np.array([np.log(perm[c] / real[c]) for c in sorted(real)])
    assert nc2["k_positive"] == int((L > 0).sum()) and nc2["n"] == 40 and nc2["passed"] is True and nc2["median_L"] == pytest.approx(float(np.median(L)))
    assert set(nc2) >= {"k_positive", "n", "passed", "median_L", "median_ci95", "crit_positives", "descriptive"}


def _bad_negative(grid, name):
    bad = make_negative(grid["tmp"] + "/" + name, grid["dirs"]) if os.makedirs(grid["tmp"] + "/" + name) is None else None
    cf = json.load(open(os.path.join(bad[1], "config.json")))
    cf["permute_stress"] = False
    _dump(cf, os.path.join(bad[1], "config.json"))
    return bad


def _boom(monkeypatch):
    """a code / compute error in NC-2 (not an input-integrity error)"""
    def raiser(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(sg, "nc2_v4", raiser)


def test_f1_a_registered_control_that_fails_to_compute_stops_a_strict_run_after_controls_json(grid, runs_with_and_without, monkeypatch):
    tmp = grid["tmp"]
    bad = grid["neg"]
    _boom(monkeypatch)
    with pytest.warns(UserWarning, match="G3_nc2"):
        with pytest.raises(ss.RegisteredControlError, match="NC-2"):
            ss.run_stats_v4(os.path.join(tmp, "an_bad"), grid["dirs"], item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=bad)
    ctl = json.load(open(os.path.join(tmp, "an_bad", "controls.json")))
    assert ctl["negative"]["nc2"]["passed"] is None and ctl["negative"]["nc2"]["status"].startswith("not evaluated: ERROR") and "boom" in json.load(open(os.path.join(tmp, "an_bad", "STATS_GAPS_ERRORS.json")))["G3_nc2"]
    assert not os.path.exists(os.path.join(tmp, "an_bad", "contrasts_v4_B.json"))
    assert ctl["gate_G"]["tripped"] is False                                              # the failure of an interpretive control is not a gate input


def test_f1_lenient_records_the_failure_and_marks_the_outcome_provisional(grid, monkeypatch):
    tmp = grid["tmp"]
    bad = grid["neg"]
    _boom(monkeypatch)
    with pytest.warns(UserWarning, match="G3_nc2"):
        out = ss.run_stats_v4(os.path.join(tmp, "an_bad_len"), grid["dirs"], item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=bad, strict=False)
    assert out["status"]["provisional"] is True and out["outcome"]["provisional"] is True and out["status"]["registered_controls_not_evaluated"]["NC-2"].startswith("ERROR")
    assert os.path.exists(os.path.join(tmp, "an_bad_len", "contrasts_v4_B.json"))


def test_f1_missing_inputs_mark_the_outcome_provisional_and_gaps_false_does_not_switch_the_controls_off(runs_with_and_without):
    base = runs_with_and_without["base"]                                                  # gaps=False, no negative runs
    ctl = json.load(open(os.path.join(runs_with_and_without["an_base"], "controls.json")))
    assert base["status"]["registered_controls_not_evaluated"] == {"NC-2": "no negative_runs given"} and base["status"]["provisional"] is True
    assert "nc2" not in ctl["negative"] and ctl["positive"]["P2_monotone_in_T"] is True and ctl["positive"]["P3_passed"] is True                  # PC-2, PC-3 still computed with gaps=False
    assert base["gate_G"]["reported_checks"] == ctl["gate_G"]["reported_checks"]


def test_f1_pc2_inputs_missing_in_a_fold_make_the_outcome_provisional_not_failed(grid):
    import shutil
    tmp = grid["tmp"] + "/pc2missing"
    os.makedirs(tmp)
    dirs = []
    for d in grid["dirs"]:
        t = os.path.join(tmp, os.path.basename(d))
        shutil.copytree(d, t)
        dirs.append(t)
    assert dirs[2].endswith("f0_m32")
    os.remove(os.path.join(dirs[2], "stress_functions.json"))
    if True:
        out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=grid["neg"], gaps=False)
    assert out["status"]["registered_controls_not_evaluated"]["PC-2"].startswith("not evaluated: stress_functions.json in 4 of 5 g4 runs") and out["outcome"]["provisional"] is True
    assert out["physval"]["status"] == "written" and out["physval"]["n_runs"] == 4
    ctl = json.load(open(os.path.join(tmp, "an", "controls.json")))
    assert ctl["positive"]["P2_monotone_in_T"] is None and ctl["gate_G"]["reported_checks"]["PC-2_calendar_rate_monotone_in_T"] is None and out["gate_G"]["reported_checks"] == ctl["gate_G"]["reported_checks"]


def test_f3_physval_is_on_by_default_for_r2_and_off_only_when_lenient(grid, runs_with_and_without):
    import inspect
    assert inspect.signature(ss.run_stats_v4).parameters["physval"].default is True and runs_with_and_without["new"]["physval"]["status"] == "written"
    with pytest.raises(ValueError, match="physval = False is refused"):
        ss.run_stats_v4(os.path.join(grid["tmp"], "an_nophys"), grid["dirs"], item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], physval=False)
    with pytest.raises(SystemExit):
        ss.main(["--analysis-dir", os.path.join(grid["tmp"], "an_cli"), "--runs", "B=" + ",".join(grid["dirs"]), "--no-physval", "--item-f-dir", grid["fdir"]])
    assert not os.path.exists(os.path.join(grid["tmp"], "an_cli"))
    out = ss.run_stats_v4(os.path.join(grid["tmp"], "an_nophys_len"), grid["dirs"], item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], physval=False, strict=False)
    assert "physval" not in out


def test_f4_contrasts_and_controls_carry_the_same_reported_checks(runs_with_and_without):
    r = runs_with_and_without
    ctl = json.load(open(os.path.join(r["an_new"], "controls.json")))
    con = json.load(open(os.path.join(r["an_new"], "contrasts_v4_B.json")))
    assert con["gate_G"]["reported_checks"] == ctl["gate_G"]["reported_checks"] == {"PC-2_calendar_rate_monotone_in_T": True, "PC-3_A1_beats_persistence": True}
    assert {k: v for k, v in con["gate_G"].items() if k != "reported_checks"} == {k: v for k, v in ctl["gate_G"].items() if k != "reported_checks"}


def test_f5_the_seed_sd_label_is_the_sd_of_single_seed_means(runs_with_and_without):
    t = json.load(open(os.path.join(runs_with_and_without["an_new"], "arm_table.json")))
    assert "single-seed pooled mean" in t["definition"] and "no seed replicate of its own" in t["definition"] and "SD over seeds of the pooled mean" not in t["definition"]


def test_pc3_is_the_m3_machinery_at_g4_with_margin_zero():
    st = make_store()
    for cell in (G4,):
        st.tables[cell]["R1"] = {c: 2.0 * np.exp(0.2 if i < 30 else -0.2) for i, c in enumerate(CONDS)}
    r = sg.pc3_v4(st, RULE)
    assert r["passed"] is True and r["positives"] == 30 and r["n"] == 40 and r["crit_positives"] == 30 and r["gating"] is False
    st.tables[G4]["R1"] = {c: 2.0 * np.exp(0.2 if i < 29 else -0.2) for i, c in enumerate(CONDS)}
    assert sg.pc3_v4(st, RULE)["passed"] is False
    st.tables[G4]["R1"] = {c: 2.0 for c in CONDS}                                       # all ties: none positive, n not reduced
    r = sg.pc3_v4(st, RULE)
    assert r["passed"] is False and r["positives"] == 0 and r["n"] == 40
    assert sg.pc3_v4(make_store(), RULE)["passed"] is None and sg.pc3_v4(make_store(), RULE)["status"].startswith("not evaluated")       # no R1 at g4


def _sf_dir(tmp, name, rate, hull_pts=None):
    d = os.path.join(tmp, name)
    os.makedirs(d)
    rate = np.asarray(rate, float)
    _dump({"m": 32, "fold": 0}, os.path.join(d, "config.json"))
    sf = {"calendar": {"soc": SOC}, "storage_rate": {"T_C": T_GRID, "soc": SOC, "mean": rate.mean(0).tolist()}, "members": {"E_kJmol": np.zeros((rate.shape[0], len(SOC))).tolist(), "a_pp500": np.zeros((rate.shape[0], len(SOC))).tolist(),
                                                                                                                       "storage_rate": rate.tolist()}, "cyclic": {}}
    _dump(sf, os.path.join(d, "stress_functions.json"))
    if hull_pts is not None:
        _dump({"points_T_SOCpct": hull_pts}, os.path.join(d, "storage_hull.json"))
    return d


def _rate(n=3, f=lambda T, s: 1.0 + 0.02 * s + (T / 10.0) ** 2):
    return np.array([[[f(T, s) for s in SOC] for T in T_GRID] for _ in range(n)])


def test_pc2_monotone_in_temperature_inside_the_storage_hull_only(tmp_path):
    hull = [[T, s] for T in T_GRID for s in (20.0, 80.0)]
    ok = sg.pc2_v4([_sf_dir(str(tmp_path), "ok", _rate(), hull)])
    assert ok["passed"] is True and ok["soc_evaluated"] == [float(s) for s in SOC if 20 <= s <= 80] and ok["soc_excluded_outside_hull"][:2] == [0.0, 5.0] and ok["hull"] == "convex hull" and ok["gating"] is False
    r = _rate()
    r[1, 2, SOC.index(5.0)] = 0.1                                                      # one member non-monotone at SOC 5 %: outside the hull, not evaluated
    assert sg.pc2_v4([_sf_dir(str(tmp_path), "outside", r, hull)])["passed"] is True
    r[1, 2, SOC.index(50.0)] = 0.1                                                     # ... and at SOC 50 %: inside the hull, every member must pass
    bad = sg.pc2_v4([_sf_dir(str(tmp_path), "inside", r, hull)])
    assert bad["passed"] is False and bad["members_failing"] == 1 and bad["first_violations"][0] == {"member": 1, "soc": 50.0}
    flat = _rate(f=lambda T, s: 1.0 + 0.02 * s)                                         # equal rates at the three temperatures: strictly increasing fails
    assert sg.pc2_v4([_sf_dir(str(tmp_path), "flat", flat, hull)])["passed"] is False
    nohull = sg.pc2_v4([_sf_dir(str(tmp_path), "nohull", _rate())])                     # F2a: no substitute rule
    assert nohull["passed"] is None and "storage_hull.json missing" in nohull["status"]
    assert sg.pc2_v4([])["passed"] is None


def test_m2_pc2_collinear_storage_points_have_no_hull_and_no_bounding_box_substitute(tmp_path):
    """red team m-2: points that do not span the plane raise (a failure to compute); there is no bounding-box fallback"""
    with pytest.raises(ValueError, match="storage points do not span"):
        sg.pc2_v4([_sf_dir(str(tmp_path), "line", _rate(), [[10.0, 50.0], [23.0, 50.0], [45.0, 50.0]])])
    with pytest.raises(ValueError, match="storage points do not span"):
        sg._inside_hull([[10.0, 20.0], [23.0, 20.0]], (23.0, 20.0))


def test_m3_the_pc2_grid_of_t1_is_asserted(tmp_path):
    """red team m-3: T = 10, 23, 45 C and SOC = 0, 5, ..., 100 % (PREREG_v4 10, T1)"""
    hull = [[T, s_] for T in T_GRID for s_ in (20.0, 80.0)]
    d = _sf_dir(str(tmp_path), "grid", _rate(), hull)
    sf = json.load(open(os.path.join(d, "stress_functions.json")))
    sf["storage_rate"]["T_C"] = [10, 23, 50]
    _dump(sf, os.path.join(d, "stress_functions.json"))
    with pytest.raises(ValueError, match="grid differs from PREREG_v4 10"):
        sg.pc2_v4([d])
    assert sg.PC2_T_GRID == [10.0, 23.0, 45.0] and sg.PC2_SOC_GRID == [float(x) for x in range(0, 101, 5)]


def test_the_reported_checks_never_trip_or_clear_the_gate():
    ctl = {"negative": {"nc1": {"runs_checked": 5, "passed": True}}, "positive": {"P1_G0_nrmse_leq_0p15": True}}
    ctl["gate_G"] = ss.gate_g(ctl)
    assert ctl["gate_G"]["tripped"] is False and ctl["gate_G"]["not_evaluated"] == []
    out = sg.extend_controls(ctl, {"passed": False, "k_positive": 5, "n": 40}, {"passed": False}, {"passed": False})
    assert out["gate_G"]["tripped"] is False and out["gate_G"]["reasons"] == [] and out["gate_G"]["not_evaluated"] == []
    assert out["gate_G"]["reported_checks"] == {"PC-2_calendar_rate_monotone_in_T": False, "PC-3_A1_beats_persistence": False} and out["negative"]["nc2"]["passed"] is False
    assert ctl["gate_G"]["reported_checks"] == {"PC-2_calendar_rate_monotone_in_T": None, "PC-3_A1_beats_persistence": None} and "nc2" not in ctl["negative"]       # the input is not mutated
    tripped = {"negative": {"nc1": {"runs_checked": 5, "passed": False}}, "positive": {"P1_G0_nrmse_leq_0p15": True}}
    tripped["gate_G"] = ss.gate_g(tripped)
    assert sg.extend_controls(tripped, None, {"passed": True}, {"passed": True})["gate_G"]["tripped"] is True


# ------------------------------------------------------------------------------------------------ G7 Q-T, G8 candidates
def test_g7_qt_interval_is_the_unadjusted_fallback_interval_of_the_secondary_family():
    st = make_store(A13g1=0.12)
    e = sg.qt_interval(st, RULE)
    _, L, _ = st.L("A1", "A13", G1)
    lo, hi, r, cov = RULE.interval(L, 0.05)
    assert e["median_ci"] == [lo, hi] and e["median_L"] == pytest.approx(0.12) and e["n"] == 40 and e["rel_reduction_pct"] == pytest.approx(v4.pct_reduction(0.12)) and "mean_pp_ci" in e
    assert v4._stat(v4.PRIMARY_SOURCE, st, RULE, "A1", "A13", G1, "QT_g1")[1:3] == (lo, hi)                    # the numbers the qualifier sentence of Q-T prints
    assert sg.qt_interval(make_store(), RULE)["median_L"] == 0.0
    s2 = make_store()
    del s2.tables[G1]["A13"]
    assert sg.qt_interval(s2, RULE) is None


def test_g7_the_interval_sits_beside_the_secondary_test_and_changes_nothing(runs_with_and_without):
    new, base = runs_with_and_without["new"], runs_with_and_without["base"]
    qt = new["secondary"]["tests"]["QT_g1"]
    assert "median_interval" in qt and qt["tier"] == base["secondary"]["tests"]["QT_g1"]["tier"] and qt["pN"] == base["secondary"]["tests"]["QT_g1"]["pN"] and qt["median_interval"]["interval_type"].startswith("unadjusted")
    assert _canon(new["qualifier_sentences"]) == _canon(base["qualifier_sentences"])


def test_g8_candidates_are_descriptive_rows_at_g4_outside_every_family(grid, runs_with_and_without):
    c = json.load(open(os.path.join(runs_with_and_without["an_new"], "contrasts_v4_B.json")))["candidates_vs_a1"]
    assert set(c["rows"]) == {"A11", "A12", "A4", "A5"} and c["cell"] == [32, "full"] and c["not_scored_at_this_cell"] == [] and "outside every family" in c["label"]
    st = v4.Store.from_runs(grid["dirs"])
    e = v4.entry(st, "A1 vs A11", "A1", "A11", G4, RULE)
    assert c["rows"]["A11"] == json.loads(json.dumps(e, default=str)) and c["rows"]["A11"]["n"] == 40
    assert not any(k in c["rows"]["A11"] for k in ("tier", "p", "rejected", "level"))
    st2 = make_store()
    assert sg.candidates_vs_a1(st2, RULE)["rows"] == {} and sg.candidates_vs_a1(st2, RULE)["not_scored_at_this_cell"] == ["A11", "A12", "A4", "A5"]


# ------------------------------------------------------------------------------------------------ G4 laws
def test_g4_stability_metric_known_cases():
    rs = np.random.default_rng(0)
    lhs = rs.uniform(-1, 1, (200, 5))
    hulls = {f: rs.uniform(-0.9, 0.9, (60, 5)) for f in range(5)}
    base = lhs @ np.array([1.0, 0.5, 0.0, -0.5, 0.2])
    same = [dict(fold=f, seed=s, log_rate=base) for f in range(5) for s in range(2)]
    r = sg.stability_metric(same, hulls, lhs)
    assert r["status"] == "evaluated" and r["median_sd_over_range"] == pytest.approx(0.0, abs=1e-12) and 0 < r["n_points_inside"] < 200
    off = [dict(fold=f, seed=s, log_rate=base + (f - 2) * 0.1) for f in range(5) for s in range(2)]            # fold offsets -0.2 .. 0.2 (SD of five values with ddof 1 = 0.1581..)
    r = sg.stability_metric(off, hulls, lhs)
    inside = np.ones(200, bool)
    for f in range(5):
        inside &= sg._hull_mask(hulls[f], lhs)[0]
    assert r["median_sd"] == pytest.approx(float(np.std([-0.2, -0.1, 0.0, 0.1, 0.2], ddof=1))) and r["range_log_rate"] == pytest.approx(float(np.ptp(base[inside])))
    assert r["median_sd_over_range"] == pytest.approx(r["median_sd"] / r["range_log_rate"]) and r["n_points_inside"] == int(inside.sum())
    far = {f: rs.uniform(5, 6, (60, 5)) for f in range(5)}
    assert sg.stability_metric(same, far, lhs)["status"].startswith("not available") and sg.stability_metric(same[:2], hulls, lhs)["status"].startswith("not available")


def test_g4_law_summary_from_the_run_files(grid, runs_with_and_without):
    ls = json.load(open(os.path.join(runs_with_and_without["an_new"], "law_summary.json")))
    assert set(ls["arms"]) == {"A15", "G15"} and ls["label"] == X.load_thresholds()["wording"]["stability_table_caption"] and ls["contribution"] is False
    a = ls["arms"]["A15"]
    assert a["n_laws"] == 25 and a["complete"] and a["n_coefs"] == {"median": 14.0, "min": 12.0, "max": 16.0} and a["train_bic"]["min"] == 100.0 and a["train_bic"]["max"] == 144.0
    assert a["stability"]["status"] == "evaluated" and a["stability"]["median_sd_over_range"] > 0 and a["stability"]["n_folds"] == 5
    assert a["representative"]["rule"].startswith("the law with the median training-side BIC") and a["representative"]["train_bic"] == sorted(l["train_bic"] for l in a["closed_forms"])[12]
    assert set(a["partial_dependence"]) == {"soc_mid", "dod", "c_ch", "c_dch"} and len(a["closed_forms"]) == 25 and "T_C" not in a["partial_dependence"] and "T" not in a["partial_dependence"]
    assert ls["temperature"]["display"] == "temperature (aliased with laboratory; no form or sign reported)" and "temperature and laboratory cannot be separated" in ls["temperature"]["note"]
    assert "consistent" not in json.dumps(ls) and "licen" not in json.dumps(ls)


def test_g4_missing_files_say_not_available_and_mismatched_hypercubes_raise(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    _dump({"m": 32, "fold": 0}, d / "config.json")
    assert sg.law_summary([str(d)])["status"].startswith("not available")
    lhs = emit.lhs_points(30)
    for f in (0, 1):
        dd = tmp_path / f"f{f}"
        dd.mkdir()
        _dump({"m": 32, "fold": f}, dd / "config.json")
        _dump(_law_forms(np.random.default_rng(f), f, lhs + (0.1 if f else 0.0)), dd / "extracted_law_forms.json")
    with pytest.raises(ValueError, match="different Latin hypercubes"):
        sg.law_summary([str(tmp_path / "f0"), str(tmp_path / "f1")])


def test_g4_run_writer_helpers_lhs_is_fixed_local_and_laws_carry_no_temperature_curve():
    st = np.random.get_state()[1].copy()
    a, b = emit.lhs_points(), emit.lhs_points()
    assert a.shape == (500, 5) and np.array_equal(a, b) and a.min() >= -1 and a.max() < 1 and np.array_equal(np.random.get_state()[1], st)         # no global RNG touched
    assert all(len(np.unique(np.floor((a[:, j] + 1) / 2 * 500))) == 500 for j in range(5))                                                             # a Latin hypercube
    import torch
    from pinnkan import specs, symbolic as S
    spec = specs.SAMSUNG
    geos = S.stress_geos(spec, np.random.default_rng(0).uniform(-0.5, 0.5, (20, 5)))
    rows = [[S.SymEdge("linear", [0.5 + i, 0.1], g) for i, g in enumerate(geos)]]
    layer = S.SymLayer(rows)
    law = types.SimpleNamespace(cyc=S.SymbolicMap(S.SymbolicStack([layer])), cal=None)
    arm = types.SimpleNamespace(model=types.SimpleNamespace(law=law), n_coefs=10, n_params=123, train_bic=77.5)
    cells = [types.SimpleNamespace(kind="cycling", raw=np.array([23.0, 0.5, 0.3, 0.7, 1.0])), types.SimpleNamespace(kind="cycling", raw=np.array([45.0, 0.6, 0.4, 0.4, 1.5]))]
    rec = emit.law_extras("A15h1", 2, 3, arm, spec, cells)
    assert rec["arm"] == "A15h1" and rec["fold"] == 2 and rec["seed"] == 3 and rec["n_coefs"] == 10 and rec["train_bic"] == 77.5 and len(rec["log_rate_on_lhs"]) == 500
    assert set(rec["pd"]) == {"soc_mid", "dod", "c_ch", "c_dch"} and rec["cyclic"][0]["edges"][0][0] == {"display": "temperature (aliased with laboratory; no form or sign reported)"}
    assert rec["cyclic"][0]["edges"][0][1]["family"] == "linear" and rec["cyclic"][0]["edges"][0][1]["theta"] == pytest.approx([1.5, 0.1])
    assert rec["closed_form"][0] == "cyclic layer 0 edge 0<-0: temperature (aliased with laboratory; no form or sign reported)" and "0.5" not in rec["closed_form"][0]
    expect = law.cyc(torch.tensor(emit.lhs_points(), dtype=torch.float32)).detach().numpy()
    assert np.allclose(rec["log_rate_on_lhs"], expect, atol=1e-6)
    hd = emit.law_forms_header(spec, np.zeros((3, 5)))
    assert len(hd["lhs"]["points"]) == 500 and "T" not in hd["pd_grid"] and hd["train_hull_points"] == np.zeros((3, 5)).tolist()


def test_g4_the_run_writer_calls_the_new_emitters_inside_their_own_guards():
    src = open(os.path.join(ROOT, "code", "pinnkan", "run.py"), encoding="utf8").read()
    assert "emit.law_extras(akey, cfg[\"fold\"], sd_, arm, spec, train)" in src and "extracted_law_forms.json" in src and "_emit_gap_inputs(run_dir, rec, spec, train, prep, fitted)" in src
    i = src.index("def _emit_gap_inputs")
    body = src[i:i + 1500]
    assert body.count("try:") == 2 and "residual_cells.npz" in body and "storage_hull.json" in body and src.index("law_forms.append") < src.index("except Exception as e_:  # noqa: BLE001  (a secondary artefact")


# ------------------------------------------------------------------------------------------------ G5 physval
def test_g5_physval_carries_a_of_soc_arrhenius_lines_and_overlays_but_no_temperature_curve(runs_with_and_without, grid, monkeypatch):
    pv = json.load(open(os.path.join(runs_with_and_without["an_new"], "physval_11a.json")))
    assert len(pv["a_of_soc"]["soc"]) == 21 and set(pv["a_of_soc"]["a_pp500"]) == {"mean", "median", "lo", "hi"} and pv["a_of_soc"]["n_members"] == 15
    ar = pv["arrhenius_ln_rate"]
    assert ar["T_C"] == T_GRID and ar["inv_T_1000_per_K"] == pytest.approx([1000 / (t + 273.15) for t in T_GRID]) and ar["soc_selected"] == [5, 50, 80, 100] and ar["n_members"] == 15
    assert len(ar["ln_rate"]["mean"]) == 4 and len(ar["ln_rate"]["mean"][0]) == 3 and ar["share_members_increasing_in_T"] == [1.0] * 4
    ov = pv["partial_dependence_overlays"]["per_input"]
    assert ov["T"] == {"display": "temperature (aliased with laboratory; no form or sign reported)"} and set(ov) == {"T", "soc_mid", "dod", "c_ch", "c_dch"}
    assert ov["c_ch"]["A4_mean"] is not None and ov["c_ch"]["A10_mean"] is not None and len(ov["c_ch"]["x"]) == 49 and set(ov["c_ch"]["A1"]) == {"mean", "median", "lo", "hi"}
    assert "figure_inputs_error" not in pv
    dirs = [d for d in grid["dirs"] if d.endswith("_m32")]
    monkeypatch.setitem(semi.A10_FORM, "verified", False)
    pv2 = physval.physval_11a(dirs)
    assert pv2["partial_dependence_overlays"]["per_input"]["c_ch"]["A10_mean"] is None and "blocked_A10" in pv2["partial_dependence_overlays"]["per_input"]
    with pytest.raises(semi.UnverifiedArmError):
        physval.physval_11a(dirs, strict=True)


# ------------------------------------------------------------------------------------------------ G6 residual map
def test_g6_merged_map_pools_raw_values_not_fold_medians(tmp_path):
    def run(name, fold, ids, T, soc, cch, vals):
        d = tmp_path / name
        d.mkdir()
        _dump({"m": 32, "fold": fold}, d / "config.json")
        a = np.array(vals, float).reshape(len(ids), 1, -1)
        np.savez(d / "residual_cells.npz", cell_id=np.array(ids), cond=np.array(ids), T=np.array(T, float), soc_mid=np.array(soc, float), c_ch=np.array(cch, float), absR=a)
        np.savez(d / "residual_map.npz", train_T_SOC=np.array([[23.0, 50.0]]), train_cch_T=np.array([[0.5, 23.0]]))
        return str(d)
    # bin (T 16-28, SOC 20-40): fold 0 has values 1, 1, 1 (one cell), fold 1 has 10, 10 (two cells, one value each) -> pooled median over the five raw values = 1, median of the fold medians = 5.5
    f0 = run("f0", 0, ["a"], [20.0], [30.0], [0.1], [[1.0, 1.0, 1.0]])
    f1 = run("f1", 1, ["b", "c"], [20.0, 20.0], [30.0, 30.0], [0.1, 0.1], [[10.0], [10.0]])
    r = sg.merge_residual_cells([f0, f1])
    ix, iy = 1, 1
    assert r["T_edges"][iy] == 16.25 and r["soc_edges"][ix] == 20.0
    assert r["absR_T_SOC"][iy, ix] == 1.0 and r["n_cells_T_SOC"][iy, ix] == 3 and int(r["n_cells"]) == 3 and np.isnan(r["absR_T_SOC"][0, 0])
    assert r["absR_T_SOC"][iy, ix] != np.median([np.median([1.0, 1.0, 1.0]), np.median([10.0, 10.0])])
    assert r["train_T_SOC"].tolist() == [[23.0, 50.0]] and set(r) >= {"T_edges", "soc_edges", "cch_edges", "absR_T_SOC", "absR_cch_T", "train_T_SOC", "train_cch_T"}
    dup = run("f2", 2, ["a"], [20.0], [30.0], [0.1], [[1.0]])
    with pytest.raises(ValueError, match="more than one outer-fold run"):
        sg.merge_residual_cells([f0, dup])
    assert sg.merge_residual_cells([]) is None


def test_g6_the_merged_map_in_the_run_pools_every_scored_cell_once(grid, runs_with_and_without):
    z = np.load(os.path.join(runs_with_and_without["an_new"], "residual_map.npz"))
    assert int(z["n_cells"]) == 80 and int(z["n_cells_T_SOC"].sum()) + int(z["n_outside_T_SOC"]) == 80 and z["absR_T_SOC"].shape == (4, 5) and z["absR_cch_T"].shape == (4, 4)
    allv = np.concatenate([np.load(os.path.join(d, "residual_cells.npz"))["absR"].reshape(16, -1) for d in grid["dirs"] if d.endswith("_m32")])
    assert np.nanmin(z["absR_T_SOC"]) >= allv.min() and np.nanmax(z["absR_T_SOC"]) <= allv.max()


def test_g6_residual_cells_emitter_evaluates_every_member_at_the_scored_cells():
    import torch

    class Model:
        col_t_max = 2.0
        zdim = 1

        class law:
            @staticmethod
            def r_cal(s):
                return s[:, 0] * 0 + 1.0

            @staticmethod
            def r_cyc(s):
                return s[:, 1] * 0 + 2.0

        def residual(self, tn, s, z, a_cal, a_cyc, nu):
            return -(tn * (a_cal + a_cyc) + nu)
    from pinnkan import specs
    members = [types.SimpleNamespace(model=Model()) for _ in range(3)]
    prep = [types.SimpleNamespace(cell=types.SimpleNamespace(cell_id=f"c{i}", cond=f"k{i}", kind="cycling", raw=np.array([23.0 + 10 * i, 0.5, 0.3, 0.6, 1.0]))) for i in range(2)]
    prep.append(types.SimpleNamespace(cell=types.SimpleNamespace(cell_id="s", cond="s", kind="storage", raw=np.array([23.0, 0.5, 0.0, 0.0, 0.0]))))
    rc = emit.residual_cells(members, specs.SAMSUNG, prep)
    assert rc["absR"].shape == (2, 3, 6) and rc["cell_id"].tolist() == ["c0", "c1"] and rc["T"].tolist() == [23.0, 33.0] and rc["soc_mid"].tolist() == [50.0, 50.0] and rc["c_ch"].tolist() == [0.6, 0.6]
    assert (rc["absR"] > 0).all() and emit.residual_cells(members, specs.SAMSUNG, prep[2:]) is None
    h = emit.storage_hull([c.cell for c in prep])
    assert h["points_T_SOCpct"] == [[23.0, 50.0]]


# ------------------------------------------------------------------------------------------------ the real run writer on a synthetic dataset (A1, A15, G15)
def test_the_real_run_writer_emits_the_new_inputs_and_the_statistics_step_reads_them(tmp_path):
    import torch
    torch.set_num_threads(1)
    from pinnkan import run
    cfg = {"design": "V3_legacy", "dataset": "synthetic", "mode": "confirmatory", "n_trials": 1, "inner_k": 2, "steps_scale": 0.04, "seeds": [0, 1], "backbone": "self_limiting",
           "arms": ["A1", "A15", "G15"], "synthetic": {"kind": "G2", "n_cyc_cond": 16, "n_sto_cond": 8, "reps": 2, "seed": 7}, "run_id": "L", "test": "B"}
    run.run(cfg, runs_dir=str(tmp_path))
    d = tmp_path / "L"
    assert not [p.name for p in d.iterdir() if p.name.startswith("emit_errors")], [p.name for p in d.iterdir()]
    f = json.load(open(d / "extracted_law_forms.json"))
    assert len(f["laws"]) == 4 and {l["arm"] for l in f["laws"]} == {"G15"} | {l["arm"] for l in f["laws"] if l["arm"].startswith("A15h")} and len(f["lhs"]["points"]) == 500
    assert np.allclose(f["lhs"]["points"], emit.lhs_points()) and np.asarray(f["train_hull_points"]).shape[1] == 5
    for l in f["laws"]:
        assert l["n_coefs"] > 0 and np.isfinite(l["train_bic"]) and len(l["log_rate_on_lhs"]) == 500 and set(l["pd"]) == {"soc_mid", "dod", "c_ch", "c_dch"}
        assert "temperature (aliased" in l["closed_form"][0] and l["cyclic"][0]["edges"][0][0] == {"display": "temperature (aliased with laboratory; no form or sign reported)"}
    rc = np.load(d / "residual_cells.npz")
    wp = len(set(pd_cell for pd_cell in rc["cell_id"]))
    assert rc["absR"].shape == (len(rc["cell_id"]), 2, 6) and wp == len(rc["cell_id"]) and np.isfinite(rc["absR"]).all()
    sh = json.load(open(d / "storage_hull.json"))
    assert len(sh["points_T_SOCpct"]) > 0
    ls = sg.law_summary([str(d)])
    assert set(ls["arms"]) == {"A15", "G15"} and ls["arms"]["G15"]["n_laws"] == 2 and ls["arms"]["A15"]["stability"]["status"].startswith("not available")           # one outer fold only
    assert sg.merge_residual_cells([str(d)]) is not None
    X.check_generated_sentences(ls, "law_summary")


# ------------------------------------------------------------------------------------------------ the defects found by the statistician (F2a, F2b)
def test_f2b_pc3_with_one_missing_r1_condition_is_not_evaluated_and_n_is_not_reduced():
    st = make_store()
    st.tables[G4]["R1"] = {c: 2.0 * np.exp(0.3) for c in CONDS[:39]}                      # R1 scores 39 of the 40 g4 conditions
    r = sg.pc3_v4(st, RULE)
    assert r["passed"] is None and r["status"].startswith("not evaluated: R1 scores 39 and A1 40 conditions at g4") and "n" not in r
    st.tables[G4]["R1"] = {c: 2.0 * np.exp(0.3) for c in CONDS}
    assert sg.pc3_v4(st, RULE)["passed"] is True and sg.pc3_v4(st, RULE)["n"] == 40


def test_f2a_pc2_does_not_drop_a_fold_or_fall_back_to_the_whole_grid(tmp_path):
    hull = [[T, s] for T in T_GRID for s in (20.0, 80.0)]
    ok = [_sf_dir(str(tmp_path), f"f{i}", _rate(), hull) for i in range(5)]
    r = sg.pc2_v4(ok)
    assert r["passed"] is True and r["n_folds"] == 5
    os.remove(os.path.join(ok[3], "stress_functions.json"))                                # one fold has no stress functions: not 'judged on 4 folds'
    r = sg.pc2_v4(ok)
    assert r["passed"] is None and r["status"] == "not evaluated: stress_functions.json in 4 of 5 g4 runs"
    ok2 = [_sf_dir(str(tmp_path), f"g{i}", _rate(), hull) for i in range(5)]
    os.remove(os.path.join(ok2[1], "storage_hull.json"))                                   # one fold has no storage hull: no substitute rule
    r = sg.pc2_v4(ok2)
    assert r["passed"] is None and "storage_hull.json missing" in r["status"]
    nohull = [_sf_dir(str(tmp_path), f"h{i}", _rate()) for i in range(5)]                  # no hull anywhere: not the whole SOC grid
    assert sg.pc2_v4(nohull)["passed"] is None and "storage_hull.json missing" in sg.pc2_v4(nohull)["status"]
    empty = [_sf_dir(str(tmp_path), f"e{i}", _rate(), []) for i in range(2)]
    assert sg.pc2_v4(empty)["passed"] is None and "no storage point" in sg.pc2_v4(empty)["status"]


# ------------------------------------------------------------------------------------------------ red team rev. 20: M-1, M-2, M-3, m-2, m-3, m-4
def test_m2_require_makes_every_absence_but_the_data_reason_a_failure_to_compute(tmp_path):
    hull = [[T, s_] for T in T_GRID for s_ in (20.0, 80.0)]
    ok = [_sf_dir(str(tmp_path), f"ok{i}", _rate(), hull) for i in range(2)]
    assert sg.pc2_v4(ok, require=True)["passed"] is True
    os.remove(os.path.join(ok[1], "storage_hull.json"))
    with pytest.raises(ValueError, match="storage_hull.json missing"):
        sg.pc2_v4(ok, require=True)
    os.remove(os.path.join(ok[1], "stress_functions.json"))
    with pytest.raises(ValueError, match="stress_functions.json in 1 of 2 g4 runs"):
        sg.pc2_v4(ok, require=True)
    assert sg.pc2_v4(ok)["passed"] is None                                              # development default: a label
    st = make_store()
    st.tables[G4]["R1"] = {c: 2.0 * np.exp(0.3) for c in CONDS[:39]}
    with pytest.raises(ValueError, match="R1 scores 39 and A1 40"):
        sg.pc3_v4(st, RULE, require=True)
    with pytest.raises(ValueError, match="R1 or A1 is not scored at g4"):
        sg.pc3_v4(make_store(), RULE, require=True)
    # the data reason stays 'not evaluated' even when required: only one temperature inside the hull at every SOC
    one_t = [_sf_dir(str(tmp_path), "onet", _rate(), [[10.0, 20.0], [10.0, 80.0], [11.0, 50.0]])]
    r = sg.pc2_v4(one_t, require=True)
    assert r["passed"] is None and r["status"].startswith("not evaluated: no SOC level has two temperatures")


def test_m2_a_strict_confirmatory_run_without_negative_runs_or_with_a_missing_pc2_input_stops(grid):
    tmp = grid["tmp"]
    with pytest.warns(UserWarning, match="G3_nc2"):
        with pytest.raises(ss.RegisteredControlError, match="NC-2"):
            ss.run_stats_v4(os.path.join(tmp, "an_nonc2"), grid["dirs"], item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], require_registered=True)
    ctl = json.load(open(os.path.join(tmp, "an_nonc2", "controls.json")))
    assert ctl["negative"]["nc2"]["status"].startswith("not evaluated: ERROR no negative_runs given") and not os.path.exists(os.path.join(tmp, "an_nonc2", "contrasts_v4_B.json"))
    # the same input absent in lenient / development mode stays a provisional label
    out = ss.run_stats_v4(os.path.join(tmp, "an_nonc2_dev"), grid["dirs"], item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], gaps=False)
    assert out["status"]["registered_controls_not_evaluated"]["NC-2"] == "no negative_runs given"


def test_m3_the_stop_keeps_the_stopped_record_with_its_sha256_and_the_output_records_mode_and_head(grid, runs_with_and_without, monkeypatch):
    import hashlib
    st = runs_with_and_without["new"]["status"]
    assert st["strict"] is True and "head" in st and (st["head"] is None or len(st["head"]) == 40)
    tmp = grid["tmp"]
    bad = grid["neg"]
    _boom(monkeypatch)
    for k in (1, 2):                                                                          # a second stop does not overwrite the first record
        with pytest.warns(UserWarning):
            with pytest.raises(ss.RegisteredControlError, match="stopped_record"):
                ss.run_stats_v4(os.path.join(tmp, "an_stop"), grid["dirs"], item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=bad)
        d = os.path.join(tmp, "an_stop", f"stopped_{k}")
        sha = json.load(open(os.path.join(d, "SHA256.json")))
        assert set(sha) == {"controls.json", "STATS_GAPS_ERRORS.json"}
        for name, h in sha.items():
            assert hashlib.sha256(open(os.path.join(d, name), "rb").read()).hexdigest() == h


def test_m3_lenient_is_refused_on_samsung_runs_after_frozen(tmp_path, monkeypatch):
    from pinnkan import guard
    d = tmp_path / "s"
    d.mkdir()
    _dump({"m": 32, "fold": 0, "dataset": "samsung"}, d / "config.json")
    monkeypatch.setattr(guard, "is_frozen", lambda root=None: True)
    with pytest.raises(ValueError, match="lenient is refused on Samsung runs after FROZEN"):
        ss.run_stats_v4(str(tmp_path / "an"), [str(d)], item_f_dir=str(tmp_path), strict=False, root=str(tmp_path))
    monkeypatch.setattr(guard, "is_frozen", lambda root=None: False)                          # before FROZEN lenient stays available (it fails later for other reasons, not this one)
    with pytest.raises(Exception) as e:
        ss.run_stats_v4(str(tmp_path / "an"), [str(d)], item_f_dir=str(tmp_path), strict=False, root=str(tmp_path))
    assert "lenient is refused" not in str(e.value)


def test_m1_a_strict_run_at_the_frozen_commit_needs_the_rows_and_the_g0_run(tmp_path, monkeypatch):
    from pinnkan import guard
    monkeypatch.setattr(guard, "is_frozen", lambda root=None: True)
    from pinnkan import blinding                                                           # the earlier guards (pinned configuration, n, item (f)) are covered by their own tests: stubbed here
    monkeypatch.setattr(v4, "effective_config", lambda cfg, root: (cfg, {}))
    monkeypatch.setattr(blinding, "expected_n", lambda root, test: 40)
    monkeypatch.setattr(v4, "require_item_f", lambda *a, **k: {})
    root = tmp_path / "root"
    (root / "research").mkdir(parents=True)
    kw = dict(item_f_dir=str(tmp_path), root=str(root))
    rows = {"lab_indicator": ["x"], "retain_all": ["x"]}
    with pytest.raises(ss.RegisteredControlError, match=r"\['lab_indicator', 'retain_all', 'random_subset', 'h7_run'\]"):
        ss.run_stats_v4(str(tmp_path / "an"), [], **kw)
    with pytest.raises(ss.RegisteredControlError, match=r"\['random_subset', 'h7_run'\]"):
        ss.run_stats_v4(str(tmp_path / "an"), [], row_runs=rows, **kw)
    with pytest.raises(ss.RegisteredControlError, match="does not name a row"):                 # an unknown row id is no exception
        ss.run_stats_v4(str(tmp_path / "an"), [], row_runs=rows, h7_run="h", random_subset_struck="D999", **kw)
    (root / "research" / "DECISIONS.md").write_text("| D001 | an unrelated row |\n| D998 | 9.9 (o) random-subset row dropped |\n| D999 | 9.9 (o) random-subset row made descriptive (stop rule 5 (5)) |\n")
    for bad_id in ("D001", "D998"):                                                           # n-2: the row must name 9.9 (o) and 'descriptive'
        with pytest.raises(ss.RegisteredControlError, match="does not name a row"):
            ss.run_stats_v4(str(tmp_path / "an"), [], row_runs=rows, h7_run="h", random_subset_struck=bad_id, **kw)
    with pytest.raises(Exception) as e:                                                       # the M-1 check passes; the next step (no runs) fails for another reason
        ss.run_stats_v4(str(tmp_path / "an"), [], row_runs=rows, h7_run="h", random_subset_struck="D999", **kw)
    assert not isinstance(e.value, ss.RegisteredControlError)
    with pytest.raises(ss.RegisteredControlError, match="does not name a row"):                 # D99 is not D999
        ss.run_stats_v4(str(tmp_path / "an"), [], row_runs=rows, h7_run="h", random_subset_struck="D99", **kw)


def test_m4_physval_flags_the_selected_soc_levels_outside_the_hull_and_fig6_marks_them(grid, runs_with_and_without):
    pv = json.load(open(os.path.join(runs_with_and_without["an_new"], "physval_11a.json")))
    ar = pv["arrhenius_ln_rate"]
    assert ar["soc_selected"] == [5, 50, 80, 100] and ar["soc_selected_in_pc2_evaluation"] == [False, True, True, False] and "supports no monotonicity statement" in ar["outside_hull_note"]
    src = open(os.path.join(ROOT, "code", "figures", "fig6_storage.py"), encoding="utf8").read()
    assert "soc_selected_in_pc2_evaluation" in src and "outside hull" in src and "dashed: SOC outside the storage hull, not in PC-2" in src
    no_hull = [d for d in grid["dirs"] if d.endswith("_m32")]
    import shutil
    t = grid["tmp"] + "/nohullphys"
    os.makedirs(t)
    cp = []
    for d in no_hull:
        c = os.path.join(t, os.path.basename(d))
        shutil.copytree(d, c)
        os.remove(os.path.join(c, "storage_hull.json"))
        cp.append(c)
    assert physval.figure_inputs(cp)["arrhenius_ln_rate"]["soc_selected_in_pc2_evaluation"] is None


# ------------------------------------------------------------------------------------------------ red team n-2, n-3, n-4
def _ok_gate():
    return {"tripped": False, "reasons": [], "not_evaluated": [], "rule": "PREREG_v4 gate G: NC-1 trips or PC-1 fails; PC-2 and PC-3 are reported checks, not gate inputs; NC-2 is not a gate"}


def test_n2_a_validly_struck_random_subset_row_is_recorded_as_struck_not_as_not_run(grid, tmp_path):
    root = tmp_path / "root"
    (root / "research").mkdir(parents=True)
    (root / "research" / "DECISIONS.md").write_text("| D777 | 9.9 (o) random-subset row made descriptive under stop rule 5 (5) |\n")
    kw = dict(item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=grid["neg"], gate=_ok_gate(), root=str(root), row_runs={"lab_indicator": grid["dirs"], "retain_all": grid["dirs"]})
    open_ = ss.run_stats_v4(os.path.join(grid["tmp"], "an_nostruck"), grid["dirs"], **kw)
    assert open_["status"]["rows_not_run"] == ["random_subset"] and open_["status"]["provisional"] is True and open_["outcome"]["provisional"] is True
    st = ss.run_stats_v4(os.path.join(grid["tmp"], "an_struck"), grid["dirs"], random_subset_struck="D777", **kw)
    s_ = st["status"]
    assert s_["rows_not_run"] == [] and s_["rows_struck"] == {"random_subset": "D777"} and s_["provisional"] is False and st["outcome"]["provisional"] is False
    assert st["outcome"]["provisional_downgrade_rows_incomplete"] is False and st["downgrade"]["rows_struck"] == {"random_subset": "D777"}
    assert s_["require_registered"] is False and s_["frozen"] is False                          # n-3: the effective values are recorded beside strict and head
    assert open_["status"]["require_registered"] is False and open_["status"]["strict"] is True
    with pytest.raises(ss.RegisteredControlError, match="does not name a row"):                  # refused whenever given, FROZEN or not
        ss.run_stats_v4(os.path.join(grid["tmp"], "an_badstruck"), grid["dirs"], random_subset_struck="D001", **kw)


def test_n3_require_registered_and_frozen_are_recorded(grid):
    out = ss.run_stats_v4(os.path.join(grid["tmp"], "an_req"), grid["dirs"], item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=grid["neg"], require_registered=True)
    assert out["status"]["require_registered"] is True and out["status"]["frozen"] is False and out["status"]["strict"] is True
    assert out["status"]["registered_controls_failed_needs_rescore"] if "registered_controls_failed_needs_rescore" in out["status"] else True


def _check_rescore(out, an, name):
    ctl = json.load(open(os.path.join(an, "controls.json")))
    assert os.path.exists(os.path.join(an, "contrasts_v4_B.json")) and not os.path.exists(os.path.join(an, "STATS_GAPS_ERRORS.json"))
    assert name in out["status"]["registered_controls_failed_needs_rescore"]
    assert name not in out["status"].get("registered_controls_not_evaluated", {})                 # failed, not 'not evaluated': not provisional for that reason
    return ctl


def test_n4_an_nc2_input_integrity_error_is_recorded_as_failed_and_the_step_continues(grid):
    tmp = grid["tmp"]
    ref = ss.run_stats_v4(os.path.join(tmp, "an_n4ref"), grid["dirs"], item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=grid["neg"])
    kw = dict(item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], require_registered=True)
    cases = {}
    cases["not a permute_stress run"] = _bad_negative(grid, "n4a")
    cases["unequal condition sets"] = make_negative(tmp + "/n4b", grid["dirs"], drop_cond=True) if os.makedirs(tmp + "/n4b") is None else None
    c_ = make_negative(tmp + "/n4c", grid["dirs"]) if os.makedirs(tmp + "/n4c") is None else None
    cases["other folds"] = c_[:4]
    for label, neg in cases.items():
        an = os.path.join(tmp, "an_n4_" + label.split()[0])
        out = ss.run_stats_v4(an, grid["dirs"], negative_runs=neg, **kw)                      # no RegisteredControlError
        ctl = _check_rescore(out, an, "NC-2")
        nc2 = ctl["negative"]["nc2"]
        assert nc2["passed"] is False and nc2["failed_needs_rescore"] is True and nc2["fail_sentence"] == "stress dependence was not shown necessary for the accuracy" and nc2["reason"], label
        assert ctl["gate_G"]["tripped"] is False and out["outcome"]["provisional"] == ref["outcome"]["provisional"]
        assert {k: v for k, v in out["effective_tiers"].items()} == ref["effective_tiers"] and out["outcome"].get("title_id") == ref["outcome"].get("title_id")


def test_n4_a_pc3_unequal_condition_set_is_recorded_as_failed_when_required_and_a_compute_error_still_stops(grid, tmp_path, monkeypatch):
    import shutil
    st = make_store()
    st.tables[G4]["R1"] = {c: 2.0 * np.exp(0.3) for c in CONDS[:39]}
    with pytest.raises(sg.NeedsRescoreError, match="R1 scores 39 and A1 40"):
        sg.pc3_v4(st, RULE, require=True)
    assert sg.pc3_v4(st, RULE)["passed"] is None                                                 # development default: the label
    tmp = grid["tmp"] + "/n4pc3"
    os.makedirs(tmp)
    dirs = []
    for d in grid["dirs"]:
        t = os.path.join(tmp, os.path.basename(d))
        shutil.copytree(d, t)
        dirs.append(t)
    f0 = dirs[2]
    assert f0.endswith("f0_m32")
    sc = json.load(open(os.path.join(f0, "condition_scores.json")))
    sc["R1"].pop(next(iter(sc["R1"])))
    _dump(sc, os.path.join(f0, "condition_scores.json"))
    an = os.path.join(tmp, "an")
    out = ss.run_stats_v4(an, dirs, item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=grid["neg"], require_registered=True)
    ctl = _check_rescore(out, an, "PC-3")
    p3 = ctl["positive"]["PC3_detail"]
    assert p3["passed"] is False and p3["failed_needs_rescore"] and p3["fail_sentence"].startswith("At g4 the network's median condition error was not shown lower") and ctl["positive"]["P3_passed"] is False
    assert ctl["gate_G"]["reported_checks"]["PC-3_A1_beats_persistence"] is False and out["gate_G"]["reported_checks"] == ctl["gate_G"]["reported_checks"]
    # a code / compute error is not an integrity error: it still stops
    _boom(monkeypatch)
    with pytest.warns(UserWarning):
        with pytest.raises(ss.RegisteredControlError):
            ss.run_stats_v4(os.path.join(tmp, "an_boom"), dirs, item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=grid["neg"], require_registered=True)
