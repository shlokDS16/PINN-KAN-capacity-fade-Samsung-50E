"""D021 [ARCH: cap]: edge-level study of the frozen library under per-edge caps (CPU, seconds). No Samsung or ISU data; every function is written here.
Reads nothing but `pinnkan.symbolic`. Output: runs/D021_cap_synth/edge_study.json (+ a printed summary).
    .venv/Scripts/python.exe -P code/prereg/d021_edge_study.py"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np  # noqa: E402

from pinnkan import symbolic as S  # noqa: E402
from pinnkan.specs import SPECS  # noqa: E402

SPEC = SPECS["synthetic"]
OUT = os.path.join(ROOT, "runs", "D021_cap_synth")


def geos():
    """T edge on the 3-level hull (23 to 45 C) and two physical edges on the box of the real design (dod 0.05-0.6, c_ch 0.2-1.0), as stress_geos builds them"""
    raw = np.array([[23.0, 0.3, 0.05, 0.2, 0.3], [45.0, 0.8, 0.6, 1.0, 2.0]])
    s = SPEC.norm(raw)
    g = S.stress_geos(SPEC, s)
    return {"T": g[0], "dod": g[2], "c_ch": g[3]}


# truth parameters in the stored layout of each family (u / p abscissae of the geometry); amplitude a = 1 so that ranges are comparable
TRUTHS = [
    ("linear", {"a": [1.0, 0.0]}), ("log", {"a": [1.0, 0.0]}),
    ("quadratic", {"curv_0.1": [0.1, 1.0, 0.0], "curv_0.3": [0.3, 1.0, 0.0], "curv_1.0": [1.0, 1.0, 0.0]}),
    ("power", {"q_-1": [1.0, -1.0, 0.0], "q_0.5": [1.0, 0.5, 0.0], "q_2": [1.0, 2.0, 0.0]}),
    ("exponential", {"b_0.5": [1.0, 0.5, 0.0], "b_1.5": [1.0, 1.5, 0.0], "b_3": [1.0, 3.0, 0.0]}),
    ("hinge", {"k_-0.5": [1.0, -0.5, 0.0], "k_0": [1.0, 0.0, 0.0], "k_0.5": [1.0, 0.5, 0.0]}),
    ("arrhenius", {"b_0.5": [1.0, 0.5, 0.0], "b_2.5": [1.0, 2.5, 0.0]}),
]


def rel(y_hat, y):
    return float(np.sqrt(np.mean((y_hat - y) ** 2)) / max(np.ptp(y), 1e-12))


def smooth_bump(n, rms_rel, rng, rng_y):
    x = np.linspace(0, 1, n)
    f = sum(rng.normal() * np.sin(np.pi * (j + 1) * x + rng.uniform(0, 2 * np.pi)) / (j + 1) for j in range(3))
    f = f - f.mean()
    return f / max(np.sqrt(np.mean(f ** 2)), 1e-12) * rms_rel * rng_y


def run():
    out = {"rule": "d021_edge_study", "library_sha256": S.library_hash(), "tol_rel": S.RMS_TOL_REL, "n_coefs": S.N_COEFS, "rows": []}
    G = geos()
    rng = np.random.default_rng(np.random.SeedSequence([20261105, 21]))
    eq34 = True
    for gname, geo in G.items():
        x = np.linspace(geo.lo, geo.hi, S.G_GRID)
        for fam, variants in TRUTHS:
            if fam == "arrhenius" and gname != "T":
                continue
            for vname, th in variants.items():
                y0 = S.eval_family(fam, geo, th, x)
                if np.ptp(y0) < 1e-9:
                    continue
                rg = float(np.ptp(y0))
                for pert in (0.0, 0.005, 0.02):
                    reps = 1 if pert == 0.0 else 20
                    stat = {c: {"hit": 0, "err": [], "fam": {}, "n_coefs": []} for c in (1, 2, 3, 4)}
                    for _ in range(reps):
                        y = y0 + (smooth_bump(len(x), pert, rng, rg) if pert > 0 else 0.0)
                        tol = S.RMS_TOL_REL * float(np.ptp(y))          # the layer's largest edge range is this edge's
                        fits = {c: S.choose_family(geo, x, y, c, tol) for c in (1, 2, 3, 4)}
                        if fits[4].family != fits[3].family or not np.allclose(fits[4].theta, fits[3].theta):
                            eq34 = False
                        for c, f in fits.items():
                            st = stat[c]
                            st["hit"] += int(f.family == fam)
                            st["err"].append(rel(S.eval_family(f.family, geo, f.theta, x), y0))
                            st["fam"][f.family] = st["fam"].get(f.family, 0) + 1
                            st["n_coefs"].append(f.n_coefs)
                    out["rows"].append({"edge": gname, "truth": fam, "variant": vname, "perturbation_rms_rel": pert, "reps": reps,
                                        "caps": {str(c): {"recovered": st["hit"] / reps, "rel_rms_err_median": float(np.median(st["err"])), "rel_rms_err_max": float(np.max(st["err"])),
                                                          "families": st["fam"], "n_coefs_mean": float(np.mean(st["n_coefs"]))} for c, st in stat.items()}})
    out["cap4_equals_cap3_everywhere"] = bool(eq34)
    # --- identifiability of a 3-coefficient edge from 3 temperature levels: how many 3-coefficient families interpolate arbitrary level means exactly?
    gT = G["T"]
    lv = np.array([gT.lo, 0.5 * (gT.lo + gT.hi) + 0.0, gT.hi])             # 23, 35 (middle), 45 C in the geometry's x
    ident = {"levels_x": lv.tolist(), "trials": 400, "exact_fit_counts": {f: 0 for f in ("linear", "log", "quadratic", "power", "exponential", "arrhenius", "hinge")}, "n_families_exact_hist": {}}
    for _ in range(400):
        yl = rng.normal(size=3)                                              # arbitrary level means (data identify nothing more than these)
        yl = yl - yl.mean()
        sc = float(np.ptp(yl))
        n_ex = 0
        for f in ident["exact_fit_counts"]:
            th, rss = S.fit_family(f, gT, lv, yl)
            ok = rss < (1e-4 * sc) ** 2
            ident["exact_fit_counts"][f] += int(ok)
            n_ex += int(ok and S.N_COEFS[f] == 3)
        ident["n_families_exact_hist"][str(n_ex)] = ident["n_families_exact_hist"].get(str(n_ex), 0) + 1
    out["identifiability_3_levels"] = ident
    # --- 1/T: the cap-2 cost of the textbook Arrhenius form in a log-rate (power q = -1) on the 23-45 C hull
    xT = np.linspace(gT.lo, gT.hi, S.G_GRID)
    y_arr = S.eval_family("power", gT, [1.0, -1.0, 0.0], xT)
    f2, f3 = S.choose_family(gT, xT, y_arr, 2, 1e-12), S.choose_family(gT, xT, y_arr, 3, 1e-12)
    out["one_over_T"] = {"cap2_family": f2.family, "cap2_rel_rms_err": rel(S.eval_family(f2.family, gT, f2.theta, xT), y_arr),
                         "cap3_family": f3.family, "cap3_rel_rms_err": rel(S.eval_family(f3.family, gT, f3.theta, xT), y_arr)}
    # --- cap 1 and 0 are degenerate: everything pruned
    y = S.eval_family("linear", gT, [1.0, 0.0], xT)
    out["cap1_family_on_a_linear_edge"] = S.choose_family(gT, xT, y, 1, 1e-3).family
    out["cap0_family_on_a_linear_edge"] = S.choose_family(gT, xT, y, 0, 1e-3).family
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "edge_study.json"), "w", encoding="utf8"), indent=1)
    return out


if __name__ == "__main__":
    o = run()
    print("cap4 == cap3 everywhere:", o["cap4_equals_cap3_everywhere"], "| cap1/cap0 on a linear edge:", o["cap1_family_on_a_linear_edge"], o["cap0_family_on_a_linear_edge"])
    print("1/T:", o["one_over_T"])
    print("identifiability (3 levels):", o["identifiability_3_levels"]["exact_fit_counts"], o["identifiability_3_levels"]["n_families_exact_hist"])
    for r in o["rows"]:
        if r["perturbation_rms_rel"] == 0.0:
            c2, c3 = r["caps"]["2"], r["caps"]["3"]
            print(f"{r['edge']:5s} {r['truth']:11s} {r['variant']:9s} cap2 {list(c2['families'])[0]:11s} err {c2['rel_rms_err_median']:.4f} | cap3 {list(c3['families'])[0]:11s} err {c3['rel_rms_err_median']:.4f}")
