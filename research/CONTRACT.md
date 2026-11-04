# Shared contract for every agent (read this first)

Project: a physics-informed neural network (PINN) combined with Kolmogorov-Arnold networks (KAN) for
lithium-ion battery health (SOH, possibly RUL or trajectory), for the **Journal of Energy Storage**
(Elsevier). Target: novelty, results and figures at the level of the strongest recent papers in that
journal. Project root: `C:\Users\Shlok\Downloads\PINN KAN battery paper` (below: `ROOT`).

## 1. Hard constraints
- **Never invent a number or a citation.** Numbers come from files in `ROOT/runs/<run-id>/` or are
  quoted from a paper with page/table/figure location. Citations carry a DOI verified on Crossref.
- **Say how deeply you read.** Every note states `reading: full text | partial (sections) | abstract
  only`. An abstract, an Exa/README summary or a search snippet is never a reading.
- **Retired topics (author's earlier paper, do not propose):** how the evaluation split (leakage,
  cross-dataset, laboratory-to-field) changes SOH/RUL accuracy; conformal or uncertainty calibration
  of battery health estimators under chemistry, dataset or lab-to-field shift. Leakage-free,
  cell-level evaluation is our standard practice, never our contribution.
- **Data preference:** a dataset different from the PINN4SOH feature tables (XJTU, TJU, MIT, HUST)
  is preferred. If those remain the best choice, the decision row must say why.
- Untrusted downloads go into their own new directory under `ROOT/data/raw/<name>/` or
  `ROOT/refs/`; never run code from inside them; run Python on them with `python -I`.
- No GPU job without the lead's explicit instruction. CPU only by default.
- AI tools are never mentioned in notes meant for the manuscript.

## 2. Roles
Proposer, opponent and judge are different agents. The proposer never validates its own output.
Gate auditor, red team, novelty auditor and citation validator only check; they never propose.

## 3. Debate protocol (every decision)
Each decision (topic, title, physics prior, KAN variant, datasets, baselines, splits, tuning,
figures, claims) gets a debate file `ROOT/debates/<decision-id>.md` with:
1. **Proposal** and its evidence (file/page pointers).
2. **Why this, and why not each serious alternative?** At least 3 named alternatives, each with the
   reason it loses.
3. **Is this the best result possible, or is there room for improvement?**
4. **What are we lacking that a JES reviewer would hit?**
5. **What would make a reviewer reject it?**
6. **Opponent's attack** (separate agent) and the proposer's answer.
7. **Judge's verdict**: accept / revise / reject, with conditions, and what evidence would re-open it.
Then a row is appended to `ROOT/research/DECISIONS.md` (format there).

## 4. Paper-extraction template ("extracting cognitive master researcher")
One file per paper: `ROOT/notes/papers/<ref-number>_<firstauthor><year>.md`, with these headings:
- **Citation** (authors, year, title, journal, volume, article no., DOI; group and country)
- **Reading depth** (full text / partial / abstract only; source file)
- **Problem and stated contribution** (paraphrase, no long quotes)
- **Data**: datasets, number of cells, chemistry, conditions, features or inputs, preprocessing,
  label definition (SOH = ?), cycles used
- **Model**: architecture with sizes; physics prior (which equation or constraint, and how it is
  enforced: loss term, architecture, feature, or only a name); KAN variant (B-spline, wavelet,
  Chebyshev, Fourier, RBF..., grid size, order, layers); training settings
- **Tuning**: how hyperparameters were chosen (and whether test data could have leaked into it)
- **Evaluation**: split (cell-level or not, which cells), metrics, baselines, headline numbers with
  table/figure location, number of seeds, any statistical test
- **Figures**: one line per figure (type and what it shows) and a note on visual style
- **Ablations** done
- **Hidden assumptions** (what must be true for the claims to hold)
- **Weaknesses a reviewer would hit**
- **Gaps and hooks for our paper** (concrete, testable)
- **Code/data availability**

## 5. Report format
Write findings to files. Reply to the lead in at most 5 lines: what you wrote (paths) and the single
most important finding or blocker.

## 6a. Figures and tables: results AND form (Shlok, 2026-11-04)
Figures must show strong results and also take the best form used by the top papers in JES.
1. **Figure-form catalogue.** The exemplar dissection records, for every figure and table of the
   strongest recent JES papers (plus 2-3 top-venue papers closest to our method), its form: plot type
   (trajectory overlay, parity plot, error heat map, violin/box, radar, Sankey, spline/activation
   panel, architecture schematic...), panel layout, colour scheme, annotation and insets, the
   message it carries, and the table style. File: `ROOT/notes/exemplars/FIGURE_FORMS.md`, with
   page/figure pointers.
2. **Figure plan debate.** Each planned figure and table gets a row in
   `ROOT/debates/D-figures.md`: the claim it supports, the chosen form, and why this form and not
   at least two alternatives from the catalogue (clarity at 13-17 cm width, information density,
   what the reviewer will look for). JES limit: about 8-10 figures and/or tables in the main text.
3. **Build and check.** Figures are generated only from `runs/` files by scripts in `ROOT/code/figures/`,
   then rendered and compared side by side with the exemplar forms: legibility at column width,
   colour-blind safety, consistent fonts and units, no overlap. A figure that looks weaker than its
   exemplar counterpart is redone.

## 6. Evaluation standards for experiments
- Splits are by cell (no cycle of a test cell in training or tuning). Splits fixed in
  `ROOT/runs/splits/` before any model sees data.
- Hyperparameters tuned only on training cells (nested or grouped CV); test cells are touched once
  per frozen configuration.
- At least 5 seeds; report mean and spread; paired comparisons on the same cells and seeds.
- Metrics: RMSE, MAE, MAPE (SOH in percent), R2; for trajectory or RUL tasks, error at fixed horizons
  and RUL error in cycles. Each run writes `config.json`, `metrics.json`, per-cell predictions and
  the git commit to its run directory.
