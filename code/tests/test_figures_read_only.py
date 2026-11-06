"""Figure and table scripts are READ-ONLY on the frozen statistics step (GATE_freeze_audit re-check rev. 19, ruling on D037; PREREG_v4 section 20 rows for code/figures/*).

1. AST check: no module of code/figures imports scipy.stats, calls a bootstrap / interval / test / quantile / spread routine, or names one; only the demo generator
   (make_demo_runs.py) may import the statistics step (it RUNS it on synthetic directories) and draw random numbers (it simulates).
2. Smoke test: every display item of PREREG_v4 section 14 (Figs. 1-8, graphical abstract, Tables 1-2) renders from SYNTHETIC demo runs; the outputs carry the SYNTHETIC suffix.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_figures_read_only.py -q
"""
import ast
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "code" / "figures"
sys.path.insert(0, str(ROOT / "code"))
sys.path.insert(0, str(FIG))
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"

import pytest

GENERATOR = {"make_demo_runs.py"}                       # simulates run-writer files and runs the statistics step on them
FORBIDDEN_CALLS = {"median", "nanmedian", "percentile", "nanpercentile", "quantile", "nanquantile", "std", "nanstd", "var", "nanvar", "ppf", "cdf", "sf", "pmf", "isf",
                   "binom_test", "binomtest", "wilcoxon", "ttest_1samp", "ttest_rel", "ttest_ind", "mannwhitneyu", "permutation_test", "resample", "bootstrap", "bootstrap_mean_ci",
                   "median_order_ci", "bca_mean_ci", "sign_p", "betabin_p", "betabin_crit", "graph_test", "order_stat_interval"}
FORBIDDEN_SUBSTR = ("bootstrap", "bca_mean", "order_ci", "sign_p", "binom", "betabin", "wilcoxon", "pvalue", "p_value")
RANDOM_NAMES = {"default_rng", "RandomState", "SeedSequence"}
STATS_PACKAGE_MODULES = {"stats_v4", "stats_step", "stats_rows", "stats_ext", "graph_test", "margins", "negcontrol", "h7"}


def modules():
    return sorted(p for p in FIG.glob("*.py"))


def analyse(path):
    tree = ast.parse(path.read_text(encoding="utf8"), filename=str(path))
    bad = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "scipy.stats" or a.name.startswith("scipy.stats."):
                    bad.append((n.lineno, f"import {a.name}"))
                if a.name.split(".")[-1] in STATS_PACKAGE_MODULES:
                    bad.append((n.lineno, f"import {a.name}"))
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            if mod == "scipy.stats" or (mod == "scipy" and any(a.name == "stats" for a in n.names)) or mod.startswith("scipy.stats."):
                bad.append((n.lineno, f"from {mod} import ..."))
            names = {a.name for a in n.names}
            if mod.split(".")[-1] in STATS_PACKAGE_MODULES or (mod.startswith("pinnkan") and names & STATS_PACKAGE_MODULES):
                bad.append((n.lineno, f"from {mod} import {sorted(names)}"))
        elif isinstance(n, ast.Call):
            f = n.func
            nm = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if nm in FORBIDDEN_CALLS:
                bad.append((n.lineno, f"call {nm}()"))
            if nm in RANDOM_NAMES:
                bad.append((n.lineno, f"random generator {nm}()"))
        elif isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            if any(s in n.name.lower() for s in FORBIDDEN_SUBSTR):
                bad.append((n.lineno, f"definition {n.name}"))
        elif isinstance(n, ast.Name):
            if any(s in n.id.lower() for s in FORBIDDEN_SUBSTR):
                bad.append((n.lineno, f"name {n.id}"))
        elif isinstance(n, ast.Attribute):
            if any(s in n.attr.lower() for s in FORBIDDEN_SUBSTR) or (n.attr == "random" and isinstance(n.value, ast.Name) and n.value.id in ("np", "numpy")):
                bad.append((n.lineno, f"attribute {n.attr}"))
    return bad


@pytest.mark.parametrize("path", [p for p in modules() if p.name not in GENERATOR], ids=lambda p: p.name)
def test_figure_and_table_modules_compute_no_statistic(path):
    assert analyse(path) == [], f"{path.name}: {analyse(path)}"


def test_generator_runs_the_statistics_step_but_computes_none_itself():
    path = FIG / "make_demo_runs.py"
    bad = [b for b in analyse(path) if not b[1].startswith("from pinnkan") and not b[1].startswith("random generator") and b[1] != "attribute random"]
    bad = [b for b in bad if not any(m in b[1] for m in STATS_PACKAGE_MODULES)]
    assert bad == [], bad
    src = path.read_text(encoding="utf8")
    assert "scipy" not in src and "bootstrap" not in src


def test_style_module_no_longer_carries_an_interval_routine():
    import pk_style
    assert not hasattr(pk_style, "bootstrap_mean_ci") and not hasattr(pk_style, "median_order_ci")


def test_every_figure_script_is_listed_in_the_readme():
    readme = (FIG / "README.md").read_text(encoding="utf8")
    for p in modules():
        if p.name.startswith(("fig", "table")):
            assert p.name in readme, p.name


@pytest.fixture(scope="module")
def demo(tmp_path_factory):
    import make_demo_runs
    out = tmp_path_factory.mktemp("figdemo_SYNTHETIC")
    make_demo_runs.main(out_dir=out)
    return out


def test_demo_analysis_carries_the_statistics_step_inputs_of_the_former_gaps(demo):
    """the demo reads the statistics step's own G1-G8 outputs, no stand-in: arm_table / reference / law_summary / residual_map files, NC-2 / PC-2 / PC-3, Q-T interval, candidates"""
    import json
    an = demo / "analysis"
    for f in ("arm_table.json", "reference.json", "law_summary.json", "residual_map.npz", "physval_11a.json", "controls.json", "contrasts_v4_B.json"):
        assert (an / f).exists(), f
    assert not (an / "STATS_GAPS_ERRORS.json").exists()
    assert "stand-in" not in (an / "arm_table.json").read_text(encoding="utf8")
    ctl = json.loads((an / "controls.json").read_text(encoding="utf8"))
    assert ctl["negative"]["nc2"]["n"] == 40 and ctl["gate_G"]["reported_checks"]["PC-2_calendar_rate_monotone_in_T"] is not None and ctl["positive"]["PC3_detail"]["n"] == 40
    st = json.loads((an / "contrasts_v4_B.json").read_text(encoding="utf8"))
    assert st["secondary"]["tests"]["QT_g1"]["median_interval"]["median_ci"] and set(st["candidates_vs_a1"]["rows"]) == {"A11", "A12", "A4", "A5"}
    pv = json.loads((an / "physval_11a.json").read_text(encoding="utf8"))
    assert {"a_of_soc", "arrhenius_ln_rate", "partial_dependence_overlays"} <= set(pv)
    assert "display" in pv["partial_dependence_overlays"]["per_input"]["T"] and "A1" not in pv["partial_dependence_overlays"]["per_input"]["T"]      # temperature: fixed label only


def test_every_display_item_renders_from_synthetic_demo_runs(demo, tmp_path):
    import run_all_demo
    outd = tmp_path / "out"
    assert run_all_demo.render_all(demo, str(outd)) == 0
    names = {p.name for p in outd.iterdir()}
    for stem in ("fig1_schematic", "fig2_design", "fig3_forecasts", "fig4_forest", "fig5_stress", "fig6_storage", "fig7_residual", "fig8_synthetic", "graphical_abstract"):
        assert f"{stem}_SYNTHETIC.pdf" in names and f"{stem}_SYNTHETIC.png" in names, stem
    for stem in ("table1", "table2"):
        assert f"{stem}_SYNTHETIC.tex" in names and f"{stem}_SYNTHETIC.csv" in names, stem
    t2 = (outd / "table2_SYNTHETIC.tex").read_text(encoding="utf8")
    assert "SYNTHETIC DEMO" in t2 and "Outcome table" in t2


def test_demo_does_not_touch_samsung_or_prereg_files():
    src = (FIG / "make_demo_runs.py").read_text(encoding="utf8")
    for token in ("samsung50e_meta", "samsung_splits", "runs/prereg", "runs\" / \"prereg", "processed/samsung"):
        assert token not in src
