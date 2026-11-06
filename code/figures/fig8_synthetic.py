"""Fig. 8: G0 pipeline check PC-1 (PREREG_v4 section 14: G0 recovery with the 0.15 line; appendix if space is short).

Top: nRMSE of the recovered log-rate surface (500-point hull Latin hypercube, divided by the true range) per draw and model; every draw is a dot (no box, no summary
statistic), lines at the pre-set pass (0.15) and fail (0.30) thresholds. The PC-1 verdict is the one of controls.json (statistics step).
Bottom: recovered against true surface for the draw at the middle rank of the supplied A1 nRMSE values (rank pick), A1 and the additive GAM (A4).
G1, G2, the additive-GAM floor and Kendall tau are struck from the confirmatory path (PREREG_v4 section 20, h7.py row) and are not drawn.
Inputs: --run (synthetic_H7 directory: summary.json, surfaces_G0.npz), --controls analysis/controls.json. READ-ONLY.
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps
import pk_data as pdt

ARMS = ["A1", "A2", "A4", "A8"]
NAMES = ["PINN-\nKAN", "Hard-\nODE", "Add.\nGAM", "Free\nG"]


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--run", required=True)
    ap.add_argument("--controls", default=None)
    a = ap.parse_args()
    ps.apply()
    prov = ps.Provenance(a.run, a.controls)
    prov.require_frozen("Fig. 8")
    run = Path(a.run)
    S = ps.load_json(ps.need(run / "summary.json"))
    thr = S["thresholds"]
    dg = [d for d in S["draws"] if d["gen"] == "G0"]
    arms = [m for m in ARMS if m in dg[0]["nrmse"]]
    CT = ps.load_json(ps.need(a.controls)) if a.controls else {}
    pc1 = CT.get("positive", {}).get("P1_G0_nrmse_leq_0p15")

    fig = plt.figure(figsize=(ps.W_FULL, 8.2 * ps.CM))
    gs = fig.add_gridspec(1, 2, left=0.085, right=0.99, top=0.90, bottom=0.30, wspace=0.28, width_ratios=[1.3, 1])
    top, bx = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    for i, m in enumerate(arms):
        v = sorted(d["nrmse"][m] for d in dg)                            # sorted for display
        xs = i + (np.arange(len(v)) / max(len(v) - 1, 1) - 0.5) * 0.4     # deterministic spread by rank
        top.scatter(xs, v, s=9, color=ps.ARMS[m][1], lw=0, zorder=3)
    top.axhline(thr["pass_"], color=ps.GREEN, lw=0.9, ls="--", zorder=1)
    top.axhline(thr["fail"], color=ps.VERM, lw=0.9, ls="--", zorder=1)
    top.set_xticks(range(len(arms)))
    top.set_xticklabels([NAMES[ARMS.index(m)] for m in arms], fontsize=7.5)
    top.set_ylim(0, 0.36)
    top.set_ylabel("nRMSE, log-rate surface")
    top.set_title("G0: well-specified control, one dot per draw", fontsize=8.5, pad=4)
    if pc1 is not None:
        top.text(0.98, 0.97, "PC-1: " + ("met" if pc1 else "not met") + " (statistics step)", transform=top.transAxes, ha="right", va="top", fontsize=7.5)
    Fz = np.load(ps.need(run / "surfaces_G0.npz"))
    order = sorted(range(len(dg)), key=lambda i: dg[i]["nrmse"]["A1"])
    k = order[len(order) // 2]
    ft = Fz["f_true"][k]
    lo, hi = ft.min(), ft.max()
    pad = 0.05 * (hi - lo)
    bx.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color="#555555", lw=0.8, zorder=1)
    for m in ("A4", "A1"):
        if f"f_{m}" in Fz:
            bx.scatter(ft, Fz[f"f_{m}"][k], s=4, color=ps.ARMS[m][1], alpha=0.55, lw=0, zorder=3 if m == "A1" else 2)
    bx.set_xlim(lo - pad, hi + pad)
    bx.set_ylim(lo - pad, hi + pad)
    bx.set_aspect("equal")
    bx.set_xlabel("True log-rate (centred)")
    bx.set_ylabel("Recovered log-rate")
    bx.set_title(f"draw {dg[k]['draw']}: A1 {dg[k]['nrmse']['A1']:.2f}", fontsize=7.5, pad=3, loc="right")
    fig.canvas.draw()
    ps.label_panels(fig, [top, bx])
    h = [Line2D([], [], color=ps.GREEN, ls="--", lw=0.9, label=f"pass {thr['pass_']:.2f}"), Line2D([], [], color=ps.VERM, ls="--", lw=0.9, label=f"fail {thr['fail']:.2f}"),
         Line2D([], [], marker="o", ls="none", color=ps.BLUE, ms=3.5, label="PINN-KAN (A1)"), Line2D([], [], marker="o", ls="none", color=ps.ARMS["A4"][1], ms=3.5, label="Additive GAM (A4)")]
    fig.legend(handles=h, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.02), fontsize=7.5, columnspacing=1.0, handletextpad=0.3)
    ps.finish(fig, "fig8_synthetic", prov, a.out_dir)


if __name__ == "__main__":
    main()
