"""D022 (KAN part): applies debates/D022_datasets_kan/kan_study_rule.md to runs/D022_kan_synth/kan_p*.jsonl -> decision.json
    .venv/Scripts/python.exe -P code/prereg/d022_kan_decide.py"""
import glob
import json
import math
import os
import sys
import zlib

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
from pinnkan.symbolic import N_COEFS  # noqa: E402

OUT = os.path.join(ROOT, "runs", "D022_kan_synth")
LINEAR = ("T_C", "dod", "c_ch", "c_dch")
VARS = ("B", "M", "L", "ML")
ARMS = ("KAN", "GAM")


def ub(x, label, q=95):
    x = np.asarray(x, float)
    rng = np.random.default_rng(np.random.SeedSequence([20261105, zlib.crc32(label.encode())]))
    return float(np.percentile(x[rng.integers(0, len(x), (10000, len(x)))].mean(1), q))


def main():
    recs = [json.loads(l) for f in sorted(glob.glob(os.path.join(OUT, "kan_p*.jsonl"))) for l in open(f, encoding="utf8") if l.strip()]
    by = {}
    for r in recs:
        by.setdefault(r["seed"], {})[(r["kind"], r["m"], r["variant"], r["arm"])] = r
    need = {(k, m, v, a) for k in ("G0", "G2", "G3") for m in (32, 8) for v in VARS for a in ARMS}
    seeds = sorted(s for s, d in by.items() if need <= set(d) and all("error" not in d[k] for k in need))
    res = {"rule": "debates/D022_datasets_kan/kan_study_rule.md", "seeds_complete": seeds, "n_seeds": len(seeds),
           "errors": [r for r in recs if "error" in r][:5], "n_errors": sum("error" in r for r in recs)}
    if len(seeds) < 3:
        print("fewer than 3 complete seed groups", seeds, res["n_errors"])
        return
    g = lambda s, k, m, v, a: by[s][(k, m, v, a)]

    def diff(key_a, v_a, key_b, v_b, kinds, m, label):
        """per-seed paired difference, mean over arms and kinds"""
        d = [float(np.mean([g(s, k, m, v_a, a)[key_a] - g(s, k, m, v_b, a)[key_b] for k in kinds for a in ARMS])) for s in seeds]
        return {"mean": float(np.mean(d)), "ub95": ub(d, label), "per_seed": d}
    R = {}
    # M
    R["M1_G0G2_m8"] = diff("E_par", "M", "E_par", "B", ("G0", "G2"), 8, "D022|M1")
    R["M2_G3_m32"] = diff("E_par", "M", "E_par", "B", ("G3",), 32, "D022|M2a")
    R["M2_G3_m8"] = diff("E_par", "M", "E_par", "B", ("G3",), 8, "D022|M2b")
    adopt_M = bool(R["M1_G0G2_m8"]["ub95"] < 0 and R["M2_G3_m32"]["ub95"] <= 0.02 and R["M2_G3_m8"]["ub95"] <= 0.02)
    # L
    def fs(v, cap="3", m=32):
        n = f = 0
        for s in seeds:
            for a in ARMS:
                fam = g(s, "G0", m, v, a)[f"fam{cap}"]
                for nm in LINEAR:
                    n += 1
                    f += int(N_COEFS[fam[nm][0]] == 3)
        return f / n
    R["L1_false_structure_cap3_G0_m32"] = {v: fs(v) for v in VARS}
    R["false_structure_cap3_G0_m8"] = {v: fs(v, m=8) for v in VARS}
    R["false_structure_cap2_G0_m32"] = {v: fs(v, "2") for v in VARS}
    for v_ in ("L", "ML"):
        R[f"L2_{v_}_G0G3_m32"] = diff("E_ext3", v_, "E_ext2", "B", ("G0", "G3"), 32, f"D022|L2|{v_}")
        R[f"L3_{v_}_G3_m32"] = diff("E_ext3", v_, "E_ext2", "B", ("G3",), 32, f"D022|L3|{v_}")
        R[f"L4_{v_}_G0G2G3_m32"] = diff("E_par", v_, "E_par", "B", ("G0", "G2", "G3"), 32, f"D022|L4|{v_}")
    adopt_L = bool(R["L1_false_structure_cap3_G0_m32"]["L"] <= 0.25 and R["L2_L_G0G3_m32"]["ub95"] <= 0.01 and R["L3_L_G3_m32"]["mean"] <= -0.005 and R["L4_L_G0G2G3_m32"]["ub95"] <= 0.01)
    # ML
    adopt_ML = False
    if adopt_M and adopt_L:
        ok = True
        for m in (32, 8):
            best_par = min(("M", "L"), key=lambda v: np.mean([g(s, k, m, v, a)["E_par"] for s in seeds for k in ("G0", "G2", "G3") for a in ARMS]))
            best_ext = min(("M", "L"), key=lambda v: np.mean([g(s, k, m, v, a)["E_ext3"] for s in seeds for k in ("G0", "G2", "G3") for a in ARMS]))
            d1 = diff("E_par", "ML", "E_par", best_par, ("G0", "G2", "G3"), m, f"D022|ML1|{m}")
            d2 = diff("E_ext3", "ML", "E_ext3", best_ext, ("G0", "G2", "G3"), m, f"D022|ML2|{m}")
            R[f"ML_vs_best_m{m}"] = {"par": d1, "ext3": d2}
            ok &= d1["ub95"] <= 0.01 and d2["ub95"] <= 0.01
        adopt_ML = bool(ok)
    res.update(R)
    res["adopt"] = {"M": adopt_M, "L": adopt_L, "ML": adopt_ML}
    res["recommendation"] = "ML" if adopt_ML else ("M" if adopt_M and not adopt_L else ("L" if adopt_L and not adopt_M else ("M and L adopted singly, ML not" if adopt_M and adopt_L else "none")))
    # descriptive table: medians of E_par, E_ext2, E_ext3 by (kind, m, variant), mean of arms
    tab = {}
    for k in ("G0", "G2", "G3"):
        for m in (32, 8):
            for v in VARS:
                row = {}
                for key in ("E_par", "E_test", "E_ext2", "E_ext3", "n_coefs_cyc2", "n_coefs_cyc3"):
                    row[key] = float(np.mean([g(s, k, m, v, a)[key] for s in seeds for a in ARMS]))
                row["mono_violation_T_dod_cch"] = [float(np.mean([g(s, k, m, v, a)["mono_violation_T_dod_cch"][i] for s in seeds for a in ARMS])) for i in range(3)]
                tab[f"{k}_m{m}_{v}"] = row
    res["table"] = tab
    # A15/G15 asymmetry (KAN minus GAM) per variant on G0, descriptive
    res["kan_minus_gam_E_ext2_G0_m32"] = {v: float(np.mean([g(s, "G0", 32, v, "KAN")["E_ext2"] - g(s, "G0", 32, v, "GAM")["E_ext2"] for s in seeds])) for v in VARS}
    res["kan_minus_gam_E_par_G0_m32"] = {v: float(np.mean([g(s, "G0", 32, v, "KAN")["E_par"] - g(s, "G0", 32, v, "GAM")["E_par"] for s in seeds])) for v in VARS}
    json.dump(res, open(os.path.join(OUT, "decision.json"), "w", encoding="utf8"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "table"}, indent=1)[:6000])
    for k, v in tab.items():
        print(k, {a: (round(b, 3) if not isinstance(b, list) else [round(x, 2) for x in b]) for a, b in v.items()})


if __name__ == "__main__":
    main()
