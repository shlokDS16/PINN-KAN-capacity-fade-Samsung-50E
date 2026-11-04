"""P5 sensitivity (post hoc, NOT used for selection): PINN at fixed lambda_res values outside / at the edge of the tuned grid, refit on all training
conditions of each draw, forecast on the same held-out conditions.  Shows whether the edge optimum (lambda = 1.0 chosen in several draws) matters.
python -P code/pilots/p5_lambda_sensitivity.py --lams 10 --out runs/pilot_P5"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p5_hard_vs_soft import *  # noqa: F401,F403,E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lams", default="10")
    ap.add_argument("--draws", default="0,1,2,3,4")
    ap.add_argument("--out", default=os.path.join(ROOT, "runs", "pilot_P5"))
    a = ap.parse_args()
    out = {"git": PC.git_info(), "note": "post-hoc sensitivity on the held-out conditions; lambda NOT selected from these numbers", "rows": []}
    design = SG.Design(ROOT)
    for dr in [int(x) for x in a.draws.split(",")]:
        ds = SG.make_dataset("G1", dr, design)
        test_conds = SG.split_conditions(dr)
        train_conds = np.setdiff1d(np.arange(design.n_cond), test_conds)
        tr_cells = PC.cells_of(design, train_conds)
        ev_cells = PC.scoring_cells(design, PC.cells_of(design, test_conds))
        for variant in ("record_end", "whole_axis"):
            for lam in [float(x) for x in a.lams.split(",")]:
                m, de, fm, pr = pinn_fit_and_forecast(design, ds, tr_cells, ev_cells, lam, variant, seed=1000 * dr + 99)
                row = {"draw": dr, "variant": variant, "lambda_res": lam, "forecast_rmse_pp_cell_cond_mean": score(pr, de, fm), "train_rmse_pp": float(np.sqrt(m.train_data_mse) * 10)}
                out["rows"].append(row)
                print(row, flush=True)
    PC.save_json(out, os.path.join(a.out, "sens_lambda_" + a.lams.replace(",", "_") + ".json"))
