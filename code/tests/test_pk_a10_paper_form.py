"""A10 against the dataset authors' published equations [FB-2].

Sources (full text read, notes/papers/stroebl2025_JES142_OED.md):
    Stroebl et al., J. Energy Storage 142, 119552, doi 10.1016/j.est.2025.119552: Eq. (17) superposition, Eq. (18) calendar, Eq. (21) cycle, Tables D.2 / D.3.
    Stroebl et al., Sci. Data 11, 1020 (2024), Supplement S.1.1: Eq. S.1 superposition, S.2 calendar, S.3 cycle.
Everything below is generated from the paper's equations with the paper's own published parameter values (Table D.2 case 3, Table D.3 case 2) and fitted by the
code's A10 form. No Samsung capacity value is read anywhere (stress design from the synthetic generator, which uses stress ranges only).

    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_a10_paper_form.py -q        (CPU)
"""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

from pinnkan import data, semi, synth
from pinnkan.specs import SPECS

SPEC = SPECS["synthetic"]            # Samsung stress structure and units: (T_C, SOC_mid, DoD, C_ch, C_dch), days, EFC

# ---- the paper's published parameter values (JES 142, 119552)
TH_CAL = (3941.0, 0.82, 0.58)                       # Table D.2, case 3 (S1 + S2b): theta_cal_0 [K], theta_cal_1, theta_cal_2
TH_CYC = (1537.0, 1.23, 9.55, -21.63, 2.5, 0.52)    # Table D.3, case 2 (S1 + S2a): theta_cyc_0 [K], _1 ... _5
# ---- reference values and EOLC are NOT published in the JES text or the SI: the numbers below are test conventions, chosen only to keep the generated losses plausible
EOLC = 0.8
TREF = 298.15
CAL_REF = dict(soc=0.5, t=10000.0)                   # days
CYC_REF = dict(smax=0.5, cch=0.5, cdch=1.0, dod=0.3, fec=10000.0)      # generated losses: median final loss 0.13, maximum 0.36 on the synthetic design
HAND_CAL_REF = dict(soc=0.5, t=1000.0)                # references of the two hand-worked examples
HAND_CYC_REF = dict(smax=0.5, cch=0.5, cdch=1.0, dod=0.3, fec=1000.0)


def paper_cal(T_K, soc, t_days, th=TH_CAL, ref=CAL_REF, eolc=EOLC, tref=TREF):
    """Eq. (18) of JES 142 / Eq. S.2 of the SI, written term by term (relative capacity LOSS, fraction of Q0)"""
    return (1.0 - eolc) * math.exp(-th[0] * (1.0 / T_K - 1.0 / tref)) * (soc / ref["soc"]) ** (1.0 / th[1]) * (t_days / ref["t"]) ** th[2]


def paper_cyc(T_K, smax, cch, cdch, dod, fec, th=TH_CYC, ref=CYC_REF, eolc=EOLC, tref=TREF, convention="SI"):
    """Eq. S.3 of the SI (exponent 1/theta_j on SOC_max, C_ch, C_dch, DoD; theta_5 on FEC). convention='JES' reads Eq. (21) of the JES text as extracted: 1/theta_1 on SOC_max
    but theta_2..theta_4 (no reciprocal) on C_ch, C_dch, DoD. The two sources disagree; see the note."""
    ex = [1.0 / th[1]] + ([1.0 / th[2], 1.0 / th[3], 1.0 / th[4]] if convention == "SI" else [th[2], th[3], th[4]])
    return ((1.0 - eolc) * math.exp(-th[0] * (1.0 / T_K - 1.0 / tref)) * (smax / ref["smax"]) ** ex[0] * (cch / ref["cch"]) ** ex[1]
            * (cdch / ref["cdch"]) ** ex[2] * (dod / ref["dod"]) ** ex[3] * (fec / ref["fec"]) ** th[5])


def paper_to_code(th_cal=TH_CAL, th_cyc=TH_CYC, convention="SI", ref_cal=CAL_REF, ref_cyc=CYC_REF, eolc=EOLC, tref=TREF):
    """The code's A10 vector [lc_cal, p0, p1, r_cal | lc_cyc, q0, q_SOCmax, q_Cch, q_Cdch, q_DoD, r_cyc] equivalent to the paper's parameters.
    Code: exp(lc) * [exp(-p0*1e4*D) * prod x_j^q_j * X]^(1/r), D = 1/T - 1/298.15. With r = 1/(time or FEC exponent), p0 = theta_0 * r / 1e4, q_j = (exponent of factor j) * r,
    and the log-scale lc absorbing (1 - EOLC), the paper's reference values and the shift of T_ref (298.15 here)."""
    a = th_cal
    r_cal = 1.0 / a[2]
    a_soc = 1.0 / a[1]
    lc_cal = math.log(1.0 - eolc) + a_soc * math.log(0.5 / ref_cal["soc"]) + a[2] * math.log(SPEC.t_scale / ref_cal["t"]) - a[0] * (1.0 / 298.15 - 1.0 / tref)
    c = th_cyc
    ex = [1.0 / c[1]] + ([1.0 / c[2], 1.0 / c[3], 1.0 / c[4]] if convention == "SI" else [c[2], c[3], c[4]])
    r_cyc = 1.0 / c[5]
    form_refs = semi.SemiForm(SPEC).refs                                 # [SOC_max, C_ch, C_dch, DoD] reference values used inside the code
    pref = [ref_cyc["smax"], ref_cyc["cch"], ref_cyc["cdch"], ref_cyc["dod"]]
    lc_cyc = (math.log(1.0 - eolc) + sum(e * math.log(f / p) for e, f, p in zip(ex, form_refs, pref)) + c[5] * math.log(SPEC.efc_scale / ref_cyc["fec"])
              - c[0] * (1.0 / 298.15 - 1.0 / tref))
    return np.array([lc_cal, a[0] * r_cal / 1e4, a_soc * r_cal, r_cal, lc_cyc, c[0] * r_cyc / 1e4] + [e * r_cyc for e in ex] + [r_cyc])


# ------------------------------------------------------------------------------------------------ hand-worked equation checks
def test_hand_worked_calendar_equation_18():
    """T = 45 C = 318.15 K, SOC = 0.8, t = 100 d, theta = (4894, 0.84, 0.58) (Table D.2 case 1), EOLC = 0.8, T_ref = 298.15 K, SOC_ref = 0.5, t_ref = 1000 d.
    by hand:  1/318.15 - 1/298.15 = -2.10845e-4 1/K;  exp(4894 * 2.10845e-4) = exp(1.03189) = 2.80632;
              (0.8/0.5)^(1/0.84) = 1.6^1.190476 = exp(0.559531) = 1.74985;  (100/1000)^0.58 = exp(-1.335) = 0.26303;
              loss = (1 - 0.8) * 2.80632 * 1.74985 * 0.26303 = 0.258326"""
    th = (4894.0, 0.84, 0.58)
    want = 0.2583258
    assert paper_cal(318.15, 0.8, 100.0, th, ref=HAND_CAL_REF) == pytest.approx(want, rel=1e-5)
    form = semi.SemiForm(SPEC)
    code_th = paper_to_code(th_cal=th, ref_cal=HAND_CAL_REF)
    got = form.loss(code_th, np.array([45.0, 0.8, 0.0, 0.0, 0.0]), np.array([100.0]), np.array([0.0]))[0]       # storage cell: no cycling, EFC = 0
    assert got == pytest.approx(want, rel=1e-5)


def test_hand_worked_cycle_equation_S3():
    """T = 35 C = 308.15 K, SOC_max = 0.7, C_ch = 0.5, C_dch = 1.0, DoD = 0.4, FEC = 200, theta = Table D.3 case 2 (SI exponents 1/theta on factors 1..4), EOLC = 0.8.
    by hand:  exp(1537 * (1/298.15 - 1/308.15)) = exp(0.16573) = 1.18210;  (0.7/0.5)^(1/1.23) = 1.4^0.81301 = 1.31463;  (0.5/0.5)^.. = 1;  (1.0/1.0)^.. = 1;
              (0.4/0.3)^(1/2.5) = 1.3333^0.4 = 1.12196;  (200/1000)^0.52 = 0.43305;   loss = 0.2 * 1.18210 * 1.31463 * 1 * 1 * 1.12196 * 0.43305 = 0.151008"""
    want = 0.1510075
    assert paper_cyc(308.15, 0.7, 0.5, 1.0, 0.4, 200.0, ref=HAND_CYC_REF) == pytest.approx(want, rel=1e-5)
    form = semi.SemiForm(SPEC)
    code_th = paper_to_code(ref_cyc=HAND_CYC_REF)
    raw = np.array([35.0, 0.7 - 0.4 / 2.0, 0.4, 0.5, 1.0])                  # (T, SOC_mid, DoD, C_ch, C_dch): SOC_max = SOC_mid + DoD/2 = 0.7
    assert form.xfeat(raw)[0][0] == pytest.approx(0.7)
    got = form.loss(code_th, raw, np.array([0.0]), np.array([200.0]))[0]          # t = 0: the calendar term is exactly 0, the cycle term alone remains
    assert got == pytest.approx(want, rel=1e-5)


@pytest.mark.parametrize("convention", ["SI", "JES"])
def test_code_form_equals_paper_form_on_random_stress_points(convention):
    """the code form is the paper form under the documented parameter map, for both exponent conventions (they differ only by theta_j <-> 1/theta_j on C_ch, C_dch, DoD)"""
    rng = np.random.default_rng(3)
    form = semi.SemiForm(SPEC)
    th = paper_to_code(convention=convention)
    for _ in range(40):
        T, smax, dod = rng.choice([23.0, 35.0, 45.0]), rng.uniform(0.3, 0.8), rng.uniform(0.2, 0.6)
        cch, cdch = rng.uniform(0.05, 1.0), rng.uniform(0.05, 2.0)
        t, fec = rng.uniform(5, 400), rng.uniform(5, 400)
        soc_mid = smax - dod / 2.0
        raw = np.array([T, soc_mid, dod, cch, cdch])
        want = paper_cal(T + 273.15, max(soc_mid, 0.02), t) + paper_cyc(      # the code floors the calendar SOC at 0.02 (a guard against 0^p)
            T + 273.15, smax, cch, cdch, dod, fec, convention=convention)
        got = form.loss(th, raw, np.array([t]), np.array([fec]))[0]
        assert got == pytest.approx(want, rel=1e-9, abs=1e-12)


def test_published_parameter_values_are_inside_the_code_bounds_for_the_SI_convention_only():
    """Table D.3 gives theta_2 = 9.55, theta_3 = -21.63 for C_ch, C_dch. Read as exponents on a rate ratio in [0.05, 2] these are absurd (0.05^9.55 ~ 4e-13), and the
    reported standard deviations (up to 400) match a vanishing effect; as 1/theta they are small exponents. The code bounds q_j in [-5, 5] hold the SI reading only."""
    lo, hi = semi.SemiForm(SPEC).bounds()
    si, jes = paper_to_code(convention="SI"), paper_to_code(convention="JES")
    assert np.all(si[[1, 2, 3, 5, 6, 7, 8, 9, 10]] >= lo[[1, 2, 3, 5, 6, 7, 8, 9, 10]]) and np.all(si[[1, 2, 3, 5, 6, 7, 8, 9, 10]] <= hi[[1, 2, 3, 5, 6, 7, 8, 9, 10]])
    assert np.all(si[[0, 4]] >= lo[[0, 4]]) and np.all(si[[0, 4]] <= hi[[0, 4]])
    assert jes[7] > hi[7]                                                   # q_Cch = 9.55 / 0.52 = 18 > 5


# ------------------------------------------------------------------------------------------------ recovery from the paper's equations
def _cells_from_paper(seed, sigma=0.0, convention="SI"):
    """synthetic stress design; retention = 1 - (calendar + cycle) of the paper's equations (calendar term for a cycling cell: ambient T, SOC_mid, elapsed days;
    the paper does not say how the two terms are combined for a cycling cell beyond the superposition Eq. S.1, so this is the code's documented choice)"""
    S = synth.make_synthetic("G0", n_cyc_cond=30, n_sto_cond=12, reps=1, seed=seed)
    rng = np.random.default_rng(seed + 100)
    out = []
    for c in S.cells:
        T, soc_mid, dod, cch, cdch = (float(v) for v in c.raw)
        loss = np.zeros(len(c.t))
        for i, (ti, ei) in enumerate(zip(c.t, c.efc)):
            if ti <= 0:
                continue
            loss[i] = paper_cal(T + 273.15, max(soc_mid, 0.02), ti)
            if c.kind == "cycling":
                loss[i] += paper_cyc(T + 273.15, soc_mid + dod / 2.0, cch, cdch, dod, ei, convention=convention)
        ret = 1.0 - loss
        if sigma:
            ret = ret + np.concatenate([[0.0], rng.normal(0.0, sigma, len(ret) - 1)])
        out.append(data.Cell(**{**c.__dict__, "ret": ret}))
    return out, S


def _fit(cells, seed=0):
    form = semi.SemiForm(SPEC)
    return form, *semi.fit_semi(form, cells, n_starts=12, seed=seed)


def test_recovery_of_the_papers_parameters_noise_free():
    cells, _ = _cells_from_paper(4)
    losses = np.concatenate([1.0 - c.ret for c in cells])
    assert 0.0 <= losses.min() and losses.max() < 0.6                      # plausible range of the generated data (sanity of the test conventions)
    form, hat, cost = _fit(cells)
    true = paper_to_code()
    assert cost < 1e-8, cost
    rel = np.abs(hat - true) / np.maximum(np.abs(true), 0.3)
    assert rel.max() < 0.02, (hat, true)
    # back to the paper's own parameters (effective theta): theta_cal_0 = p0 * 1e4 / r, 1/theta_cal_1 = p1 / r, theta_cal_2 = 1 / r; theta_cyc_5 = 1 / r_cyc
    th_cal0 = hat[1] * 1e4 / hat[3]
    th_cal2 = 1.0 / hat[3]
    th_cyc0 = hat[5] * 1e4 / hat[10]
    th_cyc5 = 1.0 / hat[10]
    assert th_cal0 == pytest.approx(TH_CAL[0], rel=0.02) and th_cal2 == pytest.approx(TH_CAL[2], rel=0.02)
    assert hat[2] / hat[3] == pytest.approx(1.0 / TH_CAL[1], rel=0.02)
    assert th_cyc0 == pytest.approx(TH_CYC[0], rel=0.02) and th_cyc5 == pytest.approx(TH_CYC[5], rel=0.02)
    assert hat[6] / hat[10] == pytest.approx(1.0 / TH_CYC[1], rel=0.02) and hat[9] / hat[10] == pytest.approx(1.0 / TH_CYC[4], rel=0.02)
    assert hat[7] / hat[10] == pytest.approx(1.0 / TH_CYC[2], rel=0.05) and hat[8] / hat[10] == pytest.approx(1.0 / TH_CYC[3], rel=0.05)
    # the activation energy the physical-validation code reports (emit.py) is theta_cal_0 * R
    assert hat[1] * 1e4 / hat[3] * 8.314462618 / 1000.0 == pytest.approx(TH_CAL[0] * 8.314462618 / 1000.0, rel=0.02)


def test_recovery_with_the_papers_measurement_noise():
    """sigma = 0.00274, the standard deviation of the real cycle experiments (JES 142 Section 4.2). Predictions must be within the noise; the temperature parameters near the truth."""
    cells, _ = _cells_from_paper(5, sigma=0.00274)
    form, hat, cost = _fit(cells)
    true = paper_to_code()
    err = []
    for c in cells:
        if c.n > 1:
            err.append(form.loss(hat, c.raw, c.t[1:], c.efc[1:]) - form.loss(true, c.raw, c.t[1:], c.efc[1:]))
    rmse = float(np.sqrt(np.mean(np.concatenate(err) ** 2)))
    assert rmse < 0.0025, rmse                                              # noise-free-truth error well below one measurement sigma
    th_cal0 = hat[1] * 1e4 / hat[3]
    assert th_cal0 == pytest.approx(TH_CAL[0], rel=0.15)


def test_paper_form_fit_is_a_superset_of_the_published_form():
    """the code has two free log-scales; the published model has none (scale fixed by EOLC and unpublished reference values). Fixing lc to the paper's value must reproduce
    the paper's loss exactly: the published form is nested in the code form (documented deviation M1)."""
    form = semi.SemiForm(SPEC)
    th = paper_to_code()
    raw = np.array([45.0, 0.5, 0.0, 0.0, 0.0])
    a = form.loss(th, raw, np.array([200.0]), np.array([0.0]))[0]
    th2 = th.copy()
    th2[0] += 0.3
    b = form.loss(th2, raw, np.array([200.0]), np.array([0.0]))[0]
    assert b == pytest.approx(a * math.exp(0.3), rel=1e-12)
    assert a == pytest.approx(paper_cal(318.15, 0.5, 200.0), rel=1e-9)      # default references (t_ref = 10000 d)
