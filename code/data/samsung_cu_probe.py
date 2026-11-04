"""P0 probe: integrate current per step of Samsung 50E check-up (CU) files to find the capacity test.

Usage: python -I code/data/samsung_cu_probe.py <CU.csv> [...]
"""
import os, sys
import numpy as np
import pandas as pd

for f in sys.argv[1:]:
    d = pd.read_csv(f)
    t = pd.to_timedelta(d.run_time).dt.total_seconds().to_numpy()
    d["ah"] = d.c_cur * np.diff(t, prepend=t[0]) / 3600.0
    d["t"] = t
    seg = (d.step_type != d.step_type.shift()).cumsum()
    g = d.groupby(seg).agg(step=("step_type", "first"), t0=("t", "first"), t1=("t", "last"),
                           ah=("ah", "sum"), imean=("c_cur", "mean"), vmin=("c_vol", "min"),
                           vmax=("c_vol", "max"))
    g["hours"] = (g.t1 - g.t0) / 3600
    print(os.path.basename(f), "rows", len(d), "total hours", round(t[-1] / 3600, 2))
    print(g.loc[g.ah.abs() > 0.05, ["step", "hours", "ah", "imean", "vmin", "vmax"]].round(4).to_string())
