"""Unit tests for code/data/samsung_checkups.py.

Run:  .venv/Scripts/python.exe -P -m pytest code/tests/test_samsung_checkups.py -q   (from ROOT)

The two probed files (TP_k03_01 CU 02: about 4.878 Ah; TP_z18_01 CU 03: about 4.822 Ah, step_type 22,
from runs/pilot_P0/RESULT.md) are tested first; the synthetic tests check the arithmetic exactly.
"""
import datetime as dt
import glob
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))

import numpy as np
import pandas as pd
import pytest

from data import samsung_checkups as S

RAW = os.path.join(ROOT, "data", "raw", "samsung50e_members")


def _find(name):
    hits = sorted(glob.glob(os.path.join(RAW, "*", name)))
    return hits[0] if hits else None


def probe_rectangle_ah(path, step):
    """The P0 probe's method (code/data/samsung_cu_probe.py): backward rectangle on every row of the step."""
    d = pd.read_csv(path)
    t = pd.to_timedelta(d.run_time.str.strip()).dt.total_seconds().to_numpy()
    ah = d.c_cur.to_numpy() * np.diff(t, prepend=t[0]) / 3600.0
    return float(ah[(d.step_type == step).to_numpy()].sum())


# ---------------------------------------------------------------- probed files (go criterion of P0)
@pytest.mark.parametrize("name,expected", [("TP_k03_01_02_CU.csv", 4.878), ("TP_z18_01_03_CU.csv", 4.822)])
def test_probed_file_capacity_matches_probe(name, expected):
    path = _find(name)
    if path is None:
        pytest.skip(f"{name} not present")
    res = S.analyse_capacity_csv(path)
    assert res["flags"] == []
    # expected values are quoted "about" in the P0 note; the probe uses a backward rectangle, we use trapezoids
    assert abs(res["q22_ah"] - expected) < 0.01
    assert abs(res["q22_ah"] - abs(probe_rectangle_ah(path, 22))) < 0.01
    assert abs(res["q21_ah"] - probe_rectangle_ah(path, 21)) < 0.01
    assert 4.3 < res["i_med22_a"] < 5.4 and 0.9 < res["dur22_h"] < 1.2
    assert res["q_mean_ah"] == pytest.approx(0.5 * (res["q21_ah"] + res["q22_ah"]))


# ---------------------------------------------------------------- synthetic csv
def _hms(sec):
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def make_cu_csv(path, q_ch=4.9, q_dch=4.9, rest_tail_h=2.0, with_22=True, with_21=True, dch_v_end=2.5, ch_hours=2.0):
    """Rest 0.5 h, CC charge (step 21), rest, CC discharge (step 22), rest tail; 10 s sampling."""
    rows = []

    def seg(n_sec, cur, v0, v1, step):
        n = int(n_sec // 10) + 1
        for k in range(n):
            rows.append((len(rows) * 0 + (rows[-1][0] + 10.0 if rows else 0.0), v0 + (v1 - v0) * k / max(n - 1, 1), cur, 24.0, 23.0, step))

    seg(1800, 0.0, 3.65, 3.65, 0)
    if with_21:
        seg(ch_hours * 3600, q_ch / ch_hours, 2.8, 4.2, 21)
    seg(600, 0.0, 4.2, 4.15, 0)
    if with_22:
        seg(q_dch / 4.9 * 3600, -4.9, 4.15, dch_v_end, 22)
    seg(rest_tail_h * 3600, 0.0, 2.5, 3.0, 0)
    df = pd.DataFrame(rows, columns=["run_time", "c_vol", "c_cur", "c_surf_temp", "amb_temp", "step_type"])
    df["run_time"] = df["run_time"].map(_hms)
    df.to_csv(path, index=False)


def test_synthetic_capacity_is_exact(tmp_path):
    p = tmp_path / "TP_z99_01_03_CU.csv"
    make_cu_csv(p, q_ch=4.9, q_dch=4.9)
    r = S.analyse_capacity_csv(str(p))
    assert r["flags"] == [], r
    assert r["q21_ah"] == pytest.approx(4.9, abs=1e-6)
    assert r["q22_ah"] == pytest.approx(4.9, abs=1e-6)
    assert r["q_mean_ah"] == pytest.approx(4.9, abs=1e-6)
    assert r["dur22_h"] == pytest.approx(1.0, abs=1e-6)
    assert r["file_hours"] == pytest.approx(0.5 + 2 + 1 / 6 + 1 + 2, abs=0.02)


def test_mean_capacity_is_mean_of_charge_and_discharge(tmp_path):
    p = tmp_path / "x_CU.csv"
    make_cu_csv(p, q_ch=4.80, q_dch=4.90)
    r = S.analyse_capacity_csv(str(p))
    assert r["q_mean_ah"] == pytest.approx(4.85, abs=1e-6)
    assert "charge_discharge_mismatch" not in r["flags"]


def test_missing_discharge_step_is_flagged(tmp_path):
    p = tmp_path / "x_CU.csv"
    make_cu_csv(p, with_22=False)
    r = S.analyse_capacity_csv(str(p))
    assert "step22_missing" in r["flags"]
    assert "q_mean_ah" not in r


def test_missing_charge_step_is_flagged(tmp_path):
    p = tmp_path / "x_CU.csv"
    make_cu_csv(p, with_21=False)
    r = S.analyse_capacity_csv(str(p))
    assert "step21_missing" in r["flags"] and "q_mean_ah" not in r


def test_truncated_discharge_is_flagged(tmp_path):
    p = tmp_path / "x_CU.csv"
    make_cu_csv(p, q_dch=1.5, dch_v_end=3.4)   # aborted at 3.4 V after 0.3 h
    r = S.analyse_capacity_csv(str(p))
    assert "duration22_out_of_range" in r["flags"] and "discharge_not_full_window" in r["flags"]


def test_charge_discharge_mismatch_flag(tmp_path):
    p = tmp_path / "x_CU.csv"
    make_cu_csv(p, q_ch=4.2, q_dch=4.9)
    assert "charge_discharge_mismatch" in S.analyse_capacity_csv(str(p))["flags"]


def test_unreadable_file_becomes_a_flag(tmp_path):
    p = tmp_path / "x_CU.csv"
    p.write_text("not,a,csv\n1,2\n")
    r = S.analyse_capacity_csv(str(p))
    assert "bad_schema" in r["flags"] or "read_error" in r["flags"]


# ---------------------------------------------------------------- parsing
def test_run_time_parsing_handles_blanks_and_long_hours():
    s = pd.Series([" 0:00:00.0022", "00:00:01.500", "71:30:00.000"])
    out = S.parse_run_time(s)
    assert out[0] == pytest.approx(0.0022) and out[1] == pytest.approx(1.5) and out[2] == pytest.approx(71.5 * 3600)


def test_meta_parsing_date_formats_and_setpoint():
    a = S.parse_meta_text("Laboratory identifier: SIE\nInternal cell serial: 055\nMeasurement start date: 28.02.2023\n"
                          "Climate chamber temperature setpoint: 23Â°C\n")
    assert a["date"] == dt.date(2023, 2, 28) and a["setpoint_c"] == 23.0 and a["lab"] == "SIE" and a["internal_serial"] == "055"
    b = S.parse_meta_text("Measurement start date: 12.02.23\nClimate chamber temperature setpoint: 45\n")
    assert b["date"] == dt.date(2023, 2, 12) and b["setpoint_c"] == 45.0
    assert S.parse_meta_text("Measurement start date: 31.02.2023")["date"] is None   # impossible date
    assert S.parse_meta_text("nothing here")["date"] is None


def test_file_name_regex():
    m = S.FILE_RE.match("TP_z12_01_15_CU.csv")
    assert m and m.group("serial") == "TP_z12_01" and m.group("idx") == "15" and m.group("kind") == "CU" and m.group("csv")
    m = S.FILE_RE.match("TP_k03_01_01_ET_T23_meta.txt")
    assert m and m.group("kind") == "ET" and m.group("temp") == "23" and m.group("meta")
    assert S.FILE_RE.match("TP_k03_01_02_exCU.csv").group("kind") == "exCU"
    assert S.FILE_RE.match("TP_z12_01_15_CU.csv.part") is None


# ---------------------------------------------------------------- design-based estimates
def test_fec_per_hour_formula():
    assert S.fec_per_hour(0.6, 1.1, 0.3) == pytest.approx(0.6 * 1.1 / 1.7)
    assert S.fec_per_hour(0.6, 1.1, 0.05) == pytest.approx(S.fec_per_hour(0.6, 1.1, 0.5))   # DoD cancels without rests
    # rests lengthen the cycle and lower the rate; a 5 min rest after each half cycle at DoD 0.3
    t_cyc = 0.3 * (1 / 0.6 + 1 / 1.1) + 2 * 300 / 3600
    assert S.fec_per_hour(0.6, 1.1, 0.3, 300) == pytest.approx(0.3 / t_cyc)
    assert math.isnan(S.fec_per_hour(0.0, 1.0, 0.3))


def test_events_between_numbering():
    assert S.events_between(1, 3, "z", None)[0] == []                 # ET, ZYK, CU
    assert S.events_between(3, 9, "z", None)[0] == ["exCU", "exCU"]   # 4 ZYK 5 X 6 ZYK 7 X 8 ZYK
    assert S.events_between(1, 2, "k", None)[0] == []                 # storage: ET then CU
    assert S.events_between(2, 6, "k", None)[0] == ["exCU"] * 3
    seq = {1: "ET", 2: "ZYK", 3: "CU", 4: "ZYK", 5: "CU", 6: "ZYK", 7: "exCU", 8: "ZYK", 9: "CU"}
    assert S.events_between(5, 9, "z", seq) == (["exCU"], False)


def test_outlier_rule():
    x = np.arange(8.0)
    q = np.array([4.90, 4.88, 4.86, 4.60, 4.82, 4.80, 4.78, 4.76])    # isolated dip at index 3
    valid = np.ones(8, bool)
    out = S.flag_outliers(x, q, valid)
    assert out.tolist() == [False, False, False, True, False, False, False, False]
    smooth = 4.9 - 0.02 * x - 0.004 * x ** 2                            # curvature / knee alone is not an outlier
    assert not S.flag_outliers(x, smooth, valid).any()
    q2 = q.copy()
    assert not S.flag_outliers(x, q2, np.r_[valid[:3], False, valid[4:]])[3]   # an invalid point is never flagged


def test_trapezoid_rule():
    t = np.array([0.0, 10.0, 20.0])
    assert S.trapz(np.array([1.0, 1.0, 1.0]), t) == pytest.approx(20.0)
    assert S.trapz(np.array([1.0]), np.array([0.0])) == 0.0


# ---------------------------------------------------------------- design lookup with duplicated serial names
def _design():
    return pd.DataFrame([
        dict(serial_internal="S019", serial="TP_z01_01", lab="SIE", stage=1, type="z"),
        dict(serial_internal="021", serial="TP_z01_01", lab="SIE", stage=2, type="z"),
        dict(serial_internal="INT037", serial="TP_z10_01", lab="INT", stage=1, type="z"),
        dict(serial_internal="INT149", serial="TP_z10_01", lab="INT", stage=2, type="z"),
        dict(serial_internal="INT043", serial="TP_z12_01", lab="INT", stage=1, type="z"),
        dict(serial_internal="TP_z12_01", serial="TP_z12_01", lab="HM", stage=2, type="z"),
        dict(serial_internal="S100", serial="TP_z30_01", lab="SIE", stage=1, type="z"),
    ])


def _m(**k):
    base = dict(date=None, date_raw=None, lab=None, internal_serial=None, setpoint_c=None)
    base.update(k)
    return base


def test_resolve_design_by_internal_serial_lab_date_and_unique_name():
    d = _design()
    row, how, notes = S.resolve_design("TP_z01_01", [_m(internal_serial="021", date=dt.date(2023, 1, 30))], d)
    assert (int(row.stage), how, notes) == (2, "internal_serial", [])
    row, how, _ = S.resolve_design("TP_z12_01", [_m(internal_serial="TP_z12_01", lab="HM")], d)
    assert (int(row.stage), how) == (2, "internal_serial")
    row, how, _ = S.resolve_design("TP_z12_01", [_m(lab="HM")], d)
    assert (int(row.stage), how) == (2, "lab")
    row, how, notes = S.resolve_design("TP_z10_01", [_m(internal_serial="INT028", lab="INT", date=dt.date(2021, 10, 12))], d)
    assert (int(row.stage), how) == (1, "date") and any("meta_internal_serial_differs" in n for n in notes)
    row, how, _ = S.resolve_design("TP_z30_01", [], d)
    assert how == "unique_name" and row.serial_internal == "S100"
    assert S.resolve_design("TP_z99_99", [], d)[0] is None
    assert S.resolve_design("TP_z10_01", [_m(lab="INT")], d)[1] == "ambiguous"


# ---------------------------------------------------------------- one synthetic cycling cell end to end
def _write_meta(path, date_str, lab="SIE", internal="S019", setpoint="23"):
    path.write_text(f"Laboratory identifier: {lab}\nInternal cell serial: {internal}\nTestpoint: z99\n"
                    f"Measurement start date: {date_str}\nClimate chamber temperature setpoint: {setpoint}Â°C\n", encoding="utf-8")


def test_process_cell_exposure_and_efc(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "LISTS", tmp_path / "no_lists")
    monkeypatch.setattr(S, "PROBE_DIR", tmp_path / "no_probe")
    f = tmp_path / "TP_z01_01__f1"
    f.mkdir()
    _write_meta(f / "TP_z01_01_01_ET_T10_meta.txt", "01.01.2023")
    # CU 03 on 20 Jan, CU 05 on 27 Jan, CU 09 on 24 Feb (an exCU is hidden between 05 and 09, file 07)
    for idx, date in ((3, "20.01.2023"), (5, "27.01.2023"), (9, "24.02.2023")):
        make_cu_csv(f / f"TP_z01_01_{idx:02d}_CU.csv", q_ch=4.8 - 0.1 * idx / 3, q_dch=4.8 - 0.1 * idx / 3 + 0.01, rest_tail_h=2.0)
        _write_meta(f / f"TP_z01_01_{idx:02d}_CU_meta.txt", date)
    cond = pd.Series(dict(serial_internal="S019", serial="TP_z01_01", lab="SIE", stage=1, type="z", tp=1, cell=1, amb_temp_tp=23,
                          soc_max_tp=0.7, dod_tp=0.3, c_ch_tp=0.6, c_dch_tp=1.1, sampling="cLH"))
    issues = []
    analysed = {str(p): S.analyse_capacity_csv(str(p)) for p in f.glob("*_CU.csv")}
    rows, cell = S.process_cell("TP_z01_01", cond, f, analysed, issues)
    assert [r["file_idx"] for r in rows] == [3, 5, 9]
    h = [r["file_hours"] for r in rows]     # measured length of each synthetic CU file (about 5.6 h)
    assert all(5.4 < x < 5.7 for x in h)
    fph = 0.6 * 1.1 / 1.7
    # first check-up: design schedule (7 d); elapsed since ET is 19 d
    assert rows[0]["elapsed_days"] == 19 and rows[0]["exposure_days_est"] == pytest.approx(7.0)
    assert rows[0]["exposure_anchor"] == "schedule"
    # second: 7 d later minus the first CU file
    assert rows[1]["exposure_days_est"] == pytest.approx(7.0 + 7 - h[0] / 24, abs=1e-6)
    # third: 35 d after the first, minus CU03, CU05 and the hidden exCU (30 h)
    assert rows[2]["exposure_days_est"] == pytest.approx(7.0 + 35 - (h[0] + h[1] + 30.0) / 24, abs=1e-6)
    assert rows[2]["efc_est_cum"] == pytest.approx(rows[2]["exposure_days_est"] * 24 * fph, rel=1e-6)
    assert rows[2]["efc_est_interval"] == pytest.approx(rows[2]["efc_est_cum"] - rows[1]["efc_est_cum"], rel=1e-6)
    assert rows[2]["n_events_before"] == 3
    # retention relative to the first quality-passed check-up, monotone decreasing here
    assert rows[0]["retention"] == pytest.approx(1.0) and rows[2]["retention"] < rows[1]["retention"] < 1.0
    assert rows[0]["ref_kind"] == "CU" and all(not r["_flags"] for r in rows)
    assert cell["n_cu_present"] == 3 and cell["n_qc_pass"] == 3


def test_process_cell_flags_decreasing_dates_and_bad_file(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "LISTS", tmp_path / "no_lists")
    monkeypatch.setattr(S, "PROBE_DIR", tmp_path / "no_probe")
    f = tmp_path / "TP_z01_01__f2"
    f.mkdir()
    _write_meta(f / "TP_z01_01_01_ET_T10_meta.txt", "01.01.2023")
    make_cu_csv(f / "TP_z01_01_03_CU.csv")
    _write_meta(f / "TP_z01_01_03_CU_meta.txt", "20.01.2023")
    make_cu_csv(f / "TP_z01_01_05_CU.csv", with_22=False)
    _write_meta(f / "TP_z01_01_05_CU_meta.txt", "10.01.2023")
    cond = pd.Series(dict(serial_internal="S019", serial="TP_z01_01", lab="SIE", stage=1, type="z", tp=1, cell=1, amb_temp_tp=23,
                          soc_max_tp=0.7, dod_tp=0.3, c_ch_tp=0.6, c_dch_tp=1.1, sampling="cLH"))
    analysed = {str(p): S.analyse_capacity_csv(str(p)) for p in f.glob("*_CU.csv")}
    rows, _ = S.process_cell("TP_z01_01", cond, f, analysed, [])
    assert "date_out_of_order" in rows[1]["_flags"] and "step22_missing" in rows[1]["_flags"]
