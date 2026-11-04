# PGKAN (Zhao et al., JES 182, 124768)

**Citation.** H. Zhao, B. Peng, L. Liu, J. Huang, L. Zhao, B. Li, "Interpretable physics-guided neural networks for state of health estimation of lithium-ion battery", J. Energy Storage 182, 124768 (issue 2026-12; online 2026-09-25 per Exa), DOI 10.1016/j.est.2026.124768 (verified on Crossref). State Grid Anhui Electric Power Research Institute; USTC; China Electric Power Research Institute. Open access (CC-BY, hybrid) per Unpaywall/OpenAlex. Code announced: https://github.com/USTC-AI4EEE/PGKAN ("will be available"; not checked).

**Reading depth: abstract only.** The published-version PDF is on ScienceDirect (CC-BY) but a script request returns HTTP 403 and no repository copy exists (Unpaywall lists only the publisher copy). I did not try to bypass the check. **Shlok can save it in a browser at no cost: https://doi.org/10.1016/j.est.2026.124768**

## Claim structure (abstract)
Sequence: reliability and transparency problem; one named method (PGKAN, a "dual-module coevolutionary architecture": SOH Estimator with KAN + Degradation Mechanism Surrogate with an adaptive PDE); headline "MAPE reduced by 8.5 % to 19.7 %" on "four public datasets encompassing 387 batteries" (the same four PINN4SOH sets: XJTU, TJU, MIT, HUST); then three interpretability claims: DMS "reveals the dominant degradation PDEs governing each dataset"; spline-based feature importance "aligns with the key terms in the discovered PDEs"; symbolic regression on each activation gives "an explicit, symbolic degradation expression". Number of claims: 1 accuracy + 3 interpretability.

## Figures and tables
Unknown. Do not fill FIGURE_FORMS until the body is read.

## Hooks for us
- Same group as PIKAN; a second KAN-plus-PDE paper from USTC in JES within months. A JES reviewer will know both; our introduction must place the work against both as estimation methods on feature tables, not forecasting on stress-labelled cells.
- "Reveals the PDE" is the interpretability standard that reviewers now expect from KAN papers; our equivalent is learned stress functions with seed envelopes plus a GAM comparison, which is a stronger, testable form.

## Shlok must save by hand
Yes (priority 1 of exemplars; free via browser, CC-BY).
