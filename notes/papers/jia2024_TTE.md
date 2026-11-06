# Jia et al. 2024 - Knee-point-conscious battery aging trajectory prediction based on physics-guided machine learning (IEEE TTE 10(1), 1056)

Paper note per research/CONTRACT.md section 4, written for novelty condition (c). Auditor: novelty-auditor, 2026-11-06.

## Citation
X. Jia, C. Zhang, Y. Li, C. Zou, L. Y. Wang, X. Cai. "Knee-Point-Conscious Battery Aging Trajectory Prediction Based on Physics-Guided Machine Learning". IEEE Transactions on Transportation Electrification, vol. 10, no. 1, March 2024, first page 1056; received 9 Jan 2023, accepted 6 Apr 2023. DOI 10.1109/TTE.2023.3266386 (Crossref-verified in `debates/D016_roles/03_novelty_recheck.md`). Beijing Jiaotong University (NANTEC), Chalmers, Wayne State. China, Sweden, USA.

## Reading depth
Full text of the article (12 pages) from `refs/pdf/jia2024_tte.pdf`, re-extracted with pdftotext (the markitdown conversion saved as `refs/fulltext/jia2024_tte.md` is a garbled two-column interleave and was not relied on). Read: abstract, introduction, Sections II (data), V-A, V-E, V-F, VI, and the passage on the four-fold validation; Table II read from the rendered page. Sections III-IV (mechanism analysis, PGML architecture) located and skimmed, not line by line; figures not inspected beyond Table II.

## Problem and stated contribution
Early prediction of the aging trajectory of accelerated-aging cells that show a knee point (KP): a physics-guided ML (PGML) scheme in which OCV-reconstruction-based LLI/LAM_PE/LAM_NE information splits a feature relationship into two regimes, each fitted by a decision-tree regressor (DTR), KP is predicted, then the lifetime follows from a linear KP-to-EOL relation (SVR) and a trajectory by KP similarity. Abstract claim: "only 14 cells are needed" to reach 2.02 % lifetime prediction error from the first 50 cycles, against "100 cells" without physical insight.

## Data
- NCM (Li[NiCoMn]O2) dataset: 36 cells aged at 10 to 45 C and discharge rates 0.5C to 2C (Section II); 19 show accelerated aging; **14 randomly chosen** are used. Collected and published in Jia et al. (ref [33]).
- LFP dataset: 123 accelerated-aging cells (ref [19]; source not identified further in the passages read), **no mechanism information**, used only with a conventional DTR.
- Labels: knee point, end of life (lifetime), capacity retention trajectory. Inputs: features from the first cycles (50th to 90th cycle for NCM, every five cycles; the fifth cycle for LFP).

## Model
PGML-DTR (decision-tree regression and classification, SVR), physics enters through OCV-reconstructed degradation-mode features that decide a segmentation, not through a loss term or a differential law. No neural network, no stress law, no calendar term.

## Tuning
Not described as a procedure in the passages read.

## Evaluation
- NCM: four-fold validation by cell; per fold 11 training and 3 test cells (Table II, e.g. test cells 20, 22, 25 in case 1); KP MAPE 4.05 % (training) and 4.18 % (test) on average (Section V-A); abstract: 2.02 % trajectory/lifetime error with 14 cells and 50 cycles. The splits are random-looking cell splits across temperatures and rates, **not held-out ageing conditions**.
- LFP: 23 of 123 cells randomly chosen as test, the rest as training with varying training size; "a total of 10 000" random training/test datasets; KP MAPE on test above 50 % for fewer than 40 training cells and falling between 40 and 100 (Fig. 14, Section V-E). With 100 LFP training cells and fifth-cycle features: KP MAPE 9.6 %, EOL error 7.48 % and trajectory error 2.68 % (Section V-F).
- **The "14 against 100" statement is a cross-dataset comparison**: physics-guided on NCM (11 training cells per fold) against physics-free DTR on LFP (up to 100 training cells), different chemistry, different cells, different error targets. In the passages read, the body reports 2.68 % (not 2.02 %) for the 100-cell LFP case. It is not a same-data, matched ablation of the physics. No seeds beyond the random splits; no intervals.

## Figures
Aging curves and knee definition (Fig. 1-2), mechanism analysis, PGML schematic (Fig. 5), KP prediction scatter (Fig. 6), learning-curve style plot of KP MAPE against number of training cells for LFP (Fig. 14), trajectory examples (Fig. 15). Forms not inspected.

## Ablations
Physics-guided against conventional DTR on NCM (training comparison in Fig. 9a; KP results in Table III); training-size sweep on LFP without physics. No ablation of the physics at matched data.

## Hidden assumptions
KP-EOL linear relation holds (correlation 0.9952 on LFP, Fig. 13b); OCV reconstruction gives usable degradation modes from early cycles; the 14 selected cells represent accelerated aging.

## Weaknesses a reviewer would hit
Tiny NCM sample (14 cells, 3 test per fold), the 14-against-100 contrast mixes datasets and error targets, random cell splits, no repeated draws on NCM, accelerated-aging only.

## Overlap with our four-part claim (condition (c))
- **Condition (c) answer: the 14-against-100 claim is a lifetime-from-early-cycles result (first 50 cycles, KP and EOL), obtained on random cell splits; it is not an extrapolation to held-out ageing conditions, and it is not a learning curve over the number of cycling conditions.** Closed.
- Data-efficiency framing: partial (cells needed, physics against none, but across datasets and as lifetime prediction).
- Matched ablation ladder: not matched (the physics-free arm is on another dataset); our ladder is not pre-empted, and an "extension of Jia" wording must name this difference.
- Joint calendar-plus-cycle law, KAN, closed-form law, Samsung 50E: none.

## Gaps and hooks for our paper
Cite as the earlier physics-versus-data cell-count claim for cycling prognostics; state the difference (cross-dataset, early-cycle lifetime, tree models, random cell splits). Do not cite it for "physics reduces the cells needed" as an established matched result.

## Code/data availability
Not stated in the passages read; NCM data in ref [33].
