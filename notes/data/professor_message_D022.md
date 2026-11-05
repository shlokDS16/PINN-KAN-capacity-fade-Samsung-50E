# Message to the supervising professor on NASA and CALCE (D022 judge 1.7, corrected), 2026-11-05

Status: proposed wording for Shlok's approval; not sent. Every factual statement below is traced to the paper (Saxena et al.
2016 = `notes/papers/saxena2016_jps_calce_pl.md`), the provider page (CALCE battery-data page, fetched 2026-11-05; NASA PCoE
repository page and zip READMEs) or our own counts (`notes/data/NASA_CALCE_feasibility.md`). Changes against judge 1.7 are listed
at the end.

## The message

We include both repositories.

From CALCE we use the graphite/LiCoO2 pouch cells of Saxena, Hendricks and Pecht (Journal of Power Sources 327, 2016), because
our model forecasts held-out ageing conditions and needs several distinct stress conditions. These 16 cells were cycled at
25 +/- 2 C ambient over five state-of-charge windows, at a C/2 discharge rate (all five windows) and at 2C (three windows):
eight combinations of window and discharge rate, two cells each. Two caveats come with them. The cells discharged at 2C over the
20-80 % and 0-100 % windows heated to more than 15 C above ambient, and the data files carry no temperature record, so
temperature is not a model input and those four cells are flagged. The state-of-charge windows are defined by Coulomb counting
against the capacity measured at the latest check-up (taken every 50 or 100 partial cycles), so the windows are nominal.

The better-known CALCE CS2/CX2 prismatic cells offer fewer conditions. In CS2 the constant-current tests are full-range cycling
at 0.5C (four cells) and at 1C (four cells), plus two partial-voltage-range tests at 0.55 A (two cells each), all one cell model,
and no test temperature is stated; in CX2 they are 0.5C cycling (eight cells) and a single 3C cell. Holding one condition out
therefore leaves at most three training conditions in CS2 (two to four cells each) and one in CX2, too few to estimate the
stress law. Thirteen of these cells were also used in the first author's earlier paper. They are listed in the paper's table of
datasets considered, with this reason.

From NASA we use the 23 cells of set 5 that have one fixed ambient temperature and one constant discharge current, grouped into
five temperature-current groups. They are reported as a descriptive section, labelled as previously analysed (the first author used
this set before), and the confound of temperature with test batch is stated. Both campaigns are analysed separately, with the
same task as the Samsung cells and no statistical test. Whether the pouch-cell download completes (at least six of eight
conditions) is decided before any model is fitted.

## Source of each statement

| statement | source |
|---|---|
| graphite/LiCoO2 pouch cells, Saxena, Hendricks, Pecht, J. Power Sources 327 (2016) | paper title, abstract and Section 2 (p. 394-395); DOI 10.1016/j.jpowsour.2016.07.057 verified on Crossref |
| 16 cells, five windows, C/2 for all five, 2C for three, two cells each, eight combinations | paper Table 1 (p. 396) and Section 2.1 (p. 395); CALCE page lists the same eight groups (PL3/10, 4/5, 9/25, 11/13, 12/14, 17/18, 19/24, 21/23) |
| 25 +/- 2 C ambient | paper Section 2 (p. 395) |
| 2C cells over 20-80 % and 0-100 % rose more than 15 C above ambient | paper Section 3 (p. 396) and Section 4 (p. 398) |
| data files carry no temperature record | our check of the variable names of the PL17 data table (Time_sec, Date_Time, Step, Cycle, Current_Amp, Voltage_Volt, Charge_Ah, Discharge_Ah), one file; other files unchecked, so "carry no temperature record" is verified for PL17 only and must be confirmed when all eight zips are complete |
| windows by Coulomb counting against the latest check-up capacity; check-up every 50 or 100 partial cycles | paper Section 2.2 (p. 395-396) |
| CS2 full-range 0.5C: CS2-8, 21, 33, 34; 1C: CS2-35 to 38; partial voltage ranges 3.77-2.7 V and 4.2-3.77 V at 0.55 A: CS2-5, 6 and CS2-24, 25 | CALCE battery-data page, CS2 test types 1, 2, 5, 6 (fetched 2026-11-05, afternoon, after the site came back) |
| CS2 and CX2 one cell model each; no test temperature stated | CALCE page (cell descriptions; temperature given only for the CX2-4 ramp, the A123 and storage sets, not for CS2/CX2 tests) |
| CX2 0.5C: CX2-16, 31, 33, 35 and CX2-34, 36, 37, 38 (eight cells); one 3C cell: CX2-8 | CALCE page, CX2 test types 1, 2, 3 |
| "at most three training conditions in CS2, one in CX2" | arithmetic on the lists above: CS2 four conditions (0.5C, 1C, two partial ranges), hold one out leaves three; CX2 two constant-current conditions with the 3C a single cell, hold one out leaves one. CX2 types 4 to 6 (pulse, 0.5C-to-2.7 V pulses, temperature ramp) are single cells and not counted |
| thirteen cells used in the earlier paper | cell names CS2_33 to 38 and CX2_16, 33 to 38 in the retired project (`research paper for proctor/Proctor Research paper 2`, corpus B "CALCE 13") |
| NASA set 5: 23 cells, five temperature-current groups (24 C/2 A: B0005-07, 18, 36; 24 C/4 A: B0033, 34; 43 C/4 A: B0029-32; 4 C/1 A: B0045-48; 4 C/2 A: B0049-56) | NASA zip READMEs (conditions) and our per-cell counts, `NASA_CALCE_feasibility.md` section 1; the exclusions (B0025-28 square wave; B0038-44 changing conditions) are listed there |
| temperature confounded with test batch | READMEs and record time stamps: the 4 C, 24 C and 43 C groups were run in different periods (section 1 of the feasibility note) |
| NASA set 5 previously analysed (29 of 34 cells after cleaning) | retired paper `progress.md` ("NASA 29") |
| pouch download completion criterion | D022 judge 1.7 (a decision, not a fact) |

## Changes against judge 1.7 as written

1. PL sentence: "(Saxena et al., J. Power Sources 2016)" kept; added the temperature (25 +/- 2 C), the 2C heating caveat and the
   window definition, all from the paper. "Eight combinations ... two cells each" confirmed by paper Table 1.
2. CS2/CX2 sentence: the claim "no variation of state-of-charge window" is removed; CS2 types 5 and 6 vary the voltage range
   (3.77-2.7 V and 4.2-3.77 V at 0.55 A, two cells each). Replaced by the correct count of conditions (four in CS2) and cells per
   condition; "leaves a single training condition" corrected to "at most three in CS2, one in CX2". The conclusion (too few
   conditions) is unchanged. Note that these windows are voltage ranges, not Coulomb-counted SOC windows, and CS2-5, 6, 24, 25
   interleave full 0.22 A cycles (earlier page digest, not in the later quotation; to be confirmed); their data are not on disk.
3. "In their constant-current tests, only two discharge rates within CS2" removed as inaccurate (the partial-range cells run at
   0.55 A, i.e. 0.5C, so they add windows, not rates; the full-range tests give two rates).
4. NASA sentence unchanged in substance; the cell groups are listed here for traceability.
