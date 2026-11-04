# Edits queued for PREREG_v3 (the version to be frozen), collected 2026-11-05 02:12

Apply together with the freeze blockers FB-1..FB-8 of PREREG_v2 section 17; each edit names its source.

1. **D013 C5** (prereg text): section 7 backbone sentence (one h), optimiser recipe paragraph (grad clip 20 on
   A1, A2, A9 and every gradient-trained arm; residual warm-up 0.4), A5 pair sets per dataset (SNL: 7 pairs);
   section 7.2 scope sentence of the A10 factor; 11a item 4 counterfactual calendar-share definition.
2. **D013 C6** (sensitivity rows 9.8): (k) clip {10, 50}, warm-up {0.2, 0.6} for H1a; (l) delta scope "total";
   (m) A2-only tournament sensitivity Y0 {0.5, 2}, gamma {0.15, 0.6}, TAU {0.075, 0.3}; (n) optional "separate
   h_cal and h_cyc" appendix row, descriptive, CPU permitting.
3. **D013 C3**: lam_res grid includes 1e-3 (confirmed by the lead, DECISIONS D013 note).
4. **D013 C8/C9** (paper wording and disclosure sentences): "single state-dependent modulation"; "three
   prespecified pairs"; SNL charge-rate sentence; A10 flexibility sentence; synthetic-circularity sentence;
   optimiser recipe and SNL pairs fixed without Samsung data.
5. **Code review m1 (lead ruling 02:12):** the Samsung capacity outlier rule (code/data/samsung_checkups.py,
   neighbour range 1 %) is made causal: a check-up is compared with preceding check-ups only, so window
   membership never depends on a post-window label. Small effect, same for all arms; stated in 3.3.
6. **Code review m6 (disclosure):** A11/A12 drop storage cells with fewer than 2 window points at k-1; the
   number of training cells used per arm (n_train_used) is reported in the E5 row; no claim of identical inputs
   for A11/A12.
7. **D012:** primary test = exact one-sided sign test on ln(S_comp/S_PINN) per held-out condition (median
   estimand); Test C descriptive; sign-flip p-values reported nowhere as primary (the run code's placeholder RNG
   seed for the sign-flip p-value is irrelevant to primary inference; fix or drop the field).

8. **Figure inputs (figure-smith, 1a8c95f):** the run writer / statistics step must emit window.csv,
   stress_functions.json, residual_map.npz, superposition.csv, contrasts_<test>.json, reference.json,
   controls.json and the H7 summary.json (formats in code/figures/README.md); PREREG_v2 section 9.3 still
   names the sign-flip rule and must say sign test (D012); Fig. 4 shows median ln-ratio with exact
   order-statistic interval plus a mean paired pp column (BCa), tiers read from the statistics step.
9. **Smoke re-run** of runs/build_v1 at the freeze commit (code changed after the smoke runs).
10. **D014 (negative control):** replace PREREG_v2 section 10 gate G with NC-1 (label invariance, gating) and NC-2
    (stress-permutation sign test on Test B, non-gating); seed rule SeedSequence([20261105, crc32(label)]);
    apply section 6 of runs/prereg/NEGCONTROL_RULING.md.
