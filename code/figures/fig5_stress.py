"""Fig. 5: learned stress functions with fold x seed envelopes and the descriptive stability table of the extracted laws (PREREG_v4 section 14; 11a items 1, 2, 5-7).

a  calendar activation energy E(SOC) with the envelope (physval_11a item 1); the dataset authors' Arrhenius parameter (A10) only if physval_11a carries the comparison
b  calendar rate prefactor a(SOC) (rate at 23 C; run-writer stress_functions.json, envelope merged over the grid runs)
c  storage fade rate against SOC at each storage temperature with the envelope (physval_11a item 2; SOC > 80 % exists in stage 1 only)
d  temperature: the fixed label only (permanent T rule, D022b N1(a): no curve, no direction, no verdict against A10 for A1's learned cyclic law)
e-h cyclic partial dependences of SOC_mid, DoD, C_ch, C_dch: envelope of PINN-KAN (physval_11a item 5), additive GAM A4 dashed and the direction of the dataset
   authors' cycle model (A10) dotted (run-writer stress_functions.json)
i  descriptive stability table of the extracted closed-form laws A15 and G15 side by side (stats step: contrasts_v4_B.json edge_wording.stability); temperature = fixed label
Inputs: --physval analysis/physval_11a.json, --stats analysis/contrasts_v4_B.json, --runs grid run directories (m = 32 runs with stress_functions.json).
READ-ONLY: envelopes, votes and shares are values of those files. NOT AVAILABLE (gap G4): closed forms, coefficient counts, BIC and the Latin-hypercube stability metric of A15 / G15
are not written by the run writer or the statistics step, so they are not drawn.
"""
import sys
import textwrap
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps
import pk_data as pdt

T_LABEL_FALLBACK = "temperature (aliased with\nlaboratory; no form or\nsign reported)"


def band(ax, x, d, color, lw=1.5, alpha=0.28):
    x = np.asarray(x)
    ax.fill_between(x, d["lo"], d["hi"], color=color, alpha=alpha, lw=0)
    ax.plot(x, d["mean"], color=color, lw=lw)


def stability_panel(ax, stats):
    ax.axis("off")
    st = stats.get("edge_wording", {}).get("stability", {})
    arms = st.get("arms", {})
    if not arms:
        ax.text(0.5, 0.5, "stability table not available\n(no extracted laws in the runs)", transform=ax.transAxes, ha="center", va="center", fontsize=7.5, color="#555555")
        return
    rows = {a: {r["input"]: r for r in arms[a]["stability_table"]} for a in arms}
    names = list(next(iter(rows.values())))
    ax.text(0.0, 1.02, "Stability of extracted laws", transform=ax.transAxes, fontsize=8.5, va="bottom")
    hdr = ["input", "A15\n+ / −", "G15\n+ / −", "A15\ntie", "A15\nadd."]
    xs = [0.0, 0.27, 0.50, 0.72, 0.88]
    for x, h in zip(xs, hdr):
        ax.text(x, 0.93, h, transform=ax.transAxes, fontsize=7, va="top", ha="left", fontweight="bold", linespacing=1.05)
    for i, nm in enumerate(names):
        y = 0.70 - 0.13 * i
        r15, g15 = rows.get("A15", {}).get(nm), rows.get("G15", {}).get(nm)
        if r15 is not None and "display" in r15:
            ax.text(xs[0], y, nm, transform=ax.transAxes, fontsize=7, va="center")
            ax.text(xs[1], y, "temperature (aliased with\nlaboratory; no form or\nsign reported)", transform=ax.transAxes, fontsize=6, va="center", color="#444444", style="italic", linespacing=1.0)
            continue
        sv = lambda r: f"{r['sign_votes']['+']} / {r['sign_votes']['-']}" if r else "–"
        ax.text(xs[0], y, nm, transform=ax.transAxes, fontsize=7, va="center")
        ax.text(xs[1], y, sv(r15), transform=ax.transAxes, fontsize=7, va="center")
        ax.text(xs[2], y, sv(g15), transform=ax.transAxes, fontsize=7, va="center")
        ax.text(xs[3], y, f"{r15['tie_share']:.2f}" if r15 else "–", transform=ax.transAxes, fontsize=7, va="center")
        ax.text(xs[4], y, f"{r15['additive_share']:.2f}" if r15 else "–", transform=ax.transAxes, fontsize=7, va="center")
    cap = arms[next(iter(arms))].get("caption", st.get("caption", ""))
    ax.text(0.0, 0.0, textwrap.fill(cap, 44), transform=ax.transAxes, fontsize=6.3, va="top", color="#444444", style="italic")


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--physval", required=True)
    ap.add_argument("--stats", required=True)
    ap.add_argument("--runs", required=True, help="grid run directories (or their parent); the m = 32 runs with stress_functions.json are used")
    a = ap.parse_args()
    ps.apply()
    runs = [r for r in pdt.runs_by_m(pdt.expand_runs(a.runs)).get(32, []) if (r / "stress_functions.json").exists()]
    prov = ps.Provenance(a.physval, a.stats, *runs)
    prov.require_frozen("Fig. 5")
    PV = ps.load_json(ps.need(a.physval))
    ST = pdt.load_stats(a.stats)
    SF = [ps.load_json(r / "stress_functions.json") for r in runs]

    fig = plt.figure(figsize=(ps.W_FULL, 14.6 * ps.CM))
    gs = fig.add_gridspec(3, 3, left=0.083, right=0.99, top=0.965, bottom=0.17, hspace=0.70, wspace=0.34)
    ax = [fig.add_subplot(gs[i // 3, i % 3]) for i in range(9)]
    ae = PV["item1"]["activation_energy"]
    soc = np.array(ae["soc"])
    A = ax[0]
    band(A, soc, ae["E_kJmol"], ps.BLUE)
    va = PV["item1"].get("vs_A10")
    if va and "A10_E_kJmol" in va:
        A.axhline(va["A10_E_kJmol"], color=ps.ARMS["A10"][1], ls="--", lw=1.3)
    A.set_ylabel("$E_{\\mathrm{a}}$ (kJ mol$^{-1}$)")
    A.set_xlabel(ps.LBL["soc"])
    A.set_title("Calendar activation energy", fontsize=8.5, pad=4)
    B = ax[1]
    if SF:
        band(B, SF[0]["calendar"]["soc"], pdt.merge_bands([s["calendar"]["a_pp500"] for s in SF]), ps.BLUE)
    B.set_ylabel("$a$ (pp / 500 d)")
    B.set_xlabel(ps.LBL["soc"])
    B.set_title("Rate prefactor at 23 °C", fontsize=8.5, pad=4)
    C = ax[2]
    temps = sorted(PV["item2"]["per_temperature"], key=float)
    for T in temps:
        d = PV["item2"]["per_temperature"][T]["rate_pp500d"]
        band(C, soc, d, ps.TEMP_COL[int(float(T))], lw=1.3, alpha=0.30)
    C.axvspan(80, 100, color="#E8E8E8", lw=0, zorder=0)
    C.text(90, 0.52, "stage 1\nonly", transform=C.get_xaxis_transform(), ha="center", va="center", fontsize=7.5, color="#444444")
    C.set_yscale("log")
    C.set_ylabel("Rate (pp / 500 d)")
    C.set_xlabel(ps.LBL["soc"])
    C.set_title("Storage rate by temperature", fontsize=8.5, pad=4)
    C.legend(handles=[Line2D([], [], color=ps.TEMP_COL[int(float(T))], lw=1.4, label=f"{float(T):g} °C") for T in temps], loc="upper left", fontsize=7.5, handlelength=1.4,
             borderaxespad=0.1, labelspacing=0.25)
    # d-h: cyclic partial dependences; temperature = label only
    D = PV["item5"]["directions"]
    spec = [("T", ps.LBL["T"]), ("soc_mid", ps.LBL["soc_mid"]), ("dod", ps.LBL["dod"]), ("c_ch", ps.LBL["cch"]), ("c_dch", ps.LBL["cdch"])]
    for k, (name, xl) in enumerate(spec):
        P = ax[3 + k]
        if name == "T":
            P.axis("off")
            P.text(0.5, 0.5, "temperature (aliased with\nlaboratory; no form or\nsign reported)", transform=P.transAxes, ha="center", va="center", fontsize=8, color="#444444")
            continue
        d = {"x": D[name]["x"], "A1": D[name]["envelope"]}                  # the statistics step's envelope of the fold x seed members
        x = np.array(d["x"])
        band(P, x, d["A1"], ps.BLUE)
        if SF and name in SF[0]["cyclic"]:
            c0 = SF[0]["cyclic"][name]
            if "A4" in c0:
                P.plot(c0["x"], c0["A4"]["mean"], color=ps.ARMS["A4"][1], ls="--", lw=1.3)
            if "A10" in c0:
                P.plot(c0["x"], c0["A10"]["mean"], color=ps.ARMS["A10"][1], ls=":", lw=1.6)
        P.axhline(0, color="#BBBBBB", lw=0.5, zorder=0)
        P.set_xlabel(xl)
        if k % 3 == 0:
            P.set_ylabel("$\\Delta\\ln r_{\\mathrm{cyc}}$")
    ax[3].set_title("Cyclic partial dependences", fontsize=8.5, pad=4, loc="left")
    stability_panel(ax[8], ST)
    hs = [Patch(fc=ps.BLUE, alpha=0.35, label=f"PINN-KAN envelope ({PV['n_members']} members: min–max)"),
          Line2D([], [], color=ps.ARMS["A4"][1], ls="--", lw=1.3, label="Additive GAM (A4)"),
          Line2D([], [], color=ps.ARMS["A10"][1], ls="--", lw=1.3, label="A10, calendar $E_{\\mathrm{a}}$"),
          Line2D([], [], color=ps.ARMS["A10"][1], ls=":", lw=1.6, label="A10, cyclic direction (not for temperature)")]
    fig.legend(handles=hs, loc="lower center", ncol=2, bbox_to_anchor=(0.5, 0.005), fontsize=7.5, columnspacing=1.4, handlelength=2.0, labelspacing=0.3)
    fig.canvas.draw()
    ps.label_panels(fig, ax[:8])
    ps.finish(fig, "fig5_stress", prov, a.out_dir)


if __name__ == "__main__":
    main()
