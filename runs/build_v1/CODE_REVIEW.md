# CODE_REVIEW: pinnkan build_v1 (static review, 2026-11-05)

Reviewer: independent code-review agent (static read of code/pinnkan/*.py, code/run_pinnkan.py, PREREG_v2,
code/README.md, runs/build_v1/RESULT.md; tests not run by the reviewer). Saved by the lead verbatim in
substance because the reviewer had no write tool. Result: no blocker, 4 major, 8 minor.

## Checked and found correct
- Train view: data.py load_split removes test cells before any array is built; scaling uses fixed physical
  ranges; collocation hull, t_max, init_levels, backbone tournament, inner folds and P3 standardisation use
  training cells only.
- tuning_done.json and margins.json are written before any test cell is scored.
- Window inference: all arms (A1, A2, A9, A10, A11, A12, R1, R2) use only window labels and the causal EFC
  curve (window-mean rate after the window).
- Physics: residual is autograd d/dt of F(t, s, z) w.r.t. t; nu = rate * t_scale / efc_scale consistent for
  Samsung, ISU, SNL; F(0) = 0 by construction; closed-form drive-to-state inverse correct for all three
  backbones; Arrhenius sign correct; rates positive (exp); 25 C reference only reparametrises.
- Metrics: cell RMSE in pp, condition mean, mean over conditions; log_ratio = ln(S_comp / S_PINN); R2
  argument order correct.
- Seeds: all RNGs seeded (refit 0-4, tuning 1000 + fold, TPE seed = fold).

## Findings
**M1 (major): split-hash check never blocks and checks the file only against itself.** data.py:349-352,379;
run.py:154-155. A regenerated folds block only logs a warning (fold_hash_ok False); the stored hash is in the
same file, so a regenerated file passes. Fix: raise on mismatch; compare sha256 of the file and fold hash
with values pinned at freeze; assert loaded conditions = split's train_cycling_conditions + storage
conditions (loader currently fail-open: "not in test"). S3 has no hash.

**M2 (major): FROZEN is only a file-exists check; a scored test run can be replaced.** guard.py:23;
run.py:131,161-162. Creating FROZEN opens everything; clean tree, pinned commit, prereg hash and grids not
verified (git.json only records a dirty tree); overwrite: true or a re-run replaces a scored outer-test run
(stop rules 4 and 6); steps_scale < 1 accepted on real data. Fix: FROZEN holds JSON (commit, PREREG and split
sha256, config hash), guard verifies them and a clean tree; refuse overwrite, steps_scale != 1 and a second
test scoring of the same config.

**M3 (major): target_kind defaults to "cycling", so S2/S3 are tuned on the wrong task.** run.py:35,181,183,190;
tuning.py:33,52. A config with test S2 or S3 that omits target_kind tunes on held-out cycling conditions and
scores storage cells. Fix: derive from the test name (S2/S3 -> storage); assert scored kind = tuned kind; add a
test and a README row.

**M4 (major): the negative control of prereg section 10 (gate G) is not implemented and not listed as a stub.**
run.py; code/README.md "Stubs". No stress-permutation mode; r2_pooled, horizon_errors, rul_error, MAPE defined
in metrics.py but not called from run.py. Fix: add a permute-stress option (permute separately in train and
test, window data untouched); list it and the unwired metrics in the stubs.

**m1: QC outlier rule non-causal.** code/data/samsung_checkups.py:490-498: whether the last window point
survives depends on the first post-window capacity (neighbour range, 1 %). Fix: preceding neighbours only,
or disclose.
**m2: ISU/SNL forecast-time list encodes the 70 % crossing.** data.py:146-150. Fix: label-free query grid or an
invariance test.
**m3: reference capacity chosen per cell (ET_T23 if present, else first CU)**, conflicting with prereg 3.3(2).
samsung_checkups.py:509-516; data.py:210. Fix: one ref_kind for all analysed cells.
**m4: nan_to_num(e - e[0], nan=0) can make cumulative EFC non-monotone**; same-day check-ups give zero-width
intervals. data.py:218. Fix: forward-fill, enforce monotone, assert np.diff(efc) >= 0.
**m5: collocation draws in invert_pinn depend on batch position.** pinn.py:182. Fix: per-cell seed from a hash
of cell_id and seed.
**m6: A11/A12 may train on fewer cells** (prepare_many drops cells with too few window points; with shift=-1,
k_sto=1 gives w=1 < 2, so all storage cells drop for A11/A12). arms.py:167; data.py:144. Fix: same cell filter
for every arm, or document.
**m7: catch=(Exception,) hides arm-specific trial failures** (tuning.py:89); equal-budget rule not enforced.
Fix: cap n_failed; redraw failed trials so every arm gets N valid ones.
**m8: smaller inconsistencies:** baselines.py:70 LightGBM mono=True vs README decision 9 (no monotone
constraint); SNL t_index=None so inner folds not temperature-stratified (specs.py:82, tuning.py:38);
auto_budget writes budget_rule.json after tuning instead of fixing N before (run.py:198); log_ratio silently
intersects condition keys (metrics.py:95): assert equal key sets.
