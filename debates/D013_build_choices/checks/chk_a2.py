import os, sys, json
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
ROOT = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
sys.path.insert(0, ROOT + r"\code")
import numpy as np, torch
torch.set_num_threads(1)
from pinnkan import synth, metrics, hard
from pinnkan.data import WindowRule, prepare_many
from pinnkan.specs import SPECS
from pinnkan.law import batch_from_cells
spec = SPECS["synthetic"]
S = synth.make_synthetic("G0", 32, 19, 3, 0)
tr, te = synth.split_conditions(S.cells, 0.25, 0)
prep = prepare_many(te, WindowRule.for_spec(spec))
b = batch_from_cells(spec, tr)
def fit(hp, seed, clip, backbone, steps=1200, lr=0.02):
    torch.manual_seed(seed)
    m = hard.HardODE(spec, hard.make_law(spec, b, hp, backbone), b.C, backbone)
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=lr * 0.05)
    n_ = []
    for _ in range(steps):
        opt.zero_grad(set_to_none=True)
        L = m.loss(b, float(hp["l2"]), float(hp["sparsity"])); L.backward()
        n_.append(float(torch.nn.utils.clip_grad_norm_(m.parameters(), clip if clip else 1e12)))
        opt.step(); sch.step()
    return m, np.array(n_)
for hp in [dict(map="kan", h=4, grid=5, l2=1e-4, sparsity=0.0), dict(map="kan", h=8, grid=12, l2=1e-5, sparsity=0.0), dict(map="kan", h=2, grid=3, l2=1e-2, sparsity=1e-2)]:
    for bb in ("self_limiting", "constant"):
        for clip in (None, 20.0):
            m, n = fit(hp, 0, clip, bb)
            preds, _ = hard.predict_hard(m, spec, [p.win for p in prep])
            sc = metrics.primary_score(metrics.score_prepared(preds, prep))
            print(json.dumps(dict(hp=hp, bb=bb, clip=clip, forecast_pp=sc, frac_over20=float((n > 20).mean()), med_norm=float(np.median(n)), max_norm=float(n.max()))), flush=True)
