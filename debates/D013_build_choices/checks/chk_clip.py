import os, sys, json, time
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
ROOT = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
sys.path.insert(0, ROOT + r"\code")
import numpy as np, torch
torch.set_num_threads(1)
from pinnkan import synth, pinn, metrics
from pinnkan.data import WindowRule, prepare_many
from pinnkan.specs import SPECS
from pinnkan.arms import default_hp

lams = [float(x) for x in sys.argv[1].split(",")]
seedset = [0]
spec = SPECS["synthetic"]
S = synth.make_synthetic("G0", 32, 19, 3, 0)
tr, te = synth.split_conditions(S.cells, 0.25, 0)
rule = WindowRule.for_spec(spec)
prep = prepare_many(te, rule)
from pinnkan.law import batch_from_cells
b = batch_from_cells(spec, tr)
# record grad norms
norms = []
orig = torch.nn.utils.clip_grad_norm_
def rec(params, max_norm, *a, **k):
    n = orig(params, max_norm, *a, **k)
    norms.append(float(n)); return n
pinn.torch.nn.utils.clip_grad_norm_ = rec
configs = {"clip20_w40": dict(clip=20.0, warmup=0.4), "noclip_w40": dict(clip=None, warmup=0.4), "clip20_w0": dict(clip=20.0, warmup=1e-9),
           "noclip_w0": dict(clip=None, warmup=1e-9), "clip50_w40": dict(clip=50.0, warmup=0.4), "clip20_w20": dict(clip=20.0, warmup=0.2), "clip20_w60": dict(clip=20.0, warmup=0.6),
           "clip5_w40": dict(clip=5.0, warmup=0.4)}
out = []
for lam in lams:
    for name, kw in configs.items():
        hp = dict(default_hp("A1"), map="kan", lam_res=lam)
        norms.clear()
        t0 = time.time()
        if kw["clip"] is None:
            # record norms without clipping: temporarily use huge clip
            kw2 = dict(kw, clip=1e12)
        else:
            kw2 = kw
        m = pinn.fit_pinn(b, spec, hp, "self_limiting", 0, steps=2000, **kw2)
        preds, _ = pinn.predict_pinn(m, spec, [p.win for p in prep], lam, 0)
        rows = metrics.score_prepared(preds, prep)
        sc = metrics.primary_score(rows)
        n = np.array(norms)
        rec_ = dict(lam=lam, cfg=name, forecast_pp=sc, data_mse=m.train_data_mse, res=m.train_res_msq, frac_over20=float((n > 20).mean()), max_norm=float(n.max()), med_norm=float(np.median(n)), sec=time.time() - t0)
        print(json.dumps(rec_), flush=True)
        out.append(rec_)
