"""P2: one timed fit (hard ODE or PINN) on SNL, CPU only. One process per measurement so peak RAM is clean.

python code/pilots/p2_timing_run.py --root <ROOT> --model {hard,pinn} --threads N --variant {base,scale279,fullcycle}
       --steps 2000 --seed S --out <json>
Timing pilot: the loss values written are finiteness / sanity checks, NOT accuracy results (no test split exists).
"""
import argparse
import json
import os
import sys
import time

os.environ["CUDA_VISIBLE_DEVICES"] = ""  # CPU only, never touch the GPU
ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--model", choices=["hard", "pinn"], required=True)
ap.add_argument("--threads", type=int, required=True)
ap.add_argument("--variant", choices=["base", "scale279", "fullcycle"], default="base")
ap.add_argument("--steps", type=int, default=2000)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--lr", type=float, default=5e-3)
ap.add_argument("--out", required=True)
a = ap.parse_args()
os.environ["OMP_NUM_THREADS"] = str(a.threads)
os.environ["MKL_NUM_THREADS"] = str(a.threads)
sys.path.insert(0, os.path.join(a.root, "code"))
sys.path.append(os.path.join(os.environ.get("APPDATA", ""), "Python", "Python314", "site-packages"))

import psutil  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(a.threads)
torch.set_num_interop_threads(1)
assert not torch.cuda.is_available() or os.environ["CUDA_VISIBLE_DEVICES"] == ""
from data.snl_pilot_data import build_fit_data  # noqa: E402
from models.ageing_models import HardODE, PINN  # noqa: E402

torch.manual_seed(a.seed)
t_load = time.perf_counter()
kw = {"base": {}, "scale279": {"tile_to": 279}, "fullcycle": {"per_cycle_all": True}}[a.variant]
if a.model == "hard" and a.variant == "fullcycle":
    sys.exit("hard-ODE full per-cycle variant is not defined (one RK4 node per cycle = ~1500 sequential steps); not run")
d, info = build_fit_data(a.root, seed=a.seed, **kw)
t_load = time.perf_counter() - t_load
C = info["n_cells"]
model = HardODE(C) if a.model == "hard" else PINN(C)
opt = torch.optim.Adam(model.parameters(), lr=a.lr)
gen = torch.Generator().manual_seed(a.seed)
proc = psutil.Process()
cpu_before = psutil.cpu_percent(interval=0.5)
losses = []
t0 = time.perf_counter()
for step in range(a.steps):
    opt.zero_grad(set_to_none=True)
    out = model.loss(d) if a.model == "hard" else model.loss(d, gen)
    out[0].backward()
    opt.step()
    if step in (0, a.steps // 2, a.steps - 1):
        losses.append((step, float(out[0].detach()), float(out[1].detach())))
fit_s = time.perf_counter() - t0
mi = proc.memory_info()
res = {
    "model": a.model, "variant": a.variant, "threads": a.threads, "steps": a.steps, "seed": a.seed, "lr": a.lr,
    "fit_seconds": fit_s, "seconds_per_step": fit_s / a.steps, "data_build_seconds": t_load,
    "peak_working_set_mb": getattr(mi, "peak_wset", float("nan")) / 1e6,
    "peak_pagefile_mb": getattr(mi, "peak_pagefile", float("nan")) / 1e6,
    "n_params": sum(p.numel() for p in model.parameters()),
    "loss_total_data_at_steps": losses, "all_finite": all(map(lambda x: x[1] == x[1] and x[1] < 1e9, losses)),
    "system_cpu_percent_before": cpu_before, "torch": torch.__version__, "num_threads_effective": torch.get_num_threads(),
    "data_info": info,
}
os.makedirs(os.path.dirname(a.out), exist_ok=True)
with open(a.out, "w", encoding="utf8") as fh:
    json.dump(res, fh, indent=1)
print(json.dumps({k: res[k] for k in ("model", "variant", "threads", "fit_seconds", "peak_working_set_mb", "loss_total_data_at_steps", "system_cpu_percent_before")}))
