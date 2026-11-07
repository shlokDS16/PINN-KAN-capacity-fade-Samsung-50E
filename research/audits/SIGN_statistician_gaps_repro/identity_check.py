"""Statistician check for row (s): with neutralisation OFF, does a single-window A1-only run reproduce A1 of a multi-arm k-grid run at k_full exactly
(the pairing assumption of NC-2 and row (s))? Then: neutralisation ON changes A1. Synthetic G2 data only. argv: runs_dir design"""
import json, os, sys
os.environ["CUDA_VISIBLE_DEVICES"] = ""; os.environ["OMP_NUM_THREADS"] = "1"
sys.path.insert(0, r"C:\Users\Shlok\Downloads\PINN KAN battery paper\code")
import torch
torch.set_num_threads(1)
from pinnkan import run
R, design = sys.argv[1], sys.argv[2]
base = {"design": design, "dataset": "synthetic", "mode": "confirmatory", "n_trials": 2, "inner_k": 2, "steps_scale": 0.04, "seeds": [0, 1], "backbone": "self_limiting",
        "synthetic": {"kind": "G2", "n_cyc_cond": 16, "n_sto_cond": 8, "reps": 2, "seed": 7}, "test": "B"}
extra = {"k": "grid"} if design == "R2" else {}
run.run({**base, **extra, "arms": ["A1", "R1", "A9"], "run_id": "GRID"}, runs_dir=R)
run.run({**base, "arms": ["A1"], "run_id": "SINGLE"}, runs_dir=R)
run.run({**base, "arms": ["A1"], "run_id": "CRATE", "neutralise_stress": ["C_ch", "C_dch"]}, runs_dir=R)
ld = lambda rid: json.load(open(os.path.join(R, rid, "condition_scores.json")))["A1"]
g, s, c = ld("GRID"), ld("SINGLE"), ld("CRATE")
print("conditions equal:", set(g) == set(s) == set(c), len(g))
print("max |GRID - SINGLE| (A1, primary k):", max(abs(g[k] - s[k]) for k in g))
print("max |CRATE - SINGLE|:", max(abs(c[k] - s[k]) for k in g))
