"""Generate SYNTHETIC demo run directories so that every figure and table script can be exercised before the
confirmatory runs exist.  Nothing here is a result: all trajectories, scores and surfaces are drawn from invented
laws.  The only real inputs are the design identifiers (condition keys, cell ids, labs, stages) from
`runs/prereg/samsung_splits_v2.json` and `data/raw/samsung50e_meta/experiments_meta.csv` (metadata only).

Output: runs/figdemo_SYNTHETIC/ (every sub-directory carries a `SYNTHETIC` marker file).

Files follow the run-writer format of code/README.md (config.json, metrics.json, condition_scores.json,
predictions.csv, margins.json, timings.json) plus the *additional* artefacts that the figure scripts need and that the
run writer / analysis step must produce (see code/figures/README.md): window.csv, stress_functions.json,
residual_map.npz, superposition.csv, analysis/contrasts_<test>.json, analysis/reference.json, analysis/controls.json,
synthetic_H7/summary.json + surfaces_<gen>.npz, design/fade_curves.csv.

Run:  .venv\\Scripts\\python.exe -P code\\figures\\make_demo_runs.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps  # noqa: E402

ROOT = ps.ROOT
OUT = ROOT / "runs" / "figdemo_SYNTHETIC"
META = ROOT / "data" / "raw" / "samsung50e_meta" / "experiments_meta.csv"
SPLITS = ROOT / "runs" / "prereg" / "samsung_splits_v2.json"
RNG = np.random.default_rng(20261105)
SEEDS = [0, 1, 2, 3, 4]


def dump(obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1)


def mark(d: Path, note="SYNTHETIC DEMO DATA - invented laws, not results of any experiment or model fit"):
    d.mkdir(parents=True, exist_ok=True)
    (d / "SYNTHETIC").write_text(note + "\n")


# ------------------------------------------------------------------------------------------ design (identifiers only)
def load_design():
    meta = pd.read_csv(META)
    meta.columns = [c.strip() for c in meta.columns]
    sp = ps.load_json(SPLITS)
    cyc_keys = sorted({k for f in sp["B"]["folds"].values() for k in f["test_conditions"]})
    sto_keys = sorted({k for f in sp["S2"]["folds"].values() for k in f["test_conditions"]})
    c35 = list(sp["C"]["folds"]["0"]["test_conditions"])
    cells = {}
    z, k = meta[meta.type == "z"], meta[meta.type == "k"]
    for key in cyc_keys:
        c = ps.parse_cond(key)
        m = z[(np.isclose(z.amb_temp_tp, c["T"])) & (np.isclose(z.soc_max_tp * 100, c["soc_max"]))
              & (np.isclose(z.dod_tp * 100, c["dod"])) & (np.isclose(z.c_ch_tp, c["c_ch"], atol=0.06))
              & (np.isclose(z.c_dch_tp, c["c_dch"], atol=0.06))]
        cells[key] = [dict(cell_id=f"{r.serial}_s{r.stage}", lab=r.lab, stage=int(r.stage), cell=int(r.cell)) for r in m.itertuples()]
    for key in sto_keys:
        c = ps.parse_cond(key)
        m = k[(np.isclose(k.amb_temp_tp, c["T"])) & (np.isclose(k.soc_max_tp * 100, c["soc"]))]
        cells[key] = [dict(cell_id=f"{r.serial}_s{r.stage}", lab=r.lab, stage=int(r.stage), cell=int(r.cell)) for r in m.itertuples()]
    return dict(cyc=cyc_keys, sto=sto_keys, c35=c35, cells=cells, folds_B=sp["B"]["folds"])


# ------------------------------------------------------------------------------------------ invented ageing law
def arr_factor(T, Ea=45000.0, Tref=23.0):
    return np.exp(-Ea / 8.314 * (1 / (T + 273.15) - 1 / (Tref + 273.15)))


def fade_pp(cond: dict, t):
    """Invented fade (percentage points) of a condition at t days: calendar + cycling, both sub-linear."""
    t = np.asarray(t, float)
    if cond["kind"] == "sto":
        s = cond["soc"] / 100
        return 2.4 * arr_factor(cond["T"]) * (0.5 + 1.4 * s ** 2) * (t / 400) ** 0.55
    s, dod = cond["soc_mid"] / 100, cond["dod"] / 100
    cal = 2.0 * arr_factor(cond["T"]) * (0.5 + 1.4 * s ** 2) * (t / 300) ** 0.6
    hours = dod / cond["c_ch"] + dod / cond["c_dch"] + 1.0
    efc = t * 24.0 / hours * dod
    cyc = 5.0 * (1 + 2.0 * max(cond["c_ch"] - 0.7, 0)) * (1 + 0.5 * (arr_factor(cond["T"], 20000) - 1)) \
        * (1 + 0.8 * (dod - 0.3)) * (efc / 1000) ** 0.7
    return cal + cyc


def cell_curves(cond_key, cells, t, rng):
    """Observed retention (fraction) per cell: condition law * cell factor + noise."""
    c = ps.parse_cond(cond_key)
    out = {}
    for ce in cells:
        u = rng.normal(0, 0.07)
        f = fade_pp(c, t) * (1 + u)
        out[ce["cell_id"]] = 1 - (f + rng.normal(0, 0.12, len(t))) / 100
    return out


# ------------------------------------------------------------------------------------------ arms: scale of forecast error (pp)
SCALE_B = dict(A1=1.00, A2=1.10, A3=1.45, A4=1.25, A5=1.20, A7=1.35, A9=2.20, A10=1.75, A11=1.22, A12=1.30, A13=1.18)
SCALE_C = dict(A1=1.30, A9=2.60, A10=2.00, A11=1.80, A12=1.95)
SCALE_S2 = dict(A1=0.90, A3=1.25, A9=1.80, A10=1.30, A14=0.95)
NPARAM = dict(A1=2621, A2=188, A3=410, A4=2623, A5=3312, A7=2790, A9=50945, A10=11, A11=14, A12=1850, A13=2621, A14=2300,
              R1=0, R2=2, A8=1378)
FITSEC = dict(A1=7.0, A2=1.4, A3=4.1, A4=5.2, A5=6.0, A7=5.8, A9=9.5, A10=2.2, A11=3.0, A12=0.6, A13=6.1, A14=3.0, R1=0.0, R2=0.0)


def simulate(conds, cells, arms, scales, n_win, t_grid, rng, rho=0.8, shift=1.0, label=""):
    """Returns predictions DataFrame, window DataFrame, cond->score per arm (seed-averaged)."""
    prow, wrow = [], []
    diff = {c: float(np.exp(rng.normal(0, 0.40))) for c in conds}
    z = {c: rng.normal() for c in conds}
    e = {(a, c): rng.normal() for a in arms for c in conds}
    cell_err = {}
    for c in conds:
        sub = cells[c]
        obs = cell_curves(c, sub, t_grid, rng)
        for ce in sub:
            cid = ce["cell_id"]
            y = obs[cid]
            ramp = np.clip((t_grid - t_grid[n_win - 1]) / (t_grid[-1] - t_grid[n_win - 1]), 0, None)
            ramp = np.where(np.arange(len(t_grid)) < n_win, 0.0, 0.2 + 0.8 * ramp)
            cc = ps.parse_cond(c)
            truth = 1 - fade_pp(cc, t_grid) / 100
            for i in range(n_win):
                wrow.append((cid, c, float(t_grid[i]), float(y[i])))
            for a in arms:
                if a in ("R1", "R2"):
                    for sd in SEEDS:
                        if a == "R1":
                            pr = np.full(len(t_grid), y[n_win - 1])
                        else:
                            k, b = np.polyfit(t_grid[:n_win], y[:n_win], 1)
                            pr = b + k * t_grid
                        for i in range(n_win, len(t_grid)):
                            prow.append(("outer_test", a, sd, cid, c, float(t_grid[i]), float(pr[i]), float(y[i])))
                    continue
                s = scales[a] * shift
                bias = s * diff[c] * (np.sqrt(rho) * z[c] + np.sqrt(1 - rho) * e[(a, c)])
                cell_dev = rng.normal(0, 0.25 * s)
                for sd in SEEDS:
                    wob = rng.normal(0, 0.18 * s)
                    pr = truth + ((bias + cell_dev + wob) * ramp) / 100
                    for i in range(n_win, len(t_grid)):
                        prow.append(("outer_test", a, sd, cid, c, float(t_grid[i]), float(pr[i]), float(y[i])))
    pred = pd.DataFrame(prow, columns=["phase", "arm", "seed", "cell_id", "cond", "t", "pred_retention", "true_retention"])
    win = pd.DataFrame(wrow, columns=["cell_id", "cond", "t", "retention"]).drop_duplicates(["cell_id", "t"])
    return pred, win


def scores_from_pred(pred):
    pred = pred.assign(se=(100 * (pred.pred_retention - pred.true_retention)) ** 2)
    cell = pred.groupby(["arm", "seed", "cond", "cell_id"]).se.mean().pipe(np.sqrt).rename("rmse").reset_index()
    cond = cell.groupby(["arm", "seed", "cond"]).rmse.mean().reset_index()
    avg = cond.groupby(["arm", "cond"]).rmse.mean()
    by_seed = cond.groupby(["arm", "seed"]).rmse.mean()
    scores = {a: {c: float(v) for c, v in avg[a].items()} for a in avg.index.get_level_values(0).unique()}
    seed_sd = {a: float(by_seed[a].std(ddof=1)) for a in scores}
    mae = pred.assign(ae=(100 * (pred.pred_retention - pred.true_retention)).abs()).groupby("arm").ae.mean().to_dict()
    return scores, seed_sd, mae


def write_run(d: Path, test, pred, win, scores, seed_sd, mae, dataset="samsung", extra_cfg=None):
    mark(d)
    cfg = dict(run_id=d.name, dataset=dataset, test=test, synthetic=True, mode="confirmatory",
               note="SYNTHETIC DEMO - invented data", seeds=SEEDS)
    cfg.update(extra_cfg or {})
    dump(cfg, d / "config.json")
    ot = {}
    for a, sc in scores.items():
        ot[a] = dict(primary_pp=float(np.mean(list(sc.values()))), seed_sd_of_mean=seed_sd[a], n_conditions=len(sc),
                     mae_pp_mean=float(mae.get(a, np.nan)), n_nonfinite=0, n_params=NPARAM.get(a, 0))
    inner = {a: ot[a]["primary_pp"] * 1.06 for a in ot}
    dump(dict(blinded=False, mode="confirmatory", inner_cv_pp=inner, backbone="self_limiting", outer_test=ot), d / "metrics.json")
    dump(scores, d / "condition_scores.json")
    tim = {a: dict(tuning_seconds=FITSEC.get(a, 1) * 60, median_fit_seconds=FITSEC.get(a, 1) * (1 + 0.1 * RNG.random()),
                   n_trials=20, n_failed=0) for a in scores}
    dump(tim, d / "timings.json")
    mg = {}
    for a in scores:
        E = inner[a]
        mg[f"E_{a}"] = dict(E_pp=E, delta_S_pp=0.02 * E, delta_N_pp=0.10 * E, log_margin_S=float(np.log(1.02)),
                            log_margin_N=float(-np.log(1.10)))
    dump(dict(contrasts=mg), d / "margins.json")
    if pred is not None:
        pred.to_csv(d / "predictions.csv", index=False, float_format="%.5f")
    if win is not None:
        win.to_csv(d / "window.csv", index=False)


def score_only_run(d: Path, test, conds, arms, scales, rng, dataset, rho=0.8):
    diff = {c: float(np.exp(rng.normal(0, 0.45))) for c in conds}
    z = {c: rng.normal() for c in conds}
    scores = {}
    for a in arms:
        scores[a] = {c: float(max(0.05, scales[a] * diff[c] * np.exp(0.18 * (np.sqrt(rho) * z[c] + np.sqrt(1 - rho) * rng.normal())))) for c in conds}
    sd = {a: float(0.04 * np.mean(list(scores[a].values()))) for a in scores}
    write_run(d, test, None, None, scores, sd, {a: 0.85 * np.mean(list(scores[a].values())) for a in scores}, dataset=dataset)
    return scores


# ------------------------------------------------------------------------------------------ analysis artefacts
def sign_tier(L, m, level):
    """Exact one-sided sign test of median(L) > m at `level`; returns (p, passed)."""
    L = np.asarray(L)
    npos = int((L > m).sum())
    p = float(stats.binom.sf(npos - 1, len(L), 0.5))
    return p, p <= level


def make_contrasts(scores, test, arms_pool=("A3", "A4", "A5", "A7"), h6="A10", h1c=("A11", "A12"), alpha=0.025):
    conds = sorted(scores["A1"])
    cs = lambda a: np.array([scores[a][c] for c in conds])
    out = {}
    s1 = cs("A1")

    def entry(label, comp, hyp, Lvec, sc_comp):
        L = np.log(sc_comp / s1)
        lo, hi, rk = ps.median_order_ci(L)
        d = sc_comp - s1
        blo, bhi = ps.bootstrap_mean_ci(d, B=3000)
        return dict(label=label, comp=comp, hyp=hyp, n=len(L), L_by_cond={c: float(v) for c, v in zip(conds, L)},
                    median_L=float(np.median(L)), median_ci95=[lo, hi], mean_L=float(L.mean()), n_wins=int((L > 0).sum()),
                    mean_pp=float(d.mean()), mean_pp_ci95=[blo, bhi], rel_reduction_median=float(1 - np.exp(-np.median(L))))

    fam = {}
    if test == "B":
        pool_means = {a: np.mean(cs(a)) for a in arms_pool if a in scores}
        best_pool = min(pool_means, key=pool_means.get)
        fam["H1a"] = entry("A9 vs A1", "A9", "H1a", None, cs("A9"))
        fam["H1b"] = entry(f"best pool arm ({best_pool}) vs A1", best_pool, "H1b", None, cs(best_pool))
        fam["H6"] = entry("A10 vs A1", "A10", "H6", None, cs("A10"))
        # Holm over N-tier p-values
        pN = {k: sign_tier(np.array(list(v["L_by_cond"].values())), -np.log(1.10), 1)[0] for k, v in fam.items()}
        order = sorted(pN, key=pN.get)
        levels = [alpha / 3, alpha / 2, alpha]
        for lev, k in zip(levels, order):
            L = np.array(list(fam[k]["L_by_cond"].values()))
            pS, okS = sign_tier(L, np.log(1.02), lev)
            pN_, okN = sign_tier(L, -np.log(1.10), lev)
            fam[k].update(tier="S" if okS else ("N" if okN else "-"), holm_level=lev, p_S=pS, p_N=pN_, status="primary family")
        allS = all(v["tier"] == "S" for v in fam.values())
        for a in h1c:
            if a in scores:
                e = entry(f"{a} vs A1", a, "H1c", None, cs(a))
                if allS:
                    L = np.array(list(e["L_by_cond"].values()))
                    pS, okS = sign_tier(L, np.log(1.02), alpha)
                    pN_, okN = sign_tier(L, -np.log(1.10), alpha)
                    e.update(tier="S" if okS else ("N" if okN else "-"), status="key secondary, gate open")
                else:
                    e.update(tier=None, status="secondary, not tested (gate closed)")
                fam[f"H1c_{a}"] = e
        e = entry("A2 vs A1 (hard ODE, decision contrast)", "A2", "H2", None, cs("A2"))
        e.update(tier=None, status="decision contrast")
        fam["H2"] = e
        e = entry("A13 vs A1 (cycling cells only)", "A13", "X1", None, cs("A13"))
        e.update(tier=None, status="descriptive")
        fam["X1"] = e
        for a in arms_pool:
            if a in scores:
                e = entry(f"{a} vs A1", a, "H1b-pool", None, cs(a))
                e.update(tier=None, status="pool arm, descriptive")
                fam[f"pool_{a}"] = e
        for a in ("R1", "R2"):
            if a in scores:
                e = entry(f"{a} vs A1", a, "ref", None, cs(a))
                e.update(tier=None, status="reference")
                fam[f"ref_{a}"] = e
    else:
        for a in scores:
            if a == "A1":
                continue
            e = entry(f"{a} vs A1", a, test, None, cs(a))
            L = np.array(list(e["L_by_cond"].values()))
            _, okS = sign_tier(L, np.log(1.02), alpha / 2)
            _, okN = sign_tier(L, -np.log(1.10), alpha / 2)
            e.update(tier="S" if okS else ("N" if okN else "-"), holm_level=alpha / 2, status="secondary")
            fam[f"vs_{a}"] = e
    return dict(test=test, rule="exact one-sided sign test on L-m (TYPE1_SIGNFLIP.md); estimand: median over conditions",
                alpha=alpha, margins=dict(S=float(np.log(1.02)), N=float(-np.log(1.10))), n=len(conds), contrasts=fam,
                synthetic=True)


# ------------------------------------------------------------------------------------------ model-derived artefacts
def stress_functions(rng):
    soc = np.arange(0, 101, 5.0)
    nm = 25
    s = soc / 100
    E0 = 38 + 14 * s ** 1.5 + 3 * np.sin(3 * s)
    lna0 = 0.9 + 1.4 * s ** 2 - 0.3 * s
    Em = E0 + rng.normal(0, 1, (nm, 1)) * 1.2 + np.cumsum(rng.normal(0, 0.35, (nm, len(soc))), 1) * (0.5 + 0.8 * s)
    lam = lna0 + rng.normal(0, 1, (nm, 1)) * 0.06 + np.cumsum(rng.normal(0, 0.03, (nm, len(soc))), 1)

    def band(m):
        return dict(mean=m.mean(0).tolist(), lo=m.min(0).tolist(), hi=m.max(0).tolist())

    aM = np.exp(lam)
    Ts = [10, 23, 45]
    rate_m = np.stack([aM * np.exp(-Em * 1000 / 8.314 * (1 / (T + 273.15) - 1 / 296.15)) for T in Ts], 1)  # nm x nT x nsoc
    rate = dict(T_C=Ts, soc=soc.tolist(), mean=rate_m.mean(0).tolist(), lo=rate_m.min(0).tolist(), hi=rate_m.max(0).tolist())
    soc_sel = [5, 50, 80, 100]
    idx = [int(np.argmin(abs(soc - v))) for v in soc_sel]
    lr = np.log(rate_m[:, :, idx])  # nm x nT x nsel
    arr = dict(soc=soc_sel, T_C=Ts, ln_rate=dict(mean=lr.mean(0).T.tolist(), lo=lr.min(0).T.tolist(), hi=lr.max(0).T.tolist()))
    cal = dict(soc=soc.tolist(), E_kJmol=band(Em), a_pp500=band(aM), A10_E_kJmol=float(E0.mean() + 3.0))
    # cyclic partial dependences (ln r_cyc, centred)
    vars_ = {
        "T": (np.linspace(5, 50, 46), lambda x: 0.045 * (x - 28) + 0.0006 * (x - 28) ** 2, lambda x: 0.05 * (x - 28), "T_C"),
        "soc_mid": (np.linspace(10, 90, 41), lambda x: 0.0008 * (x - 55) ** 2 - 0.1, lambda x: 0.004 * (x - 55), "soc_mid"),
        "dod": (np.linspace(0, 80, 41), lambda x: 0.035 * x - 0.00022 * x ** 2 - 1.0, lambda x: 0.016 * (x - 40), "dod"),
        "c_ch": (np.linspace(0, 1.2, 49), lambda x: 0.2 * x + 1.4 * np.maximum(x - 0.7, 0) ** 1.2 - 0.3, lambda x: 0.55 * (x - 0.6), "c_ch"),
        "c_dch": (np.linspace(0, 2.2, 45), lambda x: 0.07 * np.sin(2 * x) + 0.05 * x - 0.06, lambda x: 0.08 * (x - 1.1), "c_dch"),
    }
    cyc = {}
    for k, (x, f, g, lab) in vars_.items():
        base = f(x)
        mem = base + rng.normal(0, 1, (nm, 1)) * 0.05 + np.cumsum(rng.normal(0, 0.012, (nm, len(x))), 1)
        mem -= mem.mean(1, keepdims=True)
        gam = base + 0.25 * np.sin(5 * x / x.max()) * 0.2
        gam -= gam.mean()
        a10 = g(x) - g(x).mean()
        cyc[k] = dict(x=x.tolist(), A1=band(mem), A4=dict(mean=gam.tolist()), A10=dict(mean=a10.tolist()))
    return dict(n_members=nm, member_definition="outer folds x final-refit seeds (min/max envelope)", calendar=cal,
                storage_rate=rate, arrhenius=arr, cyclic=cyc, synthetic=True)


def residual_map(design, rng):
    Te = np.array([5.0, 17.0, 29.0, 40.0, 50.0])
    Se = np.array([0, 20, 40, 60, 80, 100.0])
    Ce = np.array([0, 0.3, 0.6, 0.9, 1.2])
    Tc, Sc, Cc = (Te[1:] + Te[:-1]) / 2, (Se[1:] + Se[:-1]) / 2, (Ce[1:] + Ce[:-1]) / 2
    R1 = 0.04 + 0.05 * np.abs(Tc[:, None] - 30) / 20 * (0.5 + Sc[None, :] / 100) + rng.normal(0, 0.006, (len(Tc), len(Sc)))
    R2 = 0.05 + 0.08 * Cc[None, :] * (0.6 + np.abs(Tc[:, None] - 28) / 22) + rng.normal(0, 0.006, (len(Tc), len(Cc)))
    pts_ts, pts_ct = [], []
    for k in design["sto"]:
        c = ps.parse_cond(k)
        pts_ts.append((c["T"], c["soc"]))
    for k in design["cyc"]:
        c = ps.parse_cond(k)
        pts_ts.append((c["T"], c["soc_mid"]))
        pts_ct.append((c["c_ch"], c["T"]))
    return dict(T_edges=Te, soc_edges=Se, cch_edges=Ce, absR_T_SOC=np.abs(R1), absR_cch_T=np.abs(R2).T,
                train_T_SOC=np.array(pts_ts), train_cch_T=np.array(pts_ct))


def superposition(design, rng):
    rows = []
    for k in design["cyc"]:
        c = ps.parse_cond(k)
        base = 0.20 + 0.45 * (arr_factor(c["T"]) / arr_factor(45)) * (1 - 0.3 * c["c_ch"] / 1.2)
        for ce in design["cells"][k]:
            for arm, off in (("A1", 0.0), ("A2", 0.06)):
                sh = float(np.clip(base + off + rng.normal(0, 0.05), 0.03, 1.15))
                rows.append((ce["cell_id"], k, arm, sh, sh > 1.0))
    return pd.DataFrame(rows, columns=["cell_id", "cond", "arm", "share_cal", "cal_exceeds_total"])


def fade_curves(design, meta):
    rows = []
    rng = np.random.default_rng(7)
    for r in meta.itertuples():
        if r.type == "k":
            if r.cell > 3:
                continue
            c = dict(kind="sto", T=float(r.amb_temp_tp), soc=100 * float(r.soc_max_tp))
            t = np.arange(1, 10) * 56.0
        else:
            c = dict(kind="cyc", T=float(r.amb_temp_tp), soc_mid=100 * (r.soc_max_tp - r.dod_tp / 2), dod=100 * r.dod_tp,
                     c_ch=float(r.c_ch_tp), c_dch=float(r.c_dch_tp))
            t = np.arange(1, 11) * 28.0
        u = rng.normal(0, 0.07) + (0.05 if r.stage == 2 else 0.0) + {"INT": 0.04, "HM": -0.02, "SIE": 0.0}[r.lab]
        y = 1 - (fade_pp(c, t) * (1 + u) + rng.normal(0, 0.12, len(t))) / 100
        for ti, yi in zip(t, y):
            rows.append((f"{r.serial}_s{r.stage}", r.lab, r.type, int(r.stage), float(r.amb_temp_tp), float(r.soc_max_tp),
                         float(r.dod_tp), float(r.c_ch_tp), float(r.c_dch_tp), float(ti), float(yi)))
    return pd.DataFrame(rows, columns=["cell_id", "lab", "type", "stage", "T_C", "SOC_max", "DoD", "C_ch", "C_dch",
                                       "elapsed_days", "retention"])


def synthetic_h7(rng, n_draws=20):
    d = OUT / "synthetic_H7"
    mark(d)
    gens = dict(G0=dict(A1=0.075, A2=0.075, A4=0.085, A8=0.125, floor=0.03),
                G1=dict(A1=0.095, A2=0.115, A4=0.135, A8=0.175, floor=0.05),
                G2=dict(A1=0.115, A2=0.130, A4=0.215, A8=0.230, floor=0.19))
    lhs = rng.random((500, 3))
    summary = []
    for g, par in gens.items():
        ft = np.sin(2.4 * lhs[:, 0]) + 0.9 * lhs[:, 1] ** 2 + (1.4 * np.maximum(lhs[:, 2] - 0.55, 0) * (0.3 + lhs[:, 0])
                                                                if g != "G0" else 0.5 * lhs[:, 2])
        ft = ft - ft.mean()
        rngt = ft.max() - ft.min()
        F = {k: np.zeros((n_draws, 500)) for k in ("true", "A1", "A2", "A4", "A8")}
        for i in range(n_draws):
            scale_i = np.exp(rng.normal(0, 0.12))
            F["true"][i] = ft * (1 + 0.1 * rng.normal())
            nr = {}
            for a in ("A1", "A2", "A4", "A8"):
                target = par[a] * scale_i * np.exp(rng.normal(0, 0.22))
                err = rng.normal(0, 1, 500)
                err = np.convolve(err, np.ones(25) / 25, "same")  # smooth
                err = err - err.mean()
                err *= target * (F["true"][i].max() - F["true"][i].min()) / err.std()
                F[a][i] = F["true"][i] + err
                nr[a] = float(np.sqrt(np.mean((F[a][i] - F["true"][i]) ** 2)) / (F["true"][i].max() - F["true"][i].min()))
            fr = {a: float(1.0 * (nr[a] / 0.1) ** 0.8 * np.exp(rng.normal(0, 0.1))) for a in nr}
            summary.append(dict(gen=g, draw=i, additive_floor=float(par["floor"] * np.exp(rng.normal(0, 0.15))), nrmse=nr,
                                forecast_pp=fr))
        np.savez(d / f"surfaces_{g}.npz", lhs=lhs, **{f"f_{k}": v for k, v in F.items()})
    dump(dict(synthetic=True, thresholds=dict(pass_=0.15, fail=0.30), n_draws=n_draws, arms=["A1", "A2", "A4", "A8"],
              draws=summary), d / "summary.json")


# ------------------------------------------------------------------------------------------ main
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mark(OUT)
    (OUT / "README_SYNTHETIC.md").write_text(
        "# SYNTHETIC DEMO RUNS - NOT RESULTS\n\nEvery number in this directory is drawn from an invented ageing law by "
        "`code/figures/make_demo_runs.py`.  Design identifiers (condition keys, cell ids, labs, stages) come from the "
        "dataset metadata and the preregistered split file; no Samsung, ISU or SNL retention value, model fit or test "
        "score is used.  Figures built from this directory carry the watermark 'SYNTHETIC DEMO - NOT RESULTS' and the "
        "file-name suffix `_SYNTHETIC`.\n")
    meta = pd.read_csv(META)
    meta.columns = [c.strip() for c in meta.columns]
    D = load_design()
    rng = RNG

    # Test B (40 cycling conditions) -------------------------------------------------------------
    tB = np.arange(1, 11) * 28.0
    armsB = list(SCALE_B) + ["R1", "R2"]
    cellsB = {k: D["cells"][k] for k in D["cyc"]}
    pred, win = simulate(D["cyc"], cellsB, armsB, SCALE_B, 4, tB, rng)
    scores, sd, mae = scores_from_pred(pred)
    write_run(OUT / "test_B", "B", pred, win, scores, sd, mae, extra_cfg=dict(window=dict(k_cycling=4)))
    sf = stress_functions(rng)
    dump(sf, OUT / "test_B" / "stress_functions.json")
    np.savez(OUT / "test_B" / "residual_map.npz", **residual_map(D, rng))
    superposition(D, rng).to_csv(OUT / "test_B" / "superposition.csv", index=False)
    # Test C (35 C, INT) -----------------------------------------------------------------------
    armsC = list(SCALE_C) + ["R1", "R2"]
    cellsC = {k: D["cells"][k] for k in D["c35"]}
    predC, winC = simulate(D["c35"], cellsC, armsC, SCALE_C, 4, tB, rng, rho=0.7)
    sC, sdC, maeC = scores_from_pred(predC)
    write_run(OUT / "test_C", "C", predC, winC, sC, sdC, maeC, extra_cfg=dict(window=dict(k_cycling=4)))
    # S2 storage ------------------------------------------------------------------------------
    tS = np.arange(1, 9) * 56.0
    armsS = list(SCALE_S2) + ["R1", "R2"]
    cellsS = {k: [c for c in D["cells"][k] if c["cell"] <= 3] for k in D["sto"]}
    predS, winS = simulate(D["sto"], cellsS, armsS, SCALE_S2, 2, tS, rng)
    sS, sdS, maeS = scores_from_pred(predS)
    write_run(OUT / "test_S2", "S2", predS, winS, sS, sdS, maeS, extra_cfg=dict(window=dict(k_storage=2)))
    # ISU / SNL score-only runs ----------------------------------------------------------------
    armsI = ["A1", "A2", "A4", "A5", "A7", "A9", "A10", "A11", "A12", "R1", "R2"]
    scI = dict(A1=1.0, A2=1.12, A4=1.22, A5=1.18, A7=1.32, A9=1.9, A10=1.55, A11=1.10, A12=1.20, R1=4.5, R2=3.4)
    sc_isu = score_only_run(OUT / "isu_B", "B", [f"isu_{i:02d}" for i in range(63)], armsI, scI, rng, "isu")
    scN = dict(A1=1.0, A2=1.08, A4=1.15, A5=1.12, A7=1.25, A9=1.6, A10=1.35, A11=1.18, A12=1.22, R1=4.0, R2=3.0)
    sc_snl = score_only_run(OUT / "snl_B", "B", [f"snl_{i:02d}" for i in range(23)], armsI, scN, rng, "snl")
    # analysis --------------------------------------------------------------------------------
    an = OUT / "analysis"
    mark(an)
    dump(make_contrasts(scores, "B"), an / "contrasts_B.json")
    dump(make_contrasts(sC, "C"), an / "contrasts_C.json")
    dump(make_contrasts(sS, "S2"), an / "contrasts_S2.json")
    dump(make_contrasts(sc_isu, "ISU"), an / "contrasts_ISU.json")
    dump(make_contrasts(sc_snl, "SNL"), an / "contrasts_SNL.json")
    ref = {}
    for tag, sc in (("B", scores), ("C", sC), ("S2", sS), ("ISU", sc_isu), ("SNL", sc_snl)):
        m = float(np.mean(list(sc["A1"].values())))
        ref[tag] = dict(R_LOO=m * 0.72 * (1 + 0.05 * rng.normal()), R_WARP=m * 0.80 * (1 + 0.05 * rng.normal()))
    dump(dict(definition="training-side replicate spread (descriptive, never a margin)", values=ref), an / "reference.json")
    # controls
    Lneg = np.log(np.array([scores["A9"][c] for c in sorted(scores["A9"])]) / np.array([scores["A1"][c] for c in sorted(scores["A1"])]))
    dump(dict(
        negative=dict(permutation="stress vectors permuted among conditions, A1, A9, R2 re-run", A9_minus_A1_mean_L=0.004,
                      p_two_sided=0.62, passed=True, A1_vs_R2_median_L=-0.02, A1_not_beating_R2=True),
        positive=dict(P1_G0_nrmse_leq_0p15=True, P2_monotone_in_T=True, P3_A1_beats_R1_median_L=float(np.median(
            np.log(np.array([scores["R1"][c] for c in sorted(scores["R1"])]) / np.array([scores["A1"][c] for c in sorted(scores["A1"])]))))),
        synthetic=True), an / "controls.json")
    # design
    d = OUT / "design"
    mark(d)
    fade_curves(D, meta).to_csv(d / "fade_curves.csv", index=False)
    synthetic_h7(rng)
    print("demo runs written to", OUT)


if __name__ == "__main__":
    main()
