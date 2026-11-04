# Lead's first prior-art scan (2026-11-04, 21:00)

Reading depth: **search snippets and abstracts only (E1)** from Exa, not readings. Every item must
be read in full before it is used in a decision or the manuscript.

## A. PINN + KAN for SOH: crowded, and the closest group is USTC-AI4EEE
| Work | Venue | What it claims (from abstract) | Data |
|---|---|---|---|
| PIKAN, USTC-AI4EEE (github.com/USTC-AI4EEE/PIKAN) | paper venue to be found by the code reader | KAN SOH estimator (SHEM) + KAN degradation-dynamics module (DDMM), "co-evolution"; symbolic regression gives explicit SOH mapping and degradation equations "structurally similar to electrochemical models"; small-sample and transfer gains (up to 63.4% RMSE reduction) | XJTU, TJU, MIT, HUST |
| PGKAN, Zhao, Peng, Liu, Huang, Zhao, Li | **J. Energy Storage 2026, doi 10.1016/j.est.2026.124768** | dual module (SOH estimator + degradation mechanism surrogate with adaptive PDE); "reveals the dominant degradation PDEs governing each dataset"; spline feature importance; symbolic expression per activation; MAPE 8.5-19.7% better than existing methods | 387 cells (XJTU, TJU, MIT, HUST) |
| PI-EKAN, Abebe et al. | Energy and AI 2026, doi 10.1016/j.egyai.2026.100928 | Wang-2024-style F and G networks, both Efficient-KAN; Bayesian-optimised partial-charging window; cross-chemistry | several datasets |
| KAN-PINN (Verhulst), Liu Z. et al. | Energies 18(22) 5865, 2025 (Shlok's ref [15]) | KAN replaces MLP in a PINN with a modified Verhulst ODE residual; data randomly shuffled before split (possible cycle-level leakage) | one public dataset |
| PIKAN-D, Liao, Deng, Hu | Energies 19(16) 3742, 2026, doi 10.3390/en19163742 | explicit Verhulst residual + DeepHPM implicit dynamics; uncertainty-weighted multi-task loss; SOH and RUL | MIT-Stanford-Toyota, 124 cells |
| SOH-KPINN, Li H. et al. | Measurement 259, 119769 (Shlok's ref [1]) | wavelet KAN + physics-informed, multiscale | to read |
| KAN functional relation discovery (arXiv 2604.00400) | preprint | 1-layer KAN on temperature data gives closed-form SoH(k); single VAH17 eVTOL cell | 1 cell |

**Implication:** "replace the MLP of Wang et al. 2024 with a KAN, add symbolic regression, claim
discovered degradation equations" on XJTU/TJU/MIT/HUST is already published, twice by one group,
once in JES itself. A JES reviewer will hit any paper that repeats it. Our novelty must be elsewhere.

## B. Stress-dependent degradation laws (non-KAN prior art a reviewer will expect)
- Gasper et al., J. Electrochem. Soc. 2021 (doi 10.1149/1945-7111/abdde1) and 2022 (doi
  10.1149/1945-7111/ac86a8), NREL: bilevel optimisation + symbolic regression identifies
  reduced-order life models; "rediscovers" Arrhenius and Tafel-like terms; bootstrap uncertainty;
  state-equation form for dynamic stress. **Strong baseline and strong prior art.**
- Schofer et al. 2022 (Adv. Sci., PMC9561774): genetic-programming symbolic regression for life
  models over stress factors, 104 automotive cells; reports gains over semi-empirical models.
- Kuzhiyil et al., Applied Energy 2024 (doi 10.1016/j.apenergy.2024.123692) and 2025 (doi
  10.1016/j.apenergy.2024.125221), Warwick: universal differential equations for battery models and
  calendar ageing.
- arXiv 2410.14347: NeuralODE/UDE on the Sandia NMC set (15/25/35 C, DOD windows, 0.5-3C).

## C. Open questions for the debate (not decisions)
1. What does the "physics" in the Wang-2024 family actually do? The residual u_t - G(t, x, u, u_t,
   u_x) with a free network G may be satisfied trivially; is there evidence it constrains anything?
2. Are the "discovered equations" of PIKAN/PGKAN identifiable (same law across seeds, folds and
   training cells) and predictive (do they forecast anything they were not fitted to)?
3. All of family A estimate SOH from current-cycle features (estimation); few forecast a future
   trajectory or RUL of an unseen cell from early cycles plus its operating condition (prognosis).
4. Stress-factor datasets (Sandia, ISU-ILCC, Oxford, TJU temperatures, MIT protocols) let a
   law be tested against known physics (Arrhenius, Ah-throughput power law); family A does not use
   operating conditions as inputs to the dynamics.
