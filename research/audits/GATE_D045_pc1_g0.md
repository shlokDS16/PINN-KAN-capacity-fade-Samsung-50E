# Gate audit D045: PC-1 synthetic G0 run (2026-11-12)

Auditor: gate-auditor. Scope: narrow (4 questions from the lead). Not opened by instruction: any Samsung score/run folder, `runs/prereg/SCORED.jsonl`, `runs/pc1_g0_synth/summary.json` and `draws/` (draws/ held 0 files when listed; contents not read).

## Verdict: PASS WITH CONDITIONS

No criterion is missing. Conditions (C1-C4) are disclosures and one clarification, none changes a registered rule.

## 4. Freeze integrity (met)
- HEAD = c6a89b6b2125a0ccb5b6170538fe7d43c018d2ba (c6a89b6).
- `git status --porcelain --untracked-files=no -- code runs/prereg` returns 0 lines.
- `runs/pc1_g0/` is outside `code/` and `runs/prereg/`, so the new configs do not breach the freeze check (PREREG_v4 18 step 6).

## 1. Config against the registered text (met)
Files: `runs/pc1_g0/configs/pc1_g0_shard{0,1,2}of3.json`. The three differ only in `h7.shard` ([0,3], [1,3], [2,3]); same run_id `pc1_g0_synth`.

| Field | Config | Registered | Status |
|---|---|---|---|
| mode / dataset | h7 / synthetic | PREREG_v4 13 line 454 `mode: h7` | met |
| gens | ["G0"] | G0 only (v4:453, 458) | met; run.py:233-235 also refuses anything else under R2 |
| n_draws | 20 | 20 draws (v4:458) | met |
| arms | A1, A2, A4 | "A1, A2, A4" (v4:456), 3 arms (v4:458) | met; h7.py:113,129 uses `arms` when `arms_by_gen` is None; run.py:332 passes `arms` through |
| n_trials / inner_k | 8 / 2 | pilot effort 8 x 2 (PREREG_v3:267) | met |
| design | n_cyc_cond 40, n_sto_cond 19, reps 3 | 40 + 19 with replicates (v4:454); equals build_v1 `h7_batch_shard0of3.json` | met |
| steps_scale | 1.0 (top and h7) | V3 16 scaling; same as build_v1 | met |
| backbone | default `self_limiting` (run.py:36, 336), as build_v1 | not stated for H7 | same as build_v1 |
| resume | true | n/a | met (h7.py:131 skips finished units) |

Differences from build_v1 (as intended, all follow v4): no G1/G2, no A8, no A11/A12, `arms_by_gen` absent, `design: "R2"` set at top level (build_v1 batch lacks it; run.py:225-235 then requires G0 only, which holds).
Determinism and sharding: units are (G0, i), i = 0..19; shard k takes units with index j % 3 == k (h7.py:126-128). Each unit uses `make_synthetic(seed=i)`, `split_conditions(..., i)`, `tuning.tune(..., seed i)` (h7.py:81-93), so a unit's result depends only on i, not on shard or order. `aggregate` (h7.py:139-163) writes summary.json only when all 20 unit JSONs exist; the shard that finishes last writes it. Partial shard returns `complete=False`. The `SYNTHETIC` flag file is written (h7.py:119).
Note (harmless): run.py:331 names `config.json` for the first shard to arrive and `config_shardKofN.json` for the others, so config.json may be any of the three shard configs.

## 2. Gate G reads PC-1 correctly (met, with C1 and C2)
- v4 text (PREREG_v4:345): PC-1 = structured arms recover with nRMSE <= 0.15; the V3 "and beat A11/A12" part is struck (RT F11); v4:622, 676 and PREREG_v4_REPORT:25 agree.
- Code `stats_step.build_controls` (373-395): `P1_G0_nrmse_leq_0p15` = all of A1 and A2 have median-over-draws nRMSE <= 0.15 on G0. `gate_g` (413-427) trips on `False` only ("PC-1 failed"). The A11/A12 test (`p1_positive_control`, h7.py:230-244) is computed only into `P1_full` and returns `passed=None` here; `gate_g` does not read `P1_full`/`P1_passed`, so its absence is neither a trip nor "not evaluated". `not_evaluated` lists PC-1 only if the value is `None`, which happens only if `h7_run` is absent or has no G0 draws.
- `aggregate` -> `verdicts` (h7.py:182) runs with G0 only: G1/G2 branches are skipped; `P1` is `passed: None` (harmless, informational).
- C1: v4 13 (v4:456) says the pass rule applies to "the structured arms (A1, A2, A4)"; the code gates on A1 and A2 only (the same tuple as V3 P1_ARMS). A4 is run and recorded in the summary but cannot trip the gate. This is a code/text mismatch in the lenient direction. It cannot be fixed (frozen code). The report must state PC-1 as computed (A1, A2) and print the A4 median beside it. If A4 median > 0.15 it must be disclosed, not ignored; whether that then trips gate G is a user decision in the ledger, not the lead's.
- C2: v4 does not say median versus every draw; the code uses the per-arm median over the 20 draws (as V3 verdicts, h7.py:177-179, `PASS_NRMSE`). Disclose "median over 20 draws" as the operational reading.

## 3. Consistency with PREREG_v4 (met, with C3 and C4)
- It is a registered step run late, not a rule change: v4:13, :10 (PC-1 gate input) and the 18 order list (v4:483 "Synthetic G0 ... before any real fit") already require it; all parameters equal the registered ones, no threshold, arm, size or metric was changed (stop rule 7, v4:449 and 18 step 7 not engaged).
- The design is data-independent: the synthetic generator uses round constants, not Samsung statistics (v4:455), so scoring order cannot leak into this run. No test-fold read: mode h7 is synthetic only (run.py:327-328).
- C3 (disclose): the registered order (v4:483 step 2, "before any real fit") was not followed: G0 runs after the Samsung folds were scored. The run was missing from the campaign list (`run_campaign.py` config_list, 276 configs, none h7), so the omission is a procedural gap. Disclose in the deviations log/report: what was omitted, when found, when the G0 run was launched (2026-11-12 ~05:3x), that its configs match section 13, and that the result was unseen by the lead until after this verdict.
- C4 (disclose): the pc1 configs are not in `FROZEN` `config_sha256s` (v4:18 step 2 lists every confirmatory run config; the synthetic run needs no guard). Record the sha256 of the three config files and the code commit c6a89b6 in the ledger. A negative PC-1 result trips gate G (v4:356, stop rule 3: no title, no claim) and must be reported as such, with no rerun on other seeds, trials or arms; a rerun with changed settings would be a rule change.
- Procedural: the run needs the full 20 units from all three shards before summary.json exists; `run_stats_v4` strict refuses to run without `h7_run` (stats_step.py:796) and must be pointed at `runs/pc1_g0_synth`.

## Conditions
C1 state PC-1 as A1/A2 per code and print A4's median; C2 state the median-over-draws reading; C3 disclose late execution and the omission from the campaign list; C4 record config hashes and forbid any rerun with changed settings. Gate tick: gate itself is not ticked or unticked here (narrow scope); this verdict permits using `runs/pc1_g0_synth` as `h7_run` once complete.
