"""Shared style, palette, labels, provenance and I/O helpers for all figure and table scripts.

Rules enforced here (CONTRACT 6a, figure-smith):
* every figure script reads only run directories / statistics-step outputs passed as arguments (no number typed by hand) and computes NO interval, test,
  p-value, tier, count of positive conditions, effect size or bootstrap (ALIGN_V4_REPORT.md; tests/test_figures_read_only.py);
* Okabe-Ito based, colour-blind-safe palette; method identity = colour + marker + line style;
* fonts 8-9 pt at the final width (16 cm full, 13 cm medium);
* a figure built from a run directory that carries a `SYNTHETIC` marker file is watermarked
  "SYNTHETIC DEMO - NOT RESULTS" and its file names get the suffix `_SYNTHETIC`;
* a figure built from real Samsung data is refused until `runs/prereg/FROZEN` exists (blinding rule, PREREG_v2 3.3(9)).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIG_OUT = ROOT / "paper" / "figures"
TAB_OUT = ROOT / "paper" / "tables"
CM = 1.0 / 2.54
W_FULL = 16.0 * CM      # full text width (inches)
W_MID = 13.0 * CM       # medium width / graphical abstract
WATERMARK = "SYNTHETIC DEMO - NOT RESULTS"

# --------------------------------------------------------------------------------------------- palette
# Okabe-Ito (colour-blind safe) plus black/grey and two Tol colours for the learners that are never drawn together
BLUE, ORANGE, GREEN, SKY = "#0072B2", "#E69F00", "#009E73", "#56B4E9"
VERM, PURPLE, YELLOW, BLACK, GREY = "#D55E00", "#CC79A7", "#F0E442", "#000000", "#7A7A7A"
INDIGO, TEAL, WINE = "#332288", "#44AA99", "#AA3377"

ARMS = {  # id: (display name, colour, marker, linestyle)
    "A1": ("PINN-KAN", BLUE, "o", "-"),
    "A2": ("Hard-ODE KAN", GREEN, "s", "-"),
    "A3": ("PINN parametric", SKY, "^", "-"),
    "A4": ("PINN additive GAM", PURPLE, "v", "--"),
    "A5": ("PINN interaction GAM", VERM, "D", "-"),
    "A7": ("PINN MLP stress map", GREY, "P", "-"),
    "A8": ("Free G", WINE, "d", "-"),
    "A9": ("Data-only F", BLACK, "X", "-"),
    "A10": ("Semi-empirical (dataset authors)", ORANGE, "*", "-"),
    "A11": ("GP-ARD", INDIGO, "h", "-"),
    "A12": ("LightGBM", TEAL, "p", "-"),
    "A13": ("PINN-KAN, cycling cells only", BLUE, "o", ":"),
    "A14": ("PINN-KAN, storage cells only", BLUE, "o", ":"),
    "A10P": ("Semi-empirical, as published", ORANGE, "*", "--"),
    "A15": ("Extracted closed-form law A15", INDIGO, "h", "-"),
    "G15": ("Extracted additive law G15", "#117733", "d", "--"),
    "D*": ("Best data-driven learner D*", TEAL, "p", "-"),
    "AG": ("Best additive GAM AG", PURPLE, "v", "--"),
    "R1": ("Persistence", "#B0B0B0", "_", "-"),
    "R2": ("Window-linear", "#8C8C8C", "|", "-"),
}
SHORT = {"A1": "PINN-KAN", "A2": "Hard-ODE", "A3": "Parametric", "A4": "Add. GAM", "A5": "Int. GAM", "A7": "MLP map",
         "A8": "Free G", "A9": "Data-only F", "A10": "Semi-emp.", "A11": "GP-ARD", "A12": "LightGBM",
         "A13": "Cycling-only", "A14": "Storage-only", "R1": "Persistence", "R2": "Window-lin.", "A10P": "Semi-emp. (publ.)",
         "A15": "Law A15", "G15": "Law G15", "D*": "D*", "AG": "AG"}

LAB_COL = {"SIE": ORANGE, "INT": GREEN, "HM": PURPLE}
LAB_NAME = {"SIE": "SIE", "INT": "INT", "HM": "HM"}
TEMPS = [10, 23, 35, 45]
_cv = plt.get_cmap("cividis")
TEMP_COL = {10: _cv(0.02), 23: _cv(0.30), 35: _cv(0.55), 45: _cv(0.80)}
TIER_COL = {"S": GREEN, "N": SKY, "-": "#BBBBBB", "none": "#BBBBBB", "reverse S": VERM}

# --------------------------------------------------------------------------------------------- labels (one unit per quantity)
LBL = {
    "t": "Time since reference check-up (days)",
    "ret": "Capacity retention (%)",
    "rmse": "Forecast RMSE (pp)",
    "T": "Temperature (°C)",
    "soc": "SOC (%)",
    "soc_mid": "SOC$_{\\mathrm{mid}}$ (%)",
    "dod": "DoD (%)",
    "cch": "$C_{\\mathrm{ch}}$ (C)",
    "cdch": "$C_{\\mathrm{dch}}$ (C)",
    "logratio": "ln(error of comparator / error of PINN-KAN)",
}


def _pick_font():
    have = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"):
        if name in have:
            return name
    return "sans-serif"


def apply():
    """Global rcParams: 8-9 pt text at final width, thin lines, no top/right spines, embedded TrueType fonts."""
    font = _pick_font()
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": [font, "DejaVu Sans"],
        "mathtext.fontset": "custom", "mathtext.rm": font, "mathtext.it": font + ":italic", "mathtext.bf": font + ":bold",
        "font.size": 8.0, "axes.labelsize": 8.5, "axes.titlesize": 8.5, "axes.titleweight": "normal",
        "xtick.labelsize": 8.0, "ytick.labelsize": 8.0, "legend.fontsize": 8.0, "legend.title_fontsize": 8.0,
        "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.minor.size": 1.5, "ytick.minor.size": 1.5,
        "lines.linewidth": 1.2, "lines.markersize": 4.0, "patch.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "grid.color": "#DDDDDD", "grid.linewidth": 0.5,
        "legend.frameon": False, "legend.handlelength": 1.6, "legend.handletextpad": 0.5, "legend.borderaxespad": 0.3,
        "figure.dpi": 100, "savefig.dpi": 600, "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "axes.labelpad": 2.0, "xtick.major.pad": 2.0, "ytick.major.pad": 2.0,
        "figure.constrained_layout.use": False,
    })
    return font


# --------------------------------------------------------------------------------------------- provenance
class Provenance:
    """Collects the run directories a figure reads; `synthetic` if any carries a SYNTHETIC marker (here or in a parent)."""

    def __init__(self, *paths):
        self.paths = [Path(p).resolve() for p in paths if p is not None]
        self.synthetic = any(self._is_synth(p) for p in self.paths)

    @staticmethod
    def _is_synth(p: Path) -> bool:
        for q in [p] + list(p.parents)[:3]:
            if (q / "SYNTHETIC").exists() or "SYNTHETIC" in q.name:
                return True
        return False

    def suffix(self) -> str:
        return "_SYNTHETIC" if self.synthetic else ""

    def require_frozen(self, what="this figure"):
        """Samsung-derived figures are only made after the freeze (PREREG_v2 3.3(9)); demo data are exempt."""
        if self.synthetic:
            return
        if not (ROOT / "runs" / "prereg" / "FROZEN").exists():
            raise SystemExit(f"REFUSED: {what} reads non-synthetic run data but runs/prereg/FROZEN does not exist "
                             "(retention blinding, PREREG_v2 3.3(9)).")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def need(path: Path, hint: str = ""):
    path = Path(path)
    if not path.exists():
        raise SystemExit(f"MISSING INPUT: {path}  {hint}")
    return path


# --------------------------------------------------------------------------------------------- condition keys
_NUM = r"([0-9.]+)"
_CYC = re.compile(rf"T{_NUM}\|SOCmax{_NUM}\|DoD{_NUM}\|Cch{_NUM}\|Cdch{_NUM}")
_STO = re.compile(rf"T{_NUM}\|SOC{_NUM}$")


def parse_cond(key: str) -> dict:
    """'T23|SOCmax0.65|DoD0.35|Cch0.4|Cdch1.5' (cycling) or 'T10|SOC0.05' (storage); SOC, DoD in %."""
    m = _CYC.match(key)
    if m:
        T, smax, dod, cc, cd = (float(x) for x in m.groups())
        return dict(kind="cyc", T=T, soc_max=100 * smax, dod=100 * dod, c_ch=cc, c_dch=cd, soc_mid=100 * (smax - dod / 2))
    m = _STO.match(key)
    if m:
        T, soc = (float(x) for x in m.groups())
        return dict(kind="sto", T=T, soc=100 * soc)
    raise ValueError(f"cannot parse condition key {key!r}")


def cond_text(key: str) -> str:
    c = parse_cond(key)
    if c["kind"] == "sto":
        return f"{c['T']:.0f} °C, SOC {c['soc']:.0f} %"
    return f"SOC {c['soc_max'] - c['dod']:.0f}–{c['soc_max']:.0f} %, {c['c_ch']:g}/{c['c_dch']:g} C"


# --------------------------------------------------------------------------------------------- figure helpers
def label_panels(fig, axes, letters=None, dx=0.62 * CM, dy=0.08 * CM, size=10):
    """Bold lower-case panel letters at the top-left outside each axes; call after the layout is final."""
    fig.canvas.draw()
    letters = letters or "abcdefghijklmnop"
    fw, fh = fig.get_size_inches()
    for ax, ch in zip(axes, letters):
        bb = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
        pos = ax.get_position()
        x = bb.x0
        fig.text(max(x, 0.0) + 0.0, pos.y1 + dy / fh, ch, fontsize=size, fontweight="bold", ha="left", va="bottom")


def panel_letter(ax, ch, dx=-0.0, dy=0.0, size=10):
    ax.text(dx, 1.0 + dy, ch, transform=ax.transAxes, fontsize=size, fontweight="bold", ha="right", va="bottom")


def watermark(fig):
    fw, fh = fig.get_size_inches()
    ang = float(np.degrees(np.arctan2(fh, fw)))
    fs = max(10.0, 0.040 * fw * 72)
    fig.text(0.5, 0.5, WATERMARK, rotation=ang * 0.8, fontsize=fs, color="#C00000", alpha=0.17, ha="center",
             va="center", fontweight="bold", zorder=1000, transform=fig.transFigure)
    fig.text(0.004, 0.003, WATERMARK, fontsize=6.5, color="#C00000", ha="left", va="bottom", fontweight="bold",
             zorder=1000)


def finish(fig, stem: str, prov: Provenance, out_dir=None, dpi=600, close=True):
    """Watermark (synthetic input) and write vector PDF + 600 dpi PNG. Returns the two paths."""
    out_dir = Path(out_dir) if out_dir else FIG_OUT
    out_dir.mkdir(parents=True, exist_ok=True)
    if prov.synthetic:
        watermark(fig)
    base = out_dir / f"{stem}{prov.suffix()}"
    pdf, png = base.with_suffix(".pdf"), base.with_suffix(".png")
    fig.savefig(pdf)
    fig.savefig(png, dpi=dpi)
    if close:
        plt.close(fig)
    print(f"wrote {pdf}\nwrote {png}")
    return pdf, png


def common_args(description: str):
    import argparse
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--out-dir", default=None, help="default: paper/figures")
    return ap


def fmt(x, nd=2):
    t = f"{x:.{nd}f}"
    if float(t) == 0:
        t = t.lstrip("-")
    return t.replace("-", "−")


def strip_ticks_top_right(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
