"""Freeze-blocker audit of the full Samsung 50E release (FB-3/4 stage assignment, FB-5 ZYK files, FB-6 window counts, Test B completeness).

Run (from ROOT, after samsung_extract.py and samsung_checkups.py):
    .venv/Scripts/python.exe -P code/data/samsung_full_audit.py [--jobs N] [--skip-zyk]

BLINDING: this script prints and writes identifiers, counts, schedules, file checks and pass/fail flags only. The check-up table is
read with usecols (cell_id, kind, qc_pass, flags): no capacity or retention column is ever loaded. ZYK files carry current and time;
their parse yields throughput (equivalent full cycles), which is not an outcome, and only counts of parse results are reported.

Outputs (runs/samsung_pipeline_full/):
    stage_assignment.csv     one row per zip folder: stage by each independent rule, agreement status
    window_counts.csv        one row per cell: CU / exCU / ET / AT / ZYK file counts from the zip member listing
    zyk_files.csv            one row per ZYK member (presence and parse flags only), data/processed/samsung_zyk_efc.csv the EFC table (git-ignored)
    test_b_conditions.csv    one row per cycling condition: cells in design / in the cell table / laboratory
    fb_status.json           the numbers quoted in RESULT.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from data import samsung_checkups as S  # noqa: E402

ZIPS = ROOT / "data" / "raw" / "samsung50e_full"
RAWX = ROOT / "data" / "raw" / "samsung50e_full_x"
LISTS = ROOT / "runs" / "samsung_pipeline_full" / "member_lists"
OUT = ROOT / "runs" / "samsung_pipeline_full"
PROC = ROOT / "data" / "processed"
ZIP_RE = re.compile(r"^(?P<serial>TP_[kz]\d{2}_\d{2})__f(?P<fid>\d+)\.zip$")
TP_RE = re.compile(r"Testpoint:\s*(\w+)")
CORE = ("run_time", "c_vol", "c_cur", "step_type")


# ------------------------------------------------------------------------------------------------ listings
def read_listing(folder: str, lists: Path = LISTS) -> list[str]:
    names = []
    for line in (lists / f"{folder}.txt").read_text(encoding="utf-8").splitlines()[1:]:
        if line.strip():
            names.append(line.split("\t", 1)[0].rsplit("/", 1)[-1])
    return names


def count_listing(names: list[str]) -> dict:
    c = dict(n_cu=0, n_excu=0, n_et_csv=0, n_et23_csv=0, n_at_csv=0, n_at23_csv=0, n_zyk_csv=0, n_zyk_meta=0, n_cu_meta=0, n_excu_meta=0,
             n_cu_meta_only=0, n_excu_meta_only=0)
    csv_idx, meta_idx = {"CU": set(), "exCU": set()}, {"CU": set(), "exCU": set()}
    for n in names:
        m = S.FILE_RE.match(n)
        if not m:
            continue
        k, t, meta, csv = m.group("kind"), m.group("temp"), bool(m.group("meta")), bool(m.group("csv"))
        i = int(m.group("idx"))
        if k in ("CU", "exCU"):
            (meta_idx if meta else csv_idx)[k].add(i)
        elif k == "ET" and csv:
            c["n_et_csv"] += 1
            c["n_et23_csv"] += (t == "23")
        elif k == "AT" and csv:
            c["n_at_csv"] += 1
            c["n_at23_csv"] += (t == "23")
        elif k == "ZYK":
            c["n_zyk_csv"] += csv
            c["n_zyk_meta"] += meta
    c["n_cu"], c["n_excu"] = len(csv_idx["CU"]), len(csv_idx["exCU"])
    c["n_cu_meta"], c["n_excu_meta"] = len(meta_idx["CU"]), len(meta_idx["exCU"])
    c["n_cu_meta_only"], c["n_excu_meta_only"] = len(meta_idx["CU"] - csv_idx["CU"]), len(meta_idx["exCU"] - csv_idx["exCU"])
    c["cu_csv_idx"] = sorted(csv_idx["CU"])
    c["excu_csv_idx"] = sorted(csv_idx["exCU"])
    return c


# ------------------------------------------------------------------------------------------------ FB-3 / FB-4: stage
def meta_facts(folder: Path) -> dict:
    labs, ints, dates, tps = set(), set(), [], set()
    for p in sorted(folder.glob("*_meta.txt")):
        txt = p.read_text(encoding="utf-8", errors="replace")
        md = S.parse_meta_text(txt)
        if md["lab"]:
            labs.add(md["lab"])
        if md["internal_serial"]:
            ints.add(md["internal_serial"].strip().upper())
        if md["date"]:
            dates.append(md["date"])
        m = TP_RE.search(txt)
        if m:
            tps.add(m.group(1))
    return dict(labs=labs, ints=ints, dates=dates, tps=tps, mkii=any("MKII" in t for t in tps))


def stage_audit(mapping: pd.DataFrame, design: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ids = {}
    for f in sorted(p.name for p in RAWX.iterdir() if p.is_dir()):
        m = ZIP_RE.match(f + ".zip")
        ids.setdefault(m.group("serial"), []).append(int(m.group("fid")))
    mp = mapping.set_index("folder")
    facts = {f: meta_facts(RAWX / f) for f in sorted(mp.index)}
    n_mkii = {}
    for f, mf in facts.items():
        sr = ZIP_RE.match(f + ".zip").group("serial")
        n_mkii[sr] = n_mkii.get(sr, 0) + int(mf["mkii"])
    int_users: dict = {}
    for f, mf in facts.items():
        for i in mf["ints"]:
            int_users.setdefault(i, set()).add(f)
    for folder in sorted(mp.index):
        serial, fid = ZIP_RE.match(folder + ".zip").group("serial"), int(ZIP_RE.match(folder + ".zip").group("fid"))
        mf = facts[folder]
        cands = design[design["serial"] == serial]
        pipe_stage = mp.loc[folder, "stage"]
        pipe_stage = int(pipe_stage) if str(pipe_stage) not in ("", "nan") else None
        r1 = r2 = r3 = r5 = r6 = None
        if len(cands) == 1:
            r1 = r2 = int(cands.iloc[0]["stage"])
        else:
            h = cands[cands["serial_internal"].str.upper().isin(mf["ints"])]
            r1 = int(h.iloc[0]["stage"]) if len(h) == 1 else None
            h = cands[cands["lab"].isin(mf["labs"])]
            r2 = int(h.iloc[0]["stage"]) if len(h) == 1 else None
        if mf["dates"]:
            r3 = 1 if min(mf["dates"]) < S.STAGE_SPLIT else 2
        if len(ids[serial]) == 2:
            r5 = 1 if fid == min(ids[serial]) else 2    # informational: the lower figshare id is stage 1?
            if n_mkii[serial] == 1:
                r6 = 2 if mf["mkii"] else 1             # the testpoint tag "<serial>_MKII" marks the second-stage zip of 48 serials
        tp_head = f"{cands.iloc[0]['type']}{int(cands.iloc[0]['tp']):02d}" if len(cands) else ""
        tp_ok = all(t == tp_head or t == tp_head + "noCU" or t == serial + "_MKII" for t in mf["tps"]) if mf["tps"] else None
        votes = {k: v for k, v in (("internal_serial", r1), ("lab", r2), ("date", r3), ("testpoint_tag", r6)) if v is not None}
        if pipe_stage is None:
            status = "unassigned"
        elif not votes:
            status = "no_independent_rule"
        elif all(v == pipe_stage for v in votes.values()):
            status = "consistent"
        else:
            status = "conflict"
        design_int = ""
        if pipe_stage is not None:
            d = cands[cands["stage"] == pipe_stage]
            design_int = d.iloc[0]["serial_internal"] if len(d) else ""
        rows.append(dict(folder=folder, serial=serial, cell_id=mp.loc[folder, "cell_id"], stage=pipe_stage, assigned_by=mp.loc[folder, "assigned_by"],
                         n_design_candidates=len(cands), r_internal_serial=r1, r_lab=r2, r_date=r3, r_testpoint_tag=r6, first_date=min(mf["dates"]).isoformat() if mf["dates"] else "",
                         last_date=max(mf["dates"]).isoformat() if mf["dates"] else "", r_figshare_id_order=r5, internal_serial_meta=",".join(sorted(mf["ints"])), internal_serial_design=design_int,
                         internal_serial_matches_design=(design_int.upper() in mf["ints"]) if (design_int and mf["ints"]) else None,
                         internal_serial_shared_with=",".join(sorted({x for i in mf["ints"] for x in int_users[i]} - {folder})),
                         testpoint_ok=tp_ok, n_votes=len(votes), status=status))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------ FB-5: ZYK
def _zyk_zip(args) -> list[dict]:
    """Stream every ZYK csv of one zip (nothing is extracted). Never raises: a problem becomes a flag."""
    from pinnkan import zyk as Z
    zpath, folder, cell_id = args
    out = []
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            base = info.filename.rsplit("/", 1)[-1]
            m = S.FILE_RE.match(base)
            if not m or m.group("kind") != "ZYK" or not m.group("csv") or m.group("meta"):
                continue
            row = dict(folder=folder, cell_id=cell_id, serial=m.group("serial"), file_idx=int(m.group("idx")), member=base, size_bytes=info.file_size,
                       schema_ok=False, dt_max_active_s=np.nan, n_rows=0, discharge_ah=np.nan, charge_ah=np.nan, efc=np.nan, hours=np.nan, dt_max_s=np.nan, complete=False, flags="")
            try:
                with z.open(info) as f:
                    d = pd.read_csv(f, usecols=lambda c: c.strip() in CORE, low_memory=False)
                d.columns = [c.strip() for c in d.columns]
                row["schema_ok"] = all(c in d.columns for c in CORE)
                if not row["schema_ok"]:
                    row["flags"] = "bad_schema"
                else:
                    t = Z._parse_time(d["run_time"])
                    cur = pd.to_numeric(d["c_cur"], errors="coerce").to_numpy(float)
                    seg = Z.segment_from_arrays(t, cur)
                    fl = [x for x in seg.pop("flags").split(";") if x]
                    if len(d) < 10:
                        fl.append("fewer_than_10_rows")
                    if pd.to_numeric(d["c_vol"], errors="coerce").isna().any():
                        fl.append("nan_voltage")
                    row.update(seg)
                    row["flags"] = ";".join(fl)
                    if not np.isnan(t).any() and len(t) > 1:
                        dt = np.diff(t)
                        act = (np.abs(np.nan_to_num(cur[1:])) > 0.05) | (np.abs(np.nan_to_num(cur[:-1])) > 0.05)
                        row["dt_max_active_s"] = float(dt[act].max()) if act.any() else 0.0
            except Exception as e:  # noqa: BLE001 - third-party file: report, never crash
                row["flags"] = f"read_error:{type(e).__name__}"
            out.append(row)
    return out


def zyk_scan(mapping: pd.DataFrame, jobs: int) -> pd.DataFrame:
    tasks = [(str(ZIPS / f"{r.folder}.zip"), r.folder, r.cell_id) for r in mapping.itertuples() if str(r.serial)[3] == "z"]
    rows = []
    with ProcessPoolExecutor(max_workers=jobs) as ex:
        for k, res in enumerate(ex.map(_zyk_zip, tasks, chunksize=1), 1):
            rows += res
            if k % 20 == 0:
                print(f"  zyk: {k}/{len(tasks)} zips", flush=True)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------ main
def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--skip-zyk", action="store_true")
    a = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    design = S.load_design()
    mapping = pd.read_csv(ROOT / "runs" / "samsung_pipeline" / "folder_mapping.csv")
    st: dict = {}

    # ---- FB-3 / FB-4 stage assignment
    sa = stage_audit(mapping, design)
    sa.to_csv(OUT / "stage_assignment.csv", index=False)
    cell_ids = sa["cell_id"].tolist()
    d_ids = {f"{r.serial}_s{int(r.stage)}" for r in design.itertuples()}
    st["stage"] = dict(
        folders=int(len(sa)), design_cells=int(len(design)), distinct_cell_ids=int(len(set(cell_ids))), duplicate_cell_ids=sorted({c for c in cell_ids if cell_ids.count(c) > 1}),
        unassigned=sa[sa.status == "unassigned"]["folder"].tolist(), conflict=sa[sa.status == "conflict"]["folder"].tolist(),
        no_independent_rule=sa[sa.status == "no_independent_rule"]["folder"].tolist(), consistent=int((sa.status == "consistent").sum()),
        design_ids_without_folder=sorted(d_ids - set(cell_ids)), folder_ids_not_in_design=sorted(set(cell_ids) - d_ids),
        by_stage=sa.groupby("stage").size().astype(int).to_dict(), by_assigned_by=sa.groupby("assigned_by").size().astype(int).to_dict(),
        internal_serial_differs_from_design=sa[sa.internal_serial_matches_design == False]["cell_id"].tolist(),  # noqa: E712
        testpoint_unrecognised=sa[sa.testpoint_ok == False]["folder"].tolist(),  # noqa: E712
        internal_serial_meta_differs_by_stage={int(k): int(v) for k, v in sa[sa.internal_serial_matches_design == False].groupby("stage").size().items()},  # noqa: E712
        internal_serial_shared_by_two_folders=sa[sa.internal_serial_shared_with.fillna("") != ""]["folder"].tolist(),
        first_meta_date_by_stage={int(k): v for k, v in sa.groupby("stage")["first_date"].min().items()},
        last_meta_date_by_stage={int(k): v for k, v in sa.groupby("stage")["last_date"].max().items()},
        stage1_dates_overlap_stage2_range=int((sa[sa.stage == 1]["last_date"] >= sa[sa.stage == 2]["first_date"].min()).sum()),
        stage2_dates_overlap_stage1_range=int((sa[sa.stage == 2]["first_date"] <= sa[sa.stage == 1]["last_date"].max()).sum()),
        rule_availability={k: int(sa[k].notna().sum()) for k in ("r_internal_serial", "r_lab", "r_date", "r_testpoint_tag", "r_figshare_id_order")},
        testpoint_tag_rule_agrees=int((sa.r_testpoint_tag.dropna() == sa.loc[sa.r_testpoint_tag.notna(), "stage"]).sum()),
        figshare_id_order_agrees=int((sa.r_figshare_id_order.dropna() == sa.loc[sa.r_figshare_id_order.notna(), "stage"]).sum()),
        figshare_id_order_n=int(sa.r_figshare_id_order.notna().sum()),
    )

    # ---- listings: FB-6 counts, FB-3 ET presence
    rows = []
    for r in mapping.itertuples():
        c = count_listing(read_listing(r.folder))
        c.update(folder=r.folder, cell_id=r.cell_id, serial=r.serial, type=str(r.serial)[3], stage=r.stage)
        rows.append(c)
    wc = pd.DataFrame(rows)
    cells_d = design.assign(cell_id=[f"{s}_s{int(g)}" for s, g in zip(design.serial, design.stage)])[["cell_id", "lab", "tp", "cell", "amb_temp_tp", "soc_max_tp", "dod_tp", "c_ch_tp", "c_dch_tp"]]
    wc = wc.merge(cells_d, on="cell_id", how="left")
    wc["n_intermediate"] = wc["n_cu"] + wc["n_excu"]
    wc.drop(columns=["cu_csv_idx", "excu_csv_idx"]).to_csv(OUT / "window_counts.csv", index=False)

    from pinnkan import data as D
    cyc = wc[(wc.type == "z")]
    sto = wc[(wc.type == "k") & (wc["cell"] <= 3)]
    kc, ks = D.window_rule_from_counts(cyc["n_intermediate"].to_numpy(), sto["n_intermediate"].to_numpy())

    def dist(s):
        return {"n": int(len(s)), "min": int(s.min()), "q25": float(s.quantile(.25)), "median": float(s.median()), "q75": float(s.quantile(.75)), "max": int(s.max()),
                "counts": {int(k): int(v) for k, v in s.value_counts().sort_index().items()}}
    # the same after the file-level incident drops (prereg 3.3(4), both stages of a serial), as a sensitivity
    drops = {(s, i, k) for s, i, k in D.INCIDENT_FILE_DROPS if k in ("CU", "exCU")}

    def n_after_drop(r):
        n = r["n_intermediate"]
        for s, i, k in drops:
            if r["serial"] == s and i in (r["cu_csv_idx"] if k == "CU" else r["excu_csv_idx"]):
                n -= 1
        return n
    wc["n_intermediate_after_incident_drops"] = wc.apply(n_after_drop, axis=1)
    kc2, ks2 = D.window_rule_from_counts(wc[wc.type == "z"]["n_intermediate_after_incident_drops"].to_numpy(),
                                         wc[(wc.type == "k") & (wc["cell"] <= 3)]["n_intermediate_after_incident_drops"].to_numpy())
    post = cyc["n_intermediate"] - kc
    qc = pd.read_csv(PROC / "samsung_checkups.csv", usecols=["cell_id", "kind", "qc_pass", "flags"], dtype={"flags": str}, keep_default_na=False)
    qc_cu = qc[qc.kind.isin(["CU", "exCU"])]
    n_qc = qc_cu[qc_cu.qc_pass.astype(str) == "True"].groupby("cell_id").size()
    cyc_post_qc = pd.Series({c: max(int(n_qc.get(c, 0)) - kc, 0) for c in cyc.cell_id})
    st["window"] = dict(
        definition="intermediate check-ups = CU + exCU csv members of the zip listing (ET and AT excluded), prereg section 5",
        cycling_cells=int(len(cyc)), storage_cells_01_03=int(len(sto)), cycling_count_distribution=dist(cyc["n_intermediate"]),
        storage_count_distribution=dist(sto["n_intermediate"]), n_med_cycling=float(cyc["n_intermediate"].median()), n_med_storage=float(sto["n_intermediate"].median()),
        k_cyc=int(kc), k_sto=int(ks), k_cyc_after_incident_drops=int(kc2), k_sto_after_incident_drops=int(ks2),
        k_full_lt_2_reopens_design=bool(kc < 2), cycling_cells_with_post_window_ge3_listing=int((post >= 3).sum()),
        cycling_cells_with_post_window_ge3_qc_pass=int((cyc_post_qc >= 3).sum()), cycling_cells_with_post_window_ge1_qc_pass=int((cyc_post_qc >= 1).sum()),
        by_stage_median_cycling={int(k): float(v) for k, v in cyc.groupby("stage")["n_intermediate"].median().items()},
        by_temp_median_cycling={float(k): float(v) for k, v in cyc.groupby("amb_temp_tp")["n_intermediate"].median().items()},
        cells_with_cu_meta_without_csv=wc[wc.n_cu_meta_only > 0]["cell_id"].tolist(), cells_with_excu_meta_without_csv=wc[wc.n_excu_meta_only > 0]["cell_id"].tolist(),
        cu_csv_total=int(wc.n_cu.sum()), excu_csv_total=int(wc.n_excu.sum()),
        cycling_cells_with_fewer_than_3_post_window_listing=cyc[post < 3]["cell_id"].tolist(), cycling_cells_post_window_listing_counts={int(k): int(v) for k, v in post.value_counts().sort_index().items()},
        csv_without_meta=[f"{i['serial']}:{i['file']}" for i in pd.read_csv(ROOT / "runs" / "samsung_pipeline" / "issues.csv").query("issue == 'meta_missing'").to_dict("records")])
    # ET_T23 for the Q0 rule
    analysed = wc[(wc.type == "z") | ((wc.type == "k") & (wc["cell"] <= 3))]
    et_ok = qc[(qc.kind == "ET")]
    et_pass = set(et_ok[et_ok.qc_pass.astype(str) == "True"]["cell_id"])
    st["q0_rule"] = dict(
        analysed_cells=int(len(analysed)), analysed_with_et23_csv=int((analysed.n_et23_csv > 0).sum()), analysed_without_et23_csv=analysed[analysed.n_et23_csv == 0]["cell_id"].tolist(),
        analysed_with_et23_qc_pass=int(analysed.cell_id.isin(et_pass).sum()), analysed_without_et23_qc_pass=analysed[~analysed.cell_id.isin(et_pass)]["cell_id"].tolist(),
        all_cells_with_et23_csv=int((wc.n_et23_csv > 0).sum()), all_cells_with_at23_csv=int((wc.n_at23_csv > 0).sum()))
    # incident files: which stage's zip contains them
    inc = {}
    for s, i, k in D.INCIDENT_FILE_DROPS:
        hits = []
        for r in wc.itertuples():
            if r.serial != s:
                continue
            idx = r.cu_csv_idx if k == "CU" else r.excu_csv_idx if k == "exCU" else None
            if (idx is not None and i in idx) or (k == "ET" and r.n_et_csv > 0):
                hits.append(r.cell_id)
        inc[f"{s}_{i:02d}_{k}"] = hits
    st["incident_files_present_in"] = inc

    # ---- FB-5 ZYK
    if not a.skip_zyk:
        zt = zyk_scan(mapping, a.jobs)
        # throughput values (Ah, EFC) stay in data/processed/samsung_zyk_efc.csv (git-ignored); the committed per-file table keeps presence and parse flags only
        zt.drop(columns=["discharge_ah", "charge_ah", "efc", "hours"]).to_csv(OUT / "zyk_files.csv", index=False)
        from pinnkan import zyk as Z
        # members named by the listing as ZYK csv but not read (cannot happen: the scan reads every ZYK csv); meta-only ZYK files are absent segments
        miss = []
        for r in wc[wc.type == "z"].itertuples():
            names = read_listing(r.folder)
            meta_idx = {int(S.FILE_RE.match(n).group("idx")) for n in names if S.FILE_RE.match(n) and S.FILE_RE.match(n).group("kind") == "ZYK" and S.FILE_RE.match(n).group("meta")}
            csv_idx = {int(S.FILE_RE.match(n).group("idx")) for n in names if S.FILE_RE.match(n) and S.FILE_RE.match(n).group("kind") == "ZYK" and S.FILE_RE.match(n).group("csv")}
            for i in sorted(meta_idx - csv_idx):
                miss.append(dict(cell_id=r.cell_id, serial=r.serial, file_idx=i, discharge_ah=np.nan, charge_ah=np.nan, efc=np.nan, hours=np.nan, dt_max_s=np.nan, n_rows=0,
                                 complete=False, flags="missing_file"))
        tab = pd.concat([zt[Z.TABLE_COLS], pd.DataFrame(miss, columns=Z.TABLE_COLS)], ignore_index=True).sort_values(["cell_id", "file_idx"])
        tab.to_csv(PROC / "samsung_zyk_efc.csv", index=False)
        per = zt.groupby("cell_id").agg(n_csv=("member", "size"), n_schema_ok=("schema_ok", "sum"), n_complete=("complete", "sum")).reset_index()
        per = cyc[["cell_id"]].merge(per, on="cell_id", how="left").fillna(0)
        per["n_meta_only"] = per.cell_id.map(pd.DataFrame(miss).groupby("cell_id").size() if miss else pd.Series(dtype=int)).fillna(0).astype(int)
        flag_counts: dict = {}
        for f in zt["flags"]:
            for x in filter(None, f.split(";")):
                flag_counts[x] = flag_counts.get(x, 0) + 1
        per.to_csv(OUT / "zyk_per_cell.csv", index=False)
        wk = zt[zt.cell_id.isin(wc[wc.type == "z"].cell_id)]
        st["zyk"] = dict(
            cycling_cells=int(len(cyc)), cycling_cells_with_any_zyk_csv=int((per.n_csv > 0).sum()), cycling_cells_without_zyk_csv=per[per.n_csv == 0]["cell_id"].tolist(),
            zyk_csv_members_in_listing=int(wc[wc.type == "z"].n_zyk_csv.sum()), zyk_csv_read=int(len(wk)), schema_ok=int(wk.schema_ok.sum()), parse_failed=int((~wk.schema_ok).sum()),
            complete=int(wk.complete.sum()), incomplete=int((~wk.complete).sum()), flag_counts=flag_counts, meta_without_csv=int(len(miss)),
            cells_with_meta_without_csv=sorted({m["cell_id"] for m in miss}), cells_all_zyk_complete=int(((per.n_csv > 0) & (per.n_complete == per.n_csv) & (per.n_meta_only == 0)).sum()),
            cells_with_incomplete_zyk=per[(per.n_complete < per.n_csv) | (per.n_meta_only > 0)]["cell_id"].tolist(),
            storage_cells_with_zyk_csv=int(wc[wc.type == "k"].n_zyk_csv.sum()), gap_flag_s=Z.GAP_FLAG_S, files_with_dt_max_gt_gap=int((wk.dt_max_s > Z.GAP_FLAG_S).sum()),
            files_with_dt_max_gt_60s=int((wk.dt_max_s > 60).sum()), files_with_gap_gt_gapflag_while_current_flows=int((wk.dt_max_active_s > Z.GAP_FLAG_S).sum()),
            files_with_gap_gt_60s_while_current_flows=int((wk.dt_max_active_s > 60).sum()),
            dt_max_s_bins={lab: int(((wk.dt_max_s > lo) & (wk.dt_max_s <= hi)).sum()) for lab, lo, hi in (("<=10", -1, 10), ("10-60", 10, 60), ("60-600", 60, 600), ("600-3600", 600, 3600), (">3600", 3600, 1e12))},
            dt_max_active_s_bins={lab: int(((wk.dt_max_active_s > lo) & (wk.dt_max_active_s <= hi)).sum()) for lab, lo, hi in (("<=10", -1, 10), ("10-60", 10, 60), ("60-600", 60, 600), ("600-3600", 600, 3600), (">3600", 3600, 1e12))},
            zyk_table=str(PROC / "samsung_zyk_efc.csv"), zyk_table_sha256=sha(PROC / "samsung_zyk_efc.csv"))
        try:
            st["zyk"]["validation_informational"] = D.zyk.validate_from_root(str(ROOT))
        except Exception as e:  # noqa: BLE001
            st["zyk"]["validation_informational"] = f"not run: {type(e).__name__}: {str(e)[:200]}"

    if a.skip_zyk and (OUT / "fb_status.json").exists():
        prev = json.loads((OUT / "fb_status.json").read_text(encoding="utf-8"))
        if "zyk" in prev:
            st["zyk"] = prev["zyk"]

    # ---- FB-5 informational: how many ZYK files stay complete if a gap only counts while current flows. The constant GAP_FLAG_S and the gap definition
    # are the lead's to fix (zyk.py marks them as assumptions); nothing here changes the ZYK table on disk and no validation verdict is drawn from it.
    if (OUT / "zyk_files.csv").exists() and isinstance(st.get("zyk"), dict):
        from pinnkan import zyk as Z
        zt = pd.read_csv(OUT / "zyk_files.csv", keep_default_na=False, dtype={"flags": str})
        zt["dt_max_active_s"] = pd.to_numeric(zt["dt_max_active_s"], errors="coerce")
        bad = zt["flags"].str.contains("time_not_monotonic|nan_current|unparsable|bad_schema|read_error|fewer_than_10_rows")
        alt = zt["schema_ok"].astype(str).eq("True") & ~bad & ~(zt["dt_max_active_s"] > Z.GAP_FLAG_S)
        st["zyk"].pop("validation_alt_gap_rule_informational", None)
        st["zyk"].pop("incomplete_only_by_sampling_gap_and_no_gap_while_current_flows", None)
        sg = zt["flags"].str.contains("sampling_gap")
        st["zyk"]["sampling_gap_flagged_files"] = int(sg.sum())
        st["zyk"]["sampling_gap_flagged_files_with_gap_while_current_flows"] = int((sg & (zt["dt_max_active_s"] > Z.GAP_FLAG_S)).sum())
        st["zyk"]["sampling_gap_flagged_files_gap_in_rest_only"] = int((sg & ~(zt["dt_max_active_s"] > Z.GAP_FLAG_S)).sum())
        st["zyk"]["files_complete_under_alt_rule"] = int(alt.sum())
        st["zyk"]["files_incomplete_under_alt_rule"] = int((~alt).sum())
        st["zyk"]["cells_all_complete_under_alt_rule"] = int(zt.assign(alt=alt).groupby("cell_id")["alt"].all().sum())

    # ---- QC flag counts and the rows with STRUCTURAL problems (identifiers and flag names; capacity-derived flags are counted only)
    CAP_DERIVED = {"capacity_outlier_vs_neighbours", "implausible_capacity", "charge_discharge_mismatch"}
    fl_rows = qc[qc["flags"] != ""].copy()
    fl_rows["structural_flags"] = fl_rows["flags"].map(lambda f: ";".join(x for x in f.split(";") if x not in CAP_DERIVED))
    fl_rows["n_capacity_derived_flags"] = fl_rows["flags"].map(lambda f: sum(x in CAP_DERIVED for x in f.split(";")))
    fl_rows[fl_rows["structural_flags"] != ""][["cell_id", "kind", "structural_flags"]].to_csv(OUT / "structural_problem_rows.csv", index=False)
    cnt: dict = {}
    for f in qc["flags"]:
        for x in filter(None, f.split(";")):
            cnt[x] = cnt.get(x, 0) + 1
    qc_pass = qc["qc_pass"].astype(str) == "True"
    st["qc"] = dict(rows=int(len(qc)), rows_by_kind=qc.groupby("kind").size().astype(int).to_dict(), qc_pass_rows=int(qc_pass.sum()), qc_fail_rows=int((~qc_pass).sum()),
                    qc_pass_by_kind={k: int(v) for k, v in qc[qc_pass].groupby("kind").size().items()}, flag_counts=cnt,
                    cells_with_a_failed_row=int(qc[~qc_pass]["cell_id"].nunique()), rows_with_structural_flag=int((fl_rows["structural_flags"] != "").sum()),
                    outlier_rule={"OUTLIER_REL": S.OUTLIER_REL, "OUTLIER_DROP_MULT": S.OUTLIER_DROP_MULT, "causal": True})

    # ---- Test B completeness of the cell table (lab map)
    cells = pd.read_csv(PROC / "samsung_cells.csv")
    cz = cells[cells["type"] == "z"].copy()
    cz["key"] = [D.samsung_cond_key("cycling", float(r.T_C), float(r.SOC_max), float(r.DoD), float(r.C_ch), float(r.C_dch)) for r in cz.itertuples()]
    dz = design[design["type"] == "z"].copy()
    dz["key"] = [D.samsung_cond_key("cycling", float(r.amb_temp_tp), float(r.soc_max_tp), float(r.dod_tp), float(r.c_ch_tp), float(r.c_dch_tp)) for r in dz.itertuples()]
    spl = json.loads((ROOT / "runs" / "prereg" / "samsung_splits_v2.json").read_text(encoding="utf-8"))["B"]["folds"]
    split_conds = sorted({c for f in spl.values() for c in f["test_conditions"]})
    split_cells = sorted({c for f in spl.values() for c in f["test_cells"]})
    cond = dz.groupby("key").size().rename("cells_in_design").to_frame().join(cz.groupby("key").agg(cells_in_table=("cell_id", "size"), labs=("lab", lambda x: ",".join(sorted(set(map(str, x))))),
                                                                                                   stages=("stage", lambda x: ",".join(map(str, sorted(set(x)))))))
    cond = cond.reset_index()
    cond["in_splits_v2"] = cond["key"].isin(split_conds)
    cond.to_csv(OUT / "test_b_conditions.csv", index=False)
    from prereg import extraction_calibration as EC
    labs, labs_hash = EC.majority_labs(str(ROOT))
    need = ["cell_id", "lab", "stage", "tp", "cell", "T_C", "SOC_max", "DoD", "C_ch", "C_dch", "type"]
    st["test_b"] = dict(
        conditions_in_design=int(dz["key"].nunique()), conditions_in_cell_table=int(cz["key"].nunique()), conditions_in_splits_v2=len(split_conds),
        design_conditions_missing_in_table=sorted(set(dz["key"]) - set(cz["key"])), split_conditions_missing_in_table=sorted(set(split_conds) - set(cz["key"])),
        split_conditions_not_in_design=sorted(set(split_conds) - set(dz["key"])), cycling_cells_in_design=int(len(dz)), cycling_cells_in_table=int(len(cz)),
        conditions_with_fewer_cells_than_design=cond[cond.cells_in_table.fillna(0) < cond.cells_in_design]["key"].tolist(),
        cell_table_null_cells={c: int(cz[c].isna().sum()) for c in need if int(cz[c].isna().sum())}, split_test_cells=len(split_cells),
        split_test_cells_missing_in_table=sorted(set(split_cells) - set(cz.cell_id)), table_cells_not_in_splits=int(len(set(cz.cell_id) - set(split_cells))),
        mixed_lab_condition_cell_counts={k: cz[cz.key == k].groupby("lab").size().astype(int).to_dict() for k in cond[cond.labs.fillna("").str.contains(",")]["key"]},
        majority_lab_map_conditions=len(labs), majority_lab_map_sha256=labs_hash, labs_per_condition_mixed=cond[cond.labs.fillna("").str.contains(",")]["key"].tolist(),
        cells_csv_sha256=sha(PROC / "samsung_cells.csv"), checkups_csv_sha256=sha(PROC / "samsung_checkups.csv"))
    st["storage_conditions"] = dict(design=int(design[design["type"] == "k"][["amb_temp_tp", "soc_max_tp"]].drop_duplicates().shape[0]),
                                    table=int(cells[cells["type"] == "k"][["T_C", "SOC_max"]].drop_duplicates().shape[0]), storage_cells_in_table=int((cells["type"] == "k").sum()))
    (OUT / "fb_status.json").write_text(json.dumps(st, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: (v if k in ("stage",) else "written") for k, v in st.items()}, indent=1, default=str)[:3000])
    return st


if __name__ == "__main__":
    main()
