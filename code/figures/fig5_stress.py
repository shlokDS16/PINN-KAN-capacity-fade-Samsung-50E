"""Fig. 5: learned stress functions with fold x seed envelopes and the extracted closed-form laws A15 and G15 (PREREG_v4 section 14; 11a items 1, 2, 5-7).

a  calendar activation energy E(SOC) with the envelope (physval_11a item 1); the dataset authors' Arrhenius parameter (A10) only if physval_11a carries the comparison
b  calendar rate prefactor a(SOC) (physval_11a `a_of_soc`)
c  storage fade rate against SOC at each storage temperature with the envelope (physval_11a item 2; SOC > 80 % exists in stage 1 only)
d  temperature: the fixed label only (permanent T rule, D022b N1(a): no curve, no direction, no verdict against A10 for A1, A4, A10, A15 or G15)
e-h cyclic partial dependences of SOC_mid, DoD, C_ch, C_dch: envelope of PINN-KAN, the additive GAM A4 (dashed) and the direction of the dataset authors' cycle model A10 (dotted)
   (physval_11a `partial_dependence_overlays`), and the extracted laws A15 (median over the 25 fold-by-seed laws, solid) and G15 (dashed), law_summary.json
i  law summary: stability metric, coefficient counts, training-side BIC of A15 and G15 (law_summary.json)
j  descriptive sign-vote table of the extracted laws, A15 and G15 side by side (contrasts_v4_B.json edge_wording.stability), temperature = fixed label
k  closed forms of the representative laws (the law with the median training-side BIC of each arm), temperature masked
Inputs: --physval analysis/physval_11a.json, --stats analysis/contrasts_v4_B.json, --law-summary analysis/law_summary.json. READ-ONLY: every curve, count, metric and
form is a value of those files; descriptive, no licence or comparative wording ("descriptive; not evidence that the training design identifies these forms").
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


def band(ax, x, d, color, lw=1.5, alpha=0.28):
    x = np.asarray(x)
    ax.fill_between(x, d["lo"], d["hi"], color=color, alpha=alpha, lw=0)
    ax.plot(x, d["mean"], color=color, lw=lw)


def metrics_panel(ax, LS):
    ax.axis("off")
    arms = LS.get("arms", {})
    ax.text(0.0, 1.02, "Extracted laws, summary", transform=ax.transAxes, fontsize=8.5, va="bottom")
    if not arms:
        ax.text(0.5, 0.5, "law summary not available", transform=ax.transAxes, ha="center", va="center", fontsize=7.5, color="#555555")
        return
    rows = [("stability\n(SD / range)", lambda a: "–" if a["stability"].get("median_sd_over_range") is None else f"{a['stability']['median_sd_over_range']:.3f}"),
            ("coefficients\nmed. [min, max]", lambda a: f"{a['n_coefs']['median']:g} [{a['n_coefs']['min']:g}, {a['n_coefs']['max']:g}]"),
            ("train BIC\nmedian", lambda a: f"{a['train_bic']['median']:.0f}"),
            ("laws", lambda a: f"{a['n_laws']}")]
    xs = [0.0, 0.44, 0.76]
    for x, h in zip(xs, ("", "A15", "G15")):
        ax.text(x, 0.93, h, transform=ax.transAxes, fontsize=7.5, va="top", fontweight="bold")
    for i, (nm, f) in enumerate(rows):
        y = 0.74 - 0.19 * i
        ax.text(xs[0], y, nm, transform=ax.transAxes, fontsize=6.5, va="center", linespacing=1.0)
        for x, arm in zip(xs[1:], ("A15", "G15")):
            ax.text(x, y, f(arms[arm]) if arm in arms else "–", transform=ax.transAxes, fontsize=6.2, va="center")


def votes_panel(ax, stats):
    ax.axis("off")
    st = stats.get("edge_wording", {}).get("stability", {})
    arms = st.get("arms", {})
    ax.text(0.0, 1.02, "Sign votes of the extracted laws (descriptive)", transform=ax.transAxes, fontsize=8.5, va="bottom")
    if not arms:
        ax.text(0.5, 0.5, "stability table not available", transform=ax.transAxes, ha="center", va="center", fontsize=7.5, color="#555555")
        return
    rows = {a: {r["input"]: r for r in arms[a]["stability_table"]} for a in arms}
    names = list(next(iter(rows.values())))
    hdr = ["input", "A15 votes\n+ / −", "G15 votes\n+ / −", "A15 tie\nshare", "A15 additive\nshare"]
    xs = [0.0, 0.14, 0.32, 0.50, 0.68]
    for x, h in zip(xs, hdr):
        ax.text(x, 0.93, h, transform=ax.transAxes, fontsize=7, va="top", ha="left", fontweight="bold", linespacing=1.05)
    for i, nm in enumerate(names):
        y = 0.64 - 0.115 * i
        r15, g15 = rows.get("A15", {}).get(nm), rows.get("G15", {}).get(nm)
        ax.text(xs[0], y, nm, transform=ax.transAxes, fontsize=7, va="center")
        if r15 is not None and "display" in r15:
            ax.text(xs[1], y, "temperature (aliased with laboratory; no form or sign reported)", transform=ax.transAxes, fontsize=6.6, va="center", color="#444444", style="italic")
            continue
        sv = lambda r: f"{r['sign_votes']['+']} / {r['sign_votes']['-']}" if r else "–"
        ax.text(xs[1], y, sv(r15), transform=ax.transAxes, fontsize=7, va="center")
        ax.text(xs[2], y, sv(g15), transform=ax.transAxes, fontsize=7, va="center")
        ax.text(xs[3], y, f"{r15['tie_share']:.2f}" if r15 else "–", transform=ax.transAxes, fontsize=7, va="center")
        ax.text(xs[4], y, f"{r15['additive_share']:.2f}" if r15 else "–", transform=ax.transAxes, fontsize=7, va="center")
    cap = arms[next(iter(arms))].get("caption", "")
    ax.text(0.0, -0.06, cap, transform=ax.transAxes, fontsize=6.5, va="top", color="#444444", style="italic")


def forms_panel(ax, LS):
    ax.axis("off")
    ax.text(0.0, 1.02, "Closed forms, median BIC", transform=ax.transAxes, fontsize=8.5, va="bottom")
    y = 0.95
    for arm in ("A15", "G15"):
        a = LS.get("arms", {}).get(arm)
        if not a:
            continue
        r = a["representative"]
        head = f"{arm}: fold {r['fold']}, seed {r['seed']}\n{r['n_coefs']} coef., BIC {r['train_bic']:.0f}"
        wl = [w for line in str(r["closed_form"]).splitlines() for w in textwrap.wrap(line, 30)]
        body = "\n".join(wl[:8] + (["... (full form in law_summary.json)"] if len(wl) > 8 else []))
        ax.text(0.0, y, head, transform=ax.transAxes, fontsize=6.8, va="top", fontweight="bold", linespacing=1.05)
        ax.text(0.0, y - 0.11, body, transform=ax.transAxes, fontsize=5.8, va="top", family="monospace", linespacing=1.05)
        y -= 0.50


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--physval", required=True)
    ap.add_argument("--stats", required=True)
    ap.add_argument("--law-summary", required=True)
    a = ap.parse_args()
    ps.apply()
    prov = ps.Provenance(a.physval, a.stats, a.law_summary)
    prov.require_frozen("Fig. 5")
    PV = ps.load_json(ps.need(a.physval))
    ST = pdt.load_stats(a.stats)
    LS = ps.load_json(ps.need(a.law_summary, "(statistics step output law_summary.json)"))

    fig = plt.figure(figsize=(ps.W_FULL, 21.6 * ps.CM))
    gs = fig.add_gridspec(4, 3, left=0.083, right=0.99, top=0.972, bottom=0.125, hspace=0.80, wspace=0.34, height_ratios=[1, 1, 1, 1.9])
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
    ao = PV["a_of_soc"]
    band(B, ao["soc"], ao["a_pp500"], ps.BLUE)
    B.set_ylabel("$a$ (pp / 500 d)")
    B.set_xlabel(ps.LBL["soc"])
    B.set_title("Rate prefactor at 25 °C", fontsize=8.5, pad=4)
    C = ax[2]
    temps = sorted(PV["item2"]["per_temperature"], key=float)
    for T in temps:
        band(C, soc, PV["item2"]["per_temperature"][T]["rate_pp500d"], ps.TEMP_COL[int(float(T))], lw=1.3, alpha=0.30)
    C.axvspan(80, 100, color="#E8E8E8", lw=0, zorder=0)
    C.text(90, 0.52, "stage 1\nonly", transform=C.get_xaxis_transform(), ha="center", va="center", fontsize=7.5, color="#444444")
    C.set_yscale("log")
    C.set_ylabel("Rate (pp / 500 d)")
    C.set_xlabel(ps.LBL["soc"])
    C.set_title("Storage rate by temperature", fontsize=8.5, pad=4)
    C.legend(handles=[Line2D([], [], color=ps.TEMP_COL[int(float(T))], lw=1.4, label=f"{float(T):g} °C") for T in temps], loc="upper left", fontsize=7.5, handlelength=1.4,
             borderaxespad=0.1, labelspacing=0.25)
    # d-h: cyclic partial dependences; temperature = label only
    OV = PV["partial_dependence_overlays"]["per_input"]
    spec = [("T", ps.LBL["T"]), ("soc_mid", ps.LBL["soc_mid"]), ("dod", ps.LBL["dod"]), ("c_ch", ps.LBL["cch"]), ("c_dch", ps.LBL["cdch"])]
    for k, (name, xl) in enumerate(spec):
        P = ax[3 + k]
        if name == "T":
            P.axis("off")
            P.text(0.5, 0.5, "temperature (aliased with\nlaboratory; no form or\nsign reported)", transform=P.transAxes, ha="center", va="center", fontsize=8, color="#444444")
            continue
        d = {"x": OV[name]["x"], "A1": OV[name]["A1"]}                       # the statistics step's envelope of the fold x seed members
        x = np.array(d["x"])
        band(P, x, d["A1"], ps.BLUE)
        if OV[name].get("A4_mean") is not None:
            P.plot(x, OV[name]["A4_mean"], color=ps.ARMS["A4"][1], ls="--", lw=1.2)
        if OV[name].get("A10_mean") is not None:
            P.plot(x, OV[name]["A10_mean"], color=ps.ARMS["A10"][1], ls=":", lw=1.6)
        for arm, ls_ in (("A15", "-"), ("G15", "--")):
            pdc = LS.get("arms", {}).get(arm, {}).get("partial_dependence", {}).get(name)
            if pdc:
                P.plot(pdc["x"], pdc["median"], color=ps.ARMS[arm][1], ls=ls_, lw=1.0)
        P.axhline(0, color="#BBBBBB", lw=0.5, zorder=0)
        P.set_xlabel(xl)
        if k % 3 == 0:
            P.set_ylabel("$\\Delta\\ln r_{\\mathrm{cyc}}$")
    ax[3].text(0.5, 0.92, "Cyclic partial dependences", transform=ax[3].transAxes, ha="center", va="top", fontsize=8.5)
    metrics_panel(ax[8], LS)
    V = fig.add_subplot(gs[3, 0:2])
    F = fig.add_subplot(gs[3, 2])
    votes_panel(V, ST)
    forms_panel(F, LS)
    hs = [Patch(fc=ps.BLUE, alpha=0.35, label=f"PINN-KAN envelope ({PV['n_members']} members: min–max)"),
          Line2D([], [], color=ps.ARMS["A4"][1], ls="--", lw=1.3, label="Additive GAM (A4)"),
          Line2D([], [], color=ps.ARMS["A10"][1], ls=":", lw=1.6, label="A10 cycle model (not for temperature)"),
          Line2D([], [], color=ps.ARMS["A15"][1], ls="-", lw=1.0, label="Extracted A15, median of the laws"),
          Line2D([], [], color=ps.ARMS["G15"][1], ls="--", lw=1.0, label="Extracted G15, median of the laws"),
          Line2D([], [], color=ps.ARMS["A10"][1], ls="--", lw=1.3, label="A10, calendar $E_{\\mathrm{a}}$")]
    fig.legend(handles=hs, loc="lower center", ncol=2, bbox_to_anchor=(0.5, 0.004), fontsize=7.0, columnspacing=1.2, handlelength=2.0, labelspacing=0.3)
    fig.canvas.draw()
    ps.label_panels(fig, ax[:8])
    ps.finish(fig, "fig5_stress", prov, a.out_dir)


if __name__ == "__main__":
    main()
