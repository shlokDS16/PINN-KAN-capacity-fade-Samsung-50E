# D021: per-edge cap on free coefficients of the frozen symbolic library ([ARCH: cap])

Author: method-architect, 2026-11-05. Status: proposal for red-team and judge; the designer fills PREREG_v4 7.3 item 1 and 17.3 from this file.
Reading: full text of `research/CONTRACT.md`, `code/pinnkan/symbolic.py`, `symbolic_library.json`, `code/tests/test_pk_v2_symbolic.py`, `code/pinnkan/synth.py`, `arms.SymbolicArm`, `runs/build_v2/{RESULT,CHOICES}.md`; PREREG_v4 7.3, 17.3 and the K-chain rows (grep plus the paragraphs read); D016 judge section 3 (full). `runs/prereg/subsets.json`: training identifiers only (design values of the 32 training conditions per fold). No Samsung label, outer-test datum or score was opened. CPU only (2 processes, 50 min). All numbers below are from `runs/D021_cap_synth/` (synthetic) or are counts of design identifiers.

## 1. Decision

**`max_coeffs_per_edge` = 2**, the same for A15 and G15, for the cyclic map and the calendar KAN, at every grid cell. Set in `code/pinnkan/symbolic_library.json`. Library hash (rule, cap-independent) `2bb5532ec941ae62542b894a671b7c56eb3d643a750386328047c4f50934abc4` (unchanged); sha256 of the library file with the cap, `45d171654e60e511b85e395b92d40e6eb1a3bde97c7faf171cc92c115a054efb` (the pin of PREREG 18 step 2b; recompute after any edit).

Consequence stated plainly: with the code's coefficient counts (zero 0; linear 2; log 2; quadratic, power, exponential, Arrhenius, hinge 3, each counting its additive constant), **cap 2 leaves {zero, linear, log} eligible on every edge.** The other five forms stay in the hashed library file but can never be selected. The extracted law is then a sum of effects that are each linear in the stress (rate exponential in the stress) or linear in its logarithm (rate a power law of the stress), with composition through the outer edge when h = 2. That is the standard semi-empirical form of a calendar plus cycle ageing law, and the sign of every effect is read off a slope.

**This decision has two costs that the designer and judge must accept or reverse** (section 6): (i) D016 judge 3.5, the check whether the calendar SOC slope changes sign above SOC 0.8, cannot be answered by the extracted law (no non-monotone form is eligible); (ii) the seven-family recovery unit test of PREREG 7.3 item 4 still runs, but at cap 3 as a test of the library functions, not at the pinned cap.

## 2. What the cap is (read from the code, not assumed)

`choose_family` drops a family iff `N_COEFS[f] > cap`. `N_COEFS` tops out at 3. So the cap is a three-way switch, not a dial:

| cap | eligible | note |
|---|---|---|
| 0 or 1 | zero only | every edge pruned; the law is a constant (verified by test and `edge_study.json`) |
| 2 | zero, linear, log | |
| 3, 4, 5, ... | the whole library | identical extraction (verified: family and theta equal in 120 of 120 pipeline fits and in every edge-study case; unit test) |

So "one neighbour on each side" of cap 2 is cap 1 (degenerate) and cap 3; of cap 3 it is cap 2 and cap 4 (identical to 3 by construction). A cap of 3 or more is "no cap": the preregistered safeguard would then rest on BIC and the ridge alone. That is the honest comparison, and it is why the study below compares cap 2 with cap 3.

## 3. Design arguments (no model fitted)

1. **The training design has three temperature levels.** In all five folds, at m = 32, 16 and 8, the training conditions have exactly 3 distinct temperatures (23, 35, 45 C; from `subsets.json`, identifiers only), with at least 2 conditions per level at m = 8. Other inputs: m = 32 has 14-18 distinct SOC_max, 10-11 DoD, 9-10 C_ch, 17-20 C_dch values; m = 8 has 4-5, 5-6, 4-6, 7-8. A temperature edge with k coefficients carries k - 1 identifiable shape parameters (the additive constant is confounded with the law's level). Three levels give two identifiable contrasts. A 3-coefficient form then interpolates the three level means with no residual degree of freedom, and the data cannot tell quadratic, exponential, hinge, Arrhenius and power apart. A numerical check (`edge_study.json`, `identifiability_3_levels`): for 400 arbitrary sets of three level means, the quadratic fits exactly in 400, exponential and Arrhenius in 137, hinge in 65; in 137 of 400 sets at least three different 3-coefficient forms fit exactly. Cap 2 leaves a slope and one residual degree of freedom on the temperature edge.
2. **BIC runs on the KAN's grid, not on the data.** The extraction scores families against the KAN edge on G = 101 points of the training hull; the number of conditions never enters. Between the data points the KAN edge is the spline's smoothness prior. Any form with enough shape freedom can follow that interpolation, and the 1 % floor `rms_tol_rel` is the only barrier. With 8 to 32 conditions the spline artefacts routinely exceed 1 % of an edge's range, so the floor does not stop the choice of a 3-coefficient form (edge study: a truly linear edge with a smooth 2 %-of-range perturbation is recovered as linear in 25-45 % of draws at cap 3 and in 100 % at 0.5 %; section 5 shows the same on the full pipeline).
3. **Parameter count against conditions.** At cap 3 the median extracted cyclic law has 18 coefficients for A15 h = 1 and 35 for h = 2 (G15: 15) from 32 training conditions; at m = 8 it has 17, 34 and 14.5 from 8. At cap 2 the counts are 12, 24 and 10. Both exceed 8 at g1; at m = 32 cap 2 stays below the 32 conditions for all three arms, cap 3 does not for h = 2 (35). (Coefficients are not all identifiable, which is argument 1; this is a count, not a degrees-of-freedom claim.)
4. **What cap 2 can and cannot represent on the 23-45 C hull.** The textbook Arrhenius effect on a log-rate (power with q = -1 in 1/T) is approximated by the log or linear form with a relative RMS error of 0.27 % of the edge range, below the 1 % floor; at cap 3 BIC itself already prefers the linear form for it (it selects linear at 0.54 % error). So for temperature the cap costs nothing the extraction can resolve. For genuinely curved edges the cost is real: noiseless quadratic with curvature ratio 0.3 loses 4.6 % of range, exponential with b = 1.5 loses 9.7 %, a hinge at mid-range 14.6 %. Those are the shapes that cap 2 cannot represent.
5. **Matched-pair symmetry.** The cap is per edge and the same for both arms, and the code path is one class; the cap cannot by itself favour A15 or G15. A15 with h = 2 has twice the edges of G15, so the total coefficient count differs by structure (printed beside K2, PREREG 7.3 item 2), which is unrelated to the cap.

## 4. Study (rule fixed and committed before it was run: `study_rule.md`, commit c0a9793)

Design: `synth.make_synthetic` kinds G0 (additive, linear in T, DoD, C_ch, C_dch plus a sin in SOC) and G2 (non-additive, with a hinge in C_ch and a DoD x SOC product); 40 cycling conditions with 3 temperature levels, 8 held out, 32 train (m = 32), m = 8 by the project's max-min selector; arms A15 h = 1, A15 h = 2, G15; one parent fit per arm and cell, then extraction and the end-to-end refit at cap 2 and cap 3, extraction only at cap 4; hyperparameters fixed at `default_hp`. Ten complete seed groups (seeds 0-9; seeds 10 and 11 were cut by the 50 min limit and are excluded by rule, the extra records are in the files). Metric E_law: centred RMS error of the fitted cyclic log-rate against the truth on 300 probe points, as a fraction of the truth range. Outputs: `runs/D021_cap_synth/pipeline_p0.jsonl`, `pipeline_p1.jsonl`, `decision.json`, `edge_study.json`; code `code/prereg/d021_{edge_study,cap_study,cap_decide}.py`.

| rule step | result |
|---|---|
| D0 cap 4 equals cap 3 | **true** in all 120 fits |
| D2 harm of cap 3, G0, m = 32 | mean E3 - E2 = **+0.0168**, 95 % one-sided upper bound **0.0210** > 0.02: **harmful** (lower bound 0.0121; cap 3 worse in 9 of 10 seeds) |
| D2 G2, m = 32 | mean +0.0059, upper bound 0.0094: not harmful (cap 3 worse in 8 of 10 seeds) |
| D3 verdict | **cap 2** (rule: harmful in at least one kind) |
| D4a m = 8 | G0: +0.0030, upper bound 0.0099, not harmful. G2: undefined, see below |
| D4b symmetry on G0, A15 h = 1 minus G15 | cap 2: +0.0225 (m = 32) and +0.0225 (m = 8): **flagged** (> 0.02). cap 3: +0.0143 and +0.0164: within |
| D4c false structure on G0 (a 3-coefficient form on an input whose truth is linear), A15 h = 1 and G15 pooled | cap 3 at m = 32: **37 of 40** edges for each arm; temperature edge 8 of 10 and 7 of 10. Cap 2: 0 of 40 by construction. False prune (zero chosen on a linear input): 0 in all settings |

Other reads of `decision.json` (descriptive): the refitted cap-2 law is closer to the truth than the KAN it was extracted from in every G0 and G2 cell at m = 32 (median E_law 0.045-0.084 against parent 0.078-0.102), and cap 3 is closer than the parent but less so; the median held-out forecast RMSE at m = 32 differs by 0.01-0.09 pp between the caps on G0 (cap 2 lower) and, on G2, is 0.14 and 0.16 pp lower at cap 3 for A15 (2.28 against 2.42 pp, h = 1; 2.26 against 2.42, h = 2) and equal for G15 (2.23 against 2.22); at m = 8 cap 3 has a heavier tail (A15 h = 2, G2: mean forecast RMSE 5.8 against 3.7 pp).

**Two things the rule did not anticipate, reported as found.**
- *The D2 margin is thin.* The verdict rests on an upper bound of 0.0210 against a threshold of 0.02. The point estimate (0.0168) and the false-structure rate (92 % against 0 %) point the same way and cap 3 is worse in 9 of 10 and 8 of 10 seeds, but a different bootstrap draw could flip the formal verdict. I did not adjust the rule after seeing the data.
- *Non-finite refits at cap 3.* Two of 120 cap-3 refits (G2, m = 8, A15 h = 2, seeds 3 and 6) returned a non-finite law (E_law NaN, so the D4a guard for G2 at m = 8 is undefined); there were none at cap 2. The exponential and Arrhenius forms are the likely cause (the code clamps the exponent at 20 and the refit can still blow up); I have not diagnosed it. It is a further stability argument for cap 2, not a verdict input.
- *Symmetry flag at cap 2.* On additive truth A15 h = 1 is 0.0225 of range worse than G15 after extraction at cap 2 (0.0143 at cap 3). The gap already exists in the parent networks (parent E_law A15 h = 1 minus G15: +0.0173 at m = 32, +0.0170 at m = 8, post hoc computation), so it is a property of the extra composition layer in a 26-condition fit, not of the cap: cap 2 adds 0.005, cap 3 removes 0.003. K2 compares A15 with G15, so a baseline handicap of A15 on additive truth is the conservative direction for the K+ claim.

## 5. Alternatives and why they lost

1. **Cap 3 (equal to no cap).** Keeps D016 3.5 and the full library. Loses because on synthetic data it is never better in extracted-law error at m = 32 (worse in 6 of 6 arm-by-kind means), picks a 3-coefficient form on 92 % of truly linear edges, cannot be identified on the 3-level temperature edge, had the only non-finite refits, and adds nothing the 23-45 C hull can resolve for temperature. Its one advantage is representational reach for genuinely curved edges (section 3 item 4), which the synthetic truths hardly contain (G0 is linear except a mild sin; G2 has one hinge whose threshold moves with temperature, so no single-edge form fits it).
2. **Cap 1 or 0.** Every edge pruned; the law is a constant. Not a candidate (tested).
3. **A cap that differs by layer or by input (for example 3 on the calendar SOC edge, 2 elsewhere).** Would keep D016 3.5 and respect the 3-level temperature edge. Not chosen because the frozen rule has one number and the brief fixes one cap; a per-layer cap changes the interface and the hashed rule and has not been tested here. It is the first thing to try if the judge refuses cost (i) of section 1 (section 6).
4. **A level-aware eligibility rule (a family needs more distinct training levels than coefficients).** Principled for the 3-level temperature edge and compatible with cap 3. Not chosen: it changes the frozen rule and the library hash, needs red-team review and a new test, and was not part of the brief.
5. **Keep cap 3 and rely on BIC and the ridge.** The study shows the BIC floor does not prevent false structure (92 %), so the safeguard is not effective at this sample size.

## 6. What a JES reviewer, the judge and the red team should know

- **Cost (i), D016 3.5.** With cap 2 the calendar SOC slope cannot change sign, so the statement "the slope changes sign above 0.8" can only be checked on the learned KAN partial dependence (A1 or the parent), as a descriptive observation, not on the closed-form law. The designer must either strike or reword D016 3.5, or reopen the cap (alternative 3).
- **Cost (ii), library reach.** PREREG 7.3 item 1 lists eight forms; at cap 2 five are unreachable. The paper must say that the library is the frozen superset and the cap restricts it to {zero, linear, log}; the designer should state the cap in 7.3 and not leave a reader to find it in the code.
- **Where the synthetic result may not transfer.** G0 and G2 are mild by construction; real ageing edges (a saturating DoD or C-rate effect, an SOC maximum) may be curved enough that cap 2 loses more than the synthetic study shows (edge study: 1.5 to 19 % of edge range for noiseless curved forms). K1 (A15 within 10 % of A1) is the claim at risk; its power depends on this. Nothing here is a Samsung result.
- **Calendar edges** were not scored in E_law (the metric is the cyclic surface); the cap applies to them too.
- **Test C** (35 C held out) leaves 2 temperature levels in training; any A15 or G15 on Test C has a temperature edge with a single contrast, which cap 2 fits exactly and cap 3 would not identify at all. Not scored here.
- **Seeds and hyperparameters.** One parent seed per design seed, hyperparameters at the grid middles, 10 replicates; the intervals are over design seeds. The tuned configuration of the real run may differ.
- **The run configuration does not yet pin the cap.** `run.py` and `guard.py` do not read `symbolic_library.json`; PREREG 18 step 2b requires the cap value and the file hash in the config hash. That wiring is outside this brief (RESULT.md already lists `guard.build_freeze_payload` additions as open).

## 7. Re-open if
(a) the judge refuses cost (i) (then alternative 3, a calendar-only cap of 3, needs a code change, a new hash and a rerun of this study on the calendar surface); (b) a replicate shows cap 4 != cap 3; (c) the library, the 1 % floor or the grid G changes; (d) the real training sets have fewer than 3 temperature levels for a scored arm; (e) a pilot on Samsung training sides shows that cap 2 leaves a training-side E_law-equivalent gap above 10 % of the KAN's range (a check that uses no outer-test datum).

## 8. Files
`debates/D021_cap/study_rule.md` (rule, committed first); `code/prereg/d021_edge_study.py`, `d021_cap_study.py`, `d021_cap_decide.py`; `runs/D021_cap_synth/{edge_study.json, pipeline_p0.jsonl, pipeline_p1.jsonl, decision.json, log_p*.txt, full_suite.txt}`; `code/pinnkan/symbolic_library.json` (cap 2); `code/tests/test_pk_v2_symbolic.py` (cap-unset tests now monkeypatch the file value; new tests pin the cap, the three-way switch and the file-cap default).
