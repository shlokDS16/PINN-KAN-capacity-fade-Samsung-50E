# D013 Judge ruling: implementation choices of the build (a) to (e)

Judge: independent (did not make the choices). Date 2026-11-05. Status of the preregistration: v2, NOT FROZEN; `runs/prereg/FROZEN` was not created.
reading: PREREG_v2 in full; CONTRACT in full; code/README.md and runs/build_v1/RESULT.md in full; D011 judge (greps on backbone, delta_c, A5, A6, clip) and D010 judge
section 2 (law, tournament, fair hard-vs-soft rule); code read in full: `law.py`, `pinn.py`, `hard.py`, `specs.py`, `synth.py`, `tuning.py`, `arms.py` (A9 to A14 classes),
`semi.py` (first 120 lines), `__init__.py`. Not read: `data.py` beyond the loader and window rule, `free.py`, `baselines.py`, `metrics.py` beyond the scorer.
Checks (CPU, `CUDA_VISIBLE_DEVICES=-1`, one thread; synthetic data, or ISU/SNL **training folds** via `load_split(role="train")`; no outer test fold, no Samsung data,
no FROZEN flag): scripts and logs in `debates/D013_build_choices/checks/`. Every number below is from those logs. The checks are pilots on one synthetic design
or two inner-CV seeds: they decide direction, not size.

## 0. Verdicts

| | choice | verdict |
|---|---|---|
| (a) | one backbone h(y) for both terms | **accept, with scope wording and one derived-quantity definition** |
| (b) | per-cell offset delta_c on the calendar term of storage cells | **accept** (with scope wording; one sensitivity row) |
| (c) | interaction pairs | Samsung: accept (preregistered). ISU: accept (complete set). **SNL: change** (the builder's pair T x charge is degenerate) |
| (d) | clip 20 + 40 % residual warm-up | **accept the values, change the application**: the same clip must be applied to A9 (and, for one uniform recipe, A2); lam_res grid edge flagged |
| (e) | CUDA_VISIBLE_DEVICES = -1 | **accept**, add a run-time assertion and a reporting sentence |

Code and prereg edits required before the freeze are in section 7 (list C1 to C9).

## 1. (a) One backbone h(y) shared by the calendar and the cycling term

What is in the code: `dy/dt = [r_cal + r_cyc nu] h(y)`; one h per fold from the tournament; closed form `y = Psi^-1(a_cal t + a_cyc E)`. The D010 judge wrote `h_cal` and `h_cyc` separately
(D010 section 2); PREREG_v2 section 7 says "State factor (backbone) chosen once per outer fold ... shared by all law-based arms of that fold", which is silent on one-versus-two. The
builder resolved the ambiguity to one h. This ruling closes it.

**Verdict: accept for the primary analysis.**
Why this: (1) the closed form is exact, so A2 (hard ODE) and A1 (soft PINN) integrate the same law and H2 compares coupling, not integrators (the D010 "same G, same backbone" rule);
with two h the hard ODE needs a numerical solver per cell and per Adam step, so the fit times of build_v1 (A2 2.5 s) and the compute table of section 16 and the 30 s / 90 s timing rule of section 7
would have to be re-measured (not measured here). (2) One h adds no tuned dimension: the arm table dimensions (A1 6, A2 4, ...) stay as preregistered. (3) The tournament scores held-out **cycling**
conditions (`target_kind="cycling"`), so storage cells (132 of 279) do not choose the backbone by their number alone.
Why not the alternatives: (i) separate h_cal, h_cyc: 9 combinations in the tournament, no closed form, higher cost; its benefit (calendar fade is sublinear in time, cycling fade nearer
linear in throughput) is real but cannot be measured before the freeze without looking at Samsung retention (3.3(9)); (ii) learned shape parameters of h (a free exponent as in A10):
adds a tuned dimension to A1 and A2 and changes the prereg table; (iii) h on the cycling term only (calendar term plain): then the calendar rate has no saturation and storage
cells at 45 C and high SOC are forced to a constant rate; worse.

Bias on the primary contrasts (read from code, not measured):
- H1a (A1 vs A9): none from h; A9 has no law.
- H1b: none; every pool arm gets the same fold backbone (`ctx["backbone"]`).
- H2: the tournament runs on the hard ODE (A2) at default settings, so the backbone is chosen by the model that H2 pits against A1. This favours A2 slightly; conservative for the claim about the soft residual. Already in the prereg; state it.
- H6: A10 has two free time exponents (`r_cal`, `r_cyc` in `semi.py`); A1/A2 have three rigid shapes (constants Y0 = 1, gamma = 0.3 in y_s units). So A10 is more flexible in time shape.
  This is conservative for A1 (a win over A10 is not helped by it). It also means a H6 loss may come from the rigid shape and not from the stress maps; the paper must say so.
- The synthetic generator (`synth.py`) uses a single self-limiting h and the same delta scope. G0 therefore cannot validate (a) or (b); P1 tests the fit machinery only. G1 (power-law time warp)
  is the only synthetic test of time-law misspecification and tests the shared-h structure indirectly. State this in the P1 text.

Evidence of the stakes (A2 on the synthetic G0 training/test split, one seed, `checks/a2.log`): with the right backbone the forecast error is 0.88 to 0.97 pp, with `constant` it is 5.6 to 5.9
pp. The backbone is a first-order choice, so the tournament and its logging (`backbone_tournament.json` per fold) are part of the reported method, not a detail.

Hyperparameter status. Structure choice, not tuned. Y0 = 1 and gamma = 0.3 (y_s = 10 pp units, so Y0 = 10 pp loss) are **fixed**, frozen with the commit, not tuned in the inner CV (a tuned
shape would make the tournament a search). Sensitivity range (A2 only, cheap, training side): Y0 in {0.5, 2}, gamma in {0.15, 0.6}: report whether the chosen backbone and the tournament
means change. If the tournament chooses `accelerating` or `constant` in a fold, report it.

Required statements.
- Prereg section 7 (replace the backbone sentence): "One state factor h(y) multiplies the sum of the time-driven and the throughput-driven rate, dy/dt = [r_cal + r_cyc nu] h(y), with h chosen once per outer fold ...". Cite that the D010 draft had separate factors and that one factor was chosen for the exact solution and for compute.
- Paper: "single state-dependent modulation shared by both terms"; **never** "independent superposition of calendar and cycle ageing". With h not constant the contributions are additive in the rates only.
- **Derived-quantity definition (affects 11a item 4).** The "share of predicted fade attributed to the calendar term" is not defined for a non-constant h. Define it as the counterfactual
  `share_cal = y(a_cyc = 0) / y(full)` at the cell's last check-up, and the "calendar alone exceeds the observed total fade" count as `y(a_cyc = 0) > observed y` (same counterfactual).
  Without this definition the item is ambiguous.

## 2. (b) Per-cell offset delta_c on the calendar term of storage cells

What is in the code (`law.amplitudes`): `a_cal = r_cal exp(delta)` for storage cells, `a_cyc = r_cyc exp(delta)` for cycling cells; a cycling cell's calendar term gets no cell offset.
Prior sd TAU = 0.15 (fixed, same constant in A1, A2 inversion and A10's factor prior), MAP at test time from the window. The prereg says only "delta_c" (section 7: A2 "delta_c MAP from the window").

**Verdict: accept.**
Why this: a storage cell has no cycling term, so an offset has to act on the one term it has, otherwise replicate variation between storage cells is pushed into the shared surface F
(or the law), through the residual, as bias in the calendar surface that the cycling cells then inherit. One scalar per cell with the same prior family in every law-based arm keeps A1, A2 and A10
on the same footing (section 7.2).
Why not the alternatives: (i) no offset on storage cells: replicate scatter of storage trajectories is forced into a(SOC), E(SOC); (ii) one offset scaling **both** terms for every cell (the same
scope as A10's factor): defensible and arguably more robust to a mis-specified calendar share of cycling cells (the SOC_mid choice for the calendar term of cycling cells is itself an assumption,
README item 3), but then the cycling cell's offset also rescales a calendar share that the 132 storage cells identify, mixing the two terms; (iii) a separate delta_cal and delta_cyc per cycling
cell: not identified from a window of 3 to 5 points.

Bias on the primary contrasts: H1b none (shared). H1a: A9 has no delta but a 2-dimensional (tuned 1 to 3) z_c; this is a model difference by design (E1 control), not a recipe difference.
H6: A10's factor `kappa_c` scales the **total** predicted loss (`semi.py`), A1's delta scales the cycling term only for a cycling cell. A10 is therefore more flexible on cycling cells with a large
calendar share (45 C). Conservative for A1; must be printed. The prereg 7.2 text "same prior family" is true for the prior (lognormal, sd TAU) and false for the scope.
Synthetic circularity: the generator draws its offsets with exactly this scope and sd 0.15 (`synth.py`), so TAU is exactly right on synthetic data. On real data it is unknown.

Hyperparameter status. TAU = 0.15 is **fixed**, not tuned (the pilots' round constant; tuning it would add a dimension to A1, A2 and A10 and a flexible prior can absorb the stress signal).
Diagnostics required (descriptive, no decision): report the sd of the fitted delta_c on the training cells per fold against TAU; flag a ratio outside [0.5, 2]. Sensitivity (A2, cheap): TAU in {0.075, 0.3}.
Sensitivity row **"delta on total rate"** (cycling cells: delta scales both terms) for A1 and A2 on Test B at the primary tuned settings; if the primary tier of H1a, H1b or H6 changes, the abstract says so.

Required statements. Prereg 7.2: "the factor has the same lognormal prior (sd 0.15); its scope differs: A1/A2 scale the term(s) the cell has, A10 scales the total loss; the difference favours A10". Paper methods: define the scope in one sentence and add that
the calendar contribution of a cycling cell is the population value at (T, SOC_mid).

## 3. (c) Interaction pairs for A5

Facts from the data design (training sides only, `checks/chk_snl_struct*.py`, printed in section 8):
- ISU: three stresses (charge, discharge, DoD). The builder's three pairs are **all** pairs. That is the complete second-order GAM: no selection, nothing to bias. Accept.
- Samsung: the three pairs (T x C_ch, T x SOC_mid, DoD x SOC_mid) are in PREREG_v2 7.1, fixed before any Samsung model run. Accept. Wording: "three prespecified pairs", not "interactions";
  H1b is not weakened by the missing pairs because A7 (MLP) and A1 can represent any interaction and the comparator is the inner-CV best of the pool.
- **SNL: in every one of the five Test B training folds the charge rate takes a single value (0.5 C); DoD takes two values (0.6, 1.0) in four folds and one in the fifth; temperature three; discharge four.**
  So the builder's pair T x charge is a spline tensor in a constant input (it reduces to a second temperature function at charge 0.5 and extrapolates arbitrarily for a held-out condition with another charge),
  and the other two pairs use DoD, which in training is a two-level variable. This is not a "preference", it is a degenerate pair set.

**Verdict on SNL: change.** Rule (design-based, label-free, fixed for all folds): a stress enters a pair only if it takes at least 3 distinct values among the training conditions in every Test B fold
(temperature, discharge rate), and the chemistry flags are allowed as partners of such a stress. This gives 7 pairs: T x discharge, and each of (LFP, NCA, NMC) x T and x discharge.
Why this: it uses the one physically established structure of the SNL set (chemistry-specific temperature and rate dependence) and none of the labels. Why not: (i) keep the builder's set: degenerate and gives a weak A5, so the
"best prespecified-interaction" comparator is not credible; (ii) all pairs of the 7 inputs (21): most involve a constant input, many parameters on 18 to 19 training conditions; (iii) choose pairs by inner CV: the pair set
becomes a tuned categorical and A5 gets an extra search dimension; not allowed by the equal-budget rule.

Pilot check (SNL Test B folds 0 and 4, training conditions only, inner CV 3 folds, fixed settings, 2 seeds; `checks/snl_pairs0.log`, `snl_pairs4.log`), inner-CV RMSE in pp, mean of the 4 runs: A4 additive 4.41,
A5 builder pairs 4.57, A5 design-rule pairs 4.30, A5 T x discharge only 4.40. The same additive model differs by 0.45 pp between the two seeds in the same fold, so these differences are inside the seed noise:
the check shows direction only (the degenerate set is not better, the design-rule set is not worse), not a size. No pair choice was made from labels.

Effect on H1b: with the builder pairs A5 would rarely be the pool winner on SNL, so the pool comparator would be A4 or A7 and H1b would still be a fair KAN-versus-best-alternative test. The change matters for the **wording**
("best prespecified-interaction model"), the H3 contrast, and the SNL table (A5 must be a competent interaction model). It does not bias H1b toward the KAN, as far as the check shows.

Hyperparameter status. The pair set is fixed (not tuned). The interaction-grid size `igrid` in {3, 5} stays tuned (prereg A5 dimension 5). Range: unchanged.

Required statements. Prereg 7.1 (A5 row): the pair set per dataset (Samsung three pairs as preregistered; ISU all three pairs; SNL the seven above) and the rule in one sentence. Paper: Methods table "stress-map pool", with the sentence "the SNL
charge rate is constant at 0.5 C in the training conditions and therefore excluded from interactions". Note the SNL results remain "not blind" (3.4).

## 4. (d) PINN gradient clipping at norm 20 and a 40 % residual warm-up

What is in the code: `fit_pinn` (A1, A3, A4, A5, A7, A13, A14): Adam 5e-3, cosine decay, residual weight ramped 0 to lam over the first 40 % of 2000 steps, global gradient-norm clip 20. `fit_data_only` (A9) and `fit_hard` (A2) have **no** clip.

What the check shows (synthetic G0, Samsung-size design 32 + 19 conditions, 3 replicates, one design, one seed, A1 default settings, 2000 steps, forecast RMSE in pp on 8 held-out conditions; `checks/clip_a.log`, `clip_b.log`):

| lam_res | clip 20 + warm-up 0.4 (frozen recipe) | no clip, warm-up 0.4 | clip 20, no warm-up | no clip, no warm-up | clip 50 + 0.4 | clip 5 + 0.4 | clip 20, warm-up 0.2 / 0.6 |
|---|---|---|---|---|---|---|---|
| 0.01 | 0.91 | 10.25 | 0.92 | 4.21 | 0.89 | 0.89 | 0.92 / 0.91 |
| 0.1 | 0.96 | 1.08 | 1.04 | 8.67 | 0.98 | 0.97 | 1.01 / 0.98 |
| 1 | 1.32 | 1.83 | 1.31 | 3.22 | 1.26 | 1.35 | 1.30 / 1.50 |
| 10 | 1.71 | 2.04 | 1.93 | 7.74 | 1.61 | 1.60 | 2.11 / 1.64 |
| 100 | 2.85 | 20.28 | 3.28 | 10.12 | 2.61 | 2.94 | 3.03 / 2.46 |

Readings. (1) The **clip**, not the warm-up, is the load-bearing stabiliser (without clip, 10.25 pp at lam 0.01 even with warm-up; with clip, no warm-up costs at most 0.4 pp, at lam 10 to 100). (2) Within clip 5 to 50
and warm-up 0.2 to 0.6 the result moves by about 0.05 to 0.4 pp (larger at lam >= 10, one seed): the values 20 and 0.4 are not a knife edge. (3) The clip is not a rare-spike guard: the share of steps with gradient norm above 20 is
0.29 (lam 0.01), 0.65 (0.1) and 1.0 (lam 1 or more); the median norm grows from 4 to 13,000 as lam goes from 0.01 to 100. So the clip is part of the optimiser, and it binds differently at different lam (with Adam a constant rescale is
harmless, a per-step rescale is not). (4) Error rises monotonically with lam from 0.91 to 2.85 pp **on a well-specified law (G0)**. That is an optimisation limit (stiff residual term at 400x loss scaling), not physics; and the best value sits at the
**lower grid edge** (0.01). Under the prereg edge rule the grid extends downwards.

**Is the recipe applied equally where needed? No: A9 is not clipped.** Check (`checks/a9.log`, A9 on the same split, 1500 steps, 4 configurations of its tuned space x 2 seeds, no clip vs clip 20): forecast RMSE changes from
1.56/1.27 to 1.34/1.36 (width 32, depth 3), 1.57/1.57 to 1.46/1.49 (width 128, depth 4), 1.92/1.83 to 1.19/1.19 (width 16, depth 2, wd 1e-2), 1.41/1.47 to 1.38/1.36 (width 64). Part of A9's tuned space is handicapped by about 0.1 to 0.7 pp,
i.e. up to 30 to 40 % of an error level that the H1a margin (2 % superiority) is set against. An unclipped A9 against a clipped A1 therefore confounds "residual on/off" with "optimiser recipe" and is **biased toward A1** (anti-conservative).
For A2 (`checks/a2.log`): the clip is inert (0.88 vs 0.90, 0.97 vs 0.93, 0.92 vs 0.92 pp with the self-limiting backbone; gradient norms rarely reach 20).

**Verdict: accept clip 20 and warm-up 0.4 as fixed recipe constants; change the application.**
- Apply the same global-norm clip 20 to A9 (required) and to A2 (for one uniform recipe; measured inert). The warm-up exists only where a residual exists (A1, A3, A4, A5, A7, A13, A14); A9 and A2 have none to ramp. State it so.
- Pool arms A3, A4, A5, A7 and A13/A14 already share `fit_pinn`, so H1b has an equal recipe. A10, A11, A12, R1, R2 have no gradient fit; not applicable.
- Alternative to be kept in mind (not chosen): define H1a as A1 with lam = 0 (same law, delta, tuned configuration). Not adopted because the prereg fixed A9 with a larger search space (conservative, OPEN-3); the `clip` fix removes the confound. A descriptive row
  "A1 refit with lam_res = 0 at its tuned settings" is allowed in the appendix if CPU allows.

Why this and not the alternatives: (i) drop the clip and rely on the warm-up: fails (10.25 pp at lam 0.01); (ii) tune clip and warm-up in the inner CV: adds two dimensions to every PINN arm (dimension table of 7.1 would change), turns a stability device into a
free parameter and gives A1 and the pool (not A9) two more tuning knobs, the opposite of the equal-budget rule; (iii) lower learning rate or a different optimiser: changes the pilots' recipe and needs a new search; not affordable before the freeze.

Hyperparameter status: **fixed** (clip 20, warm-up fraction 0.4, lr 5e-3, 2000 steps, cosine to 10 %); nuisance, not scientific. Sensitivity (appendix, mandatory, cheap: the primary tuned settings, 5 seeds, one fit per variant and fold, A1 and A9 for H1a only):
clip in {10, 50} and warm-up in {0.2, 0.6}; about 200 fits, about 1 CPU-h. If the tier of H1a changes across these variants, the abstract says so.

lam_res grid: **add 1e-3 to {1e-2, 1e-1, 1, 10, 100}** (6 values; dimension count of A1 unchanged). Evidence is one design and one seed (synthetic G0), so the change is a precaution under the prereg edge rule, not a result; the rule's own trigger
(a tuned value at 1e-2 on the training-side tuning of the pilot data) can be checked on the ISU/SNL training sides before the freeze. If the lead prefers to leave the grid, the paper reports the share of folds with the tuned lam at the lower edge.

Required statements. Prereg 7: "Optimiser recipe (all gradient-trained arms): Adam 5e-3, cosine decay to 10 %, global gradient-norm clip 20; in arms with a residual the residual weight is ramped linearly from 0 to lam_res over the first 40 % of steps.
Fixed constants, frozen with the commit; chosen after a divergence on a synthetic design (data MSE 1.7 and 34 at lam_res 0.1 and 1 without them), sensitivity in appendix." The divergence story is a disclosure sentence (design choice made after a fit
failed on synthetic data, not on Samsung). Paper: same, plus "the clip binds on most steps at large lam_res".

## 5. (e) CUDA_VISIBLE_DEVICES forced to -1

Facts: an empty value is dropped on Windows, so torch then sees the GPU (found by a test). `pinnkan/__init__.py` sets `-1` unconditionally (assignment, not `setdefault`), before any torch CUDA initialisation; the launcher imports `pinnkan` first;
`env.json` stores `cuda_available`. GPU idle at the check (12 MiB used).
**Verdict: accept.** It enforces CONTRACT section 1 (no GPU job without the lead's instruction), gives single-thread CPU determinism for the reproducibility statement, and cannot be bypassed by an empty environment variable.
Changes: (1) at run start `assert not torch.cuda.is_available()` (raise otherwise) so a wrong environment cannot silently produce GPU numbers in a frozen run; any later GPU use needs the lead's instruction and a new config key, not an environment edit.
(2) The older tests (`test_p2_units.py`, `test_p45_units.py`) still use `setdefault("CUDA_VISIBLE_DEVICES", "")`; harmless on CPU but change to `-1` for consistency. (3) Paper/prereg run-record sentence: "All computations on CPU, float32, one thread, torch 2.11.0+cu130 (CUDA build executed on CPU),
numpy 2.4.2, Python 3.14.3 (from `env.json` of the smoke runs); bitwise reproducibility is claimed on the same machine and library versions only." No effect on any contrast.

## 6. Cross-cutting: do any of (a) to (e) bias the primary contrasts?

| contrast | (a) | (b) | (c) | (d) | net |
|---|---|---|---|---|---|
| H1a A1 vs A9 | none | none (E1 control: A9 has z_c) | none | **A9 unclipped favoured A1 (fixed by C1)** | unbiased after C1 |
| H1b A1 vs pool | equal | equal | SNL A5 degenerate pairs (fixed by C2); Samsung/ISU fine | equal (shared `fit_pinn`) | unbiased after C2 |
| H6 A1 vs A10 | A10 more flexible in time shape: **favours A10** | A10's factor on total loss: **favours A10** | not applicable | not applicable | conservative for A1; both must be printed |
| H2 A1 vs A2 | tournament run on A2: slightly favours A2 | same scope | not applicable | clip uniform after C1; warm-up only soft | conservative for the soft-PINN claim |

All four named differences either vanish after C1/C2 or run against the claim. None of them can be tuned away; none is tuned.

## 7. Required edits (for the lead, the implementer, the statistician)

- **C1 (code).** Apply `GRAD_CLIP` (20) to `fit_data_only` (A9) and `fit_hard` (A2). Add the clip to the recipe constants block; rerun the 74 pk tests (A9/A2 tests have no clip-specific assertion; add one that the clip is called).
- **C2 (code).** `specs.SNL.interaction_pairs` := (temp_c, discharge_c) + (is_LFP, is_NCA, is_NMC) x temp_c + (is_LFP, is_NCA, is_NMC) x discharge_c. Update the code comment (the "builder's pair choice, flagged" line) and README item 7. ISU and Samsung unchanged. Check `test_arm_table_matches_prereg_dimensions` still passes (dimension of A5 stays 5).
- **C3 (prereg, grid).** `lam_res` grid gains 1e-3 (A1, A3, A4, A5, A7, A13 and A14 where it appears); or a stated reason to keep it; the lead decides.
- **C4 (code).** Run-start CUDA assertion; tests use `-1`.
- **C5 (prereg text).** Section 7: backbone sentence (one h), optimiser recipe paragraph, A5 pair sets per dataset; section 7.2: scope sentence of the A10 factor; 11a item 4: counterfactual share definition.
- **C6 (prereg, sensitivity rows 9.8).** Add: (k) optimiser recipe variants (clip {10, 50}, warm-up {0.2, 0.6}) for H1a; (l) delta scope "total"; (m) A2-only tournament sensitivity to Y0 {0.5, 2}, gamma {0.15, 0.6} and TAU {0.075, 0.3}; (n) optional appendix row "separate h_cal and h_cyc" for A2 (RK4), descriptive, only if
  CPU remains after the core set; no decision uses it.
- **C7 (reporting).** Per fold: tournament table, tuned lam_res (edge share), sd of fitted delta_c on training cells against TAU, share of steps clipped for A1 and A9 (log the clipped fraction in the run record).
- **C8 (paper wording).** "Single state-dependent modulation"; "three prespecified pairs"; the SNL charge-rate sentence; the A10 flexibility sentence (two free time exponents, factor on total loss); the synthetic-circularity sentence for P1 (generator shares choices (a) and (b)).
- **C9 (disclosure).** Add to the 3.3(10) disclosure sentences: "The optimiser recipe (gradient clip, residual warm-up) was fixed after a divergence on a synthetic design; the SNL interaction pairs were fixed from the training-design structure; neither used Samsung data."

## 8. Debate protocol items (CONTRACT section 3)

Alternatives with reasons are in each section (at least three per choice for (a) to (d); (e) has the only safe option plus the assertion). 
*Is this the best possible?* No: the largest open weakness is not in these five choices but visible through them: the PINN recipe degrades with lam_res on a **well-specified** law (G0), so the soft residual is optimiser-limited at large weight.
If the Samsung tuned lam sits at the lower edge the paper's mechanism sentence ("the residual holds F to the law where there are no data") becomes a weak-weight statement; the prereg's own H1a result will show it.
*What a JES reviewer would hit:* (1) rigid time-shape constants (Y0, gamma) against A10's free exponents: address by the Y0/gamma sensitivity; (2) a PINN that needs a clip active on every step at lam >= 1: address by the clipped-fraction log and the recipe sensitivity; (3) delta scope: sensitivity row; (4) SNL A5.
*What would make a reviewer reject:* an unclipped baseline against a clipped PINN (removed), a degenerate competitor (removed), and a synthetic positive control that shares the generator's choices (disclosed).
*Opponent:* none was convened (the lead asked for a single independent ruling); the gate auditor should check C1 to C9 against the code at the freeze commit.

**Re-open if:** the training-side Samsung tournament selects `constant` or `accelerating` in more than one fold (then (a)'s shape rigidity or the single h is the first suspect); the sd of fitted delta_c on the training cells is outside [0.5, 2] x TAU in most folds;
the tuned lam_res sits at the new lower edge in most folds; the lab-stratified or "total-scope" sensitivity changes a primary tier; the A9 clip fix moves the A9 inner-CV score by more than 10 % (then report both and consult the statistician).

## 9. Files

Checks (scripts and logs): `debates/D013_build_choices/checks/` : `chk_clip.py` (+ `clip_a.log`, `clip_b.log`), `chk_a9.py` (+ `a9.log`), `chk_a2.py` (+ `a2.log`), `chk_snl_struct.py`, `chk_snl_struct2.py` (+ `snl_struct.txt`), `chk_snl_pairs.py` (+ `snl_pairs0.log`, `snl_pairs4.log`).
Not produced: any run under `runs/`; no outer test fold was read; no Samsung data were read; `runs/prereg/FROZEN` does not exist.
Unverified: the failure-mode literature on PINN training (Krishnapriyan et al., NeurIPS 2021, "Characterizing possible failure modes in physics-informed neural networks") is cited from memory; verify with the citation-validator before it is used in the paper.
