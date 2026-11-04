"""Fig. 1: method schematic. Data strip (storage cell, cycling cell, held-out cell, drawn from run files) feeding the
solution network F, the KAN stress maps inside the law G, the soft residual with its collocation sets and the loss.
Boxes, arrows and spline glyphs are drawn with matplotlib patches (coordinates in mm); the three data panels are real
run data (the cell with the median A1 RMSE of the median-scoring condition of each run). No number is typed into the diagram.
Inputs: --run-s2, --run-b, --run-c (predictions.csv, window.csv, condition_scores.json).
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps
import pk_data as pdt

W, H = 160.0, 93.0
C_F, C_KAN, C_RES, C_IN, C_OUT = "#DCEBF7", "#FBE9C6", "#E6E0F0", "#EFEFEF", "#D9F0E6"


def box(ax, x, y, w, h, fc, ec="#444444", lw=0.8, r=1.6, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, ls=ls, zorder=2))


def arrow(ax, p0, p1, color="#333333", lw=1.0, rad=0.0, ms=7, ls="-"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=ms, lw=lw, color=color,
                                 connectionstyle=f"arc3,rad={rad}", zorder=5, shrinkA=0, shrinkB=0, linestyle=ls))


def line(ax, pts, color="#333333", lw=1.0):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=lw, solid_capstyle="butt", zorder=4)


def txt(ax, x, y, s, size=7.5, ha="center", va="center", **kw):
    return ax.text(x, y, s, fontsize=size, ha=ha, va=va, zorder=6, **kw)


def spline_glyph(ax, x0, y0, w, h, kind, color=ps.BLUE, lw=1.0, frame=True):
    t = np.linspace(0, 1, 40)
    f = {"rise": t ** 2.2, "sat": 1 - np.exp(-3.5 * t), "bump": np.sin(np.pi * t) ** 1.5, "lin": t,
         "s": 1 / (1 + np.exp(-9 * (t - 0.5))), "dip": 1 - np.sin(np.pi * t) ** 1.2}[kind]
    f = 0.1 + 0.8 * (f - f.min()) / (f.max() - f.min() + 1e-9)
    if frame:
        ax.add_patch(Rectangle((x0, y0), w, h, fc="white", ec="#888888", lw=0.5, zorder=3))
    ax.plot(x0 + w * (0.06 + 0.88 * t), y0 + h * f, color=color, lw=lw, zorder=4)


def data_panel(fig, rect_mm, run, title, pick_cond="median"):
    pred, win, sc = pdt.load_predictions(run), pdt.load_window(run), pdt.load_scores(run)
    conds = sorted(sc["A1"], key=lambda c: sc["A1"][c])
    cond = conds[len(conds) // 2]
    cell, _ = pdt.median_cell(pred, cond, "A1")
    (tw, yw), (tf, yo), Y = pdt.cell_curve(pred, win, cell, "A1")
    x, y, w, h = rect_mm
    ax = fig.add_axes([x / W, y / H, w / W, h / H])
    tw = np.r_[0, tw]
    yw = np.r_[100, yw]
    ax.axvspan(0, tw[-1], color="#E4E4E4", lw=0)
    ax.fill_between(tf, Y.min(0), Y.max(0), color=ps.BLUE, alpha=0.3, lw=0)
    ax.plot(tf, Y.mean(0), color=ps.BLUE, lw=1.3)
    ax.plot(tw, yw, "o", ms=2.8, color="#222222")
    ax.plot(tf, yo, "o", ms=2.8, color="#222222", mfc="white", mew=0.8)
    ax.set_title(f"{title}\n{ps.cond_text(cond)}", fontsize=7.5, pad=2, linespacing=1.1)
    ax.tick_params(labelsize=7, length=2, pad=1.5)
    ax.xaxis.set_major_locator(plt.MaxNLocator(3))
    ax.yaxis.set_major_locator(plt.MaxNLocator(3))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_ylabel("Retention (%)", fontsize=7.5, labelpad=1)
    ax.set_xlabel("days", fontsize=7, labelpad=-1, loc="right")
    return ax


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--run-s2", required=True)
    ap.add_argument("--run-b", required=True)
    ap.add_argument("--run-c", required=True)
    a = ap.parse_args()
    ps.apply()
    prov = ps.Provenance(a.run_s2, a.run_b, a.run_c)
    prov.require_frozen("Fig. 1 data strip")

    fig = plt.figure(figsize=(ps.W_FULL, 9.7 * ps.CM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    # ---- data strip
    data_panel(fig, (11, 71, 38, 16), a.run_s2, "Storage cell")
    data_panel(fig, (64, 71, 38, 16), a.run_b, "Cycling cell")
    data_panel(fig, (118, 71, 38, 16), a.run_c, "Held-out cell")
    # ---- row B: inputs -> F -> forecast
    box(ax, 2, 41, 40, 19, C_IN)
    txt(ax, 22, 56.2, "Inputs", size=8, fontweight="bold")
    txt(ax, 22, 49.5, "time $t$, stress vector $\\mathbf{s}$\n(storage: $T$, SOC; cycling:\n$T$, SOC$_{\\mathrm{mid}}$, DoD, $C_{\\mathrm{ch}}$, $C_{\\mathrm{dch}}$)", size=7)
    txt(ax, 22, 43.8, "cell latent $z_c$, window data", size=7)
    line(ax, [(30, 65.2), (30, 63.2), (22, 63.2)])
    line(ax, [(83, 65.2), (83, 63.2), (22, 63.2)])
    arrow(ax, (22, 63.2), (22, 60.2))
    box(ax, 50, 41, 52, 19, C_F)
    txt(ax, 76, 57.0, "Solution network $F$ (tanh MLP)", size=8, fontweight="bold")
    # node glyph
    cols = [3, 4, 4, 3, 1]
    xs = np.linspace(57, 95, len(cols))
    pts = []
    for cx, n in zip(xs, cols):
        ys = np.linspace(46.0, 53.0, n) if n > 1 else [48.8]
        pts.append([(cx, yy) for yy in ys])
    for c0, c1 in zip(pts[:-1], pts[1:]):
        for p in c0:
            for q in c1:
                ax.plot([p[0], q[0]], [p[1], q[1]], color="#8AA5C2", lw=0.3, zorder=3)
    for col in pts:
        for p in col:
            ax.add_patch(Circle(p, 0.8, fc="white", ec=ps.BLUE, lw=0.7, zorder=4))
    txt(ax, 76, 43.0, "hard initial condition, $\\hat y(t;\\mathbf{s},z_c)$", size=7)
    arrow(ax, (42, 50), (50, 50))
    box(ax, 111, 41, 47, 19, C_OUT)
    txt(ax, 134.5, 56.2, "Forecast", size=8, fontweight="bold")
    txt(ax, 134.5, 49.0, "retention at every later\ncheck-up of an unseen\ncondition", size=7)
    arrow(ax, (102, 50), (111, 50))
    arrow(ax, (137, 60.2), (137, 65.5))
    # ---- row C: law G with KAN stress maps
    box(ax, 2, 3, 92, 34, "#FFF8EA", ls="-")
    txt(ax, 48, 33.6, "Law $G$:   $\\mathrm{d}y/\\mathrm{d}t=\\left[r_{\\mathrm{cal}}(T,\\mathrm{SOC})+r_{\\mathrm{cyc}}(\\mathbf{s})\\,\\nu(t)\\right]h(y)$", size=7.8)
    box(ax, 5, 6, 40, 23, C_KAN)
    txt(ax, 25, 26, "Calendar KAN", size=7.8, fontweight="bold")
    txt(ax, 25, 22.5, "SOC $\\rightarrow$ ($a$, $E_{\\mathrm{a}}$)", size=7.2)
    spline_glyph(ax, 9, 11.0, 13, 9, "rise", color=ps.BLUE)
    spline_glyph(ax, 27, 11.0, 13, 9, "sat", color=ps.BLUE)
    txt(ax, 15.5, 10.2, "$a$(SOC)", size=6.8, color="#444444", va="top")
    txt(ax, 33.5, 10.2, "$E_{\\mathrm{a}}$(SOC)", size=6.8, color="#444444", va="top")
    box(ax, 49, 6, 42, 23, C_KAN)
    txt(ax, 70, 26, "Cyclic KAN", size=7.8, fontweight="bold")
    txt(ax, 70, 22.5, "$\\mathbf{s}\\rightarrow r_{\\mathrm{cyc}}$", size=7.2)
    # KAN glyph: inputs, hidden, output with spline edges
    xin, xh, xo = 55, 70, 85
    yin = np.linspace(9.5, 19.5, 5)
    yh = np.linspace(11, 18, 3)
    for yi in yin:
        for yy in yh:
            ax.plot([xin, xh], [yi, yy], color="#C9A24D", lw=0.4, zorder=3)
    for yy in yh:
        ax.plot([xh, xo], [yy, 14.5], color="#C9A24D", lw=0.4, zorder=3)
    for yi in yin:
        ax.add_patch(Circle((xin, yi), 0.9, fc="white", ec="#8A6A1A", lw=0.6, zorder=4))
    for yy in yh:
        ax.add_patch(Circle((xh, yy), 0.9, fc="white", ec="#8A6A1A", lw=0.6, zorder=4))
    ax.add_patch(Circle((xo, 14.5), 0.9, fc="white", ec="#8A6A1A", lw=0.6, zorder=4))
    for (xx, yy, k) in ((60.5, 17.0, "s"), (60.5, 12.3, "bump"), (77.5, 13.3, "rise"), (77.5, 17.6, "dip")):
        spline_glyph(ax, xx - 2.6, yy - 1.5, 5.2, 3.0, k, color=ps.BLUE, lw=0.7)
    # ---- row C right: residual, collocation sets, loss
    box(ax, 101, 3, 57, 34, C_RES)
    txt(ax, 129.5, 33.6, "Soft physics residual", size=8, fontweight="bold")
    txt(ax, 129.5, 29.0, "$R=\\partial\\hat y/\\partial t-G(\\hat y)$ at collocation sets", size=7.2)
    titles = ["(a) record end", "(b) hull points", "(c) twins"]
    for k, (cx, ttl) in enumerate(zip((106.0, 123.0, 140.0), titles)):
        ax.add_patch(Rectangle((cx, 12.5), 14.5, 10.5, fc="white", ec="#777777", lw=0.5, zorder=3))
        rg = np.random.default_rng(10 + k)
        if k == 0:
            tt = np.linspace(0, 1, 30)
            ax.plot(cx + 0.7 + 13 * tt, 13.5 + 8.0 * (1 - np.exp(-2.6 * tt)), color="#999999", lw=0.7, zorder=4)
            ax.scatter(np.full(6, cx + 13.5), np.linspace(20.0, 21.4, 6), s=2.2, color=ps.VERM, zorder=5, lw=0)
        elif k == 1:
            ax.scatter(cx + 1 + 12.5 * rg.random(14), 13.5 + 8.5 * rg.random(14), s=2.2, color=ps.VERM, zorder=5, lw=0)
        else:
            ax.scatter(cx + 1 + 12.5 * rg.random(10), 13.5 + 8.5 * rg.random(10), s=2.2, color="#BBBBBB", zorder=4, lw=0)
            ax.scatter(np.full(4, cx + 11.0), 14.5 + 2.0 * np.arange(4), s=4.2, marker="D", color=ps.VERM, zorder=5, lw=0)
        txt(ax, cx + 7.25, 10.2, ttl, size=6.8, va="top", linespacing=1.05)
    txt(ax, 129.5, 5.0, "$\\mathcal{L}=\\mathcal{L}_{\\mathrm{data}}+\\lambda_{\\mathrm{res}}\\mathcal{L}_{\\mathrm{res}}$ + KAN sparsity", size=7.4)
    # arrows between blocks
    arrow(ax, (94, 20), (101, 20))
    line(ax, [(90, 41), (90, 38.8)], lw=1.0)
    line(ax, [(90, 38.8), (115, 38.8)], lw=1.0)
    arrow(ax, (115, 38.8), (115, 37.2))
    txt(ax, 76, 38.8, "", size=6)
    # F -> data loss note
    txt(ax, 96.8, 40.0, "", size=6)
    ps.finish(fig, "fig1_schematic", prov, a.out_dir)


if __name__ == "__main__":
    main()
