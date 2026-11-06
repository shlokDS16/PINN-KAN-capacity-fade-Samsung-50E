"""Fig. 6: storage axis (PREREG_v4 section 14: Q-T, S2 parity, model-defined calendar share; 11a items 3, 4).

a  parity of the PINN-KAN ensemble forecast on the held-out storage conditions (S2, descriptive), coloured by temperature, grey band = +- --band-pp (display only)
b  paired condition RMSE, PINN-KAN against the dataset authors' model (A10), S2; title = the count of the statistics step (stats['s2']['rows']['A10'])
c  calendar share of the predicted fade of cycled cells (A1 filled, A2 open), one point per scored cell from superposition.csv; the number of cells with a physically
   impossible split is the physval_11a item 4 count
d  Arrhenius check of the calendar KAN: ln rate against 1000/T at four SOC, envelope of the run-writer stress_functions.json (merged over the grid runs); the PC-2 verdict is
   read from controls.json (printed only when the statistics step evaluated it)
e  Q-T: training with against without the storage cells (A1 against A13 at g1): the mean paired pp difference with its BCa interval, the tier and the fixed sentence of
   the statistics step (secondary.tests.QT_g1, mean_vs_median.contrasts.QT_g1, qualifier_sentences.QT_g1)
Inputs: --run-s2, --runs (grid runs), --stats, --physval, --controls. READ-ONLY.
"""
import sys
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps
import pk_data as pdt


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--run-s2", required=True)
    ap.add_argument("--runs", required=True, help="grid run directories (or parent): superposition.csv and stress_functions.json of the m = 32 runs")
    ap.add_argument("--stats", required=True)
    ap.add_argument("--physval", required=True)
    ap.add_argument("--controls", required=True)
    ap.add_argument("--band-pp", type=float, default=1.0, help="half-width of the grey display band (pp)")
    a = ap.parse_args()
    ps.apply()
    s2 = Path(a.run_s2)
    runs = [r for r in pdt.runs_by_m(pdt.expand_runs(a.runs)).get(32, []) if (r / "superposition.csv").exists()]
    prov = ps.Provenance(s2, a.stats, a.physval, a.controls, *runs)
    prov.require_frozen("Fig. 6")
    pred = pdt.load_predictions(s2)
    pred = pred[pred.seed == "ens"]
    sc = pdt.load_scores(s2)
    ST, PV, CT = pdt.load_stats(a.stats), ps.load_json(ps.need(a.physval)), ps.load_json(ps.need(a.controls))
    sup = pd.concat([pd.read_csv(r / "superposition.csv") for r in runs], ignore_index=True)
    SF = [ps.load_json(r / "stress_functions.json") for r in runs]

    fig = plt.figure(figsize=(ps.W_FULL, 11.6 * ps.CM))
    gs = fig.add_gridspec(2, 3, left=0.075, right=0.985, top=0.935, bottom=0.125, hspace=0.50, wspace=0.40)
    ax = [fig.add_subplot(gs[i // 3, i % 3]) for i in range(6)]

    A = ax[0]
    p = pred[pred.arm == "A1"].copy()
    p["T"] = p.cond.map(lambda c: ps.parse_cond(c)["T"])
    lo, hi = 100 * min(p.true_retention.min(), p.pred_retention.min()) - 0.5, 100.4
    A.fill_between([lo, hi], [lo - a.band_pp, hi - a.band_pp], [lo + a.band_pp, hi + a.band_pp], color="#E4E4E4", lw=0, zorder=0)
    A.plot([lo, hi], [lo, hi], color="#555555", lw=0.8, zorder=1)
    for T in sorted(p["T"].unique()):
        q = p[p["T"] == T]
        A.scatter(100 * q.true_retention, 100 * q.pred_retention, s=7, color=ps.TEMP_COL[int(T)], alpha=0.8, lw=0, zorder=3, label=f"{T:g} °C")
    A.set_xlim(lo, hi)
    A.set_ylim(lo, hi)
    A.set_aspect("equal")
    A.set_xlabel("Observed retention (%)")
    A.set_ylabel("Predicted retention (%)")
    A.legend(loc="upper left", fontsize=7.5, handletextpad=0.1, borderaxespad=0.1, markerscale=1.4, labelspacing=0.25)
    A.set_title("Held-out storage (S2)", fontsize=8.5, pad=4)

    B = ax[1]
    conds = sorted(sc["A1"])
    xa = np.array([sc["A10"][c] for c in conds])
    ya = np.array([sc["A1"][c] for c in conds])
    top = 1.05 * max(xa.max(), ya.max())
    B.plot([0, top], [0, top], color="#555555", lw=0.8, zorder=1)
    for c, x, y in zip(conds, xa, ya):
        cc = ps.parse_cond(c)
        col = ps.TEMP_COL[int(cc["T"])]
        B.scatter(x, y, s=22, marker="o", facecolors="white" if cc["soc"] > 80 else col, edgecolors=col, linewidths=1.1, zorder=3)
    B.set_xlim(0, top)
    B.set_ylim(0, top)
    B.set_aspect("equal")
    B.set_xlabel("A10 RMSE (pp)")
    B.set_ylabel("PINN-KAN RMSE (pp)")
    B.legend(handles=[Line2D([], [], marker="o", ls="none", color=ps.TEMP_COL[T], ms=4.5, label=f"{T} °C") for T in (10, 23, 45)]
             + [Line2D([], [], marker="o", ls="none", color="#555555", mfc="white", ms=4.5, label="SOC > 80 %")], loc="upper left", fontsize=7.5, handletextpad=0.1,
             borderaxespad=0.1, labelspacing=0.25)
    r10 = ST.get("s2", {}).get("rows", {}).get("A10")
    B.set_title(f"PINN-KAN lower in {r10['k_ratio_below_1']}/{r10['n']}" if r10 else "PINN-KAN against A10", fontsize=8.5, pad=4)

    C = ax[2]
    sup = sup.assign(T=sup.cond.map(lambda c: ps.parse_cond(c)["T"]))
    xpos = {23: 0, 35: 1, 45: 2}
    for arm, off, filled in (("A1", -0.16, True), ("A2", 0.16, False)):
        q = sup[sup.arm == arm].reset_index(drop=True)
        jit = ((q.index.values * 37) % 100 / 100.0 - 0.5) * 0.16          # display jitter by row index (deterministic)
        col = ps.ARMS[arm][1]
        C.scatter(q["T"].map(xpos).values + off + jit, 100 * q.share_cal, s=9, marker=ps.ARMS[arm][2], facecolors=col if filled else "white", edgecolors=col, linewidths=0.8,
                  zorder=3, label=ps.ARMS[arm][0])
    C.axhline(100, color=ps.VERM, lw=1.0, ls="--")
    C.set_xticks([0, 1, 2])
    C.set_xticklabels(["23", "35", "45"])
    C.set_xlabel("Cycling temperature (°C)")
    C.set_ylabel("Calendar share of fade (%)")
    arms4 = PV["item4"].get("arms", {})
    if arms4:
        C.text(0.98, 0.03, "calendar term > observed fade:\n" + ", ".join(f"{k} {v['n_calendar_exceeds_observed_total']} cells" for k, v in sorted(arms4.items())), transform=C.transAxes,
               ha="right", va="bottom", fontsize=7.5)
    C.legend(loc="upper left", fontsize=7.5, handletextpad=0.1, borderaxespad=0.1, labelspacing=0.25)
    C.set_ylim(0, 135)
    C.set_title("Calendar share, cycled cells", fontsize=8.5, pad=4)

    D = ax[3]
    arr = SF[0]["arrhenius"]
    Tk = np.array(arr["T_C"]) + 273.15
    xk = 1000 / Tk
    cols, mks = [ps.BLUE, ps.GREEN, ps.ORANGE, ps.VERM], ["o", "s", "^", "D"]
    bands = pdt.merge_bands([s["arrhenius"]["ln_rate"] for s in SF])
    for i, soc in enumerate(arr["soc"]):
        D.fill_between(xk, bands["lo"][i], bands["hi"][i], color=cols[i], alpha=0.25, lw=0)
        D.plot(xk, bands["mean"][i], color=cols[i], marker=mks[i], ms=4, lw=1.2, label=f"SOC {soc:g} %")
    D.set_xlabel("1000 / T (K$^{-1}$)")
    D.set_ylabel("ln rate (pp / 500 d)")
    sec = D.secondary_xaxis("top", functions=(lambda x: 1000 / x - 273.15, lambda t: 1000 / (t + 273.15)))
    sec.set_xticks(arr["T_C"])
    sec.set_xlabel("Temperature (°C)", fontsize=8, labelpad=2)
    D.legend(loc="upper right", fontsize=7.5, handletextpad=0.3, borderaxespad=0.1, labelspacing=0.25)
    pc2 = CT.get("gate_G", {}).get("reported_checks", {}).get("PC-2_calendar_rate_monotone_in_T")
    D.text(0.03, 0.04, "PC-2: " + ("not evaluated by the statistics step" if pc2 is None else ("met" if pc2 else "not met")), transform=D.transAxes, fontsize=7, color="#444444")

    E = ax[4]
    qt = ST["secondary"]["tests"].get("QT_g1")
    mv = ST["mean_vs_median"]["contrasts"].get("QT_g1")
    if qt and mv:
        lo_, hi_ = mv["mean_pp_ci"] if mv.get("mean_pp_ci") else (mv["mean_pp"], mv["mean_pp"])
        E.plot([lo_, hi_], [0, 0], color=ps.BLUE, lw=1.6, solid_capstyle="butt")
        E.plot([mv["mean_pp"]], [0], "o", color=ps.BLUE, ms=5.5)
        E.axvline(0, color="#444444", lw=0.7)
        E.set_ylim(-1, 1.6)
        E.set_yticks([])
        E.spines["left"].set_visible(False)
        E.set_xlabel("Without $-$ with storage cells, mean paired\ndifference (pp) [95 % BCa]")
        E.set_title(f"Q-T at g1: tier {pdt.tier_text(qt['tier'])}", fontsize=8.5, pad=4)
        E.text(0.0, 0.86, f"median error reduction {pdt.pct_from_log(mv['median_L']):.1f} %", transform=E.transAxes, fontsize=7.5, va="top")
        sent = ST.get("qualifier_sentences", {}).get("QT_g1")
        if sent:
            E.text(0.0, 0.70, textwrap.fill(sent, 42), transform=E.transAxes, fontsize=6.8, va="top", color="#333333")
    else:
        E.axis("off")
    ax[5].axis("off")
    fig.canvas.draw()
    ps.label_panels(fig, ax[:5])
    ps.finish(fig, "fig6_storage", prov, a.out_dir)


if __name__ == "__main__":
    main()
