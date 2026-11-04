# Negative control: purpose, restated criteria, seed (2026-11-05, statistician)

Question from the lead: the preregistered negative control (PREREG_v2 section 10, gate G) fails both criteria on the builder's small synthetic G2 demo
(A9 vs A1 mean L = -0.74, two-sided p = 0.03; A1 vs R2 median L = 1.31). Decide what the control is for, restate the criteria so that a leak-free pipeline
passes and a leaking one fails, justify with a synthetic check, and fix the sign-flip RNG seed. Synthetic data only; never FROZEN; no real file opened;
nothing here is a result. Code: `code/prereg/negcontrol_check.py`, `code/prereg/negcontrol_aggregate.py` (use the project's `pinnkan` code unmodified, with
monkeypatched data hooks); outputs `runs/prereg/stats_ruling/negctl/` (`summary_s*.json`, `aggregate.json`; the per-run directories are not committed).

## 1. Ruling in one paragraph
The control has two possible purposes and the draft merged them. **Gate G is for leakage only, and leakage is tested by intervention, not by score contrasts:**
replace the held-out cells' post-window labels by garbage and require the predictions (and the tuning record) to be bit-identical (NC-1). **"The stress
functions carry the gain" is a separate, interpretive, non-gating control (NC-2):** scrambling the stress vectors must hurt A1, paired by condition, tested
with the exact one-sided sign test. Both criteria of the draft are dropped (A9 - A1 two-sided p > 0.05; A1 must not beat R2): a leak-free pipeline is
expected to fail them, and they do not react to leaks. The sign-flip seed problem disappears because the control uses exact tests; every remaining Monte
Carlo step gets a registered per-contrast seed.

## 2. Why the draft criteria are wrong (and the builder is right)
Under permuted stress the stress-to-rate map is destroyed, but the pipeline still has (a) the window-fitted per-cell offsets and latent, and (b) a
learned time law; that is information about the cell, not about stress, and it is legitimate. So:
- **(ii) "A1 does not beat R2" cannot hold** for a leak-free A1: R2 is linear extrapolation of the window (15.1 pp in the builder's demo; inner-CV 11.7-12.5 pp in the runs here) against 1.5-4 pp for A1. It is a weak reference, not a stress-blind learner of the same information.
- **(i) "A9 - A1: mean L < ln 1.02 and two-sided p > 0.05" has no valid null.** Which of A1 and A9 is better under scrambled stress depends on the draw:
  mean L(A9/A1) = -0.30 to +0.75 across 9 leak-free synthetic datasets (A1 better in 3, worse in 6). A two-sided p > 0.05 asks for a tie that nothing
  guarantees, and the sign of the builder's observation (A1 worse, L = -0.74) is the opposite of the sign in other datasets.
- Neither criterion reacts to leaks (section 4): the draft gate fails the leak-free pipeline in 9 of 9 datasets and fails each leaking variant in 9 of 9.
  A gate that always trips has zero information.

## 3. The restated control

### NC-1 (gate G): label-invariance. Purpose: detect any flow from held-out post-window labels into predictions, tuning or selection.
Procedure. Take the run exactly as configured. Re-run it with every held-out cell's post-window retention replaced by garbage, applied to the underlying
cell object so that any copy (e.g. a duplicate in training) carries the same garbage: for the points after the window,
`ret_new = ret[w] - k_c (ret[w] - ret) + eps`, `k_c ~ U(0.3, 2.5)` per cell, `eps ~ N(0, 0.02^2)`, clipped to [0, 1.1] (`scramble` in `negcontrol_check.py`);
if the dataset has a life level L (ISU, SNL), use `ret_new = L + k_c (ret - L) + eps`, clipped, so that the set of forecast times (which stops at the first point
below L) is unchanged and is asserted equal. Window points and training cells untouched.
Pass iff, between the two runs: (a) every prediction row (inner-CV and outer-test, all arms, all seeds, same cell ids and times) is identical, max |difference| = 0
(same machine, same commit, 1 thread; if a platform ever breaks bitwise reproducibility, the tolerance is 1e-12 and a clean-vs-clean repeat must show the same);
(b) `tuning_done.json` (inner scores, chosen hyperparameters, backbone) and `margins_inputs.json` are identical. Any difference: gate G trips (stop, audit, section 12).
Where to run it:
1. **Before the freeze, mandatory:** the complete pipeline on the synthetic G2 design at Samsung size, at the candidate frozen commit, all confirmatory arms, one
   fold (evidence in the freeze checklist). This covers tuning/selection paths and the data layer.
2. **In every confirmatory fold run, predict stage:** after the final predictions, rebuild the test windows from cells with scrambled post-window labels,
   predict again with the same fitted arms and seeds, assert equality, write `invariance.json` (max |diff|, n rows) to the run record. Costs prediction time
   only and uses no real label; it covers the real loaders (reference check-up, throughput, window cut).
3. The train/test disjointness assertion of the guard (cell ids and condition keys) stays and is cited as the real-data analogue of leak variant A below.
No tolerance for "small" differences.

### NC-2 (interpretive, not gating): do the stress functions carry the gain?
Run A1 (A9 optional, same budget) on the Test B folds with the stress vectors permuted among conditions, separately in training and test (existing
`permute_stress`; R2 not needed). Contrast, paired by condition on the same held-out conditions and cells: `L_c = ln(S_A1,permuted,c / S_A1,real,c)`, where the real
run is the primary confirmatory run. Criterion: exact one-sided sign test of median(L) > 0 at 0.025 (one test; n = 40: at least 27 positives). Report median L,
exp(median L) - 1, positives k of 40, order-statistic interval. Consequence: pass licenses the sentence "the accuracy of the learned law depends on the
stress dependence it learns" (Discussion); fail removes it and the Discussion says that stress dependence was not shown necessary for the accuracy (competing
explanation E1, PREREG section 1). It does not stop the study and does not change the tier of any contrast.
Descriptive rows (no criterion): L(A9/A1) under real and under permuted stress, scores of A1, A9, R1, R2 under permutation. Read them with section 2 in mind.

## 4. Synthetic check (real `pinnkan` code, G2 demo design, 9 datasets, 10 held-out conditions each, builder-demo budgets: 2 TPE trials, 2 inner folds, steps_scale 0.15)
Variants: **clean** (as built, stress permuted); **leak A** (test cells also placed in the training set: grouping error); **leak B** (every test cell's window is one
check-up longer than the forecast-set assumes: off-by-one overlap). Each run twice, unmodified and label-scrambled. Seeds 31-34, 36-40 (seed 35 collided in the
design generator and was skipped). Rows compared per run: 5,940 (clean, leak B), 6,930 (leak A).

| | NC-1 flags a violation | max abs prediction change | draft criterion (i) passes | draft (ii) passes | draft gate passes | NC-2 per dataset (n = 10) |
|---|---|---|---|---|---|---|
| clean | **0 of 9** | **0 exactly** | 6 of 9 | 0 of 9 | **0 of 9** | 0 of 9 pass; see below |
| leak A | **9 of 9** | 0.148 to 0.657 | 3 of 9 | 0 of 9 | 0 of 9 | 2 of 9 |
| leak B | **9 of 9** | 0.201 to 1.109 | 5 of 9 | 0 of 9 | 0 of 9 | 0 of 9 |

Reading. NC-1 has no false alarm on the leak-free pipeline (identical to the last bit, including tuning records: `tuning_same` true in 9 of 9) and detects both
leaks in every dataset. The draft gate passes nothing, clean or leaking: it cannot discriminate. The mean L(A9/A1) under scrambled stress of the clean runs:
0.75, -0.30, 0.21, -0.25, -0.26, -0.10, -0.14, 0.54, -0.10 (sign flips with the draw).
NC-2: scrambling the stress raised A1's condition error in every dataset (mean error 1.26-2.34 pp with real stress, 2.24-3.88 pp scrambled; median L between 0.29 and
0.99), but with n = 10 conditions per dataset the exact sign test cannot reach 0.025 unless 10 of 10 are positive (8 or 9 of 10 were), so per-dataset NC-2 is
underpowered by design here. Pooled: 69 of 90 conditions positive (P(L > 0) = 0.77), median L = 0.46 (A1's error 59% higher when stress is scrambled). At the
Test B size the exact test needs 27 of 40; with P(L > 0) = 0.77 its power is about 0.94 (n = 13: 0.39, so Test C offers no such check). The 0.77 and 0.94 are
demo-budget, G2-truth figures, not Samsung expectations.
Limits of the check. Two leaks of many; tiny training budgets (A1 is under-trained, although it beat A9 under real stress in all 9 datasets); 9 draws of one generator. The
check demonstrates the properties of the two criteria, not the size of any effect on Samsung data. NC-1 is blind to what does not flow from labels through the
code (human selection after looking: stop rule 6; covariate use such as the design hull in collocation, E4). One more thing the builder should confirm: on datasets with a
life level (ISU, SNL) the set of forecast times ends at the first point below it, so `t_fc` encodes when a cell dies; NC-1 holds it fixed by construction and
therefore cannot detect an arm that uses the extent of its own forecast set (the arm code reads `t_fc` to evaluate at those times; `emit.py` line 195 reads `t_fc[-1]` for an emitted artefact; the builder should confirm that no fit or predict step uses the
extent of the forecast set).

## 5. Seed (the "sign-flip RNG seed issue")
Found: `metrics.signflip_p_two_sided(L, B=100000, seed=20261107)` carries a hard-coded placeholder ("until the statistician fixes it") that every call shares and
that equals the root integer of the `permute_stress` stream; `seeds.json` records "set by the statistics step"; `stats_step.bca_mean_ci` defaults to `seed=0` for every
contrast. Ruling:
1. The negative control, and every test of the pass/fail type, uses **exact binomial sign tests (no RNG)**; `signflip_p_two_sided` is removed from the control path
   (two-sided exact p, if ever shown, = min(1, 2 min(tail))). This matches TYPE1_SIGNFLIP.md, where the sign-flip test was rejected as primary.
2. Every remaining Monte Carlo step (BCa intervals, appendix permutation/Wilcoxon tests, bootstraps of sensitivity rows) uses
   `np.random.default_rng(np.random.SeedSequence([20261105, zlib.crc32(label.encode())]))` with `label` a fixed string such as `"B|H1a|BCa_mean_pp"` and B as in the
   prereg. **Seed root 20261105 is fixed by this ruling** (a date, chosen before any scoring, never changed in response to a p-value). The root and labels are written to
   `seeds.json` and covered by the config hash; changing them after FROZEN is a new version with a change-log row.
3. `permute_stress` keeps its own stream (`[20261107, 31, fold]`, `fold + 1000` for test); unchanged, it is part of the frozen code.

## 6. Edits requested (this file edits nothing else)
- PREREG_v2 section 10 first bullet: replace by NC-1 (gate G) and NC-2 (interpretive) above; remove the R2 and A9 criteria; arms for the permuted run: A1 (A9, R1, R2 optional, descriptive).
- Section 12 stop rule 3 / section 17.2 checklist: "NC-1 synthetic invariance run at the candidate frozen commit (Samsung-size G2), `invariance.json` in each confirmatory run".
- `run.py`: `negative_control()` computes NC-2 from the real run's scores plus the permuted run; add `invariance.json`; `metrics.py`: drop `signflip_p_two_sided` from the control; `stats_step.py`:
  `build_controls` reads the new fields; seeds as in section 5.2. Add a unit test: garbage labels leave predictions unchanged (clean) and change them (a deliberate leak fixture, e.g. leak B).
- Outcome table row G: tripped by NC-1 only; NC-2 failure is a wording consequence (section 3), not a gate.
