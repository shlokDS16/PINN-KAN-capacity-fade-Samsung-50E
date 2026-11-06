"""Render every figure and table on SYNTHETIC demo runs (Design R2 layout).  Optional: --regen rebuilds the demo runs; --demo-dir / --out-dir redirect.

    .venv\\Scripts\\python.exe -P code\\figures\\run_all_demo.py [--regen] [--demo-dir DIR] [--out-dir DIR]

For the confirmatory results call the same scripts with the real run directories and analysis directory (see code/figures/README.md); they refuse to read
Samsung data until runs/prereg/FROZEN exists. Nothing here reads a Samsung, ISU or SNL file: the demo design is invented (make_demo_runs.py).
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PY = sys.executable


def run(script, *args):
    cmd = [PY, "-P", str(HERE / script), *map(str, args)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(script, "OK" if r.returncode == 0 else "FAILED")
    if r.returncode:
        print(r.stdout[-1500:], r.stderr[-2500:])
    return r.returncode


def render_all(D, out_dir=None):
    """every item of PREREG_v4 section 14 from the demo directory D; returns the number of failed scripts"""
    D = Path(D)
    A, G = D / "analysis", D / "grid"
    o = ["--out-dir", out_dir] if out_dir else []
    rc = 0
    rc += bool(run("fig1_schematic.py", "--run-s2", D / "test_S2", "--run-b", G, "--run-c", D / "test_C", *o))
    rc += bool(run("fig2_design.py", "--meta", D / "design" / "experiments_meta.csv", "--fade", D / "design" / "fade_curves.csv", "--subset-runs", G, *o))
    rc += bool(run("fig3_forecasts.py", "--runs-b", G, "--run-c", D / "test_C", *o))
    rc += bool(run("fig4_forest.py", "--stats", A / "contrasts_v4_B.json", *o))
    rc += bool(run("fig5_stress.py", "--physval", A / "physval_11a.json", "--stats", A / "contrasts_v4_B.json", "--runs", G, *o))
    rc += bool(run("fig6_storage.py", "--run-s2", D / "test_S2", "--runs", G, "--stats", A / "contrasts_v4_B.json", "--physval", A / "physval_11a.json", "--controls", A / "controls.json", *o))
    rc += bool(run("fig7_residual.py", "--run", G, *o))
    rc += bool(run("fig8_synthetic.py", "--run", D / "synthetic_H7", "--controls", A / "controls.json", *o))
    rc += bool(run("fig_graphical_abstract.py", "--meta", D / "design" / "experiments_meta.csv", "--stats", A / "contrasts_v4_B.json", *o))
    rc += bool(run("table1.py", "--analysis", A, *o))
    rc += bool(run("table2.py", "--analysis", A, *o))
    return rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regen", action="store_true")
    ap.add_argument("--demo-dir", default=str(ROOT / "runs" / "figdemo_SYNTHETIC"))
    ap.add_argument("--out-dir", default=None, help="default: paper/figures and paper/tables (the tracked SYNTHETIC previews)")
    a = ap.parse_args()
    if a.regen:
        run("make_demo_runs.py", "--out", a.demo_dir)
    sys.exit(render_all(a.demo_dir, a.out_dir))


if __name__ == "__main__":
    main()
