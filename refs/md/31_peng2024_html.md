# 31 Peng et al. 2024, Batteries 10(9) 315 -- EXTRACT of the MDPI HTML text (read via Exa fetch, 2026-11-04)

Status: the fetched text (about 50 KB) came back inline, not as a saved file, so this file is a faithful extract of the
parts used in the note (metadata, abstract, setup, split, tables, figure captions), not the full verbatim text.
Equations were stripped by the HTML conversion; figure images are not available. URL: https://www.mdpi.com/2313-0105/10/9/315
DOI 10.3390/batteries10090315. Received 16 Jul 2024, accepted 2 Sep 2024, published 4 Sep 2024.

Authors: Jun Peng, Xuan Zhao (corr.), Jian Ma, Dean Meng, Shuhai Jia, Kai Zhang, Chenyan Gu, Wenhao Ding.
Affiliations: School of Automobile, Chang'an University, Xi'an; School of Mechanical Engineering, Xi'an Jiaotong University.

## Abstract (paraphrased)
15 incremental-capacity (IC) features plus internal resistance identified with a 2RC equivalent circuit (recursive least
squares) are inputs to BP, LSTM, TCN, LSTM-KAN and TCN-KAN SOH models. KAN hybrids beat conventional ones; LSTM-KAN best;
MAE below 0.412 % on test and validation; no full charge/discharge needed.

## 2.1 Aging test (Table 1)
8 commercial LiFePO4 cells, 20 Ah nominal, 3.2 V, 3.65 V charge cut-off, 2.5 V discharge cut-off, 133x70x28 mm, 35 C chamber,
1 s sampling. Neware BTS4000. Regime: CC 1C to cut-off, CV to C/20, CC 1C discharge, 0.5 h rest. HPPC profile added in each
discharge cycle (Sec. 2.3.2).
## 2.2 IC features
dQ/dV with 1 mV voltage grid, Gaussian filter. 15 features: position (L_P1-3), height (H_P1-3), width (W_P1-3) of three peaks;
position (L_d1-3) and height (H_d1-3) of three dips; all in 3.2-3.5 V (SOC 20-85 %).
## 2.3 ECM
2RC model, R0, R1, R2, C1, C2 identified by RLS on HPPC data at fixed SOC and temperature; terminal-voltage MAE < 0.4 mV (Fig. 7).
## 3 Models
LSTM-KAN: KAN layer replaces the fully connected layers in the LSTM hidden layer before output. No KAN grid size, spline order,
layer widths, optimiser, epochs or seeds are given anywhere in the text. Input stated as "18 parameters: 15 IC + 5 ECM" (15+5=20;
Table 4 lists 20 inputs for model I and 15 for model II).
## 4.1 Split and results
Table 2 (initial SOH %, cycles experienced): #1 100/500; #2 100/1070; #3 100/930; #4 100/380; #5 90.3/550; #6 87.9/375;
#7 88.09/320; #8 96.18/590.
Train: Bat 1,2,3,6,7,8. "Bat. #4 and Bat. #8 are used as the test and validation dataset" (same sentence), but figures and later text
use Bat #4 as test and Bat #5 as validation (Bat #8 is also in the training list).
Table 3 (MAE / MAPE / RMSE, %):
Test BP 0.811/0.921/1.028; TCN 0.472/0.528/0.607; LSTM 0.519/0.585/0.641; LSTM-KAN 0.412/0.462/0.570; TCN-KAN 0.426/0.476/0.572.
Validation BP 0.531/0.569/0.727; TCN 0.461/0.495/0.547; LSTM 0.438/0.472/0.490; LSTM-KAN 0.256/0.278/0.378; TCN-KAN 0.251/0.268/0.365.
Text: literature BP models in refs 11,12 had MAE 1.16 and 1.957 %.
## 4.2 Input ablation
Model I (15 IC + resistance params, Table 4 lists R0,R1,R2,C1,C2) vs model II (15 IC only); Figs 13-14 show model I lower MAE on Bat 4 and 5
(numbers only in figure insets, not in text).
## Figure captions
F1 setup photo; F2 capacity-vs-voltage and IC curve of one charge; F3 V-Q curves over 700 cycles with zoom; F4 IC curves over 700 cycles;
F5 features marked on one IC curve; F6 2RC circuit; F7 (a) simulated vs measured voltage (b) error (c,d) identified R0,R1,R2,C1,C2;
F8 KAN schematic; F9 LSTM-KAN structure; F10 predicted SOH Bat 4 (5 models); F11 Bat 5; F12 training time per model; F13/F14 input ablation.
## Data availability
"Original contributions are included in the article; further inquiries to the corresponding author." No code.
