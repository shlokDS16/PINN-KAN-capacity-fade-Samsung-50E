### Table A. Rule R2' (development data, ISU: not evidence for Samsung)

| arm | q_a (ensemble endpoint) | bootstrap 95 % (descriptive) | q_a (per-seed endpoint, descriptive) | q_a > 0 |
|---|---|---|---|---|
| A1 | -0.00882 | [-0.0189, 0.0146] | -0.00651 | no |
| A2 | -0.00604 | [-0.0100, -0.0006] | -0.00412 | no |
| A4 | 0.06351 | [-0.0041, 0.0919] | 0.06092 | yes |
| A9 | 0.06438 | [0.0393, 0.1164] | 0.05198 | yes |
| A11 | 0.00322 | [-0.0608, 0.0421] | 0.00322 | yes |
| A12 | 0.02681 | [0.0098, 0.0545] | 0.02888 | yes |

Verdict: **KEEP_2_INNER_FOLDS**. 4 of 6 arms with q > 0 (need >= 5); min q = -0.00882 against floor -0.01980 -> KEEP two inner folds.

Floor -ln(1.02) = -0.01980; arms with q > 0: 4 of 6; min q = -0.00882.

### Table B. Per-fold median ln(S_2fold / S_4fold) over the fold's pseudo-test conditions (ensemble endpoint)

| arm | fold 0 | fold 1 | fold 2 | fold 3 | fold 4 |
|---|---|---|---|---|---|
| A1 | -0.1087 | 0.0098 | 0.0319 | 0.1248 | -0.0956 |
| A2 | -0.0003 | -0.0035 | -0.0226 | -0.0008 | 0.0022 |
| A4 | 0.3277 | -0.0405 | 0.0042 | 0.0000 | 0.0031 |
| A9 | -0.1915 | 0.0954 | 0.4944 | 0.0000 | -0.1372 |
| A11 | -0.3178 | 0.2211 | 0.0000 | 0.0687 | -0.1817 |
| A12 | -0.0173 | 0.0032 | 0.1449 | -0.0033 | 0.0286 |

### Table C. Mean cross-condition ensemble score (pp), mean over folds; seed SD of the cross-condition mean (pp); median ln(per-seed / ensemble) score

| arm | S 2-fold | S 4-fold | seed SD 2 | seed SD 4 | median ln(per-seed/ens) 2 | 4 | grid-edge share 2 | 4 | failed trials 2/4 | non-finite seed values 2/4 |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | 5.486 | 5.517 | 0.249 | 0.328 | 0.0280 | 0.0361 | 0.40 | 0.32 | 0/0 | 0/0 |
| A2 | 7.731 | 7.810 | 0.102 | 0.080 | 0.0016 | 0.0002 | 0.55 | 0.45 | 0/0 | 0/0 |
| A4 | 6.233 | 5.892 | 0.281 | 0.281 | 0.0222 | 0.0243 | 0.13 | 0.20 | 0/0 | 0/0 |
| A9 | 14.397 | 12.896 | 2.403 | 2.121 | 0.0645 | 0.0855 | 0.50 | 0.50 | 0/0 | 0/0 |
| A11 | 6.646 | 6.852 | 0.000 | 0.000 | 0.0000 | 0.0000 | 0.00 | 0.40 | 0/0 | 0/0 |
| A12 | 6.123 | 5.916 | 0.057 | 0.038 | 0.0019 | 0.0010 | 0.12 | 0.08 | 0/0 | 0/0 |

### Table D. A1 against D* (inner-CV choice of A9, A11, A12 per fold and variant), ensemble endpoint, descriptive, non-binding

| variant | D* by fold | median ln(S_D* / S_A1) | share of conditions where A1 is better | conditions |
|---|---|---|---|---|
| 2-fold | 0:A11, 1:A12, 2:A12, 3:A12, 4:A12 | 0.0472 | 0.535 | 43 |
| 4-fold | 0:A12, 1:A12, 2:A12, 3:A12, 4:A12 | 0.0538 | 0.605 | 43 |

### Table E. Inversion-convergence diagnostic (seed-0 refit, pseudo-test windows W = 2 weeks; no rule attached)

| arm, variant | folds | grad norm initial (median) | grad norm final (median) | grad norm final (max) | final/initial (median) | final/initial (max) | spread over 4 inits, pp (median) | spread pp (max cell, max fold) | change when steps are doubled, pp (max) | score range over inits, pp (max) | replica vs production, pp (max) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 k=2 | 5 | 3.07e+04 | 25.1 | 6.9e+03 | 0.000726 | 0.321 | 7.3381 | 129.8795 | 4.5790 | 4.3867 | 0.00e+00 |
| A1 k=4 | 5 | 3.13e+04 | 39.2 | 5.53e+03 | 0.000328 | 3.34 | 7.5868 | 113.1600 | 8.1174 | 1.7198 | 0.00e+00 |
| A2 k=2 | 5 | 128 | 1.48e-05 | 0.000473 | 1.13e-07 | 0.00044 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00e+00 |
| A2 k=4 | 5 | 141 | 1.53e-05 | 0.000485 | 9.98e-08 | 3.13e-05 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00e+00 |
| A9 k=2 | 5 | 15.4 | 0.015 | 34.2 | 0.00144 | 2.68 | 5.1740 | 127.8337 | 42.2590 | 2.9334 | 0.00e+00 |
| A9 k=4 | 5 | 15.6 | 0.0278 | 7.16 | 0.000425 | 4.11 | 0.8710 | 130.7075 | 20.8982 | 3.1717 | 0.00e+00 |

### Table F. Run facts

- CPU hours (sum over units, tournaments and error files): 5.647; wall hours: 2.889; units complete: True.
- split sha256 before = after: True (c1227642a067e61c4e5110d577e0b84b6ccb6da1cd8e4b48b16e03b2ba4419d8).
- script commit: 93e478403a862c3e73465857a3a53c739f131425 (committed 2026-11-05T10:59:43+05:45); script sha256 unchanged since the first fit: True.
- pinnkan files whose content changed between the start and the end of the run: ['arms.py', 'guard.py', 'metrics.py', 'negcontrol.py', 'pinn.py', 'run.py', 'semi.py', 'stats_rows.py', 'stats_step.py', 'stats_v4.py', 'tuning.py'].
- tuned per fold: pseudo-train conditions = 8; pseudo-test conditions per fold: f0: 43, f1: 42, f2: 43, f3: 42, f4: 42.
