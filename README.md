> **This repository** holds the code and records of the study. The run outputs (about 85 MB) and the citable archive are on Zenodo: https://doi.org/10.5281/zenodo.24153388. The frozen analysis is tag `v1.0-frozen` (commit c6a89b6). The text below is the Zenodo README.

# Code, preregistration and run outputs: PINN-KAN capacity-fade study (Journal of Energy Storage)

Zenodo record 10.5281/zenodo.24153388, version 1.0.0, 2026-11-12. Paper: "Physics-informed and data-driven forecasts of
lithium-ion capacity fade against the number of cycling tests and check-ups: learning curves with Kolmogorov-Arnold stress
functions" (Goenka, Vairavasundaram, G N; VIT Vellore).

## Files
| File | Content |
|---|---|
| `pinnkan_code_c6a89b6.zip` | `git archive` of tag `v1.0-frozen` (commit c6a89b6b2125a0ccb5b6170538fe7d43c018d2ba): `code/` (package `pinnkan`, tests, data parsers, figure and table scripts in `code/figures/`), `runs/prereg/`, `runs/splits/`, `tools/`, `requirements.txt` |
| `prereg.zip` | `runs/prereg/` (PREREG_v4.md, FROZEN, SCORED.jsonl ledger, configs, split files, rulings) and `runs/splits/`, as of the post-freeze commit d4f3ba8 (tracked files only) |
| `stats_frozen.zip` | `runs/stats_frozen/` (frozen statistics step: `run_stats_frozen.sh`, `analysis/`, `extras/`, `post/`, `descriptive_post/`), the audit reports in `research/audits/` cited by the paper, and `research/DECISIONS.md` (decision log) |
| `run_outputs.zip` | per-run small JSON, CSV and NPZ outputs (config, metrics, condition and cell scores, predictions, window, diagnostics, superposition, stress functions, extracted laws, invariance, reference values, tuning records) of every run the paper reports: `conf_samsung_*`, `row_*`, `sens_*`, `repl_isu_*`, `expl_samsung_*`, `item_f*`, `pc1_g0_synth`. No model weights, no raw data, no logs |
| `PROVENANCE.md` | both freeze commits (original and D044 re-pin), the post-freeze commit, where the full history is |
| `LICENSE_CODE.txt`, `LICENSE_DATA.txt`, `CITATION.cff` | licences and citation metadata |
| `CHECKSUMS.sha256` | SHA-256 of every uploaded file (all files above) |

## Rebuilding the statistics step
1. Unzip `pinnkan_code_c6a89b6.zip` (code at the frozen commit) into a working directory and create the Python environment
   from `requirements.txt` (the script calls `.venv/Scripts/python.exe`; edit the path on another platform).
2. Unzip `run_outputs.zip` and `prereg.zip` into the same directory so that the run folders sit under `runs/` (for example
   `runs/conf_samsung_B_f0_m32/`) and `runs/prereg/` holds FROZEN and SCORED.jsonl.
3. Run `bash runs/stats_frozen/run_stats_frozen.sh` from the directory root (`--check` first lists missing run folders). It
   writes `runs/stats_frozen/analysis/` (contrasts, controls, margins, laws); compare with the copy in `stats_frozen.zip`.
   The step is strict at the FROZEN commit.
4. Post-freeze scripts (descriptive only, written after the freeze): `runs/stats_frozen/post_arm_table.py`,
   `runs/stats_frozen/descriptive_post/*.py`, `runs/stats_frozen/extras/*.py` (extras and sensitivity families). Their outputs
   and SHA256 files are in `stats_frozen.zip`.

Tables and figures are built from the run artifacts by the scripts in `code/figures/` at the frozen commit
(`fig1_schematic.py` to `fig8_synthetic.py`, `fig_graphical_abstract.py`, `table1.py`, `table2.py`; see
`code/figures/README.md`). The layout copies `code/figures_post/` used for the submitted manuscript are in the authors' writing
branch and are not part of this record.

## Data sources (not redistributed)
- Samsung INR21700-50E cycling and calendar ageing data: doi:10.6084/m9.figshare.25975315.v1 (CC BY 4.0).
- ISU-ILCC battery ageing data: doi:10.25380/iastate.22582234.v2 (CC BY 4.0).

Parsers are in `code/data/` and `code/data_audit/`; the raw archives are downloaded from the DOIs above and checked against the
checksums kept in the authors' repository (`data/CHECKSUMS.sha256`).

## Decision log
`research/DECISIONS.md` in `stats_frozen.zip`: D044 (retain-every-check-up row, code amendment after FROZEN), D044a (re-pin of
FROZEN to c6a89b6), D045 (PC-1 G0 synthetic run added late), D046 (arm table recomputed after the freeze), D047 (writing
decisions after the outcome). Gate audits: `research/audits/GATE_D044_*`, `GATE_D045_pc1_g0.md`, `GATE_stats_frozen.md`,
`GATE_manuscript_numbers_2026-11-12.md`.

## Licences
Code (`code/`, `tools/`): MIT, see `LICENSE_CODE.txt`. Everything else: CC BY 4.0, see `LICENSE_DATA.txt`.
