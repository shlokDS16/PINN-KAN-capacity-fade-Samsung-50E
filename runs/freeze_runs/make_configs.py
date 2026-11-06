"""Configs of the freeze-commit runs (PREREG_v4 17.1 FB-8, FB-9, FB-10; lead, 2026-11-06). Not confirmatory, not pinned.
FB-8: blinded Samsung timing on the PRIMARY confirmatory configs (zyk throughput, tournament backbone, k grid), folds 0-4, m 32 and 8.
FB-9: nc1_full on synthetic G2 data with the grid paths (k grid, m 8 and 32, A15/G15 included).
FB-10: the build_v1 smoke configs (ISU, SNL) without the arms Design R2 refuses (A3, A7)."""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "runs", "freeze_runs", "configs")
os.makedirs(OUT, exist_ok=True)
CONF = os.path.join(ROOT, "runs", "prereg", "confirmatory_configs")


def write(name, cfg):
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf8", newline="\n") as fh:
        json.dump(cfg, fh, indent=1)


for f in range(5):
    for m in (32, 8):
        c = json.load(open(os.path.join(CONF, f"conf_samsung_B_f{f}_m{m}.json"), encoding="utf8"))
        c.update({"run_id": f"fb8_timing_samsung_B_f{f}_m{m}", "mode": "timing"})
        write(c["run_id"], c)

for m in (8, 32):
    write(f"fb9_nc1_full_synth_m{m}", {"run_id": f"fb9_nc1_full_synth_m{m}", "dataset": "synthetic", "mode": "nc1_full", "m": m, "k": "grid",
                                        "n_trials": 2, "inner_k": 2, "steps_scale": 0.15, "seeds": [0, 1, 2], "backbone": "tournament", "test": "B",
                                        "arms": ["A1", "A2", "A9", "A10", "A12", "A15", "G15", "R1", "R2"],
                                        "synthetic": {"kind": "G2", "n_cyc_cond": 40, "n_sto_cond": 19, "reps": 3, "seed": 31, "test_frac": 0.2}})

write("fb10_smoke_isu_B0", {"run_id": "fb10_smoke_isu_B0", "dataset": "isu", "test": "B", "fold": 0, "mode": "inner",
                            "arms": ["R1", "R2", "A10", "A12", "A2", "A9", "A4", "A1"], "n_trials": 2, "inner_k": 2, "steps_scale": 0.3,
                            "backbone": "self_limiting", "refit_timing": True})
write("fb10_smoke_snl_B0", {"run_id": "fb10_smoke_snl_B0", "dataset": "snl", "test": "B", "fold": 0, "mode": "inner",
                            "arms": ["R1", "R2", "A10", "A11", "A12", "A2", "A9", "A5", "A1"], "n_trials": 2, "inner_k": 2, "steps_scale": 0.3,
                            "backbone": "self_limiting", "refit_timing": True})
print(sorted(os.listdir(OUT)))
