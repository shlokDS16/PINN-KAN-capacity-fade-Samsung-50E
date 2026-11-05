"""D021: applies the decision rule of debates/D021_cap/study_rule.md to runs/D021_cap_synth/pipeline_p*.jsonl. Writes runs/D021_cap_synth/decision.json and prints a summary.
    .venv/Scripts/python.exe -P code/prereg/d021_cap_decide.py"""
import glob
import json
import os
import sys
import zlib

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
from pinnkan.symbolic import N_COEFS  # noqa: E402

OUT = os.path.join(ROOT, "runs", "D021_cap_synth")
HARM_32, HARM_8, SYM = 0.02, 0.05, 0.02
ARMS = ("A15h1", "A15h2", "G15")
LINEAR = ("T_C", "dod", "c_ch", "c_dch")


def boot_ub(x, label, q=95, draws=10000):
    x = np.asarray(x, float)
    rng = np.random.default_rng(np.random.SeedSequence([20261105, zlib.crc32(label.encode())]))
    means = x[rng.integers(0, len(x), (draws, len(x)))].mean(1)
    return float(np.percentile(means, q)), float(np.percentile(means, 100 - q))


def load():
    recs = []
    for f in sorted(glob.glob(os.path.join(OUT, "pipeline_p*.jsonl"))):
        recs += [json.loads(l) for l in open(f, encoding="utf8") if l.strip()]
    by = {}
    for r in recs:
        by.setdefault(r["seed"], {})[(r["kind"], r["m"], r["arm"])] = r
    need = {(k, m, a) for k in ("G0", "G2") for m in (32, 8) for a in ARMS}
    complete = sorted(s for s, d in by.items() if need <= set(d))
    return by, complete


def main():
    by, seeds = load()
    res = {"seeds_complete": seeds, "n_seeds": len(seeds), "rule": "debates/D021_cap/study_rule.md"}
    if len(seeds) < 3:
        print("fewer than 3 complete seed groups: no decision", seeds)
        return
    g = lambda s, k, m, a: by[s][(k, m, a)]
    # D0
    res["D0_cap4_equals_cap3"] = all(g(s, k, m, a)["cap4_equals_cap3"] for s in seeds for k in ("G0", "G2") for m in (32, 8) for a in ARMS)
    # D2: harm of cap 3 against cap 2
    res["D2"] = {}
    for m, thr in ((32, HARM_32), (8, HARM_8)):
        for k in ("G0", "G2"):
            d = [float(np.mean([g(s, k, m, a)["caps"]["3"]["E_law"] - g(s, k, m, a)["caps"]["2"]["E_law"] for a in ARMS])) for s in seeds]
            ub, lb = boot_ub(d, f"D021|harm|{k}|{m}")
            res["D2"][f"{k}_m{m}"] = {"mean_diff_E3_minus_E2": float(np.mean(d)), "ub95": ub, "lb95": lb, "threshold": thr, "harmful": bool(ub > thr),
                                      "per_arm_mean": {a: float(np.mean([g(s, k, m, a)["caps"]["3"]["E_law"] - g(s, k, m, a)["caps"]["2"]["E_law"] for s in seeds])) for a in ARMS}}
    harmful32 = [k for k in ("G0", "G2") if res["D2"][f"{k}_m32"]["harmful"]]
    res["D3_verdict_cap"] = 2 if harmful32 else 3
    res["D3_harmful_kinds_m32"] = harmful32
    chosen = str(res["D3_verdict_cap"])
    other = "2" if chosen == "3" else "3"
    # D4
    res["D4a_m8_limitation"] = [k for k in ("G0", "G2") if res["D2"][f"{k}_m8"]["harmful"]]
    sym = {}
    for cap in ("2", "3"):
        for m in (32, 8):
            d = [g(s, "G0", m, "A15h1")["caps"][cap]["E_law"] - g(s, "G0", m, "G15")["caps"][cap]["E_law"] for s in seeds]
            ub, lb = boot_ub(d, f"D021|sym|{cap}|{m}")
            sym[f"cap{cap}_m{m}"] = {"mean_A15h1_minus_G15": float(np.mean(d)), "ci90": [lb, ub], "within_0.02": bool(abs(np.mean(d)) <= SYM)}
    res["D4b_symmetry_G0"] = sym
    fs = {}
    for cap in ("2", "3"):
        for m in (32, 8):
            for arm in ("A15h1", "G15"):
                cnt = {"n": 0, "false_structure": 0, "false_prune": 0}
                T = {"n": 0, "false_structure": 0, "false_prune": 0}
                for s in seeds:
                    fam = g(s, "G0", m, arm)["caps"][cap]["families_first_layer"]
                    for nm in LINEAR:
                        f = fam[nm][0]
                        for tgt in ([cnt, T] if nm == "T_C" else [cnt]):
                            tgt["n"] += 1
                            tgt["false_structure"] += int(N_COEFS[f] == 3)
                            tgt["false_prune"] += int(f == "zero")
                fs[f"cap{cap}_m{m}_{arm}"] = {"all_linear_inputs": cnt, "T_only": T}
    res["D4c_false_structure_G0"] = fs
    # descriptive table
    tab = {}
    for k in ("G0", "G2"):
        for m in (32, 8):
            for a in ARMS:
                row = {"parent_E_law_median": float(np.median([g(s, k, m, a)["parent_E_law"] for s in seeds]))}
                for cap in ("2", "3"):
                    for key in ("E_law", "E_test", "forecast_rmse_pp", "n_coefs", "n_coefs_cyc"):
                        v = [g(s, k, m, a)["caps"][cap][key] for s in seeds]
                        row[f"cap{cap}_{key}_median"] = float(np.nanmedian(v))
                        row[f"cap{cap}_{key}_mean"] = float(np.nanmean(v))
                    row[f"cap{cap}_E_extracted_median"] = float(np.median([g(s, k, m, a)["caps"][cap]["E_law_extracted"] for s in seeds]))
                row["n_train_cyc_conditions"] = int(g(seeds[0], k, m, a)["n_train_cyc_conditions"])
                tab[f"{k}_m{m}_{a}"] = row
    res["table"] = tab
    json.dump(res, open(os.path.join(OUT, "decision.json"), "w", encoding="utf8"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("table", "D4c_false_structure_G0")}, indent=1))
    for k, v in tab.items():
        print(k, {a: round(b, 4) for a, b in v.items()})
    for k, v in fs.items():
        print(k, v)


if __name__ == "__main__":
    main()
