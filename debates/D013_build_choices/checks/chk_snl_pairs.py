import os, sys, json, dataclasses, time
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
ROOT = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
sys.path.insert(0, ROOT + r"\code")
import numpy as np, torch
torch.set_num_threads(1)
from pinnkan import tuning, metrics
from pinnkan.data import load_split, WindowRule
from pinnkan.specs import SNL
from pinnkan.arms import default_hp
fold = int(sys.argv[1])
D = load_split("snl", "B", fold, role="train")
train = D.train
rule = WindowRule.for_spec(SNL)
pairs = {
  "builder(T-ch,T-DoD,DoD-dch)": SNL.interaction_pairs,
  "design_rule(T-dch + flags x T + flags x dch)": (("temp_c", "discharge_c"),) + tuple((f, "temp_c") for f in ("is_LFP", "is_NCA", "is_NMC")) + tuple((f, "discharge_c") for f in ("is_LFP", "is_NCA", "is_NMC")),
  "T-dch only": (("temp_c", "discharge_c"),),
}
res = []
for seed in (1000, 1001):
    fold_of = tuning.inner_folds(train, 3, seed, SNL, "cycling")
    ctx = {"backbone": "self_limiting", "steps_scale": 1.0, "rule": rule, "extra_twin_raw": None, "oracle": False, "per_cell_factor": True}
    cfgs = [("A4 additive", "A4", SNL, {})]
    for name, pr in pairs.items():
        cfgs.append((f"A5 {name}", "A5", dataclasses.replace(SNL, interaction_pairs=pr), {}))
    cfgs.append(("A1 KAN h4", "A1", SNL, {}))
    for label, arm, spec, extra in cfgs:
        hp = dict(default_hp(arm), **extra)
        t0 = time.time()
        rows, secs = tuning.cv_rows(arm, hp, train, fold_of, 3, spec, rule, seed, ctx, "cycling")
        cs = metrics.condition_scores(rows)
        r = dict(fold=fold, seed=seed, cfg=label, inner_cv_pp=metrics.primary_score(rows), n_cond=len(cs), sec=time.time() - t0)
        print(json.dumps(r), flush=True)
