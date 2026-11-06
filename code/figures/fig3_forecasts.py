"""Fig. 3: forecast overlays at held-out conditions at g1 = (m 8, k 2) and g4 = (m 32, k full), window shaded (PREREG_v4 section 14: P1, Test C).

Rows = temperature (23, 35, 45 C). Per row two conditions, picked by RANK of the supplied A1 condition score at g4 within that temperature (25th and 75th rank; a rule,
not a choice); each condition is drawn at g1 and at g4 (columns 1-2 and 3-4). One replicate per condition = the cell at the middle rank of the supplied A1 cell scores.
The 35 C row is Test C (scored at g4 only; boxed and labelled "held-out temperature-laboratory domain").
Markers = observed capacity (filled: model-visible window, open: forecast target); shaded = window; lines = the seed-ensemble forecast of PINN-KAN (band: range of the five
seed forecasts), of the dataset authors' model A10 and of D* (the arm that the run selected). Per-panel RMSE = the supplied condition scores.
Inputs: --runs-b (grid run directories or their parent), --run-c. Nothing is computed from the predictions: rows are selected, sorted and drawn.
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

QS = (0.25, 0.75)


def draw(ax, pred, win, cell, dstar, sc, cond, big):
    (tw, yw), (tf, yo), _, _ = pdt.forecast_curves(pred, win, cell, "A1")
    tw, yw = np.r_[0.0, tw], np.r_[100.0, yw]
    ax.axvspan(0, tw[-1], color="#E4E4E4", lw=0, zorder=0)
    for m in (["A10", dstar, "A1"] if dstar else ["A10", "A1"]):
        _, _, ens, Y = pdt.forecast_curves(pred, win, cell, m)
        key = "D*" if m == dstar else m
        name, col, mk, ls = ps.ARMS[key]
        if m == "A1" and len(Y):
            ax.fill_between(tf, Y.min(0), Y.max(0), color=col, alpha=0.30, lw=0, zorder=2)
        ax.plot(tf, ens, color=col, ls=ls, lw=1.6 if m == "A1" else 1.1, zorder=4 if m == "A1" else 3)
    ax.plot(tw, yw, "o", ms=3.4, color="#222222", zorder=6, clip_on=False)
    ax.plot(tf, yo, "o", ms=3.4, color="#222222", mfc="white", mew=0.9, zorder=6)
    ax.set_title(ps.cond_text(cond), fontsize=7.5, pad=3)
    ax.set_xlim(0, max(tf) * 1.03)
    ax.margins(y=0.08)
    ax.text(0.97, 0.96, f"A1 {sc['A1'][cond]:.2f} pp\nA10 {sc['A10'][cond]:.2f} pp", transform=ax.transAxes, ha="right", va="top", fontsize=7, color="#333333", linespacing=1.15)
    ax.tick_params(labelsize=7.5)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--runs-b", required=True)
    ap.add_argument("--run-c", required=True)
    a = ap.parse_args()
    ps.apply()
    runs = pdt.runs_by_m(pdt.expand_runs(a.runs_b))
    g1_runs, g4_runs = runs[8], runs[32]
    run_c = Path(a.run_c)
    prov = ps.Provenance(*(g1_runs + g4_runs), run_c)
    prov.require_frozen("Fig. 3")
    D = {}
    for nm, rs, k in (("g1", g1_runs, "2"), ("g4", g4_runs, "full")):
        D[nm] = dict(runs=rs, pred=pdt.load_cell_predictions(rs, k), win=pdt.load_windows(rs), sc=pdt.load_scores_runs(rs, k), cs=pdt.load_cell_scores_runs(rs, k),
                     where=pdt.cond_run(rs), comp=pdt.load_comparators(rs))
    C = dict(pred=pdt.load_predictions(run_c), win=pdt.load_window(run_c), sc=pdt.load_scores(run_c), cs=pdt.load_cell_scores(run_c),
             comp=pdt.load_comparators([run_c]).get(run_c.name, {}))

    fig, axes = plt.subplots(3, 4, figsize=(ps.W_FULL, 13.2 * ps.CM))
    fig.subplots_adjust(left=0.085, right=0.992, top=0.905, bottom=0.17, hspace=0.80, wspace=0.30)
    for ri, T in enumerate((23, 35, 45)):
        src = C if T == 35 else D["g4"]
        conds = [c for c in src["sc"]["A1"] if ps.parse_cond(c)["T"] == T]
        for qi, q in enumerate(QS):
            cond = pdt.rank_pick(conds, lambda c: src["sc"]["A1"][c], q)
            cell = pdt.pick_cell(src["cs"]["A1"], cond)
            for gi, nm in enumerate(("g1", "g4")):
                ax = axes[ri, 2 * qi + gi]
                if T == 35 and nm == "g1":
                    ax.axis("off")
                    ax.text(0.5, 0.5, "Test C is scored at g4 only", transform=ax.transAxes, ha="center", va="center", fontsize=7.5, color="#555555")
                    continue
                if T == 35:
                    draw(ax, C["pred"], C["win"], cell, C["comp"].get("D*"), C["sc"], cond, False)
                else:
                    d = D[nm]
                    run = d["where"][cond]
                    draw(ax, d["pred"], d["win"], cell, d["comp"][run.name].get("D*"), d["sc"], cond, False)
                if ri == 0:
                    ax.text(0.5, 1.30, "g1 (m 8, k 2)" if nm == "g1" else "g4 (m 32, k full)", transform=ax.transAxes, ha="center", va="bottom", fontsize=8, fontweight="bold", color="#333333")
                if 2 * qi + gi == 0:
                    ax.set_ylabel("Retention (%)")
                if ri == 2:
                    ax.set_xlabel("Days since reference")
    fig.canvas.draw()
    inv = fig.transFigure.inverted()
    row = axes[1]
    x0 = row[0].get_position().x0 - 0.02
    x1 = inv.transform(row[-1].get_tightbbox().p1)[0] + 0.003
    y0 = inv.transform(row[1].get_tightbbox().p0)[1] - 0.004
    y1 = inv.transform(row[1].get_tightbbox().p1)[1] + 0.006
    fig.add_artist(Rectangle((x0, y0), x1 - x0, y1 - y0, transform=fig.transFigure, fill=False, ec=ps.VERM, lw=1.2, zorder=10))
    fig.text(x1 - 0.004, y1 + 0.002, "35 °C: held-out temperature–laboratory domain (Test C, laboratory INT)", ha="right", va="bottom", fontsize=7.5, color=ps.VERM, fontweight="bold")
    for ri, T in enumerate((23, 35, 45)):
        pos = axes[ri, 0].get_position()
        fig.text(0.012, (pos.y0 + pos.y1) / 2, f"{T} °C", rotation=90, ha="center", va="center", fontsize=9, fontweight="bold", color=ps.VERM if T == 35 else "#222222")
    handles = [Line2D([], [], marker="o", ls="none", ms=4, color="#222222", label="Observed, window"),
               Line2D([], [], marker="o", ls="none", ms=4, color="#222222", mfc="white", mew=0.9, label="Observed, forecast target"),
               Patch(fc="#E4E4E4", label="Window"),
               Line2D([], [], color=ps.BLUE, lw=1.6, label="PINN-KAN (band: range of 5 seeds)"),
               Line2D([], [], color=ps.ARMS["A10"][1], lw=1.1, label="Semi-empirical A10"),
               Line2D([], [], color=ps.ARMS["D*"][1], lw=1.1, label="D* (selected learner)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.025), fontsize=7.5, columnspacing=1.2, labelspacing=0.3)
    ps.finish(fig, "fig3_forecasts", prov, a.out_dir)


if __name__ == "__main__":
    main()
