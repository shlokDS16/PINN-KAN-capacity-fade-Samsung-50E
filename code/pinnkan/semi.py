"""A10: the dataset authors' semi-empirical calendar + cycle superposition (Stroebl et al., data paper SI S.1.1, after Muehlbauer et al.).

STATUS: PROVISIONAL (A10_FORM['verified'] is False). The form below is the one in notes/papers/samsung50e_dataset_paper.md lines 94-103,
where the exponent placement is marked garbled by the PDF conversion. It is implemented so that the fitter, the per-cell factor and the
recovery test exist; a confirmatory run refuses A10 until the form is checked against the SI and the unread JES 142, 119552 full text [FB-2].

    loss_rel = kappa_c * ( Q_cal + Q_cyc )                                       (retention-loss fraction)
    Q_cal = exp(lc_cal) * [ exp(-p0 * 1e4 * (1/T - 1/Tref)) * (SOC/0.5)^p1 * t_n ]^(1/r_cal)
    Q_cyc = exp(lc_cyc) * [ exp(-q0 * 1e4 * (1/T - 1/Tref)) * prod_j (x_j / ref_j)^q_j * E_n ]^(1/r_cyc)
(x_j: SOC_max, C_ch, C_dch, DoD for Samsung; EOLC, the reference values tref/FECref and the (1 - EOLC) factor are absorbed by the free
log-scales lc_*. TODO [FB-2]: (i) exponent placement, (ii) SOC argument of the calendar term for cycling cells (SOC_mid is assumed here),
(iii) published parameter bounds / start values.)
Per-cell factor (A10 primary, 1.4): kappa_c = exp(delta_c), delta_c by MAP from the window with prior sd TAU; `per_cell_factor=False` is the
"A10 as published" sensitivity row. ISU / SNL analogue (prereg 3.4): cyclic term only (no calendar), same power-law structure on the stresses
the dataset has; chemistry flags (SNL) enter as additive log-scale offsets. The analogue's factor set is the builder's choice (flagged in README).
"""
import numpy as np
from scipy.optimize import least_squares, minimize_scalar

from .law import SIGMA, TAU

A10_FORM = {"status": "PROVISIONAL_FROM_DATASET_NOTES", "verified": False,
            "todo": ["exponent placement (garbled in the local conversion)", "SOC argument of the calendar term for cycling cells (SOC_mid assumed)",
                     "published parameter bounds and start values", "EOLC and reference values (absorbed in free log-scales)"]}


class UnverifiedArmError(RuntimeError):
    pass


def require_verified():
    if not A10_FORM["verified"]:
        raise UnverifiedArmError("A10 equations are not verified against Stroebl SI S.1.1 / JES 142, 119552 [FB-2]; confirmatory use refused. "
                                 + "; ".join(A10_FORM["todo"]))


TREF = 298.15


def _inv_t(T_C):
    return 1.0 / (273.15 + np.asarray(T_C, float)) - 1.0 / TREF


class SemiForm:
    """feature extraction + parameter layout per dataset"""

    def __init__(self, spec):
        self.spec = spec
        n = spec.name
        self.has_cal = spec.has_calendar
        if n in ("samsung", "synthetic"):
            self.t_idx, self.flags = 0, []
            self.refs = np.array([0.5, 0.5, 1.0, 0.3])           # SOC_max, C_ch, C_dch, DoD
        elif n == "isu":
            self.t_idx, self.flags = None, []
            self.refs = np.array([1.0, 1.0, 0.5])                # C_ch, C_dch, DoD
        else:
            self.t_idx, self.flags = 3, [0, 1, 2]
            self.refs = np.array([0.8, 1.0, 1.0])                # DoD, C_ch, C_dch
        self.nx = len(self.refs)
        self.n_cal = 4 if self.has_cal else 0
        self.n_cyc = 1 + (1 if self.t_idx is not None else 0) + self.nx + 1 + len(self.flags)

    @property
    def n_params(self):
        return self.n_cal + self.n_cyc

    def xfeat(self, raw):
        raw = np.atleast_2d(raw)
        n = self.spec.name
        if n in ("samsung", "synthetic"):
            return np.column_stack([raw[:, 1] + raw[:, 2] / 2.0, raw[:, 3], raw[:, 4], raw[:, 2]])
        if n == "isu":
            return np.column_stack([raw[:, 0], raw[:, 1], raw[:, 2] / 100.0])
        return np.column_stack([raw[:, 4], raw[:, 5], raw[:, 6]])

    def loss(self, th, raw, t, efc):
        """predicted retention-loss fraction at times t (unit) with cumulative efc; one cell"""
        raw = np.asarray(raw, float)
        tn = np.maximum(np.asarray(t, float) / self.spec.t_scale, 0.0)
        En = np.maximum(np.asarray(efc, float) / self.spec.efc_scale, 0.0)
        i, q = 0, np.zeros_like(tn)
        if self.has_cal:
            lc, p0, p1, r = th[0], th[1], th[2], th[3]
            soc = max(float(raw[self.spec.soc_index]), 0.02)
            arg = np.exp(-p0 * 1e4 * float(_inv_t(raw[self.spec.t_index]))) * (soc / 0.5) ** p1 * tn
            q = q + np.exp(lc) * np.power(arg, 1.0 / max(r, 0.1))
            i = 4
        lc = th[i]
        i += 1
        la = 0.0
        if self.t_idx is not None:
            la = -th[i] * 1e4 * float(_inv_t(raw[self.t_idx]))
            i += 1
        x = np.maximum(self.xfeat(raw)[0] / self.refs, 1e-3)
        la += float(np.sum(th[i:i + self.nx] * np.log(x)))
        i += self.nx
        r = th[i]
        i += 1
        for f_k, off in zip(self.flags, th[i:i + len(self.flags)]):
            lc = lc + off * raw[f_k]
        return q + np.exp(lc) * np.power(np.exp(la) * En, 1.0 / max(r, 0.1))

    def bounds(self):
        lo, hi = [], []
        if self.has_cal:
            lo += [-12, -3, -5, 0.3]
            hi += [4, 3, 5, 5]
        lo += [-12]
        hi += [4]
        if self.t_idx is not None:
            lo += [-3]
            hi += [3]
        lo += [-5] * self.nx
        hi += [5] * self.nx
        lo += [0.3]
        hi += [5]
        lo += [-4] * len(self.flags)
        hi += [4] * len(self.flags)
        return np.array(lo, float), np.array(hi, float)

    def starts(self, n, seed):
        rng = np.random.default_rng([20261106, 10, seed])
        lo, hi = self.bounds()
        out = []
        for _ in range(n):
            th = np.zeros(len(lo))
            i = 0
            if self.has_cal:
                th[0:4] = [rng.uniform(-6, -1), rng.uniform(0, 1.5), rng.uniform(0, 1.5), rng.uniform(0.8, 2.5)]
                i = 4
            th[i] = rng.uniform(-6, -1)
            i += 1
            if self.t_idx is not None:
                th[i] = rng.uniform(0, 1.5)
                i += 1
            th[i:i + self.nx] = rng.uniform(-0.5, 1.5, self.nx)
            i += self.nx
            th[i] = rng.uniform(0.8, 2.5)
            out.append(np.clip(th, lo + 1e-6, hi - 1e-6))
        return out


def fit_semi(form: SemiForm, cells, n_starts=8, seed=0):
    """population parameters by multi-start least squares on the training records (retention-loss residuals)"""
    lo, hi = form.bounds()
    data = [(c.raw, c.t[1:], c.efc[1:], 1.0 - c.ret[1:]) for c in cells if c.n > 1 and (form.has_cal or c.kind == "cycling")]

    def resid(th):
        return np.concatenate([form.loss(th, r, t, e) - y for r, t, e, y in data])
    best = None
    for th0 in form.starts(n_starts, seed):
        try:
            sol = least_squares(resid, th0, bounds=(lo, hi), method="trf", max_nfev=200)
        except Exception:
            continue
        if np.isfinite(sol.cost) and (best is None or sol.cost < best.cost):
            best = sol
    if best is None:
        raise RuntimeError("A10 multi-start least squares failed in every start")
    return best.x, float(best.cost)


def cell_factor(form: SemiForm, th, wc):
    """delta_c by MAP from the window (kappa = exp(delta)); prior sd TAU, noise SIGMA / y_scale in retention units"""
    sig = SIGMA / form.spec.y_scale
    base = form.loss(th, wc.raw, wc.t_win[1:], wc.efc_win[1:])
    y = 1.0 - wc.y_win[1:]

    def nll(d):
        return float(np.sum((np.exp(d) * base - y) ** 2) / sig ** 2 + d * d / TAU ** 2)
    return float(minimize_scalar(nll, bounds=(-2.0, 2.0), method="bounded").x)


def predict_semi(form: SemiForm, th, wcells, per_cell_factor=True):
    out = {}
    for w in wcells:
        d = cell_factor(form, th, w) if (per_cell_factor and len(w.t_win) > 1) else 0.0      # k = 0: population parameters, factor 1 (PREREG_v4 4.1)
        efc_fc = w.efc_curve.value(w.t_fc)
        out[w.cell_id] = 1.0 - np.exp(d) * form.loss(th, w.raw, w.t_fc, efc_fc)
    return out
