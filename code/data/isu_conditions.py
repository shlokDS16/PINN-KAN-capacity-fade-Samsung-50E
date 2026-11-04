"""P1(a): verify ISU-ILCC Table A1 against README_V2.0.pdf (converted by markitdown) and build the processed tables.

Run:  python -I code/data/isu_conditions.py <ROOT>
Inputs  (all read as text/CSV only; nothing from a download is executed):
  runs/pilot_P1/README_V2.0.md   markitdown conversion of data/raw/isu_ilcc_figshare_22582234/README_V2.0.pdf
  debates/D010_topic/pilot_scratch/isu_profile.py   proposer's hand transcription (parsed as text with ast, NOT executed)
  data/raw/isu_ilcc_small/capacity_fade.zip         251 CSV (time on test [weeks], remaining capacity [Ah])
Outputs:
  data/processed/isu_conditions.csv   group, charge_c, discharge_c, dod_pct   (63 rows, verified table)
  data/processed/isu_capacity.csv     cell, group, week, retention, capacity_ah
  runs/pilot_P1/isu_table_check.json  mismatch report
"""
import ast
import csv
import io
import json
import os
import re
import sys
import zipfile

USER_SITE = os.path.join(os.environ.get("APPDATA", ""), "Python", "Python314", "site-packages")
if os.path.isdir(USER_SITE) and USER_SITE not in sys.path:
    sys.path.append(USER_SITE)
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

NUM = re.compile(r"^-?\d+(\.\d+)?%?$")


def parse_table_flat(md_path):
    """Robust variant: flatten the whole appendix to a token stream and split on the label words."""
    txt = open(md_path, encoding="utf8", errors="replace").read()
    a = txt.index("Group #")
    b = txt.index("A2.", a)
    toks = re.sub(r"\s+", " ", txt[a:b]).strip()
    # split into labelled runs
    parts = re.split(r"(Group #|Charging C-rate|Discharging C-rate|Mean DoD)", toks)
    runs = []  # (label, [floats])
    for i in range(1, len(parts), 2):
        lab, body = parts[i], parts[i + 1]
        vals = []
        for t in body.split():
            if NUM.match(t):
                vals.append(float(t.rstrip("%")))
        runs.append((lab, vals))
    return runs


def _list_expr(expr):
    """Parse '[a,b]*N+[c,d]' without eval: split on '+', literal_eval each list, apply an optional '*N'."""
    out = []
    for part in expr.split("+"):
        m = re.match(r"^(\[[^\]]*\])(?:\*(\d+))?$", part.strip())
        out += ast.literal_eval(m.group(1)) * (int(m.group(2)) if m.group(2) else 1)
    return out


def scratch_lists(path):
    """Read the proposer's hand-transcribed lists as data (text parse; the scratch file is never executed)."""
    out = {}
    for line in open(path, encoding="utf8").read().splitlines():
        m = re.match(r"^(chg1|dis1|dod1|chg2|dis2|dod2)=(.*)$", line.strip())
        if m:
            out[m.group(1)] = _list_expr(m.group(2))
    return out


def main():
    root = sys.argv[1]
    md = os.path.join(root, "runs", "pilot_P1", "README_V2.0.md")
    runs = parse_table_flat(md)
    labels = [r[0] for r in runs]
    # expected order: Group#, Charging, Discharging, MeanDoD, Group#, Charging, Discharging, MeanDoD
    assert labels == ["Group #", "Charging C-rate", "Discharging C-rate", "Mean DoD"] * 2, labels
    groups = runs[0][1] + runs[4][1]
    # The page footer number '10' sits glued before 'Mean DoD' (page number artefact): drop a trailing 10 if the
    # DoD block has one value too many.
    chg = runs[1][1] + runs[5][1]
    dis = runs[2][1] + runs[6][1]
    dod_raw = runs[3][1] + runs[7][1]
    note = []
    if len(runs[2][1]) == 41:  # page number '10' was appended to the discharging block
        pass
    report = {"lens_raw": {"group": len(groups), "charge": len(chg), "discharge": len(dis), "dod": len(dod_raw)}}
    # page number artefact: the numeral '10' printed at the page break lands at the end of the discharging block
    # (block 1) because the PDF text order puts the footer before 'Mean DoD'.
    if len(dis) == 64 and dis[40] == 10.0:
        report["artefact"] = "dropped page-number token 10 at index 40 of the discharging C-rate column"
        dis = dis[:40] + dis[41:]
    report["lens_clean"] = {"group": len(groups), "charge": len(chg), "discharge": len(dis), "dod": len(dod_raw)}
    assert len(groups) == len(chg) == len(dis) == len(dod_raw) == 63, report
    pdf = {int(g): (c, d, o) for g, c, d, o in zip(groups, chg, dis, dod_raw)}

    # proposer's transcription (text parse, not executed as code)
    sc = scratch_lists(os.path.join(root, "debates", "D010_topic", "pilot_scratch", "isu_profile.py"))
    gall = list(range(1, 15)) + list(range(16, 65))
    C = sc["chg1"] + sc["chg2"]; D = sc["dis1"] + sc["dis2"]; O = sc["dod1"] + sc["dod2"]
    scratch = {g: (c, d, o) for g, c, d, o in zip(gall, C, D, O)}

    mism = []
    for g in sorted(set(pdf) | set(scratch)):
        a, b = pdf.get(g), scratch.get(g)
        if a is None or b is None:
            mism.append({"group": g, "pdf": a, "scratch": b, "kind": "missing"})
            continue
        for name, x, y in zip(("charge_c", "discharge_c", "dod_pct"), a, b):
            if abs(x - y) > 1e-9:
                mism.append({"group": g, "field": name, "pdf": x, "scratch": y})
    report["groups_pdf"] = sorted(pdf)
    report["n_groups_pdf"] = len(pdf)
    report["n_groups_scratch"] = len(scratch)
    report["mismatches"] = mism
    report["n_mismatches"] = len(mism)

    # sanity: groups present in capacity_fade
    z = zipfile.ZipFile(os.path.join(root, "data", "raw", "isu_ilcc_small", "capacity_fade.zip"))
    names = [n for n in z.namelist() if n.endswith(".csv")]
    gset = {int(re.search(r"G(\d+)C(\d+)", n).group(1)) for n in names}
    report["groups_in_capacity_fade"] = sorted(gset)
    report["groups_pdf_minus_capacity"] = sorted(set(pdf) - gset)
    report["groups_capacity_minus_pdf"] = sorted(gset - set(pdf))

    # processed conditions
    os.makedirs(os.path.join(root, "data", "processed"), exist_ok=True)
    cond = pd.DataFrame(
        [(g, *pdf[g]) for g in sorted(pdf)], columns=["group", "charge_c", "discharge_c", "dod_pct"])
    cond.to_csv(os.path.join(root, "data", "processed", "isu_conditions.csv"), index=False)

    # capacity table
    rows = []
    for n in sorted(names):
        m = re.search(r"G(\d+)C(\d+)", n)
        g, c = int(m.group(1)), int(m.group(2))
        r = list(csv.reader(io.StringIO(z.read(n).decode("utf8"))))
        hdr, body = r[0], r[1:]
        t = np.array([float(a[0]) for a in body]); q = np.array([float(a[1]) for a in body])
        for ti, qi in zip(t, q):
            rows.append((f"G{g}C{c}", g, ti, qi / q[0], qi))
    cap = pd.DataFrame(rows, columns=["cell", "group", "week", "retention", "capacity_ah"])
    cap.to_csv(os.path.join(root, "data", "processed", "isu_capacity.csv"), index=False)
    report["capacity_header_example"] = hdr
    report["capacity_rows"] = len(cap)
    report["capacity_cells"] = int(cap["cell"].nunique())
    report["cells_min_max_points"] = [int(cap.groupby("cell").size().min()), int(cap.groupby("cell").size().max())]
    report["retention_nonfinite"] = int((~np.isfinite(cap["retention"])).sum())
    report["first_point_week_nonzero_cells"] = int((cap.groupby("cell")["week"].first() != 0).sum())
    report["retention_gt_1.05"] = int((cap["retention"] > 1.05).sum())
    with open(os.path.join(root, "runs", "pilot_P1", "isu_table_check.json"), "w", encoding="utf8") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps({k: v for k, v in report.items() if k not in ("groups_pdf", "groups_in_capacity_fade")}, indent=1))


if __name__ == "__main__":
    main()
