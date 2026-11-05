# D020 ml-expert: pre-freeze changes that let A1 show its true best at g1, with equal strength for every comparator (2026-11-05)

Role: proposer (ml-expert). Not a validator: the statistician, red team and gate auditor check this file; the judge rules.
Reading depth: full text of `research/CONTRACT.md`, `runs/pilot_P3/RESULT.md`, `runs/pilot_P4/RESULT.md`,
`runs/pilot_P5/RESULT.md`, `runs/build_v2/CHOICES.md`, `code/pinnkan/{pinn,tuning,specs}.py`, `code/models/kan_spline.py`;
partial: `runs/prereg/PREREG_v4.md` sections 1, 4, 5, 6, 7, 8, 9, 17 (and a grep of section 11 for wording);
`debates/D016_roles/02_judge.md` sections 0, 1, 5, 6, 8; `debates/D018_test_rule/01_judge.md` sections 0-1 (2-3 via the
PREREG_v4 copy in 9.3-9.4); `runs/build_v1/RESULT.md` sections 2 and 7; `code/pinnkan/arms.py` lines 1-110; `law.py` lines
1-40 and 128-330; `run.py` (grep around tuning, thinning, tournament); `runs/prereg/BLINDING_LOG.md` head; D016 proposal 5.6.
RES section 9 was not re-read; its power values are quoted from the PREREG_v4 section 1 copy.
No Samsung retention or capacity value, no outer-test score and no ISU outer-test fold was opened. No code was edited or run.
Every number below is quoted from a named file, or is labelled "arithmetic" (from the build_v1 timing table) or "speculation".

---

## 0. Summary for the lead
- At full data the tuned data-only learners already sit at or below the replicate floor (P3: ISU 0.90, SNL 1.13), so g1 is the
  only place A1 can win, and nothing about g1 has been measured. Under the confirmatory test, 80 % power at g1 needs a
  median reduction of about 21-25 % (rho 0.75). The changes below remove avoidable handicaps (seed variance, noisy and
  mis-sized inner CV, a training loss that does not match the endpoint, ridge-only splines). They do not create a 20 % effect.
  If the law's true advantage at g1 is small, P0 or P+ with e2/e3 stays the likely outcome.
- **Recommended now (no pilot needed for the principle, the pilot sets the go):** (1) score every seeded P-chain arm as a
  5-seed prediction ensemble; (2) 4 inner folds instead of 2 at m = 8 for every tuned arm; (3) a condition-balanced data loss
  in every gradient-trained arm, which matches the endpoint and what A11/A12 already do.
- **Blinding correction:** a "Samsung training folds" pilot that uses labels is not allowed before the freeze. Every Samsung
  cycling condition is an outer-test condition in exactly one Test B fold, and the storage conditions are outer-test in S2.
  `BLINDING_LOG.md` forbids inspecting them. The pilot of section 4 therefore runs on ISU training sides only.

---

## 1. Headroom at g1 = (8 cycling conditions, 2 check-ups), against D\* = inner-CV best of {A9, A11, A12}

**Evidence on file (no g1 measurement exists):**
- *Full data, no headroom over data-only learners.* P3 (`runs/pilot_P3/RESULT.md`, verdict table and Numbers): best flexible
  learner / replicate floor = 0.90 (ISU W4) and 1.13 (SNL W100). LightGBM best in 3 of 5 (ISU) and 5 of 5 (SNL) folds. A
  per-cell power law from the window alone is worse (6.67 vs 5.21 pp ISU W4), and persistence is far worse (13.22 pp). P3
  caution 1: the learners' advantage is the held-out cell's own window, which the floor does not see.
- *The law, not the KAN, carries the forecasting gain.* P4: KAN vs GAM forecast gap 0.0-0.1 pp (median 0.89 vs 0.96 pp). P5:
  soft PINN vs hard ODE median ratio 0.96 (record-end collocation) and 0.84 (whole-axis collocation). The PINN gain over
  lam_res = 0.01 (nearly data-only F) held in inner CV in 5 of 5 draws (P5 item 2). These are synthetic draws on the ISU
  design, so they show direction, not size.
- *Power.* PREREG_v4 section 1: under the fixed design-effect sign test, the 80 %-power reduction is 0.256 / 0.212 / 0.147
  at rho 0.6 / 0.75 / 0.9. P1S power is 0.05 / 0.28 / 0.71 / 0.96 for a true reduction of 0.10 / 0.15 / 0.20 / 0.25.
  Power rises with rho, the correlation of the two arms' log condition errors. Anything that removes A1-specific noise from
  S_A1,c (seed variance, selection noise) raises the effective rho as well as lowering the mean. Speculation: of the levers
  listed here, this is the one that can move power by more than its effect on the mean.

**Where A1 can most plausibly gain at g1 (speculation, from the structure of the arms):**
1. *Long horizons after a 2-check-up window.* D\* learners map (stress, window summary, horizon) to the drop since the window
   end. At k = 2 the window summary comes from 3 points, which are early (often in the initial fast fade), and the training
   rows come from about 8 conditions. The law integrates y = Psi^-1(a_cal t_n + a_cyc E_n(t)), so it extrapolates with a
   physical time and throughput shape. Trees cannot extrapolate beyond the horizons they have seen. A GP reverts towards its
   mean.
2. *Conditions where calendar loss is a large share of the total* (low throughput: low C-rates or small DoD). In A1 the
   calendar term (T, SOC_mid) is learned from 132 storage cells with an Arrhenius abscissa built in (`law.py` `r_cal`,
   `x_arr`). With storage rows "in", D\* can see storage rows, but it cannot split a cycling cell's fade into calendar plus
   cycle parts. The extra information sits exactly where 8 cycling conditions are thinnest.
3. *Interior held-out conditions.* The max-min subset spans the hull first (PREREG 4.1), so most held-out conditions lie
   inside it. A smooth law with an h = 1 near-additive map interpolates there. LightGBM is piecewise constant across the 2-4
   distinct values each stress takes among 8 conditions.

**Where A1 is likely to lose (speculation, partly stated in PREREG 6):**
1. The first post-window check-up: the local window slope is what data-only learners exploit (PREREG 6 lists this as an
   expected regression).
2. Cells with a knee or accelerating fade inside the forecast. One state factor h per fold, chosen by the tournament, cannot
   follow a knee. Stroebl JES 142 states the cycle part is inadequate (PREREG 1, partial reading by the D18 judge).
3. Lab and stage offsets at k = 2. Three latent quantities per cell (z_c of dimension 2 plus delta_c) are inferred from 2 new
   points plus the residual, with a nominal prior (TAU = 0.15, SIGMA = 0.05 from the synthetic pilots, `law.py` lines
   28-29). At m = 8 the lab composition of the subset is thin.
4. Optimisation variance at m = 8. A1 is the most fragile arm: P5 draw 1 reversed by 0.4 pp, and a 6-dimensional
   categorical space with N = 20-40 TPE trials is scored on 8 inner conditions.
5. Temperature extrapolation at m = 8 is not a risk by construction: each temperature has at least 2 conditions. The 35 C
   conditions are all lab INT, so lab and temperature cannot be separated (scope wording already fixed).

**Two procedural handicaps that affect every arm, but hit A1's large space hardest:**
- *Inner CV at m = 8 trains on 4 conditions.* Two inner folds (PREREG 4.1, `tuning.inner_k_for_m`) mean each inner model sees
  4 cycling conditions, which is a different regime from the target m = 8. Because the max-min subset puts extreme
  conditions first, holding out half of them makes the inner task extrapolation, while the outer task is mostly
  interpolation. Selection is therefore biased towards over-regularised configurations. It is also noisy: one partition, 8
  validation conditions, and argmin over 20-40 trials. The noise grows with the number of tuned dimensions (A1 6, A12 7,
  A11 5, A9 4).
- *Training loss and endpoint do not match.* The PINN, hard-ODE and A9 data terms are a mean over observation points
  (`pinn.py` line 147, line 264). The endpoint weights cells equally within a condition and conditions equally (PREREG 6).
  A12 already weights rows so that every cell counts once (`code/pilots/p3_headroom.py` line 203). A11 samples a fixed
  number of rows per cell (P3 setup). So the comparators are already endpoint-aligned per cell, and A1 and A9 are not.

**Code/text mismatch to fix (not a change of design):** PREREG 7 says the backbone tournament is chosen "once per outer
fold", while `run.py` lines 315-319 run it on the thinned training side of each (fold, m). The code is the correct reading.
A tournament run at m = 32 and reused at m = 8 would leak 24 extra conditions into the law-based arms only. The text should
say "per (outer fold, m), on the thinned training side". The tournament also uses h = 4 (`arms.TOURNAMENT_HP`) at every m.
Using h = 1 at m < 32 would match the m = 8 regime. This is minor and optional, and applies to all law-based arms alike.

---

## 2. Ranked pre-freeze changes (at most 8)

Common rules for all items:
- Every change applies to every arm it can apply to, at every grid cell, in every downgrade row (including the g1
  random-subset row (iv)) and in NC-1/NC-2. Nothing is adopted for A1 alone.
- No item changes the D017/D019 outcome table (section 11 states, titles, sentences), g1, the margins, rho_s0, w, the
  subsets or the Test B folds.
- "Touches" lists the approved rulings (not frozen yet) that a decision row D020 must amend.
- CPU figures are arithmetic from the build_v1 timing table (`runs/build_v1/RESULT.md` section 2: A1 14.5 s, A4 10.6, A13
  13.4, A2 2.5, A9 2.7, A11 2.2, A12 about 0 s per full-step fit on a synthetic Samsung-size design; A15 is about 1.5 x A1
  per CHOICES 3.2). They are not Samsung measurements; J16's expected-to-ceiling factor is about 3.7.

### C1. Score every seeded P-chain arm as a 5-seed prediction ensemble (rank 1)
- **What.** The condition score uses the RMSE of the mean of the 5 final-refit forecasts (seeds 0-4) per cell and check-up.
  Today it is the mean over seeds of the per-seed RMSE (`metrics.seed_condition_scores`). Applies to A1, A9, A2, AG/A4, A13
  and A12 (bagged over its 5 seeds: subsample and colsample 0.8 make it seed-dependent). A11 and A10 are deterministic and
  unchanged. Per-seed scores stay as a descriptive reproducibility row.
- **K chain stays single-model.** K1 and K2 use per-seed scores (the current rule) for A1, A15 and G15. The approved
  sentences say "a closed-form stress law" (singular, PREREG 11), and an average of five laws is not one law. Within each
  chain, every arm is therefore defined the same way.
- **Expected effect.** For each cell, the RMSE of the mean forecast is at most the mean of the per-seed RMSEs (triangle
  inequality). The change can only lower each seeded arm's score, and the gain equals its seed-variance share. That share
  is likely largest for the neural arms at m = 8 (speculation; the pilot measures it). Deep ensembles are a standard strong
  model (Lakshminarayanan et al., arXiv 1612.01474, identity known, not re-read). It also raises the effective rho of P1 (see
  section 1).
- **Comparator parity.** A9 (a D\* candidate) gains the same way. A12 gains from bagging. A GP posterior mean already
  averages, which is the standard comparison of deep ensembles against GPs. D\* selection stays by inner CV, unchanged.
- **Cost.** 0 extra fits: the 5 refits exist and `predictions.csv` stores them per seed (`run.py` line 11). Coder about 2 h
  (metrics plus `stats_v4` reading the ensemble scores for P1, P2, P3, the secondary family, the ladder and the downgrade
  rows; per-seed scores for K1 and K2).
- **Risk.** It redefines the primary endpoint (PREREG 6 and 8), so the statistician must re-sign. The ladder (9.6) and P2
  stay coherent because A1, A9 and AG are all ensembles.
- **Touches.** PREREG 6 and 8 (statistician-signed sections) and the seed wording in 9.8 and 9.9 rows. Not D017/D019: no
  sentence names the seed handling (grep of section 11).

### C2. Four inner folds at m = 8 (and at m = 16 if CPU allows), the same for every tuned arm (rank 2)
- **What.** `inner_k_for_m`: 4 folds at m = 8, so each inner model trains on 6 conditions and validates on 2. Temperature
  stratification with round-robin keeps at least 1 condition per temperature in each inner training set, because every
  temperature has at least 2 conditions at m = 8. Same N, same TPE seed, same inner folds for every arm and for the
  tournament.
- **Expected effect.** Inner-train size moves closer to the target (6 vs 4 of 8), and the validation task becomes less
  extrapolative, so selection is less biased towards over-regularised configurations. On model-selection bias in small-n CV
  see Varma and Simon 2006 (doi 10.1186/1471-2105-7-91, [T] in the knowledge base) and Cawley and Talbot 2010 (JMLR 11,
  identity known, not re-read). The size is unknown; the pilot decides. A larger N is not the lever: with noisy validation,
  more trials deepen the winner's curse.
- **Comparator parity.** Identical for A9, A11, A12, A4, A2, A13, A15 and G15.
- **Cost.** At N = 40: +80 fits per arm per outer fold. A1 1.6, A4 1.2, A13 1.5, A15 2.4, G15 1.8, A2 0.3, A9 0.3, A11 0.2
  CPU-h, so about 9.3 CPU-h for the m = 8 core. Add about 6.4 CPU-h for the three random-subset draws (A1 and the D\*
  candidates). At N = 20 the totals halve. The ceiling is about 3.7 x. m = 16 would add a similar amount and can be
  dropped first (it is estimated only). Coder 0.5 h.
- **Risk.** Validation folds of 2 conditions: the per-fold scores are noisier, but the pooled out-of-fold score still covers
  all 8 conditions once. If m = 16 keeps 2 folds, the learning curve mixes two selection regimes, which must be disclosed.
- **Touches.** J16 1.2 and PREREG 4.1 ("2 for m in {8, 16}"), a judge ruling, so D020 needs a decision row and the gate
  auditor. The power simulation does not depend on it. Not D017/D019.

### C3. Condition-balanced data term in every gradient-trained arm (rank 3)
- **What.** Per-point weights in the data term so that each training condition contributes equally and each cell contributes
  equally within its condition. Weights are normalised to mean 1, so the 1/SIGMA^2 scale and clip 20 keep their meaning.
  This mirrors the endpoint (PREREG 6). Applies to A1, A2, A4/A5, A9, A13, the A15/G15 parents and refits. A12 changes from
  per-cell to per-condition sample weights. A11 draws rows per condition instead of per cell, the GP analogue.
  Test-time inversion is per cell and unaffected.
- **Expected effect.** Training stops favouring long-record cells and conditions with many replicates. Note: at m = 8,
  storage holds 19 of 27 training conditions, so storage keeps the larger share under this rule as well. A separate weight
  for storage against cycling is not proposed: there is no evidence for it, and ISU has no storage arm to pilot it on (see
  section 3).
- **Comparator parity.** The comparators are already cell-balanced; this rule brings every arm to the same per-condition
  rule.
- **Cost.** 0 extra fits; coder about 3 h (a weight vector in `Batch`, used in `fit_pinn`, `fit_hard`, `fit_data_only` and
  the symbolic refit, plus unit tests).
- **Risk.** It changes the optimisation of every neural arm after the pilots P4 and P5. The synthetic G0 recovery check
  (PC-1) and NC-1 must pass again at the candidate commit (they are freeze conditions anyway).
- **Touches.** The common recipe of PREREG 7 (D013 (d) lists lr, clip and warm-up; the weighting is new, so a decision row
  is needed). Not D017/D019.

### C4. Average the top-3 configurations of each search (rank 4)
- **What.** The final model of each tuned P-chain arm is the ensemble of its 3 best inner-CV configurations x 5 seeds. D\*
  and AG selection still use each candidate's best inner-CV score. A15 and G15 stay top-1, single-model (C1 reason).
- **Expected effect.** It reduces the selection noise of argmin over 20-40 trials scored on 8 conditions (ensemble selection:
  Caruana et al., ICML 2004; top-k ensembles in TabArena, arXiv 2506.16791, [A] in the knowledge base). The knowledge base
  warns that the benefit is inflated when it is judged on the same validation data. Here it would be judged only by the
  outer test, after the freeze, so it is a design choice, not a selection on validation data. Size unknown, smaller than C1.
- **Comparator parity.** Every tuned arm, including A9, A11 and A12.
- **Cost.** +10 refits per arm and cell, about 2.7 CPU-h over the grid and the random-subset rows. Coder about 3 h.
- **Risk.** More moving parts at the freeze. Run C4 only if C1 is adopted, since the two are the same mechanism.
- **Touches.** PREREG 7 budget rule and 8. Not D017/D019.

### C5. Second-order difference (P-spline) penalty on spline coefficients (rank 5)
- **What.** Replace the coefficient ridge `spline_l2` (shrinkage towards 0, `law.py` lines 146-147) by a second-difference
  penalty plus a small ridge, in every KAN and GAM edge of the law-based arms (A1, A2, A4/A5, A13, the A15/G15 parents and
  the calendar KAN). The tuned "l2" keeps its grid and becomes the roughness weight. P-splines: Eilers and Marx 1996,
  Statistical Science 11(2) (doi 10.1214/ss/1038425655, to verify on Crossref).
- **Expected effect.** At m = 8 each stress takes 2-4 distinct values. A ridge pulls the spline between those values towards
  zero, which is a bump in the log rate. A difference penalty interpolates smoothly, which also makes the A15 extraction
  easier. Speculation; not tested in P4 or P5 (both used the ridge).
- **Comparator parity.** Equal within the ladder (AG gets it), so the KAN-share term is not favoured. D\* keeps its own
  regularisers (GP kernel smoothness, LightGBM l2 and min-child).
- **Cost.** 0 fits; coder about 1.5 h (penalty and a unit test: zero penalty on a linear coefficient sequence).
- **Risk.** It changes the meaning of a tuned dimension in the 7.1 table (and `test_arm_table_matches_prereg_dimensions`).
  The BIC noise floor of the extraction (CHOICES 3.5) was not calibrated on ridge splines either way.
- **Touches.** PREREG 7.1 table text only. Not D017/D019.

### C6. Per-cell latent block: learned TAU and SIGMA with floors, and a converged window inversion (rank 6)
- **What.** (a) Replace the fixed TAU = 0.15 by a type-II MAP estimate per (fold, m), floored at 0.05: log TAU is learned
  jointly with a weak hyperprior, or it is set in a second pass from the sd of the fitted delta_c on training cells (the
  quantity already logged as a diagnostic in PREREG 9.9). Treat SIGMA the same way, with a floor. (b) Check convergence of
  the test-time inversion (`invert_pinn`: 200 Adam steps, lr 0.05, from zero). Log the final gradient norm and raise the
  steps equally for A1, A2 and A9 if any arm has not converged. (c) Optional: let A1 tune zdim in {1, 2}; A9 already tunes
  {1, 2, 3}. This adds a dimension, so only if the pilot shows a gain.
- **Expected effect.** At k = 2 the shrinkage of window-inferred offsets is set by the TAU/SIGMA ratio. Both values are
  nominal values from the synthetic pilots, not from data. The diagnostic flag (sd outside [0.5, 2] x 0.15) already
  anticipates a mismatch. Size unknown.
- **Comparator parity.** A10's per-cell factor uses "the same prior family as A1's delta_c" (PREREG 7.2), so A10 gets the
  same learned prior. A9's z scale is not identifiable (it is absorbed by the network weights), so there is nothing to
  learn for it. D\* learns from window features directly.
- **Cost.** 0-1 extra fit per fit (the two-pass variant doubles fit cost: about +16 CPU-h, so prefer the joint form).
  Coder about 3 h.
- **Risk.** z_c and delta_c can trade off and drive TAU to its floor. Unit test on synthetic data with a known offset sd.
- **Touches.** PREREG 7 ("prior sd TAU = 0.15 fixed"), sensitivity row 9.9(m), and the A10 prior (7.2). Not D017/D019.

### C7. Each arm's own default configuration as TPE trial 0 (rank 7)
- **What.** `study.enqueue_trial(default_hp(arm))` before the TPE run, inside the same N trials, for every tuned arm.
- **Expected effect.** It protects every arm against a search that never visits a reasonable configuration. Small.
- **Cost.** 0 CPU (inside N); coder 0.5 h.
- **Risk.** None material; `default_hp` is the middle of each grid, with no A1-specific tailoring.
- **Touches.** Nothing ruled.

### C8. Physics-transformed inputs for the stress map as a tuned option (rank 8)
- **What.** Add a categorical {raw, transformed}. The transformed set is (Arrhenius abscissa of T, SOC_mid, log DoD, log C_ch,
  log C_dch), as in `ParamMap.feats`, for the cyclic KAN and GAM of the law-based arms, and the same option for A9's
  stress input.
- **Expected effect.** D\* already has this option (PREREG 7.4, feature set {raw, pinn}), and A1 does not. With h = 1 and
  near-linear edges, the transformed set nests the Arrhenius and power-law form of semi-empirical models, which is a strong
  prior for scarce data. Speculation.
- **Comparator parity.** A9 must get the same option, otherwise P2 is confounded. D\* already has it.
- **Cost.** 0 extra fits, +1 tuned dimension (more search noise). Coder about 4 h, plus the method-architect, because the
  frozen symbolic library's abscissae (power or log on a positive physical abscissa, Arrhenius on T) interact with the
  transform, and the library hash changes.
- **Risk.** The highest of the list (A15 extraction and library hash), so last.
- **Touches.** The 7.1 spaces of six arms and 7.3 (library). Not D017/D019.

---

## 3. What must NOT be done
1. **No pilot that uses Samsung labels before `runs/prereg/FROZEN`, including "Samsung training folds".** Each cycling
   condition is outer-test in one Test B fold, the storage conditions are outer-test in S2, and the 35 C conditions are
   outer-test in Test C (`BLINDING_LOG.md` rule; PREREG 3.3(9)). A Samsung pilot may use identifiers and synthetic labels on
   the Samsung layout only. That checks mechanics, not effect size.
2. **No information from outside the 8 conditions at g1.** This includes: hyperparameters, TAU, backbone or edge families
   tuned at m = 32 and reused at m = 8 or 16; tuning at m = 8 scored on the other 24 conditions of the fold; and a "transfer"
   of the m = 32 optimum. Each would break the scarcity scenario and favour the law-based arms only. Every tuning and every
   estimated prior uses the thinned training side of its (fold, m).
3. **No collocation, twins or any training input at the held-out conditions' stress vectors** (transductive use of
   outer-test identifiers). It widens E4 and breaks the guard. Test C's 35 C twins are already stated and are not a precedent
   for Test B.
4. **No A1-only advantage.** No extra trials, inner folds, seeds, steps, ensembles or search dimensions for A1 that its
   comparators do not get. No new option for A1 without the matching option for A9. Do not tune F (width, depth) for A1
   while it stays fixed in A2-type arms. If F is opened, every F-based arm opens it equally.
5. **No weakening of D\*.** Do not drop A9 from D\* because C1 makes it stronger. Do not remove the feature or storage options,
   the monotone horizon constraint or the GP kernel choice. Do not narrow any comparator's space. Do not pick D\* or AG by
   anything other than inner CV.
6. **No change chosen by the A1-vs-D\* gap**, on ISU or anywhere else. The pilot's decision rules (section 4) use each arm's own
   error only. P6's A1-vs-D\* reading stays the non-binding signal to Shlok that J16 5.6 defines.
7. **Nothing after the first Samsung outer score.** No switching between ensemble and per-seed scoring, no second TPE seed
   used as a decision input (9.9(p) stays appendix only), no edge extension, no change of k, subsets, margins, rho_s0, w or
   blinding exclusions. Edge optima found in the confirmatory run go to the next version, never this one.
8. **No ISU outer-test fold in the pilot.** ISU is the fallback primary if Samsung is not parsed by 07 Nov 09:00.
9. **No ensemble for A15 or G15.** The approved sentences name a single closed-form law.

---

## 4. Pilot P6b: ISU training sides only, to decide C1 and C2 (decision rules fixed here, applied by script)

**Purpose.** Decide whether the ensemble endpoint (C1) and four inner folds at m = 8 (C2) are adopted. Run it together with
P6 (freeze condition C6); P6's 2-fold m = 8 runs serve as the "2 folds" arm.

**Design.**
- Data: ISU, `runs/splits/isu_testB.json` (hash checked before and after). For each of the 5 outer folds, the outer test
  conditions are removed before any feature, floor or model code runs (the enforcement of `code/pilots/p3_headroom.py`
  `main()`, with the same audit fields: intersection 0, `test_fold_scored: false`, split SHA-256).
- Pseudo-split inside each training side: pseudo-train = the nested max-min subset of 8 training conditions (selector of
  PREREG 4.1 on ISU coordinates, CHOICES 1.6). Pseudo-test = the fold's other training conditions. A condition can be
  pseudo-test in several folds: per fold values are reported, and a condition-level pooled value is the mean of its log
  ratios over the folds in which it is pseudo-test (as P3's pooled CI).
- Window: W = 2 weeks, the scarce analogue fixed in PREREG 3.4, for inner-CV scoring and pseudo-test.
- Arms: A1 (ISU form, no calendar term), A9, A11, A12 with the confirmatory spaces. N = 20 TPE trials (sampler seed =
  outer fold; tuning seed 1000 + fold); final refits seeds 0-4.
- Factor C2: inner_k in {2, 4}, same N and TPE seed, one selected configuration each.
- Factor C1: for each (arm, inner_k), pseudo-test scored (a) as the mean over seeds of the per-seed RMSE and (b) as the RMSE of
  the 5-seed mean forecast.
- Endpoint: PREREG 6 condition score (cell RMSE in pp, mean within condition, mean over conditions), log ratios per condition.

**Decision rules (fixed now; the script prints the verdict, no person chooses; nothing uses a cross-arm contrast):**
- **R1 (C1).** For a in {A1, A9}, with the 2-fold configuration: r_a = median over pooled pseudo-test conditions of
  ln(S_a,mean-of-seeds / S_a,ensemble). Each term is at least 0 by the triangle inequality. **Adopt C1 for every seeded
  P-chain arm iff max(r_A1, r_A9) >= ln(1.02).** Otherwise keep the current endpoint.
- **R2 (C2).** For each a in {A1, A9, A11, A12}: q_a = median over pooled pseudo-test conditions of ln(S_a,2-fold /
  S_a,4-fold), using the endpoint chosen by R1. **Adopt four inner folds at m = 8 for every tuned arm iff the median of the
  four q_a is > 0 and min_a q_a > -ln(1.05).** Otherwise keep 2 folds. m = 16 follows m = 8 if CPU allows; otherwise the
  disclosure of C2 applies.
- If P6b is not finished before the freeze, both rules default to "no change".
- **Reported, no decision:** A1 against the best of {A9, A11, A12} at m = 8 under each variant (P6's reading), per-fold
  values, selected configurations and grid-edge hits, seed SD, inversion gradient norms (C6 b).

**Cost (arithmetic from the build_v1 timing table, not measured on ISU).**
- A1: 20 trials x (2 + 4) fits x 5 folds = 600 fits x about 14.5 s = about 2.4 CPU-h.
- A9 about 0.45, A11 about 0.37, A12 about 0.05 CPU-h.
- Refits and pseudo-test inference about 0.4 CPU-h.
- Total about 3.7 CPU-h (about 2.5 marginal over P6), about 1.3 h wall on 3 single-thread processes, ceiling about 14 CPU-h.
- CPU only, `CUDA_VISIBLE_DEVICES=` as in P3.

**Optional third factor (+ about 1.5 CPU-h):** C3 (point-weighted vs condition-balanced loss) for A1 and A9, rule as R2.
Adopt only iff both q > 0.

**What the pilot cannot decide.** Anything about storage (ISU has none), 5-D stress sparsity (ISU has 3 inputs), or the size
of A1's g1 advantage on Samsung. C3 to C8 are therefore justified by the parity and endpoint arguments of section 2, not by
the pilot. Rank C5 to C8 as optional; drop them first if the freeze date is tight.

---

## 5. Unverified items
- Cawley and Talbot 2010 (JMLR 11), Caruana et al. 2004 (ICML), Eilers and Marx 1996 (doi 10.1214/ss/1038425655): identities
  known, not re-read here. The citation validator must check them before any of them enters the paper.
- The CPU figures assume confirmatory fit times like the synthetic Samsung-size timing. FB-8 measures the real ones.
- Whether `default_hp` (C7) yields a valid configuration for every arm at m = 8 (for example A12 min-child 32 with about
  29 cycling cells) must be checked by the coder; if not, clamp it inside the space.
