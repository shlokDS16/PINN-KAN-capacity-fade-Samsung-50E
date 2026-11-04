> **DRAFT, outcome-independent section. The claim is not frozen. Constants are those of the code at the draft commit and must be re-checked at the freeze. `[TO VERIFY: ...]` marks a statement that depends on a source not yet read; `[RESULT: ...]` marks a quantity fixed by training-side runs.**

# 4. Method

## 4.1 Problem statement and causal window

Every cell $c$ has a stress vector $\mathbf{s}_c$: $(T, \mathrm{SOC}_{\mathrm{mid}}, \mathrm{DoD}, C_{\mathrm{ch}}, C_{\mathrm{dch}})$ for a cycling cell, with $\mathrm{SOC}_{\mathrm{mid}} = \mathrm{SOC}_{\max} - \mathrm{DoD}/2$, and $(T, \mathrm{SOC})$ for a storage cell. With retention $r_c$, the state is the capacity loss in units of ten percentage points,

$$ y_{c}(t) = 10\,\bigl(1 - r_c(t)\bigr), \qquad t_n = t/500\ \mathrm{d}, \qquad E_n = \mathrm{EFC}/500. \tag{1} $$

For a held-out cell the model receives $\mathbf{s}_c$, the reference capacity, the first $k$ check-ups after the reference (the window) and the throughput rate, and it returns $r_c$ at every later check-up. Throughput is the logged one inside the window and the cell's own mean window rate afterwards, so no quantity after the window enters a forecast. Time is global (days since the reference), not a fraction of life. The window length is fixed from the test schedule alone, $k = \operatorname{round}(n_{\mathrm{med}}/3)$, where $n_{\mathrm{med}}$ is the median number of intermediate check-ups of a cycling cell [RESULT: $k_{\mathrm{cyc}}$, $k_{\mathrm{sto}}$].

## 4.2 The physics-informed network

*Law.* Fade follows one rate equation with a calendar term and a throughput term,

$$ \frac{\mathrm{d}y}{\mathrm{d}t_n} = \bigl[\,a_{\mathrm{cal}} + a_{\mathrm{cyc}}\,\nu(t)\,\bigr]\,h(y), \qquad y(0)=0, \tag{2} $$

where $\nu = \mathrm{d}E_n/\mathrm{d}t_n$ is the throughput rate (zero for storage cells) and $h$ is a single state-dependent modulation shared by both terms. The amplitudes are

$$ a_{\mathrm{cal}} = e^{\delta_c\mathbb{1}_{\mathrm{sto}}}\, \exp\!\bigl[\ell_{\mathrm{cal}} + a(\mathrm{SOC}) + E(\mathrm{SOC})\,x(T)\bigr], \tag{3} $$

$$ a_{\mathrm{cyc}} = e^{\delta_c\mathbb{1}_{\mathrm{cyc}}}\, \exp\!\bigl[\ell_{\mathrm{cyc}} + f(\mathbf{s})\bigr], \tag{4} $$

with the normalised Arrhenius abscissa $x(T) = (1/T_0 - 1/T)/(1/T_0 - 1/T_1)$, $T_0 = 298.15$ K and $T_1 = 308.15$ K. The pair $(a, E)$ is the output of a KAN on state of charge, so $E(\mathrm{SOC})\,R/(1/T_0 - 1/T_1)$, with $R$ the gas constant, is an effective activation energy that may vary with charge state. The stress map $f$ is a KAN on $\mathbf{s}$, and a cycling cell evaluates the calendar term at $(T, \mathrm{SOC}_{\mathrm{mid}})$. The levels $\ell_{\mathrm{cal}}$ and $\ell_{\mathrm{cyc}}$ are free. The per-cell log-offset $\delta_c$ has prior $\mathcal{N}(0,\tau^2)$ with $\tau = 0.15$ and scales the cycling term of a cycling cell and the calendar term of a storage cell.

The modulation is constant, self-limiting, $h = 1/(1+y/Y_0)$ with $Y_0 = 1$, or accelerating, $h = \exp(\gamma y)$ with $\gamma = 0.3$. One form is chosen per outer fold on training conditions only: a tournament of the hard-ODE variant (Section 4.4) at default settings keeps the simplest form within one standard error of the best [RESULT: form per fold]. With one $h$ for both terms, Eq. (2) integrates in closed form. Let $\Psi(y) = \int_0^y \mathrm{d}y'/h(y')$ and $\Phi(t) = a_{\mathrm{cal}}t_n + a_{\mathrm{cyc}}E_n(t)$. For piecewise-constant $\nu$,

$$ y(t) = \Psi^{-1}\bigl(\Phi(t)\bigr), \tag{5} $$

where $\Psi^{-1}(\Phi)$ equals $\Phi$, $Y_0\bigl(\sqrt{1+2\Phi/Y_0}-1\bigr)$ and $-\ln(1-\gamma\Phi)/\gamma$ for the three forms. The terms interact only through $h$, so the law is not an independent superposition.

*Solution network and residual.* A tanh network $g$ with three hidden layers of width 32 gives $F(t_n,\mathbf{s},\mathbf{z}_c) = t_n\,g(t_n,\mathbf{s},\mathbf{z}_c)$, which satisfies $F(0)=0$ by construction; $\mathbf{z}_c\in\mathbb{R}^2$ is a per-cell latent code. The physics residual comes from automatic differentiation, as in physics-informed neural networks [@raissi2019pinn],

$$ \mathcal{R} = \frac{\partial F}{\partial t_n} - \bigl[a_{\mathrm{cal}} + a_{\mathrm{cyc}}\,\nu(t)\bigr]\,h(F). \tag{6} $$

It is evaluated on three label-free collocation sets. Set (a) holds times along each training cell's axis, from the end of its record (or from zero; the placement is tuned) to 1.1 times the longest record. Set (b) holds Latin-hypercube points [@mckay1979lhs] inside the convex hull of the training cycling design, with $\nu$ from the design rates. Set (c) holds the calendar twins $(T,\mathrm{SOC}_{\mathrm{mid}})$ of the cycling conditions, with $\nu=0$.

*Training and inference.* The loss is

$$ \mathcal{L} = \frac{1}{\sigma^2}\Bigl[\overline{(F-y)^2} + \lambda\,\overline{\mathcal{R}^2}\Bigr] + \frac{\|\boldsymbol{\delta}\|^2}{\tau^2 N} + \frac{\|\mathbf{z}\|^2}{N} + \Omega, \tag{7} $$

where overbars are means over observations or collocation points, $N$ is the number of observations, $\sigma = 0.05$ (0.5 points) is a fixed nominal noise, and $\Omega$ combines a spline ridge penalty with a sparsity penalty (L1 and entropy of edge magnitudes). The weight $\lambda$ ramps from 0 to its tuned value over the first 40 % of the steps. The optimiser is Adam [@kingma2015adam] (rate $5\times10^{-3}$, cosine decay to 10 %, 2000 steps) with a global gradient-norm clip of 20, applied to every gradient-trained model in the study so that the comparison with $\lambda=0$ has no optimiser confound. For an unseen cell, with network and law frozen, $\mathbf{z}_c$ and $\delta_c$ are fitted by 200 Adam steps on the window data plus the residual over the forecast horizon. No label after the window is used. <!-- src: code/pinnkan/law.py, pinn.py (constants as of the draft commit) -->

## 4.3 KAN parametrisation

A KAN layer maps $\mathbf{x}$ to $y_j = \sum_i [\,w^{b}_{ji}\,\mathrm{silu}(x_i) + \sum_m c_{jim}B_m(x_i)\,]$ with cubic B-splines $B_m$ on a uniform grid of $G$ intervals [@liu2024kan]. The implementation is our own. Stress inputs are scaled to $[-1,1]$ by fixed physical ranges (5 to 50 C; state of charge 0 to 1; DoD 0 to 0.8; charge rate 0 to 1.2C; discharge rate 0 to 2.2C). The cycling map is a KAN $[5, h, 1]$ with hidden width $h\in\{2,3,4,6,8\}$ and $G\in\{2,3,5,8,12\}$; the calendar KAN is $[1,2]$ with $G=5$. Without a hidden layer, KAN $[5,1]$ is an additive spline model (arm A4).

## 4.4 Comparators

All comparators share inputs, window, latent inference, throughput rule and tuning budget; identifiers follow the preregistration.

| Arm | Model | Question (hypothesis) |
|---|---|---|
| A1 | the model above (PINN-KAN) | reference |
| A9 | $F$ with the same $\mathbf{z}_c$ and inversion, $\lambda=0$, no law | does the residual help (H1a) |
| A3, A4, A5, A7 | same PINN; stress map parametric log-linear (A3), additive spline (A4), additive spline plus tensor products $T\times C_{\mathrm{ch}}$, $T\times\mathrm{SOC}_{\mathrm{mid}}$, $\mathrm{DoD}\times\mathrm{SOC}_{\mathrm{mid}}$ (A5), small tanh network in the manner of PiDDM (A7) | does the KAN help (H1b); per fold, the member with the lowest inner-CV error is the comparator |
| A2 | same law, closed form of Eq. (5), $\delta_c$ by MAP from the window, no $F$ | hard law versus soft residual (H2) |
| A10 | the dataset authors' semi-empirical superposition, multi-start least squares, plus one per-cell factor fitted to the window with the prior of $\delta_c$ | the dataset authors' model (H6) |
| A11, A12 | Gaussian process with ARD kernel [@rasmussen2006gp]; LightGBM [@ke2017lightgbm] | data-only learners (H1c, gated) |
| A13, A14 | A1 on cycling cells only; on storage cells only (exploratory) | does joint training help (X1) |
| R1, R2 | persistence of the last window value; line through the window | references |

A10 is given as a structure only. The dataset authors' model is described in the supplement of [@stroebl2024] as a sum of a calendar and a cycle loss with Arrhenius and power-law factors: $Q_{\mathrm{loss}} = Q_{\mathrm{cal}} + Q_{\mathrm{cyc}}$, with $Q_{\mathrm{cal}}$ [TO VERIFY: Stroebl JES 142 full text, exponent placement] and $Q_{\mathrm{cyc}}$ [TO VERIFY: same source]. The per-cell factor is our addition and gives A10 the window information that A1 uses. It scales the total loss, unlike $\delta_c$ in Eqs. (3) and (4), which favours A10; the published form without it is a sensitivity row. A7 reproduces the idea of PiDDM [@piddm2026] inside our law and training and is not a reimplementation. A free dynamics network (A8) is used on synthetic data only.

## 4.5 Tuning and seeds

Each tuned arm receives the same number $N$ of Tree-structured Parzen Estimator trials [@bergstra2011tpe; @akiba2019optuna]. Three inner folds, grouped by condition and stratified by temperature, are drawn inside the outer-training conditions only, and the objective is the primary endpoint computed out of fold. The default is $N=20$. A timing run on training folds sets $N=40$ if every neural arm's median fit is under 20 s. If the median hard-ODE fit exceeds 30 s or the PINN fit exceeds 90 s, every arm uses 10 trials and two inner folds [RESULT: $N$]. A1 searches six dimensions: $h$, $G$, the spline ridge weight, the sparsity weight, $\lambda\in\{10^{-3},\dots,10^{2}\}$ and the collocation placement (other spaces: Appendix B). The test fold is never read by tuning, selection or a margin. Final refits use seeds 0 to 4, a condition's score is the mean over seeds, and seeds are never units of analysis. Each fold has one search, so search-to-search variation is not in the intervals, which we state as a limitation.

All models run on the CPU with one thread [AUTHOR: processor, memory; library versions are in each run record]. Code and run records are archived with the paper [AUTHOR: repository and archive DOI].
