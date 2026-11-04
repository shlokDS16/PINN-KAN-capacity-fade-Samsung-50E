"""Table 1 (booktabs LaTeX + CSV for Word): arms x {Test B, C, S2, ISU, SNL}.

Panel A: forecast RMSE in pp, mean over held-out conditions +- SD of that mean over the final-refit seeds (metrics.json,
`seed_sd_of_mean`; a reproducibility statement, not a confidence interval); best value in bold, second best underlined (per column).
Panel B (Test B and Test C): median over conditions of the error ratio comparator / PINN-KAN with its exact 95 % order-statistic
interval, tier from the statistics step (S superior, N non-inferior, - none, n.t. gated and not tested, desc. descriptive), median
fit time, parameter count, and E/R_LOO and E/R_WARP (descriptive reference quantities, never margins).
Inputs: --run-b --run-c --run-s2 --run-isu --run-snl (run directories) --analysis (directory with contrasts_<test>.json, reference.json).
All numbers come from these files; nothing is typed here.
"""
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pk_style as ps
import pk_data as pdt

ORDER = ["A1", "A2", "A3", "A4", "A5", "A7", "A9", "A10", "A11", "A12", "A13", "A14", "R1", "R2"]
NAME = {"A1": "A1 PINN-KAN", "A2": "A2 Hard-ODE KAN", "A3": "A3 Parametric", "A4": "A4 Additive GAM",
        "A5": "A5 Interaction GAM", "A7": "A7 MLP stress map", "A9": "A9 Data-only $F$",
        "A10": "A10 Semi-empirical", "A11": "A11 GP-ARD", "A12": "A12 LightGBM", "A13": "A13 Cycling only",
        "A14": "A14 Storage only", "R1": "R1 Persistence", "R2": "R2 Window-linear"}
TIER_TXT = {"S": "S", "N": "N", "-": "--", None: ""}


def tex_escape(s):
    return s.replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")


def rank_marks(vals):
    """vals: dict arm -> float or None; returns dict arm -> 'best'/'second'/None (lower is better)."""
    v = sorted((x, a) for a, x in vals.items() if x is not None)
    out = {}
    if v:
        out[v[0][1]] = "best"
    if len(v) > 1:
        out[v[1][1]] = "second"
    return out


def entry_for(contrasts, arm):
    ent = None
    for k, e in contrasts["contrasts"].items():
        if e["comp"] == arm and k != "H1b":
            ent = e
    h1b = contrasts["contrasts"].get("H1b")
    tier = ent.get("tier") if ent else None
    status = ent.get("status", "") if ent else ""
    if h1b and h1b["comp"] == arm:
        tier, status = h1b.get("tier"), h1b.get("status", "")
    return ent, tier, status


def tier_text(tier, status):
    if "reference" in status:
        return "ref."
    if tier in ("S", "N", "-"):
        return TIER_TXT[tier]
    return "n.t." if "not tested" in status else "desc."


def main():
    ap = ps.common_args(__doc__)
    ap.add_argument("--run-b", required=True)
    ap.add_argument("--run-c", required=True)
    ap.add_argument("--run-s2", required=True)
    ap.add_argument("--run-isu", required=True)
    ap.add_argument("--run-snl", required=True)
    ap.add_argument("--analysis", required=True)
    a = ap.parse_args()
    prov = ps.Provenance(a.run_b, a.run_c, a.run_s2, a.run_isu, a.run_snl, a.analysis)
    prov.require_frozen("Table 1")
    tests = [("B", a.run_b), ("C", a.run_c), ("S2", a.run_s2), ("ISU", a.run_isu), ("SNL", a.run_snl)]
    M = {t: pdt.load_metrics(r)["outer_test"] for t, r in tests}
    ncond = {t: next(iter(M[t].values()))["n_conditions"] for t in M}
    an = Path(a.analysis)
    cB, cC = pdt.load_contrasts(an / "contrasts_B.json"), pdt.load_contrasts(an / "contrasts_C.json")
    ref = ps.load_json(ps.need(an / "reference.json"))["values"]
    tim = ps.load_json(ps.need(Path(a.run_b) / "timings.json"))
    nseed = len(ps.load_json(ps.need(Path(a.run_b) / "config.json")).get("seeds", []))
    arms = [x for x in ORDER if any(x in M[t] for t in M)]

    # ---------------- panel A
    marks = {t: rank_marks({x: M[t][x]["primary_pp"] for x in M[t]}) for t in M}
    rowsA, csvA = [], []
    for x in arms:
        cells, cc = [], []
        for t in M:
            if x in M[t]:
                m = M[t][x]
                s = f"{m['primary_pp']:.2f} $\\pm$ {m['seed_sd_of_mean']:.2f}"
                mk = marks[t].get(x)
                if mk == "best":
                    s = f"\\textbf{{{s}}}"
                elif mk == "second":
                    s = f"\\underline{{{s}}}"
                cells.append(s)
                cc.append(f"{m['primary_pp']:.2f} +- {m['seed_sd_of_mean']:.2f}")
            else:
                cells.append("--")
                cc.append("")
        rowsA.append((x, cells))
        csvA.append([NAME[x].replace("$", "")] + cc)

    # ---------------- panel B
    rowsB, csvB = [], []
    for x in arms:
        if x == "A1":
            rowsB.append((x, ["--", "", "--", "", f"{tim['A1']['median_fit_seconds']:.1f}", f"{M['B']['A1']['n_params']:d}",
                              f"{M['B']['A1']['primary_pp'] / ref['B']['R_LOO']:.2f}", f"{M['B']['A1']['primary_pp'] / ref['B']['R_WARP']:.2f}"]))
            csvB.append([NAME[x].replace("$", ""), "", "", "", "", f"{tim['A1']['median_fit_seconds']:.1f}", M['B']['A1']['n_params'],
                         f"{M['B']['A1']['primary_pp'] / ref['B']['R_LOO']:.2f}", f"{M['B']['A1']['primary_pp'] / ref['B']['R_WARP']:.2f}"])
            continue
        cells, cc = [], []
        for con, t in ((cB, "B"), (cC, "C")):
            if x in M[t]:
                ent, tier, status = entry_for(con, x)
                if ent is None:
                    for k, e in con["contrasts"].items():
                        if e["comp"] == x:
                            ent = e
                if ent:
                    lo, hi = ent["median_ci95"]
                    rr = f"{np.exp(ent['median_L']):.2f} [{np.exp(lo):.2f}, {np.exp(hi):.2f}]"
                    tt = tier_text(tier, status)
                    cells += [rr, tt]
                    cc += [rr, tt]
                    continue
            cells += ["--", ""]
            cc += ["", ""]
        if x in M["B"]:
            tm = f"{tim[x]['median_fit_seconds']:.1f}" if x in tim else "--"
            npar = f"{M['B'][x]['n_params']:d}"
            e1 = f"{M['B'][x]['primary_pp'] / ref['B']['R_LOO']:.2f}"
            e2 = f"{M['B'][x]['primary_pp'] / ref['B']['R_WARP']:.2f}"
        else:
            tm = npar = e1 = e2 = "--"
        cells += [tm, npar, e1, e2]
        cc += [tm, npar, e1, e2]
        rowsB.append((x, cells))
        csvB.append([NAME[x].replace("$", "")] + cc)

    n = lambda t: ncond[t]
    hdrA = [f"Test B ($n$={n('B')})", f"Test C ($n$={n('C')})", f"S2 ($n$={n('S2')})", f"ISU ($n$={n('ISU')})", f"SNL ($n$={n('SNL')})"]
    synth = prov.synthetic
    L = []
    L.append("% Table 1, generated by code/figures/table1.py from run files; do not edit by hand.")
    if synth:
        L.append("% SYNTHETIC DEMO - NOT RESULTS")
    L.append("\\begin{table}[t]")
    L.append("\\centering\\small\\setlength{\\tabcolsep}{4.2pt}")
    if synth:
        L.append("{\\color{red}\\bfseries SYNTHETIC DEMO -- NOT RESULTS}\\par\\smallskip")
    L.append("\\begin{tabular}{l" + "c" * 5 + "}")
    L.append("\\toprule")
    L.append("\\multicolumn{6}{l}{\\textbf{A. Forecast RMSE (pp) on held-out conditions, mean $\\pm$ SD over " + str(nseed) + " seeds}} \\\\")
    L.append("\\midrule")
    L.append("Arm & " + " & ".join(hdrA) + " \\\\")
    L.append("\\midrule")
    for x, cells in rowsA:
        if x == "R1":
            L.append("\\midrule")
        L.append(f"{NAME[x]} & " + " & ".join(cells) + " \\\\")
    L.append("\\bottomrule")
    L.append("\\end{tabular}")
    L.append("\\par\\bigskip")
    L.append("\\begin{tabular}{l cc cc rrcc}")
    L.append("\\toprule")
    L.append("\\multicolumn{9}{l}{\\textbf{B. Comparison with PINN-KAN, cost and reference ratios}} \\\\")
    L.append("\\midrule")
    L.append(" & \\multicolumn{2}{c}{Test B} & \\multicolumn{2}{c}{Test C} & Fit time & Parameters & \\multicolumn{2}{c}{Test B $E/R$} \\\\")
    L.append("\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){8-9}")
    L.append("Arm & Ratio [95\\% int.] & Tier & Ratio [95\\% int.] & Tier & (s) & (count) & LOO & WARP \\\\")
    L.append("\\midrule")
    for x, cells in rowsB:
        if x == "R1":
            L.append("\\midrule")
        L.append(f"{NAME[x]} & " + " & ".join(cells) + " \\\\")
    L.append("\\bottomrule")
    L.append("\\end{tabular}")
    cap = ("\\caption{" + ("\\textcolor{red}{SYNTHETIC DEMO -- NOT RESULTS.} " if synth else "") +
           "Held-out accuracy of all arms. Panel A: forecast RMSE in percentage points (pp) averaged over held-out conditions (the unit); "
           f"$\\pm$ is the SD of that mean over the {nseed} final-refit seeds (reproducibility, not a confidence interval); best value in bold, "
           "second best underlined. ISU and SNL are secondary and not blind. Panel B: median over conditions of the error ratio "
           "comparator/PINN-KAN (above 1: PINN-KAN better) with its exact 95\\,\\% order-statistic interval; tier from the preregistered "
           "sign test (S superior, N non-inferior, -- neither; n.t.\\ gated and not tested; desc.\\ descriptive); $E/R$ is the "
           "Test B error divided by the replicate spread (LOO) or the window-aware replicate predictor (WARP), descriptive only.}")
    L.append(cap)
    L.append("\\end{table}")
    TAB = Path(a.out_dir) if a.out_dir else ps.TAB_OUT
    TAB.mkdir(parents=True, exist_ok=True)
    out = TAB / f"table1{prov.suffix()}.tex"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    with open(TAB / f"table1{prov.suffix()}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if synth:
            w.writerow(["SYNTHETIC DEMO - NOT RESULTS"])
        w.writerow(["Panel A: RMSE pp, mean +- seed SD"])
        w.writerow(["Arm"] + [h.replace("$", "") for h in hdrA])
        w.writerows(csvA)
        w.writerow([])
        w.writerow(["Panel B"])
        w.writerow(["Arm", "Test B ratio [95% int.]", "Tier B", "Test C ratio [95% int.]", "Tier C", "Fit time (s)", "Parameters", "E/R_LOO", "E/R_WARP"])
        w.writerows(csvB)
    print("wrote", out)


if __name__ == "__main__":
    main()
