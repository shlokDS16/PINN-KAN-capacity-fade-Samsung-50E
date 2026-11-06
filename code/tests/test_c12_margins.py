"""C12: pooled pp-scale margins per contrast and grid cell (PREREG_v4 9.2, 9.10; margins.pooled_margins and its wiring into the statistics step)."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

from pinnkan import margins as mg
from pinnkan import stats_step as ss
from test_pk_v2_review import _grid_runs, _item_f_before

ARMS = ["A1", "A9", "A11", "A4", "A2", "A10", "A10P", "A13", "A15", "G15"]


def _E(arm, m, f):
    """a distinct, known inner-CV score per (arm, m, fold)"""
    return 1.0 + 0.1 * ARMS.index(arm) + 0.01 * m + 0.001 * f


def _add_inputs(dirs, n_test=None, dstar=None, drop=None, nonfinite=None, order_ok=True):
    """margins_inputs.json (+ comparators score) in every run of a fake grid, written exactly as run.py does (per_arm_E_by_fold: {E_<arm>: [[n_test, inner_cv_pp]]})"""
    for d in dirs:
        cfg = json.load(open(os.path.join(d, "config.json")))
        m, f = cfg["m"], cfg["fold"]
        nt = (n_test or {}).get((m, f), 8)
        sel = (dstar or {}).get(f, "A9")
        contr = {f"E_{a}": [[nt, _E(a, m, f)]] for a in ARMS if not (drop and (m, f, a) == drop)}
        if nonfinite and nonfinite[:2] == (m, f):
            contr[f"E_{nonfinite[2]}"] = [[nt, float("nan")]]
        json.dump({"per_arm_E_by_fold": contr}, open(os.path.join(d, "margins_inputs.json"), "w"))
        json.dump({"D*": {"arm": sel, "score": _E(sel, m, f), "complete": True}, "AG": {"arm": "A4", "score": _E("A4", m, f), "complete": True}}, open(os.path.join(d, "comparators.json"), "w"))
        t = os.path.getmtime(os.path.join(d, "condition_scores.json")) + (100 if not order_ok else -100)          # run.py writes margins_inputs.json before any condition_scores file
        os.utime(os.path.join(d, "margins_inputs.json"), (t, t))


def _grid(tmp, **kw):
    os.makedirs(tmp)
    dirs = _grid_runs(tmp)
    _add_inputs(dirs, **kw)
    return dirs


def test_E_is_pooled_by_test_condition_count_and_the_margins_are_2_and_10_percent_of_it(tmp_path):
    n_test = {(8, 0): 4, (8, 1): 8, (8, 2): 8, (8, 3): 8, (8, 4): 12}
    dirs = _grid(str(tmp_path / "g"), n_test=n_test)
    rec = mg.pooled_margins(dirs)
    row = rec["contrasts"]["A1 vs A2"]["m8_k2"]
    pairs = [(n_test[(8, f)], _E("A2", 8, f)) for f in range(5)]
    E = sum(n * e for n, e in pairs) / sum(n for n, _ in pairs)
    assert row["E_pp"] == pytest.approx(E) and row["delta_S_pp"] == pytest.approx(0.02 * E) and row["delta_N_pp"] == pytest.approx(0.10 * E)
    assert [p["n_test_conditions"] for p in row["per_fold"]] == [4, 8, 8, 8, 12] and row["log_margin_S"] == pytest.approx(np.log(1.02)) and row["log_margin_N"] == pytest.approx(-np.log(1.10))
    assert row["sensitivity"]["delta_S_pp"] == {"0.0": 0.0, "0.05": pytest.approx(0.05 * E)} and row["sensitivity"]["delta_N_pp"] == {"0.05": pytest.approx(0.05 * E), "0.15": pytest.approx(0.15 * E)}


def test_every_contrast_is_formed_at_every_grid_cell_where_it_exists_and_the_k_cells_share_E(tmp_path):
    rec = mg.pooled_margins(_grid(str(tmp_path / "g")))
    cells = {c for v in rec["contrasts"].values() for c in v}
    assert cells == {f"m{m}_k{k}" for m in (8, 16, 32) for k in ("0", "2", "full")}
    assert set(rec["contrasts"]) == {"A1 vs D*", "A1 vs A9", "A1 vs AG", "A1 vs A2", "A1 vs A10", "A1 vs A10P", "A1 vs A13", "A15 vs A1", "A15 vs G15"}
    r = rec["contrasts"]["A1 vs A9"]
    assert r["m8_k0"]["E_pp"] == r["m8_k2"]["E_pp"] == r["m8_kfull"]["E_pp"] != r["m16_k2"]["E_pp"]
    assert rec["named"]["K1"]["margin"]["E_pp"] == rec["contrasts"]["A15 vs A1"]["m32_kfull"]["E_pp"] and rec["named"]["P1"]["cell"] == [8, "2"]
    assert all(rec["named"][n]["margin"] is not None for n in ("P1", "P2", "K1", "K2", "QA10_g1", "QA10P_g4", "QH_g4", "QT_g1"))


def test_k_full_2_has_two_k_cells(tmp_path):
    d = str(tmp_path / "g")
    os.makedirs(d)
    dirs = _grid_runs(d, k_full=2)
    _add_inputs(dirs)
    rec = mg.pooled_margins(dirs)
    assert {c for v in rec["contrasts"].values() for c in v} == {f"m{m}_k{k}" for m in (8, 16, 32) for k in ("0", "full")}


def test_D_star_uses_the_arm_selected_in_each_fold_and_its_own_E(tmp_path):
    sel = {0: "A9", 1: "A11", 2: "A9", 3: "A11", 4: "A11"}
    rec = mg.pooled_margins(_grid(str(tmp_path / "g"), dstar=sel))
    row = rec["contrasts"]["A1 vs D*"]["m16_k2"]
    assert [p["comparator_arm"] for p in row["per_fold"]] == [sel[f] for f in range(5)]
    assert row["E_pp"] == pytest.approx(np.mean([_E(sel[f], 16, f) for f in range(5)]))
    assert rec["contrasts"]["A1 vs AG"]["m8_k2"]["per_fold"][0]["comparator_arm"] == "A4"


def test_a_comparator_missing_in_one_fold_a_missing_fold_and_a_mismatched_selector_refuse(tmp_path):
    with pytest.raises(mg.MarginsError, match="pool a subset"):
        mg.pooled_margins(_grid(str(tmp_path / "a"), drop=(16, 2, "A2")))
    dirs = _grid(str(tmp_path / "b"))
    with pytest.raises(mg.MarginsError, match="folds"):
        mg.pooled_margins([d for d in dirs if "f4_m32" not in d])
    dirs = _grid(str(tmp_path / "c"))
    p = os.path.join(dirs[0], "comparators.json")
    c = json.load(open(p))
    c["D*"]["score"] += 1.0
    json.dump(c, open(p, "w"))
    with pytest.raises(mg.MarginsError, match="selector"):
        mg.pooled_margins(dirs)
    with pytest.raises(mg.MarginsError, match="two runs"):
        mg.pooled_margins(dirs + [dirs[0]])


def test_margins_inputs_written_after_a_score_file_is_refused_when_strict(tmp_path):
    dirs = _grid(str(tmp_path / "g"), order_ok=False)
    with pytest.raises(mg.MarginsError, match="newer than a condition-scores file"):
        mg.pooled_margins(dirs)
    assert mg.pooled_margins(dirs, strict=False)["sha256"]


def test_a_non_finite_inner_score_gives_no_margin_not_a_number(tmp_path):
    rec = mg.pooled_margins(_grid(str(tmp_path / "g"), nonfinite=(8, 3, "A2")))
    row = rec["contrasts"]["A1 vs A2"]["m8_k2"]
    assert row["E_pp"] is None and row["delta_S_pp"] is None and "non-finite" in row["note"]
    assert rec["contrasts"]["A1 vs A2"]["m16_k2"]["E_pp"] is not None
    assert mg.tier_pp(5.0, None, None) is None
    json.dumps(rec)


def test_the_hash_is_stable_follows_the_inputs_and_the_cli_writes_the_file(tmp_path):
    dirs = _grid(str(tmp_path / "g"))
    h1, h2 = mg.pooled_margins(dirs)["sha256"], mg.pooled_margins(dirs)["sha256"]
    out = str(tmp_path / "margins.json")
    mg.main(["--runs", ",".join(dirs), "--out", out])
    assert h1 == h2 == json.load(open(out))["sha256"]
    p = os.path.join(dirs[3], "margins_inputs.json")
    mi = json.load(open(p))
    mi["per_arm_E_by_fold"]["E_A2"][0][1] += 0.5
    t = os.path.getmtime(p)
    json.dump(mi, open(p, "w"))
    os.utime(p, (t, t))
    assert mg.pooled_margins(dirs)["sha256"] != h1


def test_tier_pp_compares_the_lower_bound_with_the_pp_margins():
    assert mg.tier_pp(0.5, 0.2, 1.0) == "S" and mg.tier_pp(0.1, 0.2, 1.0) == "N" and mg.tier_pp(-0.5, 0.2, 1.0) == "N" and mg.tier_pp(-1.5, 0.2, 1.0) == "-"


def test_the_real_runner_writes_inputs_in_the_shape_the_pooling_reads():
    src = open(os.path.join(ROOT, "code", "pinnkan", "run.py"), encoding="utf8").read()
    assert 'contr = {f"E_{a}": [[n_test, inner[a]["inner_cv_pp"]]] for a in arms}' in src and '"per_arm_E_by_fold": contr' in src


def test_the_statistics_step_forms_the_margins_attaches_them_to_the_estimated_rows_and_records_the_named_tiers(tmp_path):
    tmp = str(tmp_path)
    dirs = _grid(tmp + "/g")
    fdir, sha = _item_f_before(tmp, dirs)
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    assert out["margins_pp"]["status"] == "formed" and os.path.exists(os.path.join(tmp, "an", "margins.json"))
    assert json.load(open(os.path.join(tmp, "an", "margins.json")))["sha256"] == out["margins_pp"]["sha256"]
    rows = out["estimated"]["rows"]
    r = next(r for r in rows if r["comparator"] == "A2" and r["cell"] == [8, "2"])
    assert r["pp_margin"]["E_pp"] == pytest.approx(np.mean([_E("A2", 8, f) for f in range(5)])) and r["tier_pp"] in ("S", "N", "-")
    assert all("pp_margin" in r for r in rows)
    nm = out["margins_pp"]["named_tier_pp"]
    assert {"P1", "P2", "K1", "K2", "QH_g1", "QT_g1"} <= set(nm) and nm["K1"]["delta_S_pp"] == pytest.approx(0.02 * nm["K1"]["E_pp"])


def test_without_margins_inputs_the_step_says_not_available_and_a_mixture_is_refused(tmp_path):
    tmp = str(tmp_path)
    os.makedirs(tmp + "/g")
    dirs = _grid_runs(tmp + "/g")
    fdir, sha = _item_f_before(tmp, dirs)
    out = ss.run_stats_v4(os.path.join(tmp, "an"), dirs, item_f_dir=fdir, item_f_sha256=sha)
    assert out["margins_pp"]["status"].startswith("not available") and not os.path.exists(os.path.join(tmp, "an", "margins.json"))
    _add_inputs(dirs[:3])
    with pytest.raises(mg.MarginsError, match="some runs"):
        ss.run_stats_v4(os.path.join(tmp, "an2"), dirs, item_f_dir=fdir, item_f_sha256=sha)
