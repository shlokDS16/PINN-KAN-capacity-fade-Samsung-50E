"""Queue items 6 and 7 (red-team re-check N2, N5): the banned-wording gaps (';' and ':' splits, 'not unlike', double negation, formulas such as exp(-b/T)) and the physval check on the
Design R2 statistics path (run_stats_v4 and its CLI)."""
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import pytest

from pinnkan import extraction_audit as X
from pinnkan import physval, semi, stats_step as ss
from test_extraction_fallback import _grid
from test_pk_build2_stats import _sf

THR = X.load_thresholds()


# ------------------------------------------------------------------------------------------------ N2
@pytest.mark.parametrize("claim", [
    "the extracted law: it is exponential in C_ch",                       # the law and the claim sit on two sides of a colon
    "the extracted law is stated; it is quadratic in dod",                  # ... of a semicolon
    "the fitted equation holds; a power law in C_ch",
    "the extracted law is not unlike an exponential",                       # double negation
    "the extracted law is not without a hinge",
    "the extracted law follows exp(-b/T)",                                  # formulas
    "the rate follows exp(-b/T)",                                           # an Arrhenius-type formula in any sentence
    "the extracted law is c * exp(-3 x)",
    "the fitted law is x^2 in dod",
    "the learned equation is a/T",
])
def test_the_n2_gaps_are_closed(claim):
    assert X.banned_phrases_in(claim), claim


def test_single_negations_clause_breaks_and_the_approved_sentences_still_pass():
    ok = ["the extracted law is not exponential", "the extracted law has no hinge", "the extracted law has no hinge, not even a quadratic term",
          "the extracted law does not show an Arrhenius dependence", "100 (1 - exp(-median L)) in the direction stated by the sentence",
          "the extracted law cannot represent the non-monotone SOC dependence reported by the dataset authors", "G0 pipeline check: nRMSE below 0.15; extraction runs on the training side",
          THR["wording"]["stability_table_caption"], THR["wording"]["discussion_sentence"], "PC-1 failed (G0 pipeline check: nRMSE > 0.15)"]
    for t in ok:
        assert X.banned_phrases_in(t) == [], t
    assert X.banned_phrases_in("the extracted law is not exponential; it is quadratic")                  # a negation in the first clause does not exempt the second


def test_a_semicolon_no_longer_hides_the_form_claim_in_generated_output():
    with pytest.raises(X.BannedWordingError):
        X.check_generated_sentences({"note": "the extracted law is stated: it is exponential in C_ch"}, "contrasts")
    assert X.check_generated_sentences({"note": "descriptive; not evidence that the training design identifies these forms"}) is True


# ------------------------------------------------------------------------------------------------ N5
def _with_stress_functions(dirs, tmp_path):
    src = _sf(tmp_path, "sf_src")
    for d in dirs:
        if json.load(open(os.path.join(d, "config.json")))["m"] == 32:
            shutil.copy(os.path.join(src, "stress_functions.json"), d)
            shutil.copy(os.path.join(src, "superposition.csv"), d)


def test_run_stats_v4_writes_physval_through_the_wording_check(tmp_path, monkeypatch):
    monkeypatch.setitem(semi.A10_FORM, "verified", False)
    tmp = str(tmp_path)
    dirs, fdir, sha = _grid(tmp)
    _with_stress_functions(dirs, tmp_path)
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha, physval=True)
    assert out["physval"] == {"status": "written", "file": "physval_11a.json", "n_runs": 5}                 # the five m = 32 runs, one per outer fold
    pv = json.load(open(os.path.join(tmp, "an", "physval_11a.json")))
    assert pv["n_runs"] == 5 and X.check_generated_sentences(pv, "physval_11a") is True and pv["item5"]["directions"]["c_ch"]["n_members"] == 15


def test_physval_is_off_by_default_and_not_available_without_stress_functions(tmp_path):
    tmp = str(tmp_path)
    dirs, fdir, sha = _grid(tmp)
    out = ss.run_stats_v4(os.path.join(tmp, "a"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    assert "physval" not in out and not os.path.exists(os.path.join(tmp, "a", "physval_11a.json"))
    out = ss.run_stats_v4(os.path.join(tmp, "b"), dirs, item_f_dir=fdir, item_f_sha256=sha, physval=True)
    assert out["physval"]["status"].startswith("not available") and not os.path.exists(os.path.join(tmp, "b", "physval_11a.json"))


def test_a_banned_sentence_in_the_physval_output_stops_the_r2_step_and_leaves_a_diagnostic(tmp_path, monkeypatch):
    monkeypatch.setitem(semi.A10_FORM, "verified", False)
    tmp = str(tmp_path)
    dirs, fdir, sha = _grid(tmp)
    _with_stress_functions(dirs, tmp_path)
    real = physval.physval_11a
    monkeypatch.setattr(physval, "physval_11a", lambda *a, **k: {**real(*a, **k), "note": "the extracted law is exponential in C_ch"})
    with pytest.raises(X.BannedWordingError):
        ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha, physval=True)
    an = os.path.join(tmp, "an")
    assert not os.path.exists(os.path.join(an, "physval_11a.json")) and os.path.exists(os.path.join(an, "physval_11a.json.WORDING_VIOLATION.json"))
    assert not os.path.exists(os.path.join(an, "contrasts_v4_B.json"))                                       # fail closed: the contrasts are not written either


def test_the_cli_r2_path_forwards_physval(tmp_path, monkeypatch):
    monkeypatch.setitem(semi.A10_FORM, "verified", False)
    tmp = str(tmp_path)
    dirs, fdir, sha = _grid(tmp)
    _with_stress_functions(dirs, tmp_path)
    ss.main(["--analysis-dir", os.path.join(tmp, "cli"), "--runs", "B=" + ",".join(dirs), "--design", "r2", "--item-f-dir", fdir, "--item-f-sha256", sha, "--physval"])
    assert os.path.exists(os.path.join(tmp, "cli", "physval_11a.json")) and os.path.exists(os.path.join(tmp, "cli", "contrasts_v4_B.json"))
