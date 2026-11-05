"""A10: the dataset authors' semi-empirical calendar + cycle superposition (Stroebl et al.; after Muehlbauer et al.).

STATUS: VERIFIED 2026-11-05 against the full text [FB-2]. Sources and equation numbers (notes/papers/stroebl2025_JES142_OED.md has the claim-evidence table):
    Stroebl et al., J. Energy Storage 142, 119552 (doi 10.1016/j.est.2025.119552): Eq. (17) superposition, Eq. (18) calendar, Eq. (21) cycle, Tables D.2 / D.3;
    Stroebl et al., Sci. Data 11, 1020 (2024), Supplement S.1.1: Eq. S.1 superposition, S.2 calendar, S.3 cycle.
  Published form (relative capacity LOSS as a fraction of Q0; T in K; t in days; FEC = fully equivalent cycles):
    Q_loss = Q_cal + Q_cyc                                                                            (JES 17; SI S.1)
    Q_cal = (1-EOLC) exp(-th0 (1/T - 1/Tref)) (SOC/SOCref)^(1/th1) (t/tref)^th2                       (JES 18; SI S.2)
    Q_cyc = (1-EOLC) exp(-th0 (1/T - 1/Tref)) (SOCmax/ref)^(1/th1) (Cch/ref)^(1/th2) (Cdch/ref)^(1/th3) (DoD/ref)^(1/th4) (FEC/FECref)^th5     (SI S.3; JES 21 prints the
    exponents th2..th4 without the reciprocal -- a source conflict; the function class is the same and Table D.3 magnitudes agree with the SI reading, see the note)
  Implemented (a re-parameterisation with free log-scales; the map is exercised in code/tests/test_pk_a10_paper_form.py on hand-worked inputs and in a recovery test):
    loss_rel = Q_cal + Q_cyc
    Q_cal = exp(lc_cal) * [ exp(-p0 * 1e4 * (1/T - 1/Tref)) * (SOC/0.5)^p1 * t_n ]^(1/r_cal)
    Q_cyc = exp(lc_cyc) * [ exp(-q0 * 1e4 * (1/T - 1/Tref)) * prod_j (x_j / ref_j)^q_j * E_n ]^(1/r_cyc)
    with r_cal = 1/th2_cal, p0 = th0_cal r_cal / 1e4, p1 = r_cal / th1_cal;  r_cyc = 1/th5_cyc, q0 = th0_cyc r_cyc / 1e4, q_j = (exponent of factor j) r_cyc.
  (x_j: SOC_max, C_ch, C_dch, DoD for Samsung; for the SOC argument of the calendar term of a CYCLING cell the paper gives no rule: SOC_mid is the code's choice.)
Documented deviations from the published fit (none changes the function class; M1, M3-M5 in the note): (M1) the published model has no free scale (EOLC fixed, reference values not
published), here lc_cal and lc_cyc are free, so the published form is nested; (M3) one joint least-squares fit of both terms on all training cells, whereas the authors fit Q_cal on storage cells
and Q_cyc on cycling cells separately; (M4) the calendar term is added for cycling cells (superposition, Eq. 17) with SOC_mid; (M5) the authors drop SOC = 100 % storage from the calendar
fit (non-monotonic, JES Sec. 3.1) and remove flagged outliers; this code applies no such filter (the data layer decides).
Per-cell factor (A10 primary, 1.4): kappa_c = exp(delta_c), delta_c by MAP from the window with prior sd TAU; `per_cell_factor=False` is the
"A10 as published" sensitivity row. ISU / SNL analogue (prereg 3.4): cyclic term only (no calendar), same power-law structure on the stresses
the dataset has; chemistry flags (SNL) enter as additive log-scale offsets. The analogue's factor set is the builder's choice (flagged in README).
"""
import numpy as np
from scipy.optimize import least_squares, minimize_scalar

from .law import SIGMA, TAU

A10_FORM = {"status": "VERIFIED_AGAINST_STROEBL_JES142_EQ17_18_21_AND_SI_S1_S3", "verified": True, "verified_on": "2026-11-05",
            "equations": {"superposition": "JES142 Eq. (17); SI Eq. S.1", "calendar": "JES142 Eq. (18); SI Eq. S.2", "cycle": "SI Eq. S.3 (JES142 Eq. (21) differs in the exponent convention of C_ch, C_dch, DoD)",
                          "parameters": "JES142 Tables D.2 (calendar) and D.3 (cycle)"},
            "deviations": ["M1 free log-scales lc_cal, lc_cyc (published model has none; EOLC and reference values are not published)",
                           "M3 joint least-squares fit of both terms (authors fit calendar on storage cells, cycle on cycling cells)",
                           "M4 calendar term added for cycling cells with SOC_mid as its SOC (superposition is published, the SOC argument for cycling cells is not)",
                           "M5 no exclusion of SOC = 100 % storage (authors exclude it from the calendar fit) and no outlier rule inside this module"],
            "todo": []}


class UnverifiedArmError(RuntimeError):
    pass


def require_verified():
    if not A10_FORM["verified"]:
        raise UnverifiedArmError("A10 equations are not verified against Stroebl SI S.1.1 / JES 142, 119552 [FB-2]; confirmatory use refused. "
                                 + "; ".join(A10_FORM.get("todo") or []))


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


def cell_factor(form: SemiForm, th, wc, mu=0.0):
    """delta_c by MAP from the window (kappa = exp(delta)); prior N(mu, TAU^2) (mu = 0 in the primary analysis), noise SIGMA / y_scale in retention units"""
    sig = SIGMA / form.spec.y_scale
    base = form.loss(th, wc.raw, wc.t_win[1:], wc.efc_win[1:])
    y = 1.0 - wc.y_win[1:]

    def nll(d):
        return float(np.sum((np.exp(d) * base - y) ** 2) / sig ** 2 + (d - mu) ** 2 / TAU ** 2)
    return float(minimize_scalar(nll, bounds=(-2.0, 2.0), method="bounded").x)


def indicator_beta(form: SemiForm, th, cells, ridge=1.0):
    """rows 9.8(ii): prior mean of A10's per-cell factor from the lab-and-stage indicators. Each training cell's delta_c is the MAP from its full record under the N(0, TAU^2) prior, then ridge
    regression of delta_c on [1, indicators] (ridge 1 on the indicator coefficients, none on the intercept: the population fit is not centred on the reference group).
    Returns [intercept, b_INT, b_SIE, b_stage2]."""
    from .data import indicator_vector
    X, d = [], []
    for c in cells:
        if c.n < 2 or not (form.has_cal or c.kind == "cycling"):
            continue
        wc = type("W", (), dict(raw=c.raw, t_win=c.t, efc_win=c.efc, y_win=c.ret))
        X.append(np.concatenate([[1.0], indicator_vector(c.lab, c.stage).astype(float)]))
        d.append(cell_factor(form, th, wc, mu=0.0))
    if not X:
        return np.zeros(4)
    X, d = np.array(X), np.array(d)
    R = ridge * np.eye(X.shape[1])
    R[0, 0] = 0.0
    return np.linalg.solve(X.T @ X + R, X.T @ d)


def predict_semi(form: SemiForm, th, wcells, per_cell_factor=True, beta=None):
    from .data import indicator_vector
    out = {}
    for w in wcells:
        mu = 0.0 if beta is None else float(beta[0] + indicator_vector(w.lab, w.stage).astype(float) @ beta[1:])      # indicator prior mean of the factor (rows 9.8(ii))
        d = cell_factor(form, th, w, mu) if (per_cell_factor and len(w.t_win) > 1) else (mu if per_cell_factor else 0.0)      # k = 0: population parameters, factor at its prior mean (1 in the primary analysis; PREREG_v4 4.1)
        efc_fc = w.efc_curve.value(w.t_fc)
        out[w.cell_id] = 1.0 - np.exp(d) * form.loss(th, w.raw, w.t_fc, efc_fc)
    return out
