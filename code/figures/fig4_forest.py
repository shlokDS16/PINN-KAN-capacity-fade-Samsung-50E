"""Fig. 4: forest plot of paired condition-level contrasts, every arm against A1 (PINN-KAN) on Test B.

Inputs (paths as arguments):
  --contrasts  analysis/contrasts_B.json   (written by the statistics step; tier, Holm level, per-condition log ratios)
  --run        test_B run directory        (only used for provenance and for the fallback when --contrasts is absent)
Shows, per row: per-condition ln(S_comp / S_A1) as grey dots, the median with its exact order-statistic 95 % interval
(the estimand of the adopted exact sign test, TYPE1_SIGNFLIP.md), the margins ln(1.02) (tier S) and -ln(1.10) (tier N),
and in the right-hand columns wins, mean paired difference in pp with BCa interval, and tier.
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps
import pk_data as pd_

ROWS = [  # (contrast key, label, group)
    ("H1a", "H1a  A9 data-only F", "Primary family"),
    ("H1b", None, "Primary family"),
    ("pool_A3", "A3 parametric", "pool"),
    ("pool_A4", "A4 additive GAM", "pool"),
    ("pool_A5", "A5 interaction GAM", "pool"),
    ("pool_A7", "A7 MLP stress map", "pool"),
    ("H6", "H6  A10 semi-empirical model", "Primary family"),
    ("H1c_A11", "H1c  A11 GP-ARD", "Key secondary (gated)"),
    ("H1c_A12", "H1c  A12 LightGBM", "Key secondary (gated)"),
    ("H2", "H2  A2 hard-ODE KAN", "Decision contrast"),
    ("X1", "X1  A13 cycling cells only", "Descriptive"),
]


def build_from_scores(run):
    """Fallback without the statistics step: descriptive median and order-statistic interval, no tier."""
    sc = pd_.load_scores(run)
    conds = sorted(sc["A1"])
    s1 = np.array([sc["A1"][c] for c in conds])
    out = {}
    names = {"H1a": "A9", "H6": "A10", "H1c_A11": "A11", "H1c_A12": "A12", "H2": "A2", "X1": "A13",
             "pool_A3": "A3", "pool_A4": "A4", "pool_A5": "A5", "pool_A7": "A7"}
    for key, a in names.items():
        if a not in sc:
            continue
        s = np.array([sc[a][c] for c in conds])
        L = np.log(s / s1)
        lo, hi, _ = ps.median_order_ci(L)
        blo, bhi = ps.bootstrap_mean_ci(s - s1, B=3000)
        out[key] = dict(comp=a, L_by_cond=dict(zip(conds, L.tolist())), median_L=float(np.median(L)), median_ci95=[lo, hi],
                        n=len(L), n_wins=int((L > 0).sum()), mean_pp=float((s - s1).mean()), mean_pp_ci95=[blo, bhi], tier=None)
    return dict(margins=dict(S=float(np.log(1.02)), N=float(-np.log(1.10))), contrasts=out, n=len(conds))


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--contrasts", default=None)
    ap.add_argument("--run", required=True, help="Test B run directory")
    a = ap.parse_args()
    ps.apply()
    prov = ps.Provenance(a.run, a.contrasts)
    prov.require_frozen("Fig. 4")
    C = pd_.load_contrasts(a.contrasts) if a.contrasts else build_from_scores(a.run)
    con = C["contrasts"]
    mS, mN = C["margins"]["S"], C["margins"]["N"]

    rows = [r for r in ROWS if r[0] in con]
    # y positions with gaps between groups
    ys, y, last = [], 0.0, None
    for key, lab, grp in rows:
        g = "Primary family" if grp == "pool" and last in (None, "Primary family") else grp
        if last is not None and grp != "pool" and grp != last:
            y -= 0.75
        ys.append(y)
        y -= 1.0
        if grp != "pool":
            last = grp
    ys = np.array(ys)
    ymin, ymax = ys.min() - 1.5, ys.max() + 0.7

    fig = plt.figure(figsize=(ps.W_FULL, 8.6 * ps.CM))
    ax = fig.add_axes([0.262, 0.235, 0.335, 0.62])
    rng = np.random.default_rng(1)

    allL = np.concatenate([list(con[k]["L_by_cond"].values()) for k, _, _ in rows])
    xlo = min(allL.min(), min(con[k]["median_ci95"][0] for k, _, _ in rows), mN) - 0.08
    xhi = max(allL.max(), max(con[k]["median_ci95"][1] for k, _, _ in rows)) + 0.08
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(ymin, ymax)

    ax.axvline(0, color="#444444", lw=0.8, zorder=1)
    ax.axvline(mS, color=ps.GREY, lw=0.8, ls=(0, (3, 2)), zorder=1)
    ax.axvline(mN, color=ps.GREY, lw=0.8, ls=(0, (1, 2)), zorder=1)
    # alternating row bands for the tested contrasts
    for (key, lab, grp), yy in zip(rows, ys):
        if grp == "pool":
            ax.axhspan(yy - 0.5, yy + 0.5, color="#F2F2F2", lw=0, zorder=0)

    xt = ax.get_yaxis_transform()
    hdr_y = ymax + 0.15
    ax.text(1.05, hdr_y, "Wins", transform=xt, ha="left", va="bottom", fontsize=8, fontweight="bold", clip_on=False)
    ax.text(1.27, hdr_y, "Mean Δ (pp) [95 % BCa]", transform=xt, ha="left", va="bottom", fontsize=8, fontweight="bold", clip_on=False)
    ax.text(1.97, hdr_y, "Tier", transform=xt, ha="center", va="bottom", fontsize=8, fontweight="bold", clip_on=False)

    ylabels = []
    for (key, lab, grp), yy in zip(rows, ys):
        e = con[key]
        arm = e["comp"]
        name, col, mk, ls = ps.ARMS[arm]
        pool = grp == "pool"
        L = np.array(list(e["L_by_cond"].values()))
        ax.scatter(L, yy + rng.uniform(-0.28, 0.28, len(L)), s=5, color="#8A8A8A", alpha=0.55, lw=0, zorder=2, clip_on=True)
        lo, hi = e["median_ci95"]
        ax.plot([lo, hi], [yy, yy], color=col, lw=1.6 if not pool else 1.1, solid_capstyle="butt", zorder=4)
        for xe in (lo, hi):
            ax.plot([xe, xe], [yy - 0.18, yy + 0.18], color=col, lw=1.0, zorder=4)
        ax.plot([e["median_L"]], [yy], marker=mk if mk not in "_|" else "o", ms=6.5 if not pool else 4.8,
                mfc=col if not pool else "white", mec=col, mew=1.1, ls="none", zorder=5)
        if key == "H1b":
            lab = f"H1b  best pool arm ({arm})"
        ylabels.append(lab)
        ax.text(1.05, yy, f"{e['n_wins']}/{e['n']}", transform=xt, ha="left", va="center", fontsize=8, clip_on=False)
        lo_, hi_ = e["mean_pp_ci95"]
        ax.text(1.27, yy, f"{ps.fmt(e['mean_pp'])} [{ps.fmt(lo_)}, {ps.fmt(hi_)}]", transform=xt, ha="left", va="center",
                fontsize=8, clip_on=False)
        t = e.get("tier", None)
        if t in ("S", "N", "-"):
            ax.text(1.97, yy, "–" if t == "-" else t, transform=xt, ha="center", va="center", fontsize=8,
                    fontweight="bold", color="white" if t == "S" else "#222222", clip_on=False,
                    bbox=dict(boxstyle="circle,pad=0.22", fc=ps.TIER_COL[t], ec="none"))
        else:
            ax.text(1.97, yy, "n.t." if "not tested" in e.get("status", "") else "desc.", transform=xt, ha="center",
                    va="center", fontsize=7.5, color="#555555", clip_on=False)

    ax.xaxis.set_major_locator(plt.MultipleLocator(0.5))
    ax.set_yticks(ys)
    ax.set_yticklabels(ylabels)
    for tl, (key, lab, grp) in zip(ax.get_yticklabels(), rows):
        if grp == "pool":
            tl.set_fontsize(7.5)
            tl.set_color("#444444")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("ln(error of comparator / error of PINN-KAN), per held-out condition")
    ax.text(-0.04, 0.012, "← comparator better", transform=ax.get_xaxis_transform(), ha="right", va="bottom",
            fontsize=7.5, color="#444444")
    ax.text(0.04, 0.012, "PINN-KAN better →", transform=ax.get_xaxis_transform(), ha="left", va="bottom",
            fontsize=7.5, color="#444444")

    sec = ax.secondary_xaxis("top", functions=(np.exp, np.log))
    rt = [t for t in (0.25, 0.5, 1, 2, 4) if np.exp(xlo) <= t <= np.exp(xhi)]
    sec.set_xticks(rt)
    sec.set_xticklabels([f"{t:g}" for t in rt])
    sec.set_xlabel("Error ratio, comparator / PINN-KAN", fontsize=8, labelpad=3)
    sec.spines["top"].set_visible(True)
    sec.spines["top"].set_linewidth(0.6)

    seen = set()
    for (key, lab, grp), yy in zip(rows, ys):
        g = "Primary family" if grp == "pool" else grp
        if g not in seen:
            seen.add(g)
            ax.text(-0.02, yy + 0.66, g, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=7.5,
                    style="italic", color="#666666", clip_on=False)
    handles = [Line2D([], [], color=ps.BLUE, marker="o", ms=5.5, lw=1.5, label="Median, 95 % interval (order statistics)"),
               Line2D([], [], color="#8A8A8A", marker="o", ms=2.5, lw=0, alpha=0.7, label="One held-out condition"),
               Line2D([], [], color=ps.GREY, lw=0.8, ls=(0, (3, 2)), label="Tier S margin, +2 %"),
               Line2D([], [], color=ps.GREY, lw=0.8, ls=(0, (1, 2)), label="Tier N margin, −10 %")]
    fig.legend(handles=handles, loc="lower center", ncol=2, bbox_to_anchor=(0.43, 0.035), fontsize=7.5, columnspacing=1.2,
               handlelength=1.8, labelspacing=0.3)
    # group labels written in figure coordinates, left of the row labels
    ps.finish(fig, "fig4_forest", prov, a.out_dir)


if __name__ == "__main__":
    main()
