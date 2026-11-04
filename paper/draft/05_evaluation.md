> **DRAFT, outcome-independent section. The claim is not frozen. The text states the preregistered plan (`runs/prereg/PREREG_v2.md`, the queued v3 edits and decisions D009 to D013). No result appears; `[RESULT: ...]` marks where one goes.**

# 5. Evaluation protocol

## 5.1 Splits

Splits are by cell and, for cycling tests, by condition: no cycle of a test cell and no cell of a test condition is seen in training or tuning. They are generated from identifiers only and hashed before scoring.

*Test B (primary).* The 40 cycling conditions form five folds of eight, stratified over temperature and stress. All storage cells are always in training.

*Test C (secondary): a held-out temperature-laboratory domain.* All 13 conditions at 35 C (39 cells, all from laboratory INT) are held out; training uses cycling at 23 and 45 C (27 conditions, 108 cells) and all storage cells. Laboratory and temperature are aliased, so Test C is never called temperature extrapolation, the title omits 35 C, and any abstract sentence on it adds that the two cannot be separated in this design. INT cells at 23 C stay in training, which separates them only if there is no laboratory-by-temperature interaction.

*S2 (secondary): storage transfer.* The 19 storage conditions form five folds of consecutive state-of-charge blocks within each temperature, with all cycling cells in training; only cells 01 to 03 are scored, and results are also given for state of charge up to 0.8. Leave-23-C-storage-out and held-out replicates are exploratory. ISU and SNL use the Test B design on their own conditions (63 and 23), cyclic term only.

## 5.2 Endpoint

The window is $k$ check-ups (Section 4.1), with $k-1$ and $k+2$ as secondary windows. A cell's forecast set is every later regular or extended check-up that survives quality control. The primary endpoint is the retention RMSE in percentage points over that set, averaged within condition and then over conditions, after each condition's score is averaged over the five seeds. The unit of analysis is the held-out condition, with equal weight. Secondary endpoints are error by horizon, remaining-useful-life error for cells that cross 80 %, MAE, MAPE, $R^2$, run time, parameter count and the share of non-finite forecasts (scored with the persistence error and counted). The replicate spread is computed on training sides as a descriptive reference and is never a margin or gate.

## 5.3 Contrasts and test

For comparator $m$ and held-out condition $c$, let $S$ be the condition score and

$$ L_{m,c} = \ln\bigl(S_{m,c}/S_{\mathrm{A1},c}\bigr), \tag{8} $$

so that $L>0$ favours the PINN-KAN. Each contrast is tested hierarchically at one-sided level 0.025. *Tier N* (non-inferior) requires $\operatorname{med}(L) > -\ln 1.10$, so the PINN-KAN is at most 10 % worse. *Tier S* (superior) requires $\operatorname{med}(L) > \ln 1.02$, so the comparator is at least 2 % worse. N is tested first and S second at the same level, and the label is S, N or none. The test is the exact one-sided sign test [@dixon1946sign] on $L_{m,c}$ minus the margin; the estimand is the median condition, with an exact order-statistic 95 % interval [@thompson1936median], and the abstract speaks of the typical held-out condition. Beside every tier we report the mean paired difference in points with a bias-corrected and accelerated bootstrap interval [@efron1987bca], the geometric-mean ratio and the share of conditions won. A point-scale tier uses margins $0.02E$ and $0.10E$, where $E$ is the comparator's inner-CV score on the training conditions; they are written to `margins.json` before any final refit meets a test condition. If the two scales disagree, both are reported.

A studentized sign-flip permutation test was preregistered first. Its simulated rejection rate exceeded the acceptance limit of 1.2 times nominal (worst ratio 1.86 at $n=40$ and 2.14 at $n=13$), so the preregistered fallback, the sign test, is used. At $n=40$ and the first Holm step, 80 % power detects a median improvement of about 9 to 12 %, 12 to 16 % and 17 to 22 % when the arms' condition errors correlate at 0.95, 0.90 and 0.75 (assumed, not measured). Thirteen conditions are too few for such differences, so Test C is descriptive. <!-- src: runs/prereg/TYPE1_SIGNFLIP.md; DECISIONS D012 -->

## 5.4 Hypotheses, multiplicity and gates

The primary Holm family [@holm1979] has three members, each against A1: **H1a** (A9, no residual), **H1b** (the stress-map pool of Section 4.4) and **H6** (A10, the dataset authors' model). Holm levels $0.025/3$, $0.025/2$ and $0.025$ are assigned by ordering the three N-tier $p$-values. Each S tier is then tested at its contrast's own level. **H1c** (A1 against the better of A11 and A12) is tested only if all three reach tier S; otherwise it is reported with its interval as "secondary, not tested". **H2** (soft residual against the hard law A2) is decided at a separate level of 0.025. Outcome A (soft better) is tested only if the family passes, C (hard better) is tested regardless, and B (equivalence at $\pm\ln 1.10$) comes last; any other result is called unresolved. **H3** (KAN against the better of A4 and A5) can be a win only if the validity rule of Section 5.5 holds. **H4** (Test C), **H5** (S2: A1 non-inferior to the best of A3, A9 and A10) and X1 (joint against cycling-only training) are secondary. ISU and SNL follow the same rules per set, unadjusted and never pooled with Samsung.

Wording follows tiers: "outperforms" only at tier S, "matches" never, "comparable" only after a two-sided equivalence test. Titles and abstract sentences are fixed in advance for every outcome, and every outcome is reported in the text, including those in which the residual, the KAN or the comparison with the dataset authors' model does not reach tier S.

## 5.5 Controls and synthetic recovery

*Negative control.* In each Test B fold, stress vectors with their design throughput are permuted among conditions, separately in the training and test sets, with window data untouched, and A1, A9 and R2 are rerun at the same budget. The control passes if the A9-minus-A1 contrast has mean $L<\ln 1.02$ with an unshifted two-sided $p>0.05$, and A1 does not beat R2 by more than the superiority margin. A failure signals leakage through something other than stress, and the analysis stops for audit.

*Positive controls.* On the well-specified synthetic generator G0, structured arms recover the log-rate surface with normalised RMSE at most 0.15. They also beat A11 and A12 in forecast RMSE (paired Wilcoxon test [@wilcoxon1945], 20 draws). G0 uses the model's own law, so this checks the implementation, not the physics. Two real-data checks are that the fitted calendar rate rises with temperature at every charge state inside the storage hull and that A1 beats persistence (R1) on Test B.

*Identifiability.* Synthetic generators use the real Samsung design. G1 misspecifies the time law, and G2 has a non-additive stress law (a charge-rate hinge with a temperature-shifted threshold and a DoD-by-SOC product). Recovery is the normalised RMSE of the log-rate surface on 500 Latin-hypercube points of the hull, with pass at 0.15 or below and fail above 0.30. A G2 draw discriminates only if the additive-spline class floor on the true surface exceeds 0.15; otherwise KAN superiority cannot be claimed from G2. The G2 strength was set after the pilot; the pilot strength is a sensitivity.

## 5.6 Sensitivity rows and physical checks

Appendix C recomputes each primary tier under about twenty changes. These include lab-stratified and two-stage bootstraps, per-laboratory and per-stage differences, a laboratory-and-stage indicator in the per-cell prior and A10 as published. Others retain every check-up, change the window, use logged throughput after the window, or change the margins, the clip, the warm-up and the modulation settings. If the laboratory-stratified tier is lower than the primary tier, the abstract says so.

Physical checks are descriptive, with no test and no claim beyond "consistent" or "not consistent". They cover the effective activation energy against the dataset authors' calendar fit on the same data (consistency, not independent validation), the storage rate above 80 % state of charge, calendar monotonicity in temperature and the share of predicted fade attributed to the calendar term. They also compare the signs of the cyclic partial dependences with those of the dataset authors' cycle model. Storage at 10 and 45 C is laboratory-confounded, which is printed with the activation-energy result. [RESULT: Figures 5 and 6]
