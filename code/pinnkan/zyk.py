"""ZYK-logged throughput for the cycling cells (PREREG_v3 section 5, freeze blocker FB-5).

STATUS: built against the DOCUMENTED file format only; no ZYK file of the Samsung download is on disk (one `_meta.txt` exists). The format is taken from
`runs/pilot_P0/RESULT.md` and the member listings `runs/pilot_P0/*_members.tsv` plus the dataset-paper note (`notes/papers/samsung50e_dataset_paper.md`):
    * one CSV per cycling segment, named `<serial>_<idx>_ZYK.csv`, idx = the two-digit file number of the cell (ET 01, ZYK 02, CU 03, ZYK 04, CU 05, ZYK 06,
      exCU 07, ... so a ZYK file with number i lies between the check-up files before and after it);
    * columns `run_time` (HH:MM:SS.sss, hours may exceed 24), `c_vol` [V], `c_cur` [A, NEGATIVE during discharge], `c_surf_temp`, `amb_temp`, `step_type`.
Fixed by D024 (2026-11-05, after the full release was read): the completeness rule (constants below) and the DoD classes `DOD_CLASS_EDGES` = (0.15, 0.35)
(low = DoD 0.05 to 0.15, mid = 0.20 to 0.35, high = 0.40 to 0.60). The table is built by code/data/samsung_full_audit.py, which streams the ZYK csv from the zips.
Definition. Equivalent full cycles of a segment = discharged charge / rated capacity, EFC = integral of max(-I, 0) dt / (3600 * Q_NOM_AH). This is the same
definition the analytic estimate of the pipeline uses (`fec_per_hour`: one cycle of depth DoD discharges DoD * Q_nom, i.e. DoD equivalent full cycles), Q_nom = 4.9 Ah
(`data.samsung_checkups.Q_NOM_AH`). The charge side (integral of max(I, 0) dt) is recorded as a cross-check.
Cumulative throughput at a check-up file i = sum of the EFC of the complete ZYK segments with number < i. Segments with missing log data (file absent from the
download although the member list names it, or a sampling gap longer than `GAP_FLAG_S`) are not summed: the interval between the two surrounding check-ups takes the
designed (analytic) throughput of that interval (prereg 3.3(4), last sentence). Nothing is guessed: if a cycling cell has no ZYK information at all, `throughput='zyk'`
raises `ZykDataMissing` unless the fallback flag `throughput_fallback='analytic'` is set (then the whole cell uses the analytic estimate and meta records it)."""
import os
import re

import numpy as np
import pandas as pd

Q_NOM_AH = 4.9                  # = data.samsung_checkups.Q_NOM_AH (asserted in the tests)
# Segment completeness rule, fixed by D024 (judge, 2026-11-05, section 1): a gap loses or invents throughput only if an endpoint carries current, so
#   incomplete  iff  (a gap > GAP_FLAG_S with at least one endpoint |I| > ACTIVE_I_A)  or  (a rest-only gap > REST_GAP_MAX_S)  or  time not monotonic
#                    or  NaN current  or  fewer than MIN_ROWS rows  or  the file is absent from the download (missing_file).
# The longest gap of any kind (dt_max_s) is information only.
ACTIVE_I_A = 0.05               # five times below the smallest designed current (C/20 = 0.245 A)
GAP_FLAG_S = 600.0              # 60 samples at the 10 s logging interval while active
REST_GAP_MAX_S = 86400.0        # a rest-only gap longer than 24 h could hide a multi-day window
MIN_ROWS = 10
DOD_CLASS_EDGES = (0.15, 0.35)  # [ASSUMPTION, prereg 5 does not define "DoD class"] low <= 0.15 < mid <= 0.35 < high
IMBALANCE_INFO = 0.05           # info flag: |charge - discharge| / discharge above this
ZYK_RE = re.compile(r"^(?P<serial>TP_[kz]\d{2}_\d{2})_(?P<idx>\d{2})_ZYK\.csv$")
ZYK_TABLE_REL = os.path.join("data", "processed", "samsung_zyk_efc.csv")
TABLE_COLS = ["cell_id", "serial", "file_idx", "discharge_ah", "charge_ah", "efc", "hours", "dt_max_s", "dt_max_active_s", "i_dch_med_a", "n_rows", "complete", "flags"]


class ZykDataMissing(RuntimeError):
    """throughput='zyk' was requested but the ZYK table (or a cycling cell's entries in it) is not on disk"""


def _parse_time(s):
    return pd.to_timedelta(pd.Series(s).astype(str).str.strip(), errors="coerce").dt.total_seconds().to_numpy(float)


def segment_from_arrays(t_s, cur_a, gap_flag_s=GAP_FLAG_S, q_nom=Q_NOM_AH):
    """EFC and diagnostics of one ZYK segment from time [s] and current [A, negative on discharge] (trapezoid rule on the samples). `complete` follows the D024 rule
    (see the constants above); `dt_max_active_s` is the longest gap with an endpoint above ACTIVE_I_A, `i_dch_med_a` the median |I| of the samples below -ACTIVE_I_A."""
    t, i = np.asarray(t_s, float), np.asarray(cur_a, float)
    flags = []
    nan_row = dict(discharge_ah=np.nan, charge_ah=np.nan, efc=np.nan, hours=np.nan, dt_max_s=np.nan, dt_max_active_s=np.nan, i_dch_med_a=np.nan, n_rows=int(len(t)),
                   complete=False)
    if len(t) < 2 or np.isnan(t).any():
        return dict(nan_row, flags="unparsable_time_or_too_short")
    if np.isnan(i).any():
        flags.append("nan_current")
        i = np.nan_to_num(i)
    if len(t) < MIN_ROWS:
        flags.append("fewer_than_10_rows")
    dt = np.diff(t)
    if (dt < 0).any():
        flags.append("time_not_monotonic")
    dis = float(np.sum(0.5 * (np.minimum(i[1:], 0.0) + np.minimum(i[:-1], 0.0)) * dt)) / -3600.0     # positive discharged Ah
    chg = float(np.sum(0.5 * (np.maximum(i[1:], 0.0) + np.maximum(i[:-1], 0.0)) * dt)) / 3600.0
    active = (np.abs(i[1:]) > ACTIVE_I_A) | (np.abs(i[:-1]) > ACTIVE_I_A)
    dtmax = float(dt.max())
    dtact = float(dt[active].max()) if active.any() else 0.0
    dtrest = float(dt[~active].max()) if (~active).any() else 0.0
    if dtact > gap_flag_s:
        flags.append("active_gap")
    if dtrest > REST_GAP_MAX_S:
        flags.append("rest_gap_gt_24h")
    if dis > 0 and abs(chg - dis) / dis > IMBALANCE_INFO:
        flags.append("info_charge_discharge_imbalance")
    dch = i[i < -ACTIVE_I_A]
    complete = not any(f in ("active_gap", "rest_gap_gt_24h", "time_not_monotonic", "nan_current", "fewer_than_10_rows") for f in flags)
    return dict(discharge_ah=dis, charge_ah=chg, efc=dis / q_nom, hours=float((t[-1] - t[0]) / 3600.0), dt_max_s=dtmax, dt_max_active_s=dtact,
                i_dch_med_a=float(np.median(np.abs(dch))) if dch.size else np.nan, n_rows=int(len(t)), complete=bool(complete), flags=";".join(flags))


def read_zyk_segment(path, gap_flag_s=GAP_FLAG_S, q_nom=Q_NOM_AH):
    """one ZYK csv -> dict as `segment_from_arrays`; an unreadable file is an incomplete segment with a flag, never an exception"""
    try:
        d = pd.read_csv(path, usecols=lambda c: c.strip() in ("run_time", "c_cur"), low_memory=False)
        d.columns = [c.strip() for c in d.columns]
        t = _parse_time(d["run_time"])
        cur = pd.to_numeric(d["c_cur"], errors="coerce").to_numpy(float)
    except Exception as e:  # noqa: BLE001
        return dict(discharge_ah=np.nan, charge_ah=np.nan, efc=np.nan, hours=np.nan, dt_max_s=np.nan, dt_max_active_s=np.nan, i_dch_med_a=np.nan, n_rows=0, complete=False,
                    flags=f"read_error:{type(e).__name__}")
    return segment_from_arrays(t, cur, gap_flag_s, q_nom)


def build_zyk_table(folders, expected=None, gap_flag_s=GAP_FLAG_S):
    """folders: {cell_id: folder path}; expected: optional {cell_id: set of ZYK file numbers the member list names}. One row per ZYK file (present, or named by the
    member list and absent = incomplete 'missing_file'). -> DataFrame[TABLE_COLS]"""
    rows = []
    for cid, folder in sorted(folders.items()):
        seen = set()
        serial = None
        for f in sorted(os.listdir(folder)):
            m = ZYK_RE.match(f)
            if not m:
                continue
            serial = m.group("serial")
            idx = int(m.group("idx"))
            seen.add(idx)
            r = read_zyk_segment(os.path.join(folder, f), gap_flag_s)
            rows.append(dict(cell_id=cid, serial=serial, file_idx=idx, **r))
        for idx in sorted((expected or {}).get(cid, set()) - seen):
            rows.append(dict(cell_id=cid, serial=serial or cid.rsplit("_s", 1)[0], file_idx=int(idx), discharge_ah=np.nan, charge_ah=np.nan, efc=np.nan, hours=np.nan,
                             dt_max_s=np.nan, dt_max_active_s=np.nan, i_dch_med_a=np.nan, n_rows=0, complete=False, flags="missing_file"))
    return pd.DataFrame(rows, columns=TABLE_COLS)


def attach_zyk_cumulative(checkups, table, fallback="none"):
    """Adds `efc_zyk_cum` (cumulative EFC at each row of the check-up table, forward in file order) and `zyk_interval_source` ('logged' | 'analytic_fallback' |
    'cell_analytic' | 'none') to the check-up rows. `checkups` is the UNFILTERED pipeline table (so that the segments before dropped or QC-failed check-ups still count).
    Cycling cells (type 'z') only; storage rows get 0. Per interval between consecutive rows a, b of a cell (rows ordered by file_idx; the first interval starts at the
    start of the record): every ZYK file with a < number < b must be present and complete, then the interval throughput is their sum; otherwise it is the analytic
    interval `efc_est_cum[b] - efc_est_cum[a]` (the designed throughput). A cycling cell with no row in `table` at all raises ZykDataMissing unless
    fallback == 'analytic' (then every interval of the cell is analytic and marked 'cell_analytic')."""
    if fallback not in ("none", "analytic"):
        raise ValueError(fallback)
    df = checkups.copy()
    df["efc_zyk_cum"] = 0.0
    df["zyk_interval_source"] = "none"
    by_cell = {c: g for c, g in table.groupby("cell_id")} if len(table) else {}
    for cid, g in df.groupby("cell_id", sort=False):
        if str(g["type"].iloc[0]) != "z":
            continue
        order = g.sort_values("file_idx", kind="stable")
        idxs = order["file_idx"].to_numpy(int)
        ana = order["efc_est_cum"].to_numpy(float)
        tb = by_cell.get(cid)
        if tb is None:
            if fallback != "analytic":
                raise ZykDataMissing(f"cycling cell {cid}: no ZYK file information in the ZYK table (download the ZYK files and rebuild {ZYK_TABLE_REL}, or set "
                                     "throughput_fallback='analytic' for a sensitivity run); the analytic estimate is not used silently")
            df.loc[order.index, "efc_zyk_cum"] = np.where(np.isfinite(ana), ana, 0.0)
            df.loc[order.index, "zyk_interval_source"] = "cell_analytic"
            continue
        z_idx = tb["file_idx"].to_numpy(int)
        z_efc = tb["efc"].to_numpy(float)
        z_ok = tb["complete"].to_numpy(bool) & np.isfinite(z_efc)
        cum, prev_idx, prev_ana, srcs = 0.0, 0, 0.0, []
        out = []
        for k, (ix, an) in enumerate(zip(idxs, ana)):
            sel = (z_idx > prev_idx) & (z_idx < ix)
            if sel.any() and not z_ok[sel].all():
                step = (an - prev_ana) if (np.isfinite(an) and np.isfinite(prev_ana)) else np.nan
                src = "analytic_fallback"
            else:
                step, src = float(z_efc[sel].sum()), "logged"
            cum = cum + (step if np.isfinite(step) else 0.0)
            srcs.append(src if np.isfinite(step) else "none")
            out.append(cum)
            prev_idx, prev_ana = ix, (an if np.isfinite(an) else prev_ana)
        df.loc[order.index, "efc_zyk_cum"] = out
        df.loc[order.index, "zyk_interval_source"] = srcs
    return df


def load_zyk_table(root):
    p = os.path.join(root, ZYK_TABLE_REL)
    if not os.path.isfile(p):
        raise ZykDataMissing(f"{ZYK_TABLE_REL} does not exist: the ZYK segment files are not downloaded/parsed yet (prereg 5, FB-5). Build it with "
                             "`python -P -m pinnkan.zyk --build` after the download, or use throughput='analytic'.")
    t = pd.read_csv(p)
    t["complete"] = t["complete"].astype(str).str.lower().isin(["true", "1"])
    return t


def dod_class(dod, edges=DOD_CLASS_EDGES):
    return int(np.searchsorted(np.asarray(edges, float), dod, side="left"))


def validate_throughput(checkups_with_zyk, edges=DOD_CLASS_EDGES, min_cells=2, med_tol=0.05, last_tol=0.10):
    """Prereg 5 validation rule [FB-5]. `checkups_with_zyk`: the check-up table after `attach_zyk_cumulative` (columns cell_id, type, lab, DoD, efc_est_cum,
    efc_zyk_cum, file_idx, kind; cycling rows only are used). For each sampled cycling cell the relative difference |analytic - logged| / logged of the throughput
    accumulated since the cell's first check-up row (CU/exCU), at EVERY check-up. Coverage: at least `min_cells` sampled cells per (DoD class, laboratory) among the
    classes and laboratories present in the sample. Accept analytic throughput iff coverage holds, the median absolute relative difference over all (cell, check-up)
    pairs is <= med_tol and no cell exceeds last_tol at its last check-up; otherwise the ZYK-logged throughput is used for every cycling cell.
    Only intervals whose source is 'logged' enter (an analytic-fallback interval is trivially equal)."""
    d = checkups_with_zyk
    d = d[(d["type"] == "z") & d["kind"].isin(["CU", "exCU"])].sort_values(["cell_id", "file_idx"])
    rows = []
    n_nonfinite, cells_nonfinite = 0, []
    for cid, g in d.groupby("cell_id"):
        if (g["zyk_interval_source"] != "logged").any() or len(g) < 2:
            continue
        a = g["efc_est_cum"].to_numpy(float)
        z = g["efc_zyk_cum"].to_numpy(float)
        a, z = a[1:] - a[0], z[1:] - z[0]
        ok = z > 0
        if not ok.any():
            continue
        rel = np.abs(a[ok] - z[ok]) / z[ok]
        # a check-up whose analytic throughput is undefined (no usable start date) cannot be compared: it is dropped from the pairs and counted; "last check-up" is then
        # the last comparable one
        fin = np.isfinite(rel)
        if not fin.all():
            n_nonfinite += int((~fin).sum())
            cells_nonfinite.append(cid)
        rel = rel[fin]
        if not rel.size:
            continue
        rows.append(dict(cell_id=cid, lab=str(g["lab"].iloc[0]), dod=float(g["DoD"].iloc[0]), dod_class=dod_class(float(g["DoD"].iloc[0]), edges), rel=rel,
                         rel_last=float(rel[-1]), n_checkups=int(ok.sum())))
    if not rows:
        return dict(accept_analytic=False, reason="no cycling cell with logged intervals", n_cells=0)
    cov = {}
    for r in rows:
        cov.setdefault((r["dod_class"], r["lab"]), []).append(r["cell_id"])
    short = {f"class{c}|{l}": len(v) for (c, l), v in cov.items() if len(v) < min_cells}
    allrel = np.concatenate([r["rel"] for r in rows])
    med = float(np.median(allrel))
    worst_last = max(r["rel_last"] for r in rows)
    over = [r["cell_id"] for r in rows if r["rel_last"] > last_tol]
    accept = bool(not short and med <= med_tol and not over)
    return dict(accept_analytic=accept, coverage_ok=bool(not short), cells_per_class_lab={f"class{c}|{l}": len(v) for (c, l), v in sorted(cov.items())},
                n_pairs_dropped_analytic_undefined=n_nonfinite, cells_with_dropped_pairs=cells_nonfinite, short_cells=short, median_abs_rel_diff=med, worst_last_checkup_rel_diff=float(worst_last), cells_over_last_tol=over, n_cells=len(rows),
                n_pairs=int(len(allrel)), median_tol=med_tol, last_tol=last_tol, dod_class_edges=list(edges),
                decision="analytic throughput accepted" if accept else "use ZYK-logged throughput for every cycling cell (or complete the sample if coverage is short)")


GAP_VARIANTS = ("ruled", "active60", "anygap")


def apply_gap_variant(tab, variant="ruled"):
    """`ruled`: the table as built (D024 rule). `active60`: information variant, a segment is also incomplete if a gap above 60 s has an active endpoint.
    `anygap`: information variant (the pre-D024 code), a segment is also incomplete if any gap, rest or active, exceeds GAP_FLAG_S."""
    t = tab.copy()
    if variant == "ruled":
        return t
    col, lim = ("dt_max_active_s", 60.0) if variant == "active60" else ("dt_max_s", GAP_FLAG_S)
    ok = pd.to_numeric(t[col], errors="coerce") <= lim
    t["complete"] = t["complete"].astype(bool) & ok.fillna(False).to_numpy(bool)
    return t


def validate_from_root(root, edges=DOD_CLASS_EDGES, fallback="none", variant="ruled"):
    """FB-5 on the files of `root`: pipeline table + ZYK table -> validate_throughput. Only cells that have a ZYK table entry are sampled (cells without one are skipped
    here, not an error: the validation is on a sample). Uses EFC only, no capacity or retention value (the capacity columns of the pipeline table are not loaded)."""
    cu = pd.read_csv(os.path.join(root, "data", "processed", "samsung_checkups.csv"),
                     usecols=["cell_id", "type", "lab", "DoD", "efc_est_cum", "file_idx", "kind"])
    tab = apply_gap_variant(load_zyk_table(root), variant)
    cu = cu[cu["cell_id"].isin(set(tab["cell_id"]))]
    return validate_throughput(attach_zyk_cumulative(cu, tab, fallback), edges)


def main(argv=None):
    import argparse
    from . import ROOT
    ap = argparse.ArgumentParser(description="build data/processed/samsung_zyk_efc.csv from the downloaded ZYK files (stage-aware folders <serial>__f<id>)")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--validate", action="store_true", help="FB-5: compare analytic and ZYK-logged throughput on the cells present in the ZYK table (prereg 5 rule) and print the verdict")
    ap.add_argument("--variants", action="store_true", help="with --validate: also run the information variants (gap above 60 s while active; any gap above 600 s) and report all three")
    ap.add_argument("--out-json", default=None, help="with --validate: write the result here (e.g. runs/samsung_pipeline_full/fb5_validation.json)")
    ap.add_argument("--raw", default=os.path.join(ROOT, "data", "raw", "samsung50e_full_x"))
    ap.add_argument("--mapping", default=os.path.join(ROOT, "runs", "samsung_pipeline", "folder_mapping.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, ZYK_TABLE_REL))
    a = ap.parse_args(argv)
    if a.validate:
        import hashlib
        import json
        res = {"ruled": validate_from_root(ROOT)}
        if a.variants:
            res["information_active_gap_gt_60s"] = validate_from_root(ROOT, variant="active60")
            res["information_any_gap_gt_600s"] = validate_from_root(ROOT, variant="anygap")
        tpath = os.path.join(ROOT, ZYK_TABLE_REL)
        res["inputs"] = {"zyk_table": ZYK_TABLE_REL, "zyk_table_sha256": hashlib.sha256(open(tpath, "rb").read()).hexdigest(),
                         "constants": {"ACTIVE_I_A": ACTIVE_I_A, "GAP_FLAG_S": GAP_FLAG_S, "REST_GAP_MAX_S": REST_GAP_MAX_S, "MIN_ROWS": MIN_ROWS, "DOD_CLASS_EDGES": list(DOD_CLASS_EDGES)}}
        txt = json.dumps(res, indent=1, default=str)
        if a.out_json:
            open(a.out_json, "w", encoding="utf8").write(txt)
            print(f"written {a.out_json} sha256 " + hashlib.sha256(txt.encode()).hexdigest())
        print(txt)
        return
    if not a.build:
        ap.error("--build or --validate")
    from data import samsung_checkups as SC
    mp = pd.read_csv(a.mapping)
    folders, expected = {}, {}
    for _, r in mp.iterrows():
        f = os.path.join(a.raw, r["folder"])
        if str(r["serial"]).startswith("TP_z") and os.path.isdir(f):
            folders[r["cell_id"]] = f
            seq, _ = SC.expected_sequence(r["serial"], r["folder"])
            if seq:
                expected[r["cell_id"]] = {i for i, k in seq.items() if k == "ZYK"}
    t = build_zyk_table(folders, expected)
    t.to_csv(a.out, index=False)
    print(f"{len(t)} ZYK rows for {t['cell_id'].nunique()} cells -> {a.out}")


if __name__ == "__main__":
    main()
