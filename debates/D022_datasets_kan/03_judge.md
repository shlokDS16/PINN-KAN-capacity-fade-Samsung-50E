# D022 judge: NASA and CALCE datasets, the KAN contribution, monotone KAN, the cap, the titles (2026-11-05)

Judge: independent (gate-auditor role). I wrote none of the inputs. CONTRACT section 3 item 7.

**Reading depth.** Full text: `research/CONTRACT.md`; `debates/D022_datasets_kan/01_proposal_datasets.md`, `01_proposal_kan.md`, `kan_study_rule.md`, `02_novelty_kan.md`; `debates/codex_panel/turn07_response.md` (opponent); `debates/D021_cap/01_architect.md`; `notes/data/NASA_CALCE_feasibility.md`; `research/DECISIONS.md` D016-D020; `debates/D016_roles/02_judge.md` section 3. Partial: `runs/prereg/PREREG_v4.md` sections 1, 7 (7.0-7.4), 9 (9.1-9.11), 10, 11 (with 11a), 12 and 17 (17.1-17.5); `research/progress.md` RESUME block and log. Files opened for checking: `runs/D022_kan_synth/decision.json` (the adoption fields, M1/M2/L1-L4 values, false-structure rates), `runs/D022_kan_synth/posthoc_mono_init.txt`, and `git log` of the rule and result commits. **No Samsung, NASA or CALCE capacity value was opened.** Every number below is quoted from the file named beside it. The thresholds I set in rulings 1 and 2 are design choices fixed before any data, and they are labelled as such. None of them is a result.

**Ledger note.** `research/DECISIONS.md` has no D021 row (checked: the last row is D020; `progress.md` cites "D021, 2334666"). Ruling 4 records the cap decision inside D022.

---

## 0. Verdict

**REVISE: both parts adopted with modifications.**

| # | Question | Ruling |
|---|---|---|
| 1 | NASA / CALCE addendum | **ADOPT, MODIFIED.** One descriptive, ungated section on CALCE PL pouch (EXT-PL) and NASA set 5 (EXT-NA), each analysed only inside its own campaign. The addendum card is frozen after the Samsung `FROZEN` and before any model sees these data. Modifications: the direction labels and thresholds are dropped in favour of one symmetric count template. No coverage figure and no p-value appear in the paper. The card lives outside `runs/prereg/`. Samsung confirmatory runs execute from the FROZEN commit. A10c gets its own name. The retired-topic guard is extended. CS2/CX2 are "considered, not analysed", and the professor is told why (section 1.7). |
| 2 | KAN contribution | **ADOPT the identifiability-audited extraction protocol (E)** as the paper's KAN-side methodological contribution. It is framed as an *audit of KAN-extracted stress laws*, not as a new KAN architecture. The rule set (calibration design, label rule, abstention, sentence templates) is fixed in section 2 below and goes into PREREG_v4 before the freeze. It changes edge-level wording only and never a state, title or abstract sentence. |
| 3 | Monotone KAN (M) | **DEFER. Not before the freeze, and no Samsung run of M in this submission.** An optional synthetic-only second round is allowed after FROZEN, under a rule file committed first (section 3). Its result can only go to an exploratory appendix or a revision response. The paper never says M was tested and rejected. |
| 4 | Cap = 2 | **CONFIRMED.** The list of forbidden claims is in section 4. The extracted-law part of D016 3.5 is struck; the SOC question moves to A1's learned calendar KAN, descriptive only. |
| 5 | Title wording | **Unchanged and still true** under these rulings. No wording change is unavoidable. Only Shlok can change the table, and I recommend no change. |

**Answer to the author's request "include the novelty in KAN".** Yes, in a narrow and defensible form. The KAN contribution is a pre-registered identifiability audit of the stress law extracted from the KAN: a design-matched, calibrated false-structure table plus an abstention rule, applied identically to the KAN law (A15) and its matched additive law (G15). It does not depend on the K state, so it survives every outcome of the table. No new KAN architecture is adopted. The monotone KAN is prior art (MonoKAN, Neural Netw. 196, 2026; MKAN; ICKAN, per `02_novelty_kan.md`). The library-aware training (L) failed its pre-fixed false-structure criterion (L1: 79 % against the 25 % bound; `runs/D022_kan_synth/decision.json`).

**Reading of "only best outcomes".** The strongest result the method can honestly earn is a KAN-side contribution that holds whatever K1 and K2 show. An architectural change two steps before the freeze would have been reviewed as TAKEN (M) or as S2KAN-like (L), and it would have put the freeze at risk. The audit is the only candidate that adds a methodological result without touching a scored arm (`01_proposal_kan.md` section 5 item 5; the novelty audit gives NOVEL (narrow), confidence 0.55).

---

## 1. Datasets (EXT-PL, EXT-NA)

### 1.1 What is adopted from the proposal unchanged
- Within-campaign analysis only (proposal 1.3 items 1-5). Splits by condition or group, from identifiers, hashed before any model (1.5). The NASA group-level unit, not tuples (1.4; alternative F). The inclusion rules and exclusions (B0025-28, B0038-44) (1.4).
- Arms A1c, A9, A4c, A2, A10c (conditional), D\*, R1, R2. The frozen Samsung budget rule is used, with no timing run and no Partial-plan re-decision of its own. The ensemble endpoint, seeds and tuning seeds follow 1.6.
- Controls (1.9): NC-1 and PC-1 on each campaign's own design gate *that campaign only*. NC-2 analogue on PL only, cut first. Isolation from gate G and from every row of the closed table (1.9 "Isolation").
- Fade and schedule go/no-go (1.8): the rules are written into the card, `fade_gate.py` is committed before it runs, it reads capacity once, and no unit or cell is dropped by the gate. The PL completeness go/no-go applies at card freeze: at least 6 of 8 conditions with both cells readable, and the set is never extended afterwards (1.4).
- CPU cut order (1.12): NC-2 analogue, then sensitivity rows, then A10c on NASA, then NASA, then PL. Extras never displace the "never dropped" Samsung list (PREREG 12 rule 5).
- Methods disclosure text, Limitations text and data-availability text (1.13), with the edits in 1.4 below.

### 1.2 Modifications (binding)
1. **Remove the direction labels and their thresholds** (">= 6 of 8", ">= 4 of 5", the three sentence forms a/b/c). The opponent is right that a separate sign rule implies more than these overlapping, tiny holdouts can carry (turn 7). One symmetric template replaces them and is always printed, whichever direction the data take: *"On [campaign] (n = [n] held-out [conditions/groups]; descriptive, no test), [A1c] had the lower condition error than [B] in [k] of [n] units (median log ratio [r]; range [lo, hi])."* The Conclusions sentence joins the two campaign sentences, or the "was not analysed ([reason])" sentence for a void or no-go campaign.
2. **No coverage figure and no p-value in the paper.** The range is printed as "the range of the [n] unit-level log ratios", with no "1 - 2^(1-n)" statement: the proposal itself says the units are not independent. Plain exact p-values may sit in the run files for audit only. The 9.11 row reads: "EXT-PL, EXT-NA: none; counts, medians and ranges only".
3. **The card does not live in `runs/prereg/`.** PREREG 17.4 says `verify_freeze` requires HEAD = the frozen commit and a clean tree under `code/` and `runs/prereg/`. The card goes to `runs/prereg_ext/PREREG_EXT_v1.md` with its own change log. Its splits go to `runs/splits/ext_pl.json` and `ext_na.json` with hashes. Extra code goes in new files only (for example `code/ext/`) and is committed after FROZEN.
4. **Samsung confirmatory runs execute from the FROZEN commit.** They run either before any extras commit or from a separate git worktree checked out at the FROZEN SHA. Every Samsung run directory must record the FROZEN SHA. The coder confirms the guard's behaviour from the code before the first extras commit (I read the rule only in PREREG 17.4). The gate auditor checks the recorded commits.
5. **A10c is not "the dataset authors' model" on these campaigns.** It is named "a semi-empirical power-law cycle model (the cycle term of Stroebl et al., refitted)". It is defined only if the coder's separability unit test passes; otherwise it is omitted with a change-log row and no substitute (as proposed).
6. **No Highlights, abstract or title mention** of the extras. The closed table (D017/D019) and Highlights stay Samsung-only. Main text: one subsection, "Two further ageing campaigns (descriptive)". At most one main-text display item, whose form is decided in `debates/D-figures.md` (Fig. 8 swap or appendix only), with separate panels per campaign and no Samsung value in the same panel.
7. **Pre-card work is limited to identifiers.** Before FROZEN, only identifier-level work is allowed: finishing the downloads, CRC and operation-table counts, reading Saxena et al. (temperature, check-up cadence, window control), and citation verification. For PL, no capacity array is read before the card hash. Loader tests before the hash check schema, counts and identifiers only, and never print or store a capacity value. This work never takes an agent slot from a freeze blocker (FB-1 to FB-10, C1-C25).

### 1.3 Retired-topic guard (extended)
The proposal's guard (1.3) stands. Added:
- No sentence, table or figure that ranks the campaigns, calls one "harder", or counts wins across campaigns ("in all three datasets", "on 2 of 3 campaigns").
- No pooled statistic over Samsung, EXT-PL and EXT-NA. No meta-analysis.
- Banned words for this section, in addition to the proposal's list: "external validation", "robust across datasets", "generalises", "transferability", "out-of-distribution".
- No evaluation-split variants (random-cycle, within-cell, cell-split) on any campaign. No interval, coverage or calibration claim (retired topic 2).
- No CS2/CX2 within-condition early-life row. That would be a leave-cell-out protocol on previously analysed cells, which is the retired theme. If the professor insists after the message in 1.7, the question returns to a judge (re-open condition).

### 1.4 Disclosure wording for previously analysed data (adopted with edits)
- Methods, the data subsection of the main text (not only an appendix): *"Cells of the NASA set were analysed by the first author in an earlier study of battery state-of-health estimation [ref]; their identifiers and capacity values had been seen before this analysis was specified, and we treat them as previously analysed data. The CALCE pouch cells had not been analysed by the authors; their data are public and have been used by others [Saxena et al.]."*
  - I changed "The NASA cells were analysed" to "Cells of the NASA set": the feasibility note says the earlier study used 29 cells after its own cleaning, and the overlap with our 23 included cells is not verified.
- Every caption, table note and dataset-table row for NASA carries "previously analysed data", and "temperature is confounded with test batch".
- Reference for the earlier study: the citation validator decides. The Zenodo record is a DataCite DOI, and CONTRACT 1 asks for Crossref verification, so the lead asks Shlok whether a DataCite-verified DOI is acceptable. If it is not, the text reads "an earlier study by the first author (unpublished)". The disclosure sentence is printed in either case.

### 1.5 Freeze order (binding)
1. Samsung `runs/prereg/FROZEN`, by the unchanged procedure.
2. The addendum card `runs/prereg_ext/PREREG_EXT_v1.md` is committed and hashed. It contains: inclusion and QC rules, stress coordinates and active-input rule, splits and hull flags, the window rule and grid, completeness/S-gate/F-gate rules, arms, budget pointer, endpoint, the template of 1.2(1), and disclosure texts. The statistician and red team sign it, and the gate auditor checks it against this file.
3. The extras code is committed in new files only. The gate auditor checks that no pinned file changed and that a Samsung smoke run is bit-identical before and after.
4. PC-1 and NC-1 run on each campaign design.
5. `fade_gate.py` runs once and writes `fade_gate.json`.
6. Tuning and refits run, PL first, then NASA. Each frozen configuration is scored once. Any rule changed after a held-out unit is scored means a new card version, disclosed.

### 1.6 Go/no-go summary
| Gate | Rule (fixed now) | Consequence |
|---|---|---|
| PL completeness | >= 6 of 8 conditions with both cells readable when the card is frozen | otherwise: one sentence "not analysed: incomplete download"; no substitute set |
| S-gate | >= 75 % of included cells have >= 3 post-window check-ups at k_full | no-go: one sentence plus the fade table |
| F-gate | >= 75 % of units with F_u >= 5 pp (design choice, proposal 1.8) | no-go: one sentence plus the fade table |
| k_full | PL no-go if k_full < 2 | as PREREG J16 section 8 |
| NC-1 / PC-1 | per campaign | void that campaign's section; a shared-code NC-1 failure goes to Samsung stop rule 3 as written |
| A10c | separability unit test | arm omitted, change-log row |

### 1.7 CS2/CX2 and how the professor is told (the lead sends this; Shlok approves the wording)
*"We include both repositories. From CALCE we use the graphite/LiCoO2 pouch cells cycled over eight combinations of state-of-charge window and discharge rate (two cells each; Saxena et al., J. Power Sources 2016), because our model forecasts held-out ageing conditions and needs several distinct stress conditions. The better-known CALCE CS2/CX2 prismatic cells have, in their constant-current tests, only two discharge rates within CS2 (0.5C and 1C) and no variation of state-of-charge window or stated temperature, so holding one condition out leaves a single training condition and the stress law cannot be estimated. Thirteen of those cells were also used in the first author's earlier paper. They are listed in the paper's table of datasets considered, with this reason. From NASA we use the 23 cells of set 5 that have one fixed temperature and discharge current, grouped into five temperature-current groups. They are reported as a descriptive section, labelled as previously analysed (the first author used this set before), and the confound of temperature with test batch is stated. Both campaigns are analysed separately, with the same task as the Samsung cells and no statistical test. Whether the pouch-cell download completes (at least six of eight conditions) is decided before any model is fitted."*

Sources: CS2/CX2 rates and the 13 cells from `NASA_CALCE_feasibility.md` 0 and 3. The 23 cells and five groups from proposal 1.4 (arithmetic on README counts). The PL design is still a page digest: the message goes out only after the data steward confirms it against Saxena et al. (A5), and until then no PL design fact is sent or printed.

### 1.8 Why not the alternatives
- **Decline (Samsung only):** the professor asked, the cost is modest (proposal 1.12: about 3 to 5 CPU-h expected plus about 2 coder days), and the guard keeps it off the retired topic.
- **Confirmatory parity:** n = 8 and 5 cannot pass 0.025 short of unanimity, it would change the Holm levels of the closed design, and NASA is not blind.
- **Pooling or transfer:** this is the retired topic (CONTRACT 1).
- **CS2/CX2 as "CALCE":** one active input with two levels, and previously analysed.
- **Keep the direction labels:** they create a sign rule without error control (opponent). The symmetric template gives the same discipline without a threshold.
- **NASA as a zero-CPU "considered" row only:** cheaper, but the professor named NASA, and the cut order already drops it first under CPU pressure.

---

## 2. KAN contribution: identifiability-audited extraction (adopted)

### 2.1 Why adopted, and how it must be framed
- D021 shows, with ground truth, that post hoc extraction over-reads edges: 37 of 40 linear-truth edges got a 3-coefficient form at cap 3 (`D021_cap/01_architect.md` 4). D022 reproduces this for B: false structure at cap 3 of 0.9375 (G0, m = 32) and 0.875 (m = 8), and 0 at cap 2 (`runs/D022_kan_synth/decision.json`). The design bounds what an edge can carry (three temperature levels give two contrasts; in 137 of 400 three-level sets, at least three 3-coefficient forms fit exactly; D021 3.1).
- The novelty audit rates (e) NOVEL (narrow, 0.55): no per-edge table of (levels, identifiable parameters, BIC margin, calibrated false-structure rate) was found for KAN or SINDy/EQL extraction. It reads as methodological only if the calibrated table is shown and the label rule changes what the paper says (`02_novelty_kan.md` 1). Both conditions are built into the rule below.
- The opponent's objection, that this is "careful reporting, not a new KAN method", is accepted as a framing constraint. The paper calls it an audit protocol for KAN-extracted laws. It never says "new KAN" or "first", unless the novelty auditor's repeat check clears the four-part wording within 7 days of submission.
- Sovrano et al. (arXiv 2603.15250) must be cited and distinguished in the Introduction. That paper notes that extraction is unstable and that equivalent operators are not identifiable, but it offers no calibrated rate and no level-based rule. Raue et al. (doi 10.1093/bioinformatics/btp358) and stability selection (arXiv 0809.2932) are cited as the ingredients.

### 2.2 What must be pre-registered (PREREG_v4 revision 3, before FROZEN)
**(a) Method: new item 6 in 7.3, "Extraction audit".** It is applied identically to A15 and G15, at g4 (confirmatory cell) and g1 (descriptive), per (outer fold, seed) extracted law.

1. **Per-edge table**, one row per edge:
   - arm, fold, seed, input;
   - the number of distinct training levels L_e of that input in the fold's training conditions (from `subsets.json`, identifiers only);
   - the eligible families under cap 2 ({zero, linear, log});
   - the identifiable shape parameters, = min(1, L_e - 1) for a non-zero family, because the additive constant is confounded with the law level;
   - the chosen family and the BIC margin to the best other eligible family on the extraction grid, printed with the D021 caveat that BIC is computed on the KAN's grid and not on the data;
   - the fold-by-seed stability of the chosen family and sign.
2. **Calibration (design-matched synthetic truths).**
   - Use `synth.make_synthetic` on the actual Samsung training stress vectors of each outer fold at m = 32 and m = 8 (from the pinned `subsets.json`), with the PC-1 noise and check-up assumptions of PREREG 13.
   - Per input, the truth family is drawn from {zero, linear, log}, balanced over seeds by a fixed assignment table. A non-additive kind (G2-type) is added for the composition of A15 h = 2.
   - Curved truths outside the cap (quadratic, hinge) are included as report-only rows (representation error, no label effect).
   - Arms: A15 h = 1, A15 h = 2 and G15, at default hyperparameters as in D021, with the full pipeline (parent fit, extraction at cap 2, end-to-end refit).
   - Output: per (input, m, arm, truth family), the confusion counts of the extracted family and of the slope sign, with exact binomial 95 % intervals (descriptive).
   - The seed count is fixed in a rule file committed before the run, large enough that every (input, m, arm, truth family) cell has at least 20 synthetic edges. That count is a design choice.
3. **Label rule (fixed now; design choices, not results).** For each input of an extracted law:
   - **"pruned"**: zero is chosen in at least 80 % of the fold-by-seed laws (20 of 25 at g4).
   - **"identified: <family>"**: all four conditions hold:
     - (i) L_e >= 3 (with L_e = 2, linear and log both fit exactly, so the label can be at most "slope sign only");
     - (ii) the same family is chosen in at least 80 % of the fold-by-seed laws;
     - (iii) the calibrated rate of choosing that family when the truth is another eligible family is <= 0.10 in the matching (input, m, arm) cell, from at least 20 synthetic edges per truth family;
     - (iv) the law is additive in that input (h = 1, or h = 2 with every outer edge identified as linear). Otherwise the input is labelled "composed: no single form".
   - **"sign identified"**: the slope sign agrees in at least 80 % of the fold-by-seed laws and the calibrated sign-error rate is <= 0.10.
   - **"ambiguous"** (abstention): every other case. The law is still printed in closed form, but no family is named for that input.
   - **"approximate (cap)"** flag: the training-side RMS residual of the cap-2 form against A1's learned partial dependence exceeds 10 % of that dependence's range (the D021 re-open threshold, training side only). The flag adds the sentence "the cap-2 form is an approximation of a curved learned effect". After the freeze it changes neither the cap nor any label.
4. **Unit tests** (they must pass at the frozen commit):
   - an input with L levels never receives more than L - 1 identifiable parameters;
   - with L_e = 2 the label is never "identified: <family>";
   - the audit reproduces the D021 false-structure counts on D021's seeds (cap 3: 37 of 40; cap 2: 0), which is a regression test of the extraction path;
   - A15 and G15 go through one code path.
5. **Pins.** The thresholds file (for example `code/pinnkan/extraction_audit.json`) is in the frozen commit, and its sha256 is in the config hash, like the cap. The calibration rule file and script are in the frozen commit. The calibration run executes from the frozen commit before any Samsung outer score, and its output is hashed before any outer score, like item (f). The statistics step refuses to print edge labels if the hash is missing or later than the first outer score.

**(b) Reporting: new item 10 in 11a (secondary, descriptive; no test, no Holm).**
- Fixed Results sentence, always printed for A15 and G15 side by side: *"Of the [n] inputs of the extracted [KAN/additive] law, the training design identified the form of [j] and the sign of [s]; [a] were ambiguous and are reported without a named form."*
- 11a items 5 and 7 (direction of extracted effects against A10's exponents) use only the "sign identified" inputs. All others are listed as "not identified".

**(c) Checklist: new item C26 in 17.2** = items (a) 4 and 5 met. **17.4:** if the audit is not built and tested by the freeze, it is struck by a change-log row. The paper then names no edge family and prints only the law, which is the conservative default. The freeze is not delayed for it. The lead decides whether to schedule it before the remaining blockers or after them.

### 2.3 How it changes claims
- **States, titles, abstract claim sentences: no change.** The K state is set by K1/K2 alone (section 11, untouched).
- An edge-level form or direction may be named in the Results, Discussion and 11a only for "identified" inputs. It is never "recovered", "discovered" or "a mechanism".
- "Ambiguous" inputs are printed in the formula with the sentence "the training design does not identify the form of this effect".
- The Discussion carries one fixed sentence: *"Readable means that the extracted law is a short closed form that can be written out and evaluated; the audit reports separately which of its effects the training design identifies."*

### 2.4 Where it sits in the paper
- **Introduction:** one contribution bullet: "an identifiability audit for KAN-extracted stress laws (a calibrated false-structure table on design-matched synthetic truths and an abstention rule, applied identically to the KAN law and its matched additive law)".
- **Methods:** a subsection "Extraction audit", directly after the A15/G15 extraction.
- **Results:** in the KAN-law results, with the edge-audit table (A15 and G15 side by side) and the calibration table. At least a compact form of the calibration goes in the main text (the novelty audit's condition); the full confusion tables go to an appendix. Forms are decided in `debates/D-figures.md`.
- **Limitations:** BIC is computed on the KAN's grid; three temperature levels; the calibration is synthetic and inherits the generator's choices (the PC-1 circularity sentence applies).

---

## 3. Monotone KAN (M): deferred

- The opponent is right that M has not been fairly ruled out. The rule's verdict stands (M1 +0.058, upper bound +0.069; M2 +0.075 and +0.054; `decision.json`), but the check had six seeds, no refit and no held-out RMSE decision, and the proposal reports an initialisation sensitivity.
- The expected gain does not justify a delay. The post hoc diagnostic's apparent advantage is the best of four initial values on 2 seeds, one arm, one kind, at m = 32 rather than g1 (`posthoc_mono_init.txt`: 0.060 / 0.052 at -2, but 0.154 / 0.148 at -1 and 0.324 / 0.311 at 0). It is selected after the fact and shows a fragile parametrisation.
- Adoption would change the primary arm A1 two steps before the freeze. It would need sign constraints on seven law-based arms. Fair constraints are impossible for the GP member of D\*. It would mix a sign prior into P1/P2 attribution (E1) and risk PC-2. The C_ch sign is unverified. The method is TAKEN, and the battery application only INCREMENTAL (`02_novelty_kan.md`).
- Cap 2 already makes every extracted edge monotone (zero, linear, log) at the law level, though without a fixed sign.
- **Ruling.**
  - No pre-freeze second round.
  - No M arm on Samsung data in this submission.
  - An optional synthetic-only second round may run after FROZEN on idle CPU, only under a rule file committed first that fixes:
    - at least 10 complete seed groups;
    - a parametrisation or initial value chosen without the post hoc diagnostic's seeds and kind (for example a fixed Hermite/I-spline start, or an init chosen on a separate synthetic kind);
    - the end-to-end refit;
    - held-out synthetic forecast RMSE as a decision metric;
    - the same signs on every law-based arm, plus LightGBM's monotone option where it exists, stated as unavailable for the GP;
    - a lab-aliasing synthetic case;
    - the adoption rule.
  - Its result may appear only as an exploratory, synthetic appendix or a revision response.
- **The paper may cite MonoKAN as a possible extension. It never says shape constraints were tested and rejected.**
- L (library-aware training) is not adopted (L1 failed: 79 % against 25 %). This is not reopened.

---

## 4. Cap = 2: confirmed

- **Reasons.** The D021 rule was committed first (c0a9793):
  - 37 of 40 linear-truth edges got false structure at cap 3, against 0 at cap 2;
  - the three-level temperature edge is not identifiable beyond two contrasts;
  - the only non-finite refits were at cap 3;
  - cap 4 equals cap 3.
  
  The D2 margin was thin (upper bound 0.0210 against 0.02), but the false-structure evidence does not rest on that margin and was reproduced independently by D022's B variant (0.9375 and 0.875 at cap 3, 0 at cap 2). D022 found no replacement rule (L1 failed).
- **Claims the cap forbids** (manuscript, captions, Highlights, response letters):
  - that the extracted law recovered, discovered, identified or "shows" an Arrhenius, power-law, exponential, quadratic or hinge (threshold) dependence;
  - any non-monotone SOC (or other) dependence read from the extracted law;
  - any activation energy from the extracted cycling law (already barred for the cycling term by 11a item 9);
  - "the KAN discovered the stress law".
  
  The words "power law", "Arrhenius", "hinge" and "threshold" are not used to describe what the extracted law found. The fitted equation itself may be printed (for example a term linear in log C_dch) for "identified" inputs only (2.2).
- **D016 3.5.** The extracted-law check of a sign change of the calendar SOC slope above 0.8 is **struck** from 11a item 7: a cap-2 calendar edge is monotone in SOC by construction. The SOC question is answered only on A1's learned calendar KAN (11a item 2), with the fold-by-seed envelope, using the "consistent / not consistent with the dataset authors' report" wording and the stage-1-only caveat. Limitations sentence: "the extracted law is monotone in each input by construction of the coefficient cap and cannot represent the non-monotone SOC dependence reported by the dataset authors".
  - D021 alternative 3 (a calendar-only cap of 3) is not adopted. It needs a code change, a new hash and a new study, and 11a item 2 already covers the question.
  - The seven-family recovery test of 7.3 item 4 runs at cap 3 as a library test (D021 cost (ii)). 7.3 item 1 states the cap and the eligible set {zero, linear, log}.

---

## 5. Title wording (D017/D019 table; not edited here)

- **"readable Kolmogorov-Arnold stress laws"** (T1, T4, T7) appears only in K+: K1 passes and K2 reaches tier S on held-out conditions. Under cap 2 the extracted law is a short closed form of linear and log terms (composed through the outer edge when h = 2), printed in full and evaluated on unseen conditions. "Readable" in that sense is true and claims no identification. The audit (2.3) reports identification separately, and the Discussion sentence of 2.3 says so. The banned phrase "interpretable physics discovered" stays banned. **Still true.**
- **"Kolmogorov-Arnold stress functions"** (T2, T5, and the KAN wording of T9a) names A1's stress map, which is a KAN in every arm and state. **Still true.**
- **No wording change is unavoidable. I recommend none.** If Shlok wants "readable" to promise identified forms, only he can change the table, in a decision row before the freeze. That would be a stronger claim than the cap supports, and I advise against it.

---

## 6. Actions

| # | Action | Owner | File |
|---|---|---|---|
| A1 | PREREG_v4 revision 3: 7.3 item 1 (cap = 2, eligible set, superset note); 7.3 new item 6 (audit, 2.2a); 11a item 7 SOC part struck and pointed to item 2; 11a new item 10 (2.2b); 17.2 new C26; 17.4 audit build-or-strike; 3.4(ii) pointer to EXT; 9.11 row "EXT-PL, EXT-NA: none"; 12 rule 5 extras cut first; 14 and 15 pointers; 19.1 change-log row D022. Section 11 untouched | experiment-designer | `runs/prereg/PREREG_v4.md` |
| A2 | Audit code, thresholds file, unit tests (2.2a items 4 and 5); calibration rule file and script; config-hash pin; statistics-step guard | coder | `code/pinnkan/extraction_audit.py`, `extraction_audit.json`, `code/tests/test_extraction_audit.py`, `code/prereg/extraction_calibration.py`, `debates/D022_datasets_kan/calibration_rule.md` |
| A3 | Review of the audit rule and code before the freeze (red-team sign-off of 7.3 item 6) | red team | `debates/D022_datasets_kan/04_redteam_audit.md` |
| A4 | Calibration run from the FROZEN commit, hash filed before any outer score | coder; gate auditor verifies order | `runs/extraction_calibration/` |
| A5 | Finish the PL download; operation-table counts; read Saxena et al. (temperature, cadence, window control); no capacity array read | data steward | `notes/data/NASA_CALCE_feasibility.md` (appended section) |
| A6 | Verify DOIs: Saxena et al. 2016, NASA repository entry, earlier study (DataCite question to Shlok), Sovrano et al., MonoKAN | citation validator; lead asks Shlok | `notes/citations/` |
| A7 | Addendum card after FROZEN, outside `runs/prereg/`; splits and hashes | experiment-designer; statistician and red team sign | `runs/prereg_ext/PREREG_EXT_v1.md`, `runs/splits/ext_pl.json`, `ext_na.json` |
| A8 | Extras loaders, specs, `fade_gate.py`, A10c separability test in new files after FROZEN; confirm the `verify_freeze` behaviour and the worktree plan first | coder | `code/ext/` |
| A9 | Check: Samsung runs record the FROZEN SHA; no pinned file changed; Samsung smoke bit-identical; disclosure text present; template of 1.2(1) used verbatim | gate auditor | `research/audits/D022-ext-<date>.md` |
| A10 | Send the professor message of 1.7 after A5 confirms the PL design; Shlok approves the wording | lead | status file / mail |
| A11 | Rows for the extras display item and the audit and calibration tables | figure planner | `debates/D-figures.md` |
| A12 | Methods "Extraction audit", contribution bullet, banned-claims list (section 4), Discussion readability sentence, NASA disclosure, Sovrano positioning | manuscript writer | `paper/draft/` |
| A13 | Repeat novelty check of (e) within 7 days of submission (S2KAN v2 diff, MKAN follow-ups, JES 2026) | novelty auditor | `debates/D022_datasets_kan/05_novelty_repeat.md` |
| A14 | Optional M synthetic second round after FROZEN, rule file first (section 3) | method-architect (proposer); a separate judge reads it | `debates/D022_datasets_kan/m_round2_rule.md` |
| A15 | Record-only row for D021 if the lead wants the ledger complete (cap ruling is in D022) | lead | `research/DECISIONS.md` |

## 7. Re-open if
1. The professor insists on CS2/CX2 or on a NASA confirmatory role after the 1.7 message.
2. Saxena et al. contradict the PL design as recorded (conditions, cells, cadence).
3. The guard cannot run Samsung confirmatory runs from the FROZEN commit while extras commits exist. In that case the extras wait until all Samsung outputs are written.
4. The novelty repeat check finds a calibrated per-edge identifiability or false-structure protocol for KAN or symbolic extraction. The contribution bullet is then reworded to an application.
5. The calibration shows that no input can reach "identified" at g4 under any arm. The rule stays; the paper reports it, and the contribution becomes the negative audit finding, said plainly.
6. The audit is not built by the freeze. It is struck by rule, and this ruling on the KAN contribution returns to the lead and Shlok.
7. A Samsung outer score exists before FROZEN.
8. Shlok changes the title table, or asks for the closed-form SOC readout (calendar-only cap; D021 alternative 3).
9. An M second round passes a pre-committed rule. It informs a future version or a revision only, never this frozen run.
