"""Fig. 4 (file name kept from the V3 forest plot): learning curves of PINN-KAN (A1) over the 3 x 3 grid of training conditions m and window check-ups k.

PREREG_v4 section 14: median condition log ratio, drawn as the relative reduction of the error of A1 against D*, A9, AG, A2, A10 and A10P, with the SIMULTANEOUS exact
intervals of the statistics step (Bonferroni over the nine cells); the ladder decomposition (law share with a non-KAN map; KAN share inside the law); the mean paired pp
difference with its BCa interval; tiers only where the statistics step assigned one (the gated cells g1 = (8, 2), g4 = (32, full) and the secondary tests).
Positive = PINN-KAN has the lower error.

Input: --stats analysis/contrasts_v4_B.json (stats_step.run_stats_v4). READ-ONLY: every interval, tier, count and mean in the figure is a value of that file; the figure only
converts a supplied median log ratio to a percentage (pk_data.pct_from_log) and sets axis limits from the supplied values.
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps
import pk_data as pdt

COMPS = ["D*", "A9", "AG", "A2", "A10", "A10P"]
KS = ["0", "2", "full"]
MS = [8, 16, 32]
K_COL = {"0": plt.get_cmap("cividis")(0.10), "2": plt.get_cmap("cividis")(0.50), "full": plt.get_cmap("cividis")(0.85)}
K_MK = {"0": "s", "2": "o", "full": "^"}
K_OFF = {"0": -0.21, "2": 0.0, "full": 0.21}
K_NAME = {"0": "k = 0 (reference check-up only)", "2": "k = 2", "full": "k = k$_{\\mathrm{full}}$"}


def curve_panel(ax, rows, stats, comp):
    ys = []
    for k in KS:
        rk = [r for r in rows if str(r["cell"][1]) == k]
        if not rk:
            continue
        xs = np.array([MS.index(r["cell"][0]) + K_OFF[k] for r in rk])
        y = np.array([pdt.pct_from_log(r["median_L"]) for r in rk])
        lo = np.array([r["simultaneous"]["rel_reduction_ci_pct"][0] for r in rk])
        hi = np.array([r["simultaneous"]["rel_reduction_ci_pct"][1] for r in rk])
        ax.plot(xs, y, color=K_COL[k], lw=0.9, zorder=2)
        for x_, y_, l_, h_, r in zip(xs, y, lo, hi, rk):
            ax.plot([x_, x_], [l_, h_], color=K_COL[k], lw=1.3, solid_capstyle="butt", zorder=3)
            rng_only = bool(r["simultaneous"].get("is_range", False))
            ax.plot([x_], [y_], marker=K_MK[k], ms=4.6, mfc="white" if rng_only else K_COL[k], mec=K_COL[k], mew=1.0, ls="none", zorder=4)
            t = pdt.tier_text(pdt.tier_read(stats, comp, (r["cell"][0], r["cell"][1])))
            if t:
                ax.annotate(t, (x_, h_), xytext=(0, 2.5), textcoords="offset points", ha="center", va="bottom", fontsize=7.5, fontweight="bold", color="#222222")
        ys += list(lo) + list(hi)
    ax.axhline(0, color="#444444", lw=0.7, zorder=1)
    ax.set_xticks(range(len(MS)))
    ax.set_xticklabels([str(m) for m in MS])
    ax.set_xlim(-0.55, len(MS) - 0.45)
    return ys


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--stats", required=True, help="analysis/contrasts_v4_B.json")
    a = ap.parse_args()
    ps.apply()
    prov = ps.Provenance(a.stats)
    prov.require_frozen("Fig. 4")
    S = pdt.load_stats(a.stats)

    fig = plt.figure(figsize=(ps.W_FULL, 18.2 * ps.CM))
    gs = fig.add_gridspec(3, 3, left=0.085, right=0.99, top=0.955, bottom=0.145, hspace=0.80, wspace=0.34)
    ax = [fig.add_subplot(gs[i // 3, i % 3]) for i in range(9)]
    allv = []
    present = []
    for i, comp in enumerate(COMPS):
        rows = pdt.est_rows(S, comp)
        if not rows:
            ax[i].axis("off")
            continue
        present.append(i)
        allv += curve_panel(ax[i], rows, S, comp)
        ax[i].set_title(ps.ARMS[comp][0], fontsize=8.5, pad=4)
        ax[i].set_xlabel("Training conditions $m$")
        if i % 3 == 0:
            ax[i].set_ylabel("Error reduction by\nPINN-KAN (%)")
    pad = 0.12 * (max(allv) - min(allv))
    for i in present:
        ax[i].set_ylim(min(allv) - pad, max(allv) + 2.2 * pad)
    if "P3" in S["effective_tiers"] and 0 in present:
        ax[0].text(0.03, 0.04, f"P3: {pdt.tier_text(S['effective_tiers']['P3'])}", transform=ax[0].transAxes, fontsize=7.5, ha="left", va="bottom", color="#222222")

    # ladder (g, h)
    lad = S["estimated"]["ladder"]
    for j, (key, title) in enumerate((("law_share_with_non_KAN_map", "Ladder: law with a non-KAN map\n(A9 to AG)"), ("KAN_share_inside_law", "Ladder: KAN inside the law\n(AG to A1)"))):
        A = ax[6 + j]
        ys = []
        for k in KS:
            rk = [r for r in lad if str(r["cell"][1]) == k]
            rk.sort(key=lambda r: r["cell"][0])
            if not rk:
                continue
            xs = np.array([MS.index(r["cell"][0]) + K_OFF[k] for r in rk])
            y = np.array([pdt.pct_from_log(r[key]["median"]) for r in rk])
            lo = np.array([r[key]["simultaneous"]["rel_reduction_ci_pct"][0] for r in rk])
            hi = np.array([r[key]["simultaneous"]["rel_reduction_ci_pct"][1] for r in rk])
            A.plot(xs, y, color=K_COL[k], lw=0.9, zorder=2)
            for x_, y_, l_, h_, r in zip(xs, y, lo, hi, rk):
                A.plot([x_, x_], [l_, h_], color=K_COL[k], lw=1.3, solid_capstyle="butt", zorder=3)
                A.plot([x_], [y_], marker=K_MK[k], ms=4.6, mfc="white" if r[key]["simultaneous"].get("is_range") else K_COL[k], mec=K_COL[k], mew=1.0, ls="none", zorder=4)
            ys += list(lo) + list(hi)
        A.axhline(0, color="#444444", lw=0.7, zorder=1)
        A.set_xticks(range(len(MS)))
        A.set_xticklabels([str(m) for m in MS])
        A.set_xlim(-0.55, len(MS) - 0.45)
        A.set_xlabel("Training conditions $m$")
        A.set_title(title, fontsize=8.5, pad=4, linespacing=1.1)
        if j == 0:
            A.set_ylabel("Share of the error\nreduction (%)")
        if ys:
            p_ = 0.1 * (max(ys) - min(ys))
            A.set_ylim(min(ys) - p_, max(ys) + p_)

    # mean paired difference, BCa (i)
    F = ax[8]
    labels, yy, y = [], [], 0.0
    for comp in COMPS:
        for cell, nm in ((pdt.G1, "g1"), (pdt.G4, "g4")):
            rows = pdt.est_rows(S, comp, cell)
            if not rows or "mean_pp_ci" not in rows[0]:
                continue
            r = rows[0]
            lo, hi = r["mean_pp_ci"]
            col = ps.ARMS[comp][1]
            F.plot([lo, hi], [y, y], color=col, lw=1.4, solid_capstyle="butt")
            F.plot([r["mean_pp"]], [y], marker="o", ms=4.6, mfc=col if nm == "g1" else "white", mec=col, mew=1.0, ls="none", zorder=4)
            labels.append(f"{comp} {nm}")
            yy.append(y)
            y -= 1.0
        y -= 0.35
    F.axvline(0, color="#444444", lw=0.7, zorder=1)
    F.set_yticks(yy)
    F.set_yticklabels(labels, fontsize=7.5)
    F.tick_params(axis="y", length=0)
    F.spines["left"].set_visible(False)
    F.set_xlabel("Comparator $-$ A1 (pp)")
    F.set_title("Mean difference [95 % BCa]", fontsize=8.5, pad=4)

    handles = [Line2D([], [], color=K_COL[k], marker=K_MK[k], ms=4.6, lw=1.2, label=K_NAME[k]) for k in KS]
    handles += [Line2D([], [], color="#555555", marker="o", mfc="white", ms=4.6, lw=0, label="interval = range of the conditions"),
                Line2D([], [], color="#555555", marker="o", ms=4.6, lw=0, label="filled: g1, open: g4 (panel i)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.02), fontsize=7.5, columnspacing=1.2, handlelength=1.8, labelspacing=0.3)
    fig.canvas.draw()
    ps.label_panels(fig, ax)
    ps.finish(fig, "fig4_forest", prov, a.out_dir)


if __name__ == "__main__":
    main()
