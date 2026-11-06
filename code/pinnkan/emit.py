"""Run-record emitters for the figure scripts (formats: code/figures/README.md "Not yet written ..." table).

    window.csv            run writer: model-visible window check-ups of every scored cell
    stress_functions.json analysis: calendar E(SOC), a(SOC), storage rate, Arrhenius lines, cyclic partial dependences (A1 envelope over members, A4, A10)
    residual_map.npz      analysis: median |R| of the PINN residual over (T, SOC) and (C_ch, T) bins, with the training points
    superposition.csv     analysis: counterfactual calendar share per cycling cell (11a item 4; D013 definition y(a_cyc = 0) / y(full))
Stress functions, residual map and superposition exist for datasets with a calendar term and the Samsung stress layout (Samsung, synthetic). Members = the
fitted A1 models of this run (final-refit seeds; with several outer folds merge the member lists before calling). Nothing here reads a test label except
`superposition` (observed fade at the last check-up, scored cells only, called after scoring)."""
import numpy as np
import pandas as pd
import torch

from . import hard as hard_mod
from . import pinn as pinn_mod
from .law import batch_from_windows, drive_to_state
from .semi import SemiForm

R_GAS = 8.314
DELTA_ARR = 1.0 / 298.15 - 1.0 / 308.15          # x_arr = (1/298.15 - 1/T) / DELTA_ARR; Ea/R = E / DELTA_ARR
VARS = {"T": (0, np.linspace(5, 50, 46), 1.0), "soc_mid": (1, np.linspace(10, 90, 41), 0.01), "dod": (2, np.linspace(0, 80, 41), 0.01),
        "c_ch": (3, np.linspace(0, 1.2, 49), 1.0), "c_dch": (4, np.linspace(0, 2.2, 45), 1.0)}


def window_rows(prepared):
    rows = [(p.cell.cell_id, p.cell.cond, float(t), float(y)) for p in prepared for t, y in zip(p.win.t_win, p.win.y_win)]
    return pd.DataFrame(rows, columns=["cell_id", "cond", "t", "retention"])


def _band(arr):
    a = np.asarray(arr, float)
    return dict(mean=a.mean(0).tolist(), lo=a.min(0).tolist(), hi=a.max(0).tolist(), members=a.tolist())     # `members` is moved to the top-level key `members` of stress_functions.json (11a)


def supports_calendar_maps(spec):
    return bool(spec.has_calendar and spec.stress_names == ("T_C", "soc_mid", "dod", "c_ch", "c_dch"))


def _cal_members(models, spec, backbone):
    soc = np.arange(0, 101, 5.0)
    E_all, a_all = [], []
    rate_all, lr_all = [], []
    Ts, sel = [10, 23, 45], [5, 50, 80, 100]
    for m in models:
        law = m.law
        raw = np.zeros((len(soc), 5))
        raw[:, 0], raw[:, 1] = 25.0, soc / 100.0
        s = torch.tensor(spec.norm(raw), dtype=torch.float32)
        with torch.no_grad():
            ae = law.calendar_ae(s)
            E_all.append((ae[:, 1] / DELTA_ARR * R_GAS / 1000.0).numpy())
            a_cal = torch.exp(law.log_cal + ae[:, 0])
            a_all.append((spec.y_scale * drive_to_state(a_cal, backbone)).numpy())         # calendar loss after 500 d at 25 C, pp
            rates = []
            for T in Ts:
                r = np.zeros((len(soc), 5))
                r[:, 0], r[:, 1] = T, soc / 100.0
                rates.append((spec.y_scale * law.r_cal(torch.tensor(spec.norm(r), dtype=torch.float32))).numpy())     # initial rate, pp per 500 d
            rate_all.append(np.stack(rates))
            idx = [int(np.argmin(abs(soc - v))) for v in sel]
            lr_all.append(np.log(np.stack(rates)[:, idx]).T)                                 # [n_sel x nT]
    rate = np.stack(rate_all)                                                                # members x nT x nSOC
    lr = np.stack(lr_all)
    return soc, _band(E_all), _band(a_all), dict(T_C=Ts, soc=soc.tolist(), **_band(rate)), dict(soc=sel, T_C=Ts, ln_rate=_band(lr))


def _cyc_pd(law, spec, base_raw, k, xs, scale):
    out = []
    with torch.no_grad():
        for x in xs:
            r = base_raw.copy()
            r[:, k] = x * scale
            out.append(float(law.cyc(torch.tensor(spec.norm(r), dtype=torch.float32)).mean()))
    out = np.array(out)
    return out - out.mean()


def _a10_pd(arm, base_raw):
    f = arm.form
    th = arm.theta
    i = f.n_cal
    q0, qs, r = th[i + 1], th[i + 2:i + 2 + f.nx], th[i + 2 + f.nx]
    med = np.median(base_raw, axis=0)
    out = {}
    for name, (k, xs, scale) in VARS.items():
        x = xs * scale
        floor = 0.05 * float(xs.max() * scale)         # a power law diverges at 0: the plotted curve starts at 5 % of the range
        if name == "T":
            y = -q0 * 1e4 * (1.0 / (273.15 + x) - 1.0 / 298.15) / r
        elif name == "soc_mid":
            y = qs[0] / r * np.log(np.maximum((x + med[2] / 2.0) / f.refs[0], 1e-3))        # A10 acts on SOC_max = SOC_mid + DoD / 2 (dod at its median)
        elif name == "c_ch":
            y = qs[1] / r * np.log(np.maximum(np.maximum(x, floor) / f.refs[1], 1e-3))
        elif name == "c_dch":
            y = qs[2] / r * np.log(np.maximum(np.maximum(x, floor) / f.refs[2], 1e-3))
        else:
            y = qs[3] / r * np.log(np.maximum(np.maximum(x, floor) / f.refs[3], 1e-3))
        out[name] = y - y.mean()
    return out


def stress_functions(a1_arms, spec, train_cells, backbone, a4_arms=(), a10_arm=None):
    """a1_arms: fitted A1 PINNArm objects (members). Returns the dict of stress_functions.json. The per-member arrays (one row per fitted model) are written under the
    top-level key `members` for the physical-validation analyses of PREREG 11a; the figure-facing bands keep their keys (mean, lo, hi)."""
    models = [a.model for a in a1_arms]
    members = {}

    def split(band, name):
        members[name] = band.pop("members")
        return band
    soc, E, a, rate, arr = _cal_members(models, spec, backbone)
    cal = dict(soc=soc.tolist(), E_kJmol=split(E, "E_kJmol"), a_pp500=split(a, "a_pp500"))
    rate = split(rate, "storage_rate")
    arr["ln_rate"] = split(arr["ln_rate"], "arrhenius_ln_rate")
    if a10_arm is not None:
        cal["A10_E_kJmol"] = float(a10_arm.theta[1] * 1e4 / a10_arm.theta[3] * R_GAS / 1000.0)
    base = np.unique(np.stack([c.raw for c in train_cells if c.kind == "cycling"]), axis=0)
    cyc = {}
    a10 = _a10_pd(a10_arm, base) if a10_arm is not None else {}
    for name, (k, xs, scale) in VARS.items():
        mem = np.stack([_cyc_pd(m.law, spec, base, k, xs, scale) for m in models])
        e = dict(x=xs.tolist(), A1=split(_band(mem), f"cyclic.{name}"))
        if a4_arms:
            e["A4"] = dict(mean=np.mean([_cyc_pd(x.model.law, spec, base, k, xs, scale) for x in a4_arms], axis=0).tolist())
        if name in a10:
            e["A10"] = dict(mean=a10[name].tolist())
        cyc[name] = e
    return dict(n_members=len(models), member_definition="final-refit seeds of this run's outer fold (min/max envelope); merge folds for the paper",
                calendar=cal, storage_rate=rate, arrhenius=arr, cyclic=cyc, partial_dependence="mean over the training cycling conditions, centred; others at their values",
                a_pp500_definition="calendar loss after 500 d at 25 C (pp, backbone applied), no cycling", members=members)


def residual_map(a1_arms, spec, train_cells, n_t=6):
    T_edges, soc_edges, cch_edges = np.linspace(5, 50, 5), np.linspace(0, 100, 6), np.linspace(0, 1.2, 5)
    cyc_raw = np.stack([c.raw for c in train_cells if c.kind == "cycling"])
    med = np.median(cyc_raw, axis=0)
    off = np.array([1 / 6, 3 / 6, 5 / 6])

    def pts(edges_x, edges_y, fx, fy):
        P = []
        for iy in range(len(edges_y) - 1):
            row = []
            for ix in range(len(edges_x) - 1):
                xs = edges_x[ix] + off * (edges_x[ix + 1] - edges_x[ix])
                ys = edges_y[iy] + off * (edges_y[iy + 1] - edges_y[iy])
                row.append([fx(x, y) for x in xs for y in ys])
            P.append(row)
        return np.array(P)                                                                  # nY x nX x 9 x 5

    def raw(T=None, soc=None, cch=None):
        r = med.copy()
        if T is not None:
            r[0] = T
        if soc is not None:
            r[1] = soc
        if cch is not None:
            r[3] = cch
        return r

    P1 = pts(soc_edges, T_edges, lambda x, y: raw(T=y, soc=x / 100.0), None)                 # rows: T, cols: SOC
    P2 = pts(cch_edges, T_edges, lambda x, y: raw(T=y, cch=x), None)                         # rows: T, cols: C_ch

    def absR(m, P):
        shp = P.shape[:2]
        flat = P.reshape(-1, 5)
        s = torch.tensor(spec.norm(flat), dtype=torch.float32)
        nu = torch.tensor(spec.efc_rate(flat) * spec.t_scale / spec.efc_scale, dtype=torch.float32)
        with torch.no_grad():
            a_cal, a_cyc = m.law.r_cal(s), m.law.r_cyc(s)
        vals = []
        for tn in np.linspace(0.1, 1.0, n_t) * m.col_t_max:
            R = m.residual(torch.full((len(flat),), float(tn)), s, torch.zeros(len(flat), m.zdim), a_cal, a_cyc, nu)
            vals.append(R.detach().abs().numpy().reshape(shp + (9,)))
        return np.stack(vals)                                                               # n_t x nY x nX x 9

    models = [a.model for a in a1_arms]
    Z1 = np.concatenate([absR(m, P1) for m in models])
    Z2 = np.concatenate([absR(m, P2) for m in models])
    sto = np.stack([c.raw for c in train_cells if c.kind == "storage"]) if any(c.kind == "storage" for c in train_cells) else np.zeros((0, 5))
    t_soc = np.unique(np.round(np.concatenate([np.column_stack([cyc_raw[:, 0], 100 * cyc_raw[:, 1]]), np.column_stack([sto[:, 0], 100 * sto[:, 1]])]), 6), axis=0)
    t_cT = np.unique(np.round(np.column_stack([cyc_raw[:, 3], cyc_raw[:, 0]]), 6), axis=0)
    return dict(T_edges=T_edges, soc_edges=soc_edges, cch_edges=cch_edges, absR_T_SOC=np.median(Z1, axis=(0, 3)), absR_cch_T=np.median(Z2, axis=(0, 3)),
                train_T_SOC=t_soc, train_cch_T=t_cT)


def superposition(fitted, prepared, spec, backbone):
    """fitted: {'A1': PINNArm, 'A2': HardArm} (one model each, seed 0). share_cal = y(a_cyc = 0) / y(full) at the cell's last forecast check-up (D013);
    cal_exceeds_total = y(a_cyc = 0) > the observed y there (physically impossible split)."""
    prep = [p for p in prepared if p.cell.kind == "cycling"]
    wc = [p.win for p in prep]
    rows = []
    if not prep:
        return pd.DataFrame(rows, columns=["cell_id", "cond", "arm", "share_cal", "cal_exceeds_total"])
    for arm_id, arm in fitted.items():
        if arm_id == "A1":
            preds, (z, delta) = pinn_mod.predict_pinn(arm.model, spec, wc, float(arm.hp.get("lam_res", 1.0)), arm.seed)
        else:
            preds, delta = hard_mod.predict_hard(arm.model, spec, wc)
        bw = batch_from_windows(spec, wc)
        with torch.no_grad():
            a_cal, _ = arm.model.law.amplitudes(bw.s, bw.is_cyc, delta)
        for i, p in enumerate(prep):
            tn = float(p.win.t_fc[-1]) / spec.t_scale
            y_cal = float(drive_to_state(a_cal[i] * tn, backbone))
            y_full = spec.y_scale * (1.0 - float(preds[p.cell.cell_id][-1]))
            y_obs = spec.y_scale * (1.0 - float(p.fc_true[-1]))
            rows.append((p.cell.cell_id, p.cell.cond, arm_id, y_cal / max(y_full, 1e-9), bool(y_cal > y_obs)))
    return pd.DataFrame(rows, columns=["cell_id", "cond", "arm", "share_cal", "cal_exceeds_total"])


# ------------------------------------------------------------------------------------------------ inputs of the statistics-step gaps G4, G6 (STATS_GAPS_REPORT.md)
LHS_N, LHS_SEED = 500, 20261106


def lhs_points(n=LHS_N, d=5, seed=LHS_SEED):
    """the fixed Latin hypercube of the law-stability metric (PREREG_v4 11a item 6): n points in the normalised stress space [-1, 1)^d, a local RandomState (no global RNG is touched).
    Every run evaluates its extracted laws on these same points; the statistics step restricts them to the intersection of the five training hulls."""
    rs = np.random.RandomState(seed)
    u = np.empty((n, d))
    for j in range(d):
        u[:, j] = (rs.permutation(n) + rs.random_sample(n)) / n
    return 2.0 * u - 1.0


def _edges_record(stack, t_index=None, label=None):
    """final (post-refit) family and coefficients of every edge of a symbolic.SymbolicStack; the cyclic temperature input (layer 0, column t_index) carries the fixed label only (D022b N1(a))"""
    layers = []
    for li, layer in enumerate(stack.sym_layers):
        rows = []
        for row in layer.edges:
            r = []
            for i, e in enumerate(row):
                if t_index is not None and li == 0 and i == t_index:
                    r.append({"display": label})
                else:
                    r.append({"family": e.family, "theta": [] if e.theta is None else [float(x) for x in e.theta.detach().cpu().numpy()]})
            rows.append(r)
        layers.append({"layer": li, "edges": rows})
    return layers


def law_extras(arm_key, fold, seed, arm, spec, train_cells):
    """G4: one fold-by-seed extracted law (a fitted symbolic arm A15 / G15) -> closed form (final coefficients; temperature masked), coefficient count, training-side BIC, centred partial
    dependences of the non-temperature inputs on the VARS grid (the grid of stress_functions.json) and the log-rate on the fixed Latin hypercube. No temperature curve, form or sign is written."""
    from . import symbolic
    from .extraction_audit import load_thresholds
    law = arm.model.law
    label = load_thresholds()["wording"]["temperature_label"]
    cyc = _edges_record(law.cyc.net, spec.t_index, label)
    cal = _edges_record(law.cal, None, None) if getattr(law, "cal", None) is not None and hasattr(law.cal, "sym_layers") else None
    rep = {"cyclic": {"layers": cyc}}
    if cal is not None:
        rep["calendar"] = {"layers": cal}
    base = np.unique(np.stack([c.raw for c in train_cells if c.kind == "cycling"]), axis=0)
    pd_ = {name: _cyc_pd(law, spec, base, k, xs, scale).tolist() for name, (k, xs, scale) in VARS.items() if name != "T"}
    with torch.no_grad():
        lr = law.cyc(torch.tensor(lhs_points(), dtype=torch.float32)).detach().double().numpy().reshape(-1)
    return dict(arm=arm_key, fold=int(fold), seed=int(seed), h=(len(cyc[0]["edges"]) if len(cyc) > 1 else 1), n_coefs=int(arm.n_coefs), n_params=int(arm.n_params), train_bic=float(arm.train_bic),
                cyclic=cyc, calendar=cal, closed_form=symbolic.describe(rep, t_index=spec.t_index), pd=pd_, log_rate_on_lhs=lr.tolist())


def law_forms_header(spec, s_train):
    """run-level part of extracted_law_forms.json: the Latin hypercube, the partial-dependence grids and the training stress rows (normalised, identifiers of the design only) that
    define this fold's training hull"""
    return dict(lhs=dict(seed=LHS_SEED, n=LHS_N, space="normalised stress rows in [-1, 1)^5, columns T_C, soc_mid, dod, c_ch, c_dch", points=lhs_points().tolist()),
                pd_grid={name: xs.tolist() for name, (k, xs, scale) in VARS.items() if name != "T"}, train_hull_points=np.asarray(s_train, float).tolist())


def residual_cells(a1_arms, spec, prepared, n_t=6):
    """G6: |R| of every fitted A1 member at the stress vector of every scored (outer-test) cycling cell and at n_t normalised times (the times of residual_map). Each test cell belongs to
    exactly one outer fold, so the merged map of the statistics step pools these raw values (no median of medians). -> dict of arrays or None when there is no cycling test cell"""
    cells = [p.cell for p in prepared if p.cell.kind == "cycling"]
    if not cells:
        return None
    raw = np.stack([c.raw for c in cells]).astype(float)
    s = torch.tensor(spec.norm(raw), dtype=torch.float32)
    nu = torch.tensor(spec.efc_rate(raw) * spec.t_scale / spec.efc_scale, dtype=torch.float32)
    per = []
    for a in a1_arms:
        m = a.model
        with torch.no_grad():
            a_cal, a_cyc = m.law.r_cal(s), m.law.r_cyc(s)
        rows = []
        for tn in np.linspace(0.1, 1.0, n_t) * m.col_t_max:
            R = m.residual(torch.full((len(raw),), float(tn)), s, torch.zeros(len(raw), m.zdim), a_cal, a_cyc, nu)
            rows.append(R.detach().abs().numpy().reshape(-1))
        per.append(np.stack(rows))                                   # n_t x n_cells
    A = np.stack(per).transpose(2, 0, 1)                             # n_cells x members x n_t
    return dict(cell_id=np.array([c.cell_id for c in cells]), cond=np.array([c.cond for c in cells]), T=raw[:, 0], soc_mid=100.0 * raw[:, 1], c_ch=raw[:, 3], absR=A)


def storage_hull(train_cells):
    """G3 (PC-2): the (T, SOC %) points of the training storage cells (the design hull of the storage axis); identifiers of the design only"""
    pts = sorted({(float(c.raw[0]), round(100.0 * float(c.raw[1]), 6)) for c in train_cells if c.kind == "storage"})
    return dict(points_T_SOCpct=[list(p) for p in pts], definition="(temperature in C, SOC in %) of the training storage cells of this outer fold")
