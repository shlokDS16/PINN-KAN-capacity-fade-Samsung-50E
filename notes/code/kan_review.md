# kan-review (AmirNoori68) — notes

reading: full text of the repo README (all 410 lines, `refs/code/kan-review/README.md`, commit 1c652f9a, 2026-07-24). The repo holds only README.md and LICENSE (MIT, (c) 2025 Amir). **The companion paper itself was NOT read** (Noorizadegan, Wang, Ling, Dominguez-Morales, "A practitioner's guide to Kolmogorov-Arnold networks", Computer Science Review 62, 100991; DOI 10.1016/j.cosrev.2026.100991 verified on Crossref, issued 2026-11, Elsevier, paywalled). Everything below is what the README catalogues, one-line "brief result" strings and link titles. They are E1 pointers (what the maintainers say a paper shows), not verified readings of the cited papers. Ask the orchestrator for an e-gateway download of the review if any statement below is to go into the manuscript.

The README is a link catalogue. It has **no prose** on training cost, noise sensitivity, or open problems. Those topics can only be inferred from which sections exist; I mark inferences as such.

## 1. Structure (section numbers = README headings)
1 Citation; 2 Kolmogorov superposition theorem history (table, 1900-2024); 3 review/survey papers (11); 4 representative repositories (about 55); 5 KAN vs MLP bridges; 6 basis functions (table); 7 accuracy improvement (7.1 physics and loss design, 7.2 adaptive sampling and grids, 7.3 domain decomposition, 7.4 function decomposition, 7.5 hybrid/ensemble, 7.6 sequence/attention hybrids, 7.7 discontinuities, 7.8 optimisation); 8 efficiency (8.1 GPU/JAX, 8.2 matrix and parameter-efficient bases); 9 sparsity and regularisation; 10 convergence, scaling laws, spectral bias.

## 2. KAN variants catalogued (README section 6, lines 180-206)
Columns in the README: name, support (local/global), equation, grid (yes/no), type.

| Variant | Support | Basis | Grid | Reference / code named in README |
|---|---|---|---|---|
| B-spline (original KAN) | local | sum_n c_n B_n(x) | yes | Liu et al. arXiv 2404.19756 and 2408.10205; pykan; many PDE uses |
| Chebyshev | global | sum_k c_k T_k(tanh x) | no | Sidharth 2405.07200; ChebyKAN; cPIKAN uses (Shukla 2406.02917 listed in 7.1) |
| Stabilised Chebyshev | global | tanh(sum c_k T_k(tanh x)) | no | Daryakenari 2504.07379 |
| Chebyshev (grid) / KKAN | global | T_k of mean of tanh(w_i x + b_i) | yes | Toscano 2412.16738 (MLP features plus basis expansion) |
| ReLU-KAN | local | squared ReLU bumps | yes | Qiu 2406.02075 |
| HRKAN, Adaptive ReLU-KAN | local | [ReLU(x)]^m | yes | So 2409.14248; jaxKAN (Rigas, JOSS 10.21105/joss.07830) |
| fKAN (Jacobi), rKAN (Pade/Jacobi) | global | Jacobi, rational | no | Aghaei 2406.07456, 2406.14495 |
| Jacobi-KAN / Legendre | global | P_i(tanh x) | no | Kashefi 2408.02950; Legend-KINN |
| FourierKAN, KAF | global | sin/cos; random Fourier features + GELU | no | Xu 2406.01034; Zhang 2502.06018 |
| Gaussian-RBF / FastKAN | local | sum w_i exp(-((x-g_i)/eps)^2) (+ SiLU residual) | yes | Li 2405.06721 (FastKAN); LeanKAN; Gaussian-KAN; PU-GKAN (partition of unity) |
| RSWAF-KAN | local | tanh^2 switch | yes | faster-kan code |
| CVKAN | local | complex Gaussian | yes | Wolff 2502.02417 |
| BSRBF-KAN | local | B-spline plus RBF | yes | Ta 2406.11173 |
| Wav-KAN | local | wavelets psi((x-u)/s) | no | Bozorgasl 2405.12832; Patra 2407.18373 |
| FBKAN | local | partition-of-unity of local KANs | yes | Howard 2406.19662 |
| SincKAN | global | sinc | yes | Yu 2410.04096 |
| Poly-KAN | global | polynomials | no | Seydi 2406.02583 |

Implementations named in section 4 that matter for us: pykan (official, KAN 2.0, has symbolic regression), efficient-kan (Blealtan, B-spline, L1 only), fast-kan (RBF), jaxKAN (grid extension, adaptive ReLU-KAN, residual-adaptive sampling), ChebyKAN, FourierKAN, Wav-KAN, KINN (solid mechanics PIKAN), KKANs_PIML, SPIKANs, torchkan (several variants), KANbeFair (fair KAN vs MLP benchmark).

## 3. What the README says about KANs in physics-informed learning (7.1, 7.2, 7.3, 7.4, 7.8, 10.2)
Brief results as stated by the maintainers (all unverified here):
- cPIKAN (Chebyshev PIKAN) with residual attention and entropy-viscosity: Shukla, arXiv 2406.02917.
- KINN for solid mechanics, singularities and stress concentrations: Wang et al., Comput. Methods Appl. Mech. Eng. 10.1016/j.cma.2024.117518.
- Loss design: self-scaled residual reweighting (Toscano 2412.16738); augmented-Lagrangian PINN-KAN with learnable multipliers (Zhang, Sci. Rep. 10.1038/s41598-025-92900-1); residual physics plus sparse regression (Guo, Physica D); holomorphic KAN trained on boundary conditions only (Clafa 2507.22678).
- Grids and sampling: multilevel and free-knot KANs (Actor 2505.18131); grid extension with optimiser-state transition and residual-adaptive sampling (jaxKAN).
- Decomposition: finite-basis KAN (FBKAN), separable PIKAN (SPIKAN, 2411.06286, for high-dimensional PDEs), temporal subdomains to improve NTK conditioning (Faroughi 2506.07958).
- Optimisation: Adam/RAdam warm-up then (L-)BFGS refinement (Mostajeran, Daryakenari, Zeng); Bayesian PINN-KAN (Giroux 2410.01687); Bayesian hyper-parameter tuning (Lin).
- KAN-ODE: a KAN as the right-hand side dot u of an ODE with adjoint training (Koenig 2407.04192); KAN-SR recursive simplification for symbolic discovery (Buhler 2509.10089); physics-informed KAN for high-index DAEs with a dual-network structure (Lou 2504.15806).
- GINN-KAN, "interpretable growth plus KAN in PINNs" (Ranasinghe 2408.14780): a growth-law prior inside a KAN-PINN; closest in spirit to the Verhulst step in PIKAN (battery).

## 4. Known KAN weaknesses — what the README points to (inference where marked)
- **Training cost / efficiency (section 8, 14 rows):** the existence of MatrixKAN (matrix B-spline evaluation), ReLU-KAN, PowerMLP, lmKAN lookup tables, FlashKAT and "dual-matrix + RFF compression" implies B-spline KANs are slow and memory-heavy; README gives no numbers. Our own measurement from PIKAN: the 17-60-60-32-32-1 efficient-kan network has 75,960 parameters versus 7,781 for the same-width sine MLP (PIKAN README table 7.3), a factor of about 10.
- **Spectral bias (10.2):** claimed *reduced* in KANs versus MLPs (Wang 2025, arXiv 2410.01803; Gao arXiv 2410.08041, NTK view). Farea 2025 (Comput. Phys. Commun. 10.1016/j.cpc.2025.109753): learnable bases widen NTK spectra with a reach/curvature trade-off. Faroughi 2506.07958: Chebyshev/cPIKAN keep better NTK conditioning. Rigas 2510.23501 (RGA-KANs): initialisation matters for NTK stability. For SOH regression with smooth monotone curves the spectral-bias question is mostly irrelevant; it matters for the capacity-regeneration spikes.
- **Grid extension / knots (7.2):** jaxKAN grid extension, free-knot and multilevel knots are listed as accuracy fixes, i.e. fixed uniform grids on [-1,1] are a limitation. PIKAN uses a fixed grid of 5 (efficient-kan) or 3 (pykan) and never refines the grid (no `update_grid` / `refine` call, PIKAN notes).
- **Noise sensitivity:** not addressed anywhere in the README. Only indirect pointers: "PDE KAN: l1 plus smoothness penalty to denoise coefficients" (Guo, 9.1) and DropKAN (post-activation masking, Altarabichi 2407.13044). The README does not state that KANs are noise-sensitive; I do not assert it.
- **Interpretability claims:** the README lists sparsity/entropy regularisation (section 9.1: layer-wise l1 on edge activations plus entropy, pykan; EfficientKAN uses a simpler direct l1 on weights, per the README row), KAN-SR and "sparse symbolic discovery" (Wang 2410.01803), and the critical assessment of Hou et al. (arXiv 2407.11075, "Kolmogorov-Arnold Networks: A Critical Assessment of Claims, Performance, and Practical Viability", section 3). It does not summarise Hou et al.'s findings. See PIKAN note: with no sparsity regulariser the symbolic extraction there is fragile.
- **Hyper-parameter sensitivity / fair comparison:** KANbeFair is listed as the fair KAN-vs-MLP benchmark; survey "A Critical Assessment" likewise. We should compare KAN vs MLP at matched parameter count and matched tuning (PIKAN does not, see its note).

## 5. Open problems the README lists
The README has no "open problems" section. Closest content: sections 10.1 and 10.3 (approximation and sample-complexity bounds, Besov rates, minimax rates for additive and hybrid KANs, Lipschitz-controlled layers, generalisation bounds, power-law scaling) are stated as results, not as open questions. Anything about open problems must be read from the review paper.

## 6. Battery-specific entries
Only one in the whole README: line 268 (section 7.6) "Attention-KAN-PINN for battery SOH forecasting", Wei et al., **Expert Systems with Applications 296, 128969 (2026-01)**, "Predicting lithium-ion battery health using attention mechanism with Kolmogorov-Arnold and physics-informed neural networks" (authors Wei, Pang, Huang, Quan, Qian; DOI 10.1016/j.eswa.2025.128969 verified on Crossref). Not read. Not in Shlok's list of 35 (`refs/REFERENCES_FROM_SHLOK.md`); the orchestrator should queue it for a paper-reader. The PIKAN paper (JES 153, 120860) is not listed in the README either.

## 7. Useful pointers for method choices in our paper
- Variant ablation menu with ready code: B-spline (pykan / efficient-kan), Chebyshev (ChebyKAN), RBF (fast-kan), Fourier (FourierKAN), wavelet (Wav-KAN), Jacobi (fKAN), rational (rKAN), Gaussian/PU (Gaussian-KAN, PU-GKAN). Section 6 lines 184-205.
- Physics-informed KAN training recipes worth borrowing for a battery residual: Adam then L-BFGS (7.8), self-scaled residual weighting (7.1) instead of the 49-point grid of loss weights used by PIKAN, GINN-KAN growth prior (7.6), KAN-ODE for a learned right-hand side (7.6).
- Licences: repo MIT; every cited repo has its own licence, check before vendoring any code.
