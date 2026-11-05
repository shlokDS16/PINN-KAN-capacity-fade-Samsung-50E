"""D021 [ARCH: cap]: pipeline-level synthetic study of the per-edge cap (CPU only, no Samsung/ISU label). Rule: debates/D021_cap/study_rule.md (committed before the first run).
One cell = (design seed, kind in {G0, G2}, m in {32, 8}); in each cell three arms (A15 h=1, A15 h=2, G15) get ONE parent fit, then one extraction + refit per cap in (2, 3) and an
extraction-only check at cap 4. Records go to runs/D021_cap_synth/pipeline_p<proc>.jsonl, one JSON line per (cell, arm).
    .venv/Scripts/python.exe -P code/prereg/d021_cap_study.py --proc 0 --nproc 2 --seeds 12 --deadline-min 50"""
import argparse
import copy
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np  # noqa: E402
import torch  # noqa: E402
from scipy.stats import qmc  # noqa: E402

torch.set_num_threads(1)

from pinnkan import arms as A  # noqa: E402
from pinnkan import data as D  # noqa: E402
from pinnkan import metrics, symbolic, synth  # noqa: E402
from pinnkan.pinn import fit_pinn, predict_pinn  # noqa: E402
from pinnkan.law import batch_from_cells  # noqa: E402
from pinnkan.specs import SPECS  # noqa: E402

SPEC = SPECS["synthetic"]
OUT = os.path.join(ROOT, "runs", "D021_cap_synth")
CAPS = (2, 3)
ARMS = (("A15h1", "A15", {"h": 1}), ("A15h2", "A15", {"h": 2}), ("G15", "G15", {}))
LINEAR_INPUTS_G0 = ("T_C", "dod", "c_ch", "c_dch")           # truth of G0 is exactly linear in these (synth._truth)


def probe_rows(train, n=300, seed=0):
    """300 raw stress rows: 3 temperature levels x Latin hypercube over the training-hull box of (soc_mid, dod, c_ch, c_dch)"""
    cyc = np.array([c.raw for c in train if c.kind == "cycling"])
    lo, hi = cyc[:, 1:].min(0), cyc[:, 1:].max(0)
    u = qmc.LatinHypercube(d=4, seed=seed).random(n)
    body = lo + u * (hi - lo)
    temps = np.resize(np.array([23.0, 35.0, 45.0]), n)
    return np.column_stack([temps, body])


def law_err(fn, raw, truth_y, rng_y):
    s = np.clip(SPEC.norm(raw), -1.0, 1.0 - 1e-6)
    with torch.no_grad():
        f = fn(torch.tensor(s, dtype=torch.float32)).numpy().ravel().astype(float)
    e = (f - f.mean()) - (truth_y - truth_y.mean())
    return float(np.sqrt(np.mean(e ** 2)) / rng_y)


def first_layer_families(rep):
    """-> {input name: sorted families over the hidden nodes} of the cyclic stack, plus the number of 3-coefficient first-layer edges per input"""
    edges = rep["cyclic"]["layers"][0]["edges"]
    out = {}
    for i, name in enumerate(SPEC.stress_names):
        out[name] = [edges[j][i]["family"] for j in range(len(edges))]
    return out


def one_cell(kind, m, seed, log):
    S0 = synth.make_synthetic(kind, n_cyc_cond=40, n_sto_cond=8, reps=2, seed=seed)
    train32, test = synth.split_conditions(S0.cells, 0.2, seed)
    ids = {c.cond for c in train32 if c.kind == "cycling"}
    train, info = D.apply_subset(train32, "synthetic", "B", None, 0, m if m < 32 else None, ids=ids) if m < 32 else (train32, None)
    n_train_cyc = len({c.cond for c in train if c.kind == "cycling"})
    raw_probe = probe_rows(train, seed=seed)
    t_probe = np.asarray(S0.log_rate_cyc(raw_probe), float).ravel()
    rng_y = float(np.ptp(t_probe))
    te_raw = np.array([c.raw for c in test if c.kind == "cycling"])
    te_raw = np.unique(te_raw, axis=0)
    t_te = np.asarray(S0.log_rate_cyc(te_raw), float).ravel()
    prep = D.prepare_many([c for c in test if c.kind == "cycling"], D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2))
    b = batch_from_cells(SPEC, train)
    cyc = (b.is_cyc > 0.5).numpy()
    s_cyc = np.unique(b.s.numpy()[cyc], axis=0)
    s_cal = b.s.numpy()[:, SPEC.soc_index]
    steps = max(int(A.BASE_STEPS["pinn"]), 5)
    refit = max(int(steps * 0.5), 5)
    rows = []
    for label, arm_id, over in ARMS:
        t0 = time.time()
        hp = {**A.default_hp(arm_id), **over}
        hpm = dict(hp, map=A.ARMS[arm_id].map_kind)
        parent = fit_pinn(b, SPEC, hpm, "self_limiting", seed, steps=steps)
        rec = {"kind": kind, "m": m, "seed": seed, "arm": label, "n_train_cyc_conditions": n_train_cyc, "n_train_cells": len(train), "n_test_conditions": int(len(te_raw)),
               "parent_E_law": law_err(parent.law.cyc, raw_probe, t_probe, rng_y), "parent_E_test": law_err(parent.law.cyc, te_raw, t_te, rng_y),
               "parent_data_mse": float(parent.train_data_mse), "caps": {}}
        sym3 = None
        for cap in (2, 3, 4):
            sym_cyc, sym_cal, rep = symbolic.extract_law(parent.law, SPEC, s_cyc, s_cal, cap)
            fams = first_layer_families(rep)
            th = [[e.get("theta", []) for row in L["edges"] for e in row] for L in rep["cyclic"]["layers"]]
            cr = {"n_coefs": int(rep["n_coefs"]), "n_coefs_cyc": int(rep["cyclic"]["n_coefs"]), "families_first_layer": fams,
                  "families_all": [[e["family"] for row in L["edges"] for e in row] for L in rep["cyclic"]["layers"]],
                  "families_cal": ([[e["family"] for row in L["edges"] for e in row] for L in rep["calendar"]["layers"]] if rep["calendar"] else None)}
            cr["E_law_extracted"] = law_err(sym_cyc, raw_probe, t_probe, rng_y)
            if cap == 4:
                cr["theta"] = th
                rec["caps"]["4"] = cr
                rec["_th3"] = rec.get("_th3")
                continue
            cr["theta"] = th
            law_s = copy.deepcopy(parent.law)
            law_s.cyc = sym_cyc
            if sym_cal is not None:
                law_s.cal = sym_cal
            model = fit_pinn(b, SPEC, hpm, "self_limiting", seed, steps=refit, law=law_s, init_from=parent)
            cr["E_law"] = law_err(model.law.cyc, raw_probe, t_probe, rng_y)
            cr["E_test"] = law_err(model.law.cyc, te_raw, t_te, rng_y)
            try:
                preds, _ = predict_pinn(model, SPEC, [p.win for p in prep], float(hp.get("lam_res", 1.0)), seed, steps=60)
                rows_ = metrics.score_prepared(preds, prep)
                cr["forecast_rmse_pp"] = float(np.mean([r["rmse_pp"] for r in rows_]))
            except Exception as ex:                                  # a failed inversion must not lose the cell
                cr["forecast_rmse_pp"] = float("nan")
                cr["forecast_error"] = repr(ex)[:200]
            rec["caps"][str(cap)] = cr
        rec["cap4_equals_cap3"] = bool(rec["caps"]["4"]["families_all"] == rec["caps"]["3"]["families_all"] and rec["caps"]["4"]["theta"] == rec["caps"]["3"]["theta"])
        rec.pop("_th3", None)
        rec["seconds"] = time.time() - t0
        rows.append(rec)
        log(f"{kind} m={m} seed={seed} {label} done in {rec['seconds']:.0f}s E_law cap2 {rec['caps']['2']['E_law']:.3f} cap3 {rec['caps']['3']['E_law']:.3f} parent {rec['parent_E_law']:.3f}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proc", type=int, default=0)
    ap.add_argument("--nproc", type=int, default=2)
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--deadline-min", type=float, default=50.0)
    ap.add_argument("--only", default=None, help="kind:m:seed for a single timing run")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"pipeline_p{a.proc}.jsonl")
    t_start = time.time()

    def log(s):
        print(f"[{(time.time() - t_start) / 60:6.1f} min] {s}", flush=True)
    if a.only:
        k, m, s = a.only.split(":")
        cells = [(k, int(m), int(s))]
    else:
        cells = [(k, m, s) for s in range(a.seeds) for k in ("G0", "G2") for m in (32, 8)]
        cells = [c for i, c in enumerate(cells) if (c[2] % a.nproc) == a.proc]            # whole seed groups per process
    last = 0.0
    for kind, m, seed in cells:
        el = (time.time() - t_start) / 60.0
        if el + last * 1.1 > a.deadline_min:
            log(f"deadline: stop before seed {seed} ({kind}, m={m})")
            break
        t = time.time()
        recs = one_cell(kind, m, seed, log)
        with open(path, "a", encoding="utf8") as fh:
            for r in recs:
                fh.write(json.dumps(r) + "\n")
        last = (time.time() - t) / 60.0


if __name__ == "__main__":
    main()
