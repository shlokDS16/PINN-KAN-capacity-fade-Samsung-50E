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


def p3_cell(cond, tw, rw, tf, rf, stress, ds):
    if len(tw) < 2:          # k = 0: the window is the reference check-up only: stress and horizon, no window feature (PREREG_v4 4.1)
        return dict(cond=cond, tw=tw, rw=rw, t_last=tw[-1], r_last=rw[-1], summ=np.zeros(0), tf=tf, rf=rf, stress=np.asarray(stress, float))
    slope = np.polyfit(tw, rw, 1)[0]
    h = len(tw) // 2
    s1 = np.polyfit(tw[: h + 1], rw[: h + 1], 1)[0] if h >= 1 else slope
    s2 = np.polyfit(tw[h:], rw[h:], 1)[0] if len(tw) - h >= 2 else slope
    u = P3.TAU_UNIT[ds]
    return dict(cond=cond, tw=tw, rw=rw, t_last=tw[-1], r_last=rw[-1], summ=np.array([rw[-1], rw[1], slope * u, (s2 - s1) * u, tw[-1]]),
                tf=tf, rf=rf, stress=np.asarray(stress, float))


def cells_from_prepared(prepared, ds):
    """training dict: window summary + forecast truth (the learner is trained to map window summary and horizon to the drop)"""
    return {p.cell.cell_id: p3_cell(p.cell.cond, p.win.t_win, p.win.y_win, p.win.t_fc, p.fc_true, p.cell.raw, ds) for p in prepared}


def cells_from_windows(wcells, ds):
    return {w.cell_id: p3_cell(w.cond, w.t_win, w.y_win, w.t_fc, np.zeros(len(w.t_fc)), w.raw, ds) for w in wcells}   # rf unused by predict_cells


class P3Learner:
    """A11 (kind='gp') and A12 (kind='lgb') on (stress, window summary, horizon)."""

    def __init__(self, kind, hp, ds, seed):
        self.kind, self.hp, self.ds, self.seed = kind, dict(hp), ds, seed

    def fit(self, prepared_train):
        cells = cells_from_prepared(prepared_train, self.ds)
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
        cells = cells_from_windows(wcells, self.ds)
        return P3.predict_cells(cells, sorted(cells), self.ds, self.fn, self.tau_log, self.fs)
