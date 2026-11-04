"""Graphical abstract (Journal of Energy Storage / Elsevier: >= 1328 x 531 px, readable at 13 x 5.2 cm, landscape).

Left: the design (metadata only: storage and cycling conditions, laboratories); middle: the model in three glyphs (solution network F,
KAN stress maps inside the law G, soft residual); right: the primary contrasts on held-out cycling conditions (median error ratio
comparator / PINN-KAN with its exact 95 % interval and the tier) read from the statistics step. Output size 13 cm x 5.2 cm at 600 dpi
= 3071 x 1228 px.
Inputs: --meta (experiments_meta.csv), --run-b, --run-s2 (condition counts), --contrasts (analysis/contrasts_B.json).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps
import pk_data as pdt
from fig1_schematic import box, arrow, spline_glyph, txt

W, H = 130.0, 52.0
TXT = 7.6


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--run-b", required=True)
    ap.add_argument("--run-s2", required=True)
    ap.add_argument("--contrasts", required=True)
    a = ap.parse_args()
    ps.apply()
    prov = ps.Provenance(a.run_b, a.run_s2, a.contrasts)
    prov.require_frozen("Graphical abstract")
    meta = pd.read_csv(ps.need(a.meta))
    meta.columns = [c.strip() for c in meta.columns]
    nB = len(pdt.load_scores(a.run_b)["A1"])
    nS = len(pdt.load_scores(a.run_s2)["A1"])
    labs = sorted(meta.lab.unique())
    C = pdt.load_contrasts(a.contrasts)["contrasts"]

    fig = plt.figure(figsize=(13.0 * ps.CM, 5.2 * ps.CM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    # titles
    txt(ax, 21, 49.2, "1  Test matrix", size=8.4, fontweight="bold")
    txt(ax, 66, 49.2, "2  PINN-KAN", size=8.4, fontweight="bold")
    txt(ax, 108, 49.2, "3  Held-out conditions", size=8.4, fontweight="bold")
    for x0, x1 in ((0.5, 42), (45, 87), (89.5, 129.5)):
        box(ax, x0, 3.6, x1 - x0, 41.9, "#FAFAFA", r=1.2, lw=0.6)

    # ---- block 1: design glyphs from metadata
    sto = meta[meta.type == "k"]
    cyc = meta[meta.type == "z"]
    axs = fig.add_axes([6.5 / W, 21.5 / H, 15 / W, 15 / H])
    for (T, s, lab), g in sto.groupby(["amb_temp_tp", "soc_max_tp", "lab"]):
        axs.scatter(100 * s, T, s=7, color=ps.LAB_COL[lab], lw=0)
    axs.set_xticks([])
    axs.set_yticks([])
    axs.set_xlabel("SOC", fontsize=7, labelpad=1)
    axs.set_ylabel("T", fontsize=7, labelpad=1)
    axs.set_title(f"storage, {nS}", fontsize=7.4, pad=2)
    axc = fig.add_axes([25.5 / W, 21.5 / H, 15 / W, 15 / H])
    for (T, d, lab), g in cyc.groupby(["amb_temp_tp", "dod_tp", "lab"]):
        axc.scatter(T + np.random.default_rng(int(1000 * d)).uniform(-1.2, 1.2), 100 * d, s=7, color=ps.LAB_COL[lab], lw=0)
    axc.set_xticks([])
    axc.set_yticks([])
    axc.set_xlabel("T", fontsize=7, labelpad=1)
    axc.set_ylabel("DoD", fontsize=7, labelpad=1)
    axc.set_title(f"cycling, {nB}", fontsize=7.4, pad=2)
    txt(ax, 21, 15.6, f"{nS + nB} conditions,", size=TXT)
    txt(ax, 21, 12.0, f"{len(labs)} laboratories", size=TXT)
    for i, lab in enumerate(labs):
        ax.scatter([8.5 + 11 * i], [8.0], s=14, color=ps.LAB_COL[lab], lw=0, zorder=5)
        txt(ax, 10.3 + 11 * i, 8.0, lab, size=7, ha="left")
    # ---- block 2: model glyph
    box(ax, 48, 29.5, 36, 12, "#DCEBF7", r=1.2, lw=0.6)
    txt(ax, 66, 38.6, "Solution net $F$", size=TXT, fontweight="bold")
    xs = np.linspace(53, 79, 5)
    for k, n in enumerate((3, 4, 4, 3, 1)):
        ys = np.linspace(31.2, 36.0, n) if n > 1 else [33.6]
        for y in ys:
            ax.add_patch(plt.Circle((xs[k], y), 0.7, fc="white", ec=ps.BLUE, lw=0.6, zorder=4))
    box(ax, 48, 15.6, 36, 11.6, "#FBE9C6", r=1.2, lw=0.6)
    txt(ax, 66, 24.4, "KAN stress maps", size=TXT, fontweight="bold")
    for i, k in enumerate(("rise", "s", "bump", "sat")):
        spline_glyph(ax, 51.5 + 8.2 * i, 17.0, 6.5, 5.0, k, color=ps.BLUE, lw=0.8)
    box(ax, 48, 5.0, 36, 8.6, "#E6E0F0", r=1.2, lw=0.6)
    txt(ax, 66, 10.7, "Physics residual", size=TXT, fontweight="bold")
    txt(ax, 66, 7.0, "$\\mathrm{d}y/\\mathrm{d}t=G$ (calendar + cycling)", size=7.0)
    arrow(ax, (66, 29.5), (66, 27.2), ms=5, lw=0.8)
    arrow(ax, (66, 15.6), (66, 13.8), ms=5, lw=0.8)
    arrow(ax, (42.4, 24), (47.6, 24), ms=6, lw=0.9)
    # ---- block 3: mini forest
    keys = [("H1a", "Data-only"), ("H1b", "Best map"), ("H6", "Authors'")]
    keys = [(k, l) for k, l in keys if k in C]
    fa = fig.add_axes([107.5 / W, 14.5 / H, 17.0 / W, 19.0 / H])
    fa.patch.set_alpha(0)
    lo_all = min(np.exp(C[k]["median_ci95"][0]) for k, _ in keys)
    hi_all = max(np.exp(C[k]["median_ci95"][1]) for k, _ in keys)
    for i, (k, lab) in enumerate(keys):
        y = len(keys) - 1 - i
        e = C[k]
        lo, hi, m = (np.exp(v) for v in (e["median_ci95"][0], e["median_ci95"][1], e["median_L"]))
        fa.plot([lo, hi], [y, y], color=ps.BLUE, lw=1.6)
        fa.plot([m], [y], "o", color=ps.BLUE, ms=4.5)
    fa.axvline(1.0, color="#444444", lw=0.7)
    fa.set_xscale("log")
    fa.set_xlim(0.7 * min(1.0, lo_all), 1.15 * hi_all)
    fa.set_ylim(-0.6, len(keys) - 0.4)
    fa.set_yticks([])
    fa.set_xticks([t for t in (1, 2, 4) if fa.get_xlim()[0] <= t <= fa.get_xlim()[1]])
    fa.set_xticklabels([f"{t}" for t in (1, 2, 4) if fa.get_xlim()[0] <= t <= fa.get_xlim()[1]])
    fa.minorticks_off()
    fa.tick_params(labelsize=7.2, length=2, pad=1.5)
    fa.set_xlabel("error ratio", fontsize=7.2, labelpad=1.5)
    for i, (k, lab) in enumerate(keys):
        y = len(keys) - 1 - i
        yy = 13.5 + 20.0 * (y + 0.6) / (len(keys) + 0.2)
        ax.text(106.8, yy, lab, ha="right", va="center", fontsize=7.2, zorder=6)
        t = C[k].get("tier")
        if t in ("S", "N", "-"):
            ax.text(127.4, yy, "–" if t == "-" else t, ha="center", va="center", fontsize=7.4, fontweight="bold",
                    color="white" if t == "S" else "#222222", zorder=6,
                    bbox=dict(boxstyle="circle,pad=0.2", fc=ps.TIER_COL[t], ec="none"))
    txt(ax, 109.5, 40.0, f"{nB} cycling conditions\nheld out; median error\nratio, 95 % interval", size=7.0, linespacing=1.15)
    txt(ax, 109.5, 6.2, "> 1: PINN-KAN better", size=7.0, color="#444444")
    ps.finish(fig, "graphical_abstract", prov, a.out_dir)


if __name__ == "__main__":
    main()
