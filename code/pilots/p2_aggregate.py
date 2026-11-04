"""Aggregate runs/pilot_P2/raw/*.json into summary.json and summary.md (mean, min, max over seeds)."""
import glob
import json
import os
import statistics as st
import sys

root = sys.argv[1]
rows = [json.load(open(p, encoding="utf8")) for p in sorted(glob.glob(os.path.join(root, "runs", "pilot_P2", "raw", "*.json")))]
groups = {}
for r in rows:
    key = (r["model"], r["variant"], r.get("m_obs", 80), r["threads"])
    groups.setdefault(key, []).append(r)
out = []
for (m, v, mo, th), rs in sorted(groups.items()):
    f = [r["fit_seconds"] for r in rs]
    out.append({"model": m, "variant": v, "m_obs": mo, "threads": th, "n_runs": len(rs), "fit_s_mean": st.mean(f),
                "fit_s_min": min(f), "fit_s_max": max(f), "ms_per_step": 1000 * st.mean(f) / rs[0]["steps"],
                "peak_ws_mb_max": max(r["peak_working_set_mb"] for r in rs), "n_params": rs[0]["n_params"],
                "n_cells": rs[0]["data_info"]["n_cells"], "n_obs": rs[0]["data_info"]["n_obs"], "all_finite": all(r["all_finite"] for r in rs),
                "cpu_pct_before_max": max(r["system_cpu_percent_before"] for r in rs)})
json.dump(out, open(os.path.join(root, "runs", "pilot_P2", "summary.json"), "w"), indent=1)
lines = ["| model | variant | obs/cell | threads | runs | cells | obs pts | fit s mean (min-max) | ms/step | peak RAM MB |", "|---|---|---|---|---|---|---|---|---|---|"]
for o in out:
    lines.append(f"| {o['model']} | {o['variant']} | {o['m_obs'] if o['variant'] != 'fullcycle' else 'all'} | {o['threads']} | {o['n_runs']} | {o['n_cells']} | {o['n_obs']} | {o['fit_s_mean']:.1f} ({o['fit_s_min']:.1f}-{o['fit_s_max']:.1f}) | {o['ms_per_step']:.1f} | {o['peak_ws_mb_max']:.0f} |")
open(os.path.join(root, "runs", "pilot_P2", "summary.md"), "w", encoding="utf8").write("\n".join(lines) + "\n")
print("\n".join(lines))
