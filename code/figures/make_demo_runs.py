"""Generate SYNTHETIC demo run directories in the Design R2 layout, so that every figure and table script can be exercised before the confirmatory runs exist.

Nothing here is a result. Everything is invented: the design (condition keys, laboratories, stages, cells), the ageing law, the scores, the predictions, the
stress functions. NO Samsung / ISU / SNL file, split file or preregistration file is read (retention blinding, PREREG_v4 3.3(9)); the design table the demo
writes (`design/experiments_meta.csv`) has the column layout of the dataset metadata but invented rows.

What is generated, and by what:
  * run directories (the RUN WRITER's files: config, metrics, condition / cell scores, comparators, predictions, window, stress functions, residual map, superposition,
    extracted laws, subsets, reference values, invariance) for the grid (3 m x 5 outer folds), Test C and S2;
  * the ANALYSIS files are produced by the real statistics-step code (`pinnkan.stats_v4.Store.from_runs`, `stats_rows.run_v4_full`, `stats_step.build_controls`,
    `stats_step._test_c_s2`, `stats_v4.edge_level_wording`, `physval.physval_11a`) run on these synthetic directories, so the figure scripts are exercised against the
    real output formats. This module computes no interval, test or tier itself.
  * `analysis/arm_table.json` (Table 1) is NOT produced by the statistics step yet (ALIGN_V4_REPORT gap G1): the demo writes a SYNTHETIC stand-in so that the
    table code path runs; its `producer` field says so.

Run:  .venv\\Scripts\\python.exe -P code\\figures\\make_demo_runs.py [--out DIR]     (default runs/figdemo_SYNTHETIC; CPU only, about 1 minute)
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import pk_style as ps  # noqa: E402

OUT_DEFAULT = ps.ROOT / "runs" / "figdemo_SYNTHETIC"
SEEDS = [0, 1, 2, 3, 4]
GRID_M, KS, K_FULL = (8, 16, 32), ("0", "2", "full"), 4
N_FOLDS = 5
T_CYC = np.arange(1, 11) * 28.0
T_STO = np.arange(1, 9) * 56.0
WIN = {"0": 0, "2": 2, "full": K_FULL}                    # model-visible check-ups after the reference check-up


def dump(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1)


def mark(d, note="SYNTHETIC DEMO DATA - invented laws, not results of any experiment or model fit"):
    d = Path(d)
    d.mkdir(parents=True, exist_ok=True)
    (d / "SYNTHETIC").write_text(note + "\n")


# ------------------------------------------------------------------------------------------ invented design
def cond_key(T, smax, dod, cc, cd):
    return f"T{T:g}|SOCmax{smax:g}|DoD{dod:g}|Cch{cc:g}|Cdch{cd:g}"


def sto_key(T, soc):
    return f"T{T:g}|SOC{soc:g}"


def build_design(rng):
    """invented design: 40 cycling test conditions (23 and 45 C), 13 at 35 C (laboratory INT), 19 storage conditions; cells with laboratory and stage"""
    D = {"B": [], "C": [], "S2": []}
    meta, serial = [], 0

    def add_cells(key, kind, T, smax, dod, cc, cd, labs, n_cells):
        nonlocal serial
        cells = []
        for j in range(n_cells):
            serial += 1
            lab = labs[j % len(labs)]
            stage = 1 if (serial % 3) else 2
            cid = f"SYN{serial:03d}_s{stage}"
            cells.append(dict(cell_id=cid, lab=lab, stage=stage, cell=j + 1))
            meta.append(dict(type=kind, cell=j + 1, serial=f"SYN{serial:03d}", stage=stage, lab=lab, amb_temp_tp=T, soc_max_tp=smax, dod_tp=dod, c_ch_tp=cc, c_dch_tp=cd))
        return cells

    seen = set()

    def new_cyc(T, labs):
        while True:
            smax = float(rng.choice([0.55, 0.65, 0.8, 0.9, 1.0]))
            dod = float(rng.choice([0.1, 0.2, 0.35, 0.5, 0.7]))
            cc = float(rng.choice([0.2, 0.4, 0.7, 1.0, 1.2]))
            cd = float(rng.choice([0.5, 1.0, 1.5, 2.0]))
            k = cond_key(T, smax, dod, cc, cd)
            if smax - dod >= 0.05 and k not in seen:
                seen.add(k)
                return k, smax, dod, cc, cd

    for i in range(40):
        T = 23 if i < 20 else 45
        labs = ["HM", "SIE"] if T == 23 else ["HM"]
        k, smax, dod, cc, cd = new_cyc(T, labs)
        D["B"].append(dict(key=k, cells=add_cells(k, "z", T, smax, dod, cc, cd, labs, 2 + (i % 2)), T=T, fold=i % N_FOLDS))
    for i in range(13):
        k, smax, dod, cc, cd = new_cyc(35, ["INT"])
        D["C"].append(dict(key=k, cells=add_cells(k, "z", 35, smax, dod, cc, cd, ["INT"], 2 + (i % 2)), T=35, fold=0))
    soc_levels = {10: [0.05, 0.25, 0.5, 0.65, 0.8, 1.0], 23: [0.05, 0.2, 0.35, 0.5, 0.65, 0.8, 1.0], 45: [0.05, 0.25, 0.5, 0.65, 0.8, 1.0]}
    labs_sto = {10: ["SIE"], 23: ["INT", "HM", "SIE"], 45: ["HM"]}
    for T, levels in soc_levels.items():
        for soc in levels:
            D["S2"].append(dict(key=sto_key(T, soc), cells=add_cells(sto_key(T, soc), "k", T, soc, 0.0, 0.0, 0.0, labs_sto[T], 3), T=T, fold=0))
    return D, pd.DataFrame(meta)


# ------------------------------------------------------------------------------------------ invented ageing law and scores
def arr_factor(T, Ea=45000.0, Tref=23.0):
    return np.exp(-Ea / 8.314 * (1 / (T + 273.15) - 1 / (Tref + 273.15)))


def fade_pp(cond, t):
    t = np.asarray(t, float)
    if cond["kind"] == "sto":
        s = cond["soc"] / 100
        return 2.4 * arr_factor(cond["T"]) * (0.5 + 1.4 * s ** 2) * (t / 400) ** 0.55
    s, dod = cond["soc_mid"] / 100, cond["dod"] / 100
    cal = 2.0 * arr_factor(cond["T"]) * (0.5 + 1.4 * s ** 2) * (t / 300) ** 0.6
    hours = dod / cond["c_ch"] + dod / cond["c_dch"] + 1.0
    efc = t * 24.0 / hours * dod
    cyc = 5.0 * (1 + 2.0 * max(cond["c_ch"] - 0.7, 0)) * (1 + 0.5 * (arr_factor(cond["T"], 20000) - 1)) * (1 + 0.8 * (dod - 0.3)) * (efc / 1000) ** 0.7
    return cal + cyc


def observed(cond_key_, cells, t, rng):
    c = ps.parse_cond(cond_key_)
    out = {}
    for ce in cells:
        f = fade_pp(c, t) * (1 + rng.normal(0, 0.07))
        out[ce["cell_id"]] = 1 - (f + rng.normal(0, 0.12, len(t))) / 100
    return out


# mean log ratio L = ln(S_comparator / S_A1) by (arm, m); A1 error level by (m, k)
L_MEAN = {"A9": {8: 0.45, 16: 0.40, 32: 0.36}, "A11": {8: 0.30, 16: 0.17, 32: 0.08}, "A12": {8: 0.34, 16: 0.22, 32: 0.12},
          "A4": {8: 0.12, 16: 0.10, 32: 0.09}, "A5": {8: 0.14, 16: 0.12, 32: 0.10}, "A2": {8: 0.04, 16: 0.04, 32: 0.04},
          "A10": {8: 0.22, 16: 0.22, 32: 0.22}, "A10P": {8: 0.17, 16: 0.17, 32: 0.17}, "A13": {8: 0.03, 16: 0.03, 32: 0.03},
          "R1": {8: 0.80, 16: 0.80, 32: 0.80}, "R2": {8: 0.60, 16: 0.60, 32: 0.60}, "A15": {8: 0.02, 16: 0.02, 32: 0.02}, "G15": {8: 0.20, 16: 0.20, 32: 0.20}}
F_MK = {("8", "0"): 1.65, ("8", "2"): 1.35, ("8", "full"): 1.20, ("16", "0"): 1.45, ("16", "2"): 1.15, ("16", "full"): 1.05, ("32", "0"): 1.35, ("32", "2"): 1.05, ("32", "full"): 0.95}
SCORE_ARMS = ["A1", "A9", "A11", "A12", "A4", "A5", "A2", "A10", "A10P", "A13", "R1", "R2"]
NPARAM = dict(A1=2621, A2=188, A4=2623, A5=3312, A9=50945, A10=11, A11=14, A12=1850, A10P=14, A13=2621, R1=0, R2=2, A15=17, G15=9)
FITSEC = dict(A1=7.0, A2=1.4, A4=5.2, A5=6.0, A9=9.5, A10=2.2, A10P=2.4, A11=3.0, A12=0.6, A13=6.1, R1=0.0, R2=0.0, A15=1.2, G15=1.0)
PRED_ARMS = ("A1", "A10")          # plus the fold's D* arm


def arms_for_cell(m, k):
    out = list(SCORE_ARMS)
    if k == "0":
        out = [a for a in out if a not in ("R1", "R2")]
    if (m, k) == (32, "full"):
        out += ["A15", "G15"]
    return out


def make_cell_rmse(conds_cells, m, k, arms, rng, state):
    """cell RMSE (pp) per arm: condition level x A1 level x exp(mean log ratio + arm x condition effect + noise) x replicate-cell deviation; `state` keeps the shared random effects"""
    diff, u, dev = state["diff"], state["u"], state["dev"]
    out = {}
    for a in arms:
        lm = 0.0 if a == "A1" else L_MEAN[a][m]
        for cond, cells in conds_cells:
            for ce in cells:
                eps = rng.normal(0, 0.10)
                out[(a, ce["cell_id"])] = float(diff[cond] * F_MK[(str(m), k)] * np.exp(lm + (0.0 if a == "A1" else u[(a, cond)]) + eps) * np.exp(dev[ce["cell_id"]]))
    return out


def smooth_noise(rng, n, scale):
    e = rng.normal(0, 1, n)
    return np.convolve(np.r_[e[:1], e, e[-1:]], np.ones(3) / 3, "valid") * scale


def predictions_rows(phase, arm, cond, cell_id, y_obs, t_all, n_win, rmse, rng):
    """per-seed and ensemble forecast rows whose ensemble RMSE (pp) equals `rmse` exactly: ensemble = observed + shaped error, seeds scatter around it with zero mean"""
    tf = t_all[n_win:]
    yo = y_obs[n_win:]
    s = np.linspace(0.2, 1.0, len(tf))
    err = rng.choice([-1.0, 1.0]) * rmse * s / np.sqrt(np.mean(s ** 2))
    ens = yo + err / 100.0
    w = np.stack([smooth_noise(rng, len(tf), 0.18 * rmse / 100.0) for _ in SEEDS])
    w -= w.mean(0, keepdims=True)
    rows = []
    for sd, wob in zip(SEEDS, w):
        rows += [(phase, arm, str(sd), cell_id, cond, float(t), float(p), float(y)) for t, p, y in zip(tf, ens + wob, yo)]
    rows += [(phase, arm, "ens", cell_id, cond, float(t), float(p), float(y)) for t, p, y in zip(tf, ens, yo)]
    return rows


def cond_scores_from_cells(cell_rmse, conds_cells, arm):
    return {cond: float(np.mean([cell_rmse[(arm, ce["cell_id"])] for ce in cells])) for cond, cells in conds_cells}


# ------------------------------------------------------------------------------------------ model-derived artefacts (invented)
def stress_functions(rng):
    """stress_functions.json in the format of pinnkan.emit.stress_functions (bands + `members`), invented numbers"""
    soc = np.arange(0, 101, 5.0)
    nm, s = 25, soc / 100
    E0 = 38 + 14 * s ** 1.5 + 3 * np.sin(3 * s)
    lna0 = 0.9 + 1.4 * s ** 2 - 0.3 * s
    Em = E0 + rng.normal(0, 1, (nm, 1)) * 1.2 + np.cumsum(rng.normal(0, 0.35, (nm, len(soc))), 1) * (0.5 + 0.8 * s)
    lam = lna0 + rng.normal(0, 1, (nm, 1)) * 0.06 + np.cumsum(rng.normal(0, 0.03, (nm, len(soc))), 1)

    def band(m):
        return dict(mean=m.mean(0).tolist(), lo=m.min(0).tolist(), hi=m.max(0).tolist())
    aM = np.exp(lam)
    Ts = [10, 23, 45]
    rate_m = np.stack([aM * np.exp(-Em * 1000 / 8.314 * (1 / (T + 273.15) - 1 / 296.15)) for T in Ts], 1)
    rate = dict(T_C=Ts, soc=soc.tolist(), **band(rate_m))
    sel = [5, 50, 80, 100]
    idx = [int(np.argmin(abs(soc - v))) for v in sel]
    lr = np.log(rate_m[:, :, idx]).transpose(0, 2, 1)                                   # members x nsel x nT
    arr = dict(soc=sel, T_C=Ts, ln_rate=band(lr))
    members = {"E_kJmol": Em.tolist(), "a_pp500": aM.tolist(), "storage_rate": rate_m.tolist(), "arrhenius_ln_rate": lr.tolist()}
    vars_ = {"T": (np.linspace(5, 50, 46), lambda x: 0.045 * (x - 28) + 0.0006 * (x - 28) ** 2, lambda x: 0.05 * (x - 28)),
             "soc_mid": (np.linspace(10, 90, 41), lambda x: 0.0008 * (x - 55) ** 2 - 0.1, lambda x: 0.004 * (x - 55)),
             "dod": (np.linspace(0, 80, 41), lambda x: 0.035 * x - 0.00022 * x ** 2 - 1.0, lambda x: 0.016 * (x - 40)),
             "c_ch": (np.linspace(0, 1.2, 49), lambda x: 0.2 * x + 1.4 * np.maximum(x - 0.7, 0) ** 1.2 - 0.3, lambda x: 0.55 * (x - 0.6)),
             "c_dch": (np.linspace(0, 2.2, 45), lambda x: 0.07 * np.sin(2 * x) + 0.05 * x - 0.06, lambda x: 0.08 * (x - 1.1))}
    cyc = {}
    for k, (x, f, g) in vars_.items():
        base = f(x)
        mem = base + rng.normal(0, 1, (nm, 1)) * 0.05 + np.cumsum(rng.normal(0, 0.012, (nm, len(x))), 1)
        mem -= mem.mean(1, keepdims=True)
        gam = base + 0.05 * np.sin(5 * x / x.max())
        gam -= gam.mean()
        a10 = g(x) - g(x).mean()
        members[f"cyclic.{k}"] = mem.tolist()
        cyc[k] = dict(x=x.tolist(), A1=band(mem), A4=dict(mean=gam.tolist()), A10=dict(mean=a10.tolist()))
    cal = dict(soc=soc.tolist(), E_kJmol=band(Em), a_pp500=band(aM), A10_E_kJmol=float(E0.mean() + 3.0))
    return dict(n_members=nm, member_definition="final-refit seeds of this run's outer fold (min/max envelope); merge folds for the paper", calendar=cal, storage_rate=rate,
                arrhenius=arr, cyclic=cyc, members=members, synthetic=True)


def residual_map(D, rng):
    Te, Se, Ce = np.linspace(5, 50, 5), np.linspace(0, 100, 6), np.linspace(0, 1.2, 5)
    Tc, Sc, Cc = (Te[1:] + Te[:-1]) / 2, (Se[1:] + Se[:-1]) / 2, (Ce[1:] + Ce[:-1]) / 2
    R1 = 0.04 + 0.05 * np.abs(Tc[:, None] - 30) / 20 * (0.5 + Sc[None, :] / 100) + rng.normal(0, 0.006, (len(Tc), len(Sc)))
    R2 = 0.05 + 0.08 * Cc[None, :] * (0.6 + np.abs(Tc[:, None] - 28) / 22) + rng.normal(0, 0.006, (len(Tc), len(Cc)))
    pts_ts = [(ps.parse_cond(e["key"])["T"], ps.parse_cond(e["key"])["soc_mid"]) for e in D["B"]] + [(e["T"], 100 * float(e["key"].split("SOC")[-1])) for e in D["S2"]]
    pts_ct = [(ps.parse_cond(e["key"])["c_ch"], ps.parse_cond(e["key"])["T"]) for e in D["B"]]
    return dict(T_edges=Te, soc_edges=Se, cch_edges=Ce, absR_T_SOC=np.abs(R1), absR_cch_T=np.abs(R2), train_T_SOC=np.array(pts_ts), train_cch_T=np.array(pts_ct))


def superposition(entries, rng):
    rows = []
    for e in entries:
        c = ps.parse_cond(e["key"])
        base = 0.20 + 0.45 * (arr_factor(c["T"]) / arr_factor(45)) * (1 - 0.3 * c["c_ch"] / 1.2)
        for ce in e["cells"]:
            for arm, off in (("A1", 0.0), ("A2", 0.06)):
                sh = float(np.clip(base + off + rng.normal(0, 0.05), 0.03, 1.15))
                rows.append((ce["cell_id"], e["key"], arm, sh, sh > 1.0))
    return pd.DataFrame(rows, columns=["cell_id", "cond", "arm", "share_cal", "cal_exceeds_total"])


def law_records(fold, rng, thr):
    """fold x seed law records in the format of extraction_audit.law_record (invented)"""
    fams = ["linear", "log", "power", "exponential", "quadratic", "hinge"]
    recs = []
    for arm in ("A15h2", "G15"):
        for sd in SEEDS:
            inputs = {}
            for name in thr["inputs"]:
                retained = bool(rng.random() > 0.08)
                sr = int(rng.choice([-1, 1], p=[0.25, 0.75]))
                inputs[name] = dict(retained=retained, range=float(rng.uniform(0.2, 1.5)), family=str(rng.choice(fams)), edge_families=[str(rng.choice(fams))], bic_margin=float(rng.uniform(0, 40)),
                                    r_lin=float(rng.uniform(0, 0.08)), r_log=float(rng.uniform(0, 0.08)), form=str(rng.choice(["linear", "log", "tie", "none"])), sign=sr, sign_raw=sr,
                                    max_mixed=float(rng.uniform(0, 0.05)), additive=bool(rng.random() > 0.3), approx=bool(rng.random() > 0.8))
            recs.append(dict(arm=arm, fold=fold, seed=sd, h=2 if arm != "G15" else 1, outer_families=[], inputs=inputs))
    return recs


# ------------------------------------------------------------------------------------------ writers
def metrics_block(cs_k, arms, rng, n_cond):
    out = {}
    for a in arms:
        v = list(cs_k[a].values())
        out[a] = dict(primary_pp=float(np.mean(v)), seed_sd_of_mean=float(0.04 * np.mean(v) * (1 + 0.2 * rng.random())), n_conditions=len(v), n_nonfinite=0, n_params=NPARAM.get(a, 0),
                      n_train_used=int(n_cond), fit_seconds_one_fit=FITSEC.get(a, 1.0) * (1 + 0.1 * rng.random()), mae_pp_mean=float(0.85 * np.mean(v)))
    return out


def write_grid_run(out, D, meta_cells, fold, m, rng, state, subsets, thr, stress_proto):
    """one grid run = (outer fold, m): all three k cells, in the run writer's file layout"""
    d = out / "grid" / f"m{m}_f{fold}"
    mark(d)
    test = [e for e in D["B"] if e["fold"] == fold]
    conds_cells = [(e["key"], e["cells"]) for e in test]
    comp_dstar = "A11" if fold % 2 == 0 else "A12"
    comp = {"D*": {"arm": comp_dstar, "complete": True}, "AG": {"arm": "A4", "complete": True}}
    dump(dict(run_id=d.name, dataset="synthetic", test="B", design="R2", m=m, fold=fold, k="grid", seeds=SEEDS, mode="confirmatory", synthetic=True), d / "config.json")
    dump(comp, d / "comparators.json")
    ids = sorted(e["key"] for e in D["B"] if e["fold"] != fold)
    sub = subsets.apply(ids, m)
    dump(sub, d / "subsets.json")
    dump({k: dict(n_cells=len(next(e for e in D["B"] if e["key"] == k)["cells"]), lab=next(e for e in D["B"] if e["key"] == k)["cells"][0]["lab"],
                  labs={next(e for e in D["B"] if e["key"] == k)["cells"][0]["lab"]: len(next(e for e in D["B"] if e["key"] == k)["cells"])}) for k in sub["order"]}, d / "train_condition_meta.json")
    pred_rows, win_rows, by_k, cs_all = [], [], {}, {}
    for k in KS:
        arms = arms_for_cell(m, k)
        cr = make_cell_rmse(conds_cells, m, k, arms, rng, state)
        suf = "" if k == "full" else f"_k{k}"
        phase = "outer_test" if k == "full" else f"outer_test_k{k}"
        cs = {a: cond_scores_from_cells(cr, conds_cells, a) for a in arms}
        cs_files = dict(cs)
        cell_scores = {a: {ce["cell_id"]: dict(cond=cond, rmse_pp=cr[(a, ce["cell_id"])], n_fc=len(T_CYC) - WIN[k]) for cond, cells in conds_cells for ce in cells} for a in arms}
        dump(cs_files, d / f"condition_scores{suf}.json")
        dump(cell_scores, d / f"cell_scores{suf}.json")
        dump({cond: dict(n_cells=len(cells), lab={cells[0]["lab"]: len(cells)}, stage={str(cells[0]["stage"]): len(cells)}) for cond, cells in conds_cells}, d / f"condition_meta{suf}.json")
        by_k[k] = metrics_block(cs, arms, rng, len(sub["kept"]))
        cs_all[k] = cs
        for cond, cells in conds_cells:
            obs = state["obs"][cond]
            for ce in cells:
                y = obs[ce["cell_id"]]
                for a in list(PRED_ARMS) + [comp_dstar]:
                    pred_rows += predictions_rows(phase, a, cond, ce["cell_id"], y, T_CYC, WIN[k], cr[(a, ce["cell_id"])], rng)
                if k == "full":
                    win_rows += [(ce["cell_id"], cond, float(t), float(v)) for t, v in zip(T_CYC[:K_FULL], y[:K_FULL])]
    # a "D*" row of predictions is the chosen arm's (the figure reads comparators.json)
    pd.DataFrame(pred_rows, columns=["phase", "arm", "seed", "cell_id", "cond", "t", "pred_retention", "true_retention"]).to_csv(d / "predictions.csv", index=False, float_format="%.5f")
    pd.DataFrame(win_rows, columns=["cell_id", "cond", "t", "retention"]).to_csv(d / "window.csv", index=False)
    dump(dict(blinded=False, mode="confirmatory", backbone="self_limiting", k_labels=list(KS), k_primary="full", k_full=K_FULL, outer_test=by_k["full"], outer_test_by_k=by_k,
              inner_cv_pp={a: v["primary_pp"] * 1.06 for a, v in by_k["full"].items()}, comparators={k: v["arm"] for k, v in comp.items()}), d / "metrics.json")
    dump({a: dict(median_fit_seconds=FITSEC.get(a, 1.0), n_trials=40, n_failed=0) for a in SCORE_ARMS}, d / "timings.json")
    dump(dict(R_LOO=float(np.mean(list(cs_all["full"]["A1"].values())) * 0.72 * (1 + 0.05 * rng.normal())), R_WARP=float(np.mean(list(cs_all["full"]["A1"].values())) * 0.80 * (1 + 0.05 * rng.normal())),
              n_conditions=len(test)), d / "reference_values.json")
    dump(dict(passed=True, max_abs_diff=0.0, n_rows=int(len(pred_rows))), d / "invariance.json")
    if m == 32:
        dump(stress_functions(rng), d / "stress_functions.json")
        np.savez(d / "residual_map.npz", **residual_map(D, rng))
        superposition(test, rng).to_csv(d / "superposition.csv", index=False)
        dump(dict(m=32, fold=fold, laws=law_records(fold, rng, thr), levels={}, extraction_audit_sha256="synthetic"), d / "extracted_laws.json")
    return d, cs_all


def write_single_run(out, name, test_name, entries, t_all, n_win, scales_mean, rng, state, with_window=True):
    """grid-free run (Test C or S2): one cell, plain file names, scored at the k_full cell"""
    d = out / name
    mark(d)
    conds_cells = [(e["key"], e["cells"]) for e in entries]
    arms = ["A1", "A9", "A10", "A10P", "A11", "A12", "R1"] if test_name != "S2" else ["A1", "A9", "A10", "A10P", "A11", "A12", "A13", "R1"]
    comp = {"D*": {"arm": "A12", "complete": True}}
    dump(dict(run_id=name, dataset="synthetic", test=test_name, design="R2", m=None, fold=0, seeds=SEEDS, mode="confirmatory", synthetic=True), d / "config.json")
    dump(comp, d / "comparators.json")
    diff = {c: float(np.exp(rng.normal(0, 0.4))) for c, _ in conds_cells}
    cr = {}
    for a in arms:
        lm = 0.0 if a == "A1" else scales_mean.get(a, 0.2)
        for cond, cells in conds_cells:
            u = rng.normal(0, 0.12)
            for ce in cells:
                cr[(a, ce["cell_id"])] = float(diff[cond] * 1.1 * np.exp(lm + u + rng.normal(0, 0.10) + rng.normal(0, 0.1)))
    cs = {a: cond_scores_from_cells(cr, conds_cells, a) for a in arms}
    dump(cs, d / "condition_scores.json")
    dump({a: {ce["cell_id"]: dict(cond=cond, rmse_pp=cr[(a, ce["cell_id"])], n_fc=len(t_all) - n_win) for cond, cells in conds_cells for ce in cells} for a in arms}, d / "cell_scores.json")
    dump({cond: dict(n_cells=len(cells), lab={cells[0]["lab"]: len(cells)}, stage={str(cells[0]["stage"]): len(cells)}) for cond, cells in conds_cells}, d / "condition_meta.json")
    rows, wrows = [], []
    for cond, cells in conds_cells:
        obs = observed(cond, cells, t_all, rng)
        for ce in cells:
            y = obs[ce["cell_id"]]
            for a in ("A1", "A10", "A12"):
                rows += predictions_rows("outer_test", a, cond, ce["cell_id"], y, t_all, n_win, cr[(a, ce["cell_id"])], rng)
            wrows += [(ce["cell_id"], cond, float(t), float(v)) for t, v in zip(t_all[:n_win], y[:n_win])]
    pd.DataFrame(rows, columns=["phase", "arm", "seed", "cell_id", "cond", "t", "pred_retention", "true_retention"]).to_csv(d / "predictions.csv", index=False, float_format="%.5f")
    pd.DataFrame(wrows, columns=["cell_id", "cond", "t", "retention"]).to_csv(d / "window.csv", index=False)
    dump(dict(blinded=False, mode="confirmatory", backbone="self_limiting", outer_test=metrics_block(cs, arms, rng, 32), comparators={"D*": "A12"}), d / "metrics.json")
    dump({a: dict(median_fit_seconds=FITSEC.get(a, 1.0), n_trials=40, n_failed=0) for a in arms}, d / "timings.json")
    return d, cs


class Subsets:
    """nested max-min subsets from the project's own identifier-only selector (pinnkan.subsets); synthetic identifiers only"""

    def __init__(self):
        from pinnkan import subsets as S
        self.S = S

    def apply(self, ids, m):
        order = self.S.order_for_ids(ids, "samsung", None)
        keep = self.S.subset_at(order, m)
        return {"m": int(m), "kind": "maxmin", "draw": None, "n_train_conditions": len(ids), "kept": keep, "order": order, "thinned": len(keep) < len(ids), "sha256": "synthetic"}


def synthetic_h7(out, rng, n_draws=20):
    d = out / "synthetic_H7"
    mark(d)
    lhs = rng.random((500, 3))
    ft = np.sin(2.4 * lhs[:, 0]) + 0.9 * lhs[:, 1] ** 2 + 0.5 * lhs[:, 2]
    ft = ft - ft.mean()
    par = dict(A1=0.075, A2=0.075, A4=0.085, A8=0.125)
    summary, F = [], {k: np.zeros((n_draws, 500)) for k in ("true", "A1", "A2", "A4", "A8")}
    for i in range(n_draws):
        scale_i = np.exp(rng.normal(0, 0.12))
        F["true"][i] = ft * (1 + 0.1 * rng.normal())
        rg = F["true"][i].max() - F["true"][i].min()
        nr = {}
        for a in par:
            target = par[a] * scale_i * np.exp(rng.normal(0, 0.22))
            err = np.convolve(rng.normal(0, 1, 500), np.ones(25) / 25, "same")
            err = err - err.mean()
            err = err * target * rg / np.sqrt(np.mean(err ** 2))
            F[a][i] = F["true"][i] + err
            nr[a] = float(np.sqrt(np.mean(err ** 2)) / rg)
        fr = {a: float(1.0 * (nr[a] / 0.1) ** 0.8 * np.exp(rng.normal(0, 0.1))) for a in nr}
        fr["A11"], fr["A12"] = fr["A4"] * 1.35, fr["A4"] * 1.4
        summary.append(dict(gen="G0", draw=i, additive_floor=0.03, nrmse=nr, forecast_pp=fr))
    np.savez(d / "surfaces_G0.npz", lhs=lhs, **{f"f_{k}": v for k, v in F.items()})
    dump(dict(synthetic=True, thresholds=dict(pass_=0.15, fail=0.30), n_draws=n_draws, arms=list(par), draws=summary), d / "summary.json")
    return d / "summary.json"


def fade_curves(meta, rng):
    rows = []
    for r in meta.itertuples():
        if r.type == "k":
            if r.cell > 3:
                continue
            c = dict(kind="sto", T=float(r.amb_temp_tp), soc=100 * float(r.soc_max_tp))
            t = np.arange(1, 10) * 56.0
        else:
            c = dict(kind="cyc", T=float(r.amb_temp_tp), soc_mid=100 * (r.soc_max_tp - r.dod_tp / 2), dod=100 * r.dod_tp, c_ch=float(r.c_ch_tp), c_dch=float(r.c_dch_tp))
            t = np.arange(1, 11) * 28.0
        u = rng.normal(0, 0.07) + (0.05 if r.stage == 2 else 0.0) + {"INT": 0.04, "HM": -0.02, "SIE": 0.0}[r.lab]
        y = 1 - (fade_pp(c, t) * (1 + u) + rng.normal(0, 0.12, len(t))) / 100
        for ti, yi in zip(t, y):
            rows.append((f"{r.serial}_s{r.stage}", r.lab, r.type, int(r.stage), float(r.amb_temp_tp), float(r.soc_max_tp), float(r.dod_tp), float(r.c_ch_tp), float(r.c_dch_tp), float(ti), float(yi)))
    return pd.DataFrame(rows, columns=["cell_id", "lab", "type", "stage", "T_C", "SOC_max", "DoD", "C_ch", "C_dch", "elapsed_days", "retention"])


def arm_table_stand_in(cs_by_cell, metrics_by_cell, tc, s2):
    """SYNTHETIC stand-in for analysis/arm_table.json (gap G1: the statistics step does not write it). Pools the per-fold values of the synthetic runs by condition count."""
    def pooled(blocks):
        arms = sorted({a for b in blocks for a in b})
        res = {}
        for a in arms:
            bb = [b[a] for b in blocks if a in b]
            n = np.array([x["n_conditions"] for x in bb], float)
            w = n / n.sum()
            res[a] = dict(mean_pp=float(np.sum(w * [x["primary_pp"] for x in bb])), seed_sd_pp=float(np.sqrt(np.sum((w * [x["seed_sd_of_mean"] for x in bb]) ** 2))), n_conditions=int(n.sum()),
                          n_params=bb[0]["n_params"], n_train_used=bb[0]["n_train_used"], fit_seconds=float(np.mean([x["fit_seconds_one_fit"] for x in bb])))
        return res
    out = {"producer": "SYNTHETIC stand-in written by make_demo_runs.py; the statistics step does not write this file yet (ALIGN_V4_REPORT gap G1)", "cells": {}}
    for (m, k), blocks in metrics_by_cell.items():
        out["cells"][f"{m}|{k}"] = pooled(blocks)
    out["test_c"] = pooled([tc])
    out["s2"] = pooled([s2])
    return out


# ------------------------------------------------------------------------------------------ main
def main(out_dir=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    a = ap.parse_args([] if out_dir is not None else None)
    out = Path(out_dir or a.out or OUT_DEFAULT)
    out.mkdir(parents=True, exist_ok=True)
    mark(out)
    (out / "README_SYNTHETIC.md").write_text(
        "# SYNTHETIC DEMO RUNS - NOT RESULTS\n\nEvery number and every identifier in this directory is invented by `code/figures/make_demo_runs.py` (no Samsung, ISU or SNL file is read). "
        "The analysis files are produced by the project's statistics-step code run on these synthetic run directories. Figures built from this directory carry the "
        "watermark 'SYNTHETIC DEMO - NOT RESULTS' and the file-name suffix `_SYNTHETIC`.\n")
    rng = np.random.default_rng(20261105)
    from pinnkan import extraction_audit as X
    from pinnkan import physval, semi, stats_rows, stats_step
    from pinnkan import stats_v4 as v4
    thr = X.load_thresholds()
    D, meta = build_design(rng)
    mark(out / "design")
    meta.to_csv(out / "design" / "experiments_meta.csv", index=False)
    fade_curves(meta, rng).to_csv(out / "design" / "fade_curves.csv", index=False)
    # shared random effects: condition level, arm x condition, replicate cell, observed curves
    state = {"diff": {}, "u": {}, "dev": {}, "obs": {}}
    for e in D["B"]:
        state["diff"][e["key"]] = float(np.exp(rng.normal(0, 0.35)))
        for arm in L_MEAN:
            state["u"][(arm, e["key"])] = float(rng.normal(0, 0.14))
        state["obs"][e["key"]] = observed(e["key"], e["cells"], T_CYC, rng)
        for ce in e["cells"]:
            state["dev"][ce["cell_id"]] = float(rng.normal(0, 0.10))
    subsets = Subsets()
    B_dirs, metrics_by_cell = [], {}
    for m in GRID_M:
        for f in range(N_FOLDS):
            d, cs_all = write_grid_run(out, D, None, f, m, rng, state, subsets, thr, None)
            B_dirs.append(d)
            met = json.load(open(d / "metrics.json", encoding="utf8"))
            for k in KS:
                metrics_by_cell.setdefault((m, k), []).append(met["outer_test_by_k"][k])
    C_dir, _ = write_single_run(out, "test_C", "C", D["C"], T_CYC, K_FULL, {"A9": 0.5, "A10": 0.3, "A10P": 0.25, "A11": 0.2, "A12": 0.25, "R1": 0.9}, rng, state)
    S_dir, _ = write_single_run(out, "test_S2", "S2", D["S2"], T_STO, 2, {"A9": 0.4, "A10": 0.15, "A10P": 0.12, "A11": 0.25, "A12": 0.28, "A13": 0.05, "R1": 0.9}, rng, state)
    h7 = synthetic_h7(out, rng)
    # ---- the analysis: the project's statistics-step functions on the synthetic directories
    an = out / "analysis"
    mark(an)
    store = v4.Store.from_runs([str(p) for p in B_dirs], strict=True)
    controls = stats_step.build_controls(real_runs=[str(p) for p in B_dirs], h7_summary=str(h7))
    res = stats_rows.run_v4_full(store, None, gate=controls["gate_G"])
    prov = {"rows_not_run": res["downgrade"]["rows_not_run"], "gate_not_evaluated": list(controls["gate_G"].get("not_evaluated", []))}
    prov["provisional"] = True
    res["status"] = prov
    res["outcome"]["provisional"] = True
    mk = lambda dirs: v4.Store.from_runs([str(x) for x in dirs], strict=False)
    res.update(stats_step._test_c_s2(mk, False, [C_dir], None, [S_dir]))
    res["gate_G"] = controls["gate_G"]
    m32 = [str(p) for p in B_dirs if p.name.startswith("m32_")]
    res["edge_wording"] = {"printed": False, "reason": "descriptive reporting only: the extracted laws are printed in closed form without named edge families (D022b)",
                           "stability": v4.edge_level_wording(m32)}
    stats_step.write_json(str(an / "contrasts_v4_B.json"), res)
    stats_step.write_json(str(an / "controls.json"), controls)
    old = semi.A10_FORM["verified"]
    semi.A10_FORM["verified"] = True                 # synthetic demo only: exercises the "vs A10" branches of physval (the real flag is set after FB-2)
    try:
        pv = physval.physval_11a(m32, meta_csv=str(out / "design" / "experiments_meta.csv"))
    finally:
        semi.A10_FORM["verified"] = old
    stats_step.write_json(str(an / "physval_11a.json"), pv)
    ref = stats_step.reference_from_runs([str(p) for p in B_dirs if p.name.startswith("m32_")])
    stats_step.write_reference(str(an / "reference.json"), {"B": ref})
    tc_met, s2_met = json.load(open(C_dir / "metrics.json", encoding="utf8"))["outer_test"], json.load(open(S_dir / "metrics.json", encoding="utf8"))["outer_test"]
    dump(arm_table_stand_in(None, metrics_by_cell, tc_met, s2_met), an / "arm_table.json")
    print("demo runs and analysis written to", out)
    return out


if __name__ == "__main__":
    main()
