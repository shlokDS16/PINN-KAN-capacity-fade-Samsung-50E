"""Common data interface (PREREG_v2 sections 3, 4, 5).

Public entry points
    load_split(dataset, test, fold, role, ...)  -> SplitView  (role 'train' always; role 'test' only if FROZEN exists)
    prepare(cell, rule, ...)                    -> Prepared    (window / forecast split of ONE cell)
    prepare_many(cells, rule, ...)              -> list[Prepared]
The whole-dataset loaders are private (`_load_*`) on purpose: the only way to obtain cells of a real dataset is through
`load_split`, which keeps outer-test cells out of the training view and calls the test-fold guard for any test access.

Conventions
    time t: dataset unit (days / weeks / cycles) since the reference check-up (index 0, t = 0, retention = 1)
    retention: Q / Q0,c (fraction); EFC: cumulative equivalent full cycles since the reference check-up
    window: ('count', k) = reference + first k check-ups after it (Samsung) or ('time', W) = all points with t <= W (ISU, SNL)
    forecast set: later check-ups flagged fc_ok (CU, exCU), ended at the first point below spec.life_level when set (ISU, SNL)
    throughput after the window: the cell's own mean EFC rate over the window (causal); `oracle=True` uses the logged record.
"""
import dataclasses
import hashlib
import json
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import ROOT as _ROOT
from . import blinding, guard, subsets, zyk
from .specs import SPECS, DatasetSpec

# ------------------------------------------------------------------------------------------------ containers


@dataclass
class Cell:
    cell_id: str
    dataset: str
    kind: str                 # 'cycling' | 'storage'
    cond: str                 # condition key (the unit of evaluation)
    raw: np.ndarray           # raw stress vector (spec.stress_names); storage: (T, SOC, 0, 0, 0)
    t: np.ndarray             # time since the reference check-up, dataset unit, t[0] = 0
    ret: np.ndarray           # retention fraction, ret[0] = 1
    efc: np.ndarray           # cumulative EFC since the reference check-up
    fc_ok: np.ndarray         # bool: point may belong to a forecast set
    lab: str = ""
    stage: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def n(self):
        return len(self.t)


class EFCCurve:
    """Piecewise-linear cumulative throughput through the check-ups used; beyond the last used check-up the mean rate over
    the used span continues (causal rule when only the window is used)."""

    def __init__(self, t, efc, upto=None, tail=None):
        w = len(t) - 1 if upto is None else int(upto)
        self.t, self.e = np.asarray(t[: w + 1], float), np.asarray(efc[: w + 1], float)
        span = self.t[-1] - self.t[0]
        self.tail = float((self.e[-1] - self.e[0]) / span) if span > 0 else 0.0
        if tail is not None and span <= 0:       # k = 0: no window rate exists; the caller supplies the DESIGN rate (label-free)
            self.tail = float(tail)

    def value(self, tq):
        tq = np.asarray(tq, float)
        inside = np.interp(tq, self.t, self.e)
        return np.where(tq > self.t[-1], self.e[-1] + self.tail * (tq - self.t[-1]), inside)

    def rate(self, tq):
        tq = np.asarray(tq, float)
        if len(self.t) < 2:
            return np.full(tq.shape, self.tail)
        dt = np.diff(self.t)
        slopes = np.where(dt > 0, np.diff(self.e) / np.where(dt > 0, dt, 1.0), 0.0)       # same-day check-ups: zero-width interval, rate 0
        j = np.clip(np.searchsorted(self.t, tq, side="right") - 1, 0, len(slopes) - 1)
        return np.where(tq >= self.t[-1], self.tail, slopes[j])


@dataclass
class WindowCell:
    """What a model may see of a held-out cell: window data, the forecast times and a causal throughput curve. No forecast label."""
    cell_id: str
    kind: str
    cond: str
    raw: np.ndarray
    t_win: np.ndarray
    y_win: np.ndarray         # retention at the window check-ups
    efc_win: np.ndarray
    t_fc: np.ndarray
    efc_curve: EFCCurve       # causal (window-mean rate after the window) unless oracle=True
    lab: str = ""
    stage: str = ""

    @property
    def t_last(self):
        return float(self.t_win[-1])

    @property
    def y_last(self):
        return float(self.y_win[-1])


@dataclass
class Prepared:
    cell: Cell
    win: WindowCell
    fc_true: np.ndarray       # retention at the forecast times (scorer only)
    w_idx: int                # index of the last window point


@dataclass
class WindowRule:
    k_cycling: object = None
    k_storage: object = None
    W: object = None
    min_window_points: int = 3
    min_fc_points: int = 1
    life_level: object = None
    design_spec: object = None       # k = 0: the dataset spec whose analytic design EFC rate is the throughput of a cell that has no window rate

    @classmethod
    def for_grid(cls, spec: DatasetSpec, k, base, min_fc_points=None):
        """Window rule of one grid cell (PREREG_v4 4.1). k = 0: the reference check-up only (no window check-up, no window rate: the design rate of the stress vector
        is the throughput); k = 2: reference + 2 check-ups (storage cells: min(2, k_sto)); k = 'full': the base rule (k_full = k_cyc, k_sto; or the base window W).
        Time-window datasets (ISU, SNL): k is the window length W in the dataset unit (0 = reference only), 'full' = the base W."""
        full = k in ("full", None)
        mfp = base.min_fc_points if min_fc_points is None else min_fc_points
        if base.W is not None:
            W = base.W if full else float(k)
            return dataclasses.replace(base, W=W, min_window_points=1 if (not full and W == 0) else base.min_window_points, min_fc_points=mfp,
                                       design_spec=spec if (not full and W == 0) else None)
        if full:
            return dataclasses.replace(base, min_fc_points=mfp)
        k = int(k)
        if k > base.k_cycling:
            raise DesignReopenError(f"grid k = {k} exceeds k_full = {base.k_cycling}")
        return dataclasses.replace(base, k_cycling=k, k_storage=min(k, base.k_storage), min_window_points=1 if k == 0 else base.min_window_points, min_fc_points=mfp,
                                   design_spec=spec if k == 0 else None)

    @classmethod
    def for_spec(cls, spec: DatasetSpec, k_cycling=None, k_storage=None, W=None, shift=0, min_fc_points=1):
        kind, val = spec.window
        if kind == "count":
            kc = (val if k_cycling is None else k_cycling) + shift
            ks = (2 if k_storage is None else k_storage) + shift     # k_sto 'near 2' (prereg 5): replaced by the counted value [FB-6]
            return cls(k_cycling=max(kc, 1), k_storage=max(ks, 1), min_window_points=spec.min_window_points, min_fc_points=min_fc_points, life_level=spec.life_level)
        return cls(W=val if W is None else W, min_window_points=spec.min_window_points, min_fc_points=min_fc_points, life_level=spec.life_level)

    def window_end(self, cell: Cell):
        if self.W is not None:
            return int(np.sum(cell.t <= self.W + 1e-9) - 1)
        k = self.k_cycling if cell.kind == "cycling" else self.k_storage
        return int(min(int(k), cell.n - 2))  # reference + k check-ups; D025 cap: a cell with n <= k intermediate check-ups gets the window n - 1 (one check-up left to forecast)

    def capped(self, cell: Cell):
        """True when the D025 cap binds for this cell (count windows only; identifiers and point counts only, no label)"""
        if self.W is not None:
            return False
        k = self.k_cycling if cell.kind == "cycling" else self.k_storage
        return int(k) > cell.n - 2


LABS = ("HM", "INT", "SIE")          # Samsung laboratories (PREREG_v4 3.3(7)); reference level = HM
STAGES = ("1", "2")                  # reference level = stage 1


def indicator_vector(lab, stage):
    """lab-and-stage indicators of PREREG_v4 9.8 rule 2 / 9.9 (f): treatment coding [lab == INT, lab == SIE, stage == 2] with reference HM and stage 1; an unknown or empty
    laboratory or stage is the reference (all zeros). Identifiers only. The coding is this build's choice (the prereg does not fix it; CHOICES.md)."""
    return np.array([float(lab == LABS[1]), float(lab == LABS[2]), float(str(stage) == STAGES[1])], dtype=np.float32)


N_IND = 3


class DesignReopenError(RuntimeError):
    """k_full < 2: the grid k in {0, 2, k_full} is not defined and the design is re-opened (J16 section 8, PREREG_v4 4.1)"""


def grid_ks(k_full):
    """the k axis of the grid: (0, 2, 'full'); if k_full = 2 the cells k = 2 and k = full are one cell, so (0, 'full'); k_full < 2 re-opens the design"""
    if k_full < 2:
        raise DesignReopenError(f"k_full = {k_full} < 2: the grid k in {{0, 2, k_full}} cannot be formed; the design is re-opened (J16 section 8)")
    return (0, "full") if k_full == 2 else (0, 2, "full")


def window_rule_from_counts(counts_cycling, counts_storage=None):
    """Prereg 5: k_cyc = round(n_med / 3) from intermediate check-up counts (CU + exCU; ET, AT excluded) per cell, identifiers only."""
    kc = int(round(float(np.median(counts_cycling)) / 3.0))
    ks = int(round(float(np.median(counts_storage)) / 3.0)) if counts_storage is not None and len(counts_storage) else None
    return kc, ks


def window_capped_cells(cells, rule: WindowRule):
    """D025: the cells whose window is capped at n - 1 under `rule` (listed in every run; PREREG_v4 section 5)"""
    return sorted(c.cell_id for c in cells if rule.capped(c))


def prepare(cell: Cell, rule: WindowRule, oracle=False):
    """Window / forecast split of one cell, or None when the cell cannot be scored (too few window or forecast points)."""
    w = rule.window_end(cell)
    if w < rule.min_window_points - 1 or w >= cell.n - 1:
        return None
    last = cell.n - 1
    if rule.life_level is not None:
        below = np.where(cell.ret < rule.life_level)[0]
        if len(below):
            last = int(below[0])
    idx = np.array([i for i in range(w + 1, last + 1) if cell.fc_ok[i]], int)
    if len(idx) < rule.min_fc_points:
        return None
    design_tail = None
    if w == 0 and rule.design_spec is not None and cell.kind == "cycling":
        design_tail = float(rule.design_spec.efc_rate(cell.raw))      # k = 0: label-free design throughput (the window has no rate)
    curve = EFCCurve(cell.t, cell.efc, upto=None if oracle else w, tail=design_tail)
    win = WindowCell(cell.cell_id, cell.kind, cell.cond, cell.raw.copy(), cell.t[: w + 1].copy(), cell.ret[: w + 1].copy(),
                     cell.efc[: w + 1].copy(), cell.t[idx].copy(), curve, cell.lab, cell.stage)
    return Prepared(cell, win, cell.ret[idx].copy(), w)


def prepare_many(cells, rule, oracle=False):
    out = []
    for c in cells:
        p = prepare(c, rule, oracle)
        if p is not None:
            out.append(p)
    return out


# ------------------------------------------------------------------------------------------------ Samsung

# Incident handling (prereg 3.3(4); D024 section 5, 2026-11-05). The dataset paper's "Known incidents" list is organised under the headings "Stage 1" and
# "Stage 2" (refs/samsung50e_paper/paper.txt lines 94-125); all six check-up files named below stand under "Stage 1". Entries are (serial, stage, file number, kind):
# the file is dropped for that stage only; the same-named stage-2 files are ordinary check-ups.
INCIDENT_FILE_DROPS = [("TP_z01_03", 1, 11, "CU"), ("TP_z17_03", 1, 13, "exCU"), ("TP_z17_03", 1, 17, "CU"), ("TP_z17_02", 1, 19, "exCU"), ("TP_k11_02", 1, 3, "exCU")]
# Documented no-ops: TP_z25_01_01_ET_T45 (undefined load) and TP_z12_*_31_AT_T45 (aborted) are files the pipeline does not read (ET at 23 C only; AT excluded). The
# earlier entry ("TP_z25_01", 1, "ET") removed the ET_T23 row, a different file, and flipped the reference anchor for every cell (defect found by the D024 judge).
INCIDENT_NOOP_FILES = ["TP_z25_01_01_ET_T45", "TP_z12_*_31_AT_T45"]
# Consecutive-file drops (prereg 3.3(4), second sentence): every later check-up of a cell whose cycling segment shows undefined load or a wrong SOC_max.
# Entry = (serial, stage, segment file number): every row of that cell and stage with file number > segment is dropped (the segment itself is a ZYK file and has no
# capacity row). Stage scope from the paper's headings: stage 1 for TP_z24_01 (after 2), TP_z25_01 (after 4), TP_z20_03 (after 16), TP_z17_03 (after 18); stage 2 for
# TP_z07_03 (after 16). "TP_z17 from segment 18" is read as cell 03 (the incident names TP_z17_03; D024 section 5, a reading of PREREG's own definition). A key
# without a cell number would still match every cell of that test point; a stage of None matches both stages. Segments with only missing log data keep their check-ups.
INCIDENT_CONSECUTIVE_DROPS = [("TP_z24_01", 1, 2), ("TP_z25_01", 1, 4), ("TP_z07_03", 2, 16), ("TP_z20_03", 1, 16), ("TP_z17_03", 1, 18)]
INCIDENT_CONSECUTIVE_DROPS_IMPLEMENTED = True


def consecutive_drop_mask(df, rules=None):
    """boolean mask of the rows removed by the consecutive-file incident rule (see INCIDENT_CONSECUTIVE_DROPS); rules: (key, stage, segment) or legacy (key, segment)"""
    m = np.zeros(len(df), bool)
    ser = df["serial"].astype(str)
    for rule in (INCIDENT_CONSECUTIVE_DROPS if rules is None else rules):
        key, stage, seg = rule if len(rule) == 3 else (rule[0], None, rule[1])
        match = (ser == key) | ser.str.startswith(key + "_")
        if stage is not None:
            if "stage" not in df.columns:
                raise ValueError("a stage-scoped incident rule needs a 'stage' column")
            match = match & (pd.to_numeric(df["stage"], errors="coerce") == stage)
        m |= (match & (df["file_idx"] > seg)).to_numpy()
    return m


def file_drop_mask(df, rules=None):
    """boolean mask of the rows removed by the file-level incident rule (INCIDENT_FILE_DROPS, stage-aware)"""
    m = np.zeros(len(df), bool)
    for ser, stage, fidx, knd in (INCIDENT_FILE_DROPS if rules is None else rules):
        m |= ((df["serial"] == ser) & (pd.to_numeric(df["stage"], errors="coerce") == stage) & (df["file_idx"] == fidx) & (df["kind"] == knd)).to_numpy()
    return m


def samsung_cond_key(kind, T, soc_max, dod, c_ch, c_dch):
    if kind == "cycling":
        return "T%g|SOCmax%g|DoD%g|Cch%g|Cdch%g" % (T, soc_max, dod, c_ch, c_dch)
    return "T%g|SOC%g" % (T, soc_max)


def _load_samsung(root, retain_all=False, throughput="analytic", include_at=False, drop_incidents=True, keep=None, throughput_fallback="none", include_storage_0406=False, zyk_table_sha256=None):
    if throughput not in ("analytic", "zyk"):
        raise ValueError(throughput)
    if throughput == "zyk" and zyk_table_sha256 is not None:      # D028 C1: the ZYK table is git-ignored; the config pins its hash and a different file is refused before use
        zp = os.path.join(root, zyk.ZYK_TABLE_REL)
        if not os.path.isfile(zp) or sha256_file(zp) != zyk_table_sha256:
            from .run import ConfigError
            raise ConfigError(f"zyk_table_sha256 does not match {zyk.ZYK_TABLE_REL} in this tree (absent or another table): the primary ZYK throughput table is pinned by hash (D028 C1)")
    df = pd.read_csv(os.path.join(root, "data", "processed", "samsung_checkups.csv"))
    if throughput == "zyk":
        # ZYK-logged throughput (prereg 5, FB-5): cumulative EFC from the ZYK segment table, computed on the UNFILTERED rows so that the segments before dropped or
        # QC-failed check-ups still count; an interval with missing log data takes the designed throughput (3.3(4)); no table / no cell entry -> ZykDataMissing
        if "efc_zyk_cum" not in df.columns:
            df = zyk.attach_zyk_cumulative(df, zyk.load_zyk_table(root), fallback=throughput_fallback)
    # ONE reference rule for all analysed cells (prereg 3.3(2), D024 section 2): ET_T23 capacity iff an ET row exists for every analysed cell. The test is made ONCE, on
    # the rows of the pipeline table before any incident or QC step (row existence only, no capacity value), and is not re-decided from the rows that survive.
    all_ids = set(df["cell_id"])
    et_ids = set(df.loc[df["kind"] == "ET", "cell_id"])
    et_all = bool(all_ids) and all_ids <= et_ids
    reference = "ET" if et_all else "first_CU"
    n_incident = n_consec = 0
    if drop_incidents:
        m = file_drop_mask(df)
        n_incident = int(m.sum())
        mc = consecutive_drop_mask(df) & ~m
        n_consec = int(mc.sum())
        df = df[~(m | mc)]
    if not retain_all:
        df = df[df["qc_pass"].astype(str).str.lower().isin(["true", "1"])]
    else:
        # D044: the retain-every-check-up row keeps every DATED check-up. A row with no start date has no elapsed time and cannot be
        # placed on the time axis (3 rows, flag no_start_date, all qc_pass false, so this is a no-op whenever retain_all is false).
        df = df[df["elapsed_days"].notna()]
    if not include_at:
        df = df[df["kind"] != "AT"]
    if not et_all:
        df = df[df["kind"] != "ET"]            # fallback: the first check-up of every cell is the reference, ET rows are dropped for everybody
    else:
        lost = sorted(all_ids - set(df.loc[df["kind"] == "ET", "cell_id"]))
        if lost:
            raise ValueError(f"reference is ET_T23 for all cells, but the ET row of {lost[:5]} ({len(lost)} cells) was removed by a QC or incident step")
    cells = []
    for cid, g in df.groupby("cell_id", sort=True):
        g = g.sort_values(["elapsed_days", "file_idx"], kind="stable")
        r0 = g.iloc[0]
        kind = "cycling" if r0["type"] == "z" else "storage"
        cond = samsung_cond_key(kind, float(r0["T_C"]), float(r0["SOC_max"]), float(r0["DoD"]), float(r0["C_ch"]), float(r0["C_dch"]))
        if keep is not None and not keep(cid, cond, kind, int(r0["cell"])):
            continue          # a filtered-out (test-side) cell is never turned into arrays
        t = g["elapsed_days"].to_numpy(float)
        t = t - t[0]
        q = g["q_mean_ah"].to_numpy(float)
        ret = q / q[0]                                   # q_mean of the (single-rule) reference row
        if throughput == "zyk":
            e = g["efc_zyk_cum"].to_numpy(float) if kind == "cycling" else np.zeros(len(g))
        else:
            e = g["efc_est_cum"].to_numpy(float) if kind == "cycling" else np.zeros(len(g))
        e = pd.Series(e).ffill().fillna(0.0).to_numpy(float)     # forward-fill gaps (review m4), never zero them mid-record
        e = e - e[0]
        n_fix = int(np.sum(np.diff(e) < 0))
        e = np.maximum.accumulate(e)
        assert np.all(np.diff(e) >= 0) and np.all(np.diff(t) >= 0), f"{cid}: time or cumulative EFC not monotone"
        T, smax, dod, cch, cdch = (float(r0[c]) for c in ("T_C", "SOC_max", "DoD", "C_ch", "C_dch"))
        raw = np.array([T, smax - dod / 2.0, dod, cch, cdch]) if kind == "cycling" else np.array([T, smax, 0.0, 0.0, 0.0])
        fc_ok = g["kind"].isin(["CU", "exCU", "AT"] if include_at else ["CU", "exCU"]).to_numpy()      # AT only in the AT-included sensitivity row (3.3(6), 9.8(i))
        fc_ok[0] = False
        cells.append(Cell(cid, "samsung", kind, cond, raw, t, ret, e, fc_ok,
                          lab=str(r0["lab"]), stage=str(int(r0["stage"])),
                          meta={"cell_no": int(r0["cell"]), "tp": int(r0["tp"]), "n_incident_rows_dropped_dataset": n_incident,
                                "n_consecutive_incident_rows_dropped": n_consec, "reference": reference,
                                "reference_decided_on_n_cells": len(all_ids), "reference_decided_before_incident_and_qc": True, "efc_decreases_fixed": n_fix,
                                "throughput_source": throughput, "zyk_intervals": (dict(g["zyk_interval_source"].value_counts()) if throughput == "zyk" and "zyk_interval_source" in g else {})}))
    return cells


# ------------------------------------------------------------------------------------------------ ISU, SNL


def _load_isu(root, keep=None):
    spec = SPECS["isu"]
    cap = pd.read_csv(os.path.join(root, "data", "processed", "isu_capacity.csv"))
    cond = pd.read_csv(os.path.join(root, "data", "processed", "isu_conditions.csv")).set_index("group")
    cells = []
    for name, g in cap.groupby("cell", sort=True):
        g = g.sort_values("week")
        gr = int(g["group"].iloc[0])
        if keep is not None and not keep(name, str(gr), "cycling", 0):
            continue
        raw = cond.loc[gr, ["charge_c", "discharge_c", "dod_pct"]].to_numpy(float)
        t = g["week"].to_numpy(float) - g["week"].iloc[0]
        ret = g["retention"].to_numpy(float)
        ret = ret / ret[0]
        e = spec.efc_rate(raw) * t
        fc = np.ones(len(t), bool)
        fc[0] = False
        cells.append(Cell(name, "isu", "cycling", str(gr), raw, t, ret, e, fc, meta={"group": gr}))
    return cells


SNL_GRID = 25


def _load_snl(root, keep=None):
    spec = SPECS["snl"]
    cl = pd.read_csv(os.path.join(root, "data", "processed", "snl_cells.csv"))
    cl["cond"] = (cl.chemistry + "|" + cl.temp_c.astype(str) + "C|" + cl.soc_window + "|ch" + cl.charge_c.astype(str) + "|dis" + cl.discharge_c.astype(str))
    cy = pd.read_csv(os.path.join(root, "data", "processed", "snl_cycles.csv"), usecols=["cell", "cycle", "q_dis_ah"])
    cy = cy[cy.q_dis_ah > 0.05]  # invalid records (P1 caveat), as in P3
    first = cy[cy.cycle == 1].set_index("cell").q_dis_ah
    cy = cy[(cy.cycle - 1) % SNL_GRID == 0].copy()
    cy["r"] = cy.q_dis_ah / cy.cell.map(first)
    cells = []
    for _, c in cl.iterrows():
        if keep is not None and not keep(c["cell"], c["cond"], "cycling", 0):
            continue
        g = cy[cy.cell == c["cell"]].sort_values("cycle")
        if len(g) < 2:
            continue
        lo, hi = (int(v) for v in c["soc_window"].split("-"))
        dod = (hi - lo) / 100.0
        raw = np.array([c.chemistry == "LFP", c.chemistry == "NCA", c.chemistry == "NMC", float(c.temp_c), dod, float(c.charge_c), float(c.discharge_c)], float)
        t = g["cycle"].to_numpy(float) - 1.0
        ret = g["r"].to_numpy(float)
        fc = np.ones(len(t), bool)
        fc[0] = False
        cells.append(Cell(c["cell"], "snl", "cycling", c["cond"], raw, t, ret, spec.efc_rate(raw) * t, fc, meta={"chemistry": c.chemistry}))
    return cells


# ------------------------------------------------------------------------------------------------ splits


def _digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def split_path(root, dataset, test):
    if dataset == "samsung":
        for p in (os.path.join(root, "runs", "splits", "samsung_splits_v2.json"), os.path.join(root, "runs", "prereg", "samsung_splits_v2.json")):
            if os.path.isfile(p):
                return p
        raise FileNotFoundError("samsung_splits_v2.json")
    return os.path.join(root, "runs", "splits", f"{dataset}_test{test}.json")


class SplitIntegrityError(RuntimeError):
    """split file hash mismatch (stored vs recomputed, or vs the value pinned at freeze), or a loaded condition outside the split's training set"""


@dataclass
class SplitView:
    dataset: str
    test: str
    fold: int
    spec: DatasetSpec
    train: list
    test_cells: object          # list[Cell] when role == 'test' and frozen, else None
    train_conditions: list
    test_conditions: list
    test_cell_ids: list
    split_file: str
    split_sha256: str
    fold_hash_stored: str
    fold_hash_recomputed: str
    input_files: list
    missing_train_conditions: list = field(default_factory=list)
    pinned: bool = False
    subset_info: object = None   # D016 grid: nested training subset record (None = unthinned)
    blinding_excluded: list = field(default_factory=list)      # PREREG_v4 3.3(11): outer-test cells withheld from scoring (kind (b) pre-freeze exposures); [] = none

    @property
    def hash_ok(self):
        return self.fold_hash_stored == self.fold_hash_recomputed


def _input_manifest(root, dataset):
    names = {"samsung": ["samsung_checkups.csv", "samsung_zyk_efc.csv"], "isu": ["isu_capacity.csv", "isu_conditions.csv"], "snl": ["snl_cells.csv", "snl_cycles.csv"]}[dataset]
    out = []
    for n in names:
        p = os.path.join(root, "data", "processed", n)
        if os.path.isfile(p):
            out.append({"path": os.path.relpath(p, root).replace("\\", "/"), "size": os.path.getsize(p), "sha256": sha256_file(p)})
    return out


def apply_subset(train, dataset, test, fdef, fold, m, subset="maxmin", draw=0, root=None, ids=None):
    """D016 grid (PREREG_v4 4.1): keep the first m conditions of the nested max-min order (or of the seeded random order) of the fold's training cycling
    conditions; storage cells stay. m None or >= the number of training conditions = the unthinned training side (the SAME list, bit for bit).
    -> (train, info). Identifiers only."""
    if m is None:
        return train, None
    if ids is not None:                       # synthetic data: the training cycling conditions present in the training cells
        ids = sorted(str(c) for c in ids)
        cond_table = None
    elif dataset == "samsung" and test in ("B", "C"):
        ids = [str(c) for c in fdef["train_cycling_conditions"]]
        cond_table = None
    elif dataset == "isu" and fdef.get("train_conditions"):
        ids = [str(c) for c in fdef["train_conditions"]]
        cond_table = pd.read_csv(os.path.join(root or _ROOT, "data", "processed", "isu_conditions.csv")).set_index("group")
    else:
        raise ValueError(f"nested training subsets are defined for Samsung Test B/C and ISU Test B, not {dataset} test {test}")
    if subset == "maxmin":
        order = subsets.order_for_ids(ids, dataset, cond_table)
    elif subset == "random":
        order = subsets.random_order(ids, fold, draw)
    else:
        raise ValueError(f"subset must be 'maxmin' or 'random', not {subset!r}")
    keep = subsets.subset_at(order, m)
    info = {"m": int(m), "kind": subset, "draw": int(draw) if subset == "random" else None, "n_train_conditions": len(ids), "kept": keep, "order": order,
            "thinned": len(keep) < len(ids), "sha256": _digest({"kept": keep, "order": order})}
    if len(keep) >= len(ids):
        return train, info
    return subsets.thin_cells(train, keep), info


def load_split(dataset, test, fold, role="train", root=None, retain_all=False, throughput="analytic", include_at=False, throughput_fallback="none", include_storage_0406=False,
               m=None, subset="maxmin", subset_draw=0, runs_dir=None, score_blinded_cells=False, zyk_table_sha256=None):
    """Cells of one outer split. role 'train' never contains a test cell or a test condition. role 'test' also returns the test cells
    and requires the FROZEN flag file; without it the guard raises before any test cell is built."""
    root = root or _ROOT
    guard.guard_role(role, f"load_split({dataset}, {test}, fold {fold})", root)
    path = split_path(root, dataset, test)
    sp = json.load(open(path, encoding="utf8"))
    block = sp[test] if dataset == "samsung" else sp
    if test == "S3":
        fdef = {"test_conditions": block["test_conditions"], "test_cells": []}
        stored, recomputed = "", ""
    else:
        fdef = block["folds"][str(fold)]
        stored, recomputed = block["sha256_of_folds"], _digest(block["folds"])
        if stored != recomputed:
            raise SplitIntegrityError(f"{path}: stored fold hash {stored[:12]} != recomputed {recomputed[:12]} (a regenerated or edited split)")
    file_sha = sha256_file(path)
    pin = guard.pinned_split(root, dataset, test)          # None before the freeze; after it a missing or different value is an error
    if pin is not None:
        if pin["file_sha256"] != file_sha or (stored and pin["fold_hash"] != stored):
            raise SplitIntegrityError(f"{path}: split file or fold hash differs from the value pinned in FROZEN")
    spec = SPECS[dataset]
    tc = {str(c) for c in fdef.get("test_conditions", [])}
    tids = {str(c) for c in fdef.get("test_cells", [])}

    def is_test(cid, cond, kind, cell_no):
        return cid in tids if test == "A" else (cond in tc or cid in tids)

    def storage_ok(kind, cell_no):          # cells 04-06 have entry/final tests only (prereg 3.3(6))
        return dataset != "samsung" or kind == "cycling" or cell_no <= 3 or include_storage_0406      # the flag is the 9.8(i) sensitivity row

    def keep_train(cid, cond, kind, cell_no):
        return (not is_test(cid, cond, kind, cell_no)) and storage_ok(kind, cell_no)

    def keep_test(cid, cond, kind, cell_no):
        return is_test(cid, cond, kind, cell_no) and storage_ok(kind, cell_no)

    def build(keep):
        if dataset == "samsung":
            return _load_samsung(root, retain_all, throughput, include_at, keep=keep, throughput_fallback=throughput_fallback, include_storage_0406=include_storage_0406, zyk_table_sha256=zyk_table_sha256)
        return (_load_isu if dataset == "isu" else _load_snl)(root, keep=keep)

    train = build(keep_train)             # outer-test cells are filtered out before any array is built
    expected = None
    if dataset == "samsung" and test in ("B", "C"):
        expected = set(fdef["train_cycling_conditions"])
    elif dataset in ("isu", "snl") and fdef.get("train_conditions"):
        expected = {str(c) for c in fdef["train_conditions"]}
    loaded = {c.cond for c in train if c.kind == "cycling"}
    if expected is not None and loaded - expected:         # fail closed: every loaded training condition must be listed in the split
        raise SplitIntegrityError(f"loaded training conditions outside the split's training set: {sorted(loaded - expected)[:3]}")
    missing = sorted(expected - loaded) if expected is not None else []
    train, sub_info = apply_subset(train, dataset, test, fdef, fold, m, subset, subset_draw, root)      # test cells are never thinned
    test_cells, blinded = None, []
    if role != "train":
        guard.require_frozen(f"release of test cells ({dataset} test {test} fold {fold})", root)
        if dataset == "samsung":                    # D026 review I1: the item (f) gate also guards every direct caller, not only run.py
            guard.require_item_f_record(root, runs_dir)
        test_cells = build(keep_test)
        if dataset == "samsung" and not score_blinded_cells:          # 3.3(11): kind (b) pre-freeze exposures are not scored (training sides are untouched); conditions left without a cell vanish, n is reduced
            ex = blinding.excluded_cells(root, test, fold, file_sha)
            blinded = sorted(c.cell_id for c in test_cells if c.cell_id in ex)
            test_cells = [c for c in test_cells if c.cell_id not in ex]
    return SplitView(dataset, test, int(fold), spec, train, test_cells, sorted({c.cond for c in train}), sorted(tc), sorted(tids), path,
                     file_sha, stored, recomputed, _input_manifest(root, dataset), missing, pin is not None, sub_info, blinded)
