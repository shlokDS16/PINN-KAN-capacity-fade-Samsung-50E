# Descriptive extras: sensitivity rows, ISU replication, Test A, S3

Descriptive only. Tiers in the column 'tier it would reach' are what the row would give at the primary final local levels (stats_rows.row_tiers, same sign rule: sign test with a fixed design effect (assumed average pairwise sign correlation at most 0.03); assumption-based, not exact and not distribution-free). They are reported, never applied: the effective tiers stay those of the frozen step. Median L as % reduction = 100(1 - exp(-median L)); positive = A1 (or the first arm) better. Interval = unadjusted 95 % rank interval of the frozen rule (rank 11 of 40 at n = 40). Positives = conditions with L > 0.

Inputs checked: 209 run directories, each with metrics.json and a campaign.log end line rc=0; not ok: none.
Validation: row_tiers on the primary store reproduces every frozen primary tier; the recomputed A1 vs D* g1 median L equals the frozen value (validation_primary.json).

## A. Sensitivity rows (Samsung Test B, 40 held-out conditions unless n says otherwise)

| Row (9.9) | What changes | Contrast | Cell | n | Median L as % reduction | 95 % interval (%) | Positives | Primary: median % [interval], positives | Tier it would reach | Primary tier | Changes tier? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 9.9 (i) at | final test (AT) included | A1 vs D* (g1) [P1] | g1 | 40 | -9.2 | [-24.1, 20.7] | 18/40 | -2.4 [-38.3, 32.9], 20/40 | none | none | False |
| 9.9 (i) at | final test (AT) included | A1 vs A9 (g1) [P2] | g1 | 40 | -9.7 | [-32.5, 24.6] | 17/40 | -10.7 [-45.8, 14.7], 18/40 | False | False | False |
| 9.9 (i) at | final test (AT) included | A1 vs A10 (g1) [QA10_g1] | g1 | 40 | 7.5 | [-28.4, 36.7] | 24/40 | 22.6 [-6.7, 56.8], 28/40 | none | none | False |
| 9.9 (i) at | final test (AT) included | A1 vs A10P (g1) [QA10_g1] | g1 | 40 | 19.2 | [-46.8, 44.0] | 23/40 | 29.9 [-17.6, 53.7], 28/40 | none | none | False |
| 9.9 (i) at | final test (AT) included | A1 vs D* (g4) [-] | g4 | 40 | -4.1 | [-66.5, 21.5] | 20/40 | 2.2 [-66.1, 41.5], 21/40 | no registered tier | None | None |
| 9.9 (i) at | final test (AT) included | A1 vs A9 (g4) [-] | g4 | 40 | 13.6 | [-22.9, 35.6] | 24/40 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (i) at | final test (AT) included | A1 vs A10 (g4) [QA10_g4] | g4 | 40 | 17.5 | [-40.9, 48.7] | 25/40 | 26.2 [-42.4, 64.1], 26/40 | none | none | False |
| 9.9 (i) at | final test (AT) included | A1 vs A10P (g4) [QA10_g4] | g4 | 40 | 37.8 | [-9.0, 60.7] | 29/40 | 41.4 [0.7, 63.3], 30/40 | none | none | False |
| 9.9 (i) at | final test (AT) included | most-test d_c (median d_c -0.042) | g1 | 40 | | | 18 | | False | False | False |
| 9.9 (i) st0406 | storage cells 04-06 included | A1 vs D* (g1) [P1] | g1 | 40 | -2.0 | [-70.7, 36.1] | 19/40 | -2.4 [-38.3, 32.9], 20/40 | none | none | False |
| 9.9 (i) st0406 | storage cells 04-06 included | A1 vs A9 (g1) [P2] | g1 | 40 | -6.4 | [-97.6, 24.7] | 16/40 | -10.7 [-45.8, 14.7], 18/40 | False | False | False |
| 9.9 (i) st0406 | storage cells 04-06 included | A1 vs A10 (g1) [QA10_g1] | g1 | 40 | 7.8 | [-40.9, 39.3] | 24/40 | 22.6 [-6.7, 56.8], 28/40 | none | none | False |
| 9.9 (i) st0406 | storage cells 04-06 included | A1 vs A10P (g1) [QA10_g1] | g1 | 40 | 23.6 | [-35.2, 50.4] | 26/40 | 29.9 [-17.6, 53.7], 28/40 | none | none | False |
| 9.9 (i) st0406 | storage cells 04-06 included | A1 vs D* (g4) [-] | g4 | 40 | -13.0 | [-81.7, 45.6] | 19/40 | 2.2 [-66.1, 41.5], 21/40 | no registered tier | None | None |
| 9.9 (i) st0406 | storage cells 04-06 included | A1 vs A9 (g4) [-] | g4 | 40 | 15.3 | [-25.7, 49.5] | 26/40 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (i) st0406 | storage cells 04-06 included | A1 vs A10 (g4) [QA10_g4] | g4 | 40 | 19.1 | [-49.9, 58.6] | 25/40 | 26.2 [-42.4, 64.1], 26/40 | none | none | False |
| 9.9 (i) st0406 | storage cells 04-06 included | A1 vs A10P (g4) [QA10_g4] | g4 | 40 | 40.4 | [-22.8, 65.7] | 28/40 | 41.4 [0.7, 63.3], 30/40 | none | none | False |
| 9.9 (i) st0406 | storage cells 04-06 included | most-test d_c (median d_c -0.121) | g1 | 40 | | | 12 | | False | False | False |
| 9.9 (i) fc3 | cells with >= 3 forecast points | A1 vs D* (g1) [P1] | g1 | 40 | 5.9 | [-37.7, 33.3] | 21/40 | -2.4 [-38.3, 32.9], 20/40 | none | none | False |
| 9.9 (i) fc3 | cells with >= 3 forecast points | A1 vs A9 (g1) [P2] | g1 | 40 | -10.7 | [-45.8, 17.3] | 18/40 | -10.7 [-45.8, 14.7], 18/40 | False | False | False |
| 9.9 (i) fc3 | cells with >= 3 forecast points | A1 vs A10 (g1) [QA10_g1] | g1 | 40 | 22.6 | [-8.3, 56.8] | 27/40 | 22.6 [-6.7, 56.8], 28/40 | none | none | False |
| 9.9 (i) fc3 | cells with >= 3 forecast points | A1 vs A10P (g1) [QA10_g1] | g1 | 40 | 27.4 | [-20.0, 53.7] | 27/40 | 29.9 [-17.6, 53.7], 28/40 | none | none | False |
| 9.9 (i) fc3 | cells with >= 3 forecast points | A1 vs D* (g4) [-] | g4 | 39 | -3.5 | [-48.1, 42.9] | 19/39 | 2.2 [-66.1, 41.5], 21/40 | no registered tier | None | None |
| 9.9 (i) fc3 | cells with >= 3 forecast points | A1 vs A9 (g4) [-] | g4 | 39 | 14.4 | [5.0, 50.8] | 29/39 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (i) fc3 | cells with >= 3 forecast points | A1 vs A10 (g4) [QA10_g4] | g4 | 39 | 26.9 | [-32.6, 65.4] | 26/39 | 26.2 [-42.4, 64.1], 26/40 | none | none | False |
| 9.9 (i) fc3 | cells with >= 3 forecast points | A1 vs A10P (g4) [QA10_g4] | g4 | 39 | 41.2 | [2.9, 63.3] | 30/39 | 41.4 [0.7, 63.3], 30/40 | none | none | False |
| 9.9 (i) fc3 | cells with >= 3 forecast points | most-test d_c (median d_c -0.063) | g1 | 40 | | | 17 | | False | False | False |
| 9.9 (i) oracle | oracle throughput | A1 vs D* (g1) [P1] | g1 | 40 | 23.1 | [-50.3, 43.9] | 23/40 | -2.4 [-38.3, 32.9], 20/40 | none | none | False |
| 9.9 (i) oracle | oracle throughput | A1 vs A9 (g1) [P2] | g1 | 40 | 9.3 | [-60.8, 44.4] | 23/40 | -10.7 [-45.8, 14.7], 18/40 | False | False | False |
| 9.9 (i) oracle | oracle throughput | A1 vs A10 (g1) [QA10_g1] | g1 | 40 | 28.1 | [-27.4, 68.8] | 26/40 | 22.6 [-6.7, 56.8], 28/40 | none | none | False |
| 9.9 (i) oracle | oracle throughput | A1 vs A10P (g1) [QA10_g1] | g1 | 40 | 32.5 | [-40.6, 71.8] | 26/40 | 29.9 [-17.6, 53.7], 28/40 | none | none | False |
| 9.9 (i) oracle | oracle throughput | A1 vs D* (g4) [-] | g4 | 40 | -11.8 | [-91.8, 31.2] | 18/40 | 2.2 [-66.1, 41.5], 21/40 | no registered tier | None | None |
| 9.9 (i) oracle | oracle throughput | A1 vs A9 (g4) [-] | g4 | 40 | 3.1 | [-30.7, 34.3] | 21/40 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (i) oracle | oracle throughput | A1 vs A10 (g4) [QA10_g4] | g4 | 40 | 1.8 | [-89.5, 42.9] | 20/40 | 26.2 [-42.4, 64.1], 26/40 | none | none | False |
| 9.9 (i) oracle | oracle throughput | A1 vs A10P (g4) [QA10_g4] | g4 | 40 | 31.4 | [-7.9, 56.3] | 28/40 | 41.4 [0.7, 63.3], 30/40 | none | none | False |
| 9.9 (i) oracle | oracle throughput | most-test d_c (median d_c 0.011) | g1 | 40 | | | 20 | | False | False | False |
| 9.9 (i) selflim | backbone fixed to self-limiting | A1 vs D* (g1) [P1] | g1 | 40 | 21.9 | [-25.0, 46.3] | 23/40 | -2.4 [-38.3, 32.9], 20/40 | none | none | False |
| 9.9 (i) selflim | backbone fixed to self-limiting | A1 vs A9 (g1) [P2] | g1 | 40 | 9.7 | [-44.5, 39.5] | 23/40 | -10.7 [-45.8, 14.7], 18/40 | False | False | False |
| 9.9 (i) selflim | backbone fixed to self-limiting | A1 vs A10 (g1) [QA10_g1] | g1 | 40 | 31.6 | [-3.3, 59.2] | 29/40 | 22.6 [-6.7, 56.8], 28/40 | none | none | False |
| 9.9 (i) selflim | backbone fixed to self-limiting | A1 vs A10P (g1) [QA10_g1] | g1 | 40 | 36.8 | [5.2, 60.3] | 30/40 | 29.9 [-17.6, 53.7], 28/40 | none | none | False |
| 9.9 (i) selflim | backbone fixed to self-limiting | A1 vs D* (g4) [-] | g4 | 40 | 2.2 | [-66.1, 41.5] | 21/40 | 2.2 [-66.1, 41.5], 21/40 | no registered tier | None | None |
| 9.9 (i) selflim | backbone fixed to self-limiting | A1 vs A9 (g4) [-] | g4 | 40 | 14.2 | [5.0, 50.8] | 30/40 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (i) selflim | backbone fixed to self-limiting | A1 vs A10 (g4) [QA10_g4] | g4 | 40 | 26.2 | [-42.4, 64.1] | 26/40 | 26.2 [-42.4, 64.1], 26/40 | none | none | False |
| 9.9 (i) selflim | backbone fixed to self-limiting | A1 vs A10P (g4) [QA10_g4] | g4 | 40 | 41.4 | [0.7, 63.3] | 30/40 | 41.4 [0.7, 63.3], 30/40 | none | none | False |
| 9.9 (i) selflim | backbone fixed to self-limiting | most-test d_c (median d_c 0.082) | g1 | 40 | | | 23 | | False | False | False |
| 9.9 (i) blinded | blinded cells scored (score_blinded_cells) | A1 vs D* (g1) [P1] | g1 | 40 | -2.4 | [-38.3, 32.9] | 20/40 | -2.4 [-38.3, 32.9], 20/40 | none | none | False |
| 9.9 (i) blinded | blinded cells scored (score_blinded_cells) | A1 vs A9 (g1) [P2] | g1 | 40 | -15.8 | [-45.8, 16.7] | 17/40 | -10.7 [-45.8, 14.7], 18/40 | False | False | False |
| 9.9 (i) blinded | blinded cells scored (score_blinded_cells) | A1 vs A10 (g1) [QA10_g1] | g1 | 40 | 22.6 | [-6.7, 56.8] | 28/40 | 22.6 [-6.7, 56.8], 28/40 | none | none | False |
| 9.9 (i) blinded | blinded cells scored (score_blinded_cells) | A1 vs A10P (g1) [QA10_g1] | g1 | 40 | 28.9 | [-17.6, 53.7] | 28/40 | 29.9 [-17.6, 53.7], 28/40 | none | none | False |
| 9.9 (i) blinded | blinded cells scored (score_blinded_cells) | A1 vs D* (g4) [-] | g4 | 40 | 0.9 | [-66.1, 41.5] | 20/40 | 2.2 [-66.1, 41.5], 21/40 | no registered tier | None | None |
| 9.9 (i) blinded | blinded cells scored (score_blinded_cells) | A1 vs A9 (g4) [-] | g4 | 40 | 14.2 | [5.0, 50.8] | 30/40 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (i) blinded | blinded cells scored (score_blinded_cells) | A1 vs A10 (g4) [QA10_g4] | g4 | 40 | 26.2 | [-42.4, 64.1] | 26/40 | 26.2 [-42.4, 64.1], 26/40 | none | none | False |
| 9.9 (i) blinded | blinded cells scored (score_blinded_cells) | A1 vs A10P (g4) [QA10_g4] | g4 | 40 | 41.4 | [0.7, 63.3] | 30/40 | 41.4 [0.7, 63.3], 30/40 | none | none | False |
| 9.9 (i) blinded | blinded cells scored (score_blinded_cells) | most-test d_c (median d_c -0.083) | g1 | 40 | | | 18 | | False | False | False |
| 9.9 (i) kfull_m1 | window k_full - 1 (3 cycling check-ups) | A1 vs D* (g4) [-] | g4 | 40 | 18.8 | [-81.0, 55.6] | 25/40 | 2.2 [-66.1, 41.5], 21/40 | no registered tier | None | None |
| 9.9 (i) kfull_m1 | window k_full - 1 (3 cycling check-ups) | A1 vs A9 (g4) [-] | g4 | 40 | 15.9 | [-17.4, 50.1] | 24/40 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (i) kfull_m1 | window k_full - 1 (3 cycling check-ups) | A1 vs A10 (g4) [QA10_g4] | g4 | 40 | 34.2 | [-8.5, 45.7] | 26/40 | 26.2 [-42.4, 64.1], 26/40 | none | none | False |
| 9.9 (i) kfull_m1 | window k_full - 1 (3 cycling check-ups) | A1 vs A10P (g4) [QA10_g4] | g4 | 40 | 33.6 | [1.2, 59.6] | 30/40 | 41.4 [0.7, 63.3], 30/40 | none | none | False |
| 9.9 (i) kfull_p2 | window k_full + 2 (6 cycling check-ups) | A1 vs D* (g4) [-] | g4 | 40 | 13.5 | [-40.8, 41.0] | 23/40 | 2.2 [-66.1, 41.5], 21/40 | no registered tier | None | None |
| 9.9 (i) kfull_p2 | window k_full + 2 (6 cycling check-ups) | A1 vs A9 (g4) [-] | g4 | 40 | 4.4 | [-45.3, 31.9] | 20/40 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (i) kfull_p2 | window k_full + 2 (6 cycling check-ups) | A1 vs A10 (g4) [QA10_g4] | g4 | 40 | -28.2 | [-106.4, 58.7] | 18/40 | 26.2 [-42.4, 64.1], 26/40 | none | none | False |
| 9.9 (i) kfull_p2 | window k_full + 2 (6 cycling check-ups) | A1 vs A10P (g4) [QA10_g4] | g4 | 40 | 47.9 | [-42.5, 69.4] | 29/40 | 41.4 [0.7, 63.3], 30/40 | none | none | False |
| 9.9 (p) tpe2 | second TPE search seed (100 + fold) | A1 vs D* (g1) [P1] | g1 | 40 | 4.3 | [-28.4, 41.9] | 20/40 | -2.4 [-38.3, 32.9], 20/40 | none | none | False |
| 9.9 (p) tpe2 | second TPE search seed (100 + fold) | A1 vs A9 (g1) [P2] | g1 | 40 | 5.3 | [-31.3, 48.8] | 21/40 | -10.7 [-45.8, 14.7], 18/40 | False | False | False |
| 9.9 (p) tpe2 | second TPE search seed (100 + fold) | most-test d_c (median d_c 0.073) | g1 | 40 | | | 21 | | False | False | False |
| 9.9 (k) clip10 | gradient clip 10 | A1 vs A9 (g1) [P2] | g1 | 40 | -12.5 | [-64.9, 25.1] | 19/40 | -10.7 [-45.8, 14.7], 18/40 | False | False | False |
| 9.9 (k) clip10 | gradient clip 10 | A1 vs A9 (g4) [-] | g4 | 40 | 24.6 | [-5.1, 41.3] | 27/40 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (k) clip50 | gradient clip 50 | A1 vs A9 (g1) [P2] | g1 | 40 | -13.6 | [-70.1, 44.4] | 19/40 | -10.7 [-45.8, 14.7], 18/40 | False | False | False |
| 9.9 (k) clip50 | gradient clip 50 | A1 vs A9 (g4) [-] | g4 | 40 | 9.9 | [-39.4, 46.7] | 21/40 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (k) warm02 | warm-up 0.2 | A1 vs A9 (g1) [P2] | g1 | 40 | -24.4 | [-56.4, 12.5] | 16/40 | -10.7 [-45.8, 14.7], 18/40 | False | False | False |
| 9.9 (k) warm02 | warm-up 0.2 | A1 vs A9 (g4) [-] | g4 | 40 | 11.0 | [-38.3, 38.0] | 26/40 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (k) warm06 | warm-up 0.6 | A1 vs A9 (g1) [P2] | g1 | 40 | -11.1 | [-48.3, 18.7] | 18/40 | -10.7 [-45.8, 14.7], 18/40 | False | False | False |
| 9.9 (k) warm06 | warm-up 0.6 | A1 vs A9 (g4) [-] | g4 | 40 | 23.4 | [-9.2, 48.4] | 28/40 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (t) a10nosoc100 | A10, A10P refitted without SOC = 100 % storage cells | A1 vs A10 (g1) [QA10_g1] | g1 | 40 | 23.9 | [-2.1, 57.4] | 29/40 | 22.6 [-6.7, 56.8], 28/40 | none | none | False |
| 9.9 (t) a10nosoc100 | A10, A10P refitted without SOC = 100 % storage cells | A1 vs A10P (g1) [QA10_g1] | g1 | 40 | 28.8 | [-9.7, 50.9] | 28/40 | 29.9 [-17.6, 53.7], 28/40 | none | none | False |
| 9.9 (t) a10nosoc100 | A10, A10P refitted without SOC = 100 % storage cells | A1 vs A10 (g4) [QA10_g4] | g4 | 40 | 27.1 | [-39.1, 62.3] | 26/40 | 26.2 [-42.4, 64.1], 26/40 | none | none | False |
| 9.9 (t) a10nosoc100 | A10, A10P refitted without SOC = 100 % storage cells | A1 vs A10P (g4) [QA10_g4] | g4 | 40 | 40.0 | [-4.1, 64.6] | 28/40 | 41.4 [0.7, 63.3], 30/40 | none | none | False |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A1 vs D* (g1) [P1] | g1 | 40 | -4.8 | [-38.7, 32.4] | 18/40 | -2.4 [-38.3, 32.9], 20/40 | none | none | False |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A1 vs A9 (g1) [P2] | g1 | 40 | -19.2 | [-54.4, 34.4] | 15/40 | -10.7 [-45.8, 14.7], 18/40 | False | False | False |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A1 vs A10 (g1) [QA10_g1] | g1 | 40 | 20.9 | [-16.4, 36.2] | 26/40 | 22.6 [-6.7, 56.8], 28/40 | none | none | False |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A1 vs A10P (g1) [QA10_g1] | g1 | 40 | 27.0 | [-18.3, 47.0] | 26/40 | 29.9 [-17.6, 53.7], 28/40 | none | none | False |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A1 vs D* (g4) [-] | g4 | 40 | 13.7 | [-77.3, 42.1] | 21/40 | 2.2 [-66.1, 41.5], 21/40 | no registered tier | None | None |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A1 vs A9 (g4) [-] | g4 | 40 | 28.2 | [-18.9, 52.2] | 28/40 | 14.2 [5.0, 50.8], 30/40 | no registered tier | None | None |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A1 vs A10 (g4) [QA10_g4] | g4 | 40 | 24.0 | [-37.5, 57.5] | 26/40 | 26.2 [-42.4, 64.1], 26/40 | none | none | False |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A1 vs A10P (g4) [QA10_g4] | g4 | 40 | 36.6 | [-17.5, 63.4] | 28/40 | 41.4 [0.7, 63.3], 30/40 | none | none | False |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A1 vs R1 (g1) [R1_g1] | g1 | 40 | 76.7 | [68.2, 83.2] | 40/40 | 78.5 [69.3, 84.4], 40/40 | True | True | False |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A1 vs A2 (g1) [QH_g1] | g1 | 40 | 20.4 | [-22.2, 48.3] | 26/40 | 25.8 [-1.2, 48.2], 29/40 | none | none | False |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A1 vs A2 (g4) [QH_g4] | g4 | 40 | 27.6 | [-40.7, 68.3] | 24/40 | 25.4 [-15.5, 63.3], 27/40 | none | none | False |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A1 vs A13 (g1) [QT_g1] | g1 | 40 | 27.4 | [-16.5, 49.7] | 26/40 | 30.2 [-1.4, 51.8], 28/40 | none | none | False |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | A15 vs A1 (g4; per-seed endpoints) [K1] | g4 | 40 | -8.8 | [-55.1, 8.7] | 16/40 | -9.9 [-64.1, 13.1], 17/40 | False | False | False |
| 9.9 (l) deltatotal | delta_c on the total rate (A1) | most-test d_c (median d_c -0.070) | g1 | 40 | | | 18 | | False | False | False |
| 9.9 (m) a2_Y05 | A2 tournament Y0 = 0.5 | A1 vs A2 (g1) [QH_g1] | g1 | 40 | 22.3 | [-17.3, 53.2] | 26/40 | 25.8 [-1.2, 48.2], 29/40 | none | none | False |
| 9.9 (m) a2_Y05 | A2 tournament Y0 = 0.5 | A1 vs A2 (g4) [QH_g4] | g4 | 40 | 20.4 | [-22.0, 54.4] | 27/40 | 25.4 [-15.5, 63.3], 27/40 | none | none | False |
| 9.9 (m) a2_Y2 | A2 tournament Y0 = 2 | A1 vs A2 (g1) [QH_g1] | g1 | 40 | 38.3 | [8.2, 57.8] | 32/40 | 25.8 [-1.2, 48.2], 29/40 | N | none | True |
| 9.9 (m) a2_Y2 | A2 tournament Y0 = 2 | A1 vs A2 (g4) [QH_g4] | g4 | 40 | 41.8 | [6.6, 65.5] | 30/40 | 25.4 [-15.5, 63.3], 27/40 | none | none | False |
| 9.9 (m) a2_g015 | A2 tournament gamma = 0.15 | A1 vs A2 (g1) [QH_g1] | g1 | 40 | 25.8 | [-1.2, 48.2] | 29/40 | 25.8 [-1.2, 48.2], 29/40 | none | none | False |
| 9.9 (m) a2_g015 | A2 tournament gamma = 0.15 | A1 vs A2 (g4) [QH_g4] | g4 | 40 | 25.4 | [-15.5, 63.3] | 27/40 | 25.4 [-15.5, 63.3], 27/40 | none | none | False |
| 9.9 (m) a2_g06 | A2 tournament gamma = 0.6 | A1 vs A2 (g1) [QH_g1] | g1 | 40 | 25.8 | [-1.2, 48.2] | 29/40 | 25.8 [-1.2, 48.2], 29/40 | none | none | False |
| 9.9 (m) a2_g06 | A2 tournament gamma = 0.6 | A1 vs A2 (g4) [QH_g4] | g4 | 40 | 25.4 | [-15.5, 63.3] | 27/40 | 25.4 [-15.5, 63.3], 27/40 | none | none | False |
| 9.9 (m) a2_tau0075 | A2 tournament TAU = 0.075 | A1 vs A2 (g1) [QH_g1] | g1 | 40 | 30.4 | [5.5, 53.6] | 31/40 | 25.8 [-1.2, 48.2], 29/40 | none | none | False |
| 9.9 (m) a2_tau0075 | A2 tournament TAU = 0.075 | A1 vs A2 (g4) [QH_g4] | g4 | 40 | 32.3 | [-8.8, 59.0] | 29/40 | 25.4 [-15.5, 63.3], 27/40 | none | none | False |
| 9.9 (m) a2_tau03 | A2 tournament TAU = 0.3 | A1 vs A2 (g1) [QH_g1] | g1 | 40 | 18.1 | [-19.3, 54.9] | 24/40 | 25.8 [-1.2, 48.2], 29/40 | none | none | False |
| 9.9 (m) a2_tau03 | A2 tournament TAU = 0.3 | A1 vs A2 (g4) [QH_g4] | g4 | 40 | 29.8 | [-21.4, 56.0] | 28/40 | 25.4 [-15.5, 63.3], 27/40 | none | none | False |

Notes on how the contrasts were formed (assumptions; the PREREG fixes no arm list for these rows, D028):
- Rows whose runs hold the arms A1, A9, A10, A10P, A11, A12 (and D* where the three D* candidates ran) are scored within the row's own runs. Contrasts that need an arm not in the row (A2, A13, A15, G15, R1, the cell (32, 2) for P3) are not covered.
- deltatotal (A1 only) and the A2 tournament rows (A2 only) replace that arm in a copy of the primary store, in the cells the row ran, and pair it with the primary scores of every other arm on the same conditions; P3 and K2 are not formed (P3 needs the (32, 2) cell, which was not rerun; K2 does not involve A1). Per-seed endpoints for K1 as in the frozen step.
- Contrasts at g4 for P1/P2 carry no registered tier (g4 is an estimated cell); only Q-A10 at g4 and Q-H at g4 have one.
- Several rows use A1 and A9 only (clip, warm-up): the D* candidate set is incomplete there, so P1 and the most-test are not formed.
- 'Changes tier?' compares with the primary-analysis tier (not the effective, downgrade-lowered tier). The ~100 contrasts are unadjusted and no multiplicity control applies; the single would-be tier rise (a2_Y2, Q-H g1) is a descriptive observation that sets nothing.
- NO-OP ROWS, not robustness evidence: a2_g015; a2_g06 (A2 condition scores are bit-identical to the primary in every run of the row: the tournament still picks the 'constant' backbone, so the changed parameter has no effect). selflim at g4 equals the primary (the tournament already chose self_limiting in all five m = 32 folds; only g1 differs): True (bit-identical flags in family_selflim.json).

## B. ISU replication, Test A, S3 (descriptive; plain exact intervals; no tier, no claim word)

Where the interval is marked 'range', no pair of order statistics reaches 95 % and the printed interval is the full range [L(1), L(n)] with the coverage shown (S3, n = 7: coverage 0.984); it is not a 95 % interval. S3 carries no claim and no test (PREREG section 4): read the counts (2/7, 6/7) only. ISU g1 and full differ in n (45 and 62) because different conditions survive the 2-week and 4-week windows; ISU is not blind, not pooled with Samsung, has no error control; claims are 'also holds / does not hold' with their own n. Test A: the pooled n = 118 is 40 unique conditions tested on different replicate cells in up to three folds, so it is not 118 independent conditions and its interval is too narrow; use the per-condition n = 40 row or the three folds.

### ISU_g1
condition scores pooled over outer folds with fold-prefixed keys; unit = (fold, condition); condition-key collisions across folds: 0. D* by fold (arm, complete): {'fold0': ('A11', True), 'fold1': ('A12', True), 'fold2': ('A12', True), 'fold3': ('A12', True), 'fold4': ('A12', True)}. ISU authors' EOL MAPE to be reported beside ours (PREREG 3.4): not available in the run outputs, not computed here; the config generator read the 'full' analogue as the unthinned training side (m unset), see repl configs; Cycling_json calibration not done (stated limitation)

| Block | Arm means pp (n, mean, median) | A1 vs | n | Median L as % reduction | 95 % plain interval (%) or range | Coverage | Positives | Mean pp diff |
|---|---|---|---|---|---|---|---|---|
| pooled | A1 45, 5.50, 5.15; A9 45, 17.43, 13.68; A10 45, 13.42, 7.70; A11 45, 6.51, 6.23; A12 45, 5.59, 4.90; D* 45, 5.76, 5.18 | D* | 45 | 0.3 | [-7.2, 10.1] | 0.964 | 23/45 | 0.257 |
| pooled | A1 45, 5.50, 5.15; A9 45, 17.43, 13.68; A10 45, 13.42, 7.70; A11 45, 6.51, 6.23; A12 45, 5.59, 4.90; D* 45, 5.76, 5.18 | A9 | 45 | 61.7 | [48.4, 74.0] | 0.964 | 39/45 | 11.926 |
| pooled | A1 45, 5.50, 5.15; A9 45, 17.43, 13.68; A10 45, 13.42, 7.70; A11 45, 6.51, 6.23; A12 45, 5.59, 4.90; D* 45, 5.76, 5.18 | A10 | 45 | 25.5 | [8.2, 56.6] | 0.964 | 35/45 | 7.920 |
| pooled | A1 45, 5.50, 5.15; A9 45, 17.43, 13.68; A10 45, 13.42, 7.70; A11 45, 6.51, 6.23; A12 45, 5.59, 4.90; D* 45, 5.76, 5.18 | A11 | 45 | 14.2 | [-4.1, 27.5] | 0.964 | 27/45 | 1.001 |
| pooled | A1 45, 5.50, 5.15; A9 45, 17.43, 13.68; A10 45, 13.42, 7.70; A11 45, 6.51, 6.23; A12 45, 5.59, 4.90; D* 45, 5.76, 5.18 | A12 | 45 | 2.0 | [-4.5, 8.6] | 0.964 | 24/45 | 0.085 |
| fold0 | A1 8, 5.79, 4.93; A9 8, 18.04, 14.37; A10 8, 8.44, 7.88; A11 8, 7.94, 8.08; A12 8, 6.97, 7.54; D* 8, 7.94, 8.08 | D* | 8 | 29.3 | range [-27.6, 53.9] | 0.992 | 6/8 | 2.158 |
| fold0 | A1 8, 5.79, 4.93; A9 8, 18.04, 14.37; A10 8, 8.44, 7.88; A11 8, 7.94, 8.08; A12 8, 6.97, 7.54; D* 8, 7.94, 8.08 | A9 | 8 | 66.0 | range [18.2, 85.1] | 0.992 | 8/8 | 12.258 |
| fold0 | A1 8, 5.79, 4.93; A9 8, 18.04, 14.37; A10 8, 8.44, 7.88; A11 8, 7.94, 8.08; A12 8, 6.97, 7.54; D* 8, 7.94, 8.08 | A10 | 8 | 22.2 | range [-43.0, 69.6] | 0.992 | 6/8 | 2.650 |
| fold0 | A1 8, 5.79, 4.93; A9 8, 18.04, 14.37; A10 8, 8.44, 7.88; A11 8, 7.94, 8.08; A12 8, 6.97, 7.54; D* 8, 7.94, 8.08 | A11 | 8 | 29.3 | range [-27.6, 53.9] | 0.992 | 6/8 | 2.158 |
| fold0 | A1 8, 5.79, 4.93; A9 8, 18.04, 14.37; A10 8, 8.44, 7.88; A11 8, 7.94, 8.08; A12 8, 6.97, 7.54; D* 8, 7.94, 8.08 | A12 | 8 | 9.6 | range [-3.3, 51.8] | 0.992 | 7/8 | 1.188 |
| fold1 | A1 8, 5.35, 5.45; A9 8, 8.04, 8.29; A10 8, 13.29, 6.57; A11 8, 7.24, 6.77; A12 8, 4.43, 4.25; D* 8, 4.43, 4.25 | D* | 8 | -17.5 | range [-155.3, 10.1] | 0.992 | 3/8 | -0.919 |
| fold1 | A1 8, 5.35, 5.45; A9 8, 8.04, 8.29; A10 8, 13.29, 6.57; A11 8, 7.24, 6.77; A12 8, 4.43, 4.25; D* 8, 4.43, 4.25 | A9 | 8 | 39.8 | range [-46.8, 61.2] | 0.992 | 5/8 | 2.686 |
| fold1 | A1 8, 5.35, 5.45; A9 8, 8.04, 8.29; A10 8, 13.29, 6.57; A11 8, 7.24, 6.77; A12 8, 4.43, 4.25; D* 8, 4.43, 4.25 | A10 | 8 | 29.9 | range [-65.7, 83.9] | 0.992 | 5/8 | 7.939 |
| fold1 | A1 8, 5.35, 5.45; A9 8, 8.04, 8.29; A10 8, 13.29, 6.57; A11 8, 7.24, 6.77; A12 8, 4.43, 4.25; D* 8, 4.43, 4.25 | A11 | 8 | 24.5 | range [9.6, 50.0] | 0.992 | 8/8 | 1.892 |
| fold1 | A1 8, 5.35, 5.45; A9 8, 8.04, 8.29; A10 8, 13.29, 6.57; A11 8, 7.24, 6.77; A12 8, 4.43, 4.25; D* 8, 4.43, 4.25 | A12 | 8 | -17.5 | range [-155.3, 10.1] | 0.992 | 3/8 | -0.919 |
| fold2 | A1 10, 6.61, 5.66; A9 10, 13.11, 11.73; A10 10, 8.66, 6.14; A11 10, 6.49, 6.46; A12 10, 6.47, 5.10; D* 10, 6.47, 5.10 | D* | 10 | 3.8 | [-27.0, 25.6] | 0.979 | 5/10 | -0.140 |
| fold2 | A1 10, 6.61, 5.66; A9 10, 13.11, 11.73; A10 10, 8.66, 6.14; A11 10, 6.49, 6.46; A12 10, 6.47, 5.10; D* 10, 6.47, 5.10 | A9 | 10 | 45.9 | [1.8, 78.4] | 0.979 | 9/10 | 6.497 |
| fold2 | A1 10, 6.61, 5.66; A9 10, 13.11, 11.73; A10 10, 8.66, 6.14; A11 10, 6.49, 6.46; A12 10, 6.47, 5.10; D* 10, 6.47, 5.10 | A10 | 10 | 8.3 | [-9.7, 45.6] | 0.979 | 8/10 | 2.053 |
| fold2 | A1 10, 6.61, 5.66; A9 10, 13.11, 11.73; A10 10, 8.66, 6.14; A11 10, 6.49, 6.46; A12 10, 6.47, 5.10; D* 10, 6.47, 5.10 | A11 | 10 | -17.2 | [-47.2, 32.1] | 0.979 | 4/10 | -0.118 |
| fold2 | A1 10, 6.61, 5.66; A9 10, 13.11, 11.73; A10 10, 8.66, 6.14; A11 10, 6.49, 6.46; A12 10, 6.47, 5.10; D* 10, 6.47, 5.10 | A12 | 10 | 3.8 | [-27.0, 25.6] | 0.979 | 5/10 | -0.140 |
| fold3 | A1 9, 4.78, 4.18; A9 9, 29.69, 22.08; A10 9, 24.71, 11.77; A11 9, 6.11, 5.27; A12 9, 5.33, 5.18; D* 9, 5.33, 5.18 | D* | 9 | -0.0 | [-15.6, 35.2] | 0.961 | 4/9 | 0.547 |
| fold3 | A1 9, 4.78, 4.18; A9 9, 29.69, 22.08; A10 9, 24.71, 11.77; A11 9, 6.11, 5.27; A12 9, 5.33, 5.18; D* 9, 5.33, 5.18 | A9 | 9 | 88.2 | [48.4, 93.6] | 0.961 | 8/9 | 24.909 |
| fold3 | A1 9, 4.78, 4.18; A9 9, 29.69, 22.08; A10 9, 24.71, 11.77; A11 9, 6.11, 5.27; A12 9, 5.33, 5.18; D* 9, 5.33, 5.18 | A10 | 9 | 64.5 | [16.7, 85.4] | 0.961 | 9/9 | 19.931 |
| fold3 | A1 9, 4.78, 4.18; A9 9, 29.69, 22.08; A10 9, 24.71, 11.77; A11 9, 6.11, 5.27; A12 9, 5.33, 5.18; D* 9, 5.33, 5.18 | A11 | 9 | 7.9 | [-17.6, 56.7] | 0.961 | 5/9 | 1.331 |
| fold3 | A1 9, 4.78, 4.18; A9 9, 29.69, 22.08; A10 9, 24.71, 11.77; A11 9, 6.11, 5.27; A12 9, 5.33, 5.18; D* 9, 5.33, 5.18 | A12 | 9 | -0.0 | [-15.6, 35.2] | 0.961 | 4/9 | 0.547 |
| fold4 | A1 10, 4.95, 4.78; A9 10, 17.74, 18.35; A10 10, 12.13, 8.03; A11 10, 5.13, 4.94; A12 10, 4.76, 4.75; D* 10, 4.76, 4.75 | D* | 10 | -3.4 | [-35.6, 24.1] | 0.979 | 5/10 | -0.187 |
| fold4 | A1 10, 4.95, 4.78; A9 10, 17.74, 18.35; A10 10, 12.13, 8.03; A11 10, 5.13, 4.94; A12 10, 4.76, 4.75; D* 10, 4.76, 4.75 | A9 | 10 | 76.2 | [1.5, 82.4] | 0.979 | 9/10 | 12.795 |
| fold4 | A1 10, 4.95, 4.78; A9 10, 17.74, 18.35; A10 10, 12.13, 8.03; A11 10, 5.13, 4.94; A12 10, 4.76, 4.75; D* 10, 4.76, 4.75 | A10 | 10 | 44.2 | [-12.4, 82.6] | 0.979 | 7/10 | 7.177 |
| fold4 | A1 10, 4.95, 4.78; A9 10, 17.74, 18.35; A10 10, 12.13, 8.03; A11 10, 5.13, 4.94; A12 10, 4.76, 4.75; D* 10, 4.76, 4.75 | A11 | 10 | -4.9 | [-36.8, 31.3] | 0.979 | 4/10 | 0.185 |
| fold4 | A1 10, 4.95, 4.78; A9 10, 17.74, 18.35; A10 10, 12.13, 8.03; A11 10, 5.13, 4.94; A12 10, 4.76, 4.75; D* 10, 4.76, 4.75 | A12 | 10 | -3.4 | [-35.6, 24.1] | 0.979 | 5/10 | -0.187 |

### ISU_full
condition scores pooled over outer folds with fold-prefixed keys; unit = (fold, condition); condition-key collisions across folds: 0. D* by fold (arm, complete): {'fold0': ('A11', True), 'fold1': ('A12', True), 'fold2': ('A12', True), 'fold3': ('A11', True), 'fold4': ('A12', True)}. ISU authors' EOL MAPE to be reported beside ours (PREREG 3.4): not available in the run outputs, not computed here; the config generator read the 'full' analogue as the unthinned training side (m unset), see repl configs; Cycling_json calibration not done (stated limitation)

| Block | Arm means pp (n, mean, median) | A1 vs | n | Median L as % reduction | 95 % plain interval (%) or range | Coverage | Positives | Mean pp diff |
|---|---|---|---|---|---|---|---|---|
| pooled | A1 62, 6.01, 5.30; A9 62, 8.49, 7.37; A10 62, 7.04, 6.12; A11 62, 5.81, 5.30; A12 62, 4.98, 4.15; D* 62, 5.08, 4.18 | D* | 62 | -22.7 | [-32.7, -9.0] | 0.970 | 13/62 | -0.934 |
| pooled | A1 62, 6.01, 5.30; A9 62, 8.49, 7.37; A10 62, 7.04, 6.12; A11 62, 5.81, 5.30; A12 62, 4.98, 4.15; D* 62, 5.08, 4.18 | A9 | 62 | 20.6 | [5.1, 37.0] | 0.970 | 42/62 | 2.480 |
| pooled | A1 62, 6.01, 5.30; A9 62, 8.49, 7.37; A10 62, 7.04, 6.12; A11 62, 5.81, 5.30; A12 62, 4.98, 4.15; D* 62, 5.08, 4.18 | A10 | 62 | 12.1 | [6.9, 18.2] | 0.970 | 45/62 | 1.027 |
| pooled | A1 62, 6.01, 5.30; A9 62, 8.49, 7.37; A10 62, 7.04, 6.12; A11 62, 5.81, 5.30; A12 62, 4.98, 4.15; D* 62, 5.08, 4.18 | A11 | 62 | -10.7 | [-23.6, 3.6] | 0.970 | 24/62 | -0.198 |
| pooled | A1 62, 6.01, 5.30; A9 62, 8.49, 7.37; A10 62, 7.04, 6.12; A11 62, 5.81, 5.30; A12 62, 4.98, 4.15; D* 62, 5.08, 4.18 | A12 | 62 | -22.7 | [-32.3, -9.6] | 0.970 | 12/62 | -1.032 |
| fold0 | A1 12, 5.40, 4.58; A9 12, 7.66, 8.16; A10 12, 6.83, 6.04; A11 12, 5.71, 4.82; A12 12, 4.93, 4.15; D* 12, 5.71, 4.82 | D* | 12 | -7.3 | [-34.3, 13.5] | 0.961 | 5/12 | 0.312 |
| fold0 | A1 12, 5.40, 4.58; A9 12, 7.66, 8.16; A10 12, 6.83, 6.04; A11 12, 5.71, 4.82; A12 12, 4.93, 4.15; D* 12, 5.71, 4.82 | A9 | 12 | 30.1 | [-3.3, 54.3] | 0.961 | 8/12 | 2.262 |
| fold0 | A1 12, 5.40, 4.58; A9 12, 7.66, 8.16; A10 12, 6.83, 6.04; A11 12, 5.71, 4.82; A12 12, 4.93, 4.15; D* 12, 5.71, 4.82 | A10 | 12 | 13.1 | [-1.6, 26.7] | 0.961 | 9/12 | 1.432 |
| fold0 | A1 12, 5.40, 4.58; A9 12, 7.66, 8.16; A10 12, 6.83, 6.04; A11 12, 5.71, 4.82; A12 12, 4.93, 4.15; D* 12, 5.71, 4.82 | A11 | 12 | -7.3 | [-34.3, 13.5] | 0.961 | 5/12 | 0.312 |
| fold0 | A1 12, 5.40, 4.58; A9 12, 7.66, 8.16; A10 12, 6.83, 6.04; A11 12, 5.71, 4.82; A12 12, 4.93, 4.15; D* 12, 5.71, 4.82 | A12 | 12 | -12.0 | [-27.9, -1.5] | 0.961 | 2/12 | -0.464 |
| fold1 | A1 13, 6.97, 6.56; A9 13, 11.20, 9.83; A10 13, 7.86, 5.90; A11 13, 5.83, 5.06; A12 13, 5.58, 4.74; D* 13, 5.58, 4.74 | D* | 13 | -22.8 | [-94.6, 6.2] | 0.978 | 3/13 | -1.393 |
| fold1 | A1 13, 6.97, 6.56; A9 13, 11.20, 9.83; A10 13, 7.86, 5.90; A11 13, 5.83, 5.06; A12 13, 5.58, 4.74; D* 13, 5.58, 4.74 | A9 | 13 | 28.0 | [13.2, 55.4] | 0.978 | 12/13 | 4.227 |
| fold1 | A1 13, 6.97, 6.56; A9 13, 11.20, 9.83; A10 13, 7.86, 5.90; A11 13, 5.83, 5.06; A12 13, 5.58, 4.74; D* 13, 5.58, 4.74 | A10 | 13 | 10.8 | [-76.1, 19.0] | 0.978 | 9/13 | 0.887 |
| fold1 | A1 13, 6.97, 6.56; A9 13, 11.20, 9.83; A10 13, 7.86, 5.90; A11 13, 5.83, 5.06; A12 13, 5.58, 4.74; D* 13, 5.58, 4.74 | A11 | 13 | -19.4 | [-82.1, 0.8] | 0.978 | 3/13 | -1.138 |
| fold1 | A1 13, 6.97, 6.56; A9 13, 11.20, 9.83; A10 13, 7.86, 5.90; A11 13, 5.83, 5.06; A12 13, 5.58, 4.74; D* 13, 5.58, 4.74 | A12 | 13 | -22.8 | [-94.6, 6.2] | 0.978 | 3/13 | -1.393 |
| fold2 | A1 12, 6.87, 5.60; A9 12, 7.28, 5.39; A10 12, 6.38, 5.51; A11 12, 4.96, 3.63; A12 12, 5.18, 4.00; D* 12, 5.18, 4.00 | D* | 12 | -35.8 | [-66.5, -1.8] | 0.961 | 1/12 | -1.690 |
| fold2 | A1 12, 6.87, 5.60; A9 12, 7.28, 5.39; A10 12, 6.38, 5.51; A11 12, 4.96, 3.63; A12 12, 5.18, 4.00; D* 12, 5.18, 4.00 | A9 | 12 | -8.4 | [-43.7, 24.3] | 0.961 | 5/12 | 0.415 |
| fold2 | A1 12, 6.87, 5.60; A9 12, 7.28, 5.39; A10 12, 6.38, 5.51; A11 12, 4.96, 3.63; A12 12, 5.18, 4.00; D* 12, 5.18, 4.00 | A10 | 12 | 8.2 | [-43.1, 19.5] | 0.961 | 7/12 | -0.490 |
| fold2 | A1 12, 6.87, 5.60; A9 12, 7.28, 5.39; A10 12, 6.38, 5.51; A11 12, 4.96, 3.63; A12 12, 5.18, 4.00; D* 12, 5.18, 4.00 | A11 | 12 | -42.2 | [-82.3, -20.0] | 0.961 | 1/12 | -1.907 |
| fold2 | A1 12, 6.87, 5.60; A9 12, 7.28, 5.39; A10 12, 6.38, 5.51; A11 12, 4.96, 3.63; A12 12, 5.18, 4.00; D* 12, 5.18, 4.00 | A12 | 12 | -35.8 | [-66.5, -1.8] | 0.961 | 1/12 | -1.690 |
| fold3 | A1 12, 5.78, 5.51; A9 12, 7.98, 7.37; A10 12, 7.60, 7.75; A11 12, 4.79, 4.88; A12 12, 5.06, 4.62; D* 12, 4.79, 4.88 | D* | 12 | -20.0 | [-56.3, -4.6] | 0.961 | 2/12 | -0.989 |
| fold3 | A1 12, 5.78, 5.51; A9 12, 7.98, 7.37; A10 12, 7.60, 7.75; A11 12, 4.79, 4.88; A12 12, 5.06, 4.62; D* 12, 4.79, 4.88 | A9 | 12 | 14.9 | [-24.1, 39.2] | 0.961 | 8/12 | 2.199 |
| fold3 | A1 12, 5.78, 5.51; A9 12, 7.98, 7.37; A10 12, 7.60, 7.75; A11 12, 4.79, 4.88; A12 12, 5.06, 4.62; D* 12, 4.79, 4.88 | A10 | 12 | 17.4 | [2.3, 34.5] | 0.961 | 10/12 | 1.826 |
| fold3 | A1 12, 5.78, 5.51; A9 12, 7.98, 7.37; A10 12, 7.60, 7.75; A11 12, 4.79, 4.88; A12 12, 5.06, 4.62; D* 12, 4.79, 4.88 | A11 | 12 | -20.0 | [-56.3, -4.6] | 0.961 | 2/12 | -0.989 |
| fold3 | A1 12, 5.78, 5.51; A9 12, 7.98, 7.37; A10 12, 7.60, 7.75; A11 12, 4.79, 4.88; A12 12, 5.06, 4.62; D* 12, 4.79, 4.88 | A12 | 12 | -15.2 | [-56.6, 17.8] | 0.961 | 4/12 | -0.720 |
| fold4 | A1 13, 5.04, 4.69; A9 13, 8.14, 8.17; A10 13, 6.49, 5.25; A11 13, 7.61, 7.29; A12 13, 4.16, 3.75; D* 13, 4.16, 3.75 | D* | 13 | -24.4 | [-35.7, -1.6] | 0.978 | 2/13 | -0.874 |
| fold4 | A1 13, 5.04, 4.69; A9 13, 8.14, 8.17; A10 13, 6.49, 5.25; A11 13, 7.61, 7.29; A12 13, 4.16, 3.75; D* 13, 4.16, 3.75 | A9 | 13 | 45.9 | [-13.3, 58.3] | 0.978 | 9/13 | 3.102 |
| fold4 | A1 13, 5.04, 4.69; A9 13, 8.14, 8.17; A10 13, 6.49, 5.25; A11 13, 7.61, 7.29; A12 13, 4.16, 3.75; D* 13, 4.16, 3.75 | A10 | 13 | 18.2 | [-1.7, 45.3] | 0.978 | 10/13 | 1.457 |
| fold4 | A1 13, 5.04, 4.69; A9 13, 8.14, 8.17; A10 13, 6.49, 5.25; A11 13, 7.61, 7.29; A12 13, 4.16, 3.75; D* 13, 4.16, 3.75 | A11 | 13 | 35.7 | [24.7, 49.2] | 0.978 | 13/13 | 2.578 |
| fold4 | A1 13, 5.04, 4.69; A9 13, 8.14, 8.17; A10 13, 6.49, 5.25; A11 13, 7.61, 7.29; A12 13, 4.16, 3.75; D* 13, 4.16, 3.75 | A12 | 13 | -24.4 | [-35.7, -1.6] | 0.978 | 2/13 | -0.874 |

### TestA
condition scores pooled over outer folds with fold-prefixed keys; unit = (fold, condition); condition-key collisions across folds: 78. D* by fold (arm, complete): {'fold0': ('A9', False), 'fold1': ('A9', False), 'fold2': ('A9', False)}. D* candidate set incomplete (arms A1 A2 A9 / A1 A9 A10 A10P only): D* is not formed; PREREG names no arms for S3, the S2 arms were assumed by the config generator

| Block | Arm means pp (n, mean, median) | A1 vs | n | Median L as % reduction | 95 % plain interval (%) or range | Coverage | Positives | Mean pp diff |
|---|---|---|---|---|---|---|---|---|
| pooled (n = fold x condition, NOT independent) | A1 118, 0.53, 0.33; A2 118, 0.74, 0.54; A9 118, 0.60, 0.30 | A9 | 118 | 0.4 | [-31.8, 16.4] | 0.966 | 60/118 | 0.072 |
| pooled (n = fold x condition, NOT independent) | A1 118, 0.53, 0.33; A2 118, 0.74, 0.54; A9 118, 0.60, 0.30 | A2 | 118 | 16.4 | [2.7, 36.4] | 0.966 | 75/118 | 0.214 |
| per condition, mean over folds (n = 40 conditions) | A1 40, 0.52, 0.34; A2 40, 0.75, 0.59; A9 40, 0.60, 0.45 | A9 | 40 | 12.1 | [-7.0, 27.2] | 0.962 | 23/40 | 0.079 |
| per condition, mean over folds (n = 40 conditions) | A1 40, 0.52, 0.34; A2 40, 0.75, 0.59; A9 40, 0.60, 0.45 | A2 | 40 | 23.7 | [5.8, 36.8] | 0.962 | 29/40 | 0.227 |
| fold0 | A1 39, 0.47, 0.35; A2 39, 0.61, 0.56; A9 39, 0.36, 0.25 | A9 | 39 | -32.2 | [-88.4, 3.8] | 0.976 | 14/39 | -0.112 |
| fold0 | A1 39, 0.47, 0.35; A2 39, 0.61, 0.56; A9 39, 0.36, 0.25 | A2 | 39 | 13.8 | [-8.2, 44.9] | 0.976 | 24/39 | 0.142 |
| fold1 | A1 39, 0.63, 0.29; A2 39, 0.93, 0.54; A9 39, 0.57, 0.28 | A9 | 39 | 0.1 | [-45.7, 16.7] | 0.976 | 20/39 | -0.066 |
| fold1 | A1 39, 0.63, 0.29; A2 39, 0.93, 0.54; A9 39, 0.57, 0.28 | A2 | 39 | 28.1 | [2.4, 53.7] | 0.976 | 27/39 | 0.300 |
| fold2 | A1 40, 0.48, 0.34; A2 40, 0.68, 0.54; A9 40, 0.86, 0.54 | A9 | 40 | 31.6 | [-3.9, 47.8] | 0.962 | 26/40 | 0.387 |
| fold2 | A1 40, 0.48, 0.34; A2 40, 0.68, 0.54; A9 40, 0.86, 0.54 | A2 | 40 | 14.2 | [-10.4, 54.9] | 0.962 | 24/40 | 0.199 |

### S3
condition scores pooled over outer folds with fold-prefixed keys; unit = (fold, condition); condition-key collisions across folds: 0. D* by fold (arm, complete): {'fold0': ('A9', False)}. D* candidate set incomplete (arms A1 A2 A9 / A1 A9 A10 A10P only): D* is not formed; PREREG names no arms for S3, the S2 arms were assumed by the config generator

| Block | Arm means pp (n, mean, median) | A1 vs | n | Median L as % reduction | 95 % plain interval (%) or range | Coverage | Positives | Mean pp diff |
|---|---|---|---|---|---|---|---|---|
| pooled | A1 7, 0.21, 0.18; A9 7, 0.19, 0.21; A10 7, 0.62, 0.71; A10P 7, 0.68, 0.73 | A9 | 7 | -46.9 | range [-100.1, 55.2] | 0.984 | 2/7 | -0.026 |
| pooled | A1 7, 0.21, 0.18; A9 7, 0.19, 0.21; A10 7, 0.62, 0.71; A10P 7, 0.68, 0.73 | A10 | 7 | 58.4 | range [-1.0, 82.7] | 0.984 | 6/7 | 0.406 |
| pooled | A1 7, 0.21, 0.18; A9 7, 0.19, 0.21; A10 7, 0.62, 0.71; A10P 7, 0.68, 0.73 | A10P | 7 | 56.0 | range [-1.3, 86.4] | 0.984 | 6/7 | 0.464 |
| fold0 | A1 7, 0.21, 0.18; A9 7, 0.19, 0.21; A10 7, 0.62, 0.71; A10P 7, 0.68, 0.73 | A9 | 7 | -46.9 | range [-100.1, 55.2] | 0.984 | 2/7 | -0.026 |
| fold0 | A1 7, 0.21, 0.18; A9 7, 0.19, 0.21; A10 7, 0.62, 0.71; A10P 7, 0.68, 0.73 | A10 | 7 | 58.4 | range [-1.0, 82.7] | 0.984 | 6/7 | 0.406 |
| fold0 | A1 7, 0.21, 0.18; A9 7, 0.19, 0.21; A10 7, 0.62, 0.71; A10P 7, 0.68, 0.73 | A10P | 7 | 56.0 | range [-1.3, 86.4] | 0.984 | 6/7 | 0.464 |

## C. Not run / unclear

- Runs not run or failed: none (all 209 inputs have metrics.json and rc=0).
- Rows struck by PREREG (first-check-up reference, forecast failures under the window cap, separate h_cal/h_cyc for A2, SNL replication): not run, printed as such (C.4 of the appendix).
- Rows (a), (j), (q), (s), (u) are outputs of the frozen statistics step (contrasts_v4_B.json: lab_rows, downgrade, dependence_sensitivity, plain_descriptive, crate_ablation; margins.json); (f), (h), (o) are the downgrade rows already in the frozen step. Rows (b) per stage, (c), (d), (e), (v), (vi) are NOT in the frozen analysis directory; they are computed in section D by run_rows.py.
- ISU authors' EOL MAPE beside ours: not in the run outputs, not computed. Whether 'full' means the unthinned training side (the PREREG 3.4 wording: 'full-data analogue') or the g4 analogue is stated in the generator (unthinned, m unset).
- Test A: 3 folds x 39-40 conditions (118 fold x condition units = 40 unique conditions); the per-condition n = 40 view is printed beside the pooled one; R_LOO yardstick not computed here.
- The contrast for the A2 and deltatotal rows pairs a variant arm with primary scores of other arms; PREREG 9.9 does not state this, it is the only reading available without rerunning those arms.

CHANGE LOG (re-check 2): (a) row (d) intervals were printed upper-bound first (bounds swapped in the percent conversion); fixed, row_d_two_stage_bootstrap.json and D3 regenerated, no other number changed. (b) row (e): A1 vs A13 (g1) is now computed from margins.json and entry() (it was wrongly listed as having no margin entry), and K1 and K2 are listed explicitly in D4. All other rows are unchanged.

## D. Rows (b) per stage, (c), (d), (e), (v), (vi): computed after the frozen step from the existing run outputs (run_rows.py; frozen functions, read-only; descriptive, no consequence)

### D1. (b) per laboratory and per stage (stats_ext.lab_stage_rows; mean pp = comparator - target, positive favours the target arm)

| Contrast | Block | n | Mean pp diff | Median L as % reduction | Positives |
|---|---|---|---|---|---|
| P1: A1 vs D* g1 | lab HM | 17 | 0.455 | 25.5 | 11/17 |
| P1: A1 vs D* g1 | lab INT | 19 | -0.106 | -14.0 | 7/19 |
| P1: A1 vs D* g1 | lab SIE | 4 | -0.071 | -3.0 | 2/4 |
| P1: A1 vs D* g1 | stage 1 | 25 | 0.199 | -6.7 | 12/25 |
| P1: A1 vs D* g1 | stage 2 | 15 | 0.031 | 3.0 | 8/15 |
| P2: A1 vs A9 g1 | lab HM | 17 | 0.651 | 5.9 | 10/17 |
| P2: A1 vs A9 g1 | lab INT | 19 | -0.056 | -16.7 | 7/19 |
| P2: A1 vs A9 g1 | lab SIE | 4 | -0.195 | -21.2 | 1/4 |
| P2: A1 vs A9 g1 | stage 1 | 25 | 0.258 | -6.7 | 11/25 |
| P2: A1 vs A9 g1 | stage 2 | 15 | 0.185 | -25.3 | 7/15 |
| R1_g1: A1 vs R1 g1 | lab HM | 17 | 3.783 | 82.2 | 17/17 |
| R1_g1: A1 vs R1 g1 | lab INT | 19 | 1.446 | 76.8 | 19/19 |
| R1_g1: A1 vs R1 g1 | lab SIE | 4 | 3.052 | 69.1 | 4/4 |
| R1_g1: A1 vs R1 g1 | stage 1 | 25 | 2.802 | 80.7 | 25/25 |
| R1_g1: A1 vs R1 g1 | stage 2 | 15 | 2.263 | 75.0 | 15/15 |
| QA10_g1: A1 vs A10 | lab HM | 17 | 1.013 | 57.6 | 15/17 |
| QA10_g1: A1 vs A10 | lab INT | 19 | -0.039 | 9.7 | 11/19 |
| QA10_g1: A1 vs A10 | lab SIE | 4 | 0.043 | 10.3 | 2/4 |
| QA10_g1: A1 vs A10 | stage 1 | 25 | 0.263 | 18.9 | 15/25 |
| QA10_g1: A1 vs A10 | stage 2 | 15 | 0.673 | 34.3 | 13/15 |
| QA10_g1: A1 vs A10P | lab HM | 17 | 1.090 | 52.6 | 15/17 |
| QA10_g1: A1 vs A10P | lab INT | 19 | -0.060 | 5.2 | 11/19 |
| QA10_g1: A1 vs A10P | lab SIE | 4 | 0.845 | 1.2 | 2/4 |
| QA10_g1: A1 vs A10P | stage 1 | 25 | 0.396 | 19.4 | 16/25 |
| QA10_g1: A1 vs A10P | stage 2 | 15 | 0.724 | 32.8 | 12/15 |
| QA10_g4: A1 vs A10 | lab HM | 17 | -0.067 | 31.3 | 11/17 |
| QA10_g4: A1 vs A10 | lab INT | 19 | 0.036 | 9.8 | 11/19 |
| QA10_g4: A1 vs A10 | lab SIE | 4 | 0.969 | 74.4 | 4/4 |
| QA10_g4: A1 vs A10 | stage 1 | 25 | 0.200 | 19.8 | 17/25 |
| QA10_g4: A1 vs A10 | stage 2 | 15 | -0.105 | 31.3 | 9/15 |
| QA10_g4: A1 vs A10P | lab HM | 17 | 0.219 | 36.8 | 11/17 |
| QA10_g4: A1 vs A10P | lab INT | 19 | 0.178 | 34.5 | 15/19 |
| QA10_g4: A1 vs A10P | lab SIE | 4 | 0.896 | 69.0 | 4/4 |
| QA10_g4: A1 vs A10P | stage 1 | 25 | 0.385 | 41.2 | 19/25 |
| QA10_g4: A1 vs A10P | stage 2 | 15 | 0.071 | 42.4 | 11/15 |
| QH_g1: A1 vs A2 | lab HM | 17 | 0.930 | 46.0 | 16/17 |
| QH_g1: A1 vs A2 | lab INT | 19 | 0.132 | 8.2 | 11/19 |
| QH_g1: A1 vs A2 | lab SIE | 4 | 0.258 | 6.7 | 2/4 |
| QH_g1: A1 vs A2 | stage 1 | 25 | 0.517 | 26.6 | 17/25 |
| QH_g1: A1 vs A2 | stage 2 | 15 | 0.428 | 25.1 | 12/15 |
| QH_g4: A1 vs A2 | lab HM | 17 | 0.503 | 28.7 | 14/17 |
| QH_g4: A1 vs A2 | lab INT | 19 | 0.120 | -5.4 | 9/19 |
| QH_g4: A1 vs A2 | lab SIE | 4 | 0.376 | 48.7 | 4/4 |
| QH_g4: A1 vs A2 | stage 1 | 25 | 0.421 | 46.1 | 18/25 |
| QH_g4: A1 vs A2 | stage 2 | 15 | 0.120 | 10.7 | 9/15 |
| QT_g1: A1 vs A13 | lab HM | 17 | 0.562 | 29.5 | 12/17 |
| QT_g1: A1 vs A13 | lab INT | 19 | 0.166 | 32.7 | 13/19 |
| QT_g1: A1 vs A13 | lab SIE | 4 | 0.319 | 25.4 | 3/4 |
| QT_g1: A1 vs A13 | stage 1 | 25 | 0.355 | 32.7 | 19/25 |
| QT_g1: A1 vs A13 | stage 2 | 15 | 0.341 | 19.3 | 9/15 |
| K1: A15 vs A1 g4 (per-seed) | lab HM | 17 | -0.008 | -20.7 | 6/17 |
| K1: A15 vs A1 g4 (per-seed) | lab INT | 19 | -0.002 | 1.8 | 11/19 |
| K1: A15 vs A1 g4 (per-seed) | lab SIE | 4 | -0.718 | -213.1 | 0/4 |
| K1: A15 vs A1 g4 (per-seed) | stage 1 | 25 | -0.110 | -16.2 | 10/25 |
| K1: A15 vs A1 g4 (per-seed) | stage 2 | 15 | -0.020 | -2.0 | 7/15 |
| K2: A15 vs G15 g4 (per-seed) | lab HM | 17 | -0.052 | -1.3 | 8/17 |
| K2: A15 vs G15 g4 (per-seed) | lab INT | 19 | -0.006 | 4.5 | 12/19 |
| K2: A15 vs G15 g4 (per-seed) | lab SIE | 4 | -0.386 | -55.0 | 2/4 |
| K2: A15 vs G15 g4 (per-seed) | stage 1 | 25 | -0.034 | 0.8 | 14/25 |
| K2: A15 vs G15 g4 (per-seed) | stage 2 | 15 | -0.114 | 1.4 | 8/15 |

### D2. (c) leave-one-laboratory-out (frozen sign rule at the primary final levels; row_tiers on the primary store without one laboratory's conditions)

| Lab removed | Conditions removed | Contrast | n left | Median L as % reduction | 95 % interval (%) | Positives | Tier it would reach | Primary tier |
|---|---|---|---|---|---|---|---|---|
| HM | 17 | P1: A1 vs D* g1 | 23 | -13.6 | [-37.7, 19.8] | 9/23 | none | none |
| HM | 17 | P2: A1 vs A9 g1 | 23 | -16.7 | [-37.7, 11.1] | 8/23 | False | False |
| HM | 17 | R1_g1: A1 vs R1 g1 | 23 | 74.4 | [68.8, 83.4] | 23/23 | True | True |
| HM | 17 | QA10_g1: A1 vs A10 | 23 | 9.7 | [-18.7, 23.2] | 13/23 | none | none |
| HM | 17 | QA10_g1: A1 vs A10P | 23 | 5.2 | [-101.7, 32.2] | 13/23 | none | none |
| HM | 17 | QA10_g4: A1 vs A10 | 23 | 19.8 | [-42.4, 65.4] | 15/23 | none | none |
| HM | 17 | QA10_g4: A1 vs A10P | 23 | 41.5 | [2.9, 62.5] | 19/23 | none | none |
| HM | 17 | QH_g1: A1 vs A2 | 23 | 8.2 | [-17.3, 44.6] | 13/23 | none | none |
| HM | 17 | QH_g4: A1 vs A2 | 23 | 17.8 | [-49.5, 62.0] | 13/23 | none | none |
| HM | 17 | QT_g1: A1 vs A13 | 23 | 31.0 | [-16.8, 53.1] | 16/23 | none | none |
| HM | 17 | K1: A15 vs A1 g4 (per-seed) | 23 | -2.0 | [-64.1, 13.1] | 11/23 | False | False |
| HM | 17 | K2: A15 vs G15 g4 (per-seed) | 23 | 4.5 | [-12.9, 14.9] | 14/23 | none | none |
| INT | 19 | P1: A1 vs D* g1 | 21 | 12.8 | [-70.0, 52.9] | 13/21 | none | none |
| INT | 19 | P2: A1 vs A9 g1 | 21 | 3.3 | [-57.7, 70.8] | 11/21 | False | False |
| INT | 19 | R1_g1: A1 vs R1 g1 | 21 | 80.7 | [68.9, 86.7] | 21/21 | True | True |
| INT | 19 | QA10_g1: A1 vs A10 | 21 | 37.2 | [16.0, 69.4] | 17/21 | none | none |
| INT | 19 | QA10_g1: A1 vs A10P | 21 | 47.5 | [20.8, 72.8] | 17/21 | none | none |
| INT | 19 | QA10_g4: A1 vs A10 | 21 | 45.4 | [-69.6, 69.5] | 15/21 | none | none |
| INT | 19 | QA10_g4: A1 vs A10P | 21 | 62.3 | [-63.4, 74.5] | 15/21 | none | none |
| INT | 19 | QH_g1: A1 vs A2 | 21 | 35.2 | [4.3, 64.1] | 18/21 | none | none |
| INT | 19 | QH_g4: A1 vs A2 | 21 | 30.8 | [5.7, 77.5] | 18/21 | none | none |
| INT | 19 | QT_g1: A1 vs A13 | 21 | 29.5 | [-1.4, 51.8] | 15/21 | none | none |
| INT | 19 | K1: A15 vs A1 g4 (per-seed) | 21 | -33.6 | [-203.7, 16.4] | 6/21 | False | False |
| INT | 19 | K2: A15 vs G15 g4 (per-seed) | 21 | -1.3 | [-29.6, 19.3] | 10/21 | none | none |
| SIE | 4 | P1: A1 vs D* g1 | 36 | 4.2 | [-52.2, 33.0] | 18/36 | none | none |
| SIE | 4 | P2: A1 vs A9 g1 | 36 | -10.1 | [-45.8, 20.2] | 17/36 | False | False |
| SIE | 4 | R1_g1: A1 vs R1 g1 | 36 | 78.6 | [70.7, 84.7] | 36/36 | True | True |
| SIE | 4 | QA10_g1: A1 vs A10 | 36 | 24.3 | [-6.7, 57.6] | 26/36 | none | none |
| SIE | 4 | QA10_g1: A1 vs A10P | 36 | 32.5 | [-16.5, 53.7] | 26/36 | none | none |
| SIE | 4 | QA10_g4: A1 vs A10 | 36 | 18.1 | [-57.7, 48.2] | 22/36 | none | none |
| SIE | 4 | QA10_g4: A1 vs A10P | 36 | 35.7 | [-8.0, 62.5] | 26/36 | none | none |
| SIE | 4 | QH_g1: A1 vs A2 | 36 | 29.2 | [2.0, 54.5] | 27/36 | none | none |
| SIE | 4 | QH_g4: A1 vs A2 | 36 | 20.0 | [-18.9, 63.3] | 23/36 | none | none |
| SIE | 4 | QT_g1: A1 vs A13 | 36 | 31.1 | [-1.4, 53.1] | 25/36 | none | none |
| SIE | 4 | K1: A15 vs A1 g4 (per-seed) | 36 | -4.1 | [-38.7, 14.4] | 17/36 | False | False |
| SIE | 4 | K2: A15 vs G15 g4 (per-seed) | 36 | 1.1 | [-9.9, 12.3] | 20/36 | none | none |

The plain-exact leave-one-lab-out of stats_ext (v3 convention) is in row_c_leave_one_lab_out.json. P3 is covered in the tier list (row_tiers) only.

### D3. (d) two-stage bootstrap (stats_ext.two_stage_bootstrap, B = 10000, percentile 95 %; weights by scored cells)

| Contrast | n conditions | Median L as % reduction (point) | 95 % bootstrap interval (%) | Median L primary store |
|---|---|---|---|---|
| P1: A1 vs D* g1 | 40 | -2.4 | [-28.5, 22.5] | -0.0233 |
| P2: A1 vs A9 g1 | 40 | -10.7 | [-31.1, 10.3] | -0.1020 |
| R1_g1: A1 vs R1 g1 | 40 | 78.5 | [72.6, 82.8] | 1.5353 |
| QA10_g1: A1 vs A10 | 40 | 22.6 | [6.3, 36.6] | 0.2568 |
| QA10_g1: A1 vs A10P | 40 | 29.9 | [13.6, 47.1] | 0.3550 |
| QA10_g4: A1 vs A10 | 40 | 26.2 | [-3.6, 48.0] | 0.3031 |
| QA10_g4: A1 vs A10P | 40 | 41.4 | [27.1, 58.6] | 0.5340 |
| QH_g1: A1 vs A2 | 40 | 25.8 | [8.5, 43.2] | 0.2990 |
| QH_g4: A1 vs A2 | 40 | 25.4 | [1.5, 50.3] | 0.2935 |
| QT_g1: A1 vs A13 | 40 | 30.2 | [3.4, 45.0] | 0.3602 |
| K1: A15 vs A1 g4 (per-seed) | not computed: not computed: the K contrasts use per-seed endpoints and cell_scores files hold mean-over-seeds cell scores only | | | |
| K2: A15 vs G15 g4 (per-seed) | not computed: not computed: the K contrasts use per-seed endpoints and cell_scores files hold mean-over-seeds cell scores only | | | |

### D4. (e) pp-scale row (BCa 95 % interval of the mean pp difference against delta_S = 0.02 E, delta_N = 0.10 E of margins.json; the mean-based pp tier can differ from the median-based log-scale tier)

| Contrast and cell | n | Mean pp diff | BCa 95 % | delta_S pp | delta_N pp | pp-scale tier it would reach |
|---|---|---|---|---|---|---|
| A1 vs D* m8_k2 | 40 | 0.136 | [-0.043, 0.434] | 0.020 | 0.099 | N |
| A1 vs A9 m8_k2 | 40 | 0.230 | [-0.012, 0.596] | 0.031 | 0.155 | N |
| A1 vs A10 m8_k2 | 40 | 0.417 | [0.197, 0.709] | 0.105 | 0.526 | S |
| A1 vs A10P m8_k2 | 40 | 0.519 | [0.252, 0.917] | 0.567 | 2.834 | N |
| A1 vs A10 m32_kfull | 40 | 0.086 | [-0.156, 0.254] | 0.017 | 0.084 | none |
| A1 vs A10P m32_kfull | 40 | 0.267 | [-0.006, 0.493] | 0.022 | 0.108 | N |
| A1 vs A2 m8_k2 | 40 | 0.484 | [0.285, 0.786] | 0.031 | 0.154 | S |
| A1 vs A2 m32_kfull | 40 | 0.308 | [0.157, 0.502] | 0.018 | 0.088 | S |
| A1 vs A13 m8_k2 | 40 | 0.350 | [0.203, 0.526] | 0.023 | 0.115 | S |
| A1 vs D* m32_kfull | 40 | 0.052 | [-0.265, 0.276] | 0.012 | 0.058 | none |
| A1 vs A9 m32_kfull | 40 | 0.222 | [0.094, 0.401] | 0.014 | 0.070 | S |
| A15 vs A1 m32_kfull (K1; per-seed endpoints) | 40 | -0.076 | [-0.194, 0.011] | 0.012 | 0.059 | none |
| A15 vs G15 m32_kfull (K2; per-seed endpoints) | 40 | -0.064 | [-0.201, 0.023] | 0.013 | 0.065 | none |

### D5. (v) diagnostic starts and (vi) z-prior weights (single-seed scores, seed 0 of the final refit; the primary is the five-seed ensemble, so the counts are not compared with primary tiers; plain-rule counts; D* not reselected)

Primary reference at g1 (ensemble endpoint): P1 N-node positives 22/40, S-node 19/40, P2 18/40.

| Row | Cell | Contrast | Median L as % reduction | Positives (L > 0) | Plain count reaches the critical count at the primary final level (node: positives/n) | Note |
|---|---|---|---|---|---|---|
| v1 | 8,2 | P1: A1 vs D* | -28.4 | 18/40 | P1N 19/40 no; P1S 17/40 no | D* = A12 not inverted: base (ensemble) score |
| v1 | 8,2 | P2: A1 vs A9 | -32.6 | 16/40 | P2 16/40 no |  |
| v1 | 8,2 | A1 vs AG | -4.5 | 20/40 |  |  |
| v1 | 32,full | P1: A1 vs D* | -15.4 | 19/40 |  | D* = A11 not inverted: base (ensemble) score; D* = A12 not inverted: base (ensemble) score |
| v1 | 32,full | P2: A1 vs A9 | 18.0 | 23/40 |  |  |
| v1 | 32,full | A1 vs AG | 5.5 | 23/40 |  |  |
| v2 | 8,2 | P1: A1 vs D* | -4.3 | 18/40 | P1N 21/40 no; P1S 18/40 no | D* = A12 not inverted: base (ensemble) score |
| v2 | 8,2 | P2: A1 vs A9 | -34.0 | 16/40 | P2 16/40 no |  |
| v2 | 8,2 | A1 vs AG | -9.4 | 17/40 |  |  |
| v2 | 32,full | P1: A1 vs D* | -21.4 | 18/40 |  | D* = A11 not inverted: base (ensemble) score; D* = A12 not inverted: base (ensemble) score |
| v2 | 32,full | P2: A1 vs A9 | 20.6 | 25/40 |  |  |
| v2 | 32,full | A1 vs AG | 5.6 | 22/40 |  |  |
| v3 | 8,2 | P1: A1 vs D* | -27.9 | 16/40 | P1N 18/40 no; P1S 16/40 no | D* = A12 not inverted: base (ensemble) score |
| v3 | 8,2 | P2: A1 vs A9 | -40.2 | 13/40 | P2 13/40 no |  |
| v3 | 8,2 | A1 vs AG | -6.3 | 18/40 |  |  |
| v3 | 32,full | P1: A1 vs D* | -3.0 | 20/40 |  | D* = A11 not inverted: base (ensemble) score; D* = A12 not inverted: base (ensemble) score |
| v3 | 32,full | P2: A1 vs A9 | 20.6 | 26/40 |  |  |
| v3 | 32,full | A1 vs AG | -0.9 | 19/40 |  |  |
| vi4 | 8,2 | P1: A1 vs D* | 8.6 | 23/40 | P1N 25/40 no; P1S 21/40 no | D* = A12 not inverted: base (ensemble) score |
| vi4 | 8,2 | P2: A1 vs A9 | -8.6 | 17/40 | P2 17/40 no |  |
| vi4 | 8,2 | A1 vs AG | -1.8 | 18/40 |  |  |
| vi4 | 32,full | P1: A1 vs D* | 11.6 | 23/40 |  | D* = A11 not inverted: base (ensemble) score; D* = A12 not inverted: base (ensemble) score |
| vi4 | 32,full | P2: A1 vs A9 | 16.4 | 26/40 |  |  |
| vi4 | 32,full | A1 vs AG | -5.0 | 17/40 |  |  |
| vi16 | 8,2 | P1: A1 vs D* | 13.0 | 23/40 | P1N 25/40 no; P1S 23/40 no | D* = A12 not inverted: base (ensemble) score |
| vi16 | 8,2 | P2: A1 vs A9 | 0.5 | 20/40 | P2 19/40 no |  |
| vi16 | 8,2 | A1 vs AG | 4.7 | 22/40 |  |  |
| vi16 | 32,full | P1: A1 vs D* | -1.0 | 20/40 |  | D* = A11 not inverted: base (ensemble) score; D* = A12 not inverted: base (ensemble) score |
| vi16 | 32,full | P2: A1 vs A9 | 11.8 | 25/40 |  |  |
| vi16 | 32,full | A1 vs AG | -0.1 | 20/40 |  |  |
