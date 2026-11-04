"""Fig. 6: storage transfer (S2) and the superposition checks (PREREG_v2 11a items 3, 4; H5, X1).

a  parity of PINN-KAN forecasts on held-out storage conditions (S2), coloured by temperature, grey band = +- --band-pp
b  paired condition RMSE, PINN-KAN against the dataset authors' model (A10); below the diagonal = PINN-KAN better;
   open symbols: SOC above 80 % (stage 1 only)
c  share of the predicted fade of cycled cells attributed to the calendar term (A1 filled, A2 open); > 100 % is physically impossible
d  Arrhenius check of the calendar KAN: ln rate against 1000/T at four SOC with fold x seed envelope
Inputs: --run-s2 (predictions.csv, condition_scores.json), --run-b (superposition.csv, stress_functions.json).
"""
import sys
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
    ap.add_argument("--run-b", required=True)
    ap.add_argument("--band-pp", type=float, default=1.0, help="half-width of the grey display band (pp)")
    a = ap.parse_args()
    ps.apply()
    prov = ps.Provenance(a.run_s2, a.run_b)
    prov.require_frozen("Fig. 6")
    pred = pdt.load_predictions(a.run_s2)
    sc = pdt.load_scores(a.run_s2)
    sup = pd.read_csv(ps.need(Path(a.run_b) / "superposition.csv"))
    S = ps.load_json(ps.need(Path(a.run_b) / "stress_functions.json"))

    fig = plt.figure(figsize=(ps.W_FULL, 11.6 * ps.CM))
    gs = fig.add_gridspec(2, 2, left=0.085, right=0.985, top=0.935, bottom=0.125, hspace=0.50, wspace=0.28)
    ax = [fig.add_subplot(gs[i // 2, i % 2]) for i in range(4)]

    # a parity
    A = ax[0]
    p = pred[pred.arm == "A1"].groupby(["cond", "cell_id", "t"], as_index=False).agg(y=("true_retention", "first"),
                                                                                  yh=("pred_retention", "mean"))
    p["T"] = p.cond.map(lambda c: ps.parse_cond(c)["T"])
    lo, hi = 100 * min(p.y.min(), p.yh.min()) - 0.5, 100.4
    A.fill_between([lo, hi], [lo - a.band_pp, hi - a.band_pp], [lo + a.band_pp, hi + a.band_pp], color="#E4E4E4", lw=0, zorder=0)
    A.plot([lo, hi], [lo, hi], color="#555555", lw=0.8, zorder=1)
    for T in (10, 23, 45):
        q = p[p["T"] == T]
        A.scatter(100 * q.y, 100 * q.yh, s=7, color=ps.TEMP_COL[T], alpha=0.8, lw=0, zorder=3, label=f"{T} °C")
    A.set_xlim(lo, hi)
    A.set_ylim(lo, hi)
    A.set_aspect("equal")
    A.set_xlabel("Observed retention (%)")
    A.set_ylabel("Predicted retention (%)")
    A.legend(loc="upper left", fontsize=7.5, handletextpad=0.1, borderaxespad=0.1, markerscale=1.4, labelspacing=0.25)
    A.set_title("Held-out storage conditions (S2)", fontsize=8.5, pad=4)

    # b paired RMSE
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
             + [Line2D([], [], marker="o", ls="none", color="#555555", mfc="white", ms=4.5, label="SOC > 80 %")],
             loc="upper left", fontsize=7.5, handletextpad=0.1, borderaxespad=0.1, labelspacing=0.25)
    B.set_title(f"PINN-KAN lower in {int((ya < xa).sum())}/{len(conds)} conditions", fontsize=8.5, pad=4)

    # c superposition
    C = ax[2]
    rng = np.random.default_rng(4)
    g = sup.groupby(["arm", "cond"], as_index=False).agg(share=("share_cal", "median"))
    g["T"] = g.cond.map(lambda c: ps.parse_cond(c)["T"])
    xpos = {23: 0, 35: 1, 45: 2}
    for arm, off, filled in (("A1", -0.16, True), ("A2", 0.16, False)):
        q = g[g.arm == arm]
        xs = q["T"].map(xpos).values + off + rng.uniform(-0.08, 0.08, len(q))
        col = ps.ARMS[arm][1]
        C.scatter(xs, 100 * q.share, s=14, marker=ps.ARMS[arm][2], facecolors=col if filled else "white", edgecolors=col, linewidths=0.9,
                  zorder=3, label=ps.ARMS[arm][0])
    C.axhline(100, color=ps.VERM, lw=1.0, ls="--")
    C.set_xticks([0, 1, 2])
    C.set_xticklabels(["23", "35", "45"])
    C.set_xlabel("Cycling temperature (°C)")
    C.set_ylabel("Calendar share of fade (%)")
    n1 = int(sup[sup.arm == "A1"].cal_exceeds_total.sum())
    n2 = int(sup[sup.arm == "A2"].cal_exceeds_total.sum())
    C.text(0.98, 0.98, f"calendar term > observed fade:\nA1 {n1} cells, A2 {n2} cells", transform=C.transAxes, ha="right", va="top",
           fontsize=7.5)
    C.legend(loc="upper left", fontsize=7.5, handletextpad=0.1, borderaxespad=0.1, labelspacing=0.25)
    C.set_ylim(0, 128)
    C.set_title("Calendar share, cycled cells", fontsize=8.5, pad=4)

    # d Arrhenius
    D = ax[3]
    arr = S["arrhenius"]
    Tk = np.array(arr["T_C"]) + 273.15
    xk = 1000 / Tk
    cols = [ps.BLUE, ps.GREEN, ps.ORANGE, ps.VERM]
    mks = ["o", "s", "^", "D"]
    for i, soc in enumerate(arr["soc"]):
        m, l, h = (np.array(arr["ln_rate"][k][i]) for k in ("mean", "lo", "hi"))
        D.fill_between(xk, l, h, color=cols[i], alpha=0.25, lw=0)
        D.plot(xk, m, color=cols[i], marker=mks[i], ms=4, lw=1.2, label=f"SOC {soc:g} %")
    D.set_xlabel("1000 / T (K$^{-1}$)")
    D.set_ylabel("ln rate (pp / 500 d)")
    sec = D.secondary_xaxis("top", functions=(lambda x: 1000 / x - 273.15, lambda t: 1000 / (t + 273.15)))
    sec.set_xticks(arr["T_C"])
    sec.set_xlabel("Temperature (°C)", fontsize=8, labelpad=2)
    D.legend(loc="upper right", fontsize=7.5, handletextpad=0.3, borderaxespad=0.1, labelspacing=0.25)

    fig.canvas.draw()
    ps.label_panels(fig, ax)
    ps.finish(fig, "fig6_storage", prov, a.out_dir)


if __name__ == "__main__":
    main()
