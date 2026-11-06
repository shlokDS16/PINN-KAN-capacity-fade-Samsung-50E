# D025 window cap: full list from the code (lead, 2026-11-06 13:05; identifiers and check-up counts only, no capacity value)
Computed with `data.WindowRule.capped` on all 279 Samsung cells after the QC steps (counts are post-QC points; D025 counted listings).
- Cycling cells where the cap binds at k = k_full = 4 and the cell is scoreable: TP_z04_01_s1, TP_z20_02_s2, TP_z20_03_s2,
  TP_z23_01_s2, TP_z23_02_s2, TP_z23_03_s2 (D025 had listed TP_z20_02 and TP_z23_01 only).
- Cap binds but the cell stays unscoreable (window < 3 points): TP_z24_01_s1, TP_z25_01_s1; storage cells 04-06 of every storage
  condition (two-point records, out of the primary analysis anyway, 3.3(6)).
- At k = 2: cycling cells TP_z20_02_s2, TP_z23_01_s2 (TP_z24_01_s1, TP_z25_01_s1 unscoreable).
- Condition-level n: 40 cycling conditions with >= 1 scoreable cell before and after the cap, at k = 4 and k = 2 (D025 re-open
  condition not triggered). Scoreable cells per condition change at k = 4 for two conditions:
  T23|SOCmax0.8|DoD0.5|Cch0.8|Cdch0.3 (2 -> 3) and T45|SOCmax0.8|DoD0.6|Cch1|Cdch2 (4 -> 7).
