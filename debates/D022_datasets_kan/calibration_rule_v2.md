# D022a calibration of the extraction audit, rule v2 (written and committed BEFORE the v2 calibration code)

Author: coder (build_v2), 2026-11-05, from `debates/D022_datasets_kan/05_judge_audit_revision.md` sections 2.1 to 2.8 and 3 (judge ruling D022a; decision row D022a). `calibration_rule.md` (v1, commit 3f0d492) is **superseded** by this file: its unit (an edge), its 600-fit plan and its "false-family rate per cell" are not used. Reading: full text of the judge file; the v1 rule, `extraction_audit.json` (v1), `code/prereg/extraction_calibration.py` (v1), `synth.py`, `arms.py`, `subsets.json` (identifiers only). No Samsung label, outer-test datum or score was opened. Nothing in this file was run. Every number is a design choice fixed before any result. The thresholds file is `code/pinnkan/extraction_audit.json` (v2); this file fixes the calibration design. Both are in the frozen commit; their sha256 values are config keys (`extraction_audit_sha256`, `calibration_rule_sha256`).

Lines marked **[coder]** are the coder's reading of a point the judge file leaves open; each is also in `runs/build_v2/CHOICES.md`.

## 1. Unit and procedure
- **Unit = one synthetic dataset d** (D = 30 per arm, d = 0..29), run through the real procedure: for each outer fold f = 0..4 the fold's training design at m = 32 (the 32 training cycling identifiers of `subsets.json` and the 19 S2 storage identifiers, two replicate cycling cells per condition, one storage cell per storage condition), `arms.SymbolicArm` with refit seeds 0 to 4. That gives **25 extracted laws per arm** (5 folds x 5 seeds), the same count as g4 on the real data.
- Arms: A15 (h as drawn per fold, section 2.5) and G15. Labels come from the same function as on the real data (`extraction_audit.label_law`), with condition (d) of the label rule taken as satisfied (the calibration measures the licences the rule would give).
- 2 arms x 30 datasets x 5 folds x 5 seeds = **1500 fits**. The baseline (section 4.4) reuses them.

## 2. The synthetic datasets
1. **One truth per dataset, shared by all folds.** The truth of input i is a function of the physical stress on one fixed hull [lo_i, hi_i] (T in kelvin): the union of the five folds' m = 32 training identifiers (identifiers only). **[coder]** A fold's training hull is a sub-range of it, so a symmetric quadratic has a hull-averaged slope of zero by definition (the truth's sign is fixed by the truth, not by a fold's hull).
2. **Strata (rotation).** Stratum of input i in dataset j = `S[(j + i) mod 5]`, S = (zero, linear, log, quadratic `A(2u^2 - 1)`, hinge `A(2 max(0, u - 0.2)/0.8 - 1)`), u = 2 (x - lo)/(hi - lo) - 1 (linear and log as `synth.truth_effect`). Slope sign `+1` if `(j + i)` is even, else `-1`. Over D = 30 each input meets each stratum 6 times.
3. **Interaction datasets.** j = 0, 3, 6, ..., 27 (ten datasets) add `A_int u_p u_q` to the cyclic log-rate. The pair (p, q) of the k-th interaction dataset (k = j / 3) is the k-th element of `itertools.combinations(range(5), 2)` in lexicographic order (each of the ten pairs once). The inputs p and q are *interacting* in that dataset.
4. **Amplitudes.** A (per dataset and input) and A_int (per interaction dataset) are drawn log-uniform on [0.05, 0.5]; 0.5 is the PREREG 13 value, 0.05 a weak effect.
5. **Laboratory aliasing.** An offset per laboratory, drawn N(0, 0.15^2) on the cyclic log-rate (sd = TAU), shared by all folds of the dataset, is added to every cycling cell of a condition whose **majority laboratory** (most cells of the condition in `data/processed/samsung_cells.csv`, type `z`; ties: first in sorted order; identifiers only) is that laboratory. Temperature and laboratory are aliased exactly as in the design. The sha256 of the resulting condition-to-laboratory map is recorded in `calibration.json`. A training condition with no cell in the table is an error (the calibration runs after the cell download is complete).
6. **Hyperparameters.** Per (dataset, fold) and arm, drawn uniformly from the tuned space of PREREG 7.1: A15 (`ARMS["A15"].space`: h in {1, 2} and the five other dimensions of A1), G15 (`ARMS["G15"].space`, the A4 space). One draw is used for the five refit seeds of that fold. This marginalises over the space and does not reproduce inner-CV tuning (it would multiply the cost by the trial count). Noise 0.5 pp, offsets sd 0.15, median final fade 20 pp, check-up cadence: `synth.make_synthetic` / PREREG 13 values (a Limitation).
7. **Seeds.** `base = SeedSequence([20261105, crc32("calib2|d<j>")])`; `amp, lab, hp, noise = base.spawn(4)`. Amplitudes and the interaction amplitude come from `amp`, laboratory offsets (laboratories in sorted order) from `lab`; the hyperparameter draw of (fold f, arm a) uses `hp.spawn(10)[2 f + (0 for A15, 1 for G15)]`; the generator seed of fold f is `noise.spawn(5)[f].generate_state(1)[0] % 2^31`. The parent and refit seeds are 0 to 4, as on the real data.

## 3. The audit applied to a dataset (the label function)
Per-law quantities, the additivity test and the label rule are those of judge sections 2.2 and 2.3, with the thresholds of `extraction_audit.json` (retained, 0.01 tolerance, 20 of 25, strict win, tie rule, additivity on a 5 x 5 grid). Both arms use the one function. **[coder]** The partial dependence is on 41 points of the fold's training hull in physical x, the other inputs at the hull midpoint. Lines of the label rule that need a count are `20 of 25` and `more than 5 of 25`; a call with a number of laws other than 25 is an error.

## 4. Scoring
### 4.1 False statements
A printed statement is **false** if:
- a form F is licensed and the input's truth stratum is not F, or the input is interacting in that dataset;
- a sign is licensed (alone or with a form: a form label implies the sign of its slope) and the truth's hull-averaged slope sign differs from it. The truth sign is `0` for the zero and the (symmetric) quadratic strata and the stratum sign for linear, log and hinge. For an interacting input it is the sign of the hull-averaged slope of its main effect (the product term averages to zero over the hull).

"Not retained", "composed" and "not identified" are never false statements. **E_d(arm) = 1 if dataset d has at least one false statement for that arm.**

### 4.2 Conditions (per arm; fixed now)
- **C1, calibrated.** The one-sided 95 % Clopper-Pearson upper limit of P(E_d = 1), from k datasets with a false statement out of D completed, is <= 0.20. (At D = 30: k <= 2, upper limits 0.095, 0.149, 0.195; at D = 22: k <= 1, 0.127, 0.198.)
- **C2, useful.** Over the (dataset, input) events with input in {soc_mid, dod, c_ch, c_dch}, truth stratum linear or log, and the input not interacting, the share where the audit licenses the correct form is >= 0.5 (point estimate; a floor, not a guarantee; exact interval printed).
- **C3, necessary.** The stability-only baseline (4.4) fails C1 on the same datasets.
- **Consequence.** The extraction audit is the paper's KAN-side contribution only if C1, C2 and C3 hold for **both** G15 and A15. If any fails the contribution bullet is withdrawn; the audit and calibration tables go to an appendix as a descriptive report; labels are printed only for an arm that passed C1; the Discussion carries the fixed sentence for each failed condition (4.3). This is a stop, not an alternative finding.

### 4.3 Fixed sentences
*"The extraction audit did not meet its pre-set calibration condition, so it is reported as a description, not as a method result."* (C1) / *"... pre-set usefulness condition ..."* (C2) / *"... pre-set necessity condition ..."* (C3). One sentence per failed condition, fixed text in `extraction_audit.json`.

### 4.4 Stability-only baseline (same fits, no extra cost)
A form is named for an input when at least 20 of the 25 laws choose the same extracted edge family (the extractor's own list order: the input's family is `zero` if every first-layer edge is zero, the family of its single non-zero edge, else `composed`; only linear and log are named forms); a sign is named when at least 20 of the 25 laws agree on the sign of PD(hi) - PD(lo) (non-zero). No tie, additivity or magnitude condition. Scored by the rules of 4.1.

### 4.5 Always printed (descriptive, license nothing)
Per arm: D completed, k and the false-statement upper limit, the C2 recall with an exact interval, the baseline's k and upper limit and recall, and per (input, stratum) confusion rows (form and sign licensed, abstention, not retained, composed) with exact two-sided intervals; the tie share (laws in which linear and log both fit within 0.01), and, for inputs whose truth is not zero and not interacting, the share labelled "not retained" (a false zero) by amplitude band (< 0.1, 0.1 to 0.25, > 0.25).

## 5. Running, resuming, stopping
- Order: datasets d = 0..29, folds 0..4 within a dataset; with `--nproc P` the (dataset, fold) work items are dealt round-robin. One record per (dataset, arm, fold, seed): the law record, the drawn hyperparameters, CPU seconds, `refit_diverged`. Records are appended to `records_p<proc>.jsonl`.
- Resume: a work item is skipped when all its 10 keys exist; **de-duplicate on (dataset, arm, fold, seed)** (the first record wins); a **torn last line** of a records file is ignored (any other unreadable line is an error).
- A dataset is *complete* when it has all 50 keys. The verdict is computed once, at the end, on the complete datasets. **D >= 22 is required**; fewer voids the calibration (judge section 5 applies).
- CPU cap **36 CPU-hours** (sum of the recorded fit CPU seconds, checked at each work item); at the cap the run stops, the verdict is computed on the complete datasets. The expected cost is about 18 CPU-h (ceiling about 33 CPU-h) from the D021 pipeline times (arithmetic, not a measurement).

## 6. Guard and content control
- The script refuses to run unless `guard.verify_freeze` passes **with untracked files under `code/` included** (`__pycache__` and `*.pyc` excepted) and both pins match (config-style pins of the thresholds file and of this rule file are checked against the files in the tree; FROZEN pins are those of `verify_freeze`).
- `calibration.json` records the FROZEN commit SHA, `rule_sha256`, `thresholds_sha256`, the lab-map hash, D completed, the CPU seconds and the per-dataset records. The statistics step requires its commit to equal the FROZEN SHA.
- **Bit-identical re-run check.** Three datasets are chosen by the first bytes of `sha256(calibration.json)`: take the bytes in order, index `b mod D_complete` into the sorted list of complete dataset ids, skip repeats, until three are chosen. The gate auditor re-runs them from a FROZEN worktree (`extraction_calibration.py --rerun`) and the records must be bit-identical (same keys, equal JSON; the CPU-seconds field is excluded, a timing cannot repeat). A mismatch voids the calibration.
- mtime ordering is logged only. The calibration may run before, alongside or after the confirmatory grid; no Samsung outer score may be used to change this rule.

## 7. What would void the calibration
A change to this file, to the thresholds file or to the extraction path (`symbolic.py`, `symbolic_library.json`, `extraction_audit.py`, `synth.py`) after the run; a run from a commit other than the FROZEN one; a failed bit-identical re-run; fewer than 22 complete datasets; real-data hyperparameters outside the spaces of section 2.6; a request for labels at g1 or on the calendar law (needs its own calibration and a new decision row).
