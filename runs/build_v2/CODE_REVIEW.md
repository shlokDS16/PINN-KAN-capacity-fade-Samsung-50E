# Independent code review of build_v2 (D016/D018/D020), 2026-11-05

Reviewer: independent code-reviewer agent (read-only; did not execute the suite). Saved by the lead from the reviewer's reply.
Counts: Critical 0 | Important 7 | Minor 9 | no test-fold leakage path found.

## Checked and sound
Test-fold access (load_split "test" behind require_frozen; tuning, D*/AG selection, comparators/margins inputs and subsets use
training cells and ids only; k=0 design rate label-free; causal t/EFC; NC-1 scrambles after each k window). Subset selector
temperature constraint holds. graph_test is the standard Bretz update; Beta-binomial a=b=(1/rho-1)/2; counts 30/40 at 0.025 and
31/40 at 0.0125; ranks 11 and 8 consistent; L sign conventions correct. Ensemble: per-seed persistence before averaging; A11
deterministic; A10/A12 seed-dependent and ensembled; K chain reads per-seed view.

## Important
- I1 stats_v4.py:724-732 primary_numbers: T9 clause [W] minimum taken over all A10 forms, not only reverse-S forms; can print a
  negative effect. Fix: filter by reverse_S[f]["rejected"]; add a mixed-form test.
- I2 stats_rows.py:52-89, 208-230; stats_v4.py:787-788: the "most" (d_c) test is not recomputed under downgrade rows (ii)-(iv)
  as PREREG 9.8 rule 4 / D018 s4 require. Fix: compute t["most"] per row store at g1 (A1/A9/D*), 30/40 at 0.025; add lab-stratified bound.
- I3 stats_v4.py:282: chain K silently struck when K arms are missing, so P1 runs at 0.025. Fix: raise unless k_chain_struck is
  True in the frozen config; report initial levels correctly.
- I4 run.py:303-304 vs arms.py:177-178,195: config "symbolic" (cap, refit_frac) never reaches the arm. Fix: pass cfg symbolic
  into ctx, add to DEFAULTS, run()-level test (or refuse the key).
- I5 stats_step.py:510-512, 517-528: CLI and run_stats_v4 call run_v4 with gate=None, row_tiers=None; run_v4_full never called;
  no provisional marker. Fix: route through stats_rows.run_v4_full; provisional flag by default; gate from NC-1/PC-1/invariance.
- I6 silent acceptance of missing inputs: selectors complete/candidates_present unread; Q-A10 with one form; Store.pair
  intersection shrinks n; nc shrinks the Bonferroni divisor. Fix: completeness check in Store.from_runs (folds 0-4 for every cell,
  n = 40 unless blinding-exclusion list, D*/AG complete, A10 and A10P both present).
- I7 PREREG 9.8 rule 1 (mean-vs-median sign disagreement at g1/g4) not implemented and not listed as unbuilt.

## Minor
- M1 run.py:424 fit timing includes predict and NC-1 re-predict; time fit() alone.
- M2 subsets.json sha not compared in run.py nor in the freeze payload; P6b sha recorded after chash is computed.
- M3 run.py:293 k_full silently defaults to 4 when window.k_cycling absent; require it for real data.
- M4 run.py:326-336 auto_budget makes N and inner folds wall-clock dependent and unhashed; sym family excluded from Partial
  trigger. Refuse auto_budget in confirmatory mode or pin budget_rule.json.
- M5 stats_v4.py:513 item (f) ordering by file mtime; pin sha in git/FROZEN. item_f_from_runs rebuilds inner folds from scored
  conditions; take them from the training meta file.
- M6 run.py:298 nc1_full scrambles after k_full only; scramble at k=0 and k=2 too.
- M7 pinn.predict_data_only (272-291): A9 not explicitly forced to z=0 at k=0 (works by architecture only); add the force.
- M8 semi.py:176-186 indicator_beta docstring says flat prior, code uses N(0, TAU^2).
- M9 stats_v4.py:155-166 partial per-seed files mix score kinds; require all or none; check Design R2 markers in from_runs.

## Verdicts on builder choices (summary)
build_v1 7.3: 7.3.1 agree provisionally (fix from ZYK files before freeze); 7.3.2 open (TP_z24_01 segment drop vs the dataset
paper's incident list); 7.3.3/7.3.4/7.3.6 moot; 7.3.5 agree; 7.3.7 out of scope.
CHOICES: item 1 agree (choice 4: justification should be "noisier row, triggers downgrades more often", judge to confirm);
item 2 agree; item 3 agree except choice 3: refit_frac 0.5 gives A15/G15 1,000 extra warm-started steps over A1 (3,000 vs 2,000),
favouring A15 in K1 - match A1's budget or add a matched-continuation A1 row (confidence 60); item 4 agree (strike GRU with a
change-log row); item 5 agree except choice 3 (I3) and choice 6 (I1); item 6 agree, provisional flag not wired (I5), "most"
omitted from row (iv) (I2); item 7 agree; D020 rows agree, timing (M1), adopt key contract confirmed with P6b writer.
