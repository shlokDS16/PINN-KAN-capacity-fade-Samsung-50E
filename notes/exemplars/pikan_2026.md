# PIKAN (Liu et al., JES 153, 120860)

**Citation.** L. Liu, J. Huang, B. Peng, Y. Li, P. Wang, X. Wang, H. Zhao (corresponding), B. Li (corresponding), "Physics-informed and interpretable state of health estimation framework for lithium-ion batteries", J. Energy Storage 153, 120860 (issued 2026-04; online 2026-02-10), DOI 10.1016/j.est.2026.120860 (verified on Crossref). University of Science and Technology of China (USTC). Closed access. Code: https://github.com/USTC-AI4EEE/PIKAN (no licence file, per `notes/code/PIKAN.md`).

**Reading depth: abstract (journal and README) + the released code (full, separate note) ; the journal body is NOT read.** Figures and tables of the paper are unknown. Everything about the model and its weaknesses is in `ROOT\notes\code\PIKAN.md` (not repeated here).

## Claim structure (from the abstract)
Three challenges (data scarcity, physical consistency, interpretability) answered by **three numbered innovations**: (1) SHEM, a KAN state-of-health estimation module; (2) DDMM, a KAN dynamics module that "discovers" degradation equations without a predefined form; (3) bidirectional coupling (self-regularisation). Headline numbers: four datasets, "maximum 63.4 % RMSE reduction in small-sample scenarios" (the code note shows this is against a test-tuned PINN on HUST with one training cell). Closing claims: symbolic regression gives explicit analytical expressions; discovered equations "structurally similar to existing electrochemical models"; some cross-battery transferability.

Pattern worth copying: problem stated as three challenges, solution as three innovations, headline relative improvement in the small-sample regime plus an interpretability claim. Pattern not to copy: a physics claim that rests on a hand-chosen parabola and unaudited tuning (see PIKAN.md section 6).

## Figures and tables
Unknown for the journal paper. From the code repo only: README holds two result tables (regular and small-sample, mean over 10 seeds, no SD) and notebooks plot learned splines (pykan). Plot forms of the paper not recorded.

## Hooks for us (from the code note, unchanged)
No forecasting, life-fraction time axis, no stress inputs, test-set hyper-parameter selection. Our paper's differentiators are the opposite on each count, and each must be demonstrated with an ablation, not asserted.

## Shlok must save by hand
Yes, priority 2 of the exemplars: PIKAN full text (figures, tables, ablation, transfer numbers).
