"""Render every figure and table on the SYNTHETIC demo runs (runs/figdemo_SYNTHETIC).  Optional: --regen rebuilds the demo runs.

    .venv\\Scripts\\python.exe -P code\\figures\\run_all_demo.py [--regen]

For the confirmatory results, call the same scripts with the real run directories (see code/figures/README.md); they refuse to read
Samsung data until runs/prereg/FROZEN exists.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D = ROOT / "runs" / "figdemo_SYNTHETIC"
META = ROOT / "data" / "raw" / "samsung50e_meta" / "experiments_meta.csv"
PY = sys.executable


def run(script, *args):
    cmd = [PY, "-P", str(HERE / script), *map(str, args)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(script, "OK" if r.returncode == 0 else "FAILED")
    if r.returncode:
        print(r.stdout[-1500:], r.stderr[-2500:])
    return r.returncode


def main():
    if "--regen" in sys.argv:
        run("make_demo_runs.py")
    B, C, S2 = D / "test_B", D / "test_C", D / "test_S2"
    A = D / "analysis"
    rc = 0
    rc |= run("fig1_schematic.py", "--run-s2", S2, "--run-b", B, "--run-c", C)
    rc |= run("fig2_design.py", "--meta", META, "--fade", D / "design" / "fade_curves.csv")
    rc |= run("fig3_forecasts.py", "--run-b", B, "--run-c", C)
    rc |= run("fig4_forest.py", "--run", B, "--contrasts", A / "contrasts_B.json")
    rc |= run("fig5_stress.py", "--run", B)
    rc |= run("fig6_storage.py", "--run-s2", S2, "--run-b", B)
    rc |= run("fig7_residual.py", "--run", B)
    rc |= run("fig8_synthetic.py", "--run", D / "synthetic_H7")
    rc |= run("fig_graphical_abstract.py", "--meta", META, "--run-b", B, "--run-s2", S2, "--contrasts", A / "contrasts_B.json")
    rc |= run("table1.py", "--run-b", B, "--run-c", C, "--run-s2", S2, "--run-isu", D / "isu_B", "--run-snl", D / "snl_B", "--analysis", A)
    rc |= run("table2.py", "--run-b", B, "--analysis", A)
    sys.exit(rc)


if __name__ == "__main__":
    main()
