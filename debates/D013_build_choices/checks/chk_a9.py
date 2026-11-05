import os, sys, json, time
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
ROOT = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
sys.path.insert(0, ROOT + r"\code")
import numpy as np, torch
torch.set_num_threads(1)
from pinnkan import synth, pinn, metrics
from pinnkan.pinn import DataOnlyF, SIGMA, predict_data_only
from pinnkan.data import WindowRule, prepare_many
from pinnkan.specs import SPECS
from pinnkan.law import batch_from_cells
spec = SPECS["synthetic"]
S = synth.make_synthetic("G0", 32, 19, 3, 0)
tr, te = synth.split_conditions(S.cells, 0.25, 0)
prep = prepare_many(te, WindowRule.for_spec(spec))
b = batch_from_cells(spec, tr)
def fit(hp, seed, clip, steps=1500, lr=5e-3):
    torch.manual_seed(seed)
    m = DataOnlyF(spec, b.C, int(hp["width"]), int(hp["depth"]), int(hp["zdim"]))
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=lr * 0.1)
    norms = []
    for _ in range(steps):
        opt.zero_grad(set_to_none=True)
        r = m.F(b.obs_t, b.s[b.obs_cell], m.z[b.obs_cell]) - b.obs_y
        n = r.numel()
        ((r ** 2).mean() / SIGMA ** 2 + (m.z ** 2).sum() / n + float(hp["wd"]) * m.weight_l2()).backward()
        norms.append(float(torch.nn.utils.clip_grad_norm_(m.parameters(), clip if clip else 1e12)))
        opt.step(); sch.step()
    return m, np.array(norms)
for hp in [dict(width=32, depth=3, zdim=2, wd=1e-4), dict(width=128, depth=4, zdim=3, wd=1e-5), dict(width=16, depth=2, zdim=1, wd=1e-2), dict(width=64, depth=3, zdim=2, wd=1e-3)]:
    for seed in (0, 1):
        for clip in (None, 20.0):
            m, n = fit(hp, seed, clip)
            sc = metrics.primary_score(metrics.score_prepared(predict_data_only(m, spec, [p.win for p in prep]), prep))
            print(json.dumps(dict(hp=hp, seed=seed, clip=clip, forecast_pp=sc, frac_over20=float((n > 20).mean()), med_norm=float(np.median(n)), max_norm=float(n.max()))), flush=True)
