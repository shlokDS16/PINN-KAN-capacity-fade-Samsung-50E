# D020 judge: pre-freeze strengthening of the confirmatory run (2026-11-05)

Role: judge. I proposed nothing in D020 and wrote none of the inputs (`01_mlexpert.md`, `turn06_response.md`, PREREG_v4,
D018 judge file).

**Reading.**
- Full text: `research/CONTRACT.md`; `debates/D020_strengthen/01_mlexpert.md`; `debates/codex_panel/turn06_response.md`;
  `debates/D018_test_rule/01_judge.md`.
- Partial: `runs/prereg/PREREG_v4.md` sections 3.4, 4, 4.1, 5, 6, 7 (budget rule, 7.1 table, 7.2), 8, 15, 16, 17.1 to 17.5;
  `research/DECISIONS.md` (format, D018, D019); `runs/build_v2/CHOICES.md` (tail, items 4 to 6);
  `code/pinnkan/tuning.py` (`inner_k_for_m`) and `code/pinnkan/run.py` lines 300 to 325 and 136 to 141.
- Not opened: any outer-test data, score or prediction, any Samsung label, `runs/pilot_P3` to `P5` files (I rely on the
  expert's quotation of them; I did not re-verify those quotes). No code was run or edited.

**Number sources.** Every number comes from the input files. Numbers labelled "my arithmetic" derive from them; thresholds
labelled "design choice" are set by this ruling and are not measured quantities (as in D018 section 3).

---

## 0. Verdict

**ACCEPT in part, REVISE in part.** I accept the opponent's REVISE on all three required changes.

| Item | Ruling |
|---|---|
| C1 five-seed ensemble | **Adopt modified.** Uniform deployment estimand for every seeded arm, frozen now, no pilot gate. K chain stays per-seed. |
| C2 four inner folds | **Adopt modified, conditional.** Decided by a revised P6b rule over six tuned arms; default is no change; development evidence only. |
| C3 condition-balanced loss | **Reject** for this confirmatory run. |
| P6b | **Runs**, narrowed to C2, six arms, new decision rule R2'. R1 is deleted. |
| PREREG section 7 tournament text | **Adopt** as a text correction (per (outer fold, m), on the thinned training side). |
| C4 to C8 | Not before me. **No change**; each may return only as its own decision row before the freeze. |

None of the rulings changes the D017/D019 outcome table, g1, the margins, rho_s0, w, the subsets, the Test B folds or the
section 11 text. Every ruling applies to every arm it can apply to, at every grid cell, in every downgrade row, NC-1/NC-2,
Test C and S2.

---

## 1. C1: score every seeded arm as a five-seed prediction ensemble

**Ruling: adopt modified. No pilot gate.**

**What is frozen.**
1. **Deployed predictor.** For every arm that has final-refit seeds 0-4 (A1, A2, A4/A5 and therefore AG, A9, A12, A13), the
   forecast that is scored is the mean of its five refit forecasts, per cell and per check-up, in retention space. Arms with no
   seed-dependent step (A10, R1, R2, the k = 0 references; A11 if the coder confirms it is deterministic) are unchanged: for them
   one fit is their own ensemble. If the coder finds any seed-dependent step in A11 or A10, that arm is ensembled the same way.
2. **Endpoint.** Cell RMSE of the ensemble forecast over the forecast set, mean within condition, then over conditions
   (PREREG 6 otherwise unchanged). This is the condition score S in every P-chain contrast, the secondary family, the ladder
   (9.6), the four downgrade rows, the lab-indicator re-runs, NC-1/NC-2, Test C, S2, Test A and the sensitivity rows.
3. **Non-finite forecasts.** The existing rule (a non-finite forecast is scored with the persistence error and counted) is
   applied seed-wise, before averaging: a diverged seed is replaced by the persistence forecast for that cell, and the count
   is reported per seed. The coder confirms that the present rule is already seed-wise; if it is not, this sentence governs.
4. **K chain stays single-model.** K1 and K2 use the per-seed score (mean over seeds of per-seed condition RMSE, the present
   rule) for A1, A15 and G15 alike. Reason: the approved sentences speak of one closed-form law, and Codex agrees. Within each
   chain every arm is defined by the same rule. The consequence that A1 has an ensemble score in the P chain and a per-seed
   score in the K chain is disclosed in one sentence, and both scores are reported for A1 in both chains.
5. **Per-seed scores stay as a descriptive row**, with the seed SD beside every score (PREREG 8). The per-seed P1 and P2
   counts are printed with the plain rule, labelled descriptive. They are **not** a new downgrade row: the closed list of 9.8
   rows (i)-(iv) belongs to D016/D017 and is unchanged.
6. **Tuning and selection are unchanged.** Each inner-CV trial is one fit (tuning seed 1000 + outer fold). D\* and AG are chosen
   by those inner-CV scores, the same for every arm. Codex asks for "the same definition in tuning/selection and final
   scoring". I rule that this is satisfied by the rule that every arm's selection score is one fit per trial and every arm's
   deployed predictor is its ensemble; scoring five fits per trial would multiply the tuning cost by five for the neural arms
   and is rejected. The mismatch is disclosed in Methods.

**Why the opponent's objection to R1 is upheld.** R1 adopted C1 if `max(r_A1, r_A9)` cleared a threshold. That is a favourable
selection among two arms, and it leaves A2, AG and A12 untested. The ensemble is an evaluation choice (what the deployed
predictor is), not a tuning choice, so it is fixed for all arms by principle:
- For each cell the RMSE of the mean forecast is at most the mean of the per-seed RMSEs (triangle inequality; expert section
  2, C1). No arm can be made worse by the rule, so it cannot be tuned to the outcome by choosing arms.
- It needs no Samsung information and no ISU result.

**Parity statement (printed in Methods).** The ensemble lowers each seeded arm's score by its own seed-variance share. Arms with
no seed variance gain nothing from it, which is a property of the model class. The wall clock and parameter count are reported
for the ensemble and for one fit (PREREG 6 secondary metrics), so a reader can see that A1, A9, AG and A12 pay five fits and
A11 and A10 pay one.

**Rejected alternatives.**
- *R1 pilot gate on A1 and A9* (the expert's proposal): favourable selection among two arms (opponent).
- *Ensemble for A1 and A9 only:* an A1-advantage the comparators do not get; forbidden by the expert's own section 3 rule 4.
- *Ensemble in the K chain:* an average of five laws is not one law; breaks the approved wording (Codex; expert section 3 rule 9).
- *Five-seed scoring inside tuning:* five times the tuning cost for the neural arms, no gain in what is being claimed.
- *Keep the per-seed rule:* leaves seed noise in S_A1,c, which lowers the effective correlation of the two arms' log condition
  errors and with it the power (expert section 1, on PREREG 1's rho dependence); the power values are the expert's quotation
  of PREREG 1, which I did not re-derive.

---

## 2. C2: four inner folds at m = 8

**Ruling: adopt modified, conditional on the result of P6b under rule R2' (section 4). Default: no change.**

**Reasoning.**
- The mismatch is real in structure: at m = 8 two inner folds train on 4 conditions and validate on 4, so each inner model is
  trained on half the target size (expert section 1). A change that repairs it is fair if it is the same for every tuned arm.
- But no number on file says what the change buys. The expert says so himself ("the size is unknown; the pilot decides"). Codex's
  caution stands: four folds put 2 conditions in each validation fold, which can replace one noisy regime with another.
- The expert's R2 is too weak to decide. It tests four arms, and adopts if the median of the four q values is above 0 and the
  minimum is above -ln(1.05). Under no effect the median of four noisy values is above 0 about half the time, so the rule would
  adopt a null change by chance. It also omits A2 and A4 (the second is AG at m < 32), which Codex flagged.

**What is frozen if adopted.**
- Inner folds for m in {8, 16} become 4, for every tuned arm and for the backbone tournament, with the same N, the same TPE
  seed and the same inner folds for every arm. m = 32 keeps 3. PREREG 4.1 has one rule for the two thinned cells ("2 for m in
  {8, 16}"), and I keep one rule for them, so m = 16 follows m = 8 and no new mixed regime between them is created. The pilot
  measures m = 8 only; this is disclosed.
- **The Partial plan overrides it.** If the freeze-commit timing run (FB-8) triggers the Partial plan (trials 20 to 10, inner
  folds at m = 32 from 3 to 2), inner folds at m in {8, 16} return to 2 for every arm. The Partial plan exists because CPU is
  short; four folds are not affordable then.
- The lead may also veto C2 on CPU grounds before the freeze and record it; the default is then 2. No other trigger can change
  it (in particular, nothing seen on Samsung).

**Cost.** Expert, arithmetic from `runs/build_v1/RESULT.md` section 2: about 9.3 CPU-h for the m = 8 core at N = 40, plus about
6.4 CPU-h for the random-subset rows; halved at N = 20; ceiling about 3.7 times; m = 16 adds a similar amount. For scale,
PREREG 16 gives the whole core as about 25 CPU-h expected and 85 at the ceiling. This cost is why the default is no change.

**Status of the evidence.** ISU is a development dataset (PREREG 3.4: "not blind"). The result is non-confirmatory and is never
cited as support for any Samsung claim. The paper states four inner folds as a design choice made after a development check;
it never says four folds are better.

**Rejected alternatives.**
- *Adopt unconditionally:* no measurement behind it, a real CPU cost, and Codex's noisy-validation risk is unquantified.
- *Reject outright:* leaves a known structural mismatch unmeasured when the measurement costs about 6 CPU-h (section 4).
- *The expert's R2 as written:* adopts a null change about half the time; omits A2 and A4 (above).
- *More trials N instead of more folds:* the expert notes that with noisy validation more trials deepen the winner's curse.
- *Four folds for A1 only or for the law-based arms only:* A1-only advantage; forbidden.

---

## 3. C3: condition-balanced data loss

**Ruling: reject for the confirmatory run.**

**Reasons.**
1. **It cannot be measured before the freeze where it matters.** The expert states that ISU has no storage arm and that "there is
   no evidence" for how storage should weigh against cycling. At m = 8 storage holds 19 of 27 training conditions, so a
   per-condition weight puts 19/27 of the weight on storage (my arithmetic from the expert's counts). Whether that helps the
   cycling endpoint is unknown, and a Samsung pilot is not allowed (section 5).
2. **The opponent's condition cannot be met uniformly.** Codex requires the weighting in every fitted objective, including A10.
   For A10 (least squares) and the sample weights of A12 it is simple. For A11, a GP, the expert's version is a sampling
   scheme ("draws rows per condition"), not a loss weight, so the parity is only nominal. The expert also states the
   comparators are already cell-balanced (A12 by weights, A11 by rows per cell), while A1, A2, A4/A5, A9, A13 are point-averaged.
   Equalising by moving the comparators to point averages would weaken D\*, which the expert's own rule 5 forbids.
3. **It changes the common optimiser recipe after pilots P4 and P5** (they ran on the per-point loss) and needs PC-1 and NC-1
   to pass again, in the window before the freeze, for a change whose sign is unknown.
4. **Direction of the present disparity is conservative.** If per-point averaging disadvantages the PINN arms relative to the
   cell-balanced learners, the claim is weakened, not inflated. The disparity is therefore disclosed, not removed.

**What goes into the paper instead.** One Limitations sentence, supplied by the designer in PREREG (action table): the gradient
arms average the data loss over points, A11 and A12 weight cells equally, A10 weights its least-squares points equally, and the
endpoint weights cells within a condition and conditions equally; no arm's loss is condition-balanced. C3 is a candidate for the
next version, not a result.

**Rejected alternatives.**
- *C3 in all objectives incl. A10 (Codex option 1):* see reasons 1 to 3.
- *C3 as the optional third pilot factor, adopt iff both q > 0 (expert):* pilot has no storage; rule is again a coin flip.
- *C3 for A1 and A9 only:* A1-only advantage.
- *Condition-balanced loss as a sensitivity row:* adds a full re-run for a row that carries no consequence; not added.

---

## 4. P6b

**Ruling: P6b runs, as a development check of C2 only. R1 and the optional C3 factor are deleted. Rule R2' replaces R2.**

**Status.** Development, non-confirmatory (Codex). ISU is not blind (PREREG 3.4). No Samsung label, identifier-based outer score or
ISU outer-test fold is read. If ISU later becomes primary (Samsung not parsed by 07 Nov 09:00), the paper discloses this
pilot as part of the ISU development exposure.

**Data and split.**
- ISU, `runs/splits/isu_testB.json`, hash checked before and after. For each of the 5 outer folds the outer-test conditions are
  removed before any feature, floor or model code runs, with the audit fields of `code/pilots/p3_headroom.py main()`
  (intersection 0, `test_fold_scored: false`, split SHA-256).
- Pseudo-train: the nested max-min subset of 8 of the fold's training conditions (selector of PREREG 4.1 on ISU coordinates,
  CHOICES 1.6). Pseudo-test: the fold's other training conditions. A condition may be pseudo-test in several folds; the pooled
  per-condition value is the mean of its log ratios over the folds in which it is pseudo-test.
- Window W = 2 weeks (the scarce analogue fixed in PREREG 3.4), for inner-CV scoring and for pseudo-test.

**Arms (all six must run).** A1 (ISU form), A2, A4 (= AG at m < 32), A9, A11, A12, each with its confirmatory space. A10 has no
hyperparameters. A13 (storage removal), A15 and G15 cannot be piloted on ISU (no storage; A15/G15 at g1 are descriptive) and
follow the A1 and A4 result. N = 20 TPE trials (sampler seed = outer fold; tuning seed 1000 + fold); final refits seeds 0-4;
`inner_k` in {2, 4}, same N and TPE seed; the backbone tournament also takes `inner_k`. Endpoint: the ensemble score of section 1
for every arm. If any of the six arms cannot run on ISU in time, the default (no change) applies; no arm is dropped from the rule.

**Decision rule R2' (fixed here; the script prints the verdict, no person chooses).**
- For each arm a: q_a = median over the pooled pseudo-test conditions of ln(S_a,2-fold / S_a,4-fold).
- **Adopt four inner folds for m in {8, 16}, for every tuned arm, iff q_a > 0 for at least 5 of the 6 arms AND min_a q_a >
  -ln(1.02).** Otherwise keep 2.
- Both thresholds are design choices of this ruling. Under no effect, at least 5 of 6 positive has probability 7/64 = 0.11 (my
  arithmetic, fair-coin signs); the 2 % floor bounds the loss any one arm may take.
- Not filed with its hash before the freeze commit: no change.
- Nothing in the rule uses an A1-versus-D\* contrast, and no number from Samsung.

**Reported, no decision.** Per-fold values; selected configurations and grid-edge hits for each arm and variant; seed SD and the
descriptive share of seed variance (per-seed against ensemble score, all arms); A1 against the best of {A9, A11, A12} under each
variant (the P6 reading of J16 5.6, non-binding signal to Shlok); final gradient norm of the test-time inversion of A1, A2 and A9
at k = 2 and the prediction spread across three random initialisations (answers Codex's inversion-convergence audit as a
diagnostic). **No rule is attached to the inversion audit.** If it shows non-convergence in some arm, the fix (more steps or
starts, equal for every affected arm) needs its own decision row before the freeze; nothing is changed by default.

**Cost (my arithmetic from the expert's fit counts and the `build_v1` timing table).**
- Expert: A1 600 fits x 14.5 s = 2.4 CPU-h; A9 0.45; A11 0.37; A12 0.05; refits and pseudo-test inference 0.4; subtotal 3.7.
- Added by this ruling: A4 600 x 10.6 s = 1.77 CPU-h; A2 600 x 2.5 s = 0.42 CPU-h.
- Total about 6 CPU-h expected (about 2 h wall on 3 single-thread processes); ceiling about 22 CPU-h using the expert's factor of
  3.7 (about 7 h wall). CPU only, `CUDA_VISIBLE_DEVICES=` empty as in P3. The CPU figures are not ISU measurements.
- Output files: `runs/pilot_P6b/RESULT.md`, `runs/pilot_P6b/decision.json` (the verdict, the q_a values, script and split hashes,
  start and end time), `runs/pilot_P6b/per_condition.csv`.
- The script and rule R2' are committed **before** the first fit runs; the commit hash goes into `decision.json`.

**What the pilot cannot decide (stated in the result file):** storage, 5-D stress sparsity (ISU has 3 inputs), the size of A1's
advantage on Samsung, and anything about C1 or C3.

---

## 5. Agreement with the expert's blinding correction

I adopt expert section 3 item 1: **no pilot that uses Samsung labels before `runs/prereg/FROZEN`**, including "Samsung training
folds". Every cycling condition is outer-test in one Test B fold, and the storage and 35 C conditions are outer-test in S2 and Test C
(BLINDING_LOG rule; PREREG 3.3(9), as quoted by the expert). A Samsung run may use identifiers and synthetic labels only
(mechanics, not effect size). I also adopt items 2 to 9 of expert section 3: nothing from outside the 8 conditions, no
transductive inputs, no A1-only options, no weakening of D\*, no change chosen by the A1-versus-D\* gap, nothing after the first
Samsung outer score, no ISU outer-test fold in the pilot, no ensemble for A15/G15.

---

## 6. PREREG section 7 text fix: the backbone tournament

**Ruling: adopt.** PREREG 7 says the tournament is chosen "once per outer fold". `run.py` runs it on the training side of each
(fold, m) (`backbone_tournament(train, ...)`, with `train` the thinned side from the subset selector). The code is the correct
reading, because a tournament run at m = 32 and reused at m = 8 would leak 24 extra conditions into the law-based arms only
(expert section 1).

**New text:** "chosen once per (outer fold, m) by a tournament on that cell's thinned training conditions only, with the same inner
folds as the tuned arms of that cell, at default settings, and shared by all law-based arms of that cell. A result from a larger
m is never reused."

**The expert's optional h = 1 in the tournament at m < 32: rejected.** The tournament's `TOURNAMENT_HP` (h = 4) is a default that
was not part of any pilot reading; changing it is an unmeasured change to the arms' backbone choice and not needed to remove the
leak. It stays as is.

---

## 7. C4 to C8 (not before me)

No ruling was requested on C4 to C8 and none is made. They are **not adopted**: the status quo stands. Notes for whoever brings
them back (each only as its own decision row before the freeze, with the same parity and pre-freeze conditions):
- C4 (top-3 configurations) depends on C1 and adds about 2.7 CPU-h (expert).
- C5, C8 change the 7.1 spaces or the frozen library hash.
- C6 changes TAU/SIGMA fixed in PREREG 7; C6(b), the convergence check, is now a reported diagnostic (section 4).
- C7 (default configuration as trial 0) is small; if wanted, the coder first checks that `default_hp` is valid for every arm at
  m = 8 (expert section 5, last item).

---

## 8. Re-open conditions

D020 is re-opened if:
- any Samsung outer score is computed before `runs/prereg/FROZEN`;
- the coder finds that the ensemble endpoint cannot be applied seed-wise as in section 1 item 3, or that NC-1 invariance fails
  with it;
- the P6b script is changed after its first fit, or its `decision.json` is edited by hand;
- the Partial plan is triggered (C2 reverts to 2 folds by rule; no re-opening needed, recorded in the freeze row);
- Shlok asks for a different reading of "best outcome" (for example a change that is not applied to every comparator).

These do not re-open it: a P6b result of "no change"; a large or small seed-variance share; an unfinished P6b (default applies).

---

## Actions

| # | Owner | What | File |
|---|---|---|---|
| A1 | experiment-designer | PREREG_v4: (a) sections 6 and 8: endpoint = ensemble score for all seeded arms, per-seed for K1/K2, per-seed row descriptive, non-finite rule seed-wise, wording of section 1 items 1 to 6; (b) section 7: tournament text of section 6 above; (c) section 4.1 and the 7 budget rule: "inner folds 2 for m in {8, 16}, 3 for m = 32, unless `runs/pilot_P6b/decision.json` says adopt, then 4 for m in {8, 16}; the Partial plan returns them to 2"; (d) new freeze condition C25: P6b filed with hash, or default stated; (e) Limitations/Methods sentences: loss-weighting disparity (section 3), ensemble cost and selection mismatch (section 1 items 4 and 6), ISU development status; (f) change-log row; section 11 byte-identical (C21). | `runs/prereg/PREREG_v4.md` (or v4.1) |
| A2 | statistician | Re-sign sections 6 and 8 under the ensemble endpoint; confirm the power paragraph is unchanged in form (no re-simulation needed: the endpoint changes the arms' error, not the test); confirm item (f) inner-CV estimates are single-fit scores by design. | `runs/prereg/stats_sim_v4/` note; PREREG 17.3 |
| A3 | implementer (coder, `runs/build_v2`) | `metrics.py`: add `ensemble_condition_scores` (ensemble of the five refit forecasts, seed-wise non-finite substitution) next to `seed_condition_scores`, which stays. `run.py` ~line 404 and `predictions.csv`: write both. `stats_v4.py`: P1, P2, P3, secondary, ladder, downgrade rows, Test C/S2, NC-2 read ensemble scores; K1/K2 read per-seed; print per-seed descriptive row. Config field `endpoint: ensemble` in the config hash. Unit tests: ensemble <= per-seed mean cell by cell; equal for a one-seed or deterministic arm; NC-1 invariance with the ensemble; non-finite seed substitution. Confirm A11 and A10 are deterministic. | `code/pinnkan/metrics.py`, `run.py`, `stats_v4.py`, `code/tests/` |
| A4 | implementer | `tuning.inner_k_for_m` reads a config field (default 2 for m in {8, 16}; 4 only if `decision.json` says adopt; Partial plan forces 2); the tournament inherits it. Unit test for each branch. Do not implement C3 to C8. | `code/pinnkan/tuning.py`, `run.py`, `code/tests/` |
| A5 | implementer | P6b script and runner: arms A1, A2, A4, A9, A11, A12; ISU training sides only; guard fields as section 4; rule R2' exactly as written, printing the verdict and writing `decision.json` with hashes and the script commit. Commit the script before the first fit. | `code/pilots/p6b_inner_folds.py`; `runs/pilot_P6b/{RESULT.md,decision.json,per_condition.csv}` |
| A6 | gate auditor | At the freeze: verify A1 to A5 on disk; check that the P6b script commit precedes its first fit and that `decision.json` matches the rule; add the C25 tick; check C21. Verify section 11 is unchanged. | `research/audits/`; PREREG 17.2 |
| A7 | lead | Tell Shlok in one message: the ensemble endpoint is fixed for all seeded arms; four inner folds are conditional on a development check; the condition-balanced loss is dropped; the K chain stays single-model. Schedule P6b (CPU only, 3 processes, about 2 h wall expected). | `research/progress.md` |
| A8 | paper writer | Methods wording only after A1 lands: ensemble definition and its parity statement; inner-fold sentence; loss-weighting Limitations sentence. No sentence says four folds or ensembles are better. | `paper/draft/` |

Decision row D020 appended to `research/DECISIONS.md`.
