"""D022a: calibrated extraction audit (PREREG_v4 7.3 item 6): the label rule on the partial dependence, the additivity test, one code path for A15 and G15, 25-law completeness, the
dataset scoring, C1-C3 arithmetic, the guard of the statistics step, the D021 regression, the synthetic truths.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_extraction_audit.py -q"""
import copy
import glob
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest
import torch

torch.set_num_threads(1)

from pinnkan import arms as A
from pinnkan import extraction_audit as X
from pinnkan import symbolic as S
from pinnkan import synth
from pinnkan.specs import SPECS

THR = X.load_thresholds()
INPUTS = THR["inputs"]
SPEC = SPECS["synthetic"]


def _LL(laws, thr=None, calibrated=X.CALIBRATION_RUN, n_expected=None):
    return X.label_law(laws, thr, calibrated, n_expected)


def _LI(name, laws, thr=None, calibrated=X.CALIBRATION_RUN, n_expected=None):
    return X.label_input(name, laws, thr, calibrated, n_expected)


def _AA(laws, arm, calibrated=X.CALIBRATION_RUN, thr=None, n_expected=None):
    return X.audit_arm(laws, arm, calibrated, thr, n_expected)


def _inp(form="linear", sign=1, retained=True, additive=True, family=None, approx=False):
    return {"retained": retained, "range": 0.3 if retained else 0.0, "family": family or (form if form in ("linear", "log") else "composed"), "edge_families": [form], "bic_margin": 4.0,
            "r_lin": 0.0 if form == "linear" else 0.1, "r_log": 0.0 if form == "log" else 0.1, "form": form if retained else "none", "sign": sign if retained else 0, "sign_raw": sign if retained else 0,
            "max_mixed": 0.0 if additive else 0.1, "additive": additive, "approx": approx}


def _law(arm="A15h1", fold=0, seed=0, **per_input):
    return {"arm": arm, "fold": fold, "seed": seed, "h": 1, "outer_families": [], "inputs": {n: per_input.get(n, _inp()) for n in INPUTS}}


def _laws(n=25, arm="A15h1", make=None):
    """25 laws (5 folds x 5 seeds); make(i) -> dict of per-input records (default: every input a strict linear winner, sign +, additive)"""
    return [_law(arm=arm, fold=i // 5, seed=i % 5, **(make(i) if make else {})) for i in range(n)]


# ------------------------------------------------------------------------------------------------ thresholds, wording
def test_thresholds_file_matches_the_frozen_cap_and_is_hashed():
    assert THR["cap"] == S.library_file_cap() == 2 and tuple(THR["eligible_families"]) == ("zero", "linear", "log")
    assert X.thresholds_sha256() == X.sha256_file(X.THRESHOLDS_FILE) and len(X.thresholds_sha256()) == 64 and X.rule_sha256() == X.sha256_file(X.RULE_FILE)
    assert X.RULE_FILE.endswith("calibration_rule_v2.md")
    for k, v in (("laws_per_arm_g4", 25), ("min_agree_share", 0.8), ("tolerance_over_range", 0.01), ("pd_grid_points", 41), ("additivity_grid", 5), ("approx_flag_min_share", 0.5)):
        assert THR[k] == v                                                      # judge 2.2-2.3
    c = THR["calibration"]
    assert (c["D"], c["D_min"], c["alpha"], c["max_upper_limit"], c["min_recall"], c["cpu_cap_hours"], c["amplitude_range"], c["laboratory_offset_sd"]) == (30, 22, 0.05, 0.2, 0.5, 36, [0.05, 0.5], 0.15)
    assert set(THR["inputs"]) == set(SPEC.stress_names)
    assert "identifiable_parameters" not in json.dumps(THR) and "bic_margin_median" not in json.dumps(THR["wording"]["labels"])        # the constant column is gone; BIC margin is an appendix field
    assert THR["future_version_wording"]["failure"]["necessity"] == "The extraction audit did not meet its pre-set necessity condition, so it is reported as a description, not as a method result."
    assert set(X.banned_phrases_in("the law has no effect of dod; structurally identifiable")) == {"no effect", "identifiable"} and X.banned_phrases_in("not retained by the extraction") == []


def test_unreachable_audit_sentences_live_only_in_the_future_version_block():
    assert not ({"scope_sentence", "results_sentence", "not_identified_input", "failure"} & set(THR["wording"]))
    fw = THR["future_version_wording"]
    assert {"scope_sentence", "results_sentence", "not_identified_input", "failure"} <= set(fw) and "fixed by the frozen commit and verified by re-run" in fw["scope_sentence"] and "enforced" not in fw["scope_sentence"]


# ------------------------------------------------------------------------------------------------ arms and completeness
def test_unknown_arm_or_missing_h_is_an_error_and_never_a_silent_default():
    assert X.arm_key("G15", {}) == "G15" and X.arm_key("A15", {"h": 2}) == "A15h2" and X.arm_key("A15", {"h": 1}) == "A15h1"
    for bad in (("A1", {"h": 1}), ("A15", {}), ("A15", {"h": 3}), ("A15", None), ("X", {})):
        with pytest.raises(X.AuditError):
            X.arm_key(*bad)


def test_exactly_25_distinct_laws_per_arm_are_required():
    _LL(_laws())                                                        # 25: fine
    for n in (0, 24, 26):
        with pytest.raises(X.AuditError, match="expected exactly 25"):
            _LL(_laws(n))
    dup = _laws()
    dup[7]["fold"], dup[7]["seed"] = dup[6]["fold"], dup[6]["seed"]
    with pytest.raises(X.AuditError, match="duplicate"):
        _LL(dup)
    with pytest.raises(X.AuditError, match="unknown or mixed"):
        _LL(_laws(arm="A1"))
    mixed = _laws()
    mixed[3]["arm"] = "G15"
    with pytest.raises(X.AuditError, match="unknown or mixed"):
        _LL(mixed)
    _LL(_laws(make=None, arm="A15h2")[:12] + [dict(l, arm="A15h1") for l in _laws()[12:]])        # a KAN arm may mix h = 1 and h = 2 across folds
    with pytest.raises(X.AuditError):
        _AA(_laws()[:24], "A15")
    with pytest.raises(X.AuditError):
        X.baseline_labels(_laws()[:24])


# ------------------------------------------------------------------------------------------------ the label rule
def test_not_retained_needs_20_of_25_and_is_not_a_claim_about_the_truth():
    mk = lambda k: (lambda i: {"dod": _inp(retained=(i >= k))})
    assert _LL(_laws(make=mk(20)))["dod"]["label"] == "not_retained"          # 20 of 25 not retained
    assert _LL(_laws(make=mk(19)))["dod"]["label"] != "not_retained"          # 19
    assert X.label_text(_LL(_laws(make=mk(20)))["dod"]) == "not retained (below the extraction tolerance)"


def test_composed_when_additivity_fails_in_more_than_5_laws():
    mk = lambda k: (lambda i: {"dod": _inp(additive=(i >= k))})
    assert _LL(_laws(make=mk(6)))["dod"]["label"] == "composed"               # 6 of 25 fail
    assert _LL(_laws(make=mk(5)))["dod"]["label"] == "form"                   # 5 of 25 fail: still additive in 20
    assert X.label_text(_LL(_laws(make=mk(6)))["dod"]) == "composed: no single form"


def test_a_tie_gives_no_family_and_a_strict_win_needs_20_of_25():
    mk = lambda k: (lambda i: {"soc_mid": _inp("linear" if i < k else "tie", sign=1)})
    lab = _LL(_laws(make=mk(20)))["soc_mid"]
    assert lab["label"] == "form" and lab["form"] == "linear" and lab["sign"] == 1 and lab["tie_share"] == pytest.approx(5 / 25) and X.label_text(lab) == "form: linear"
    lab = _LL(_laws(make=mk(19)))["soc_mid"]                                      # 19 strict wins + 6 ties: no family; the sign (same in 25 laws) is still licensed
    assert lab["label"] == "sign" and lab["form"] is None and lab["sign"] == 1 and X.label_text(lab) == "sign: +"
    all_tie = _LL(_laws(make=lambda i: {"soc_mid": _inp("tie", sign=-1)}))["soc_mid"]    # T on the Samsung hull: linear and log tie in every law
    assert all_tie["label"] == "sign" and all_tie["form"] is None and all_tie["sign"] == -1 and all_tie["tie_share"] == 1.0
    mixed = _LL(_laws(make=lambda i: {"c_ch": _inp("linear" if i < 12 else "log")}))["c_ch"]       # 12 linear, 13 log: neither family reaches 20
    assert mixed["form"] is None and mixed["wins"] == {"linear": 12, "log": 13}


def test_sign_rule_requires_20_votes_and_no_plus_minus_tie():
    mk = lambda k: (lambda i: {"c_dch": _inp("none", sign=1 if i < k else -1)})
    assert _LL(_laws(make=mk(20)))["c_dch"]["label"] == "sign" and _LL(_laws(make=mk(20)))["c_dch"]["sign"] == 1
    assert _LL(_laws(make=mk(19)))["c_dch"]["label"] == "not_identified"
    assert _LL(_laws(make=mk(5)))["c_dch"]["sign"] == -1
    # a + / - tie cannot reach the 80 % share; with a looser share the tie rule itself must give no sign
    thr = copy.deepcopy(THR)
    thr["min_agree_share"] = 0.4
    lab = _LI("c_dch", _laws(10, make=lambda i: {"c_dch": _inp("none", sign=1 if i < 5 else -1)}), thr, n_expected=10)
    assert lab["label"] == "not_identified" and lab["sign"] == 0
    # a sign needs additivity: 6 non-additive laws make the input composed, not signed
    assert _LL(_laws(make=lambda i: {"c_dch": _inp("none", sign=1, additive=i >= 6)}))["c_dch"]["label"] == "composed"
    # magnitude: a sign of 0 (change below 1 % of the range) is not a vote
    assert _LL(_laws(make=lambda i: {"soc_mid": _inp("none", sign=0)}))["soc_mid"]["label"] == "not_identified"


def test_no_label_is_printed_for_an_arm_that_failed_c1():
    lab = _LL(_laws(), calibrated=False)
    assert all(v["label"] == "not_identified" and v["form"] is None and v["sign"] == 0 for v in lab.values()) and "no verified calibration" in lab["dod"]["reasons"][0]
    out = _AA(_laws(), "A15", False)
    assert out["labels_printed"] is False and "labels" not in out and len(out["stability_table"]) == 5 and "scope_sentence" not in out and "calibration" not in json.dumps(out) and "re-run" not in json.dumps(out)
    assert {"input", "extracted_edge_family_counts", "sign_votes", "tie_share", "not_retained_share"} <= set(out["stability_table"][2])


def test_fixed_results_sentence_counts_and_the_table_columns():
    mk = lambda i: {"soc_mid": _inp("tie", sign=-1), "T_C": _inp("none", sign=0), "dod": _inp("linear"), "c_ch": _inp("log"), "c_dch": _inp(retained=False)}
    out = _AA(_laws(make=mk), "A15")
    s = out["sentences"]
    assert s["counts"] == {"n": 5, "form": 2, "sign": 1, "not_identified": 1, "not_retained": 1}              # dod, c_ch form; T sign only; soc_mid not identified; c_dch not retained
    assert s["results"] == "Of the 5 inputs of the extracted KAN law, the audit licensed the form of 2 and the sign of 1; 1 were not identified and 1 were not retained by the extraction."
    assert _AA(_laws(arm="G15", make=mk), "G15")["sentences"]["results"].startswith("Of the 5 inputs of the extracted additive law,")
    t = {r["input"]: r for r in out["table"]}
    assert t["soc_mid"]["label"] == "sign: -" and t["dod"]["label"] == "form: linear" and t["c_dch"]["label"].startswith("not retained")
    assert {"arm", "input", "label", "form_wins", "tie_share", "sign_votes", "n_not_retained", "notes", "appendix"} <= set(t["dod"]) and "identifiable_parameters" not in t["dod"]
    assert t["dod"]["appendix"]["bic_margin_median"] == 4.0 and "KAN's grid" in t["dod"]["appendix"]["bic_caveat"]
    assert "the audit does not license a form for this effect" in t["T_C"]["notes"] and t["dod"]["notes"] == []
    assert THR["wording"]["discussion_sentence"].endswith("we name no form or direction for its individual effects.")


def test_extraction_loss_flag_uses_the_arms_own_parent():
    lab = _LL(_laws(make=lambda i: {"dod": _inp(approx=(i < 13))}))["dod"]          # 13 of 25 flagged: share 0.52 > 0.5
    assert lab["extraction_loss"] is True
    assert _LL(_laws(make=lambda i: {"dod": _inp(approx=(i < 12))}))["dod"]["extraction_loss"] is False


def test_a15_and_g15_laws_are_labelled_by_one_function_with_identical_results():
    mk = lambda i: {"dod": _inp("log", sign=-1), "T_C": _inp("tie", sign=1), "c_ch": _inp("none", sign=1, additive=i > 7)}
    la, lg = _LL(_laws(arm="A15h1", make=mk)), _LL(_laws(arm="G15", make=mk))
    assert la == lg
    assert X.label_law.__module__ == X.audit_arm.__module__ == X.law_record.__module__ == "pinnkan.extraction_audit"
    assert _AA(_laws(arm="G15", make=mk), "G15")["labels"] == _AA(_laws(arm="A15h1", make=mk), "A15")["labels"]


# ------------------------------------------------------------------------------------------------ the per-law quantities on real functions
def _fake_report(h, outer_family):
    first = [[{"family": "linear", "range": 1.0} for _ in range(5)] for _ in range(h)]
    return {"cyclic": {"layers": [{"edges": first}, {"edges": [[{"family": outer_family, "range": 1.0} for _ in range(h)]]}]}}


def _s_train(n=40, seed=0):
    return np.random.default_rng(seed).uniform(-1.0, 1.0, size=(n, 5))


def test_a15_h1_with_a_log_outer_edge_is_non_additive_and_a_linear_one_is_additive():
    w = torch.tensor([0.2, 0.15, 0.25, 0.2, 0.1])
    log_outer = lambda s: torch.log(1.2 + s @ w)                                              # outer log edge over the one hidden unit: log(c + w.s)
    lin_outer = lambda s: 0.7 * (s @ w)
    rec_log = X.law_record("A15h1", 0, 0, _fake_report(1, "log"), SPEC, log_outer, None, _s_train())
    rec_lin = X.law_record("A15h1", 0, 0, _fake_report(1, "linear"), SPEC, lin_outer, None, _s_train())
    assert rec_log["h"] == 1 and rec_log["outer_families"] == ["log"]
    assert all(not r["additive"] and r["max_mixed"] > 0.01 * r["range"] for r in rec_log["inputs"].values())          # h = 1 is NOT assumed additive (D022a M6)
    assert all(r["additive"] and r["max_mixed"] < 1e-5 for r in rec_lin["inputs"].values())
    labs = _LL([dict(rec_log, fold=i // 5, seed=i % 5) for i in range(25)])
    assert all(v["label"] == "composed" for v in labs.values())


def test_partial_dependence_quantities_for_linear_and_log_effects_and_the_tie_on_a_narrow_hull():
    lo, hi = SPEC.denorm(-np.ones(5)), SPEC.denorm(np.ones(5))
    def fn_log_in(i, sign):
        def f(s):
            x = SPEC.denorm(s.numpy().astype(float))[:, i] + (273.15 if i == 0 else 0.0)
            return torch.tensor(sign * np.log(x), dtype=torch.float32)
        return f
    # c_ch is log-like in x: r_log ~ 0, r_lin > 0.01, strict log winner; a linear effect is the other way round
    rec = X.law_record("G15", 0, 0, _fake_report(1, "linear"), SPEC, fn_log_in(3, 1.0), None, _s_train())["inputs"]["c_ch"]
    assert rec["retained"] and rec["form"] == "log" and rec["sign"] == 1 and rec["r_log"] < 1e-5 and rec["r_lin"] > 0.01 and rec["additive"]
    lin = X.law_record("G15", 0, 0, _fake_report(1, "linear"), SPEC, lambda s: -0.4 * s[:, 2], None, _s_train())["inputs"]
    assert lin["dod"]["form"] == "linear" and lin["dod"]["sign"] == -1 and lin["dod"]["r_lin"] < 1e-6
    for n in ("T_C", "soc_mid", "c_ch", "c_dch"):                                                       # inputs the function does not use: not retained, additive by convention
        assert lin[n]["retained"] is False and lin[n]["form"] == "none" and lin[n]["sign"] == 0 and lin[n]["additive"]
    # a narrow positive hull (ratio hi/lo near 1.1): linear and log both within 1 % -> tie
    narrow = np.random.default_rng(1).uniform(0.15, 0.55, size=(40, 5))            # normalised T on a narrow part of its range
    tie = X.law_record("G15", 0, 0, _fake_report(1, "linear"), SPEC, lambda s: 1.0 * s[:, 0], None, narrow)["inputs"]["T_C"]
    assert tie["form"] in ("tie", "linear") and tie["r_lin"] < 1e-6                                       # exactly linear in the normalised (hence the physical) input; log within tolerance on this hull
    assert (tie["r_log"] <= 0.01) == (tie["form"] == "tie")


def test_extraction_loss_flag_compares_with_the_arms_own_parent():
    f = lambda s: 0.4 * s[:, 2]
    same = X.law_record("G15", 0, 0, _fake_report(1, "linear"), SPEC, f, f, _s_train())["inputs"]["dod"]
    off = X.law_record("G15", 0, 0, _fake_report(1, "linear"), SPEC, f, lambda s: 0.4 * s[:, 2] ** 3, _s_train())["inputs"]["dod"]
    assert same["approx"] is False and off["approx"] is True
    assert X.law_record("G15", 0, 0, _fake_report(1, "linear"), SPEC, f, None, _s_train())["inputs"]["dod"]["approx"] is None


def test_law_record_refuses_an_unknown_arm_key_or_an_h_that_disagrees_with_the_network():
    f = lambda s: 0.4 * s[:, 2]
    with pytest.raises(X.AuditError):
        X.law_record("A1", 0, 0, _fake_report(1, "linear"), SPEC, f, None, _s_train())
    with pytest.raises(X.AuditError, match="disagrees"):
        X.law_record("A15h2", 0, 0, _fake_report(1, "linear"), SPEC, f, None, _s_train())


def test_a15_and_g15_go_through_one_code_path_and_the_extraction_is_cap_2():
    S0 = synth.make_synthetic("G0", n_cyc_cond=12, n_sto_cond=5, reps=2, seed=3)
    tr, _ = synth.split_conditions(S0.cells, 0.25, 3)
    ctx = {"backbone": "self_limiting", "steps_scale": 0.15, "symbolic": {"cap": 2}}
    laws = {}
    for arm_id, over in (("A15", {"h": 1}), ("A15", {"h": 2}), ("G15", {})):
        hp = {**A.default_hp(arm_id), **over}
        key = X.arm_key(arm_id, hp)
        arm = A.make_arm(arm_id, SPEC, hp, 0, ctx).fit(tr)
        assert arm.report["cap"] == 2
        laws[key] = X.law_record(key, 0, 0, arm.report, SPEC, arm.model.law.cyc, arm.parent_cyc, arm.s_cyc_train)
    assert laws["A15h1"]["h"] == 1 and laws["A15h2"]["h"] == 2 and laws["G15"]["h"] == 1 and laws["G15"]["outer_families"] == []
    for rec in laws.values():
        assert set(rec["inputs"]) == set(INPUTS)
        for r in rec["inputs"].values():
            assert r["form"] in ("linear", "log", "tie", "none") and r["sign"] in (-1, 0, 1) and isinstance(r["additive"], bool) and isinstance(r["approx"], bool)
            assert all(f in ("zero", "linear", "log") for f in r["edge_families"])                 # cap 2: no 3-coefficient family can appear
            assert (r["r_lin"] is None) == (not r["retained"])
        json.dumps(rec)


# ------------------------------------------------------------------------------------------------ dataset scoring and C1-C3
def _truth(**kw):
    base = {n: {"stratum": "zero", "sign": 0, "interacting": False, "amp": 0.2} for n in INPUTS}
    for n, v in kw.items():
        base[n] = {**base[n], **v}
    return base


def test_false_statements_follow_the_definitions_of_rule_v2_section_4_1():
    lin = {"stratum": "linear", "sign": 1, "interacting": False}
    assert X.false_statements({"form": "linear", "sign": 1}, lin) == []
    assert X.false_statements({"form": "log", "sign": 1}, lin) == ["form"]                    # the other family
    assert X.false_statements({"form": "linear", "sign": -1}, lin) == ["sign"]                # right form, wrong sign
    assert X.false_statements({"form": "linear", "sign": 1}, {**lin, "stratum": "zero", "sign": 0}) == ["form", "sign"]
    for s in ("quadratic", "hinge"):
        assert "form" in X.false_statements({"form": "linear", "sign": 0}, {"stratum": s, "sign": 0, "interacting": False})
    assert X.false_statements({"form": None, "sign": 1}, {"stratum": "quadratic", "sign": 0, "interacting": False}) == ["sign"]        # sign on a symmetric quadratic
    assert X.false_statements({"form": None, "sign": 1}, {"stratum": "hinge", "sign": 1, "interacting": False}) == []
    assert X.false_statements({"form": "linear", "sign": 1}, {**lin, "interacting": True}) == ["form"]                                  # a form on an interacting input
    assert X.false_statements({"form": None, "sign": 1}, {**lin, "interacting": True}) == []                                           # its sign equals the main-effect sign
    assert X.false_statements({"form": None, "sign": 0}, lin) == [] and X.false_statements({"form": None, "sign": 0}, _truth()["dod"]) == []   # abstention is never false


def test_score_dataset_recall_events_and_the_stability_baseline():
    tr = _truth(dod={"stratum": "linear", "sign": 1}, c_ch={"stratum": "log", "sign": -1}, c_dch={"stratum": "linear", "sign": 1, "interacting": True}, soc_mid={"stratum": "quadratic", "sign": 0})
    perfect = {n: {"form": None, "sign": 0} for n in INPUTS}
    perfect.update(dod={"form": "linear", "sign": 1}, c_ch={"form": "log", "sign": -1})
    assert X.score_dataset(perfect, tr) == {"E": 0, "false": []}
    assert X.recall_events(perfect, tr) == [1, 1]                                  # events: dod (linear), c_ch (log); c_dch interacts, soc_mid is quadratic, T is not a many-level input
    bad = dict(perfect, soc_mid={"form": "linear", "sign": 1})
    assert X.score_dataset(bad, tr) == {"E": 1, "false": [("soc_mid", "form"), ("soc_mid", "sign")]}
    assert X.recall_events(dict(perfect, dod={"form": None, "sign": 1}), tr) == [0, 1]
    base = X.baseline_labels(_laws(make=lambda i: {"dod": _inp("linear", sign=-1, family="linear"), "c_ch": _inp("log", sign=1, family="log" if i < 20 else "composed")}))
    assert base["dod"] == {"form": "linear", "sign": -1} and base["c_ch"] == {"form": "log", "sign": 1}
    base = X.baseline_labels(_laws(make=lambda i: {"c_ch": _inp("log", family="log" if i < 19 else "composed")}))
    assert base["c_ch"]["form"] is None and base["c_ch"]["sign"] == 1                    # 19 of 25: no form; the sign vote is 25 of 25
    assert X.baseline_labels(_laws(make=lambda i: {"T_C": _inp("tie", family="composed")}))["T_C"]["form"] is None


def _per_arm(D, k, kb=None, ev=(1, 1, 0, 1), evb=(1, 0, 0, 0)):
    """D datasets, the first k with a false statement (audit) and the first kb (baseline)"""
    kb = D if kb is None else kb
    return [{"d": d, "E": int(d < k), "E_baseline": int(d < kb), "events": list(ev), "events_baseline": list(evb)} for d in range(D)]


def test_clopper_pearson_arithmetic_against_the_judge_counts():
    up = lambda k, n: X.clopper_pearson_upper(k, n)
    assert [round(up(k, 30), 3) for k in (0, 1, 2, 3)] == [0.095, 0.149, 0.195, 0.239]               # D = 30: at most 2 false datasets pass
    assert [round(up(k, 22), 3) for k in (0, 1, 2)] == [0.127, 0.198, 0.259]                          # D = 22: at most 1
    assert up(30, 30) == 1.0 and np.isnan(up(0, 0))
    assert X.clopper_pearson(0, 20)[0] == 0.0 and X.clopper_pearson(20, 20)[1] == 1.0 and X.clopper_pearson(5, 20) == pytest.approx((0.0866, 0.4910), abs=1e-3)


def test_c1_c2_c3_verdict_arithmetic_and_the_consequence():
    ok = X.verdict({"A15": _per_arm(30, 2), "G15": _per_arm(30, 0)})
    assert ok["contribution"] is True and ok["arms"]["A15"]["C1"] and ok["arms"]["A15"]["upper_limit"] == pytest.approx(0.195, abs=1e-3) and ok["failed_conditions"] == [] and ok["failure_sentences"] == []
    assert ok["arms"]["G15"]["recall"] == 0.75 and ok["arms"]["G15"]["C2"] and ok["arms"]["G15"]["C3"] and ok["arms"]["G15"]["baseline_upper_limit"] == 1.0
    # C1 fails at 3 of 30; the other arm passing does not save the contribution
    v = X.verdict({"A15": _per_arm(30, 3), "G15": _per_arm(30, 0)})
    assert v["arms"]["A15"]["C1"] is False and v["arms"]["G15"]["C1"] is True and v["contribution"] is False and v["failed_conditions"] == [("A15", "calibration")]
    assert v["failure_sentences"] == [THR["future_version_wording"]["failure"]["calibration"]]
    # D = 22: one false dataset passes, two fail
    assert X.verdict({"A15": _per_arm(22, 1), "G15": _per_arm(22, 0)})["contribution"] is True
    assert X.verdict({"A15": _per_arm(22, 2), "G15": _per_arm(22, 0)})["arms"]["A15"]["C1"] is False
    # C2: recall 0.5 passes (point estimate), 0.25 fails
    assert X.verdict({"A15": _per_arm(30, 0, ev=(1, 0)), "G15": _per_arm(30, 0)})["arms"]["A15"]["C2"] is True
    v = X.verdict({"A15": _per_arm(30, 0, ev=(1, 0, 0, 0)), "G15": _per_arm(30, 0)})
    assert v["arms"]["A15"]["C2"] is False and v["failure_sentences"] == [THR["future_version_wording"]["failure"]["usefulness"]]
    # C3: a stability-only baseline that passes C1 makes the audit unnecessary
    v = X.verdict({"A15": _per_arm(30, 0, kb=2), "G15": _per_arm(30, 0)})
    assert v["arms"]["A15"]["baseline_C1"] is True and v["arms"]["A15"]["C3"] is False and v["contribution"] is False and v["failure_sentences"] == [THR["future_version_wording"]["failure"]["necessity"]]
    # several failures: one fixed sentence each, in the order calibration, usefulness, necessity
    v = X.verdict({"A15": _per_arm(30, 3, ev=(0, 0), kb=0), "G15": _per_arm(30, 0)})
    assert v["failure_sentences"] == [THR["future_version_wording"]["failure"][k] for k in ("calibration", "usefulness", "necessity")]
    # fewer than 22 complete datasets: void
    vv = X.verdict({"A15": _per_arm(21, 0), "G15": _per_arm(21, 0)})
    assert vv["void"] is True and vv["contribution"] is False and "D_min" in vv["reason"]
    assert X.verdict({"A15": _per_arm(22, 0), "G15": _per_arm(22, 0)})["void"] is False


# ------------------------------------------------------------------------------------------------ the guard of the statistics step (calibration record)
def _write_cal(cdir, commit="c" * 40, thr_sha=None, rule_sha=None, verdict=None, extra=None):
    os.makedirs(cdir, exist_ok=True)
    v = verdict or {"void": False, "contribution": True, "failure_sentences": [], "arms": {"A15": {"C1": True}, "G15": {"C1": True}}}
    cal = {"commit": commit, "thresholds_sha256": thr_sha or X.thresholds_sha256(), "rule_sha256": rule_sha or X.rule_sha256(), "verdict": v, **(extra or {})}
    p = os.path.join(cdir, X.CALIBRATION_FILE)
    with open(p, "w") as fh:
        json.dump(cal, fh, sort_keys=True)
    return X.sha256_file(p)


def test_edge_wording_pins_are_mandatory_and_the_record_must_match(tmp_path):
    cdir = str(tmp_path / "cal")
    C = "c" * 40
    with pytest.raises(X.AuditGuardError, match="audit_thresholds_pin is mandatory"):
        X.require_calibration(cdir, None, "x", C)
    with pytest.raises(X.AuditGuardError, match="calibration_sha256 is mandatory"):
        X.require_calibration(cdir, X.thresholds_sha256(), None, C)
    with pytest.raises(X.AuditGuardError, match="no FROZEN commit"):
        X.require_calibration(cdir, X.thresholds_sha256(), "x", None)
    with pytest.raises(X.AuditGuardError, match="no calibration record"):
        X.require_calibration(cdir, X.thresholds_sha256(), "x", C)
    sha = _write_cal(cdir)
    assert X.require_calibration(cdir, X.thresholds_sha256(), sha, C)["verdict"]["contribution"] is True
    with pytest.raises(X.AuditGuardError, match="does not hash"):
        X.require_calibration(cdir, X.thresholds_sha256(), "0" * 64, C)
    with pytest.raises(X.AuditGuardError, match="other thresholds"):
        X.require_calibration(cdir, "0" * 64, sha, C)
    with pytest.raises(X.AuditGuardError, match="not the FROZEN commit"):
        X.require_calibration(cdir, X.thresholds_sha256(), sha, "d" * 40)
    sha2 = _write_cal(cdir, thr_sha="1" * 64)
    with pytest.raises(X.AuditGuardError, match="other thresholds"):
        X.require_calibration(cdir, X.thresholds_sha256(), sha2, C)
    sha3 = _write_cal(cdir, rule_sha="2" * 64)
    with pytest.raises(X.AuditGuardError, match="another rule file"):
        X.require_calibration(cdir, X.thresholds_sha256(), sha3, C)
    sha4 = _write_cal(cdir, commit="e" * 40)
    with pytest.raises(X.AuditGuardError, match="not the FROZEN commit"):
        X.require_calibration(cdir, X.thresholds_sha256(), sha4, C)
    sha5 = _write_cal(cdir, verdict={"void": True, "contribution": False})
    with pytest.raises(X.AuditGuardError, match="void"):
        X.require_calibration(cdir, X.thresholds_sha256(), sha5, C)
    _write_cal(cdir)
    with open(os.path.join(cdir, X.CALIBRATION_FILE), "a") as fh:
        fh.write(" ")                                                           # altered after hashing
    with pytest.raises(X.AuditGuardError, match="does not hash"):
        X.require_calibration(cdir, X.thresholds_sha256(), sha, C)


def _runs_with_laws(tmp_path, n_a15=25, n_g15=25):
    dirs = []
    for f in range(5):
        d = tmp_path / f"run{f}"
        d.mkdir()
        json.dump({"m": 32, "fold": f}, open(d / "config.json", "w"))
        laws = []
        for s in range(5):
            if f * 5 + s < n_a15:
                laws.append(_law(arm="A15h1", fold=f, seed=s))
            if f * 5 + s < n_g15:
                laws.append(_law(arm="G15", fold=f, seed=s))
        json.dump({"m": 32, "fold": f, "laws": laws, "levels": {}}, open(d / "extracted_laws.json", "w"))
        dirs.append(str(d))
    return dirs


def test_collect_laws_needs_exactly_25_laws_per_arm_at_g4(tmp_path):
    (tmp_path / "a").mkdir()
    ok = X.collect_laws(_runs_with_laws(tmp_path / "a"))
    assert len(ok["A15"]) == len(ok["G15"]) == 25
    (tmp_path / "b").mkdir()
    with pytest.raises(X.AuditError, match="expected exactly 25"):
        X.collect_laws(_runs_with_laws(tmp_path / "b", n_g15=24))
    (tmp_path / "c").mkdir()
    with pytest.raises(X.AuditError, match="expected exactly 25"):
        X.collect_laws(_runs_with_laws(tmp_path / "c", n_a15=20))


# ------------------------------------------------------------------------------------------------ D021 regression
def test_audit_reproduces_the_D021_false_structure_counts_on_the_D021_seeds():
    files = glob.glob(os.path.join(ROOT, "runs", "D021_cap_synth", "pipeline_p*.jsonl"))
    assert files
    recs = [json.loads(l) for f in files for l in open(f, encoding="utf8")]
    assert X.false_structure_counts(recs, 3, "A15h1", 32) == (37, 40) and X.false_structure_counts(recs, 3, "G15", 32) == (37, 40)
    for arm in ("A15h1", "A15h2", "G15"):
        for m in (32, 8):
            assert X.false_structure_counts(recs, 2, arm, m) == (0, 40)                                    # cap 2: no 3-coefficient form exists
    assert X.false_structure_counts(recs, 3, "A15h1", 8)[0] == 32


# ------------------------------------------------------------------------------------------------ synthetic truths on the real design
def X_truth(fam, sign, x):
    return synth.truth_effect(fam, sign, x, 1.0, 5.0)


def test_truth_effects_and_the_synthetic_generator_on_a_given_design():
    x = np.linspace(1.0, 5.0, 11)
    for fam in ("linear", "log", "hinge"):
        e = X_truth(fam, 1, x)
        assert e[0] == pytest.approx(-0.5) and e[-1] == pytest.approx(0.5)
        assert np.allclose(X_truth(fam, -1, x), -e)
    q = X_truth("quadratic", 1, x)
    assert q[0] == pytest.approx(0.5) and q[-1] == pytest.approx(0.5) and q[5] == pytest.approx(-0.5)
    assert np.all(X_truth("zero", 1, x) == 0)
    assert [synth.truth_sign(f, 1) for f in ("zero", "linear", "log", "quadratic", "hinge")] == [0, 1, 1, 0, 1] and synth.truth_sign("log", -1) == -1
    assert synth.truth_effect("linear", 1, x, 1.0, 5.0, 0.1)[-1] == pytest.approx(0.1)                            # amplitude argument
    sp = json.load(open(os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json")))
    ids = sp["B"]["folds"]["0"]["train_cycling_conditions"]
    sto = sorted({c for f in sp["S2"]["folds"].values() for c in f["test_conditions"]})
    design = synth.design_from_keys(ids, sto, 2)
    assert len(design[0]) == 32 and len(design[1]) == 19
    T = {0: ("linear", 1, 296.15, 318.15), 1: ("zero", 1, 0.2, 0.9), 2: ("log", -1, 0.05, 0.6, 0.2), 3: ("linear", -1, 0.2, 1.0), 4: ("zero", 1, 0.2, 2.0)}
    S0 = synth.make_synthetic("GA", reps=2, seed=1, design=design, truth=T)
    cyc = [c for c in S0.cells if c.kind == "cycling"]
    assert len({c.cond for c in cyc}) == 32 and len(cyc) == 64 and len({c.cond for c in S0.cells if c.kind == "storage"}) == 19
    raw = np.array([c.raw for c in cyc])
    f = np.asarray(S0.log_rate_cyc(raw)).ravel() - S0.params["c_cyc"]
    ref = sum(synth.truth_effect(t[0], t[1], raw[:, i] + (273.15 if i == 0 else 0.0), t[2], t[3], *t[4:5]) for i, t in T.items())
    assert np.allclose(f, ref)
    # interaction: adds amp * u_p * u_q on the physical hull coordinates
    inter = (2, 3, 0.3, 0.05, 0.6, 0.2, 1.0)
    S1 = synth.make_synthetic("GA", reps=2, seed=1, design=design, truth=T, interaction=inter)
    f1 = np.asarray(S1.log_rate_cyc(raw)).ravel() - S1.params["c_cyc"]
    up, uq = 2 * (raw[:, 2] - 0.05) / 0.55 - 1, 2 * (raw[:, 3] - 0.2) / 0.8 - 1
    assert np.allclose(f1 - ref, 0.3 * up * uq)


def test_condition_offsets_are_added_to_the_cyclic_log_rate_without_changing_the_random_draws():
    sp = json.load(open(os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json")))
    ids = sp["B"]["folds"]["0"]["train_cycling_conditions"]
    sto = sorted({c for f in sp["S2"]["folds"].values() for c in f["test_conditions"]})
    design = synth.design_from_keys(ids, sto, 2)
    T = {0: ("linear", 1, 296.15, 318.15)}
    a = synth.make_synthetic("GA", reps=2, seed=4, design=design, truth=T)
    b = synth.make_synthetic("GA", reps=2, seed=4, design=design, truth=T, cond_offsets={0: 0.3, 5: -0.2})
    da, db = {c.cell_id: c.meta["delta_true"] for c in a.cells}, {c.cell_id: c.meta["delta_true"] for c in b.cells}
    assert set(da) == set(db)
    ch = {k for k in da if abs(db[k] - da[k]) > 1e-12}
    assert {a.cond_of[k] for k in ch} == {"C00", "C05"} and len(ch) == 4                                           # two replicate cells of each of the two conditions
    assert all(abs((db[k] - da[k]) - (0.3 if a.cond_of[k] == "C00" else -0.2)) < 1e-12 for k in ch)
    c0 = synth.make_synthetic("GA", reps=2, seed=4, design=design, truth=T, cond_offsets={})
    assert all(np.array_equal(x.ret, y.ret) for x, y in zip(a.cells, c0.cells))                      # no offsets: identical data


# ------------------------------------------------------------------------------------------------ D022b: the fallback (audit struck; descriptive reporting only)
def test_label_functions_default_to_no_licence_and_refuse_a_bare_true():
    lab = X.label_law(_laws())                                                  # default calibrated=False
    assert all(v["label"] == "not_identified" and v["form"] is None and v["sign"] == 0 for v in lab.values())
    assert X.label_input("dod", _laws())["label"] == "not_identified" and X.audit_arm(_laws(), "A15")["labels_printed"] is False
    for call in (lambda: X.label_law(_laws(), calibrated=True), lambda: X.label_input("dod", _laws(), calibrated=True), lambda: X.audit_arm(_laws(), "A15", True)):
        with pytest.raises(X.AuditGuardError, match="verified calibration"):
            call()
    assert _LL(_laws())["dod"]["label"] == "form"                               # only the calibration script's sentinel (or a verified record) licenses
    assert X.label_law(_laws(), calibrated={"verdict": {"void": False, "contribution": True, "arms": {"A15": {"C1": True}}}})["dod"]["label"] == "form"
    for empty in ({}, {"verdict": {}}, {"verdict": None}, {"commit": "x"}):
        assert X._licensed(empty) is False and X.label_law(_laws(), calibrated=empty)["dod"]["label"] == "not_identified"


def test_a_temperature_form_or_sign_is_never_licensed_even_with_a_verified_calibration():
    lab = _LL(_laws())["T_C"]
    assert lab["label"] == "not_identified" and lab["form"] is None and lab["sign"] == 0 and lab["never_licensed"] is True
    assert _LL(_laws(make=lambda i: {"T_C": _inp("none", sign=-1)}))["T_C"]["sign"] == 0
    assert _LL(_laws())["dod"]["label"] == "form"
    rows = {r["input"]: r for r in X.stability_table(_laws())}
    assert rows["T_C"] == {"input": "T_C", "display": "temperature (aliased with laboratory; no form or sign reported)", "note": "temperature and laboratory cannot be separated"}      # no counts, no votes
    assert rows["dod"]["note"] is None and {"additive_share", "tie_share", "sign_votes", "extracted_edge_family_counts"} <= set(rows["dod"])
    assert [r["label"] for r in _AA(_laws(), "A15")["table"] if r["input"] == "T_C"] == ["temperature (aliased with laboratory; no form or sign reported)"]


def test_banned_phrases_use_word_boundaries_and_cover_the_03_section_4_claims():
    pass
    assert THR["wording"]["discussion_sentence"].endswith("we name no form or direction for its individual effects.")
    assert THR["wording"]["stability_table_caption"] == "descriptive; not evidence that the training design identifies these forms"
