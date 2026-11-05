# Report on PREREG_v4 (draft of the freeze candidate, Design R2), 2026-11-05

Role: experiment-designer. File written: `runs/prereg/PREREG_v4.md` (22 sections, about 600 lines). Reading depth: full text of the D016 judge file, PREREG_v3, V3_EDITS, the D015 red team, STATS_RULING, TYPE1_SIGNFLIP, NEGCONTROL_RULING, BLINDING_LOG, CONTRACT, DECISIONS D013-D017 and the progress RESUME and log; partial: D016 proposal 5.1-5.8, `code/README.md`, `stats_step.py` (lines 1-125 and grep), `specs.py`, `paper/draft/05_evaluation.md` and `00_open_items.md` (full), the exemplar notes on Stroebl and Zhang (reading-depth lines), P5 RESULT lines 20-30. No Samsung value, no outer-test score and no `stats_sim_v4/` file was opened (the directory does not exist yet). No confirmatory code was run.

## 1. What v4 is
- Built from V3 by a script that copies unchanged V3 text byte for byte (sections 3.1-3.3, 4, 5 task/throughput/forecast set, 7 law and recipe, 7.2, 8, 10 NC-1/NC-2, 11a items 1-5, 18) and inserts the Design R2 text. Section 11 is `02_judge.md` lines 219-291 copied verbatim; a byte check against the judge file passed. A reading note outside the block maps its internal section references to v4.
- Changes from v3 are tabulated in section 19.2 (section, change, source); V3_EDITS 1-11 in 19.3; each D015 finding F1-F16 in 19.4 ("resolved by section X" or "stated limitation"); alignment list in section 20; pending simulation results in section 21; gaps and source conflicts in section 22.

## 2. Open placeholders (nothing invented)
- `[SIM: item a]` size of the sign test under shared fold/lab effects and the pre-set fallback (9.3, 12 rule 9); `[SIM: item b]` power of P1 at g1 and the P2/P3 chain probabilities (section 1, 9.4); `[SIM: item c]` power of K1, K2 (section 1, 9.4); `[SIM: item d]` `graph_test` and the graph FWER check (9.4, 9.5, 17.2 C10); `[SIM: item e]` existence and coverage of the exact intervals at 1 - 0.05/9 (9.7); `[SIM: item f]` rho estimates (section 1, 15). Section 21 lists place and expected file for each.
- `[ARCH: cap]` in 7.3 item 1 and 17.3.
- `[D]` values: k_full, k_sto, N or Partial plan, A10 equation numbers, ISU scarce window analogue (3.4), seeds.
- Binomial counts quoted (28 of 40 at 0.0125, 27 at 0.025, 29 at 0.00625) are the T1 values; I re-derived them by exact binomial arithmetic only as a check.

## 3. Freeze checklist status (from files, not assumptions)
Met: FB-7 (closed in V3); D016 condition "Shlok's approval of the table" (D017); "Shlok told the likely outcome" (status file section 00, D017). Everything else is open, in particular: FB-1 and FB-2 (Zhang, Stroebl, Hallinger unread; `A10_FORM["verified"]` False), FB-3/4/6 (check-up fetch 147 of 279 cells at 08:37, no manifest, window counts are placeholders), FB-5 (no ZYK file), FB-8/9/10 (only earlier-commit runs), statistician items (a)-(f) (`stats_sim_v4/` absent), novelty re-check (`03_novelty_recheck.md` absent), D016 code and its limiting-case tests (none written), pilot P6 (not run), alignment (section 20, nothing changed), gate auditor tick and signatures.

## 4. V3_EDITS dispositions (detail in 19.3)
1 applied (law/recipe text kept verbatim; A5 pairs; scope sentence; 11a item 4). 2 applied, row (k) re-aimed at P2. 3 applied. 4 applied (synthetic-circularity sentence limited to G0). 5 applied unchanged. 6 applied, adapted to k = 0. 7 applied; the code still has a Test C Holm-2 (section 20). 8 applied and extended (new figure inputs). 9 applied as FB-10. 10 applied (NC-2 now at g4). 11 ruled by a pre-set default: outer-test cells whose values were shown on a terminal (currently TP_z24_01_s1 is known; four more need an identifier-only split look-up) are excluded from scoring; the pipeline parse is disclosed only; the freeze judge may overrule before FROZEN.

## 5. Things in the sources that conflict or leave a gap (fuller list in section 22)
1. **Clause (e1) "most of the advantage came from the physics law"** has no tested quantity behind "most". Table wording is untouched (D017); a numeric reading rule needs a new decision row before the freeze. Highest-priority item for the lead.
2. **Secondary family:** the judge says Holm; D015 F4 forbids ordering by an untested statistic. v4 uses a sequentially rejective graph with nested N and S nodes that reduces to Holm; the statistician should confirm it.
3. **Downgrade rule:** the judge lowers "the abstract's tier word"; v4 also evaluates the P/K states on the lowered tiers so that title and sentence agree. The lab-stratified tier and the lab-and-stage-indicator rows were undefined; v4 defines them (9.8).
4. **Gate G** in the approved table omits the old positive controls (V3 said any failed one trips G). The approved table wins: PC-2 and PC-3 become reported checks, only PC-1 (G0, nRMSE <= 0.15) gates.
5. **V3/T1 sign slip:** "relative reduction = 1 - exp(median L)" is wrong for L = ln(comparator/target); the code uses 1 - exp(-median L); v4 fixes the convention (section 1).
6. **ISU/SNL under R2** are not specified by D016 beyond "the same table on ISU" as fallback; v4 fills the ISU grid analogue (W in {0, 2, 4} weeks, the 2 is my choice) and makes the Samsung-side replication optional and descriptive. S2/H5 and X1 leave the hypothesis set (H5 is second on the judge's drop list; Q-T replaces X1).
7. **Q-A10 with two forms:** "weaker of the two sets the tier" is implemented as the lowest tier over the two forms; the reverse-S safety test is then run twice (disclosed).
8. **K1 tier S** ("reported if reached") has no place in the table; it is reported unadjusted with no effect on title or abstract.
9. Process: `debates/D015_redteam_v3/` and `debates/D013_build_choices/` are untracked in git; DECISIONS has no D010 row (D015 F12.6); the existing code and README still contradict v3 on Test C (Holm-2), and draft 5.5 still carries the withdrawn negative-control criteria.

## 6. Not done, by instruction or by lack of input
No edit of code, README or the draft; no split-membership look-up of the five terminal-exposed cells (identifier-only task, listed in 17.2 C13); no novelty or literature check; no citation was added.
