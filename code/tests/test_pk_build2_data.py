"""build_v1 section 7: consecutive-file incident drops, the ZYK throughput branch (synthetic ZYK-format files), include_at / include_storage_0406 / min_fc_points,
law overrides (sensitivity rows (l), (m)), the guard default. Synthetic data only: no Samsung retention value is read."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pandas as pd
import pytest

from pinnkan import data as D
from pinnkan import guard, law, zyk
from data import samsung_checkups as SC


# ------------------------------------------------------------------------------------------------ helpers
def _checkups_rows(serial, stage, typ, files, lab="HM", dod=0.4, q0=4.8, fph=1.0, cell_no=1, tp=1, T=23.0):
    """rows of the pipeline table for one cell; files = [(file_idx, kind)]; capacity falls 0.002 Ah per row; analytic EFC = 10 per file index step of 2 (days = 7 * rank)"""
    rows = []
    for r, (idx, kind) in enumerate(files):
        rows.append(dict(cell_id=f"{serial}_s{stage}", serial=serial, type=typ, lab=lab, tp=tp, cell=cell_no, stage=stage, T_C=T, SOC_max=0.8, DoD=dod, C_ch=0.5, C_dch=1.0,
                         kind=kind, file_idx=idx, elapsed_days=7.0 * r, q_mean_ah=q0 - 0.002 * r, qc_pass=True,
                         efc_est_cum=(10.0 * r if typ == "z" else np.nan)))
    return rows


def _write_root(tmp_path, rows):
    p = tmp_path / "data" / "processed"
    p.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(p / "samsung_checkups.csv", index=False)
    return str(tmp_path)


def _write_zyk_csv(path, discharge_a=4.9, discharge_h=0.5, charge_a=2.45, charge_h=1.0, dt=10.0, start_h=26, gap_after_s=None):
    """a ZYK-format segment: run_time 'HH:MM:SS.sss' (hours > 24, leading blanks as in the CU files), c_vol, c_cur (negative on discharge), temps, step_type"""
    t0 = start_h * 3600.0
    n_c, n_d = int(charge_h * 3600 / dt), int(discharge_h * 3600 / dt)
    t = t0 + dt * np.arange(n_c + n_d + 1)
    cur = np.concatenate([np.full(n_c + 1, charge_a), np.full(n_d, -discharge_a)])
    if gap_after_s is not None:
        t[n_c + 1:] += gap_after_s
    def fmt(x):
        h, rem = divmod(x, 3600.0)
        m, s = divmod(rem, 60.0)
        return " %02d:%02d:%06.3f" % (h, m, s)
    pd.DataFrame({"run_time": [fmt(x) for x in t], "c_vol": 3.7, "c_cur": cur, "c_surf_temp": 24.0, "amb_temp": 23.0, "step_type": np.where(cur > 0, 21, 22)}).to_csv(path, index=False)


# ------------------------------------------------------------------------------------------------ guard
def test_guard_default_is_prereg_v3():
    assert guard.PREREG_DEFAULT.endswith("PREREG_v3.md")
    assert os.path.isfile(os.path.join(ROOT, guard.PREREG_DEFAULT))


# ------------------------------------------------------------------------------------------------ consecutive incident drops
def test_consecutive_incident_rule_drops_later_files_only():
    ser = ["TP_z24_01"] * 4 + ["TP_z17_01"] * 3 + ["TP_z17_03"] * 2 + ["TP_z05_01"] * 2 + ["TP_z25_01"] * 3
    idx = [1, 3, 5, 7] + [17, 19, 21] + [18, 19] + [1, 9] + [3, 5, 7]
    df = pd.DataFrame({"serial": ser, "file_idx": idx})
    m = D.consecutive_drop_mask(df)
    dropped = list(zip(np.array(ser)[m], np.array(idx)[m]))
    # TP_z24_01: segment 2 -> every check-up after it; TP_z17 (all cells): from segment 18 -> file numbers > 18; TP_z25_01 segment 4 -> 5, 7 dropped, 3 kept
    assert [d for d in dropped if d[0] == "TP_z24_01"] == [("TP_z24_01", 3), ("TP_z24_01", 5), ("TP_z24_01", 7)]
    assert sorted(d for d in dropped if d[0].startswith("TP_z17")) == [("TP_z17_01", 19), ("TP_z17_01", 21), ("TP_z17_03", 19)]
    assert [d for d in dropped if d[0] == "TP_z25_01"] == [("TP_z25_01", 5), ("TP_z25_01", 7)]
    assert not any(d[0] == "TP_z05_01" for d in dropped)
    assert D.INCIDENT_CONSECUTIVE_DROPS_IMPLEMENTED is True


def test_consecutive_rule_matches_serial_prefix_not_substring():
    df = pd.DataFrame({"serial": ["TP_z170_01", "TP_z17_02"], "file_idx": [30, 30]})
    assert D.consecutive_drop_mask(df).tolist() == [False, True]


def test_loader_applies_consecutive_drops_and_counts_them(tmp_path):
    rows = (_checkups_rows("TP_z24_01", 1, "z", [(3, "CU"), (5, "CU"), (7, "exCU"), (9, "CU")])
            + _checkups_rows("TP_z07_03", 1, "z", [(3, "CU"), (5, "CU"), (15, "CU"), (17, "CU"), (19, "CU")], cell_no=3, tp=7)
            + _checkups_rows("TP_z05_01", 1, "z", [(3, "CU"), (5, "CU"), (17, "CU")], cell_no=1, tp=5))
    root = _write_root(tmp_path, rows)
    cells = {c.cell_id: c for c in D._load_samsung(root)}
    assert "TP_z24_01_s1" not in cells                                  # segment 02 is bad: every check-up after it is dropped, nothing is left
    assert cells["TP_z07_03_s1"].n == 3 and cells["TP_z05_01_s1"].n == 3     # files 17 and 19 follow the bad segment 16 of TP_z07_03; TP_z05_01 has no incident
    assert cells["TP_z05_01_s1"].meta["n_consecutive_incident_rows_dropped"] == 4 + 2
    off = {c.cell_id for c in D._load_samsung(root, drop_incidents=False)}
    assert "TP_z24_01_s1" in off                                        # the rule is part of drop_incidents


# ------------------------------------------------------------------------------------------------ ZYK segment files
def test_zyk_segment_integral_matches_the_designed_cycle(tmp_path):
    p = tmp_path / "TP_z10_01_02_ZYK.csv"
    _write_zyk_csv(p, discharge_a=4.9, discharge_h=0.5, charge_a=2.45, charge_h=1.0)
    r = zyk.read_zyk_segment(str(p))
    assert r["discharge_ah"] == pytest.approx(2.45, rel=5e-3)          # 4.9 A for 0.5 h
    assert r["charge_ah"] == pytest.approx(2.45, rel=5e-3)             # 2.45 A for 1 h
    assert r["efc"] == pytest.approx(2.45 / 4.9, rel=5e-3)             # = 0.5 equivalent full cycles (one half-depth cycle)
    assert r["complete"] and "sampling_gap" not in r["flags"]
    assert r["hours"] == pytest.approx(1.5, rel=1e-3)                  # hours > 24 in run_time are parsed


def test_zyk_constants_agree_with_the_pipeline():
    assert zyk.Q_NOM_AH == SC.Q_NOM_AH


def test_zyk_gap_makes_a_segment_incomplete_and_bad_file_is_a_flag(tmp_path):
    p = tmp_path / "TP_z10_01_04_ZYK.csv"
    _write_zyk_csv(p, gap_after_s=3 * 3600.0)
    r = zyk.read_zyk_segment(str(p))
    assert not r["complete"] and "sampling_gap" in r["flags"]
    bad = tmp_path / "TP_z10_01_06_ZYK.csv"
    bad.write_text("not,a,zyk\n1,2,3\n")
    rb = zyk.read_zyk_segment(str(bad))
    assert not rb["complete"] and rb["flags"].startswith("read_error")


def test_build_zyk_table_marks_files_named_by_the_member_list_but_absent(tmp_path):
    f = tmp_path / "TP_z10_01__f1"
    f.mkdir()
    _write_zyk_csv(f / "TP_z10_01_02_ZYK.csv")
    t = zyk.build_zyk_table({"TP_z10_01_s1": str(f)}, {"TP_z10_01_s1": {2, 4}})
    assert sorted(t["file_idx"]) == [2, 4]
    r4 = t[t.file_idx == 4].iloc[0]
    assert (not r4["complete"]) and r4["flags"] == "missing_file" and np.isnan(r4["efc"])
    assert set(t.columns) == set(zyk.TABLE_COLS)


# ------------------------------------------------------------------------------------------------ cumulative throughput and fallback
def _table(cell_id, efcs, complete=None):
    complete = complete or [True] * len(efcs)
    return pd.DataFrame([dict(cell_id=cell_id, serial=cell_id.split("_s")[0], file_idx=2 + 2 * i, discharge_ah=e * 4.9, charge_ah=e * 4.9, efc=e, hours=1.0, dt_max_s=10.0, n_rows=100,
                              complete=c, flags="") for i, (e, c) in enumerate(zip(efcs, complete))], columns=zyk.TABLE_COLS)


def test_cumulative_efc_is_the_sum_of_segments_before_each_checkup():
    rows = _checkups_rows("TP_z10_01", 1, "z", [(1, "ET"), (3, "CU"), (5, "CU"), (7, "exCU"), (9, "CU")])
    df = pd.DataFrame(rows)
    out = zyk.attach_zyk_cumulative(df, _table("TP_z10_01_s1", [3.0, 4.0, 5.0, 6.0]))
    assert out["efc_zyk_cum"].tolist() == [0.0, 3.0, 7.0, 12.0, 18.0]            # segments 02, 04, 06, 08 lie before check-ups 03, 05, 07, 09
    assert set(out["zyk_interval_source"]) == {"logged"}


def test_incomplete_segment_takes_the_designed_throughput_for_that_interval():
    df = pd.DataFrame(_checkups_rows("TP_z10_01", 1, "z", [(1, "ET"), (3, "CU"), (5, "CU"), (7, "exCU")]))      # analytic cum: 0, 10, 20, 30
    out = zyk.attach_zyk_cumulative(df, _table("TP_z10_01_s1", [3.0, 4.0, 5.0], complete=[True, False, True]))
    assert out["efc_zyk_cum"].tolist() == [0.0, 3.0, 13.0, 18.0]               # interval (3,5) holds the incomplete segment 04: analytic 20 - 10 = 10
    assert out["zyk_interval_source"].tolist()[1:] == ["logged", "analytic_fallback", "logged"]


def test_cycling_cell_without_zyk_entries_raises_unless_the_flag_is_set():
    df = pd.DataFrame(_checkups_rows("TP_z10_01", 1, "z", [(1, "ET"), (3, "CU"), (5, "CU")]))
    with pytest.raises(zyk.ZykDataMissing):
        zyk.attach_zyk_cumulative(df, _table("OTHER_s1", [1.0]))
    out = zyk.attach_zyk_cumulative(df, _table("OTHER_s1", [1.0]), fallback="analytic")
    assert out["efc_zyk_cum"].tolist() == [0.0, 10.0, 20.0] and set(out["zyk_interval_source"]) == {"cell_analytic"}
    with pytest.raises(ValueError):
        zyk.attach_zyk_cumulative(df, _table("OTHER_s1", [1.0]), fallback="guess")


def test_storage_cells_are_untouched_by_the_zyk_branch():
    st = pd.DataFrame(_checkups_rows("TP_k03_01", 2, "k", [(1, "ET"), (3, "CU"), (5, "CU")]))
    out = zyk.attach_zyk_cumulative(st, zyk.pd.DataFrame(columns=zyk.TABLE_COLS))
    assert (out["efc_zyk_cum"] == 0.0).all()


def test_missing_table_is_a_clear_error(tmp_path):
    with pytest.raises(zyk.ZykDataMissing, match="not downloaded/parsed yet"):
        zyk.load_zyk_table(str(tmp_path))
    rows = _checkups_rows("TP_z10_01", 1, "z", [(1, "ET"), (3, "CU"), (5, "CU"), (7, "CU")])
    root = _write_root(tmp_path, rows)
    with pytest.raises(zyk.ZykDataMissing):
        D._load_samsung(root, throughput="zyk")


def test_loader_zyk_branch_end_to_end_on_a_synthetic_root(tmp_path):
    rows = _checkups_rows("TP_z10_01", 1, "z", [(1, "ET"), (3, "CU"), (5, "CU"), (7, "exCU"), (9, "CU")]) + _checkups_rows("TP_k03_01", 2, "k", [(1, "ET"), (3, "CU"), (5, "CU"), (7, "CU")], cell_no=1)
    root = _write_root(tmp_path, rows)
    _table("TP_z10_01_s1", [3.0, 4.0, 5.0, 6.0]).to_csv(tmp_path / "data" / "processed" / "samsung_zyk_efc.csv", index=False)
    z = {c.cell_id: c for c in D._load_samsung(root, throughput="zyk")}
    a = {c.cell_id: c for c in D._load_samsung(root, throughput="analytic")}
    # every analysed cell has an ET row here, so the reference is ET (file 01); EFC at 03, 05, 07, 09 = 3, 3+4, 3+4+5, 3+4+5+6
    np.testing.assert_allclose(z["TP_z10_01_s1"].efc, [0.0, 3.0, 7.0, 12.0, 18.0])
    np.testing.assert_allclose(a["TP_z10_01_s1"].efc, [0.0, 10.0, 20.0, 30.0, 40.0])
    assert np.all(z["TP_k03_01_s2"].efc == 0.0)                                     # storage: no throughput
    assert z["TP_z10_01_s1"].meta["throughput_source"] == "zyk" and z["TP_z10_01_s1"].meta["zyk_intervals"]["logged"] == 5


def test_unfiltered_rows_count_segments_before_dropped_checkups(tmp_path):
    rows = _checkups_rows("TP_z10_01", 1, "z", [(1, "ET"), (3, "CU"), (5, "CU"), (7, "CU")])
    rows[2]["qc_pass"] = False                                                      # check-up 05 fails QC: its segment still counts in the interval to 07
    root = _write_root(tmp_path, rows)
    _table("TP_z10_01_s1", [3.0, 4.0, 5.0]).to_csv(tmp_path / "data" / "processed" / "samsung_zyk_efc.csv", index=False)
    c = D._load_samsung(root, throughput="zyk")[0]
    np.testing.assert_allclose(c.efc, [0.0, 3.0, 3.0 + 4.0 + 5.0])               # retained rows: ET, 03, 07


# ------------------------------------------------------------------------------------------------ FB-5 validation rule
def _validation_table(rel_by_cell, labs, dods, n=5):
    rows = []
    for i, rel in enumerate(rel_by_cell):
        for k in range(n):
            rows.append(dict(cell_id=f"c{i}", type="z", kind="CU", file_idx=3 + 2 * k, lab=labs[i], DoD=dods[i], efc_est_cum=100.0 * k * (1 + rel), efc_zyk_cum=100.0 * k,
                             zyk_interval_source="logged"))
    return pd.DataFrame(rows)


def test_validation_accepts_when_close_and_covered():
    labs = ["HM", "HM", "INT", "INT", "SIE", "SIE"]
    dods = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
    r = zyk.validate_throughput(_validation_table([0.01, 0.02, 0.03, 0.01, 0.02, 0.04], labs, dods))
    assert r["accept_analytic"] and r["coverage_ok"] and r["median_abs_rel_diff"] <= 0.05


def test_validation_rejects_large_median_a_cell_over_10pct_or_short_coverage():
    labs = ["HM", "HM", "INT", "INT"]
    dods = [0.1] * 4
    assert not zyk.validate_throughput(_validation_table([0.08, 0.09, 0.07, 0.08], labs, dods))["accept_analytic"]            # median 8 % > 5 %
    r = zyk.validate_throughput(_validation_table([0.01, 0.01, 0.01, 0.12], labs, dods))
    assert not r["accept_analytic"] and r["cells_over_last_tol"] == ["c3"]                                                    # one cell above 10 % at its last check-up
    r = zyk.validate_throughput(_validation_table([0.01, 0.01, 0.01], ["HM", "HM", "INT"], [0.1, 0.1, 0.1]))
    assert not r["accept_analytic"] and not r["coverage_ok"] and "class0|INT" in r["short_cells"]                              # one INT cell in the class only
    assert zyk.validate_throughput(pd.DataFrame(columns=["cell_id", "type", "kind", "file_idx", "lab", "DoD", "efc_est_cum", "efc_zyk_cum", "zyk_interval_source"]))["n_cells"] == 0


def test_validate_from_root_uses_only_cells_in_the_zyk_table(tmp_path):
    rows = []
    for k, (ser, lab) in enumerate([("TP_z10_01", "HM"), ("TP_z10_02", "HM"), ("TP_z11_01", "INT")]):
        rows += _checkups_rows(ser, 1, "z", [(1, "ET"), (3, "CU"), (5, "CU"), (7, "CU")], lab=lab, dod=0.1, cell_no=k + 1)
    root = _write_root(tmp_path, rows)
    t = pd.concat([_table("TP_z10_01_s1", [10.0, 10.0, 10.0]), _table("TP_z10_02_s1", [10.4, 10.0, 9.8])])       # the INT cell has no ZYK files yet
    t.to_csv(tmp_path / "data" / "processed" / "samsung_zyk_efc.csv", index=False)
    r = zyk.validate_from_root(root)
    assert r["n_cells"] == 2 and r["accept_analytic"] and r["worst_last_checkup_rel_diff"] < 0.02
    assert r["cells_per_class_lab"] == {"class0|HM": 2}


def test_dod_classes_use_the_registered_edges():
    assert [zyk.dod_class(x) for x in (0.05, 0.15, 0.2, 0.35, 0.6)] == [0, 0, 1, 1, 2]


# ------------------------------------------------------------------------------------------------ sensitivity options of the loader
def test_include_at_adds_the_final_test_to_the_forecast_set_only_when_asked(tmp_path):
    rows = _checkups_rows("TP_z10_01", 1, "z", [(1, "ET"), (3, "CU"), (5, "CU"), (7, "CU"), (9, "AT")])
    root = _write_root(tmp_path, rows)
    assert D._load_samsung(root)[0].n == 4                                           # ET + 3 check-ups; AT dropped by default
    c = D._load_samsung(root, include_at=True)[0]
    assert c.n == 5 and c.fc_ok.tolist() == [False, True, True, True, True]


def test_storage_cells_04_to_06_enter_only_with_the_flag(tmp_path):
    # mini Samsung root with a split file: storage cells 01 and 05 of one condition
    rows = _checkups_rows("TP_k03_01", 2, "k", [(1, "ET"), (3, "CU"), (5, "CU"), (7, "CU")], cell_no=1) + _checkups_rows("TP_k03_05", 2, "k", [(1, "ET"), (3, "AT")], cell_no=5)
    for r in rows:
        r["SOC_max"] = 0.5
        r["DoD"] = r["C_ch"] = r["C_dch"] = 0.0
    root = _write_root(tmp_path, rows)
    folds = {"0": {"test_conditions": [], "test_cells": [], "train_cycling_conditions": []}}
    import hashlib
    dig = hashlib.sha256(json.dumps(folds, sort_keys=True).encode()).hexdigest()
    (tmp_path / "runs" / "splits").mkdir(parents=True)
    (tmp_path / "runs" / "splits" / "samsung_splits_v2.json").write_text(json.dumps({"B": {"folds": folds, "sha256_of_folds": dig}}))
    base = {c.cell_id for c in D.load_split("samsung", "B", 0, "train", root=root, include_at=True).train}
    flag = {c.cell_id for c in D.load_split("samsung", "B", 0, "train", root=root, include_at=True, include_storage_0406=True).train}
    assert "TP_k03_05_s2" not in base and "TP_k03_05_s2" in flag and "TP_k03_01_s2" in base


# ------------------------------------------------------------------------------------------------ law overrides (rows (l), (m))
def test_overrides_change_and_restore_the_constants():
    y0, g, tau, sc = law.Y0, law.GAMMA, law.TAU, law.DELTA_SCOPE
    with law.overrides(Y0=2.0, gamma=0.6, tau=0.3, delta_scope="total"):
        assert (law.Y0, law.GAMMA, law.TAU, law.DELTA_SCOPE) == (2.0, 0.6, 0.3, "total")
        phi = law.state_to_drive(law.drive_to_state(__import__("torch").tensor([1.0]), "self_limiting"), "self_limiting")
        assert float(phi) == pytest.approx(1.0, abs=1e-6)
    assert (law.Y0, law.GAMMA, law.TAU, law.DELTA_SCOPE) == (y0, g, tau, sc)
    with pytest.raises(ValueError):
        with law.overrides(delta_scope="both"):
            pass
    assert law.Y0 == y0


def test_total_delta_scope_scales_both_terms_of_a_cycling_cell():
    import torch
    from pinnkan.specs import SPECS
    spec = SPECS["synthetic"]
    lw = law.Law(spec, law.build_stress_map("kan", spec, {"h": 2, "grid": 3}))
    s = torch.zeros(2, spec.d)
    is_cyc = torch.tensor([1.0, 0.0])
    delta = torch.tensor([0.5, 0.5])
    a_cal0, a_cyc0 = (x.detach() for x in lw.amplitudes(s, is_cyc, delta))
    with law.overrides(delta_scope="total"):
        a_cal1, a_cyc1 = (x.detach() for x in lw.amplitudes(s, is_cyc, delta))
    r_cal, r_cyc = lw.r_cal(s).detach(), lw.r_cyc(s).detach()
    e = float(np.exp(0.5))
    assert float(a_cal0[0]) == pytest.approx(float(r_cal[0])) and float(a_cal1[0]) == pytest.approx(float(r_cal[0]) * e)     # cycling cell: calendar term scaled only in the total scope
    assert float(a_cyc1[0]) == pytest.approx(float(r_cyc[0]) * e) and float(a_cyc0[0]) == pytest.approx(float(r_cyc[0]) * e)
    assert float(a_cal1[1]) == pytest.approx(float(a_cal0[1]))                                                                  # storage cell: same in both scopes


def test_run_refuses_law_overrides_for_other_arms_and_the_forecast_failure_row(tmp_path):
    from pinnkan import run as R
    with pytest.raises(R.ConfigError, match="sensitivity rows"):
        R.run({"run_id": "x", "dataset": "synthetic", "arms": ["A1", "A2"], "law_overrides": {"tau": 0.3}}, root=str(tmp_path), runs_dir=str(tmp_path / "runs"))
    with pytest.raises(R.ConfigError, match="unknown law_overrides"):
        R.run({"run_id": "x", "dataset": "synthetic", "arms": ["A2"], "law_overrides": {"bogus": 1}}, root=str(tmp_path), runs_dir=str(tmp_path / "runs"))
    with pytest.raises(R.NotBuiltError, match="forecast times"):
        R.run({"run_id": "x", "dataset": "synthetic", "arms": ["A2"], "forecast_failure": True}, root=str(tmp_path), runs_dir=str(tmp_path / "runs"))
