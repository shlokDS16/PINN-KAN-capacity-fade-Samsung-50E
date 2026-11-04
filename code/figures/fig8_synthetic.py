"""Fig. 8: synthetic identifiability (H7): recovery of the true log-rate surface on G0 (control), G1 and G2.

Top row: nRMSE of the recovered log-rate surface (500-point hull Latin hypercube, divided by the true range) per draw and
model, box = quartiles, dots = draws, lines at the pre-set pass (0.15) and fail (0.30) thresholds; for each generator the
additive-GAM class floor on the true surface (validity rule, PREREG_v2 section 13) is marked by a diamond on the GAM box.
Bottom row: recovered against true surface for the median-nRMSE draw of the PINN-KAN (A1) and the additive GAM (A4).
Input: --run (directory with summary.json and surfaces_<gen>.npz; format of runs/pilot_P4 per_draw + surfaces).
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps

GENS = [("G0", "G0: well specified (control)"), ("G1", "G1: misspecified time law"), ("G2", "G2: non-additive stress law")]
ARMS = ["A1", "A2", "A4", "A8"]


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    ps.apply()
    prov = ps.Provenance(a.run)
    prov.require_frozen("Fig. 8")
    run = Path(a.run)
    S = ps.load_json(ps.need(run / "summary.json"))
    thr = S["thresholds"]
    draws = S["draws"]
    rng = np.random.default_rng(2)

    fig = plt.figure(figsize=(ps.W_FULL, 11.2 * ps.CM))
    gs = fig.add_gridspec(2, 3, left=0.075, right=0.99, top=0.93, bottom=0.17, hspace=0.62, wspace=0.28, height_ratios=[1, 1.05])
    top = [fig.add_subplot(gs[0, i]) for i in range(3)]
    bot = [fig.add_subplot(gs[1, i]) for i in range(3)]
    for gi, (g, title) in enumerate(GENS):
        ax = top[gi]
        dg = [d for d in draws if d["gen"] == g]
        data = [[d["nrmse"][m] for d in dg] for m in ARMS]
        pos = np.arange(len(ARMS))
        bp = ax.boxplot(data, positions=pos, widths=0.55, showfliers=False, patch_artist=True,
                        medianprops=dict(color="#111111", lw=1.2), whiskerprops=dict(lw=0.7), capprops=dict(lw=0.7),
                        boxprops=dict(lw=0.7))
        for patch, m in zip(bp["boxes"], ARMS):
            patch.set_facecolor(ps.ARMS[m][1])
            patch.set_alpha(0.35)
            patch.set_edgecolor(ps.ARMS[m][1])
        for x, m, v in zip(pos, ARMS, data):
            ax.scatter(x + rng.uniform(-0.16, 0.16, len(v)), v, s=6, color=ps.ARMS[m][1], lw=0, zorder=3)
        fl = float(np.median([d["additive_floor"] for d in dg]))
        ax.axhline(fl, xmin=0.55, xmax=0.78, color=ps.PURPLE, lw=0.0)
        ax.scatter([2], [fl], marker="D", s=22, color="white", edgecolors="#111111", linewidths=0.9, zorder=5)
        ax.axhline(thr["pass_"], color=ps.GREEN, lw=0.9, ls="--", zorder=1)
        ax.axhline(thr["fail"], color=ps.VERM, lw=0.9, ls="--", zorder=1)
        ax.set_xticks(pos)
        ax.set_xticklabels(["PINN-\nKAN", "Hard-\nODE", "Add.\nGAM", "Free\nG"], fontsize=7.5)
        ax.set_ylim(0, 0.36)
        ax.set_title(title, fontsize=8.5, pad=4)
        if gi == 0:
            ax.set_ylabel("nRMSE, log-rate surface")
        # bottom: recovered vs true
        Fz = np.load(ps.need(run / f"surfaces_{g}.npz"))
        bx = bot[gi]
        i1 = [i for i, d in enumerate(dg)]
        order = np.argsort([d["nrmse"]["A1"] for d in dg])
        k = int(order[len(order) // 2])
        ft = Fz["f_true"][k]
        lo, hi = ft.min(), ft.max()
        pad = 0.05 * (hi - lo)
        bx.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color="#555555", lw=0.8, zorder=1)
        for m in ("A4", "A1"):
            bx.scatter(ft, Fz[f"f_{m}"][k], s=4, color=ps.ARMS[m][1], alpha=0.55, lw=0, zorder=3 if m == "A1" else 2)
        bx.set_xlim(lo - pad, hi + pad)
        bx.set_ylim(lo - pad, hi + pad)
        bx.set_aspect("equal")
        bx.set_xlabel("True log-rate (centred)")
        if gi == 0:
            bx.set_ylabel("Recovered log-rate")
        bx.set_title(f"draw {dg[k]['draw']}: A1 {dg[k]['nrmse']['A1']:.2f}, A4 {dg[k]['nrmse']['A4']:.2f}", fontsize=7.5, pad=3, loc="right")
    fig.canvas.draw()
    ps.label_panels(fig, top + bot)
    h = [Line2D([], [], color=ps.GREEN, ls="--", lw=0.9, label=f"pass {thr['pass_']:.2f}"),
         Line2D([], [], color=ps.VERM, ls="--", lw=0.9, label=f"fail {thr['fail']:.2f}"),
         Line2D([], [], marker="D", ls="none", mfc="white", mec="#111111", ms=4.5, label="additive-GAM class floor (median)"),
         Line2D([], [], marker="o", ls="none", color=ps.BLUE, ms=3.5, label="PINN-KAN (A1)"),
         Line2D([], [], marker="o", ls="none", color=ps.ARMS["A4"][1], ms=3.5, label="Additive GAM (A4)")]
    fig.legend(handles=h, loc="lower center", ncol=5, bbox_to_anchor=(0.5, 0.03), fontsize=7.5, columnspacing=1.0, handletextpad=0.3)
    ps.finish(fig, "fig8_synthetic", prov, a.out_dir)


if __name__ == "__main__":
    main()
