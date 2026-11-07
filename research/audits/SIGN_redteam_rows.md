# Red-team check: row 9.9 (s), the descriptive C-rate ablation (D041), PREREG_v4 rev. 23

Date: 2026-11-06. Role: red team (signs sections 1, 10 and 11).

**Verdict: NOT SIGNED.** I found 2 MAJOR and 6 MINOR findings and nothing FATAL. Both MAJOR findings are code-level and cheap to fix. The row cannot change a section 1 claim, a section 10 control or a section 11 title or state (checked below).

## Scope and reading
- **Text.** `runs/prereg/PREREG_v4.md`: row (s) inside 9.9 (`:309`), the 9.11 row (`:330`), section 14 Table 2 (`:474`), and the rev. 23 change-log row (`:600`), as a word diff against a46d7b8. Also DECISIONS D041 and its correction.
- **Code (uncommitted on a46d7b8).** `git diff` of:
  - `metrics.py` (`resolve_neutralise`, `neutralise_stress`);
  - `run.py` (`validate_config`, `_run`);
  - `stats_gaps.py` (`crate_row`, `CRATE_SENTENCES`);
  - `stats_step.py` (`gap`, `_stats_gaps_v4`, `run_stats_v4`, CLI);
  - `code/prereg/make_confirmatory_configs.py`.
- **Other code read.**
  - `code/figures/table2.py:81-89`.
  - `pinn._hull_sample` and `make_collocation` (`:39-78`).
  - The "Row (s)" section of `STATS_GAPS_REPORT.md`.
  - The test names in `test_pk_crate_ablation.py`, whose 15 tests pass (27 s, CPU).
- **Supporting notes.** `notes/exemplars/deep/stroebl2025.md:48, 85` and `notes/exemplars/BLUEPRINT_v2.md:444-452`.
- **What I did not touch.** No Samsung data or run output was opened, and nothing was edited except this file. `runs/prereg/FROZEN` is absent.

**Probes (synthetic, CPU).**
- *Collocation hull.* I called `pinn._hull_sample` on 32 random 5-D normalised stress vectors, then on the same vectors with columns 3 and 4 (C_ch, C_dch) set to constants. The C-rate columns of the 64 collocation points:

  | Case | C_ch column range | C_dch column range |
  |---|---|---|
  | primary | [-0.90, 0.75] | [-0.68, 0.64] |
  | neutralised | [0.21, 1.20] | [-0.10, 0.88] |

  In the neutralised case, **64 of 64** points are off the neutral value. Script: `$TMP/hull5.py`.
- *Configs.* The pinned fold-0 crate config differs from the NC-2 config only in `neutralise_stress` replacing `permute_stress`. It differs from the primary g4 config in `arms` (A1 only), `k` (grid → None) and the two audit hashes.

## Answers to the brief's questions
- **Can it change a section 1 claim, a section 10 control or a section 11 title or state?** No.
  - `crate_row` writes only `out["crate_ablation"]`. Nothing in `stats_rows`, `stats_v4` or the outcome assembly reads it (grep).
  - The gate fields are untouched.
  - The section 11 hash is unchanged (per the rev. 23 row).
- **Can the row be dropped?** Not quietly. If `crate_runs` is absent in a strict run once FROZEN exists, the run is refused (`stats_step.py`, the M-1 `absent` list), and a compute error stops a strict run (`G9_crate` is in `REGISTERED`).
- **Is there a "not computed" escape?** Yes, a narrow one (m-1).
- **Median versus another neutral value.** The median is fixed in the text and the configs. It is taken over training conditions only (`metrics.neutralise_stress`; test `test_the_median_is_a_training_side_quantity_only`), so this is not a fork.
- **Storage cells untouched.** This is correct, because their cycling inputs are structurally 0.
- **Re-tuning.** Re-tuning is part of the declared estimand: A1 is tuned and refitted. However, the arm also differs from A1 in its collocation design (M-2) and possibly in its run configuration (m-6).
- **Do the fixed sentences overclaim?** The prereg sentences are hedged ("consistent with"; "not shown to contribute"). The code's sentence is not the prereg's sentence (M-1). The framing towards Stroebl overreaches (m-3).

## Findings

### M-1 (MAJOR) The code's fixed sentences are not the preregistered sentences, and the negative one overclaims
- **Where.** `stats_gaps.CRATE_SENTENCES` writes:
  - "consistent with the learned C-rate dependence contributing to accuracy at g4";
  - "**not consistent with** the learned C-rate dependence contributing to accuracy at g4".
- **Conflict.** PREREG `:309` fixes two different full sentences: "Setting both C-rate inputs ... raised the median condition error at g4 (median ratio [x], interval [a, b]), which is consistent with ..." and "... did not raise ... beyond its interval ...; the learned C-rate dependence is not shown to contribute to accuracy".
- **Why it overclaims.** An interval that includes 0 is absence of evidence. "Not consistent with" asserts evidence against.
- **Rejection condition.** Any generated or manuscript sentence for row (s) that is not a verbatim fill of a `:309` sentence.
- **Fix.** Replace `CRATE_SENTENCES` with the two `:309` sentences verbatim, with the brackets [x], [a, b] filled from `exp(median_L)` and `exp(median_ci)` in `crate_row`, and record them under `sentence`. Add a test asserting string equality with the PREREG text.

### M-2 (MAJOR) The ablated arm changes the physics-residual collocation design, not only the C-rate inputs
- **Mechanism.** `pinn.make_collocation` builds the hull sample from the training cycling stress vectors `b.s` (`pinn.py:72-78`). `_hull_sample` (`:39-57`) sets `span = 1.0` for a constant column and falls back to the bounding box when the hull is degenerate.
- **Effect.** With C_ch and C_dch neutralised, both columns are constant. Every hull collocation point then gets C-rates spread over [c, c + 1] in normalised units, off the neutral value and outside any training condition (probe: 64 of 64). `nu_h = spec.efc_rate(raw)` is then computed at those C-rates.
- **Consequence.** A1crate differs from A1 in two ways: it loses the C-rate information, and it gains a residual enforced at one-sided, out-of-design C-rates.
- **Cheapest alternative explanation of a "raised" result.** The collocation artifact. This biases the row towards the favourable sentence.
- **Rejection condition.** A crate run whose `col` hull points carry C_ch or C_dch values other than the fold's neutral value.
- **Fix.** In `pinn._hull_sample`, take `const = (hi - lo) <= 1e-9`, run the Delaunay and LHS on the non-constant columns only, and set `P[:, const] = lo[const]` (span 0, not 1). Then:
  - add a test that the neutralised collocation points carry exactly the neutral C-rate values;
  - re-run `head_comparison` / FB-9 to show that the primary outputs are byte-identical (no primary configuration has a constant stress column; if one has, that is a pre-existing defect and must be reported).

### m-1 (MINOR) A caller can choose "not computed", and Table 2 then drops the row
- **Where.** `stats_step._stats_gaps_v4` raises `NeedsRescoreError` when a passed crate directory is not a neutralised Test B run. Passing the wrong directories (for example, the primary g4 runs) therefore gives "not computed", and the step continues.
- **Why that is wrong.** The cure is to pass the pinned runs. It needs no re-score, so it is a caller error, not a rescore case.
- **Table 2.** `table2.py:82` prints the row only when `status == "computed"`. A not-computed row disappears, against `:309` "recorded as not computed and printed as such".
- **Mitigation.** The M-1 text of section 10 makes the first complete strict run binding, which limits the exploit.
- **Rejection condition.** A confirmatory Table 2 without a row (s) line.
- **Fix.** Check the configs instead of raising `NeedsRescoreError`: each crate directory's canonical config hash must equal the MANIFEST hash of `crate_ablation/conf_samsung_B_f{f}_m32_crate.json` for its fold, with exactly folds 0-4. On a mismatch raise `ValueError`; this is a stop, because strict runs stop on `G9_crate` in `REGISTERED`. In `table2.py`, print a line `A1 C-rate neutralised | not computed: <reason>` when the status is not "computed".

### m-2 (MINOR) The label (s) is used twice in 9.9
- **Where.** 9.9 already has "(s) *independent-conditions row and per-lab rows*" before (t). The new row is a second "(s)". "Row (s) of 9.9" in 9.11, section 14, D041 and the code is therefore ambiguous.
- **Fix.** Relabel the new row "(u)" in `:309`, `:330`, `:474`, `:600`, the code docstrings, the CLI help and `STATS_GAPS_REPORT.md`. D041 is append-only, so add a correction line instead.

### m-3 (MINOR) "It answers" Stroebl overreaches, and the A8 reference dangles
- **Stroebl.** Stroebl et al. Table 1 compares the in-sample fit and residuals of a parametric model with and without C-rate terms (`notes/exemplars/deep/stroebl2025.md:48`). Row (s) compares held-out-condition forecasts of a learned model. Different model, criterion and split: neither outcome confirms or contradicts their finding.
- **A8.** "the Discussion rule on C-rate (A8; section 2)" points to nothing in section 2. A8 is an action in `notes/exemplars/BLUEPRINT_v2.md:449` ("never call a C-rate effect established").
- **Fix.** At `:309`, replace "It answers the dataset authors' finding that ..." with:
  > "It is reported beside the dataset authors' finding that removing the C-rate terms left their parametric cycle model's fit unchanged (Stroebl et al., JES 142, 119552, Table 1); the model, criterion and split differ, so it neither confirms nor contradicts that finding."

  Replace "(A8; section 2)" with "(the A8 rule of `notes/exemplars/BLUEPRINT_v2.md`: a C-rate effect is never called established)".

### m-4 (MINOR) The fixed sentences have no case for lower error, and no alias caveat
- **Missing case.** If the upper bound is below 0, the ablated model is more accurate. The second sentence ("did not raise ... beyond its interval") is literally true but hides this.
- **Missing caveat.** The C-rate inputs can also carry laboratory and stage identity. That is the same aliasing caveat as temperature (11a item 9).
- **Fix (text, `:309`).** Add a third sentence, chosen when the interval's upper bound is below 0:
  > "Setting both C-rate inputs to their training median lowered the median condition error at g4 (median ratio [x], interval [a, b]); the learned C-rate dependence did not help accuracy at this cell."

  Append to every sentence:
  > "; the C-rate inputs may also carry laboratory and stage identity."

  Use the same strings in `crate_row`.

### m-5 (MINOR) "No test" is cosmetic
- **Problem.** The sentence rule "lower bound of [L(11), L(30)] > 0" is the same event as at least 30 of 40 conditions with L_c > 0. That is the design-effect sign test at about 0.019 one-sided (9.3, `:267`), the bar of NC-2.
- **Fix.** At `:309`, after "No test, no p-value, no tier", add:
  > "(the sentence rule is the event that at least [the rank-11 count] of n conditions have L_c > 0, the bar of the design-effect sign test at 0.0194; it is outside every family)".

### m-6 (MINOR) Nothing shows that the pairing changes C-rate alone
- **Problem.** The paired real run is the primary g4 run (15 arms, `k: grid`). The crate run is A1 only with a single window. No test shows that A1's g4 scores are identical between those two configuration forms when `neutralise_stress` is absent (for example, whether tuning or RNG depend on the arm list or on k).
- **Fix.** Add a synthetic G2 test: the crate config with `neutralise_stress` removed, against the primary g4 config, must give identical A1 `condition_scores` at g4 (max |difference| = 0). This also covers NC-2's pairing.

## Not found (checked)
- The median is training-side only.
- Throughput, times, retention, window and QC are untouched.
- The key is absent from DEFAULTS, so the 276 existing hashes are unchanged (pinned fixture and test).
- `permute_stress` together with `neutralise_stress` is refused.
- L orientation: `entry(pair, ..., "A1", "A1_crate")` gives L = ln(S_A1crate / S_A1), with L > 0 meaning the full model is better.
- The interval is the rank-11 fallback of 9.7.
- No title, state, gate, graph or count reads the row.

## Ledger
This project has no `tools/ledger.py`, so no ledger rows were added.

**Red-team signature for row 9.9 (s): NOT SIGNED.** Re-signing needs only a check of the M-1 and M-2 fixes and of whichever minors are applied.

## Re-sign (2026-11-06, row (u), formerly (s); scoped to M-1, M-2 and m-1 to m-6)

**Scope.** I checked the following, all synthetic and on CPU:
- the row (u) text at PREREG `:309`, its 9.11 row (`:329`) and the section 14 row (`:475`);
- `git diff a46d7b8` of `pinn._hull_sample`;
- `stats_gaps.check_crate_runs`, `CRATE_SENTENCES` and `crate_row`;
- the row (u) block of `stats_step._stats_gaps_v4` and `table2.py:81-94`;
- the M-2 paragraph of `STATS_GAPS_REPORT.md` (`:79-82`).

Results:
- `test_pk_crate_ablation.py`: **20 passed** (51 s).
- My `hull5.py` probe, re-run: the neutralised columns now hold exactly 0.2 and -0.1, with **0 of 64** points off the neutral value. The primary ranges are unchanged ([-0.90, 0.75] / [-0.68, 0.64]).

I opened no Samsung data or run output.

| Item | Status | Evidence |
|---|---|---|
| M-1 | FIXED | `CRATE_SENTENCES` holds the three `:309` sentences verbatim (a test reads the prereg). The brackets are filled with exp(median L) and exp of the interval (`crate_row`). "Not consistent with" is gone, and the neutral case reads "did not clearly raise ... (the interval includes a ratio of 1; ...); ... not shown to contribute". |
| M-2 | FIXED | `_hull_sample` forms the hull on the non-constant columns and sets constant columns to their value exactly. Without a constant column the original code runs unchanged, so its output is bit-identical. **The SNL defect is outside the registered analysis, confirmed:** PREREG `:95` says "There is no SNL replication (D028 (d) 7)", and `:310` lists the SNL replication among the rows not run. The report states that no Samsung, ISU or synthetic Samsung-layout run in the suite has a constant stress column. |
| m-1 | FIXED | `check_crate_runs` requires the MANIFEST hash of each pinned crate config, recomputes the hash from `config_input`, and requires folds 0-4 exactly once. It raises `ValueError`, which stops a strict run, so wrong directories no longer give "not computed". `table2.py:90-94` prints "not computed: reason" with no substitute. |
| m-2 | FIXED | The row is relabelled (u). No "(s) *C-rate" remains (grep count 0), and the status line, 9.11 and section 14 say (u). |
| m-3 | FIXED | The Stroebl text now says "reported beside ... the model, criterion and split differ, so it neither confirms nor contradicts that finding". A8 now points to `notes/exemplars/BLUEPRINT_v2.md`. |
| m-4 | FIXED | The "lowered" sentence for an upper bound below 0 is added, and every sentence carries the laboratory/stage identity caveat. |
| m-5 | FIXED | The duality sentence is in place: L(11) > 0 iff at least 30 of 40 positive, one-sided 0.0194, at most 0.025 under the 9.3 assumption. It has its own 9.11 row. |
| m-6 | FIXED (per the coder) | A test shows identical A1 scores with the key absent (max |difference| 0.0). I did not re-run it separately; it is in the 888-test suite the lead reports. |

**One new minor (non-blocking).**
- **n-1 (text, `:309`).** "a pairing or configuration integrity error is recorded as not computed" no longer matches the code. Since m-1, a run that is not the pinned configuration stops the step; only a pairing mismatch between the pinned runs gives "not computed". The code is the stricter of the two, so nothing can be exploited.
- **Fix.** Replace the phrase with: "runs that are not the five pinned configurations stop the step; a pairing integrity error between the pinned runs is recorded as not computed and printed as such, without a substitute".

**Unchanged.** The row reads into no title, state, tier, gate, graph or count, and section 11 is untouched.

**Red-team signature for row 9.9 (u): SIGNED.** n-1 is minor and does not block.
