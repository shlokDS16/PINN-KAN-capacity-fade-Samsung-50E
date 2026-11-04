"""P1(b): per-cycle summary of the Sandia (SNL) mirror and a duplicate-record test.

Run:  python -I code/data/snl_cycles.py <ROOT>
Pickles are opened ONLY through the allowlist loader in code/data_audit/verify_raw.py (static opcode scan,
allowlist-only Unpickler); plain pickle.load is never called here.

Per cycle and cell: cycle number, n samples, start/end time [s since first sample], discharge and charge capacity
(max of the cumulative column) [Ah], charge throughput (integral |I| dt) [Ah], mean temperature, mean |current|.
Outputs:
  data/processed/snl_cycles.csv       long table, one row per (cell, cycle)
  data/processed/snl_cells.csv        one row per cell: parsed condition from the file name and metadata
  runs/pilot_P1/snl_duplicates.json   duplicate-record report
"""
import hashlib
import json
import os
import re
import sys
import zipfile

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
sys.path.insert(0, os.path.join(ROOT, "code", "data_audit"))  # trusted project code
import verify_raw as vr  # noqa: E402  (adds the user site-packages to sys.path)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import psutil  # noqa: E402

NAME = re.compile(r"SNL_18650_(?P<chem>LFP|NCA|NMC)_(?P<T>\d+)C_(?P<soc>\d+-\d+)_(?P<rc>[\d.]+)-(?P<rd>[\d.]+)C_(?P<rep>[a-d])")


def summarise(cell):
    rows = []
    cd = cell["cycle_data"]
    t0 = None
    fp = {}
    for c in cd:
        t = np.asarray(c["time_in_s"], dtype=float)
        i = np.asarray(c["current_in_A"], dtype=float)
        qd = np.asarray(c["discharge_capacity_in_Ah"], dtype=float)
        qc = np.asarray(c["charge_capacity_in_Ah"], dtype=float)
        temp = np.asarray(c["temperature_in_C"], dtype=float) if c["temperature_in_C"] is not None else np.array([np.nan])
        if t.size == 0:
            rows.append((c["cycle_number"], 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan))
            continue
        if t0 is None:
            t0 = t[0]
        thr = float(np.trapezoid(np.abs(i), t) / 3600.0) if t.size > 1 else 0.0
        rows.append((int(c["cycle_number"]), int(t.size), float(t[0] - t0), float(t[-1] - t0),
                     float(qd.max()), float(qc.max()), thr, float(np.nanmean(temp)) if np.isfinite(temp).any() else np.nan, float(np.abs(i).mean())))
    return rows


def raw_fingerprint(cell, cycle_idx):
    """SHA-1 of rounded voltage + current of one cycle (raw-record duplicate test)."""
    cd = cell["cycle_data"]
    if not cd:
        return None
    c = cd[min(cycle_idx, len(cd) - 1)]
    v = np.round(np.asarray(c["voltage_in_V"], dtype=float), 4)
    i = np.round(np.asarray(c["current_in_A"], dtype=float), 4)
    return hashlib.sha1(v.tobytes() + i.tobytes()).hexdigest()


def main():
    zpath = os.path.join(ROOT, "data", "raw", "batterylife_processed_snl", "SNL.zip")
    proc = psutil.Process()
    peak = 0
    all_rows, cell_rows, fps = [], [], {}
    with zipfile.ZipFile(zpath) as z:
        members = sorted((i for i in z.infolist() if i.filename.endswith(".pkl")), key=lambda i: i.filename)
        for info in members:
            key = info.filename.split("/")[-1][:-4]
            obj, meta = vr.safe_pickle_load(z.read(info))
            if obj is None:
                raise RuntimeError(f"{key}: not loaded {meta}")
            rows = summarise(obj)
            m = NAME.match(key)
            cell_rows.append({
                "cell": key, "chemistry": m["chem"], "temp_c": int(m["T"]), "soc_window": m["soc"],
                "charge_c": float(m["rc"]), "discharge_c": float(m["rd"]), "replicate": m["rep"],
                "nominal_ah": obj["nominal_capacity_in_Ah"], "n_cycles_record": len(obj["cycle_data"]),
                "depth_of_discharge_meta": obj["depth_of_discharge"],
            })
            n = len(obj["cycle_data"])
            fps[key] = {nm: raw_fingerprint(obj, k) for nm, k in (("first", 0), ("second", 1), ("c100", 99), ("mid", n // 2), ("last", n - 1))}
            for r in rows:
                all_rows.append((key, *r))
            del obj
            peak = max(peak, proc.memory_info().rss)
    cols = ["cell", "cycle", "n_samples", "t_start_s", "t_end_s", "q_dis_ah", "q_chg_ah", "throughput_ah", "temp_mean_c", "abs_current_mean_a"]
    df = pd.DataFrame(all_rows, columns=cols)
    df["cum_throughput_ah"] = df.groupby("cell")["throughput_ah"].cumsum()
    nom = {c["cell"]: c["nominal_ah"] for c in cell_rows}
    df["retention_vs_first"] = df["q_dis_ah"] / df.groupby("cell")["q_dis_ah"].transform("first")
    df["retention_vs_nominal"] = df["q_dis_ah"] / df["cell"].map(nom)
    outdir = os.path.join(ROOT, "data", "processed")
    os.makedirs(outdir, exist_ok=True)
    df.to_csv(os.path.join(outdir, "snl_cycles.csv"), index=False)
    cells = pd.DataFrame(cell_rows)
    cells.to_csv(os.path.join(outdir, "snl_cells.csv"), index=False)

    # ---- duplicate test --------------------------------------------------
    # (1) identical raw-record fingerprints at 5 cycle positions; (2) identical per-cycle capacity vectors
    # (common prefix, rounded to 1e-4 Ah); (3) near duplicates: max |dq| over common cycles tiny.
    qv = {k: g.sort_values("cycle")["q_dis_ah"].to_numpy() for k, g in df.groupby("cell")}
    keys = sorted(qv)
    rep = {"n_cells": len(keys), "pairs_checked": 0, "raw_fingerprint_matches": [], "capacity_vector_identical": [],
           "capacity_near_identical": [], "same_cycle_count_groups": []}
    for a in range(len(keys)):
        for b in range(a + 1, len(keys)):
            ka, kb = keys[a], keys[b]
            rep["pairs_checked"] += 1
            fa, fb = fps[ka], fps[kb]
            same_fp = [p for p in fa if fa[p] is not None and fa[p] == fb[p]]
            # a fingerprint match counts only if the cycle at that position has the same length/content
            if same_fp:
                rep["raw_fingerprint_matches"].append({"a": ka, "b": kb, "positions": same_fp})
            n = min(len(qv[ka]), len(qv[kb]))
            da = np.abs(qv[ka][:n] - qv[kb][:n])
            if n > 10 and np.nanmax(da) == 0.0:
                rep["capacity_vector_identical"].append({"a": ka, "b": kb, "common_cycles": n})
            elif n > 10 and np.nanmedian(da) < 1e-4:
                rep["capacity_near_identical"].append({"a": ka, "b": kb, "common_cycles": n, "median_abs_diff": float(np.nanmedian(da))})
    # cells sharing the same number of recorded cycles
    byn = {}
    for c in cell_rows:
        byn.setdefault(c["n_cycles_record"], []).append(c["cell"])
    rep["same_cycle_count_groups"] = [{"n_cycles": n, "cells": v} for n, v in sorted(byn.items()) if len(v) > 1]
    # within-condition replicate spread check: do "same-count" cells differ in capacity trajectories?
    spread = []
    for g in rep["same_cycle_count_groups"]:
        vs = [qv[c] for c in g["cells"]]
        n = min(len(v) for v in vs)
        mat = np.vstack([v[:n] for v in vs])
        spread.append({"cells": g["cells"], "n_cycles": g["n_cycles"],
                       "median_abs_pairwise_diff_ah": float(np.median(np.abs(mat[:, None, :] - mat[None, :, :])[np.triu_indices(len(vs), 1)]))})
    rep["same_count_pairwise_capacity_diff"] = spread
    # simple data-quality flags per cell
    q = {}
    for k, g in df.groupby("cell"):
        g = g.sort_values("cycle")
        qq = g["q_dis_ah"].to_numpy()
        q[k] = {"n_cycles": int(len(g)), "first_cycle": int(g["cycle"].iloc[0]), "last_cycle": int(g["cycle"].iloc[-1]),
                "n_missing_cycle_numbers": int(g["cycle"].iloc[-1] - g["cycle"].iloc[0] + 1 - len(g)),
                "n_zero_or_nan_capacity": int(((qq <= 0) | ~np.isfinite(qq)).sum()),
                "q_first_ah": float(qq[0]), "q_last_ah": float(qq[-1]),
                "retention_last_vs_first": float(qq[-1] / qq[0]) if qq[0] > 0 else None,
                "total_throughput_ah": float(g["throughput_ah"].sum()), "span_days": float(g["t_end_s"].max() / 86400)}
    rep["cell_quality"] = q
    rep["peak_rss_mb"] = peak / 1e6
    rep["verdict_duplicates"] = (
        "NO whole-trajectory duplicates" if not rep["capacity_vector_identical"] and not rep["raw_fingerprint_matches"]
        else "DUPLICATES FOUND: see lists")
    with open(os.path.join(ROOT, "runs", "pilot_P1", "snl_duplicates.json"), "w", encoding="utf8") as fh:
        json.dump(rep, fh, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != "cell_quality"}, indent=1)[:6000])
    print("rows", len(df), "cells", len(cells), "peak RSS MB", round(peak / 1e6))


if __name__ == "__main__":
    main()
