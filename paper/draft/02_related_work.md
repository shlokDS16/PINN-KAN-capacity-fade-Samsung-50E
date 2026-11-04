> **DRAFT, outcome-independent section. The claim is not frozen and no result appears here. `[TO VERIFY: ...]` marks a statement that rests on an abstract or an unread full text.**

# 2. Related work

## 2.1 Data-driven health and life models, including KAN variants

Data-driven models map features of a charge segment or of early cycles to state of health (SOH) or life; the cycle-life model of Severson et al. [@severson2019] and BatLiNet [@zhang2025batlinet] are typical, and neither contains a physical law. Kolmogorov-Arnold networks (KANs) replace the fixed node activations of a multilayer perceptron by learnable univariate splines on the edges, so each input has a readable response function [@liu2024kan]. In batteries, KANs have been combined with recurrent, transformer and meta-learning models for SOH estimation, including papers in this journal [@jarraya2025; @yuan2026timexer; @wang2026meta]. Another study feeds them incremental-capacity features [@peng2024]. <!-- src: titles verified in refs/INDEX.csv rows 3, 5, 11, 29, 31; full text read only for 11 and 31 -->

## 2.2 Physics-informed SOH estimation

Wang et al. [@wang2024] introduced the form on which most later work builds: a solution network $F$ predicts SOH, a second network $G$ stands for the unknown dynamics, and the residual of $\partial_t F = G$ enters the loss. Later papers replace one or both networks by KANs, namely PIKAN and PGKAN in this journal [@pikan2026; @pgkan2026], PI-EKAN [@piekan2026], a KAN with a Verhulst-type residual [@liu2025verhulst] and SOH-KPINN [@sohkpinn2026]. According to their abstracts and, for PIKAN, the released code, these frameworks estimate SOH from charge-segment features of the four PINN4SOH datasets and take no stress condition as input [TO VERIFY: PIKAN and PGKAN full texts].

## 2.3 Physics-informed ageing laws and early-life forecasting

Models that place the stress dependence of ageing in the equation are closer to ours. Gasper et al. identify algebraic stress-factor laws by bilevel symbolic regression, one paper for calendar ageing and one for cycling [@gasper2021; @gasper2022]. Kuzhiyil et al. place a neural network inside the state equation of calendar ageing [@kuzhiyil2025]. PiDDM [@piddm2026] integrates an Arrhenius time term and an Arrhenius term in depth of discharge and throughput, with parameters supplied by a small network. It uses no storage cells, no state of charge and no KAN, and its test cells share protocols with the training cells. Guo et al. [@guo2026] forecast from the first 2 to 20 % of an unseen cell's record under a physics constraint (preprint). KA-CRNN, also in this journal, uses KAN-valued Arrhenius parameters that depend on state of charge, but for thermal-abuse kinetics measured by calorimetry [@kacrnn2026]. <!-- src: notes/papers/PRIORART_SUMMARY.md and priorart_*.md -->

On the data used here, the dataset authors fit a semi-empirical superposition of calendar and cycle loss [@stroebl2024; @muehlbauer2022], use it to design experiments [@palm2022], and report in this journal that its cycle part was inadequate [@stroebl2026]. Zhang et al. [@zhang2026] cite the dataset in a physics-informed model of equivalent-circuit parameters [TO VERIFY: full text unread; task and cells used unknown].

## 2.4 The gap

Physics-informed SOH networks estimate health from features. Stress-law models learn the dependence for one ageing mode, fix its form, or are not scored on held-out stress conditions of cells with storage and cycling records. We therefore test a combination whose parts each have precedent. It has one law with an Arrhenius calendar term whose coefficients are KAN functions of state of charge, a throughput-driven cycling term whose stress dependence is a KAN, and a soft physics residual. It is trained jointly on the storage and cycling cells of one dataset and scored on held-out cycling conditions from the first check-ups. Section 5 isolates each part by a prespecified comparison.
