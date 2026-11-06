# Coder queue before the freeze (lead, 2026-11-05 23:55). Start after pilot P6 finishes (P6 imports code/pinnkan).

1. **C26 red-team re-check** (debates/D022_datasets_kan/09_redteam_fallback_recheck.md, 3437b4d): fix N1 MAJOR (gate reason
   "PC-1 failed (G0 recovery nRMSE > 0.15)" trips the banned-stem check `recover\w*` in stats_step.py:575-576, so a tripped
   Gate G writes no contrasts/controls; the diagnostic must be reported, not crash), B1 (`_licensed({"verdict": True})` still
   licenses), the partly fixed A4, B2, B5, and minors N2-N5 as the re-check proposes. Tests per finding. Then the red team re-signs.
2. **C12** pp-scale margins per contrast and grid cell (`margins.json` procedure; PREREG 9.2, 9.10).
3. **C13** `runs/prereg/blinding_exclusions.json` and the scorer's exclusion list (3.3(11)); copy
   `runs/prereg/samsung_splits_v2.json` to `runs/splits/` with hashes unchanged.
4. **C14** confirmatory config set (one per outer fold and arm group; every Samsung grid config carries
   `window: {"k_cycling": 4, "k_storage": 2}`, N = 20 unless FB-8 changes it, `extraction_audit_sha256` / `calibration_rule_sha256`
   as run.py demands) and the five item (f) configs regenerated to match them (runs/item_f/configs/).
5. Full suite, one pytest process per file; commit; independent review of the batch.

## Added 2026-11-06 (after C26 round 3, bc9e4c4: SIGNED; minors only)
6. N2: banned-wording check misses sentences split at ";" or ":", "not unlike", double negation and formulas such as exp(-b/T).
7. N5: the physval check sits only on the v3 `run_stats` path; attach it to the R2 confirmatory CLI path (`run_stats_v4`).
8. N6: designer: PREREG 11a item 6 text gets the T carve-out the code already applies (text tightening only; section 11 untouched).
9. 17.2 C26 row wording: "fixed" -> per-finding status as in 09_redteam_fallback_recheck.md round 3 (designer, final-text pass).
