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
