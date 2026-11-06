# D029 judge: novelty scope after Lucu A/B (2026-11-06)

Inputs: `debates/D016_roles/04_novelty_C4_audit.md` (proposer), `notes/papers/lucu2020_A_B_JES30.md`, `debates/codex_panel/turn10_response.md` (opponent, REVISE), D018 judge 6-7, PREREG_v4 11. No Samsung data opened.

## 0. Verdict: REVISE (auditor section 5 adopted with the changes below)
D018 7's fifth bullet fired: Lucu A/B give a nested GP learning curve over the number of conditions on held-out cells (no k axis, comparators, intervals or physics arm). The m-curve alone is not ours. Stop rule 12 not triggered (not the 50E).

## 1. New section 6 scope (replaces D018 6 "Effect on framing"; binding for the writer)
**Introduction contribution list**, in this order, each a test performed, never its outcome (outcomes only from PREREG 11):
1. Held-out test of the closed-form law extracted from the KAN (A15) against an equally simplified additive law (G15), D022 protocol (7.3 matching). Novelty attaches to this matched test, not to symbolic extraction; PIKAN/PGKAN, PiDDM, KA-CRNN named as extraction precedents.
2. Matched ablation ladder and tuned data-driven comparators on the same cells; Jia's comparison stated as cross-dataset (auditor 5.1 item 2).
3. Learning curves over m and k as an extension of Lucu A/B ("number of conditions", GP, storage and cycling separate), Stroebl JES 142 and Guo, each difference named (auditor 5.1 item 1).
4. The conjunction sentence (auditor 5.1), "to our knowledge" form.
Items 1-3 without novelty phrases may be drafted now.

**Discussion.** The "how many tests" question is credited to Lucu et al. 2020; our results say whether a physics law and a joint calendar-plus-cycle law change that curve. Lucu B's 9 conditions at 2 % MAE_Q is context only, differences stated; no "fewer conditions than Lucu". D018's Stroebl rules stand.

**Abstract.** Context sentence: earlier studies quantified how many ageing tests Gaussian-process and mechanistic models need; never that the question is open. Only novelty sentence: auditor 5.1's conjunction sentence, verbatim, after (d).

**Banned:** auditor 5.2; any sentence calling "how many tests" open or unanswered; "we answer how many tests are needed"; "first" in every form.

**Condition (d) gates** every "to our knowledge" and "we found no earlier study" sentence. Within 7 days of submission: (i) arXiv and OpenReview incl. ICLR 2027; (ii) new Stroebl/Palm or Hallinger work on the 50E (learned-law data efficiency: stop rule 12); (iii) PIKAN/PGKAN and KA-CRNN at method level for a matched held-out extracted-law versus additive-law test. A hit in (iii) removes item 1's novelty phrase and the conjunction.

## 2. Titles (recommendation to Shlok; section 11 not edited)
T5/T6 put Lucu's question in the title as if open; body text cannot cure that. Replacement removes the question form only: same cells (P0/K=, P0/K-), same evidence words, no new claim, no change to state selection.

| | Old (approved, D017) | New (proposed) |
|---|---|---|
| T5 | "How many cycling tests and check-ups do physics-informed and data-driven forecasts of lithium-ion capacity fade need? Learning curves with Kolmogorov-Arnold stress functions" | "Physics-informed and data-driven forecasts of lithium-ion capacity fade against the number of cycling tests and check-ups: learning curves with Kolmogorov-Arnold stress functions" |
| T6 | "How many cycling tests and check-ups do physics-informed and data-driven forecasts of lithium-ion capacity fade need? Learning curves on a designed ageing dataset" | "Physics-informed and data-driven forecasts of lithium-ion capacity fade against the number of cycling tests and check-ups: learning curves on a designed ageing dataset" |

**Keep as approved:** T1-T3 ("few" anchored by the fixed lead-in "With eight cycling conditions and two check-ups per held-out cell,"); T4, T7, T8 ("learning curves" names the method); T9a/T9b; all abstract claim and qualifier sentences (no novelty words).

If approved before FROZEN: PREREG 11 gets the two strings, a reading-note line and a change-log row; C21's byte check uses the D016 block plus this amendment. If declined or unanswered at FROZEN, T5/T6 stand and the Introduction's first paragraph carries the Lucu extension sentence.

## 3. Design, tests, freeze
No change to hypotheses, arms, splits, tests, alpha, states or stop rules. C4: (a), (c) closed; (b) closed, re-open resolved here; (d) open. FB-1, FB-2 met pending the gate auditor. Not a freeze blocker.

## 4. Re-open if
(d) hit; a k axis or physics arm found in a condition-count study; Shlok declines (record only).
