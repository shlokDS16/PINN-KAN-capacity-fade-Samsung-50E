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
import hashlib
import json
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import ROOT as _ROOT
from . import guard
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

    def __init__(self, t, efc, upto=None):
        w = len(t) - 1 if upto is None else int(upto)
        self.t, self.e = np.asarray(t[: w + 1], float), np.asarray(efc[: w + 1], float)
        span = self.t[-1] - self.t[0]
        self.tail = float((self.e[-1] - self.e[0]) / span) if span > 0 else 0.0

    def value(self, tq):
        tq = np.asarray(tq, float)
        inside = np.interp(tq, self.t, self.e)
        return np.where(tq > self.t[-1], self.e[-1] + self.tail * (tq - self.t[-1]), inside)

    def rate(self, tq):
        tq = np.asarray(tq, float)
        if len(self.t) < 2:
            return np.full(tq.shape, self.tail)
        slopes = np.diff(self.e) / np.diff(self.t)
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
        return int(k)  # reference + k check-ups


def window_rule_from_counts(counts_cycling, counts_storage=None):
    """Prereg 5: k_cyc = round(n_med / 3) from intermediate check-up counts (CU + exCU; ET, AT excluded) per cell, identifiers only."""
    kc = int(round(float(np.median(counts_cycling)) / 3.0))
    ks = int(round(float(np.median(counts_storage)) / 3.0)) if counts_storage is not None and len(counts_storage) else None
    return kc, ks


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
    curve = EFCCurve(cell.t, cell.efc, upto=None if oracle else w)
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

# Dropped at file level (prereg 3.3(4)). Names as printed in the dataset paper: <serial>_<file>_<kind>. The paper does not name the
# stage, so a drop applies to BOTH stages of that serial (over-drop risk, counted in meta). TODO [FB-4]: map each to its stage.
INCIDENT_FILE_DROPS = [("TP_z25_01", 1, "ET"), ("TP_z01_03", 11, "CU"), ("TP_z17_03", 13, "exCU"), ("TP_z17_03", 17, "CU"),
                       ("TP_z17_02", 19, "exCU"), ("TP_k11_02", 3, "exCU")]
# TODO [FB-4]: "every later check-up of a cell whose cycling segment shows undefined load or wrong SOC_max (TP_z24_01_02, TP_z25_01_04,
# TP_z07_03_16, TP_z20_03_16, TP_z17 from segment 18) is dropped from that point" needs the segment-to-file map of the complete download.
INCIDENT_CONSECUTIVE_DROPS_IMPLEMENTED = False


def samsung_cond_key(kind, T, soc_max, dod, c_ch, c_dch):
    if kind == "cycling":
        return "T%g|SOCmax%g|DoD%g|Cch%g|Cdch%g" % (T, soc_max, dod, c_ch, c_dch)
    return "T%g|SOC%g" % (T, soc_max)


def _load_samsung(root, retain_all=False, throughput="analytic", include_at=False, drop_incidents=True, keep=None):
    if throughput not in ("analytic", "zyk"):
        raise ValueError(throughput)
    df = pd.read_csv(os.path.join(root, "data", "processed", "samsung_checkups.csv"))
    n_incident = 0
    if drop_incidents:
        m = np.zeros(len(df), bool)
        for ser, fidx, knd in INCIDENT_FILE_DROPS:
            m |= ((df["serial"] == ser) & (df["file_idx"] == fidx) & (df["kind"] == knd)).to_numpy()
        n_incident = int(m.sum())
        df = df[~m]
    if not retain_all:
        df = df[df["qc_pass"].astype(str).str.lower().isin(["true", "1"])]
    if not include_at:
        df = df[df["kind"] != "AT"]
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
        ret = g["retention"].to_numpy(float)
        ret = ret / ret[0]
        if throughput == "zyk":
            if "efc_zyk_cum" not in g.columns:
                raise NotImplementedError("ZYK-logged throughput is not on disk yet (prereg 5, [FB-5]); use throughput='analytic'")
            e = g["efc_zyk_cum"].to_numpy(float)
        else:
            e = g["efc_est_cum"].to_numpy(float) if kind == "cycling" else np.zeros(len(g))
        e = np.nan_to_num(e - e[0], nan=0.0)
        T, smax, dod, cch, cdch = (float(r0[c]) for c in ("T_C", "SOC_max", "DoD", "C_ch", "C_dch"))
        raw = np.array([T, smax - dod / 2.0, dod, cch, cdch]) if kind == "cycling" else np.array([T, smax, 0.0, 0.0, 0.0])
        fc_ok = g["kind"].isin(["CU", "exCU"]).to_numpy()
        fc_ok[0] = False
        cells.append(Cell(cid, "samsung", kind, cond, raw, t, ret, e, fc_ok,
                          lab=str(r0["lab"]), stage=str(int(r0["stage"])),
                          meta={"cell_no": int(r0["cell"]), "tp": int(r0["tp"]), "n_incident_rows_dropped_dataset": n_incident}))
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

    @property
    def hash_ok(self):
        return self.fold_hash_stored == self.fold_hash_recomputed


def _input_manifest(root, dataset):
    names = {"samsung": ["samsung_checkups.csv"], "isu": ["isu_capacity.csv", "isu_conditions.csv"], "snl": ["snl_cells.csv", "snl_cycles.csv"]}[dataset]
    out = []
    for n in names:
        p = os.path.join(root, "data", "processed", n)
        if os.path.isfile(p):
            out.append({"path": os.path.relpath(p, root).replace("\\", "/"), "size": os.path.getsize(p), "sha256": sha256_file(p)})
    return out


def load_split(dataset, test, fold, role="train", root=None, retain_all=False, throughput="analytic", include_at=False):
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
    spec = SPECS[dataset]
    tc = {str(c) for c in fdef.get("test_conditions", [])}
    tids = {str(c) for c in fdef.get("test_cells", [])}

    def is_test(cid, cond, kind, cell_no):
        return cid in tids if test == "A" else (cond in tc or cid in tids)

    def storage_ok(kind, cell_no):          # cells 04-06 have entry/final tests only (prereg 3.3(6))
        return dataset != "samsung" or kind == "cycling" or cell_no <= 3

    def keep_train(cid, cond, kind, cell_no):
        return (not is_test(cid, cond, kind, cell_no)) and storage_ok(kind, cell_no)

    def keep_test(cid, cond, kind, cell_no):
        return is_test(cid, cond, kind, cell_no) and storage_ok(kind, cell_no)

    def build(keep):
        if dataset == "samsung":
            return _load_samsung(root, retain_all, throughput, include_at, keep=keep)
        return (_load_isu if dataset == "isu" else _load_snl)(root, keep=keep)

    train = build(keep_train)             # outer-test cells are filtered out before any array is built
    test_cells = None
    if role != "train":
        guard.require_frozen(f"release of test cells ({dataset} test {test} fold {fold})", root)
        test_cells = build(keep_test)
    return SplitView(dataset, test, int(fold), spec, train, test_cells, sorted({c.cond for c in train}), sorted(tc), sorted(tids), path,
                     sha256_file(path), stored, recomputed, _input_manifest(root, dataset))
