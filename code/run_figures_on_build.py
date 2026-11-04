"""Render the figure and table scripts (code/figures/) on the run directories written by pinnkan on SYNTHETIC data (proof that the scripts consume the run writer's
and the statistics step's own outputs).  Usage:  .venv/Scripts/python.exe -P code/run_figures_on_build.py [--prefix build_v1_fig] [--h7 runs/<h7 run>]

Directories (runs/): <prefix>_synth_B / _C / _S2 (synthetic confirmatory runs, test labels B, C, S2), <prefix>_synth_ISUslot / _SNLslot (synthetic runs standing in for the
ISU and SNL slots of Table 1: ISU/SNL outer tests are blocked by the guard, their training-fold runs have no outer metrics), the H7 run, <prefix>_analysis_SYNTHETIC (statistics step).
Fig. 2 and the design table are not produced by the run writer: they use the figure demo's invented fade table (runs/figdemo_SYNTHETIC/design)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "code" / "figures"
PREFIX = sys.argv[sys.argv.index("--prefix") + 1] if "--prefix" in sys.argv else "build_v1_fig"
R = ROOT / "runs"
B, C, S2 = (R / f"{PREFIX}_synth_B", R / f"{PREFIX}_synth_C", R / f"{PREFIX}_synth_S2")
if "--b" in sys.argv:
    B = Path(sys.argv[sys.argv.index("--b") + 1])
H7 = Path(sys.argv[sys.argv.index("--h7") + 1]) if "--h7" in sys.argv else R / f"{PREFIX}_synth_H7"
A = R / f"{PREFIX}_analysis_SYNTHETIC"
ISU, SNL = R / f"{PREFIX}_synth_ISUslot", R / f"{PREFIX}_synth_SNLslot"
META = ROOT / "data" / "raw" / "samsung50e_meta" / "experiments_meta.csv"
FADE = ROOT / "runs" / "figdemo_SYNTHETIC" / "design" / "fade_curves.csv"


def run(script, *args):
    r = subprocess.run([sys.executable, "-P", str(FIG / script), *map(str, args)], capture_output=True, text=True)
    print(script, "OK" if r.returncode == 0 else "FAILED")
    if r.returncode:
        print(r.stdout[-1200:], r.stderr[-2000:])
    return r.returncode


rc = 0
rc |= run("fig1_schematic.py", "--run-s2", S2, "--run-b", B, "--run-c", C)
rc |= run("fig2_design.py", "--meta", META, "--fade", FADE)
rc |= run("fig3_forecasts.py", "--run-b", B, "--run-c", C)
rc |= run("fig4_forest.py", "--run", B, "--contrasts", A / "contrasts_B.json")
rc |= run("fig5_stress.py", "--run", B)
rc |= run("fig6_storage.py", "--run-s2", S2, "--run-b", B)
rc |= run("fig7_residual.py", "--run", B)
rc |= run("fig8_synthetic.py", "--run", H7)
rc |= run("fig_graphical_abstract.py", "--meta", META, "--run-b", B, "--run-s2", S2, "--contrasts", A / "contrasts_B.json")
rc |= run("table1.py", "--run-b", B, "--run-c", C, "--run-s2", S2, "--run-isu", ISU, "--run-snl", SNL, "--analysis", A)
rc |= run("table2.py", "--run-b", B, "--analysis", A)
sys.exit(rc)
