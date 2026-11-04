# SYNTHESIS A - refs 11, 23, 29, 33 (physics-informed KAN, stress-dependent degradation laws, identifiability)

(Full main text of all four read; 33 Supplement not read; 11 is the preprint.)

1. **Nobody shows the learned function.** Jarraya (11) never plots a spline; Wang (33) never inspects G; Yuan (23) has no physics. Liu (29) uses learned edge functions as its main evidence (Fig 4.1, 2.4). Learned stress-response curves with spread over cells and seeds are novel here and the accepted KAN evidence form.

2. **"Physics" is a loss name, not a law.** In 33 G is a free MLP that can satisfy the residual by copying u_t (code note); 11 has none. Identifiability (recover a known law from synthetic cells, then real cells across seeds and folds) is untested in all four; Liu treats seed-dependent pruning as a remark (Appendix C).

3. **Controls are missing.** No physics-term ablation in 33, no SSL-term or supervised-pretraining control in 23, no KAN-removed LSTM in 11; 29 uses vanilla-LBFGS MLPs and reports the lowest test loss over seeds and depths. Factorial ablations, tuned equal-parameter MLPs and validation-based selection differentiate us.

4. **Thin, unreplicated evidence.** Single runs (11, 23); 10 repeats of one split with 2-3 test cells per batch (33); 3 seeds, best-of (29). Cell-fold spread with at least 5 seeds is a clear step up. 23 and 33 share the same 16 charge-window features.

5. **Shortcuts inflate headlines.** 11 feeds the previous-cycle capacity with an in-cell split; 33 scales per cell with whole-life min/max including t; 23 validates inside training cells. Our inputs exclude label history.

6. **KAN should not be expected to win on accuracy.** 29 finds KAN and MLP "comparable" on smooth monotone Feynman laws and KANs about 10x slower. Rate laws in stress are that regime, so the claim is interpretability and identifiability, with compositional structure (exp/log edges, product of power laws; p.20) as mechanism.

7. **Symbolic extraction needs noise-free targets.** 29's snap-and-retrain reaches machine precision on synthetic data; on the knot signature it yields non-unique formulas B-F of differing accuracy (Table 4). Report a formula Pareto set and a noise-level sweep.

8. **Figure forms to use.** Parity plus violin (33 Fig 4), violin with raw points and a horizon heat map (23 Fig 14-15), staircase diagnostic (29 Fig 2.3), edge-function grid (29 Fig 4.1), limits decision tree (29 Fig 6.1). Avoid 24-panel curve grids (23 Fig 8).
