"""Fig. 3: forecast overlays at held-out conditions (small multiples).

Rows = temperature (23, 35, 45 C); columns = conditions at the 25th / 50th / 75th percentile of the A1 condition score
within that temperature (rule, not a choice); one replicate per condition = the cell with the median A1 RMSE.
23 and 45 C come from Test B, 35 C from Test C (all 35 C conditions held out; the row is boxed and labelled).
Markers = observed capacity (filled: model-visible window, open: forecast target); shaded = window; lines = models
(PINN-KAN with its min-max band over the 5 final-refit seeds, semi-empirical A10, best-of data-driven A12).
Inputs: --run-b, --run-c (run directories with predictions.csv, window.csv, condition_scores.json).
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps
import pk_data as pdt

MODELS = ["A10", "A12", "A1"]  # draw order: A1 on top


def pick_conditions(scores_a1, T, q=(0.25, 0.5, 0.75)):
    conds = [c for c in scores_a1 if ps.parse_cond(c)["T"] == T]
    conds.sort(key=lambda c: scores_a1[c])
    idx = [int(round(x * (len(conds) - 1))) for x in q]
    return [conds[i] for i in idx]


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--run-b", required=True)
    ap.add_argument("--run-c", required=True)
    a = ap.parse_args()
    ps.apply()
    prov = ps.Provenance(a.run_b, a.run_c)
    prov.require_frozen("Fig. 3")
    runs = {23: a.run_b, 35: a.run_c, 45: a.run_b}
    cache = {}
    for r in {a.run_b, a.run_c}:
        cache[r] = (pdt.load_predictions(r), pdt.load_window(r), pdt.load_scores(r))

    fig, axes = plt.subplots(3, 3, figsize=(ps.W_FULL, 13.0 * ps.CM), sharex=True)
    fig.subplots_adjust(left=0.105, right=0.992, top=0.945, bottom=0.175, hspace=0.62, wspace=0.27)
    for ri, T in enumerate((23, 35, 45)):
        run = runs[T]
        pred, win, sc = cache[run]
        conds = pick_conditions(sc["A1"], T)
        for ci, cond in enumerate(conds):
            ax = axes[ri, ci]
            cell, _ = pdt.median_cell(pred, cond, "A1")
            (tw, yw), (tf, yo), _ = pdt.cell_curve(pred, win, cell, "A1")
            tw = np.r_[0.0, tw]
            yw = np.r_[100.0, yw]
            ax.axvspan(0, tw[-1], color="#E4E4E4", lw=0, zorder=0)
            for m in MODELS:
                _, _, Y = pdt.cell_curve(pred, win, cell, m)
                name, col, mk, ls = ps.ARMS[m]
                if m == "A1":
                    ax.fill_between(tf, Y.min(0), Y.max(0), color=col, alpha=0.30, lw=0, zorder=2)
                ax.plot(tf, Y.mean(0), color=col, ls=ls, lw=1.6 if m == "A1" else 1.1, zorder=4 if m == "A1" else 3)
            ax.plot(tw, yw, "o", ms=3.6, color="#222222", mfc="#222222", zorder=6, clip_on=False)
            ax.plot(tf, yo, "o", ms=3.6, color="#222222", mfc="white", mew=0.9, zorder=6)
            ax.set_title(ps.cond_text(cond), fontsize=8, pad=3)
            ax.set_xlim(0, tf.max() * 1.03)
            ax.margins(y=0.08)
            ax.text(0.97, 0.96, f"A1 {sc['A1'][cond]:.2f} pp\nA10 {sc['A10'][cond]:.2f} pp", transform=ax.transAxes,
                    ha="right", va="top", fontsize=7.5, color="#333333", linespacing=1.15)
            ax.tick_params(labelsize=7.5)
            if ci == 0:
                ax.set_ylabel("Retention (%)")
            if ri == 2:
                ax.set_xlabel("Days since reference")
            ax.xaxis.set_major_locator(plt.MultipleLocator(100))
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))

    # box and label the 35 C row
    fig.canvas.draw()
    inv = fig.transFigure.inverted()
    row = axes[1]
    x0 = inv.transform(row[0].get_tightbbox().p0)[0] - 0.010
    x1 = inv.transform(row[-1].get_tightbbox().p1)[0] + 0.003
    y0 = inv.transform(row[0].get_tightbbox().p0)[1] - 0.004
    y1 = inv.transform(row[0].get_tightbbox().p1)[1] + 0.006
    fig.add_artist(Rectangle((x0, y0), x1 - x0, y1 - y0, transform=fig.transFigure, fill=False, ec=ps.VERM, lw=1.2, zorder=10))
    fig.text(x1 - 0.004, y1 + 0.006, "35 °C: held-out temperature–laboratory domain (Test C, laboratory INT)",
             ha="right", va="bottom", fontsize=7.5, color=ps.VERM, fontweight="bold")

    for ri, T in enumerate((23, 35, 45)):
        pos = axes[ri, 0].get_position()
        fig.text(0.013, (pos.y0 + pos.y1) / 2, f"{T} °C", rotation=90, ha="center", va="center", fontsize=9,
                 fontweight="bold", color=ps.VERM if T == 35 else "#222222")
    handles = [Line2D([], [], marker="o", ls="none", ms=4, color="#222222", label="Observed, window"),
               Line2D([], [], marker="o", ls="none", ms=4, color="#222222", mfc="white", mew=0.9, label="Observed, forecast target"),
               Patch(fc="#E4E4E4", label="Window"),
               Line2D([], [], color=ps.BLUE, lw=1.6, label="PINN-KAN (band: 5 seeds, min–max)"),
               Line2D([], [], color=ps.ARMS["A10"][1], lw=1.1, label="Semi-empirical A10"),
               Line2D([], [], color=ps.ARMS["A12"][1], lw=1.1, label="LightGBM A12")]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.032), fontsize=7.5, columnspacing=1.2,
               labelspacing=0.3)
    ps.finish(fig, "fig3_forecasts", prov, a.out_dir)


if __name__ == "__main__":
    main()
