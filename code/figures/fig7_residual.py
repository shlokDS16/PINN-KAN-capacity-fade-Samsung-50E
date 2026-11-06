"""Fig. 7: PDE-residual map |R| of the fitted PINN-KAN over (T, SOC) and (C_ch, T), pooled over the five outer folds, training conditions overlaid.

Input: --map analysis/residual_map.npz (statistics step, stats_gaps.merge_residual_cells): the bin value is the median of ALL raw |R| values of the scored cycling cells in the bin
(no median of medians), evaluated at the cells' own stress vectors; `n_cells_T_SOC`, `n_cells_cch_T` = scored cells per bin (an empty bin is NaN and drawn blank).
  T_edges, soc_edges, cch_edges (bin edges), absR_T_SOC [nT x nSOC], absR_cch_T [nT x nC], train_T_SOC [n x 2] (T, SOC or SOC_mid), train_cch_T [m x 2] (C_ch, T).
Each panel has its own colour scale (as in the exemplar Yuan Fig. 15); values and cell counts are printed in the cells.
Descriptive only: PREREG_v2 section 13 allows no claim from this figure without a rank-correlation threshold. READ-ONLY.
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps


def heat(ax, edges_x, edges_y, Z, N, xlabel, ylabel, pts, ptsxy, cmap="cividis"):
    """Z, N indexed [y, x]."""
    Zm = np.ma.masked_invalid(Z)
    im = ax.pcolormesh(edges_x, edges_y, Zm, cmap=cmap, shading="flat", rasterized=True)
    xc, yc = (edges_x[1:] + edges_x[:-1]) / 2, (edges_y[1:] + edges_y[:-1]) / 2
    vmin, vmax = np.nanmin(Z), np.nanmax(Z)
    for i, yy in enumerate(yc):
        for j, xx in enumerate(xc):
            v = Z[i, j]
            if not np.isfinite(v):
                ax.text(xx, yy, "no cell", ha="center", va="center", fontsize=6.5, color="#777777", zorder=7)
                continue
            dark = (v - vmin) / (vmax - vmin + 1e-12) < 0.55
            ax.text(xx, yy, f"{v:.2f}\nn={int(N[i, j])}", ha="center", va="center", fontsize=7, color="white" if dark else "#111111", zorder=7, linespacing=1.05,
                    path_effects=[pe.withStroke(linewidth=1.6, foreground="#111111" if dark else "white")])
    ax.scatter(*pts.T[ptsxy], s=5, facecolors="none", edgecolors="white", linewidths=0.5, alpha=0.8, zorder=4)
    ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.set_xlim(edges_x[0], edges_x[-1])
    ax.set_ylim(edges_y[0], edges_y[-1])
    for sp in ax.spines.values():
        sp.set_visible(True)
    return im


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--map", required=True, help="analysis/residual_map.npz (pooled over the outer folds)")
    a = ap.parse_args()
    ps.apply()
    prov = ps.Provenance(a.map)
    prov.require_frozen("Fig. 7")
    Z = np.load(ps.need(a.map, "(statistics step output residual_map.npz)"))
    fig = plt.figure(figsize=(ps.W_FULL, 7.2 * ps.CM))
    A = fig.add_axes([0.075, 0.25, 0.34, 0.64])
    cA = fig.add_axes([0.425, 0.25, 0.012, 0.64])
    B = fig.add_axes([0.555, 0.25, 0.34, 0.64])
    cB = fig.add_axes([0.905, 0.25, 0.012, 0.64])
    imA = heat(A, Z["soc_edges"], Z["T_edges"], Z["absR_T_SOC"], Z["n_cells_T_SOC"], "SOC (%)", ps.LBL["T"], Z["train_T_SOC"][:, ::-1], [0, 1])  # points as (SOC, T)
    A.set_title("(T, SOC)", fontsize=8.5, pad=4)
    imB = heat(B, Z["cch_edges"], Z["T_edges"], Z["absR_cch_T"], Z["n_cells_cch_T"], ps.LBL["cch"], None, Z["train_cch_T"], [0, 1])
    B.set_title("($C_{\\mathrm{ch}}$, T)", fontsize=8.5, pad=4)
    for im, c in ((imA, cA), (imB, cB)):
        cb = fig.colorbar(im, cax=c)
        cb.set_label("median |R| (law units)", fontsize=8, labelpad=3)
        cb.ax.tick_params(labelsize=7.5)
    fig.canvas.draw()
    ps.label_panels(fig, [A, B])
    fig.text(0.5, 0.07, f"{int(Z['n_cells'])} scored cycling cells pooled over the outer folds; n = cells per bin.  Open circles: training conditions.  Colour scale per panel.",
             ha="center", fontsize=7.5, color="#444444")
    ps.finish(fig, "fig7_residual", prov, a.out_dir)


if __name__ == "__main__":
    main()
