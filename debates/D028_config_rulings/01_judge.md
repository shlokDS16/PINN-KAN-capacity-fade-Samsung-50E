# D028 judge: rulings on the C14b confirmatory config set (2026-11-06)

Read: `CODER_BATCH_REPORT.md` (7438718), D027 review, PREREG_v4 3.3, 3.4, 4.1, 5, 7.1, 9.4-9.5, 9.8, 9.9, 12, 15, 16, 18;
`make_confirmatory_configs.py`; `run.py` 147-245; `zyk.py`; `fb5_validation.json`; RESULT.md C4; D016 judge 6, D024, D025.
No fit run, no retention value or score opened.

## (a) `"throughput": "zyk"`: correct
FB-5 accepts analytic throughput only if median |rel. diff| <= 5 % and no cell exceeds 10 % at its last check-up. Ruled
validation: 134 cells, 1472 pairs, coverage met, median 0.203, 86 cells over the last tolerance, `accept_analytic: false`.
ZYK applies to every cycling cell; no fallback flag is right (missing-file intervals take designed throughput, 3.3(4)). Gap:
the ZYK table is git-ignored, so no hash covers it (C1). **FB-8 timing must run a pinned primary config (zyk, tournament, k grid).**

## (b) Override checks in `validate_config`: accepted
`_check_overrides` runs there and again in `run()`, which still wraps `_run` in `law.overrides`. Only error order changes.

## (c) Arm lists
- **Downgrade rows (ii), (iii):** confirmed; each cell holds every arm of every gated and secondary contrast there (P1-P3 via
  D\*, K1, K2, Q-A10 both forms, Q-H, Q-T at g1). AG is estimated only. Row (iv) = 9.8 text.
- **9.9 descriptive rows:** PREREG silent; confirmed A1 A9 A11 A12 A10 A10P at g1, g4 (windows g4 only): this covers chain P
  and Q-A10 (RT F8); A2, A13, A15, G15 would add neural refits to rows without consequence. (k), (l), (m) follow the text.
- **Test A** A1 A2 A9 (7.1): confirmed. **S3:** silent; confirmed A1 A9 A10 A10P (storage transfer like S2; both A10 forms
  primary, 7.2).
- **ISU "full-data analogue": replaced by the unthinned training side.** On Samsung m = 32 is unthinned (4.1), so g4 is both;
  ISU folds train on about 50 of 63 conditions, so m = 32 would thin. "Full-data" is the PREREG's word, SNL (about 18 training
  conditions) could never mean m = 32, and (32, 4 weeks) belongs only to the fallback grid 3.4 (i). Scarce (m 8, W 2 weeks):
  confirmed. C2.

## (d) The eight items
1. **First-CU reference row: strike.** Optional (D024), a full re-run of every arm, window origin unspecified; Q0 = ET_T23 stands.
2. **Forecast-failure row 3.3(8): strike.** Under the D025 cap every Samsung cell keeps at least one post-window check-up
   (minimum 3 intermediate), so the scored set is empty and no forecast times exist; the cap already keeps short-record cells.
   The matching ISU/SNL sentence of 3.4 goes too.
3. **(n) separate h_cal/h_cyc: strike.** Needs a new law parameterisation; not small.
4. **(p) second TPE seed: build.** Key `tpe_seed` (None = outer fold, as now); only `TPESampler(seed=)` changes (tuning-fit
   seed and inner folds unchanged). Row: g1, A1 A9 A11 A12, folds 0-4, `tpe_seed = 100 + fold`; last in drop order (about one
   item (f) set of CPU).
5. **(t) A10 without SOC = 100 % storage: build.** Key `a10_drop_soc100_storage` (False): A10/A10P fit without training storage
   cells at SOC 1.0; other arms' training sets and the scored set unchanged. Row: A1 A10 A10P, g1 and g4, folds 0-4.
6. **A14: strike.** Cut by 7.1 under R2 and refused by `run.py`; 15 step 6 and 12 rule 5 are leftovers.
7. **SNL replication: strike.** No scarce SNL window was fixed; choosing one now on non-blind data is a new design choice;
   EXT-PL/EXT-NA hold the optional slot first.
8. **ISU fallback grid: lapsed.** Samsung was parsed 2026-11-05 (RESULT.md, 42c2a84), before 07 Nov 09:00.

## Actions
**Coder** (then regenerate, `--check`, full suite, update the strike list in `CODER_BATCH_REPORT.md`):
- C1. `zyk_table_sha256` in every Samsung zyk config (generator hashes `zyk.ZYK_TABLE_REL`); `validate_config` requires a
  64-hex value; `data._load_samsung` raises `ConfigError` on mismatch before use. Tests: wrong hash refused; all Samsung
  configs carry the on-disk hash; item (f) configs inherit it.
- C2. `replication_configs`: g4 configs become `repl_isu_B_f{f}_full`, `m` unset, `k ["full"]`. Test: no `m`; window = 4 weeks.
- C3. `tpe_seed` (tuning.py 81, 97; run DEFAULTS; `validate_config`: None or int >= 0); configs `sens_tpe2_B_f{f}_g1`. Test:
  default gives `tpe_seed == fold`.
- C4. `a10_drop_soc100_storage` (semi.py fit path; DEFAULTS; refused without A10/A10P); configs
  `sens_a10nosoc100_B_f{f}_{g1,g4}`. Test: A10 training set lacks SOC 1.0 storage cells, A1's unchanged, scored ids equal.
- C5. `forecast_failure` stays refused; message says "struck (D028)".

**Designer (PREREG rev. 13; section 11, 9.4-9.5 and 9.8 rule 2 untouched):**
- T1. 3.3(8), its 9.9 (i) entry and the 3.4 sentence: struck (superseded by the D025 cap).
- T2. 9.9: first-CU row and (n) struck; (p) and (t) carry the specs above; one sentence giving the descriptive-row arms and cells.
- T3. 3.4 (ii): ISU only; scarce = (m 8, 2 weeks); full-data = unthinned, 4 weeks. 3.4 (i): "not triggered (parsed 2026-11-05)".
- T4. 7.1 "Arms by test": "S3 (exploratory): A1, A9, A10 (both forms)". 15 step 6 and 12 rule 5: delete A14; "ISU replication".
- T5. 17.1 FB-5: met (fb5_validation.json sha256 d3d45fb5...; zyk in every Samsung config; table hash pinned).
- T6. Change-log row rev. 13 for T1-T5, and the appendix sentence: "Four rows were not run (first-check-up reference, forecast
  failures under the window cap, separate h_cal/h_cyc for A2, SNL replication); none was a downgrade row."
