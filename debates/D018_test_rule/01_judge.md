# D018 judge: confirmatory test rule after the size simulation failed (2026-11-05)

Role: judge and gate auditor for this decision. I proposed nothing in D018. I did not write the statistician's RESULT, the Codex
response, PREREG_v4, the D016 judge file or the novelty re-check.

**Reading.**
- Full text: `research/CONTRACT.md`; `debates/D018_test_rule/00_index.md`; `runs/prereg/stats_sim_v4/RESULT.md` (all sections);
  `debates/codex_panel/turn05_response.md`; `debates/D016_roles/02_judge.md` (all); `debates/D016_roles/03_novelty_recheck.md` (all);
  `research/DECISIONS.md` (format and D016-D017).
- Partial: `runs/prereg/PREREG_v4.md` sections 1-2, 3.4, 4, 4.1, 9, 10, 11 (reading note), 12, 17.2, 21 and 22.
- FT-partial: Stroebl et al., JES 142, 119552 (`refs/fulltext/ft_stroebl2025_OED_JES142_119552.txt`). I read the highlights, the
  start of sections 1 and 2, all of 4.2 with Table 1, and all of 5, and grepped the whole file for learned-model, forecast and
  learning-curve terms.
- FT-partial: Zhang et al., JES 182, 125097 (`refs/fulltext/ft_zhang2026_JES182_125097.txt`). I read the highlights, the section
  list and the split paragraph (3.1), and grepped the whole file.
- Blinding check: `runs/prereg/BLINDING_LOG.md` header and rows, and the metadata of `runs/build_v1_timing_samsung_B0_blinded`
  (`"blinded": true`, "no scoring, no predictions"). No `SCORED.jsonl` exists under `runs/`.

**No outer-test data, score or prediction was opened.**

**Checks I ran.**
- I recomputed the Beta-binomial critical counts in pure Python, from the formula of RESULT 4.4 (no data). The counts and sizes
  for rho_s0 in {0, 0.01, 0.02, 0.03, 0.05} and every level in that table match RESULT 4.4 exactly.
- I ran `code/tests/test_graph_test.py`: 12 passed.

**Number sources.** Every number below comes from the input files. The exceptions are labelled "my arithmetic" and derive from
those numbers.

---

## 0. Verdict

**ACCEPT the fallback, with revisions.** I accept the opponent's REVISE on all three of its required changes, with the
modifications stated below.

1. **Estimand.** Labs are **fixed strata**. Each held-out condition has equal weight, so the implied lab weights are the Test B
   majority-lab counts: HM 17, INT 19, SIE 4 of 40. Every gated contrast is also reported per lab. Nothing is claimed about new
   labs, and nothing is claimed about temperature alone.
2. **Test.** The confirmatory test for every sign test on the Test B conditions is the **Beta-binomial design-effect sign test
   with a fixed rho_s0 = 0.03**. The table below gives the positives needed out of 40.

   | Local level | Positives needed (of 40) |
   |---|---|
   | 0.005 | 33 |
   | 0.00625 | 32 |
   | 0.00833 | 32 |
   | 0.0125 | 31 |
   | 0.025 | 30 |

   The test is named **assumption-based**: it is valid if the average pairwise sign correlation is at most 0.03. It is never
   called exact or distribution-free. The plain exact test becomes a descriptive "independent-conditions" row. A dependence
   sensitivity row (rho_s0 in {0, 0.01, 0.02, 0.03, 0.05}) and the item (f) training-side dependence estimate are reported. Neither
   changes a tier.
   - **Pre-score approval by the gate auditor (D016 section 2 (a); PREREG_v4 9.3 and 17.2 C2) is hereby given for this rule.**
3. **Graph weights.** The current 1/2-1/2 split stays the default. It can be replaced by one pre-identified alternative,
   **w = 0.78 on P1N and 0.22 on K1**, through one simulation whose decision rule is fixed in section 3. Margins and g1 are
   unchanged.
4. **GAP-1 ("most").** I confirm the opponent's rule, changed to a per-condition paired contrast tested with the fallback. If e1 is
   reached but "most" fails, no approved clause fits. The added clause e1', built only from e1's own words, needs **Shlok's
   approval**. Until then, this is a freeze condition. No approved word changes.
5. **GAP-2 to GAP-11.** All accepted. GAP-2, GAP-4, GAP-5 and GAP-7 are accepted with specifications (section 5).
6. **Novelty.** The "first" scope of `03_novelty_recheck.md` section 3 is adopted. The Stroebl JES 142 and Zhang JES 182 full texts
   (partial reading) trigger neither the D016 re-open condition nor any change to titles or abstract claim sentences.
   - The abstract carries **no** novelty sentence until conditions (a)-(d) are all met.
   - The Introduction presents data efficiency and the ablation ladder as extensions of named prior work, not as new questions.

---

## 1. Estimand

**Ruling.** Labs are fixed design strata.
- **Estimand.** The median, over the 40 held-out Test B cycling conditions of this campaign, of the paired condition log ratio
  L_c. Every condition has equal weight (PREREG_v4 9.1, unchanged).
- **Lab weights.** The implied lab weights are the majority-lab counts HM 17, INT 19 and SIE 4 (RESULT section 2). The 3
  mixed-lab conditions are assigned to their majority lab. These weights are fixed now from identifiers. They are not chosen
  after scoring.
- **Lab-specific reporting.** For every gated and secondary contrast at g1 and g4, the Results table reports for each lab: n, the
  positive count, the median L and the order-statistic interval. Where no pair of order statistics attains the level, the
  labelled range is used (PREREG_v4 9.7 rule; this applies to SIE, n = 4). These rows are descriptive.
- **What is claimed.** Performance on held-out cycling conditions of one cell type in these three laboratories, which is the scope
  wording already fixed in PREREG_v4 section 1. Not claimed:
  - generalisation to other laboratories;
  - a random-lab variance;
  - any temperature effect separated from lab, since 35 C is all INT (J16 3.7).

**Reasons.**
- There are three labs, and they were not sampled from any population.
- Temperature is partly aliased with lab.
- A random-effect variance estimated from three clusters has no support. Both the opponent (section 1) and the statistician
  (RESULT 10.3) say the designer must pick the target. The approved scope words already describe fixed labs.

**Fixed labs do not remove fold dependence.** With fixed lab offsets, the plain test still has a size ratio of 1.83 / 1.72 at
intra-fold 0.10 (lab share 0.1; RESULT 4.3). Section 2 therefore keeps a dependence allowance.

**Rejected alternatives.**
- *Labs as a random effect.* This implies an inference about new labs that three clusters cannot support, and it cannot separate
  temperature from lab.
- *Equal lab weights (1/3 each) as the primary estimand.*
  - It gives a third of the weight to the 4 SIE conditions, which makes the estimand noisy.
  - It departs from the median-condition estimand of D012.
  - It is kept instead as the definition of the lab-stratified downgrade row (GAP-4, section 5), where it can only lower a tier.
- *Lab-stratified exact sign test as the primary test.* Fold-shared dependence remains, and the SIE stratum is too small for a
  separate test (opponent, section 2).

---

## 2. The confirmatory test

### 2.1 Frozen rule

**Test.** For a contrast with n conditions and margin m, let X be the number of conditions with L_c > m (ties are not positive).
Under H0, X is Beta-binomial(n; a = b = (1/rho_s0 - 1)/2) with **rho_s0 = 0.03** (a = b = 16.17; design effect 2.17). The node is
rejected at local level alpha iff P(BetaBin >= X) <= alpha. No random numbers are used.

**Critical counts at n = 40** (RESULT 4.4 and 9 [SIM: a]; recomputed by me and identical):

| Local level | Use | Positives needed | Size under the BetaBin null |
|---|---|---|---|
| 0.005 | Holm 1/5 | 33 | n/a |
| 0.00625 | Holm 1/4 | 32 | n/a |
| 0.00833 | Holm 1/3 | 32 | n/a |
| 0.0125 | graph, one chain | 31 | 0.0106 |
| 0.025 | graph, both chains; reverse S; last Holm step | 30 | 0.0194 |

**Where the rule applies.** It applies to every sign test on the Test B conditions that carries a tier word, a safety finding, a
wording consequence or a downgrade:
- graph nodes P1N, P1S, P2, P3, K1, K2N and K2S;
- P1-rev and K2-rev (0.025: 30);
- the five secondary tests and their reverse-S tests at the slot level;
- **NC-2**: 30 of 40, in place of the 27 in PREREG_v4 section 10. Its conditions share the same fold fits, so 9.3's rule "replaces
  the sign test for the affected contrasts" covers it;
- the GAP-1 test (section 4);
- the sign-test downgrade rows (ii)-(iv) of 9.8, each at the contrast's final local level;
- K1's tier S, which stays unadjusted and descriptive.

Test C and S2 sign tests stay plain exact and labelled descriptive, as now.

**Reduced n** (blinding exclusions, 3.3(11)): the same rule at the reduced n. The statistician tabulates the counts before the
freeze. The simulation covered n = 40 only, and this is disclosed.

**Intervals.**
- The simultaneous 1 - 0.05/9 interval uses the fallback rank 8, [L(8), L(33)] (RESULT 3 and 9 [SIM: e]).
- The unadjusted 95 % interval in the abstract sentence uses the fallback rank from the same arithmetic. *My arithmetic* gives
  rank 11, [L(11), L(30)], with coverage 1 - 2 x 0.0194, from the 0.0194 tail at 30 in RESULT 4.4. The statistician confirms this
  in the tables of action A3.

**Wording in the paper.** The test is called "a sign test with a fixed design effect (assumed average pairwise sign correlation
at most 0.03)". It is never called "exact" without that qualifier, and never called distribution-free.

### 2.2 What the plain exact test becomes

It becomes a **descriptive "independent-conditions" row** beside every gated and secondary contrast: positives, plain exact p and
plain tier. It never sets a state or an abstract tier, and it cannot raise a tier. The abstract follows the fallback tier with no
choice (RESULT 4.4, "Cost").

### 2.3 Reported dependence evidence (no consequence for any tier)

- **(i) Dependence sensitivity row.** The tier of each gated contrast at rho_s0 in {0, 0.01, 0.02, 0.03, 0.05}, using the counts
  of RESULT 4.4. The Results add one fixed sentence: "The [tier] holds for an assumed average sign correlation up to [largest
  rho_s0 on this grid at which it holds]."
- **(ii) Item (f) on the Samsung training sides.** The `item_f_rho_report` estimates (intra-fold and intra-lab correlation of the
  signs, from inner-CV training-side scores only) are written to the run directory and hashed **before any outer score is
  computed**. The statistics step refuses to run if the file is missing or written later.
  - It also reports a one-sided upper bound, whose estimator is defined in code before the freeze.
  - Fixed disclosure: if the intra-fold point estimate exceeds 0.03, Limitations carries the sentence "The training-side estimate
    of the sign correlation exceeded the value assumed by the test; the confirmatory tiers rest on that assumption."
  - Nothing changes the critical counts after the freeze.

### 2.4 Why rho_s0 = 0.03, and why not each alternative

**Why 0.03.**
- Region R4 (intra-fold <= 0.10, random intra-lab <= 0.05) is the widest region in which a grid value keeps every simulated ratio
  below 1.2. At 0.03 the worst ratio is 0.88 / 0.79 over all nine cells, P3 and three shapes (RESULT 4.4).
- At the R4 corner the graph's FWER is at most 0.0159 (RESULT 7).
- Under the fixed-lab estimand of section 1, R4's random-lab component is not the target. I still keep 0.03 for three reasons:
  - The fold bound of 0.10 is a judgement, not a measurement. The only data anchor, SNL, gives an ICC of 0.15 with a 90 %
    permutation range of -0.14 to 0.25, which cannot tell 0 from 0.2 (RESULT 4.5).
  - Lab-by-fold variation of the fitted laws was not simulated. It depends on which training conditions a fold holds, so it is not
    one of the fixed offsets, and it inflates the variance of the count the way a random lab effect does.
  - With fixed lab offsets, 0.03 is conservative (ratios 0.01-0.51, RESULT 4.4). This leaves room for fold correlation above
    0.10.

**Cost of 0.03.** This is stated to Shlok (action A5) and printed in the power paragraph.
- Under independence the size is 0.0003 / 0.0011.
- The 80 %-power gain of P1S at g1 rises to 0.212 (ISU-like skew) to 0.253 (normal) at rho 0.75. The plain test needs 0.166 to
  0.198.
- At a true 20 % reduction, P1S power is 0.71.
- The P chain through P3 has probability 0.36 when the K chain never rejects (RESULT 5.1, 5.4, 9 [SIM: b]).
- In short: the 17-22 % that Shlok was told before D017 is now 21-25 % at rho 0.75. P0, or P+ with clause e2 or e3, is a likely
  outcome unless the true gain is near 25 % (P1S power 0.96).

**Rejected alternatives.**
- *Plain exact sign test as the confirmatory test.*
  - It fails D016's 1.2 x nominal criterion from intra-fold 0.03-0.05 or random intra-lab 0.015-0.023 (RESULT 4.1).
  - The graph FWER is 0.0303 at intra-fold 0.05 and 0.0877 at the R4 corner (RESULT 7).
  - Fixed labs do not rescue it (1.83 / 1.72 at intra-fold 0.10, RESULT 4.3).
  - PREREG_v4 9.3 already fixes that the fallback replaces it once the criterion is exceeded.
- *rho_s0 = 0.02 under fixed labs.*
  - It is valid on R3 (worst 1.03 / 0.92) and with fixed lab offsets up to intra-fold 0.10.
  - At the R4 corner it fails (worst 1.59 / 1.36; graph maximum FWER 0.0299, with 33 of 72 configurations above 0.025 + 2 SE,
    RESULT 7).
  - Its validity would rest entirely on the unmeasured fold bound and on there being no lab-by-fold component.
  - Its gain is modest: P1S power 0.82 against 0.71 at r = 0.20, and an 80 %-power gain of 0.197 against 0.212 (RESULT 5.1).
  - It stays visible as a column of the sensitivity row (2.3 (i)).
- *Training-side upper-bound rule: rho_s0 = max(floor, one-sided upper bound from inner-CV scores).*
  - **Few clusters.** Inner CV has 2 folds (m in {8, 16}) or 3 (m = 32) per outer fold, and each condition sits in four of the
    five training sides, so the estimates are few and not independent.
  - **Estimation fails here.** RESULT 4.4 shows that a design effect estimated from five folds is liberal (normal reference, up
    to 3.4 x nominal) or vacuous (t4 reference). With a floor of 2 it "adds nothing over a fixed value".
  - **Different structure.** Inner-CV dependence is not outer-test dependence. The opponent concedes this.
  - **Conflicts with D016.** D016 item (f) fixed that "no rule changes with it".
  - **Moving count.** The critical count would be unknown at the freeze.
  - **Same assumption, less power.** With a floor of 0.03 it can only lower power, while validity rests on the same assumption.
  - It is kept as reported evidence (2.3 (ii)), which is what the opponent's required change 2 asks: "report its dependence
    sensitivity".
- *Fold-blocked permutation, cluster bootstrap, mixed model.*
  - With 5 folds the smallest permutation p is 1/32 = 0.031, so the test cannot reject at 0.025 (RESULT 4.4).
  - Five folds or three labs give no usable bootstrap coverage.
  - A mixed model would be model-dependent with so few clusters (opponent, section 2).
- *Relaxing the margins or moving g1 to regain power.* Rejected, as the opponent says. It would change the question after seeing
  the power.

### 2.5 Gate-auditor pre-score approval

**Given** for the rule of 2.1-2.3: rho_s0 = 0.03 fixed, the counts above, and the scope of application.

| Criterion | Status | Evidence |
|---|---|---|
| Fallback specified with a deterministic rule | met | RESULT 4.4, 9 [SIM: a] |
| Fallback size <= 1.2 x nominal on the stated region (R4), all cells and P3 | met (simulation) | RESULT 4.4 table "Worst ratio", 0.88 / 0.79 |
| Graph FWER <= 0.025 with the fallback at the R4 corner | met (simulation) | RESULT 7, `d_fwer.csv` row fold10_lab05_fb0.03 (maximum 0.0159) |
| Critical counts correct | met | my recomputation, identical to RESULT 4.4 |
| Graph implementation tested | met | `code/tests/test_graph_test.py`, 12 passed (run by me) |
| No Samsung outer score exists | met | BLINDING_LOG (exposures are raw check-up values, not scores); timing run `blinded: true`, "no scoring, no predictions"; no `SCORED.jsonl` under `runs/` |

Limits of this approval:
- It covers the C2 sub-item "pre-set fallback approved" only. **C2 as a whole is not ticked.** That waits on the statistician's
  additions from this ruling (A2, A3) and on the PREREG text (A1).
- The approval lapses if any Samsung outer score is computed before `runs/prereg/FROZEN` (stop rule 7).

---

## 3. Graph weights

**Ruling.** The default stays at 1/2-1/2. One alternative is simulated, and the choice follows a rule fixed now.

**Why one alternative only (discreteness; my arithmetic from RESULT 4.4).**
- Under rho_s0 = 0.03, P(BetaBin >= 30) = 0.0194 (RESULT 4.4). P(BetaBin >= 32) = 0.00535 is my recomputation; RESULT only bounds
  it between 0.005 and 0.00625.
- P1's count falls from 31 to 30 only when its local level is at least 0.0194, that is, w >= 0.775.
- K1 needs 32, not 33, as long as its level is at least 0.00535, that is, w <= 0.786.
- Hence:
  - any w in (1/2, 0.775) keeps P at 31 and raises K to 32, so it is strictly dominated (this covers 2/3 and 3/4);
  - any w above 0.786 raises K to 33 for no gain on P;
  - the fixed sequence (w = 1) gives P nothing beyond 30 and leaves K untested unless P3 is rejected.
- **The only non-dominated alternative is w = 0.78.** P1N then has local level 0.0195 (30 of 40) and K1 has 0.0055 (32 of 40). The
  hand-over edges are unchanged.

**What is already known.** At w = 0.78 the P chain uses 30 positives at every node, whatever K does. Its probabilities are
therefore the "K_first" rows of RESULT 5.4 (rho 0.75, r1 0.20, r2 0.15, r4 0.05, corr(g1,g4) 0.6):

| Setting | P chain through P3, current weights (K never) | P chain through P3, w = 0.78 (K_first rows) |
|---|---|---|
| No clustering | 0.36 (P1N/P1S 0.71, P2 0.70) | 0.53 (0.82 / 0.82) |
| Intra-fold 0.10, intra-lab 0.05 | 0.36 (0.67 / 0.65) | 0.49 (0.76 / 0.75) |

The unknown is the K chain at 32 positives when P does not complete. With the current weights, K1 under the fallback has power
0.74 (rho 0.95) and 0.33 (rho 0.90) when P never completes, and 0.85 / 0.46 when P completes first (RESULT 6, fallback table).

**Simulation the statistician must run** (before the freeze; file `runs/prereg/stats_sim_v4/g_weights.csv` and
`RESULT_weights.md`; code in `sim_v4.py` as item `g`):
1. **Generator.** The joint arm generator of item (d) (section 2 arm structure), with both chains under alternatives.
   - P side: rho(A1,D\*) = 0.75, r1 = 0.20, r2 = 0.15, r4 = 0.05, corr(g1,g4) = 0.6, ISU-like right skew.
   - K side: A15 excess error over A1 = 0.00, gain q of A15 over G15 = 0.05.
2. **Settings (four).** {independent conditions; intra-fold 0.10 with intra-lab 0.05} x {rho(A15,A1) = rho(A15,G15) = 0.90; 0.95}.
3. **Graphs (two).** w = 1/2 (current) and w = 0.78, both with the fallback counts (rho_s0 = 0.03).
4. **Replicates and seeds.** 20,000 per setting and graph, seeds `SeedSequence([20261105, crc32(scenario name)])`, with the
   same random draws for both graphs (common random numbers).
5. **Outputs per setting and graph.** P(P1N,P1S), P(..,P2), P(..,P3), P(K1), P(K1,K2N), P(K1,K2N,K2S).
6. **Implementation guard.** Item (d)'s 72 configurations with w = 0.78 in the settings iid_fb0.03 and fold10_lab05_fb0.03, at
   50,000 replicates. The maximum FWER must not exceed 0.025 + 2 Monte Carlo SE. If it does, the code is audited and w stays 1/2.
   Add a unit test that the initial levels are 0.0195 / 0.0055 and that the counts are 30 / 32.

**Decision rule (fixed now; applied by the script, which prints the chosen w; no person chooses).**
- Let ΔP = P(P chain through P3 | w = 0.78) - P(same | w = 1/2), and ΔK = P(K1 | 0.78) - P(K1 | 1/2).
- **Adopt w = 0.78 iff, in all four settings, ΔP + ΔK > 0 and ΔK >= -0.10.** Otherwise keep 1/2. The threshold 0.10 is a design
  choice of this ruling, not a measured quantity.
- If `g_weights.csv` is not filed before the freeze, w = 1/2.
- If chain K is struck (D016 section 8), P is at 0.025 (30 of 40) and the question is moot.
- The chosen w is not revisited if blinding exclusions reduce n. The counts at the chosen w are then recomputed by rule.
- Whichever w is chosen, the paper discloses the trade-off between the chains.

**Why ΔP + ΔK with a floor on K.**
- The P chain carries the paper's question and clause e1. K1 carries the K= clause "no more than 10 % worse", which is in the
  realistic best case T2 (J16 7).
- Weighting the two equally, with a floor that stops a large K1 loss, is symmetric between the two roles and cannot be tuned to
  the outcome.

**Rejected alternatives.**
- *Keep 1/2 with no simulation.* The opponent asked for the check, and RESULT 5.4 already shows a gain on P (0.36 to 0.49-0.53). The
  question is real and cheap to settle.
- *w = 2/3 or 3/4.* Dominated by discreteness (above).
- *Fixed sequence P then K.* The K chain would be tested only after P3 is rejected, which costs K1, the claim most likely to pass
  (J16 1.5).
- *Choosing w after looking at the power tables.* Excluded by the fixed rule.

---

## 4. GAP-1: "most of the advantage" in clause e1

**Ruling: confirmed, with one modification.**

**Definitions.** At g1, per condition c:
- L_total,c = ln(S_D\*,c / S_A1,c);
- L_law,c = ln(S_A9,c / S_A1,c);
- d_c = L_law,c - 0.5 L_total,c.

**"Most" holds iff both of the following are true:**
- e1 is reached: P1S, P2 and P3 are rejected in the graph, so L_total > 0 is implied by P1S, as the opponent requires.
- The one-sided sign test of median(d_c) > 0 at 0.025 under the fallback rule reaches **30 of 40** positive conditions.
  Equivalently, the lower end of the one-sided interval for median d_c (fallback rank) is above 0.

**How the test is run and reported.**
- It sits outside the graph and is labelled like the safety findings. Its alpha is disclosed in 9.11.
- Downgrade rows (ii)-(iv) of 9.8 apply to it as a binary pass/fail, as for the P2 clause.
- Reported beside it (descriptive): median L_law, median L_total, their ratio, and median d_c with its fallback 95 % interval.
- No KAN share is obtained by subtraction (opponent, section 4). The ladder of 9.6 stays as written.

**Modification against the opponent.** The opponent compares two medians (L_law against 0.5 L_total) and asks for "an interval
for L_law - 0.5 L_total". I use the median of the per-condition contrast instead, for three reasons:
- a difference of two medians has no exact order-statistic interval, so it would need a bootstrap, which this design does not
  trust with five folds;
- the per-condition contrast keeps D012's median-condition estimand;
- it uses the same deterministic machinery.

The paper states that median(d_c) > 0 is not the same statement as median L_law >= 0.5 median L_total. Both medians are printed.

**The failure branch must not change wording.** If P2 and P3 are S but "most" fails, none of the approved clauses is true:
- e1 would claim "most";
- e2 would say the dependence on condition count "was not shown", which is false after P3 S;
- e3 would deny P2 S, which is also false.

I therefore propose **clause e1'**, made only of words already in e1:
- (e1') P2 S and P3 S, "most" not shown: "the same network without the physics law was [Y] % worse, and the advantage was larger
  with 8 than with 32 cycling conditions"

e1, e2 and e3 stay word for word. **Adding e1' is a change to the D017 table, so only Shlok can make it.** It is a freeze
condition (action A6):
- If he approves, the rule above is in force.
- If he declines, GAP-1 stays as PREREG_v4 left it: e1 is used as approved and d_c is reported descriptively. His choice is
  recorded in a decision row.

**Rejected alternatives.**
- *No numeric rule.* The word "most" would have no tested quantity behind it (PREREG_v4 GAP-1).
- *The opponent's difference of medians with a bootstrap interval.* See the reasons above.
- *Moving to e2 or e3 when "most" fails.* That would print a false statement.
- *Adding a graph node P4 after P3.* It would delay the hand-over to K by one node and change the approved graph structure.

---

## 5. GAP-2 to GAP-11 (PREREG_v4 section 22)

| Gap | Ruling |
|---|---|
| GAP-2 secondary family as a nested N_i/S_i graph that reduces to Holm | **Accept, with a specification.** Local tests use the fallback (33 / 32 / 32 / 31 / 30 at 0.005 / 0.00625 / 0.00833 / 0.0125 / 0.025). Reverse S is tested at the slot's final level with the same counts. Item (d) did not simulate this family (RESULT 10.8), so the statistician adds hand-worked unit tests showing the reduction to Holm, instead of a simulation (it is Bonferroni-based). |
| GAP-3 states evaluated on the downgraded tiers | **Accept.** It keeps the title from being stronger than the abstract sentence. It is a consistency reading of J16 2 rule 2, not a table change. Row tiers are computed at the contrast's final primary level with the fallback counts. |
| GAP-4 lab-stratified tier definition | **Accept, with a specification.** Stratum weights are **1/3 per lab**, with equal weight per condition inside a lab. Weights proportional to stratum size would reproduce the primary median and test nothing. The bootstrap uses the MC seed rule of section 8. The row can only lower a tier. Its within-stratum bootstrap ignores fold dependence, which makes it a weaker check, never a source of extra type-I error. |
| GAP-5 ISU analogue window and descriptive replication | **Accept, with a specification.** If the ISU fallback applies (Samsung not parsed by 07 Nov 09:00), the same fixed rho_s0 = 0.03 rule is used at ISU's n. The counts are tabulated before any ISU score is used confirmatorily. The paper discloses that the dependence simulation was for the Samsung fold and lab structure. The 2-week scarce window stands. |
| GAP-6 S2 descriptive; PC-2 and PC-3 reported, not gate inputs | **Accept.** The approved definition of G wins. |
| GAP-7 blinding default 3.3(11) | **Accept** as the default. The freeze judge may overrule it before FROZEN. Reduced-n counts use the fallback rule. |
| GAP-8 K1 tier S reported at the unadjusted p, no effect on any title | **Accept**, using the fallback p, labelled unadjusted. |
| GAP-9 conventions (X = 100 (1 - exp(-median L)), k = 0, storage window, D\* ties) | **Accept.** The sign is correct for L = ln(S_C / S_T): a positive L means T has the lower error. |
| GAP-10 Q-A10: lowest tier over the two forms; reverse S run twice | **Accept.** The double safety test is disclosed. |
| GAP-11 standardisation over the fold's 32 training conditions; operational temperature constraint | **Accept.** It is label-free, fixed from identifiers, and its subsets are hashed into the config. |

---

## 6. Novelty: scope of "first" and the pre-submission reading conditions

**Adopted.** The allowed sentence of `03_novelty_recheck.md` section 3 (a conjunction of four elements) and its list of banned
"first" claims.
- The abstract may only say "we found no earlier study that ...".
- "To our knowledge" belongs only in the Introduction contribution list.
- Both are allowed only once conditions (a)-(d) all hold.

**Readings since the re-check** (FT-partial by me, as stated in the header):
- **Stroebl et al., JES 142, 119552.**
  - It applies model-based optimal experimental design to a fixed parametric calendar and cycle model on this dataset. The
    measured quantity is parameter uncertainty: a 28 % reduction for calendar ageing (highlights, section 5).
  - For cycle ageing, OED did not help, which the authors attribute to model inadequacy. Their leave-one-covariate-out analysis
    found that C_ch and C_dch "do not contribute significantly to explaining the residuals": MWU p > 0.05 and Spearman rho_s >
    0.995 between the residual distributions (section 4.2, Table 1). The superlinear trajectories of their Fig. 3f are not
    represented by the model.
  - I found no learned forecaster and no learning curve of forecast error over held-out conditions.
  - **Result:** the D016 re-open condition ("Stroebl JES 142 contains a data-efficiency study of learned ageing laws on this
    dataset") is not triggered. The Stroebl half of condition (a) is met at FT-partial depth. The novelty auditor records it in a
    paper note per CONTRACT section 4.
- **Zhang et al., JES 182, 125097.**
  - ECM-PINN for joint SOH estimation and ECM parameter inversion, with a cell-level split (12 unseen test cells; 15 for the
    voltage check).
  - No capacity-fade forecast, no calendar or cycle law, no KAN model, no learning curve.
  - **Result:** this agrees with the re-check. "First PINN on this dataset" stays banned, and the re-open condition is not
    triggered.

**Still open before the sentence may be used:**
- (a) Hallinger, full text;
- (b) Lucu Parts A and B, full text, confirming there is no physics-informed arm;
- (c) Jia, full text, confirming that the 14-against-100 claim is about lifetime prediction from early cycles, not extrapolation
  to new conditions;
- (d) the arXiv and OpenReview repeat, including ICLR 2027, within 7 days of submission.

**Effect on framing.**
- **Titles and abstract claim sentences: no change.** They are D017's and are untouched.
- **Abstract:** no novelty sentence until (a)-(d) are all met. The abstract's context sentence must not present "how few ageing
  tests" as an open question, because Lucu et al. asked it in JES in 2020.
- **Introduction contribution list (binding for the writer).**
  1. Learning curves over m and k for a joint calendar-plus-cycle learned law on held-out conditions. This is presented as an
     extension of Lucu A/B (GP, number of cells, no law), Jia (number of cells, early-cycle lifetime), Stroebl JES 142 (parameter
     variance of a fixed law under OED, same data) and Guo (trajectory fraction). The difference from each is named.
  2. The matched ablation ladder, presented as an extension of Jia and Navidi.
  3. A closed-form law extracted from the KAN, tested against an equally simplified additive law on held-out conditions. This is
     the element rated NOVEL.
  4. The conjunction sentence, only after (a)-(d) hold.
- **Discussion and Limitations (binding).**
  - Any C-rate dependence that the learned stress map shows is reported against Stroebl's finding that their parametric model's
    C-rate terms were not supported. C-rate effects are never called established.
  - Stroebl's statement that the cycle model is inadequate may be cited as motivation for a learned stress law. It is not
    evidence for our law.

---

## 7. Re-open conditions

D018 is re-opened if any of the following happens:
- the statistician's tabulation (A3) or the code does not reproduce the counts of section 2.1;
- the weight simulation's FWER guard fails, in which case w = 1/2 holds until the audit closes;
- any Samsung outer score is computed before FROZEN, which voids the approval of 2.5 (stop rule 7);
- Shlok declines e1', which re-opens GAP-1 only; his row records the alternative;
- Hallinger, Lucu A/B or Jia (full text) contain a learning curve of a learned or physics-informed forecaster over the number of
  ageing conditions on held-out conditions, which re-opens the novelty scope of section 6; a Hallinger result of that kind on this
  dataset also triggers stop rule 12;
- the ISU fallback is triggered, in which case the counts of GAP-5 must be filed before any ISU confirmatory score;
- a later pre-freeze simulation or derivation shows the fallback's size above 1.2 x nominal inside R4, which would mean the
  simulation was in error.

The following do **not** re-open D018:
- a training-side dependence estimate above 0.03 (it is reported, section 2.3);
- weak power, and an inconclusive result (the opponent: "report inconclusive evidence as such").

---

## Actions

| # | Owner | What | File |
|---|---|---|---|
| A1 | experiment-designer | Write D018 into PREREG_v4 before the freeze:<br>- fill [SIM: a-e] from RESULT 9;<br>- 9.1 and 9.3: the fallback as the confirmatory test and its wording;<br>- 9.4: counts 31 / 30 and w per A2;<br>- 9.5: Holm-level counts;<br>- 9.7: ranks 8 and 11;<br>- 9.8: GAP-4 weights and the GAP-1 test;<br>- 9.9: rows 2.3 (i) and (ii);<br>- 9.11: GAP-1 and NC-2 lines;<br>- section 10: NC-2 at 30 of 40;<br>- section 1: power bullet with the fallback numbers;<br>- 12 rule 9 and 17.2 C2 (fallback approved, D018);<br>- strike GAP-1 to GAP-11 markers per section 5.<br>Section 11 stays byte-identical (C21). | `runs/prereg/PREREG_v4.md` (or v4.1 with a change-log row) |
| A2 | statistician | Weight simulation and decision script exactly as in section 3 | `runs/prereg/stats_sim_v4/sim_v4.py` (item g), `g_weights.csv`, `RESULT_weights.md` |
| A3 | statistician | Tabulate:<br>- fallback counts and the 95 % and 1 - 0.05/9 ranks at n = 40 and at every n down to the 3.3(11) minimum, for every level in use (including 0.0195 / 0.0055 if w = 0.78 is adopted);<br>- the ISU n if the fallback applies;<br>- the estimator of the one-sided upper bound for item (f).<br>Add hand-worked unit tests of the secondary graph (GAP-2). | `runs/prereg/stats_sim_v4/fb_tables.csv`; `code/tests/` |
| A4 | implementer | In `stats_step.py`:<br>- the Beta-binomial sign test (rho_s0 = 0.03) for every Test B test listed in 2.1;<br>- the plain row and the dependence-sensitivity row with its fixed sentence;<br>- per-lab rows;<br>- the GAP-1 d_c test;<br>- the item (f) dependence file, hashed before any outer score, with a guard that blocks the statistics step otherwise.<br>Limiting-case tests: rho_s0 = 0 reproduces the plain counts 28 / 27. | `code/pinnkan/stats_step.py`, `code/pinnkan/graph_test.py`, `code/tests/` |
| A5 | lead | Tell Shlok before the freeze:<br>- under the fallback, the 80 %-power gain at g1 is 0.21-0.25 at rho 0.75 (not 17-22 %);<br>- the P chain through P3 has probability 0.36 (0.49-0.53 if w = 0.78 is adopted);<br>- P0, or P+ with e2 or e3, is a likely outcome.<br>The table does not change. | status file; `research/progress.md` |
| A6 | lead, then Shlok | Ask Shlok to approve or decline clause e1' (section 4). Record his answer as a decision row. This is a freeze condition. | `research/DECISIONS.md` |
| A7 | novelty auditor | Paper notes for Stroebl JES 142 and Zhang JES 182 (CONTRACT 4). Full texts of Hallinger, Lucu A/B and Jia (Shlok's e-gateway if paywalled). Repeat the arXiv and OpenReview check within 7 days of submission. | `notes/papers/`; `refs/PAYWALLED_FOR_SHLOK.md` |
| A8 | paper writer | Introduction contribution list and abstract rule of section 6. Discussion sentence on Stroebl's C-rate finding. Limitations sentence on the dependence assumption (2.3). | `paper/draft/` |
| A9 | gate auditor (at the freeze) | Verify A1-A4 and A6 on disk; tick C2 with pointers; check C21 byte for byte. | `runs/prereg/PREREG_v4.md` 17.2; `research/audits/` |
| A10 | lead | Update the RESUME block with D018 and the open items A2-A8. | `research/progress.md` |
