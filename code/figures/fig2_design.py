"""Fig. 2: design map of the Samsung 50E test matrix, with laboratory and stage colouring (the confound), and replicate fade.

Panels a-d use METADATA ONLY (experiments_meta.csv: identifiers and test conditions); panels e-f use the check-up table
(columns as data/processed/samsung_checkups.csv: cell_id, lab, stage, type, T_C, SOC_max, DoD, C_ch, C_dch, elapsed_days,
retention) and are refused until runs/prereg/FROZEN exists (retention blinding, PREREG_v2 3.3(9)).
Panel g (PREREG_v4 section 14): composition of the nested max-min training subsets at m = 8, 16, 32 (conditions per temperature and laboratory) of ONE outer fold, from the
`subsets.json` and `train_condition_meta.json` of the grid runs (identifiers only). All numbers are design counts of identifiers; no statistic is computed.
Encoding: colour = laboratory; stage 1 = filled marker / solid line, stage 2 = open marker / dashed line.
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


def conditions(meta):
    sto = meta[meta.type == "k"].copy()
    cyc = meta[meta.type == "z"].copy()
    gs = sto.groupby(["amb_temp_tp", "soc_max_tp"]).agg(n=("cell", "size"), labs=("lab", lambda x: tuple(sorted(set(x)))),
                                                         stages=("stage", lambda x: tuple(sorted(set(x))))).reset_index()
    gc = cyc.groupby(["amb_temp_tp", "soc_max_tp", "dod_tp", "c_ch_tp", "c_dch_tp"]).agg(
        n=("cell", "size"), labs=("lab", lambda x: tuple(sorted(set(x)))), stages=("stage", lambda x: tuple(sorted(set(x))))).reset_index()
    return gs, gc


def lab_of(labs):
    return labs[0] if len(labs) == 1 else None


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--meta", required=True, help="experiments_meta.csv (metadata only)")
    ap.add_argument("--fade", required=True, help="check-up table with retention (panels e-f)")
    ap.add_argument("--subset-runs", required=True, help="grid run directories (or their parent): subsets.json + train_condition_meta.json (panel g)")
    ap.add_argument("--fold", type=int, default=0, help="outer fold shown in panel g")
    a = ap.parse_args()
    ps.apply()
    prov = ps.Provenance(a.fade)
    prov.require_frozen("Fig. 2 panels e-f")
    meta = pd.read_csv(ps.need(a.meta))
    meta.columns = [c.strip() for c in meta.columns]
    fade = pd.read_csv(ps.need(a.fade))
    gs, gc = conditions(meta)

    fig = plt.figure(figsize=(ps.W_FULL, 15.4 * ps.CM))
    gsp = fig.add_gridspec(3, 3, left=0.075, right=0.99, top=0.965, bottom=0.15, hspace=0.80, wspace=0.40)
    ax = [fig.add_subplot(gsp[i // 3, i % 3]) for i in range(6)] + [fig.add_subplot(gsp[2, 0:2])]

    # a: storage T x SOC
    A = ax[0]
    for r in gs.itertuples():
        labs = r.labs
        for lab in labs:
            col = ps.LAB_COL[lab]
            dy = (labs.index(lab) - (len(labs) - 1) / 2) * 2.4
            filled = 1 in r.stages
            A.scatter(100 * r.soc_max_tp, r.amb_temp_tp + dy, s=10 + 3.2 * r.n / len(labs), marker="o",
                      c=col if filled else "white", edgecolors=col, linewidths=1.0, zorder=3)
    big = gs.loc[gs.n.idxmax()]
    A.annotate(f"{int(big.n)} cells", (100 * big.soc_max_tp, big.amb_temp_tp), xytext=(0, 11), textcoords="offset points",
               ha="center", fontsize=7.5)
    A.set_yticks([10, 23, 45])
    A.set_ylim(2, 52)
    A.set_xlim(-5, 107)
    A.set_xlabel("Storage SOC (%)")
    A.set_ylabel(ps.LBL["T"])
    A.set_title(f"Storage ({len(gs)} conditions)", fontsize=8.5, pad=4)

    # b: cycling T x DoD
    B = ax[1]
    for i_, r in enumerate(gc.itertuples()):
        lab = lab_of(r.labs)
        col = ps.LAB_COL[lab] if lab else "#555555"
        mk = "o" if lab else "D"
        dx = ((i_ * 37) % 100 / 100.0 - 0.5) * 2.6          # display jitter by row index (deterministic)
        B.scatter(r.amb_temp_tp + dx, 100 * r.dod_tp, s=8 + 2.6 * r.n, marker=mk, c=col, alpha=0.85, edgecolors="white",
                  linewidths=0.4, zorder=3)
    B.set_xticks([23, 35, 45])
    B.set_xlim(19, 49)
    B.set_xlabel(ps.LBL["T"])
    B.set_ylabel(ps.LBL["dod"])
    B.set_title(f"Cycling ({len(gc)} conditions)", fontsize=8.5, pad=4)

    # c: cycling charge x discharge rate
    C = ax[2]
    for r in gc.itertuples():
        lab = lab_of(r.labs)
        col = ps.LAB_COL[lab] if lab else "#555555"
        C.scatter(r.c_ch_tp, r.c_dch_tp, s=8 + 2.6 * r.n, marker="o" if lab else "D", c=col, alpha=0.85, edgecolors="white",
                  linewidths=0.4, zorder=3)
    C.set_xlabel(ps.LBL["cch"])
    C.set_ylabel(ps.LBL["cdch"])
    C.set_title("Cycling, rate space", fontsize=8.5, pad=4)

    # d: cells per temperature, laboratory and stage
    D = ax[3]
    labs_all = ["SIE", "INT", "HM"]
    groups = [("sto", 10), ("sto", 23), ("sto", 45), ("cyc", 23), ("cyc", 35), ("cyc", 45)]
    xs = np.array([0, 1, 2, 3.8, 4.8, 5.8])
    for x, (typ, T) in zip(xs, groups):
        sub = meta[(meta.type == ("k" if typ == "sto" else "z")) & (meta.amb_temp_tp == T)]
        bottom = 0
        for lab in labs_all:
            for stage in (1, 2):
                n = int(((sub.lab == lab) & (sub.stage == stage)).sum())
                if n:
                    D.bar(x, n, 0.72, bottom=bottom, color=ps.LAB_COL[lab] if stage == 1 else "white", ec=ps.LAB_COL[lab],
                          lw=0.9, hatch=None if stage == 1 else "////", zorder=3)
                    bottom += n
        D.text(x, bottom + 1.5, f"{bottom}", ha="center", va="bottom", fontsize=7.5)
    D.set_xticks(xs)
    D.set_xticklabels(["10", "23", "45", "23", "35", "45"])
    D.set_xlabel("Temperature (°C)")
    D.set_ylabel("Cells")
    D.set_ylim(0, 98)
    D.text(1, 90, "storage", ha="center", fontsize=8, color="#444444")
    D.text(4.8, 90, "cycling", ha="center", fontsize=8, color="#444444")
    D.set_title("Cells by laboratory and stage", fontsize=8.5, pad=4)

    # e, f: replicate fade
    def curves(axx, sub, title):
        for cid, g in sub.groupby("cell_id"):
            g = g.sort_values("elapsed_days")
            lab, stage = g.lab.iloc[0], int(g.stage.iloc[0])
            axx.plot(np.r_[0, g.elapsed_days], np.r_[100, 100 * g.retention], color=ps.LAB_COL[lab], lw=0.9,
                     ls="-" if stage == 1 else (0, (3, 1.6)), alpha=0.9)
        axx.set_xlabel("Days since reference")
        axx.set_ylabel(ps.LBL["ret"])
        axx.set_title(title, fontsize=8.5, pad=4)

    fc = fade[fade.type == "z"]
    key = ["T_C", "SOC_max", "DoD", "C_ch", "C_dch"]
    cnt = fc.groupby(key).cell_id.nunique()
    k = cnt.idxmax()
    sub = fc[(fc[key] == pd.Series(k, index=key)).all(axis=1)]
    curves(ax[4], sub, f"Cycling replicates\n{cnt.max()} cells, {k[0]:g} °C")
    fs = fade[fade.type == "k"]
    cnt = fs.groupby(["T_C", "SOC_max"]).cell_id.nunique()
    k2 = cnt.idxmax()
    sub2 = fs[(fs.T_C == k2[0]) & (fs.SOC_max == k2[1])]
    curves(ax[5], sub2, f"Storage replicates\n{cnt.max()} cells, {k2[0]:g} °C, {100 * k2[1]:.0f} %")

    # g: nested max-min subsets of one outer fold
    G = ax[6]
    runs = [r for r in pdt.expand_runs(a.subset_runs) if int(pdt.run_config(r)["fold"]) == a.fold]
    byM = {pdt.run_m(r): r for r in runs}
    xs, labs_all = [], ["SIE", "INT", "HM"]
    xpos = 0.0
    ticks, tl = [], []
    temps = sorted({ps.parse_cond(c)["T"] for r in byM.values() for c in ps.load_json(r / "subsets.json")["kept"]})
    for mm in sorted(byM):
        sub = ps.load_json(byM[mm] / "subsets.json")
        meta_t = ps.load_json(byM[mm] / "train_condition_meta.json")
        for T in temps:
            bottom = 0
            for lab in labs_all:
                n = sum(1 for c in sub["kept"] if ps.parse_cond(c)["T"] == T and meta_t[c]["lab"] == lab)
                if n:
                    G.bar(xpos, n, 0.8, bottom=bottom, color=ps.LAB_COL[lab], zorder=3)
                    bottom += n
            G.text(xpos, bottom + 0.3, f"{bottom}", ha="center", va="bottom", fontsize=7.5)
            ticks.append(xpos)
            tl.append(f"{T:g}")
            xpos += 1.0
        G.text(xpos - 0.5 * len(temps) - 0.5, -0.2, f"$m$ = {mm}", ha="center", va="top", fontsize=8, transform=G.get_xaxis_transform(), clip_on=False)
        xpos += 0.9
    G.set_xticks(ticks)
    G.set_xticklabels(tl)
    G.set_xlabel("Cycling temperature (°C), by nested subset size", labelpad=14)
    G.set_ylabel("Training conditions")
    G.set_title(f"Nested max-min subsets, outer fold {a.fold}", fontsize=8.5, pad=4)
    handles = [Line2D([], [], marker="o", ls="none", color=ps.LAB_COL[l], ms=5, label=f"Laboratory {l}") for l in labs_all]
    handles += [Line2D([], [], marker="D", ls="none", color="#555555", ms=4.5, label="Several laboratories"),
                Line2D([], [], marker="o", ls="none", color="#555555", ms=5, label="Stage 1 (filled, solid)"),
                Line2D([], [], marker="o", ls="none", color="#555555", mfc="white", ms=5, label="Stage 2 (open, dashed)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.015), fontsize=7.5, columnspacing=1.0,
               handletextpad=0.3)
    fig.canvas.draw()
    ps.label_panels(fig, ax)
    ps.finish(fig, "fig2_design", prov, a.out_dir)


if __name__ == "__main__":
    main()
