"""C26 red-team re-check (debates/D022_datasets_kan/09_redteam_fallback_recheck.md): N1 (a tripped Gate G must be reported, not blocked by the wording check), B1 (a verdict that is not a
verified calibration record licenses nothing, also in label_text and results_sentence), A4/N2/N3 (negation scope, form words and licence words need no 'extracted'), B5 (no g4 laws), N4 (stale
text), N5 (controls and physval pass through the check)."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import pytest

from pinnkan import extraction_audit as X
from pinnkan import stats_step as ss, stats_v4
from test_extraction_audit import _laws, _LL
from test_extraction_fallback import _grid

THR = X.load_thresholds()


# ------------------------------------------------------------------------------------------------ N1
def test_every_gate_g_reason_passes_the_wording_check():
    for controls in ({"positive": {"P1_G0_nrmse_leq_0p15": False}},
                     {"negative": {"nc1": {"passed": False, "runs_checked": 3}}},
                     {"negative": {"nc1": {"passed": False, "runs_checked": 3}}, "positive": {"P1_G0_nrmse_leq_0p15": False}},
                     {}):
        g = ss.gate_g(controls)
        assert X.check_generated_sentences(g, "gate_G") is True, g
    g = ss.gate_g({"positive": {"P1_G0_nrmse_leq_0p15": False}})
    assert g["tripped"] is True and g["reasons"] == ["PC-1 failed (G0 pipeline check: nRMSE > 0.15)"]


def test_a_tripped_gate_g_is_written_to_controls_and_contrasts_and_nothing_crashes(tmp_path):
    tmp = str(tmp_path)
    dirs, fdir, sha = _grid(tmp)
    tripped = ss.gate_g({"positive": {"P1_G0_nrmse_leq_0p15": False}, "negative": {"nc1": {"passed": False, "runs_checked": 5}}})
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha, gate=tripped)
    assert out["gate_G"]["tripped"] is True and os.path.exists(os.path.join(tmp, "an", "controls.json")) and os.path.exists(os.path.join(tmp, "an", "contrasts_v4_B.json"))
    written = json.load(open(os.path.join(tmp, "an", "contrasts_v4_B.json")))
    assert "PC-1 failed" in " ".join(written["gate_G"]["reasons"])


def test_a_wording_violation_writes_no_contrasts_but_leaves_controls_and_a_diagnostic(tmp_path, monkeypatch):
    tmp = str(tmp_path)
    dirs, fdir, sha = _grid(tmp)
    monkeypatch.setattr(stats_v4, "edge_level_wording", lambda *a, **k: {"descriptive_only": True, "note": "the extracted law recovered a power-law"})
    with pytest.raises(X.BannedWordingError):
        ss.run_stats_v4(os.path.join(tmp, "bad"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    assert os.path.exists(os.path.join(tmp, "bad", "controls.json")) and not os.path.exists(os.path.join(tmp, "bad", "contrasts_v4_B.json"))
    diag = json.load(open(os.path.join(tmp, "bad", "contrasts_v4_B.json.WORDING_VIOLATION.json")))
    assert diag["violations"] and "recovered" not in json.dumps(diag)                                    # the diagnostic names the path and the pattern, it does not copy the sentence


# ------------------------------------------------------------------------------------------------ B1
@pytest.mark.parametrize("fake", [{"verdict": True}, {"verdict": {"void": True}}, {"verdict": {"contribution": True}}, {"verdict": {"void": False}}, {"verdict": {"void": False, "arms": {}}},
                                  {"verdict": {"arms": {"A15": {"C1": True}}}}, {"verdict": "yes"}, {}, {"verdict": None}])
def test_a_verdict_that_is_not_a_verified_record_licenses_nothing(fake):
    assert X._licensed(fake) is False
    assert X.label_law(_laws(), calibrated=fake)["dod"]["label"] == "not_identified"


def test_a_verified_record_licenses_and_labels_carry_the_licence_that_label_text_and_results_sentence_check():
    ok = {"verdict": {"void": False, "contribution": True, "arms": {"A15": {"C1": True}}}}
    assert X._licensed(ok) is True
    lab = X.label_law(_laws(), calibrated=ok)
    assert lab["dod"]["label"] == "form" and lab["dod"]["licensed"] is True and X.label_text(lab["dod"]) == "form: linear"
    assert "Of the 5 inputs" in X.results_sentence(lab, "A15")["results"]
    unl = X.label_law(_laws())
    assert all(v["licensed"] is False for v in unl.values())
    forged = {"label": "form", "form": "linear", "sign": 1}
    with pytest.raises(X.AuditGuardError, match="B1"):
        X.label_text(forged)
    with pytest.raises(X.AuditGuardError, match="B1"):
        X.results_sentence({"dod": forged}, "A15")
    assert X.label_text(unl["dod"]) == "not identified by the audit"                                      # an unlicensed label is printable: it names no form


# ------------------------------------------------------------------------------------------------ A4 / N2 / N3
@pytest.mark.parametrize("claim", [
    "the extracted law is not linear but shows an Arrhenius dependence",                       # N2: a negation elsewhere does not exempt
    "the extracted law is a power law, not a hinge",
    "the extracted law, with no tie, is quadratic",
    "the fitted equation follows a power law in C_ch",                                         # N3: no 'extracted' needed
    "the PINN-KAN shows an Arrhenius dependence on temperature",
    "the learned law is exponential in c_ch",
    "the extracted law licensed the form of 3 inputs",
    "calibration C1 passed with upper limit 0.12",
    "the calibration design is fixed by the frozen commit",
    "the licence of the form was granted",
    "The extraction audit did not meet its pre-set calibration condition, so it is reported as a description, not as a method result.",
    "Of the 5 inputs of the extracted KAN law, the audit licensed the form of 2 and the sign of 1; 1 were not identified and 1 were not retained by the extraction.",
])
def test_the_closed_holes_n2_and_n3(claim):
    assert X.banned_phrases_in(claim), claim


def test_negated_form_words_and_the_approved_sentences_are_still_not_claims():
    ok = ["the extracted law is not exponential in C_ch", "the extracted law has no hinge", "the extracted law does not show an Arrhenius dependence",
          "the extracted law cannot represent the non-monotone SOC dependence reported by the dataset authors", "a threshold of 0.15 on the nRMSE of the G0 check",
          THR["wording"]["stability_table_caption"], THR["wording"]["discussion_sentence"], "PC-1 failed (G0 pipeline check: nRMSE > 0.15)", "NC-1 tripped"]
    for t in ok:
        assert X.banned_phrases_in(t) == [], t


def test_the_licensed_branch_with_every_arm_failing_c1_still_trips_the_check():
    failing = {"failure_sentences": [THR["future_version_wording"]["failure"][k] for k in ("calibration", "usefulness", "necessity")]}
    with pytest.raises(X.BannedWordingError):
        X.check_generated_sentences({"edge_wording": failing}, "contrasts_v4_B")


# ------------------------------------------------------------------------------------------------ B5
def test_a_grid_whose_extracted_laws_are_not_at_g4_does_not_abort_the_descriptive_path(tmp_path):
    tmp = str(tmp_path)
    dirs, fdir, sha = _grid(tmp)
    for d in dirs:                                                                                           # laws files exist but none belongs to an m = 32 run
        cfg = json.load(open(os.path.join(d, "config.json")))
        if cfg["m"] == 32:
            os.remove(os.path.join(d, "extracted_laws.json"))
        else:
            json.dump({"m": cfg["m"], "fold": cfg["fold"], "laws": []}, open(os.path.join(d, "extracted_laws.json"), "w"))
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    assert out["edge_wording"]["stability"]["status"].startswith("not available") and "no extracted laws" in out["edge_wording"]["stability"]["status"]
    assert os.path.exists(os.path.join(tmp, "an", "contrasts_v4_B.json"))


# ------------------------------------------------------------------------------------------------ N4 / N5
def test_stale_text_is_gone():
    src = open(os.path.join(ROOT, "code", "pinnkan", "stats_step.py"), encoding="utf8").read()
    assert "no calibration table supplied" not in src and "without it no edge-level wording is printed" not in src and "recovery nRMSE" not in src


def test_controls_and_physval_outputs_pass_through_the_check(tmp_path):
    p = str(tmp_path / "c.json")
    ss.write_checked_json(p, {"note": "G0 pipeline check passed"}, "controls")
    assert json.load(open(p)) == {"note": "G0 pipeline check passed"}
    q = str(tmp_path / "bad.json")
    with pytest.raises(X.BannedWordingError):
        ss.write_checked_json(q, {"note": "the KAN recovers the dependence"}, "physval_11a")
    assert not os.path.exists(q) and os.path.exists(q + ".WORDING_VIOLATION.json")
