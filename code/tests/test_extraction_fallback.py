"""D022b red-team fixes (08_redteam_fallback.md): A1 permanent temperature ban on the learned law (physval, Fig. 5), A2 no calibration scope sentence in unlicensed output, A4 banned list and the
fail-closed check on generated sentences, minors (empty calibration dict, temperature display, partial-grid descriptive path)."""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

from pinnkan import extraction_audit as X
from pinnkan import guard, physval, semi, stats_step as ss, stats_v4
from pinnkan import symbolic as S
from test_extraction_calibration import _calibration, _with_laws
from test_pk_v2_review import _grid_runs, _item_f_before

THR = X.load_thresholds()
TLABEL = "temperature (aliased with laboratory; no form or sign reported)"


# ------------------------------------------------------------------------------------------------ A1
def _M():
    x = np.linspace(0, 1, 11)
    up = np.stack([x, 1.1 * x, 0.9 * x])
    return {"cyc": {"T": dict(x=x, members=up, a10=x), "c_ch": dict(x=x, members=up, a10=x)}}


def test_the_learned_law_prints_no_temperature_direction_and_no_verdict_other_inputs_unchanged(monkeypatch):
    monkeypatch.setitem(semi.A10_FORM, "verified", True)
    M = _M()
    d = physval.cyclic_directions(M)
    assert d["T"] == {"display": TLABEL} and d["c_ch"]["share_increasing"] == 1.0 and d["c_ch"]["direction_of_mean_curve"] == 1.0 and d["c_ch"]["n_members"] == 3
    v = physval.compare_with_a10_signs(M)
    assert v["T"] == {"display": TLABEL} and v["c_ch"]["verdict"] == "consistent" and v["c_ch"]["sign_A10"] == 1.0
    txt = json.dumps({"d": d["T"], "v": v["T"]})
    assert all(w not in txt for w in ("consistent", "increasing", "decreasing", "verdict", "share", "sign_A10", "envelope"))
    M["cyc"]["T_C"] = M["cyc"].pop("T")                                                                      # either name of the temperature input
    assert physval.cyclic_directions(M)["T_C"] == {"display": TLABEL} and physval.compare_with_a10_signs(M)["T_C"] == {"display": TLABEL}
    only_t = {"cyc": {"T": dict(x=np.arange(3.0), members=np.zeros((2, 3)), a10=None)}}
    assert "verdict" not in json.dumps(physval.compare_with_a10_signs(only_t))


def test_the_figure_5_temperature_panel_has_no_curve_and_the_printed_formula_masks_temperature():
    src = open(os.path.join(ROOT, "code", "figures", "fig5_stress.py"), encoding="utf8").read()
    i = src.index('if name == "T":')
    assert "temperature (aliased with" in src[i:i + 400] and "continue" in src[i:i + 500] and src.index("band(P, x, d[\"A1\"]") > i
    rep = {"cyclic": {"layers": [{"layer": 0, "edges": [[{"family": "log", "theta": [0.5, 1.0]}, {"family": "linear", "theta": [0.2, 0.1]}]]},
                                  {"layer": 1, "edges": [[{"family": "linear", "theta": [1.0, 0.0]}]]}]}, "calendar": None}
    lines = S.describe(rep)
    assert lines[0] == f"cyclic layer 0 edge 0<-0: {TLABEL}" and "linear" in lines[1] and "[0.2, 0.1]" in lines[1] and "log" not in "".join(lines) and "0.5" not in lines[0]
    assert "outer" not in lines[2] and lines[2].startswith("cyclic layer 1 edge 0<-0: linear")                       # the outer edge acts on a hidden unit, not on temperature


# ------------------------------------------------------------------------------------------------ A2
def _laws(n_arm_laws=25):
    from test_extraction_audit import _laws as L
    return L(n_arm_laws)


def test_the_unlicensed_output_carries_no_calibration_or_rerun_sentence():
    out = X.audit_arm(_laws(), "A15")
    txt = json.dumps(out).lower()
    assert "scope_sentence" not in out and "calibration design" not in txt and "re-run" not in txt and "verified" not in txt
    assert "calibration" not in json.dumps(THR["wording"]).lower() and "re-run" not in json.dumps(THR["wording"]).lower()
    assert "calibration design" in json.dumps(THR["future_version_wording"])                                    # kept only in the unreachable future-version block


# ------------------------------------------------------------------------------------------------ A4
CLAIMS = ["the extracted law recovered a trend", "the KAN recovers the dependence", "it discovers a form", "a discovery of the stress law", "the extracted law shows an Arrhenius dependence",
          "the extracted law shows the power-law form", "the extracted cycling law follows a power\nlaw", "the extracted law is exponential in C_ch", "the extracted stress law is quadratic",
          "a hinge in the extracted law", "a threshold in the extracted law", "the activation energy of the extracted cycling law is 30 kJ", "the extracted law is non-monotone in SOC",
          "the extracted law is non-monotonic in SOC", "the input was identified", "the effect is identifiable", "structural identifiability", "the law has no effect of dod", "more identified",
          "the KAN law recovers the power-law form", "the extracted law shows a hinge"]


@pytest.mark.parametrize("claim", CLAIMS)
def test_banned_claims_and_their_variants_are_caught(claim):
    assert X.banned_phrases_in(claim), claim


def test_required_and_approved_text_is_not_a_claim():
    ok = ["the extracted law cannot represent the non-monotone SOC dependence reported by the dataset authors", "the library holds linear, quadratic, power, exponential, Arrhenius and hinge forms",
          "A10 uses an Arrhenius factor for the calendar term", "end of life is reached at the 80 % threshold", "an unenforced rule, unthresholded", "not_identified",
          THR["wording"]["stability_table_caption"], THR["wording"]["discussion_sentence"], TLABEL, THR["wording"]["temperature_note"],
          "we do not name forms or directions of individual extracted effects, because the training design aliases laboratory with temperature and the extraction has no laboratory term"]
    for t in ok:
        assert X.banned_phrases_in(t) == [], t


def test_the_approved_section_11_sentences_of_the_preregistration_never_trip_the_check():
    lines = open(os.path.join(ROOT, "runs", "prereg", "PREREG_v4.md"), encoding="utf8").read().split("\n")
    a = next(i for i, l in enumerate(lines) if l.startswith("## 11. Outcomes"))
    b = next(i for i, l in enumerate(lines) if l.startswith("## 11a."))
    block = " ".join(lines[a:b])
    quoted = re.findall(r"\"([^\"]{40,})\"", block) + re.findall(r"'([^']{40,})'", block)                          # the quoted claim sentences and alternatives
    assert len(quoted) > 10 and any("equally simplified" in q for q in quoted)
    bad = [(q[:70], X.banned_phrases_in(q)) for q in quoted if X.banned_phrases_in(q)]
    assert bad == []
    assert X.banned_phrases_in("an equally simplified additive law") == []


def test_generated_sentences_are_checked_and_the_check_fails_closed():
    assert X.check_generated_sentences({"a": ["fine", {"b": "descriptive; not evidence that the training design identifies these forms"}]}) is True
    with pytest.raises(X.BannedWordingError, match="banned wording"):
        X.check_generated_sentences({"a": ["fine", {"b": "the extracted law recovered an Arrhenius term"}]})
    with pytest.raises(X.BannedWordingError):
        X.check_generated_sentences({"key_with_recovered": "ok", "x": ["the audit licensed the form of 2; 1 were not identified"]})      # the future-version sentence cannot be printed
    assert X.check_generated_sentences({"recovered": "ok"}) is True                                                    # dictionary keys are identifiers, not sentences


def _grid(tmp, drop=False):
    os.makedirs(tmp + "/g")
    dirs = _grid_runs(tmp + "/g")
    _with_laws(dirs, drop=drop)
    fdir, sha = _item_f_before(tmp, dirs)
    return dirs, fdir, sha


def test_the_statistics_step_refuses_a_run_whose_generated_sentences_contain_a_banned_claim(tmp_path, monkeypatch):
    tmp = str(tmp_path)
    dirs, fdir, sha = _grid(tmp)
    ok = ss.run_stats_v4(os.path.join(tmp, "ok"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    assert os.path.exists(os.path.join(tmp, "ok", "contrasts_v4_B.json")) and ok["edge_wording"]["stability"]["descriptive_only"]
    monkeypatch.setattr(stats_v4, "edge_level_wording", lambda *a, **k: {"descriptive_only": True, "note": "the extracted law recovered a power-law"})
    with pytest.raises(X.BannedWordingError):
        ss.run_stats_v4(os.path.join(tmp, "bad"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    assert not os.path.exists(os.path.join(tmp, "bad", "contrasts_v4_B.json"))                                          # nothing is written


# ------------------------------------------------------------------------------------------------ minors
def test_a_partial_grid_does_not_abort_the_descriptive_path_and_the_licence_path_stays_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "read_freeze", lambda root=None: None)
    tmp = str(tmp_path)
    dirs, fdir, sha = _grid(tmp, drop=True)                                                                           # fold 0 lacks one G15 law
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    st = out["edge_wording"]["stability"]
    assert st["status"].startswith("not available") and "expected exactly 25" in st["status"] and os.path.exists(os.path.join(tmp, "an", "contrasts_v4_B.json"))
    cdir = os.path.join(tmp, "cal")
    csha = _calibration(cdir)
    with pytest.raises(X.AuditError):                                                                                   # the licence path (future version) still requires 25 laws
        stats_v4.edge_level_wording(dirs, cdir, X.thresholds_sha256(), csha, "c" * 40, licences=True)


def test_the_stats_step_prints_temperature_only_under_its_fixed_label(tmp_path):
    tmp = str(tmp_path)
    dirs, fdir, sha = _grid(tmp)
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    rows = {r["input"]: r for r in out["edge_wording"]["stability"]["arms"]["A15"]["stability_table"]}
    assert rows["T_C"] == {"input": "T_C", "display": TLABEL, "note": "temperature and laboratory cannot be separated"} and "extracted_edge_family_counts" in rows["dod"]
