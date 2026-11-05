"""Fig. 5: learned stress functions with fold x seed envelopes (PREREG_v2 11a items 1, 2, 5).

a  calendar activation energy E(SOC) of the calendar KAN, with the dataset authors' Arrhenius parameter (A10) dashed
b  calendar rate prefactor a(SOC) (rate at 23 C)
c  storage fade rate against SOC at each storage temperature (SOC > 80 % exists in stage 1 only: shaded)
d-h cyclic partial dependences ln r_cyc(x) (others at their training median, centred): PINN-KAN envelope, additive GAM
   (A4) dashed, direction implied by the dataset authors' cycle model (A10) dotted
Input: --run (Test B run directory with stress_functions.json written by the analysis step).
Envelope = min-max over the members stated in the file (outer folds x final-refit seeds).
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps


def band(ax, x, d, color, label=None, lw=1.5, alpha=0.28):
    x = np.asarray(x)
    ax.fill_between(x, d["lo"], d["hi"], color=color, alpha=alpha, lw=0)
    ax.plot(x, d["mean"], color=color, lw=lw, label=label)


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    ps.apply()
    prov = ps.Provenance(a.run)
    prov.require_frozen("Fig. 5")
    S = ps.load_json(ps.need(Path(a.run) / "stress_functions.json", "(analysis step output)"))
    cal, rate, cyc = S["calendar"], S["storage_rate"], S["cyclic"]

    fig = plt.figure(figsize=(ps.W_FULL, 14.6 * ps.CM))
    gs = fig.add_gridspec(3, 3, left=0.083, right=0.99, top=0.965, bottom=0.115, hspace=0.62, wspace=0.34)
    ax = [fig.add_subplot(gs[i // 3, i % 3]) for i in range(9)]
    soc = np.array(cal["soc"])

    # a: E(SOC)
    A = ax[0]
    band(A, soc, cal["E_kJmol"], ps.BLUE)
    A.axhline(cal["A10_E_kJmol"], color=ps.ARMS["A10"][1], ls="--", lw=1.3)
    A.set_ylabel("$E_{\\mathrm{a}}$ (kJ mol$^{-1}$)")
    A.set_xlabel(ps.LBL["soc"])
    A.set_title("Calendar activation energy", fontsize=8.5, pad=4)
    # b: a(SOC)
    B = ax[1]
    band(B, soc, cal["a_pp500"], ps.BLUE)
    B.set_ylabel("$a$ (pp / 500 d)")
    B.set_xlabel(ps.LBL["soc"])
    B.set_title("Rate prefactor at 23 °C", fontsize=8.5, pad=4)
    # c: rate vs SOC at storage temperatures
    C = ax[2]
    rs = np.array(rate["soc"])
    for i, T in enumerate(rate["T_C"]):
        d = dict(mean=rate["mean"][i], lo=rate["lo"][i], hi=rate["hi"][i])
        band(C, rs, d, ps.TEMP_COL[T], lw=1.3, alpha=0.30)
    C.axvspan(80, 100, color="#E8E8E8", lw=0, zorder=0)
    C.text(90, 0.52, "stage 1\nonly", transform=C.get_xaxis_transform(), ha="center", va="center", fontsize=7.5, color="#444444")
    C.set_yscale("log")
    C.set_ylabel("Rate (pp / 500 d)")
    C.set_xlabel(ps.LBL["soc"])
    C.set_title("Storage rate by temperature", fontsize=8.5, pad=4)
    # d-h: cyclic partial dependences
    spec = [("T", ps.LBL["T"]), ("soc_mid", ps.LBL["soc_mid"]), ("dod", ps.LBL["dod"]), ("c_ch", ps.LBL["cch"]),
            ("c_dch", ps.LBL["cdch"])]
    for k, (name, xl) in enumerate(spec):
        P = ax[3 + k]
        if name == "T":                                          # temperature is aliased with laboratory: no curve, no direction line (D022b N1(a), permanent)
            P.axis("off")
            P.text(0.5, 0.5, "temperature (aliased with\nlaboratory; no form or\nsign reported)", transform=P.transAxes, ha="center", va="center", fontsize=8, color="#444444")
            continue
        d = cyc[name]
        x = np.array(d["x"])
        band(P, x, d["A1"], ps.BLUE)
        P.plot(x, d["A4"]["mean"], color=ps.ARMS["A4"][1], ls="--", lw=1.3)
        P.plot(x, d["A10"]["mean"], color=ps.ARMS["A10"][1], ls=":", lw=1.6)
        P.axhline(0, color="#BBBBBB", lw=0.5, zorder=0)
        P.set_xlabel(xl)
        if k % 3 == 0:
            P.set_ylabel("$\\Delta\\ln r_{\\mathrm{cyc}}$")
    ax[3].set_title("Cyclic partial dependences", fontsize=8.5, pad=4, loc="left")

    # legend panel
    L = ax[8]
    L.axis("off")
    hs = [Patch(fc=ps.BLUE, alpha=0.35, label=f"PINN-KAN envelope\n({S['n_members']} members: min–max)"),
          Line2D([], [], color=ps.BLUE, lw=1.5, label="PINN-KAN, mean"),
          Line2D([], [], color=ps.ARMS["A4"][1], ls="--", lw=1.3, label="Additive GAM (A4)"),
          Line2D([], [], color=ps.ARMS["A10"][1], ls="--", lw=1.3, label="A10, calendar $E_{\mathrm{a}}$"),
          Line2D([], [], color=ps.ARMS["A10"][1], ls=":", lw=1.6, label="A10, cyclic direction")]
    L.legend(handles=hs, loc="center left", fontsize=7.5, labelspacing=0.7, handlelength=2.2, bbox_to_anchor=(-0.05, 0.5))
    # temperature key inside c
    fig.canvas.draw()
    for T in rate["T_C"]:
        pass
    C.legend(handles=[Line2D([], [], color=ps.TEMP_COL[T], lw=1.4, label=f"{T} °C") for T in rate["T_C"]], loc="upper left",
             fontsize=7.5, handlelength=1.4, borderaxespad=0.1, labelspacing=0.25)
    ps.label_panels(fig, ax[:8])
    ps.finish(fig, "fig5_stress", prov, a.out_dir)


if __name__ == "__main__":
    main()
