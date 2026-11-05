"""Reference and data-only baselines: R1 persistence, R2 window-linear extrapolation, A11 GP-ARD and A12 LightGBM.

A11 / A12 reuse the P3 learners (code/pilots/p3_headroom.py: fit_gp, fit_lgb, predict_cells) by import. They work on cells described by a
dict {cond, tw, rw, t_last, r_last, summ, tf, rf, stress}: the window summary (r_last, first step, slope, curvature, t_last) plus the stress
vector, target = r_last - r(t) at the forecast times. Dataset keys of P3's tables are extended in memory (`P3.TAU_UNIT`), the P3 file is not edited."""
import os
import sys

import numpy as np

from . import ROOT

_PILOTS = os.path.join(ROOT, "code", "pilots")
if _PILOTS not in sys.path:
    sys.path.insert(0, _PILOTS)
import p3_headroom as P3  # noqa: E402

for _ds, _u in (("samsung", 30.0), ("synthetic", 30.0)):     # one check-up step ~ 30 days (pipeline median gap 29 d)
    P3.TAU_UNIT.setdefault(_ds, _u)
    P3.STRESS.setdefault(_ds, ["T_C", "soc_mid", "dod", "c_ch", "c_dch"])


def persistence(wcells):
    return {w.cell_id: np.full(len(w.t_fc), w.y_last) for w in wcells}


def window_linear(wcells):
    """R2: ordinary least-squares line through the window points (reference included), extrapolated; clipped to [0, 1.1]"""
    out = {}
    for w in wcells:
        slope, icpt = np.polyfit(w.t_win, w.y_win, 1)
        out[w.cell_id] = np.clip(icpt + slope * w.t_fc, 0.0, 1.1)
    return out


# ---- D* feature option (PREREG_v4 7.4): the PINN's transformed inputs (A3 abscissae) plus t and EFC, raw and log. P3's feature builder is wrapped, not edited: a cell that carries
# an 'extra' block (n_forecast x e) gets those columns inserted before the horizon column; a cell without it goes through P3's own code unchanged (bit for bit).
_P3_FEAT_ROWS = P3.feat_rows


def _feat_rows_with_extra(cell, ds, tau_log, fs):
    X = _P3_FEAT_ROWS(cell, ds, tau_log, fs)
    ex = cell.get("extra")
    return X if ex is None else np.column_stack([X[:, :-1], ex, X[:, -1:]])


if not getattr(P3.feat_rows, "_pinnkan_wrapped", False):
    _feat_rows_with_extra._pinnkan_wrapped = True
    P3.feat_rows = _feat_rows_with_extra

FEATURE_SETS = ("raw", "pinn")
STORAGE_ROWS = ("in", "out")


def pinn_stress_features(spec, raw):
    """A3 abscissae of raw stress rows (n, d): Arrhenius abscissa of T, log C-rates, log DoD, SOC_mid and SOC_mid^2 (law.ParamMap.feats; storage rows keep their (T, SOC) with the
    log columns at the clamp, as in A3)"""
    from .law import ParamMap
    import torch
    pm = ParamMap(spec)
    with torch.no_grad():
        return pm.feats(torch.tensor(spec.norm(np.atleast_2d(raw)), dtype=torch.float32)).numpy().astype(float)


def pinn_extra_columns(spec, tf, efc_at_tf):
    """t_n, E_n (the PINN's scaled time and cumulative throughput at the forecast points, causal curve) raw and log"""
    tn = np.asarray(tf, float) / spec.t_scale
    en = np.asarray(efc_at_tf, float) / spec.efc_scale
    return np.column_stack([tn, en, np.log(tn + 1e-3), np.log(en + 1e-3)])


def p3_cell(cond, tw, rw, tf, rf, stress, ds, extra=None):
    out = _p3_cell_core(cond, tw, rw, tf, rf, stress, ds)
    if extra is not None:
        out["extra"] = extra
    return out


def _p3_cell_core(cond, tw, rw, tf, rf, stress, ds):
    if len(tw) < 2:          # k = 0: the window is the reference check-up only: stress and horizon, no window feature (PREREG_v4 4.1)
        return dict(cond=cond, tw=tw, rw=rw, t_last=tw[-1], r_last=rw[-1], summ=np.zeros(0), tf=tf, rf=rf, stress=np.asarray(stress, float))
    slope = np.polyfit(tw, rw, 1)[0]
    h = len(tw) // 2
    s1 = np.polyfit(tw[: h + 1], rw[: h + 1], 1)[0] if h >= 1 else slope
    s2 = np.polyfit(tw[h:], rw[h:], 1)[0] if len(tw) - h >= 2 else slope
    u = P3.TAU_UNIT[ds]
    return dict(cond=cond, tw=tw, rw=rw, t_last=tw[-1], r_last=rw[-1], summ=np.array([rw[-1], rw[1], slope * u, (s2 - s1) * u, tw[-1]]),
                tf=tf, rf=rf, stress=np.asarray(stress, float))


def _stress_with_ind(stress, lab, stage, indicator):
    """lab-and-stage indicator columns appended to the static stress features (D* feature set of the lab-indicator row, PREREG_v4 9.8 rule 2)"""
    if not indicator:
        return stress
    from .data import indicator_vector
    return np.concatenate([np.asarray(stress, float), indicator_vector(lab, stage).astype(float)])


def cells_from_prepared(prepared, ds, spec=None, feat="raw", indicator=False):
    """training dict: window summary + forecast truth (the learner is trained to map window summary and horizon to the drop)"""
    if feat == "raw":
        return {p.cell.cell_id: p3_cell(p.cell.cond, p.win.t_win, p.win.y_win, p.win.t_fc, p.fc_true, _stress_with_ind(p.cell.raw, p.cell.lab, p.cell.stage, indicator), ds) for p in prepared}
    return {p.cell.cell_id: p3_cell(p.cell.cond, p.win.t_win, p.win.y_win, p.win.t_fc, p.fc_true, _stress_with_ind(pinn_stress_features(spec, p.cell.raw)[0], p.cell.lab, p.cell.stage, indicator), ds,
                                    extra=pinn_extra_columns(spec, p.win.t_fc, p.win.efc_curve.value(p.win.t_fc))) for p in prepared}


def cells_from_windows(wcells, ds, spec=None, feat="raw", indicator=False):
    if feat == "raw":
        return {w.cell_id: p3_cell(w.cond, w.t_win, w.y_win, w.t_fc, np.zeros(len(w.t_fc)), _stress_with_ind(w.raw, w.lab, w.stage, indicator), ds) for w in wcells}   # rf unused by predict_cells
    return {w.cell_id: p3_cell(w.cond, w.t_win, w.y_win, w.t_fc, np.zeros(len(w.t_fc)), _stress_with_ind(pinn_stress_features(spec, w.raw)[0], w.lab, w.stage, indicator), ds,
                               extra=pinn_extra_columns(spec, w.t_fc, w.efc_curve.value(w.t_fc))) for w in wcells}


class P3Learner:
    """A11 (kind='gp') and A12 (kind='lgb') on (stress, window summary, horizon)."""

    def __init__(self, kind, hp, ds, seed, spec=None, indicator=False):
        self.kind, self.hp, self.ds, self.seed, self.spec, self.indicator = kind, dict(hp), ds, seed, spec, bool(indicator)
        self.feat = self.hp.get("feat", "raw")
        self.storage = self.hp.get("storage", "in")
        if self.feat not in FEATURE_SETS or self.storage not in STORAGE_ROWS:
            raise ValueError(f"feat {self.feat!r} / storage {self.storage!r}: options are {FEATURE_SETS} / {STORAGE_ROWS}")
        if self.feat == "pinn" and spec is None:
            raise ValueError("feat='pinn' needs the dataset spec")
        self.n_train_used = None

    def fit(self, prepared_train):
        if self.storage == "out":                     # storage rows option: out = the learner trains on cycling cells only
            prepared_train = [p for p in prepared_train if p.cell.kind != "storage"]
        self.n_train_used = len(prepared_train)
        cells = cells_from_prepared(prepared_train, self.ds, self.spec, self.feat, self.indicator)
        names = sorted(cells)
        if cells and all(len(c["summ"]) == 0 for c in cells.values()):
            self.hp = dict(self.hp, fs="full")          # no window feature exists at k = 0: the 'min' feature set (which indexes window columns) is not defined
        if self.kind == "gp":
            p = dict(nu=self.hp.get("nu", 2.5), m=4, tau_log=True, fs=self.hp.get("fs", "full"), noise_lo=self.hp.get("noise_lo", 1e-4))
            self.fn = P3.fit_gp(cells, names, p, self.ds, self.seed)
            self.tau_log, self.fs = p["tau_log"], p["fs"]
        else:
            p = dict(n_est=int(self.hp.get("n_est", 200)), lr=float(self.hp.get("lr", 0.05)), leaves=int(self.hp.get("leaves", 8)), mcs=int(self.hp.get("mcs", 20)),
                     sub=0.8, col=0.8, l2=float(self.hp.get("l2", 1.0)), mono=True, tau_log=False)
            self.fn = P3.fit_lgb(cells, names, p, self.ds, self.seed)
            self.tau_log, self.fs = p["tau_log"], "full"
        return self

    def predict(self, wcells):
        cells = cells_from_windows(wcells, self.ds, self.spec, self.feat, self.indicator)
        return P3.predict_cells(cells, sorted(cells), self.ds, self.fn, self.tau_log, self.fs)
