"""Samsung INR21700-50E (Stroebl et al. 2024): one row per check-up, built from the raw CU files.

Run (from ROOT):  .venv/Scripts/python.exe -P code/data/samsung_checkups.py [--jobs N] [--no-cache]

Inputs (all parsed with pandas / plain text only; nothing from a download is executed):
  data/raw/samsung50e_members/<serial>/*_CU.csv, *_exCU.csv, *_ET_T23.csv, *_AT_T23.csv (if present)
  data/raw/samsung50e_members/<serial>/*_meta.txt         measurement start date, chamber set point
  data/raw/samsung50e_meta/experiments_meta.csv           design (T, SOC_max, DoD, C_ch, C_dch) per cell
  runs/pilot_P0/member_lists/<serial>.txt (or runs/pilot_P0/<serial>_members.tsv)
                                                          optional: zip member names, used for the
                                                          expected file sequence and completeness
Outputs:
  data/processed/samsung_checkups.csv   one row per check-up
  data/processed/samsung_cells.csv      one row per cell
  runs/samsung_pipeline/{config.json,metrics.json,issues.csv,cells_summary.csv}

Definitions (see runs/samsung_pipeline/RESULT.md for the evidence):
  step_type 21 = CC-CV charge (C/2 to 4.2 V, C/20 cut-off), step_type 22 = CC-CV discharge (1C to 2.5 V,
  C/20 cut-off). q_ch / q_dch = integral of current over all samples of that step (trapezoid rule).
  q_mean = (q_ch + q_dch) / 2: the capacity definition of the dataset paper (mean of charge and discharge
  capacity of the RPT at 23 C). retention = q_mean / reference capacity, where the reference is the ET_T23
  capacity if that file is present, otherwise the first quality-passed check-up of the cell.
  Quality flag capacity_outlier_vs_neighbours (name kept for compatibility) is CAUSAL since 2026-11-05.6
  (review m1): a valid 23 C check-up is flagged when its capacity is above the range of the up to 2
  preceding valid check-ups of the cell by more than 1 % of its own value, or below it by more than 1 % plus
  twice the latest observed fall (flag_outliers docstring); the first check-up is not tested, the second for a
  rise only, and no later check-up is used. (Before: range of the preceding and the following neighbour; the
  plain preceding-range rule, OUTLIER_DROP_MULT = 0, would flag 24 % of the check-ups as steady ageing.)
  Equivalent full cycles (EFC, cycling cells) are an ANALYTIC ESTIMATE from the design, not a measurement;
  they must be validated against the ZYK segment files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "samsung50e_members"
META_CSV = ROOT / "data" / "raw" / "samsung50e_meta" / "experiments_meta.csv"
LISTS = ROOT / "runs" / "pilot_P0" / "member_lists"
PROBE_DIR = ROOT / "runs" / "pilot_P0"
OUT_DIR = ROOT / "data" / "processed"
OUT_CHECKUPS = OUT_DIR / "samsung_checkups.csv"
OUT_CELLS = OUT_DIR / "samsung_cells.csv"
CACHE = OUT_DIR / ".samsung_file_cache.json"
RUN_DIR = ROOT / "runs" / "samsung_pipeline"

CODE_VERSION = "2026-11-05.6"  # bump to invalidate the per-file cache

# ---- constants taken from the dataset paper (notes/papers/samsung50e_dataset_paper.md, Table 3) ----
Q_NOM_AH = 4.9                    # rated capacity; C-rates refer to it
DUR_H = {"ET": 220.0, "AT": 200.0, "exCU": 30.0, "CU": 15.0}   # nominal RPT durations (paper); CU is
#                                                                  replaced by the measured file duration
REF_TEMP_C = 23

# ---- quality thresholds (physical reasoning, documented in RESULT.md) ----
DCH_DUR_H = (0.45, 1.35)      # 1C discharge of 0.5-1.1 x 4.9 Ah plus CV tail
CH_DUR_H = (0.90, 2.80)       # C/2 charge of 0.5-1.1 x 4.9 Ah plus CV tail
DCH_CURRENT_A = (4.4, 5.4)    # median current of the discharge step (1C = 4.9 A)
CH_CURRENT_A = (2.2, 2.7)     # median current of the charge step (C/2 = 2.45 A)
CAP_RANGE_AH = (2.0, 5.2)
CH_DCH_MISMATCH = 0.03        # |q_ch - q_dch| / q_dch
STEP_GAP_S = 60.0             # sampling gap inside a capacity step
STUB_AH = 0.05                # a second run of a step passing less than this is a stub (info only)
LONG_FILE_H = 30.0            # info flag
START_TEMP_TOL_C = 5.0        # |surface temperature at the start of the discharge - 23 C|
OUTLIER_REL = 0.01            # point outside the range of its (up to) 2 PRECEDING valid points by more than this fraction
OUTLIER_DROP_MULT = 2.0       # ... a fall is further allowed up to this multiple of the latest observed fall
RISE_REL = 0.005              # info flag: capacity rises by more than this fraction vs previous check-up
SCHEDULE_FIRST_D = {"z": 7.0, "k": 35.0}   # days from the start of ageing to the first check-up (Fig. 4 of the dataset
#                                             paper, read from the image: cycling 1 W, storage 5 W)
REST_SENSITIVITY_S = 300.0    # illustrative rest after every half-cycle for the second EFC column

FILE_RE = re.compile(
    r"^(?P<serial>TP_[kz]\d{2}_\d{2})_(?P<idx>\d{2})_(?P<kind>ET|CU|exCU|AT|ZYK)(?:_T(?P<temp>\d+))?"
    r"(?P<meta>_meta\.txt)?(?P<csv>\.csv)?$")
DATE_RE = re.compile(r"Measurement start date:\s*(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})")
SETPOINT_RE = re.compile(r"setpoint:\s*(-?\d+(?:[.,]\d+)?)")
LAB_RE = re.compile(r"Laboratory identifier:\s*(\w+)")
INTSER_RE = re.compile(r"Internal cell serial:\s*(\S+)")
CORE_COLS = ("run_time", "c_vol", "c_cur", "c_surf_temp", "amb_temp", "step_type")


# ----------------------------------------------------------------------------------------------
# parsing helpers
# ----------------------------------------------------------------------------------------------
def parse_meta_text(text: str) -> dict:
    """Measurement start date (day resolution), lab, internal serial and chamber set point."""
    out = {"date": None, "date_raw": None, "lab": None, "internal_serial": None, "setpoint_c": None}
    m = DATE_RE.search(text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        out["date_raw"] = m.group(0).split(":", 1)[1].strip()
        if y < 100:
            y += 2000
        try:
            date = dt.date(y, mo, d)
            out["date"] = date if dt.date(2019, 1, 1) <= date <= dt.date(2026, 12, 31) else None
        except ValueError:
            out["date"] = None
    m = LAB_RE.search(text)
    out["lab"] = m.group(1) if m else None
    m = INTSER_RE.search(text)
    out["internal_serial"] = m.group(1) if m else None
    m = SETPOINT_RE.search(text)
    out["setpoint_c"] = float(m.group(1).replace(",", ".")) if m else None
    return out


def read_meta_file(path: Path) -> dict:
    return parse_meta_text(path.read_text(encoding="utf-8", errors="replace"))


def parse_run_time(s: pd.Series) -> np.ndarray:
    """'HH:MM:SS.sss' (hours may exceed 24, leading blanks occur) -> seconds as float."""
    return pd.to_timedelta(s.astype(str).str.strip(), errors="coerce").dt.total_seconds().to_numpy(float)


def trapz(y: np.ndarray, x: np.ndarray) -> float:
    return float(np.trapezoid(y, x)) if len(x) > 1 else 0.0


def step_runs(t, cur, vol, step, s) -> list[dict]:
    """Contiguous runs of step_type == s with charge (A h, signed), duration and diagnostics."""
    idx = np.flatnonzero(step == s)
    if idx.size == 0:
        return []
    groups = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    runs = []
    for g in groups:
        tt, ii = t[g], cur[g]
        dts = np.diff(tt) if len(g) > 1 else np.array([0.0])
        runs.append({
            "n": int(len(g)), "dur_h": float((tt[-1] - tt[0]) / 3600.0), "ah": trapz(ii, tt) / 3600.0,
            "i_med": float(np.nanmedian(ii)), "dt_max": float(np.nanmax(dts)),
            "v_first": float(vol[g][0]), "v_last": float(vol[g][-1]), "n_nan": int(np.isnan(ii).sum()),
            "i_first_idx": int(g[0]),
        })
    return runs


def analyse_capacity_csv(path: str) -> dict:
    """Capacity numbers and per-file diagnostics of one RPT csv. Never raises: problems become flags."""
    res: dict = {"path": path, "read_error": None, "flags": [], "info": []}
    try:
        d = pd.read_csv(path, usecols=lambda c: c.strip() in CORE_COLS, low_memory=False)
    except Exception as e:  # noqa: BLE001 - unreadable file becomes a flag, not a crash
        res["read_error"] = f"{type(e).__name__}: {e}"[:200]
        res["flags"].append("read_error")
        return res
    d.columns = [c.strip() for c in d.columns]
    missing = [c for c in ("run_time", "c_vol", "c_cur", "step_type") if c not in d.columns]
    if missing or len(d) < 10:
        res["flags"].append("bad_schema")
        res["read_error"] = f"missing columns {missing}; rows {len(d)}"
        return res
    t = parse_run_time(d["run_time"])
    cur = pd.to_numeric(d["c_cur"], errors="coerce").to_numpy(float)
    vol = pd.to_numeric(d["c_vol"], errors="coerce").to_numpy(float)
    step = pd.to_numeric(d["step_type"], errors="coerce").to_numpy(float)
    ts = pd.to_numeric(d["c_surf_temp"], errors="coerce").to_numpy(float) if "c_surf_temp" in d else np.full(len(d), np.nan)
    ta = pd.to_numeric(d["amb_temp"], errors="coerce").to_numpy(float) if "amb_temp" in d else np.full(len(d), np.nan)
    res["n_rows"] = int(len(d))
    if np.isnan(t).any():
        res["flags"].append("unparsable_time")
    if np.isnan(t).all():
        return res
    t = pd.Series(t).interpolate(limit_direction="both").to_numpy()
    res["file_hours"] = float(t[-1] / 3600.0)
    if (np.diff(t) < 0).any():
        res["flags"].append("time_not_monotonic")
    if res["file_hours"] > LONG_FILE_H:
        res["info"].append("long_file")
    act = np.flatnonzero(np.abs(np.nan_to_num(cur)) > 0.05)   # the files end in a rest period of a few hours to a week
    res["active_hours"] = float(t[act[-1]] / 3600.0) if act.size else 0.0
    res["v_min_file"] = float(np.nanmin(vol)) if np.isfinite(vol).any() else np.nan
    if res["v_min_file"] < 2.0:
        res["info"].append("voltage_glitch_below_2V")

    r21 = step_runs(t, cur, vol, step, 21)
    r22 = step_runs(t, cur, vol, step, 22)
    for name, runs, lo_hi_dur, lo_hi_i in (("21", r21, CH_DUR_H, CH_CURRENT_A), ("22", r22, DCH_DUR_H, DCH_CURRENT_A)):
        if not runs:
            res["flags"].append(f"step{name}_missing")
            continue
        main = max(runs, key=lambda r: abs(r["ah"]))
        extra = [r for r in runs if r is not main]
        if extra:
            res["flags"].append(f"multiple_runs_{name}" if any(abs(r["ah"]) > STUB_AH for r in extra) else None)
            res["info"].append(f"stub_run_{name}")
        res[f"q{name}_ah"] = float(sum(abs(r["ah"]) for r in runs))
        res[f"dur{name}_h"] = float(main["dur_h"])
        res[f"i_med{name}_a"] = float(abs(main["i_med"]))
        res[f"v_first{name}"], res[f"v_last{name}"] = main["v_first"], main["v_last"]
        res[f"dt_max{name}_s"] = float(max(r["dt_max"] for r in runs))
        res[f"n_nan{name}"] = int(sum(r["n_nan"] for r in runs))
        if not lo_hi_dur[0] <= main["dur_h"] <= lo_hi_dur[1]:
            res["flags"].append(f"duration{name}_out_of_range")
        if not lo_hi_i[0] <= abs(main["i_med"]) <= lo_hi_i[1]:
            res["flags"].append(f"current{name}_off_nominal")
        if res[f"dt_max{name}_s"] > STEP_GAP_S:
            res["flags"].append(f"sampling_gap_in_step{name}")
        if res[f"n_nan{name}"] > 0:
            res["flags"].append(f"nan_current_in_step{name}")
        if name == "22":
            i0 = main["i_first_idx"]
            seg = slice(i0, i0 + main["n"])
            res["t_surf_dch_mean_c"] = float(np.nanmean(ts[seg])) if np.isfinite(ts[seg]).any() else np.nan
            res["t_surf_dch_start_c"] = float(ts[i0])
            res["amb_median_c"] = float(np.nanmedian(ta[seg])) if np.isfinite(ta[seg]).any() else np.nan
    res["flags"] = [f for f in res["flags"] if f]
    if "q22_ah" in res and not CAP_RANGE_AH[0] <= res["q22_ah"] <= CAP_RANGE_AH[1]:
        res["flags"].append("implausible_capacity")
    if "v_first22" in res and not (res["v_first22"] >= 4.0 and res["v_last22"] <= 2.55):
        res["flags"].append("discharge_not_full_window")
    if "v_last21" in res and res["v_last21"] < 4.15:
        res["flags"].append("charge_not_to_4p2V")
    if "q21_ah" in res and "q22_ah" in res:
        res["q_mean_ah"] = 0.5 * (res["q21_ah"] + res["q22_ah"])
        if abs(res["q21_ah"] - res["q22_ah"]) / res["q22_ah"] > CH_DCH_MISMATCH:
            res["flags"].append("charge_discharge_mismatch")
    return res


# ----------------------------------------------------------------------------------------------
# design-based estimates
# ----------------------------------------------------------------------------------------------
def fec_per_hour(c_ch: float, c_dch: float, dod: float, rest_s: float = 0.0) -> float:
    """Equivalent full cycles per hour of cycling for a CC-only cycle.

    One cycle moves DoD * Q_nom in each direction: t_ch = DoD / C_ch h, t_dch = DoD / C_dch h (Q_nom
    cancels), plus two rests of rest_s. FEC per cycle = DoD (discharged Ah / Q_nom). With rest_s = 0 the
    result is C_ch * C_dch / (C_ch + C_dch), independent of DoD.
    """
    if not (c_ch > 0 and c_dch > 0 and dod > 0):
        return float("nan")
    t_cycle_h = dod * (1.0 / c_ch + 1.0 / c_dch) + 2.0 * rest_s / 3600.0
    return dod / t_cycle_h


def read_name_list(path: Path) -> list[str]:
    names = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        first = line.split("\t", 1)[0].strip()
        if first and first != "member" and not first.endswith("/"):
            names.append(first.rsplit("/", 1)[-1])
    return names


def expected_sequence(serial: str, folder: str | None = None) -> tuple[dict[int, str] | None, str]:
    """({file index: kind}, source) from a zip member list, or (None, '') if no list exists for the folder.

    Folders are named <serial>__f<figshare file id> (serial names are shared by two different zips, one per
    stage); the list of a folder is runs/pilot_P0/member_lists/<folder>.txt. Older plain-named folders fall back
    to <serial>.txt and to the pilot listing runs/pilot_P0/<serial>_members.tsv.
    """
    cands = []
    if folder:
        cands.append((LISTS / f"{folder}.txt", "folder_list"))
    if not folder or folder == serial:
        cands.append((LISTS / f"{serial}.txt", "serial_list"))
    cands.append((PROBE_DIR / f"{serial}_members.tsv", "pilot_tsv"))
    for p, src in cands:
        if p.exists():
            seq: dict[int, str] = {}
            for n in read_name_list(p):
                m = FILE_RE.match(n)
                if m and m.group("csv") and m.group("serial") == serial:
                    seq.setdefault(int(m.group("idx")), m.group("kind"))
            return seq, src
    return None, ""


def events_between(a: int, b: int, ctype: str, seq: dict[int, str] | None) -> tuple[list[str], bool]:
    """Check-up events (CU / exCU) with file index strictly between a and b; flag if kinds were assumed."""
    if seq is not None:
        return [seq[i] for i in range(a + 1, b) if seq.get(i) in ("CU", "exCU")], False
    n = (b - a - 1) if ctype == "k" else (b - a - 2) / 2.0   # cycling: ZYK segment between check-ups
    n = int(round(n)) if n >= 0 else 0
    return ["exCU"] * n, True


def flag_outliers(x: np.ndarray, q: np.ndarray, valid: np.ndarray, thr: float = OUTLIER_REL,
                  drop_mult: float = OUTLIER_DROP_MULT) -> np.ndarray:
    """Causal isolated-outlier rule (code review m1, V3 edit 5). Among the valid points with a finite capacity,
    in order, with a, b the two preceding valid points (a older) and d = max(a - b, 0) the latest observed drop,
    point i is flagged when
        q[i] > max(a, b) + thr * q[i]                      (rise above the preceding range), or
        q[i] < min(a, b) - drop_mult * d - thr * q[i]      (fall below it by more than the drop allowance).
    drop_mult = 0 is the plain preceding-range rule; the default allows a fall of up to drop_mult times the last
    observed fall plus thr, so that steady or accelerating ageing is not flagged (the plain rule would flag about
    a quarter of the check-ups of this dataset, whose check-ups are 1-4 months apart). The first valid point is
    never tested; the second has one predecessor and is tested for a rise only (a fall cannot be judged without a
    trend). Preceding points are the valid ones, flagged or not, so the point after a spike is not flagged. Only
    earlier points enter, so the flag of i never changes when later points change. Isolated spikes are caught;
    smooth curvature or a knee is not. x is unused (kept for the call signature)."""
    out = np.zeros(len(q), bool)
    vi = np.flatnonzero(valid & np.isfinite(q))
    for k in range(1, len(vi)):
        i = vi[k]
        prev = q[vi[max(0, k - 2):k]]
        hi = prev.max() + thr * q[i]
        d = max(prev[0] - prev[1], 0.0) if len(prev) == 2 else np.inf
        lo = prev.min() - drop_mult * d - thr * q[i]
        if q[i] > hi or q[i] < lo:
            out[i] = True
    return out


# ----------------------------------------------------------------------------------------------
# per-cell assembly
# ----------------------------------------------------------------------------------------------
def classify_files(folder: Path) -> dict:
    caps, metas = {}, {}
    for f in sorted(folder.iterdir()):
        m = FILE_RE.match(f.name)
        if not m:
            continue
        key = (int(m.group("idx")), m.group("kind"), m.group("temp"))
        if m.group("meta"):
            metas[key] = f
        elif m.group("csv"):
            caps[key] = f
    return {"csv": caps, "meta": metas}


def process_cell(serial: str, cond: pd.Series | None, folder: Path, analysed: dict, issues: list) -> tuple[list[dict], dict]:
    files = classify_files(folder)
    ctype = serial[3]
    seq, seq_src = expected_sequence(serial, folder.name)
    if seq is not None:  # the list was made from the zip of that name; distrust it if it does not match the folder
        stray = [(i, k) for (i, k, t) in files["csv"] if seq.get(i) != k]
        if stray:
            issues.append({"serial": serial, "file": "", "issue": "member_list_does_not_match_folder", "detail": str(stray[:5])})
            seq, seq_src = None, ""

    def issue(file, kind, detail=""):
        issues.append({"serial": serial, "file": file, "issue": kind, "detail": detail})

    # ---- first-test date ----
    et_dates = []
    for (idx, kind, temp), p in files["meta"].items():
        if kind == "ET":
            md = read_meta_file(p)
            if md["date"]:
                et_dates.append(md["date"])
    first_test, first_src = (min(et_dates), "ET_meta") if et_dates else (None, None)
    if first_test is None:
        zyk = [read_meta_file(p)["date"] for (i, k, t), p in files["meta"].items() if k == "ZYK"]
        zyk = [z for z in zyk if z]
        if zyk:
            first_test, first_src = min(zyk), "ZYK_meta"

    # ---- capacity files that enter the series ----
    cap_keys = []
    for (idx, kind, temp), p in files["csv"].items():
        if kind in ("CU", "exCU"):
            cap_keys.append((idx, kind, temp))
        elif kind in ("ET", "AT") and temp == str(REF_TEMP_C):
            cap_keys.append((idx, kind, temp))
    cap_keys.sort()

    rows = []
    for idx, kind, temp in cap_keys:
        p = files["csv"][(idx, kind, temp)]
        a = analysed[str(p)]
        mp = files["meta"].get((idx, kind, temp))
        md = read_meta_file(mp) if mp else {"date": None, "lab": None, "setpoint_c": None, "internal_serial": None, "date_raw": None}
        if mp is None:
            issue(p.name, "meta_missing")
        elif md["date"] is None:
            issue(mp.name, "start_date_unparsable", str(md["date_raw"]))
        if md["lab"] and cond is not None and md["lab"] != cond["lab"]:
            issue(p.name, "meta_lab_differs_from_table", f"{md['lab']} vs {cond['lab']}")
        if md["setpoint_c"] is not None and abs(md["setpoint_c"] - REF_TEMP_C) > 0.5:
            issue(p.name, "chamber_setpoint_not_23C", str(md["setpoint_c"]))
        flags = list(a["flags"])
        if md["date"] is None:
            flags.append("no_start_date")
        if md["setpoint_c"] is not None and abs(md["setpoint_c"] - REF_TEMP_C) > 0.5:
            flags.append("setpoint_not_23C")
        ts = a.get("t_surf_dch_start_c", np.nan)
        if np.isfinite(ts) and abs(ts - REF_TEMP_C) > START_TEMP_TOL_C:
            flags.append("surface_temp_at_discharge_start_far_from_23C")
        info = list(a["info"])
        if kind == "AT":
            info.append("AT_after_10C_45C_tests")
        rows.append({
            "serial": serial, "kind": kind, "file_idx": idx, "test_temp_c": REF_TEMP_C,
            "meas_start_date": md["date"].isoformat() if md["date"] else "",
            "chamber_setpoint_c": md["setpoint_c"],
            "q_dch_ah": a.get("q22_ah", np.nan), "q_ch_ah": a.get("q21_ah", np.nan), "q_mean_ah": a.get("q_mean_ah", np.nan),
            "dur_dch_h": a.get("dur22_h", np.nan), "dur_ch_h": a.get("dur21_h", np.nan),
            "i_dch_med_a": a.get("i_med22_a", np.nan), "file_hours": a.get("file_hours", np.nan),
            "t_surf_dch_start_c": ts, "t_surf_dch_mean_c": a.get("t_surf_dch_mean_c", np.nan),
            "active_hours": a.get("active_hours", np.nan), "amb_median_c": a.get("amb_median_c", np.nan),
            "_flags": flags, "_info": info, "_date": md["date"],
        })

    # ---- check-up events between rows, chronology ----
    cu_rank = 0
    for r in rows:
        if r["kind"] == "CU":
            cu_rank += 1
            r["cu_idx"] = cu_rank
        else:
            r["cu_idx"] = np.nan

    # date order consistent with file index?
    dated = [r for r in rows if r["_date"]]
    for p_, n_ in zip(dated[:-1], dated[1:]):
        if n_["_date"] < p_["_date"]:
            issue(f"idx {n_['file_idx']}", "start_date_decreases_with_file_index", f"{p_['_date']} -> {n_['_date']}")
            n_["_flags"].append("date_out_of_order")

    # ---- timeline of check-up events (CU / exCU) in file order, present or not -------------------------
    # duration of an event: measured file length for a CU csv that is present; the median measured CU length
    # of the cell for a CU whose csv is absent; 30 h (dataset paper, Table 3) for every exCU (csv not fetched).
    meas_cu_h = {r["file_idx"]: r["file_hours"] for r in rows if r["kind"] == "CU" and np.isfinite(r["file_hours"])}
    cu_median_h = float(np.median(list(meas_cu_h.values()))) if meas_cu_h else DUR_H["CU"]

    def event_hours(kind_: str, i: int | None) -> float:
        if kind_ == "CU":
            return meas_cu_h.get(i, cu_median_h)
        return DUR_H["exCU"] if kind_ == "exCU" else 0.0

    # timeline entries: (position key, hours); a row's exposure subtracts every entry with key < its own key
    timeline: list[tuple[float, float]] = []
    events_assumed = False
    if seq is not None:
        timeline = [(float(i), event_hours(k, i)) for i, k in sorted(seq.items()) if k in ("CU", "exCU")]
    else:  # no member list: infer unseen events between consecutive present rows from the file numbering
        last = 1  # file 01 is the entry test
        for x in rows:
            if x["kind"] not in ("CU", "exCU"):
                continue
            ks, _ = events_between(last, x["file_idx"], ctype, None)
            events_assumed = events_assumed or bool(ks)
            timeline += [(last + 0.5 + 0.01 * j, event_hours(k, None)) for j, k in enumerate(ks)]
            timeline.append((float(x["file_idx"]), event_hours(x["kind"], x["file_idx"])))
            last = x["file_idx"]

    first_row_date = next((r["_date"] for r in rows if r["_date"]), None)
    if first_test is None and first_row_date is not None:
        first_test, first_src = first_row_date, "first_capacity_row"
        issue("", "no_entry_test_date", "elapsed days measured from the first capacity row")
    et_h = DUR_H["ET"] if first_src == "ET_meta" else 0.0   # a ZYK-file start date is already after the ET
    fph = fph_rest = np.nan
    if ctype == "z" and cond is not None:
        fph = fec_per_hour(cond["c_ch_tp"], cond["c_dch_tp"], cond["dod_tp"])
        fph_rest = fec_per_hour(cond["c_ch_tp"], cond["c_dch_tp"], cond["dod_tp"], REST_SENSITIVITY_S)
    first_ev = min((key for key, _ in timeline), default=None)
    anchor = next((r for r in rows if first_ev is not None and r["file_idx"] == first_ev and r["_date"]), None)
    prev = None
    for r in rows:
        d_ = r["_date"]
        r["first_test_date"] = first_test.isoformat() if first_test else ""
        r["first_test_source"] = first_src or ""
        r["elapsed_days"] = float((d_ - first_test).days) if (d_ and first_test) else np.nan
        before = [h for key, h in timeline if key < r["file_idx"]]
        r["n_events_before"] = len(before)
        r["events_kinds_assumed"] = events_assumed
        exp_et = r["elapsed_days"] - et_h / 24.0 - sum(before) / 24.0 if np.isfinite(r["elapsed_days"]) else np.nan
        r["exposure_days_est_et_route"] = 0.0 if r["kind"] == "ET" else exp_et
        if r["kind"] == "ET":
            exp, r["exposure_anchor"] = 0.0, ""
        elif anchor is not None and r["file_idx"] >= anchor["file_idx"] and r["_date"]:
            # anchored on the design schedule: the first check-up falls SCHEDULE_FIRST_D[type] days after the
            # start of ageing; later ones add the calendar gap minus the check-up events in between
            span = sum(h for key, h in timeline if anchor["file_idx"] <= key < r["file_idx"])
            exp = SCHEDULE_FIRST_D[ctype] + float((r["_date"] - anchor["_date"]).days) - span / 24.0
            r["exposure_anchor"] = "schedule"
        else:
            exp, r["exposure_anchor"] = exp_et, "et_route"
        r["exposure_days_est"] = exp
        if np.isfinite(exp) and exp < -1.0:
            r["_flags"].append("negative_exposure_time")
        r["gap_days_prev"] = float((d_ - prev["_date"]).days) if (prev is not None and d_ and prev["_date"]) else np.nan
        pe = prev["exposure_days_est"] if prev is not None else 0.0
        r["interval_exposure_days_est"] = (exp - pe) if np.isfinite(exp) and np.isfinite(pe) else np.nan
        prev = r
        if ctype == "z":
            e = max(exp, 0.0) if np.isfinite(exp) else np.nan
            r["efc_est_cum"] = e * 24.0 * fph if np.isfinite(e) else np.nan
            r["efc_est_cum_rest300s"] = e * 24.0 * fph_rest if np.isfinite(e) else np.nan
        else:
            r["efc_est_cum"] = r["efc_est_cum_rest300s"] = np.nan
    for i, r in enumerate(rows):
        for col in ("efc_est_cum", "efc_est_cum_rest300s"):
            pv = rows[i - 1][col] if i > 0 else 0.0
            r[col.replace("_cum", "_interval")] = (r[col] - pv) if np.isfinite(r[col]) and np.isfinite(pv) else np.nan

    for i, r in enumerate(rows):
        if i == 0:
            r["n_skipped_events_prev"] = r["n_events_before"]
        else:
            pr = rows[i - 1]
            r["n_skipped_events_prev"] = r["n_events_before"] - pr["n_events_before"] - (1 if pr["kind"] in ("CU", "exCU") else 0)

    # ---- quality flag: outliers among the 23 C series (AT excluded: contaminated by 10/45 C tests) ----
    base_ok = np.array([not r["_flags"] and np.isfinite(r["q_mean_ah"]) for r in rows], bool)
    series = np.array([r["kind"] != "AT" for r in rows], bool)
    x = np.array([r["elapsed_days"] for r in rows], float)
    q = np.array([r["q_mean_ah"] for r in rows], float)
    out = flag_outliers(x, q, base_ok & series)
    for r, o in zip(rows, out):
        if o:
            r["_flags"].append("capacity_outlier_vs_neighbours")
    # information: rises
    ok_prev = None
    for r in rows:
        if r["kind"] == "AT" or r["_flags"] or not np.isfinite(r["q_mean_ah"]):
            continue
        if ok_prev is not None and r["q_mean_ah"] > ok_prev * (1 + RISE_REL):
            r["_info"].append("capacity_rise_gt_0p5pct")
        ok_prev = r["q_mean_ah"]

    # ---- reference capacity and retention ----
    good = [r for r in rows if not r["_flags"] and np.isfinite(r["q_mean_ah"])]
    et = [r for r in good if r["kind"] == "ET"]
    first_cu = next((r for r in good if r["kind"] in ("CU", "exCU")), None)
    ref = et[0] if et else first_cu
    for r in rows:
        r["q_ref_ah"] = ref["q_mean_ah"] if ref else np.nan
        r["ref_kind"] = (ref["kind"] if ref else "")
        r["retention"] = r["q_mean_ah"] / ref["q_mean_ah"] if ref else np.nan
        r["retention_vs_first_cu"] = r["q_mean_ah"] / first_cu["q_mean_ah"] if first_cu else np.nan

    # ---- cell record ----
    n_exp_cu = sum(1 for k in (seq or {}).values() if k == "CU") if seq is not None else None
    n_cu_present = sum(1 for r in rows if r["kind"] == "CU")
    cell = {
        "serial": serial, "n_capacity_rows": len(rows), "n_cu_present": n_cu_present,
        "n_cu_expected": n_exp_cu if n_exp_cu is not None else np.nan,
        "n_excu_expected": sum(1 for k in (seq or {}).values() if k == "exCU") if seq is not None else np.nan,
        "has_member_list": seq is not None, "member_list_source": seq_src,
        "complete": (n_cu_present == n_exp_cu) if n_exp_cu is not None else np.nan,
        "n_qc_pass": len(good), "first_test_source": first_src or "",
        "csv_files_other": sum(1 for (i, k, t) in files["csv"] if k not in ("CU",)),
    }
    cell["_flags_any"] = sorted({f for r in rows for f in r["_flags"]})
    # the cell is complete only if no CU csv is missing; meta-only CU files (csv pending) are reported
    metas_cu = [k for k in files["meta"] if k[1] == "CU"]
    cell["n_cu_meta_without_csv"] = sum(1 for k in metas_cu if k not in files["csv"])
    return rows, cell


# ----------------------------------------------------------------------------------------------
# driver
# ----------------------------------------------------------------------------------------------
def _analyse_one(path: str) -> dict:
    return analyse_capacity_csv(path)


def load_cache(use: bool) -> dict:
    if use and CACHE.exists():
        try:
            c = json.loads(CACHE.read_text(encoding="utf-8"))
            if c.get("version") == CODE_VERSION:
                return c["files"]
        except Exception:  # noqa: BLE001
            pass
    return {}


def analyse_all(paths: list[Path], jobs: int, use_cache: bool) -> dict:
    cache = load_cache(use_cache)
    result, todo = {}, []
    for p in paths:
        st = p.stat()
        key = f"{st.st_size}:{st.st_mtime_ns}"
        hit = cache.get(str(p))
        if hit and hit["key"] == key:
            result[str(p)] = hit["res"]
        else:
            todo.append((p, key))
    print(f"files: {len(paths)} capacity csv, {len(paths) - len(todo)} from cache, {len(todo)} to analyse", flush=True)
    t0 = time.time()
    if todo:
        if jobs > 1:
            with ProcessPoolExecutor(max_workers=jobs) as ex:
                outs = list(ex.map(_analyse_one, [str(p) for p, _ in todo], chunksize=4))
        else:
            outs = [analyse_capacity_csv(str(p)) for p, _ in todo]
        for (p, key), o in zip(todo, outs):
            result[str(p)] = o
            cache[str(p)] = {"key": key, "res": o}
        print(f"analysed {len(todo)} files in {time.time() - t0:.0f} s", flush=True)
    if use_cache:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"version": CODE_VERSION, "files": cache}), encoding="utf-8")
    return result


STAGE_SPLIT = dt.date(2022, 7, 1)   # stage 1 tests started Sep-Oct 2021, stage 2 in Jan-Feb 2023 (observed in the meta files)


def load_design() -> pd.DataFrame:
    m = pd.read_csv(META_CSV, skipinitialspace=True)
    m.columns = [c.strip() for c in m.columns]
    m["serial_internal"] = m["serial_internal"].astype(str).str.strip()
    return m


def resolve_design(serial: str, metas: list[dict], design: pd.DataFrame) -> tuple[pd.Series | None, str, list[str]]:
    """Design row of a downloaded cell folder.

    experiments_meta.csv `serial` is NOT unique: stage 1 and stage 2 reuse the names TP_k01_01 ... with different
    conditions and cells (141 distinct names for 279 cells; the figshare zips share the names too). The stage
    is therefore decided from the files: (1) the internal cell serial in the meta text equals a candidate's
    serial_internal, else (2) the laboratory identifier singles out one candidate, else (3) the first test
    date (stage 1 started 2021, stage 2 in 2023).
    """
    notes: list[str] = []
    cands = design[design["serial"] == serial]
    if cands.empty:
        return None, "not_in_design", notes
    dates = [m["date"] for m in metas if m["date"]]
    by_date = None
    if dates:
        by_date = 1 if min(dates) < STAGE_SPLIT else 2
    if len(cands) == 1:
        return cands.iloc[0], "unique_name", notes
    ints = {m["internal_serial"].strip().upper() for m in metas if m["internal_serial"]}
    hit = cands[cands["serial_internal"].str.upper().isin(ints)]
    if len(hit) == 1:
        row, how = hit.iloc[0], "internal_serial"
    else:
        labs = {m["lab"] for m in metas if m["lab"]}
        hit = cands[cands["lab"].isin(labs)]
        if len(hit) == 1:
            row, how = hit.iloc[0], "lab"
        elif by_date is not None and len(cands[cands["stage"] == by_date]) == 1:
            row, how = cands[cands["stage"] == by_date].iloc[0], "date"
        else:
            return None, "ambiguous", notes
    if by_date is not None and int(row["stage"]) != by_date:
        notes.append(f"stage_conflict: {how} says stage {int(row['stage'])}, first-test date says stage {by_date}")
    if ints and row["serial_internal"].upper() not in ints:
        notes.append(f"meta_internal_serial_differs_from_table: {sorted(ints)} vs {row['serial_internal']}")
    return row, how, notes


def name_of_folder(folder: Path) -> str:
    names = [FILE_RE.match(p.name).group("serial") for p in folder.iterdir() if FILE_RE.match(p.name)]
    if not names:
        return folder.name.split("__")[0]
    return max(set(names), key=names.count)


def build(jobs: int = 2, use_cache: bool = True):
    design = load_design()
    issues: list[dict] = []
    folders = sorted(p for p in RAW.iterdir() if p.is_dir()) if RAW.exists() else []
    cap_paths = []
    for f in folders:
        for p in sorted(f.iterdir()):
            m = FILE_RE.match(p.name)
            if m and m.group("csv") and not m.group("meta"):
                if m.group("kind") in ("CU", "exCU") or (m.group("kind") in ("ET", "AT") and m.group("temp") == str(REF_TEMP_C)):
                    cap_paths.append(p)
    analysed = analyse_all(cap_paths, jobs, use_cache)

    all_rows, cells, seen_ids, mapping = [], [], {}, []
    for f in folders:
        serial = name_of_folder(f)
        if serial != f.name.split("__")[0]:
            issues.append({"serial": serial, "file": f.name, "issue": "folder_name_differs_from_file_names", "detail": ""})
        metas = [read_meta_file(p) for p in classify_files(f)["meta"].values()]
        cond, how, notes = resolve_design(serial, metas, design)
        for n in notes:
            issues.append({"serial": serial, "file": "", "issue": n.split(":")[0], "detail": n})
        if cond is None:
            issues.append({"serial": serial, "file": "", "issue": f"design_row_{how}", "detail": ""})
        cell_id = f"{serial}_s{int(cond['stage'])}" if cond is not None else f"{serial}_s?"
        if cell_id in seen_ids:
            issues.append({"serial": serial, "file": f.name, "issue": "two_folders_same_cell", "detail": f"{cell_id}: {seen_ids[cell_id]} and {f.name}"})
        seen_ids[cell_id] = f.name
        # cross-check against the design with an independent field: the chamber set point of ZYK (cycling) files
        # is the ageing temperature of the test point; ET / CU files are at 10 / 23 / 45 / 23 C regardless
        checks = []
        if cond is not None:
            for (i_, k_, t_), pth in classify_files(f)["meta"].items():
                if k_ == "ZYK":
                    sp = read_meta_file(pth)["setpoint_c"]
                    if sp is not None and abs(sp - float(cond["amb_temp_tp"])) > 0.5:
                        issues.append({"serial": serial, "file": pth.name, "issue": "zyk_setpoint_differs_from_design", "detail": f"{sp} vs {cond['amb_temp_tp']}"})
                        checks.append("zyk_setpoint_MISMATCH")
                    elif sp is not None:
                        checks.append("zyk_setpoint_ok")
                    break
        dts = [m["date"] for m in metas if m["date"]]
        mapping.append({"folder": f.name, "serial": serial, "stage": int(cond["stage"]) if cond is not None else "", "cell_id": cell_id,
                        "assigned_by": how, "lab_meta": ",".join(sorted({m["lab"] for m in metas if m["lab"]})),
                        "internal_serial_meta": ",".join(sorted({m["internal_serial"] for m in metas if m["internal_serial"]})),
                        "internal_serial_design": cond["serial_internal"] if cond is not None else "",
                        "first_meta_date": min(dts).isoformat() if dts else "", "last_meta_date": max(dts).isoformat() if dts else "",
                        "design_T_C": cond["amb_temp_tp"] if cond is not None else "", "notes": "; ".join(notes + checks)})
        rows, cell = process_cell(serial, cond, f, analysed, issues)
        for r in rows:
            for a, b in (("T_C", "amb_temp_tp"), ("SOC_max", "soc_max_tp"), ("DoD", "dod_tp"), ("C_ch", "c_ch_tp"), ("C_dch", "c_dch_tp"),
                         ("lab", "lab"), ("tp", "tp"), ("cell", "cell"), ("stage", "stage"), ("sampling", "sampling")):
                r[a] = cond[b] if cond is not None else np.nan
            r["cell_id"], r["stage_match"] = cell_id, how
            r["type"] = serial[3]
            r["flags"] = ";".join(r.pop("_flags"))
            r["info_flags"] = ";".join(r.pop("_info"))
            r["qc_pass"] = (r["flags"] == "") and bool(np.isfinite(r["q_mean_ah"]))
            r.pop("_date", None)
            r["efc_method"] = ("analytic: FEC/h = C_ch*C_dch/(C_ch+C_dch), CC only, zero rest, exposure = 7 d at the first check-up (design schedule) + calendar gaps - check-up file durations "
                               "(CU measured, exCU 30 h); NOT validated against ZYK") if r["type"] == "z" else ""
            all_rows.append(r)
        cell.update({"cell_id": cell_id, "stage_match": how, "folder": f.name,
                     "endpoint_only_cell": bool(cond is not None and cond["type"] == "k" and int(cond["cell"]) >= 4)})
        if cond is not None:
            cell.update({"type": cond["type"], "lab": cond["lab"], "tp": int(cond["tp"]), "cell": int(cond["cell"]), "stage": int(cond["stage"]),
                         "T_C": cond["amb_temp_tp"], "SOC_max": cond["soc_max_tp"], "DoD": cond["dod_tp"], "C_ch": cond["c_ch_tp"], "C_dch": cond["c_dch_tp"],
                         "sampling": cond["sampling"]})
        cells.append(cell)

    df = pd.DataFrame(all_rows)
    cells_df = pd.DataFrame(cells)
    cols = ["cell_id", "serial", "stage_match", "type", "lab", "tp", "cell", "stage", "sampling", "T_C", "SOC_max", "DoD", "C_ch", "C_dch",
            "kind", "file_idx", "cu_idx", "test_temp_c", "meas_start_date", "first_test_date", "first_test_source",
            "elapsed_days", "gap_days_prev", "exposure_days_est", "exposure_anchor", "exposure_days_est_et_route", "interval_exposure_days_est", "n_events_before", "n_skipped_events_prev", "events_kinds_assumed",
            "q_dch_ah", "q_ch_ah", "q_mean_ah", "q_ref_ah", "ref_kind", "retention", "retention_vs_first_cu",
            "efc_est_interval", "efc_est_cum", "efc_est_interval_rest300s", "efc_est_cum_rest300s", "efc_method",
            "dur_dch_h", "dur_ch_h", "i_dch_med_a", "file_hours", "active_hours", "t_surf_dch_start_c", "t_surf_dch_mean_c", "amb_median_c", "chamber_setpoint_c",
            "flags", "info_flags", "qc_pass"]
    if len(df):
        df = df[cols].sort_values(["type", "cell_id", "file_idx"]).reset_index(drop=True)
    else:
        df = pd.DataFrame(columns=cols)
    build.mapping = pd.DataFrame(mapping)
    return df, cells_df, issues, design, folders


def cell_gap_table(df: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    g = []
    for s, d in df.groupby("cell_id"):
        d = d[d.kind.isin(["CU", "exCU", "ET"])].sort_values("file_idx")
        gaps = d["gap_days_prev"].dropna().astype(int).tolist()
        g.append({"cell_id": s, "n_checkups": int(len(d)),
                  "gaps_days": ";".join(map(str, gaps)), "median_gap_days": float(np.median(gaps)) if gaps else np.nan,
                  "max_gap_days": max(gaps) if gaps else np.nan, "first_elapsed_days": d["elapsed_days"].min(),
                  "last_elapsed_days": d["elapsed_days"].max()})
    gt = pd.DataFrame(g)
    out = cells.drop(columns=[c for c in cells.columns if c.startswith("_")]).merge(gt, on="cell_id", how="left") if len(gt) else cells
    return out


def summarise(df, cells, issues, design) -> dict:
    s: dict = {"generated": dt.datetime.now().isoformat(timespec="seconds"), "code_version": CODE_VERSION}
    s["cells_in_design"] = int(len(design))
    s["cells_dirs_present"] = int(len(cells))
    s["cells_with_capacity_rows"] = int(cells.n_capacity_rows.gt(0).sum()) if len(cells) else 0
    s["checkup_rows"] = int(len(df))
    s["rows_by_kind"] = df.kind.value_counts().to_dict() if len(df) else {}
    s["qc_pass_rows"] = int(df.qc_pass.sum()) if len(df) else 0
    s["rows_by_type"] = df.groupby("type").size().to_dict() if len(df) else {}
    if len(df):
        flag_counts: dict = {}
        for f in df["flags"]:
            for x in filter(None, f.split(";")):
                flag_counts[x] = flag_counts.get(x, 0) + 1
        s["flag_counts"] = flag_counts
        info_counts: dict = {}
        for f in df.info_flags:
            for x in filter(None, f.split(";")):
                info_counts[x] = info_counts.get(x, 0) + 1
        s["info_counts"] = info_counts
    if len(cells):
        s["cells_complete_cu"] = int(cells.complete.fillna(False).astype(bool).sum())
        s["cells_without_member_list"] = int((~cells.has_member_list).sum())
        s["cells_meta_cu_without_csv"] = int((cells.n_cu_meta_without_csv > 0).sum())
        traj = cells[cells.n_qc_pass >= 3] if "n_qc_pass" in cells else cells.iloc[0:0]
        s["cells_with_trajectory_ge3"] = {k: int(v) for k, v in traj.groupby("type").size().items()}
        s["cells_with_trajectory_ge5"] = {k: int(v) for k, v in cells[cells.n_qc_pass >= 5].groupby("type").size().items()}
        cond_cols = ["type", "T_C", "SOC_max", "DoD", "C_ch", "C_dch"]
        s["conditions_in_design"] = int(design.assign(type=design["type"]).rename(columns={"amb_temp_tp": "T_C", "soc_max_tp": "SOC_max", "dod_tp": "DoD", "c_ch_tp": "C_ch", "c_dch_tp": "C_dch"})[cond_cols].drop_duplicates().shape[0])
        s["conditions_with_trajectory_ge3"] = int(traj[cond_cols].drop_duplicates().shape[0]) if len(traj) else 0
        s["conditions_with_trajectory_ge3_by_type"] = {k: int(v[cond_cols].drop_duplicates().shape[0]) for k, v in traj.groupby("type")} if len(traj) else {}
        s["conditions_present_by_type"] = {k: int(v[cond_cols].drop_duplicates().shape[0]) for k, v in cells.groupby("type")}
    if len(df):
        d = df[df.kind.isin(["CU", "exCU"])]
        s["cadence_gap_days_by_type"] = {t: {"n": int(x.gap_days_prev.notna().sum()), "median": float(x.gap_days_prev.median()), "min": float(x.gap_days_prev.min()),
                                              "max": float(x.gap_days_prev.max()), "q25": float(x.gap_days_prev.quantile(.25)), "q75": float(x.gap_days_prev.quantile(.75))}
                                          for t, x in d.groupby("type") if x.gap_days_prev.notna().any()}
        s["first_checkup_elapsed_days_by_type"] = {t: {"median": float(x.groupby("cell_id").elapsed_days.min().median()),
                                                          "min": float(x.groupby("cell_id").elapsed_days.min().min()), "max": float(x.groupby("cell_id").elapsed_days.min().max())}
                                                   for t, x in d.groupby("type")}
    s["issue_counts"] = pd.Series([i["issue"] for i in issues]).value_counts().to_dict() if issues else {}
    return s


def conditions_table(cells: pd.DataFrame, design: pd.DataFrame) -> pd.DataFrame:
    """Per condition: cells in the design, cells downloaded, cells with >= 3 quality-passed check-ups."""
    key = ["type", "T_C", "SOC_max", "DoD", "C_ch", "C_dch"]
    d = design.rename(columns={"amb_temp_tp": "T_C", "soc_max_tp": "SOC_max", "dod_tp": "DoD", "c_ch_tp": "C_ch", "c_dch_tp": "C_dch"})
    t = d.groupby(key).agg(cells_in_design=("serial_internal", "size"), stages=("stage", lambda x: ",".join(map(str, sorted(set(x)))))).reset_index()
    if len(cells):
        c = cells.groupby(key).agg(cells_downloaded=("cell_id", "size"), cells_with_rows=("n_capacity_rows", lambda x: int((x > 0).sum())),
                                   cells_traj_ge3=("n_qc_pass", lambda x: int((x >= 3).sum())), capacity_rows=("n_capacity_rows", "sum")).reset_index()
        t = t.merge(c, on=key, how="left")
    for col in ("cells_downloaded", "cells_with_rows", "cells_traj_ge3", "capacity_rows"):
        if col in t:
            t[col] = t[col].fillna(0).astype(int)
    return t.sort_values(key).reset_index(drop=True)


def git_head() -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--no-cache", action="store_true")
    a = ap.parse_args(argv)
    df, cells, issues, design, folders = build(a.jobs, not a.no_cache)
    cells_full = cell_gap_table(df, cells)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CHECKUPS, index=False)
    cells_full.to_csv(OUT_CELLS, index=False)
    summ = summarise(df, cells_full, issues, design)
    (RUN_DIR / "metrics.json").write_text(json.dumps(summ, indent=2, default=str), encoding="utf-8")
    (RUN_DIR / "config.json").write_text(json.dumps({
        "code_version": CODE_VERSION, "git_commit": git_head(), "raw_dir": str(RAW),
        "thresholds": {"dch_dur_h": DCH_DUR_H, "ch_dur_h": CH_DUR_H, "dch_current_a": DCH_CURRENT_A, "ch_current_a": CH_CURRENT_A,
                       "cap_range_ah": CAP_RANGE_AH, "ch_dch_mismatch": CH_DCH_MISMATCH, "step_gap_s": STEP_GAP_S,
                       "outlier_rel": OUTLIER_REL, "outlier_drop_mult": OUTLIER_DROP_MULT, "rise_rel": RISE_REL, "rest_sensitivity_s": REST_SENSITIVITY_S},
        "nominal_durations_h": DUR_H, "q_nom_ah": Q_NOM_AH,
        "output_sha256": {OUT_CHECKUPS.name: hashlib.sha256(OUT_CHECKUPS.read_bytes()).hexdigest()}}, indent=2), encoding="utf-8")
    pd.DataFrame(issues, columns=["serial", "file", "issue", "detail"]).to_csv(RUN_DIR / "issues.csv", index=False)
    cells_full.to_csv(RUN_DIR / "cells_summary.csv", index=False)
    conditions_table(cells_full, design).to_csv(RUN_DIR / "conditions_summary.csv", index=False)
    build.mapping.to_csv(RUN_DIR / "folder_mapping.csv", index=False)
    print(json.dumps({k: summ[k] for k in ("cells_in_design", "cells_dirs_present", "cells_with_capacity_rows", "checkup_rows", "qc_pass_rows")}, indent=2))
    return df, cells_full, issues


if __name__ == "__main__":
    main()
