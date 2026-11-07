# Prose check report

Generated 2026-11-06 by `tools/prose_check.py`. Nothing in the drafts was edited; every row is a suggestion for you to accept, rephrase or dismiss.

## How this run was configured

- **Command:** `python -I tools/prose_check.py paper/draft/00_open_items.md paper/draft/01_introduction.md paper/draft/02_related_work.md paper/draft/03_data.md paper/draft/04_methods.md paper/draft/05_evaluation.md paper/draft/CITATION_AUDIT.md paper/draft/PROSE_CHECK_REPORT.md paper/draft/WRITER_C3_C17_REPORT.md paper/draft/refs_used.md paper/draft/refs_verified.md --out paper/draft/PROSE_CHECK_REPORT.md` (10 files checked)
- **Spelling variant:** en-GB (auto-detected from the draft: 16 UK-spelled vs 0 US-spelled words in the paired list)
- **Python:** 3.14.3 (isolated mode `-I`; project packages from `tools/bin/pylib`)
- **LanguageTool:** LanguageTool 6.8 (folder `LanguageTool-6.8`, official release zip checked against SHA-256 by language_tool_python; server jar SHA-256 `f6d4a95d7756c5db334c255d77306b2b0f3cdb4a4621b7301bff7e8fa7c714fd`); server download version 6.8; language_tool_python 3.4.0; picky level on; local server only (no public API); openjdk version "17.0.19" 2026-04-21
- **Vale:** vale version 3.26.0; binary SHA256 `a4e0b17ea31fb61f3117f3171af502ff95f3467ca60d7097e6aa909928078c30`; styles (proselint, write-good, Microsoft) SHA256 `2e8a2c09b96e7a01547e7f9cd4b62959d90bdc579171f0111d5f4e7a8bf8f137`
- **spaCy:** 3.8.13 / en_core_web_sm 3.8.0 (user site C:\Users\Shlok\AppData\Roaming\Python\Python314\site-packages)
- **Journal rules:** `tools/prose_rules/jes_rules.yml` (SHA256 prefix `43f255bd46dc715f`) and `jes_checks.py`
- **Similarity:** verbatim runs of 10+ words against 13 reference texts in `refs/fulltext`
- **Hidden characters:** zero-width, bidi, tag, variation selectors, odd spaces, soft hyphen, control, homoglyph; scans the raw file including comments
- **Byte-order marks:** 00_open_items.md

## Summary

Manuscript files: 5 (counted in the ranking). Working notes: 5 (checked, shown separately, left out of the top 20).

| Category | Manuscript | Working notes |
|---|---:|---:|
| Hidden characters | 0 | 1 |
| Grammar | 0 | 4 |
| Spelling | 1 | 15 |
| Punctuation | 1 | 1 |
| Claim needs evidence | 3 | 2 |
| AI-sounding phrasing | 0 | 2 |
| Clarity | 66 | 9 |
| Weak or hedged wording | 4 | 1 |
| Abbreviation | 26 | 0 |
| Units and numbers | 26 | 1 |
| Consistency | 20 | 0 |
| Typography | 1 | 8 |
| Style | 2 | 12 |
| Placeholder | 22 | 4 |
| **Total** | **172** | **60** |

| File | Flags | High | Medium | Low |
|---|---:|---:|---:|---:|
| 00_open_items.md (working note) | 11 | 5 | 4 | 2 |
| 01_introduction.md | 28 | 5 | 20 | 3 |
| 02_related_work.md | 11 | 1 | 8 | 2 |
| 03_data.md | 47 | 5 | 37 | 5 |
| 04_methods.md | 43 | 5 | 28 | 10 |
| 05_evaluation.md | 43 | 5 | 28 | 10 |
| CITATION_AUDIT.md (working note) | 40 | 14 | 15 | 11 |
| WRITER_C3_C17_REPORT.md (working note) | 7 | 2 | 5 | 0 |
| refs_used.md (working note) | 0 | 0 | 0 | 0 |
| refs_verified.md (working note) | 2 | 0 | 0 | 2 |

Flags by tool (a merged row counts once per tool): hidden 1, jes 178, languagetool 48, vale 20.

## Top 20 to fix first

Ranked by severity, then by what a referee notices first (hidden characters, grammar and spelling, verbatim text, unsupported claims, undefined abbreviations). At most 5 per category and one per line. Placeholders are excluded; they are listed in `00_open_items.md` and in the tables below.

| # | Where | Category | Flagged text | Rule | Why and suggestion |
|---:|---|---|---|---|---|
| 1 | 03_data.md:15 | Spelling | ... and stage of these cells follow the file names, the «Testpoint» field, laboratory and dates, which agree for all 279 ... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'Test point' |
| 2 | 01_introduction.md:16 | Abbreviation | ... network without the law (A9), with an additive-map law («AG»), with the hard-integrated law (A2), with the dataset au... | `abbr-undefined` | 'AG' is never expanded in the manuscript text (3 uses). -> Write the full term at first use, then '(AG)'. |
| 3 | 01_introduction.md:25 | Abbreviation | ...ssion, including ICLR 2027 and a method-level check of «PIKAN», PGKAN and KA-CRNN, is open by design and gates every s... | `abbr-undefined` | 'PIKAN' is never expanded in the manuscript text (4 uses). -> Write the full term at first use, then '(PIKAN)'. |
| 4 | 02_related_work.md:15 | Abbreviation | ...work inside the state equation of calendar ageing [1]. «PiDDM» [1] integrates an Arrhenius time term and an Arrhenius ... | `abbr-undefined` | 'PiDDM' is never expanded in the manuscript text (3 uses). -> Write the full term at first use, then '(PiDDM)'. |
| 5 | 03_data.md:7 | Abbreviation | ...ted 4.9 Ah) tested in two stages and three laboratories («HM», INT, SIE) with one protocol. Stage 2 used a new cell ba... | `abbr-undefined` | 'HM' is never expanded in the manuscript text (4 uses). -> Write the full term at first use, then '(HM)'. |
| 6 | 03_data.md:17 | Abbreviation | ... preregistration was frozen, without scoring any model. «ISU» and SNL were explored in a scratch pilot before their sp... | `abbr-undefined` | 'ISU' is never expanded in the manuscript text (3 uses). -> Write the full term at first use, then '(ISU)'. |
| 7 | 01_introduction.md:18 | Clarity | «X Text: "To our knowledge, no earlier study has reported ...» | `sentence-length` | Sentence of 73 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 8 | 01_introduction.md:29 | Clarity | «Related rules for sections not yet drafted (action A8): t...» | `sentence-length` | Sentence of 67 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 9 | 04_methods.md:29 | Clarity | «The modulation is constant, self-limiting, X with X, or a...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 75 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |
| 10 | 04_methods.md:45 | Clarity | ... neither used Samsung data. «For an unseen cell, with network and law frozen, X and X ...» | `sentence-length` | Sentence of 70 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 11 | 04_methods.md:73 | Clarity | «The data-only learners (A11, A12) are trained on the cell...» | `sentence-length` | Sentence of 75 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 12 | 01_introduction.md:22 | Claim needs evidence | 1.3 Rule for the abstract's «novelty» wording (fixed before any result; internal, not for the manuscript) | `claim-novel` | 'novelty' is a claim, not a result. -> Name what differs from which prior work; keep 'novel' only where a search supports it. |
| 13 | 03_data.md:9 | Units and numbers | ...ons after repeated centre points are merged (10, 23 and «45 C»; state of charge 5 to 100 %, limited to 80 % in stage 2... | `temp-bare-C` | Temperature unit written as '45 C'. -> Write '45 °C' (number, space, degree sign, C). |
| 14 | 03_data.md:11 | Units and numbers | ...e five repeated centre points. Cycling temperatures are «23 C» (10 conditions, 33 cells), 35 C (13 conditions, 39 cell... | `temp-bare-C` | Temperature unit written as '23 C'. -> Write '23 °C' (number, space, degree sign, C). |
| 15 | 03_data.md:13 | Units and numbers | ...arge at C/2 to 4.2 V, discharge at 1C to 2.5 V, ambient «23 C»), integrated from the logged current as in the data pap... | `temp-bare-C` | Temperature unit written as '23 C'. -> Write '23 °C' (number, space, degree sign, C). |
| 16 | 03_data.md:19 | Units and numbers | Confounds. All 39 cells at «35 C» were run by laboratory INT. Cycling at 45 C is HM (66 cells) and SIE (9 cells), and ... | `temp-bare-C` | Temperature unit written as '35 C'. -> Write '35 °C' (number, space, degree sign, C). |
| 17 | 03_data.md:23 | Units and numbers | ...LFP 18, NCA 22, NMC 21; our count) cycled at 15, 25 and «35 C» and discharge rates of 0.5 to 3C in 23 conditions; time... | `temp-bare-C` | Temperature unit written as '35 C'. -> Write '35 °C' (number, space, degree sign, C). |
| 18 | 04_methods.md:75 | Punctuation | ...s the X of A1 scales only the term or terms the cell has« and» the law has one modulation; the difference favours A10.... | `COMMA_COMPOUND_SENTENCE_2` | Use a comma before “and” if it connects two independent clauses (unless they are closely connected and short). -> Try: ', and' |
| 19 | 01_introduction.md:26 | Typography | ...e abstract may say only "we found no earlier study that «...»" followed by the conjunction of Section 1.2 item 4. It n... | `proselint.Typography + Microsoft.Ellipses` | Consider using the '…' symbol instead of '...'. \| In general, don't use an ellipsis. |
| 20 | 01_introduction.md:7 | Consistency | ... much from the KAN? Does the KAN yield a closed-form «stress law» that predicts held-out conditions at least as well a... | `term-variant` | Inconsistent spelling of one term: 'Stress-law' x1, 'stress law' x1. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |

## Flags by file

Line:column refers to the source file. Flagged text is the cleaned prose (math shown as X, citations as [1]) with the flagged span between « ».

### paper/draft/00_open_items.md  (working note, not manuscript text)

Per category: Hidden characters 1, Spelling 3, Claim needs evidence 1, Clarity 4, Weak or hedged wording 1, Style 1.

| Line | Category | Flagged text | Rule | Suggestion |
|---|---|---|---|---|
| 1:1 | Hidden characters | [U+FEFF]# Draft index and open items ( | `bom` | Byte-order mark at start of file (harmless for most tools) -> Save as UTF-8 without BOM if a tool complains. |
| 3:453 | Weak or hedged wording | ...sent. The journal's required declaration section is «deliberately» not written here. Length: about 3,900 words includ... | `Microsoft.Adverbs` | Remove 'deliberately' if it's not important to the meaning of the statement. |
| 9:1 | Clarity | «Placeholders that wait for runs: the throughput check and...» | `sentence-length` | Sentence of 69 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 9:145 | Style | ...luded and used; record lengths of the capped windows; «backbone» form per fold and m; whether the freeze-commit timing... | `Microsoft.Avoid` | Don't use 'backbone'. See the A-Z word list for details. |
| 9:359 | Spelling | ...ed by the preregistration and no longer placeholders: k_«cyc» = k_full = 4 and k_sto = 2 (counted from member listings... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'CBC', 'NYC', 'CCC' |
| 9:382 | Spelling | ...on and no longer placeholders: k_cyc = k_full = 4 and k_«sto» = 2 (counted from member listings), the ET_T23 reference... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'STO', 'to', 'so' |
| 11:1 | Clarity | «Statements to verify before the freeze: the definition of...» | `sentence-length` | Sentence of 48 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 13:1 | Clarity | «Prereg and draft text agree (2026-11-06): Section 5.3 fol...» | `sentence-length` | Sentence of 50 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 13:1 | Spelling | ...d in the preregistration and are no longer open here. «Prereg» and draft text agree (2026-11-06): Section 5.3 follows... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. |
| 13:376 | Claim needs evidence | ...troduction contribution list and the abstract rule on «novelty» are in X (sections 1.2 and 1.3; D18 6 / A8, order of D... | `claim-novel` | 'novelty' is a claim, not a result. -> Name what differs from which prior work; keep 'novel' only where a search supports it. |
| 13:516 | Clarity | ... need verified references). «Items of the preregistration's alignment list that have n...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 95 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |

### paper/draft/01_introduction.md

Per category: Claim needs evidence 3, Clarity 11, Abbreviation 5, Consistency 1, Typography 1, Style 1, Placeholder 6.

| Line | Category | Flagged text | Rule | Suggestion |
|---|---|---|---|---|
| 7:367 | Consistency | ... much from the KAN? Does the KAN yield a closed-form «stress law» that predicts held-out conditions at least as well a... | `term-variant` | Inconsistent spelling of one term: 'Stress-law' x1, 'stress law' x1. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 9:142 | Clarity | ...cle part is inadequate [1]. «The present study replaces the stress dependence of such ...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 46 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |
| 15:317 | Clarity | ...n and one end-to-end refit. «Chain K tests whether A15 is non-inferior to the network ...» | `sentence-length` | Sentence of 42 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 16:58 | Clarity | ...der with tuned comparators. «The network with the physics law (A1) is compared with th...» | `sentence-length` | Sentence of 45 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 16:178 | Abbreviation | ... network without the law (A9), with an additive-map law («AG»), with the hard-integrated law (A2), with the dataset au... | `abbr-undefined` | 'AG' is never expanded in the manuscript text (3 uses). -> Write the full term at first use, then '(AG)'. |
| 16:536 | Clarity | ...e never read as a decomposition of the median (Eq. 11). «This» extends the matched comparisons of Jia et al. and Navid... | `bare-demonstrative` | Bare 'This' opening a sentence: antecedent may be unclear. -> Add the noun: 'This <noun> ...'. |
| 16:605 | Placeholder | [AUTHOR: add verified references] | `open-item` | Unresolved placeholder [AUTHOR] -> Resolve before submission. |
| 16:747 | Placeholder | [AUTHOR: confirm wording against the full texts] | `open-item` | Unresolved placeholder [AUTHOR] -> Resolve before submission. |
| 17:80 | Clarity | ...onditions and of check-ups. «For a joint calendar-plus-cycle law, forecast error on he...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 60 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |
| 17:496 | Clarity | ...arger there than at X (P3). «We present this as an extension of the nested learning cu...» | `sentence-length` | Sentence of 46 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 17:657 | Placeholder | [AUTHOR: add verified references] | `open-item` | Unresolved placeholder [AUTHOR] -> Resolve before submission. |
| 17:830 | Clarity | ...trajectory forecasting [1]. «It differs from Lucu et al. in using a joint physics-info...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 43 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |
| 17:1082 | Placeholder | [AUTHOR: confirm against the full texts] | `open-item` | Unresolved placeholder [AUTHOR] -> Resolve before submission. |
| 18:6 | Clarity | «X Text: "To our knowledge, no earlier study has reported ...» | `sentence-length` | Sentence of 73 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 18:6 | Placeholder | [GATED: the conjunction sentence.] | `open-item` | Unresolved placeholder [GATED] -> Resolve before submission. |
| 20:1 | Clarity | «The paper does not call the model, the law or any result ...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 43 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |
| 22:32 | Claim needs evidence | 1.3 Rule for the abstract's «novelty» wording (fixed before any result; internal, not for the manuscript) | `claim-novel` | 'novelty' is a claim, not a result. -> Name what differs from which prior work; keep 'novel' only where a search supports it. |
| 25:28 | Claim needs evidence | The abstract contains no «novelty» sentence until conditions (a) to (d) all hold. Status: (a) Hallinger, (b) Lucu A an... | `claim-novel` | 'novelty' is a claim, not a result. -> Name what differs from which prior work; keep 'novel' only where a search supports it. |
| 25:83 | Clarity | ...itions (a) to (d) all hold. «Status: (a) Hallinger, (b) Lucu A and B and (c) Jia are c...» | `sentence-length` | Sentence of 53 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 25:189 | Claim needs evidence | ...are closed by full-text reading (PREREG_v4 section 1, «novelty» status); (d), the arXiv and OpenReview repeat within 7... | `claim-novel` | 'novelty' is a claim, not a result. -> Name what differs from which prior work; keep 'novel' only where a search supports it. |
| 25:282 | Abbreviation | ...penReview repeat within 7 days of submission, including «ICLR» 2027 and a method-level check of PIKAN, PGKAN and KA-CR... | `abbr-undefined` | 'ICLR' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(ICLR)'. |
| 25:320 | Abbreviation | ...ssion, including ICLR 2027 and a method-level check of «PIKAN», PGKAN and KA-CRNN, is open by design and gates every s... | `abbr-undefined` | 'PIKAN' is never expanded in the manuscript text (4 uses). -> Write the full term at first use, then '(PIKAN)'. |
| 25:327 | Abbreviation | ...including ICLR 2027 and a method-level check of PIKAN, «PGKAN» and KA-CRNN, is open by design and gates every such sen... | `abbr-undefined` | 'PGKAN' is never expanded in the manuscript text (3 uses). -> Write the full term at first use, then '(PGKAN)'. |
| 25:337 | Abbreviation | ...CLR 2027 and a method-level check of PIKAN, PGKAN and «KA-CRNN», is open by design and gates every such sentence. | `abbr-undefined` | 'KA-CRNN' is never expanded in the manuscript text (2 uses). -> Write the full term at first use, then '(KA-CRNN)'. |
| 26:75 | Style | ...e abstract may say only "we found no earlier study that «...»" followed by the conjunction of Section 1.2 item 4. It n... | `ELLIPSIS` | Consider using the typographical ellipsis character here instead. -> Try: '…' |
| 26:75 | Typography | ...e abstract may say only "we found no earlier study that «...»" followed by the conjunction of Section 1.2 item 4. It n... | `proselint.Typography + Microsoft.Ellipses` | Consider using the '…' symbol instead of '...'. \| In general, don't use an ellipsis. |
| 29:3 | Clarity | «Related rules for sections not yet drafted (action A8): t...» | `sentence-length` | Sentence of 67 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 31:1 | Placeholder | [RESULT: none; this section contains no result and is filled only with the abstract numbers of the outcome table.] | `open-item` | Unresolved placeholder [RESULT] -> Resolve before submission. |

### paper/draft/02_related_work.md

Per category: Weak or hedged wording 1, Abbreviation 5, Consistency 1, Placeholder 4.

| Line | Category | Flagged text | Rule | Suggestion |
|---|---|---|---|---|
| 7:38 | Consistency | Data-driven models map features of a «charge segment» or of early cycles to state of health (SOH) or life. Examples ar... | `term-variant` | Inconsistent spelling of one term: 'charge-segment' x1, 'charge segment' x1. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 11:340 | Weak or hedged wording | ...ation has since appeared in this journal as well [1]. «Several» papers combine the idea with KANs. PIKAN and PGKAN, bo... | `write-good.Weasel` | 'Several' is a weasel word! |
| 11:578 | Abbreviation | ...ogate in PGKAN) and report four public data sets [1]. «PI-EKAN» uses eight data sets with a partial-charge window chos... | `abbr-undefined` | 'PI-EKAN' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(PI-EKAN)'. |
| 11:738 | Abbreviation | ... a Verhulst-type residual takes discharge curves of the «TRI» and XJTU cells as input [1]. SOH-KPINN is described by i... | `abbr-undefined` | 'TRI' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(TRI)'. |
| 11:746 | Abbreviation | ...lst-type residual takes discharge curves of the TRI and «XJTU» cells as input [1]. SOH-KPINN is described by its title... | `abbr-undefined` | 'XJTU' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(XJTU)'. |
| 11:786 | Abbreviation | ...harge curves of the TRI and XJTU cells as input [1]. «SOH-KPINN» is described by its title as a wavelet-enhanced physi... | `abbr-undefined` | 'SOH-KPINN' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(SOH-KPINN)'. |
| 11:881 | Placeholder | [TO VERIFY: title only] | `open-item` | Unresolved placeholder [TO VERIFY] -> Resolve before submission. |
| 11:1180 | Placeholder | [TO VERIFY: PGKAN, PI-EKAN and SOH-KPINN full texts] | `open-item` | Unresolved placeholder [TO VERIFY] -> Resolve before submission. |
| 15:436 | Abbreviation | ...work inside the state equation of calendar ageing [1]. «PiDDM» [1] integrates an Arrhenius time term and an Arrhenius ... | `abbr-undefined` | 'PiDDM' is never expanded in the manuscript text (3 uses). -> Write the full term at first use, then '(PiDDM)'. |
| 17:354 | Placeholder | [TO VERIFY: title only] | `open-item` | Unresolved placeholder [TO VERIFY] -> Resolve before submission. |
| 17:483 | Placeholder | [TO VERIFY: full text unread; task and cells used unknown] | `open-item` | Unresolved placeholder [TO VERIFY] -> Resolve before submission. |

### paper/draft/03_data.md

Per category: Spelling 1, Clarity 9, Abbreviation 8, Units and numbers 20, Consistency 5, Placeholder 4.

| Line | Category | Flagged text | Rule | Suggestion |
|---|---|---|---|---|
| 7:178 | Abbreviation | ...ted 4.9 Ah) tested in two stages and three laboratories («HM», INT, SIE) with one protocol. Stage 2 used a new cell ba... | `abbr-undefined` | 'HM' is never expanded in the manuscript text (4 uses). -> Write the full term at first use, then '(HM)'. |
| 7:182 | Abbreviation | ....9 Ah) tested in two stages and three laboratories (HM, «INT», SIE) with one protocol. Stage 2 used a new cell batch, ... | `abbr-undefined` | 'INT' is never expanded in the manuscript text (5 uses). -> Write the full term at first use, then '(INT)'. |
| 7:187 | Abbreviation | ...) tested in two stages and three laboratories (HM, INT, «SIE») with one protocol. Stage 2 used a new cell batch, so st... | `abbr-undefined` | 'SIE' is never expanded in the manuscript text (5 uses). -> Write the full term at first use, then '(SIE)'. |
| 9:39 | Clarity | ...arm. The arm has 132 cells. «The data paper lists 22 test points, and our count from t...» | `sentence-length` | Sentence of 47 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 9:186 | Units and numbers | ...ons after repeated centre points are merged (10, 23 and «45 C»; state of charge 5 to 100 %, limited to 80 % in stage 2... | `temp-bare-C` | Temperature unit written as '45 C'. -> Write '45 °C' (number, space, degree sign, C). |
| 9:486 | Units and numbers | ...in the primary analysis. No storage condition exists at «35 C». | `temp-bare-C` | Temperature unit written as '35 C'. -> Write '35 °C' (number, space, degree sign, C). |
| 11:39 | Clarity | ...arm. The arm has 147 cells. «The data paper lists 49 test points (71 with storage, as ...» | `sentence-length` | Sentence of 41 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 11:294 | Units and numbers | ...e five repeated centre points. Cycling temperatures are «23 C» (10 conditions, 33 cells), 35 C (13 conditions, 39 cell... | `temp-bare-C` | Temperature unit written as '23 C'. -> Write '23 °C' (number, space, degree sign, C). |
| 11:326 | Units and numbers | ...ycling temperatures are 23 C (10 conditions, 33 cells), «35 C» (13 conditions, 39 cells) and 45 C (17 conditions, 75 c... | `temp-bare-C` | Temperature unit written as '35 C'. -> Write '35 °C' (number, space, degree sign, C). |
| 11:361 | Units and numbers | ...nditions, 33 cells), 35 C (13 conditions, 39 cells) and «45 C» (17 conditions, 75 cells). The design varies upper stat... | `temp-bare-C` | Temperature unit written as '45 C'. -> Write '45 °C' (number, space, degree sign, C). |
| 13:2 | Clarity | «Capacity and time. The study provides no capacity table. ...» | `paragraph-length` | Paragraph of 227 words (limit 200). -> Split at a change of sub-topic; one idea per paragraph. |
| 13:191 | Units and numbers | ...arge at C/2 to 4.2 V, discharge at 1C to 2.5 V, ambient «23 C»), integrated from the logged current as in the data pap... | `temp-bare-C` | Temperature unit written as '23 C'. -> Write '23 °C' (number, space, degree sign, C). |
| 13:255 | Clarity | ...rrent as in the data paper. «Retention is capacity divided by a per-cell reference X, ...» | `sentence-length` | Sentence of 56 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 13:340 | Units and numbers | ... divided by a per-cell reference X, the capacity of the «23 C» entry test (ET_T23) of the cell, which comes from the s... | `temp-bare-C` | Temperature unit written as '23 C'. -> Write '23 °C' (number, space, degree sign, C). |
| 13:345 | Consistency | ... by a per-cell reference X, the capacity of the 23 C «entry test» (ET_T23) of the cell, which comes from the same char... | `term-variant` | Inconsistent spelling of one term: 'entry-test' x1, 'entry test' x1. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 13:632 | Clarity | ... written to the run record. «Retention is anchored on the ET_T23 capacity of each cell...» | `sentence-length` | Sentence of 51 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 13:727 | Abbreviation | ...pacity of each cell; the order of the entry tests inside «ET» (10, 45 and 23 C) was not verified, and if the 23 C test... | `abbr-undefined` | 'ET' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(ET)'. |
| 13:742 | Units and numbers | ...ell; the order of the entry tests inside ET (10, 45 and «23 C») was not verified, and if the 23 C test follows the oth... | `temp-bare-C` | Temperature unit written as '23 C'. -> Write '23 °C' (number, space, degree sign, C). |
| 13:777 | Units and numbers | ...nside ET (10, 45 and 23 C) was not verified, and if the «23 C» test follows the others every cell carries the same one... | `temp-bare-C` | Temperature unit written as '23 C'. -> Write '23 °C' (number, space, degree sign, C). |
| 13:1134 | Clarity | ...omes from the design rates. «The analytic value is accepted if its median absolute rel...» | `sentence-length` | Sentence of 43 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 13:1376 | Placeholder | [RESULT: median and maximum relative difference, and the branch taken] | `open-item` | Unresolved placeholder [RESULT] -> Resolve before submission. |
| 15:159 | Clarity | ...The outlier rule is causal. «A check-up is compared only with the two valid check-ups ...» | `sentence-length` | Sentence of 51 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 15:780 | Clarity | ...or its capacity trajectory. «A cell is keyed by serial and stage, and a cell whose sta...» | `sentence-length` | Sentence of 58 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 15:879 | Placeholder | [RESULT: cells excluded] | `open-item` | Unresolved placeholder [RESULT] -> Resolve before submission. |
| 15:1060 | Spelling | ... and stage of these cells follow the file names, the «Testpoint» field, laboratory and dates, which agree for all 279 ... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'Test point' |
| 17:211 | Abbreviation | ... preregistration was frozen, without scoring any model. «ISU» and SNL were explored in a scratch pilot before their sp... | `abbr-undefined` | 'ISU' is never expanded in the manuscript text (3 uses). -> Write the full term at first use, then '(ISU)'. |
| 17:219 | Abbreviation | ...stration was frozen, without scoring any model. ISU and «SNL» were explored in a scratch pilot before their splits wer... | `abbr-before-definition` | 'SNL' is used before it is expanded (expanded in 03_data.md line 23). -> Move the expansion 'The Sandia set (SNL)' to this first use. |
| 17:460 | Units and numbers | ...ed on regular check-up (CU) rows; in the final data the «23 C» entry-test (ET_T23) and extended check-up (exCU) rows e... | `temp-bare-C` | Temperature unit written as '23 C'. -> Write '23 °C' (number, space, degree sign, C). |
| 17:498 | Consistency | ... final data the 23 C entry-test (ET_T23) and extended «check-up» (exCU) rows enter its series, and the thresholds were... | `abbr-expansion-repeated` | 'check-up' is written out again after 'CU' was defined. -> Use 'CU' (journals re-expand only in the abstract and captions). |
| 17:632 | Clarity | ...ged after the full release. «The quality-control thresholds were fixed after those 163...» | `sentence-length` | Sentence of 46 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 17:636 | Consistency | ...olds were not changed after the full release. The «quality-control» thresholds were fixed after those 163 check-ups, w... | `term-variant` | Inconsistent spelling of one term: 'Quality control' x3, 'quality-control' x2. -> Use one form throughout (most frequent: spaced). A hyphen is right only before a noun. |
| 17:894 | Consistency | ...en inspected on them; a sensitivity row retains every «check-up» (Section 5.6). A few capacity values of five cells we... | `abbr-expansion-repeated` | 'check-up' is written out again after 'CU' was defined. -> Use 'CU' (journals re-expand only in the abstract and captions). |
| 19:30 | Units and numbers | Confounds. All 39 cells at «35 C» were run by laboratory INT. Cycling at 45 C is HM (66 cells) and SIE (9 cells), and ... | `temp-bare-C` | Temperature unit written as '35 C'. -> Write '35 °C' (number, space, degree sign, C). |
| 19:74 | Units and numbers | ...39 cells at 35 C were run by laboratory INT. Cycling at «45 C» is HM (66 cells) and SIE (9 cells), and storage at 10 C... | `temp-bare-C` | Temperature unit written as '45 C'. -> Write '45 °C' (number, space, degree sign, C). |
| 19:130 | Units and numbers | ...45 C is HM (66 cells) and SIE (9 cells), and storage at «10 C» is entirely SIE and at 45 C entirely HM. Temperature is... | `temp-bare-C` | Temperature unit written as '10 C'. -> Write '10 °C' (number, space, degree sign, C). |
| 19:158 | Units and numbers | ...E (9 cells), and storage at 10 C is entirely SIE and at «45 C» entirely HM. Temperature is therefore aliased with labo... | `temp-bare-C` | Temperature unit written as '45 C'. -> Write '45 °C' (number, space, degree sign, C). |
| 19:232 | Units and numbers | ...Temperature is therefore aliased with laboratory in the «35 C» test of Section 5 and in part of the storage analysis. ... | `temp-bare-C` | Temperature unit written as '35 C'. -> Write '35 °C' (number, space, degree sign, C). |
| 19:360 | Units and numbers | ...test is also not isothermal: the cell surface averages «31.6 C» (stage 1) and 29.8 C (stage 2) during the 1C discharge... | `temp-bare-C` | Temperature unit written as '31.6 C'. -> Write '31.6 °C' (number, space, degree sign, C). |
| 19:381 | Units and numbers | ...hermal: the cell surface averages 31.6 C (stage 1) and «29.8 C» (stage 2) during the 1C discharge in the 23 C chamber,... | `temp-bare-C` | Temperature unit written as '29.8 C'. -> Write '29.8 °C' (number, space, degree sign, C). |
| 19:429 | Units and numbers | ... 1) and 29.8 C (stage 2) during the 1C discharge in the «23 C» chamber, and laboratories differ. The primary models do... | `temp-bare-C` | Temperature unit written as '23 C'. -> Write '23 °C' (number, space, degree sign, C). |
| 21:8 | Consistency | 3.2 «Secondary data» sets | `term-variant` | Inconsistent spelling of one term: 'secondary-data' x1, 'Secondary data' x1. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 23:1 | Abbreviation | «ISU-ILCC» [1] consists of NMC/graphite pouch cells cycled at varied charge rate, discharge rate and DoD, with weekly ... | `abbr-undefined` | 'ISU-ILCC' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(ISU-ILCC)'. |
| 23:286 | Placeholder | [TO VERIFY: the record states 238 cells in the current release; our processed file has 251] | `open-item` | Unresolved placeholder [TO VERIFY] -> Resolve before submission. |
| 23:509 | Abbreviation | ...chemistries. Our processed copy holds 61 cells (LFP 18, «NCA» 22, NMC 21; our count) cycled at 15, 25 and 35 C and dis... | `abbr-undefined` | 'NCA' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(NCA)'. |
| 23:557 | Units and numbers | ...LFP 18, NCA 22, NMC 21; our count) cycled at 15, 25 and «35 C» and discharge rates of 0.5 to 3C in 23 conditions; time... | `temp-bare-C` | Temperature unit written as '35 C'. -> Write '35 °C' (number, space, degree sign, C). |
| 23:631 | Placeholder | [AUTHOR: cite the verified source of the processed copy] | `open-item` | Unresolved placeholder [AUTHOR] -> Resolve before submission. |
| 29:69 | Units and numbers | ...cling, Test C ; secondary ; 39 held out ; 13 held out ; «35 C», laboratory INT ; [RESULT]  | `temp-bare-C` | Temperature unit written as '35 C'. -> Write '35 °C' (number, space, degree sign, C). |

### paper/draft/04_methods.md

Per category: Punctuation 1, Clarity 24, Weak or hedged wording 1, Abbreviation 3, Units and numbers 1, Consistency 6, Style 1, Placeholder 6.

| Line | Category | Flagged text | Rule | Suggestion |
|---|---|---|---|---|
| 11:1 | Clarity | «For a held-out cell the model receives X, the reference c...» | `paragraph-length` | Paragraph of 253 words (limit 200). -> Split at a change of sub-topic; one idea per paragraph. |
| 11:914 | Clarity | ...for storage cells 01 to 03. «A cell whose number X of intermediate check-ups is not gr...» | `sentence-length` | Sentence of 42 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 11:1135 | Clarity | ...ry arm and every grid cell. «It binds for six cycling cells at X and for two at X, and...» | `sentence-length` | Sentence of 42 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 11:1373 | Placeholder | [RESULT: record lengths] | `open-item` | Unresolved placeholder [RESULT] -> Resolve before submission. |
| 11:1399 | Clarity | ...ontrol are in Appendix A X. «The nominal window of two check-ups is therefore shorter ...» | `sentence-length` | Sentence of 42 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 13:2 | Clarity | «Grid of training conditions and window. We vary two quant...» | `paragraph-length` | Paragraph of 224 words (limit 200). -> Split at a change of sub-topic; one idea per paragraph. |
| 13:631 | Clarity | ...sen from identifiers alone. «For each outer fold, a greedy max-min order over the fold...» | `sentence-length` | Sentence of 60 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 21:160 | Style | ...ation shared by both terms. «The amplitudes are X. X with the normalised Arrhenius abs...» | `TOO_LONG_SENTENCE` | This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. |
| 29:1 | Clarity | «The modulation is constant, self-limiting, X with X, or a...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 75 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |
| 29:441 | Placeholder | [RESULT: form per fold and $m$] | `open-item` | Unresolved placeholder [RESULT] -> Resolve before submission. |
| 29:525 | Consistency | ...X. With one X for both terms, Eq. (2) integrates in «closed form». Let X and X. For piecewise-constant X, X where X eq... | `term-variant` | Inconsistent spelling of one term: 'closed-form' x9, 'closed form' x2. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 39:349 | Clarity | ... training cycling design, with X from the design rates. «Set» (c) holds the calendar twins X of the cycling conditions... | `ENGLISH_WORD_REPEAT_BEGINNING_RULE` | Three successive sentences begin with the same word. Consider rewording the sentence or use a thesaurus to find a synonym. |
| 41:2 | Clarity | «Training and inference. The loss is X where overbars are ...» | `paragraph-length + sentence-length` | Paragraph of 261 words (limit 200). \| Sentence of 44 words (limit 40). -> Split at a change of sub-topic; one idea per paragraph. |
| 45:761 | Consistency | ...gn; the SNL interaction pairs were fixed from the «training-design» structure; neither used Samsung data. For an unsee... | `term-variant` | Inconsistent spelling of one term: 'training design' x2, 'training-design' x1. -> Use one form throughout (most frequent: spaced). A hyphen is right only before a noun. |
| 45:850 | Clarity | ... neither used Samsung data. «For an unseen cell, with network and law frozen, X and X ...» | `sentence-length` | Sentence of 70 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 45:1228 | Consistency | ...o not raise the cell's objective, and stopped at a «gradient norm» of X (relative) or after 100 iterations. A cell tha... | `term-variant` | Inconsistent spelling of one term: 'gradient-norm' x1, 'gradient norm' x1. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 45:1369 | Clarity | ...onverge keeps its last accepted iterate and is counted. «This» is a computational convention adopted because fixed-ste... | `bare-demonstrative` | Bare 'This' opening a sentence: antecedent may be unclear. -> Add the noun: 'This <noun> ...'. |
| 49:287 | Units and numbers | ...s inputs are scaled to X by fixed physical ranges (5 to «50 C»; state of charge 0 to 1; DoD 0 to 0.8; charge rate 0 to... | `temp-bare-C` | Temperature unit written as '50 C'. -> Write '50 °C' (number, space, degree sign, C). |
| 49:381 | Clarity | ... discharge rate 0 to 2.2C). «The cycling map is a KAN X with hidden width X and X (the...» | `sentence-length` | Sentence of 50 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 71:88 | Clarity | ...show what the features buy. «The abscissae of a parametric log-linear stress map (A3: ...» | `sentence-length` | Sentence of 44 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 73:1 | Clarity | «The data-only learners (A11, A12) are trained on the cell...» | `sentence-length` | Sentence of 75 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 75:2 | Clarity | «A10. The dataset authors' model, described in the supplem...» | `paragraph-length` | Paragraph of 324 words (limit 200). -> Split at a change of sub-topic; one idea per paragraph. |
| 75:543 | Clarity | ...s the supplement's reading. «Every A10 contrast is computed for two forms: "as publish...» | `sentence-length` | Sentence of 60 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 75:822 | Abbreviation | ...dicted total loss fitted to the cell's window points by «MAP» with the same prior family as X. The weaker of the two c... | `abbr-undefined` | 'MAP' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(MAP)'. |
| 75:1149 | Punctuation | ...s the X of A1 scales only the term or terms the cell has« and» the law has one modulation; the difference favours A10.... | `COMMA_COMPOUND_SENTENCE_2` | Use a comma before “and” if it connects two independent clauses (unless they are closely connected and short). -> Try: ', and' |
| 75:1255 | Clarity | ...the difference favours A10. «A10 is the published calendar-plus-cycle superposition un...» | `sentence-length` | Sentence of 103 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 75:1514 | Placeholder | [AUTHOR: define EOLC from the source] | `open-item` | Unresolved placeholder [AUTHOR] -> Resolve before submission. |
| 75:1725 | Weak or hedged wording | ...on storage cells and the cycle term on cycling cells «separately»; the calendar term of a cycled cell uses ambient tem... | `Microsoft.Adverbs` | Remove 'separately' if it's not important to the meaning of the statement. |
| 79:1 | Clarity | «Each tuned arm receives the same number X of Tree-structu...» | `paragraph-length` | Paragraph of 246 words (limit 200). -> Split at a change of sub-topic; one idea per paragraph. |
| 79:162 | Consistency | ...timator trials [1], with the sampler seed set to the «outer-fold» index, at every pair of outer fold and X; failed tri... | `term-variant` | Inconsistent spelling of one term: 'outer fold' x3, 'outer-fold' x1. -> Use one form throughout (most frequent: spaced). A hyphen is right only before a noun. |
| 79:271 | Clarity | ...n until X valid ones exist. «Inner folds are grouped by condition, stratified by tempe...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 66 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |
| 79:488 | Consistency | ... An arm is tuned once per outer fold and X, scored in «inner CV» at X for X and at X for X, and the tuned configuratio... | `term-variant` | Inconsistent spelling of one term: 'inner-CV' x2, 'inner CV' x1. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 79:494 | Abbreviation | ... arm is tuned once per outer fold and X, scored in inner «CV» at X for X and at X for X, and the tuned configuration i... | `abbr-undefined` | 'CV' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(CV)'. |
| 79:769 | Clarity | ...e-fit score of Section 5.2. «A timing run at the freeze commit tests a trigger: if the...» | `sentence-length` | Sentence of 41 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 79:867 | Abbreviation | ...trigger: if the median hard-ODE fit exceeds 30 s or the «PINN» fit exceeds 90 s, every arm uses 10 trials and two inne... | `abbr-undefined` | 'PINN' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(PINN)'. |
| 79:945 | Placeholder | [RESULT: whether the trigger fired] | `open-item` | Unresolved placeholder [RESULT] -> Resolve before submission. |
| 81:1 | Clarity | «All computations ran on CPU, one thread, in float32 excep...» | `sentence-length` | Sentence of 42 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 81:308 | Placeholder | [AUTHOR: processor and memory] | `open-item` | Unresolved placeholder [AUTHOR] -> Resolve before submission. |
| 81:389 | Placeholder | [AUTHOR: repository and archive DOI] | `open-item` | Unresolved placeholder [AUTHOR] -> Resolve before submission. |
| 85:1 | Clarity | «A15 extracts a closed form from a trained KAN and G15 doe...» | `paragraph-length` | Paragraph of 313 words (limit 200). -> Split at a change of sub-topic; one idea per paragraph. |
| 85:16 | Consistency | A15 extracts a «closed form» from a trained KAN and G15 does the same for the additive terms of A4. A frozen symbolic ... | `term-variant` | Inconsistent spelling of one term: 'closed-form' x9, 'closed form' x2. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 85:493 | Clarity | ...free coefficients per edge. «With the coefficient counts of the code, this cap leaves ...» | `sentence-length` | Sentence of 43 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 85:1387 | Clarity | ...s the extraction never saw. «The extracted cyclic laws are printed in full as closed f...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 43 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |

### paper/draft/05_evaluation.md

Per category: Clarity 22, Weak or hedged wording 2, Abbreviation 5, Units and numbers 5, Consistency 7, Placeholder 2.

| Line | Category | Flagged text | Rule | Suggestion |
|---|---|---|---|---|
| 9:259 | Consistency | ...t is paired by condition across the grid. Only the «training side» is thinned, to the first X conditions of a nested l... | `term-variant` | Inconsistent spelling of one term: 'training-side' x3, 'training side' x1. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 11:78 | Clarity | ...perature-laboratory domain. «All 13 conditions at 35 C (39 cells, all from laboratory ...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 71 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |
| 11:99 | Units and numbers | ...out temperature-laboratory domain. All 13 conditions at «35 C» (39 cells, all from laboratory INT) are held out; train... | `temp-bare-C` | Temperature unit written as '35 C'. -> Write '35 °C' (number, space, degree sign, C). |
| 11:186 | Units and numbers | ...tory INT) are held out; training uses cycling at 23 and «45 C» (27 conditions, 108 cells, not thinned) and all storage... | `temp-bare-C` | Temperature unit written as '45 C'. -> Write '45 °C' (number, space, degree sign, C). |
| 11:400 | Units and numbers | ...never called temperature extrapolation, the title omits «35 C», and any abstract sentence on it adds that the two cann... | `temp-bare-C` | Temperature unit written as '35 C'. -> Write '35 °C' (number, space, degree sign, C). |
| 11:505 | Units and numbers | ...he two cannot be separated in this design. INT cells at «23 C» stay in training, which separates them only if there is... | `temp-bare-C` | Temperature unit written as '23 C'. -> Write '23 °C' (number, space, degree sign, C). |
| 19:50 | Abbreviation | The primary endpoint is the cell-level retention «RMSE» in percentage points over the forecast set, averaged within co... | `abbr-undefined` | 'RMSE' is never expanded in the manuscript text (3 uses). -> Write the full term at first use, then '(RMSE)'. |
| 19:151 | Clarity | ...n and then over conditions. «The scored forecast of an arm with seed-dependent refits ...» | `sentence-length` | Sentence of 44 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 21:165 | Abbreviation | ... remaining-useful-life error for cells that cross 80 %, «MAE», MAPE, X, run time, parameter count, the number of train... | `abbr-undefined` | 'MAE' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(MAE)'. |
| 21:170 | Abbreviation | ...ining-useful-life error for cells that cross 80 %, MAE, «MAPE», X, run time, parameter count, the number of training c... | `abbr-undefined` | 'MAPE' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(MAPE)'. |
| 29:106 | Clarity | ...test on these X log ratios. «Tier N (non-inferior) requires the median of X to exceed ...» | `sentence-length` | Sentence of 42 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 31:2 | Clarity | «Test. For a margin X let X be the number of conditions wi...» | `paragraph-length` | Paragraph of 293 words (limit 200). -> Split at a change of sub-topic; one idea per paragraph. |
| 35:139 | Consistency | ...e correlation of the sign indicators, so X and the «design effect» is 2.17. A node is rejected at local level X if X. ... | `term-variant` | Inconsistent spelling of one term: 'design-effect' x1, 'design effect' x1. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 35:486 | Clarity | ...exact or distribution-free. «The reason is a simulation, not a result: with shared fol...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 69 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |
| 35:1164 | Clarity | ...an order-statistic interval «[1]: the unadjusted 95 % interval is X and the interval s...» | `sentence-length` | Sentence of 45 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 37:10 | Clarity | Power. «At X, with 30 positive conditions required, 80 % power ne...» | `sentence-length` | Sentence of 61 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 41:1 | Clarity | ...ew for such differences, so Test C is descriptive. «There are» two confirmatory chains, tested in one sequentially r... | `write-good.ThereIs + empty-opener-there` | Don't start a sentence with 'There are'. \| Empty opener 'There are ...'. -> Recast with the real subject. |
| 43:348 | Clarity | ...on the held-out conditions. «P2 asks whether the same network without the physics law ...» | `sentence-length` | Sentence of 45 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 47:33 | Clarity | ... margin 0, tested after P2. «Equation (10) is paired by condition and uses the same wi...» | `sentence-length` | Sentence of 52 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 51:11 | Clarity | Levels. «The initial local level is 0.0195 on P1 (tier N) and 0.00...» | `sentence-length` | Sentence of 42 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 51:376 | Clarity | ...nce the P chain is complete, K1 is tested at 0.025 and «needs» 30 of 40. The choice of weights trades the chains: in s... | `EN_REPEATEDWORDS_NEED` | This word has been used in one of the immediately preceding sentences. Using a synonym could make your text more interesting to read, unless the repetition is intentional. -> Try: 'requires' |
| 55:21 | Clarity | Secondary family. «Five qualifiers form a second graph at 0.025: A1 against ...» | `sentence-length` | Sentence of 66 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 55:82 | Consistency | ...alifiers form a second graph at 0.025: A1 against the «hard ODE» A2 (Q-H) at X and X; A1 against the dataset authors' ... | `term-variant` | Inconsistent spelling of one term: 'hard-ODE' x2, 'hard ODE' x2. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 55:87 | Abbreviation | ...fiers form a second graph at 0.025: A1 against the hard «ODE» A2 (Q-H) at X and X; A1 against the dataset authors' mod... | `abbr-undefined` | 'ODE' is never expanded in the manuscript text (2 uses). -> Write the full term at first use, then '(ODE)'. |
| 55:588 | Weak or hedged wording | ...jected never releases its level, so a family that ends «mostly» at tier N is more conservative than Holm's procedure o... | `write-good.Weasel` | 'mostly' is a weasel word! |
| 57:198 | Clarity | ...simultaneous 95 % interval. «The ladder splits the log ratio of A9 to A1 per condition...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 46 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |
| 63:169 | Clarity | ...efore any data were scored. «Its states combine a gate G, the P state (physics law hel...» | `sentence-length` | Sentence of 58 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 63:586 | Clarity | ...tier S and "matches" never. «Every outcome is reported in the text, including those in...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 44 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |
| 63:760 | Consistency | ...d-form law is no better than the additive law, or the «hard ODE» or the dataset authors' model is better than A1.  | `term-variant` | Inconsistent spelling of one term: 'hard-ODE' x2, 'hard ODE' x2. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 67:759 | Clarity | ...se such as the design hull. «A post-window outlier that the quality-control rule drops...» | `sentence-length` | Sentence of 45 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 67:790 | Consistency | ...s the design hull. A post-window outlier that the «quality-control» rule drops shortens the retained record, so the fo... | `term-variant` | Inconsistent spelling of one term: 'Quality control' x3, 'quality-control' x2. -> Use one form throughout (most frequent: spaced). A hyphen is right only before a noun. |
| 69:129 | Weak or hedged wording | ...X with the stress vectors permuted among conditions, «separately» in the training and the test set, each cell keeping ... | `Microsoft.Adverbs` | Remove 'separately' if it's not important to the meaning of the statement. |
| 71:22 | Clarity | Positive controls. «PC-1 uses a well-specified synthetic generator, G0, built...» | `sentence-length + TOO_LONG_SENTENCE` | Sentence of 49 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. -> Split at the logical joint; keep each qualifier attached to its claim. |
| 75:1 | Clarity | «Four sensitivity rows have a consequence. They are the la...» | `paragraph-length + sentence-length` | Paragraph of 203 words (limit 200). \| Sentence of 57 words (limit 40). -> Split at a change of sub-topic; one idea per paragraph. |
| 75:627 | Clarity | ...ithout rerunning the graph. «The tier is placed on the scale reverse S, none, N, S; th...» | `sentence-length` | Sentence of 49 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 77:85 | Clarity | ...o consequence for any tier. «These include per-laboratory and per-stage differences, l...» | `sentence-length + TOO_LONG_SENTENCE + bare-demonstrative` | Sentence of 46 words (limit 40). \| This sentence is over 40 words long. Consider splitting it up, as shorter sentences make the text easier to read. \| Bare 'These' opening a sentence: antecedent may be unclear. -> Split at the logical joint; keep each qualifie |
| 77:308 | Abbreviation | ...utes each gated tier at X, A10 and cell-window variants, «AT» and storage cells 04 to 06 included, oracle throughput, ... | `abbr-undefined` | 'AT' is never expanded in the manuscript text (1 use). -> Write the full term at first use, then '(AT)'. |
| 79:101 | Clarity | ...stent" or "not consistent". «They cover the effective activation energy against the da...» | `sentence-length` | Sentence of 43 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 79:126 | Consistency | ...t" or "not consistent". They cover the effective «activation energy» against the dataset authors' calendar fit on the ... | `term-variant` | Inconsistent spelling of one term: 'activation-energy' x1, 'activation energy' x1. -> Use one form throughout (most frequent: hyphen). A hyphen is right only before a noun. |
| 79:631 | Units and numbers | ...mperature is aliased with laboratory. Storage at 10 and «45 C» is laboratory-confounded, which is printed with the act... | `temp-bare-C` | Temperature unit written as '45 C'. -> Write '45 °C' (number, space, degree sign, C). |
| 79:714 | Placeholder | [RESULT: Figures 5 and 6] | `open-item` | Unresolved placeholder [RESULT] -> Resolve before submission. |
| 83:523 | Placeholder | [RESULT: estimate] | `open-item` | Unresolved placeholder [RESULT] -> Resolve before submission. |
| 83:733 | Consistency | ... A11 and A12 weight cells equally, A10 weights its «least-squares» points equally, and the endpoint weights cells with... | `term-variant` | Inconsistent spelling of one term: 'least squares' x2, 'least-squares' x1. -> Use one form throughout (most frequent: spaced). A hyphen is right only before a noun. |

### paper/draft/CITATION_AUDIT.md  (working note, not manuscript text)

Per category: Grammar 4, Spelling 10, Punctuation 1, Clarity 5, Units and numbers 1, Typography 8, Style 11.

| Line | Category | Flagged text | Rule | Suggestion |
|---|---|---|---|---|
| 5:184 | Grammar | ..., page or article number, X, X, X); arXiv API for arXiv «ids»; DataCite for the two dataset DOIs; proceedings pages fo... | `ID_CASING` | This abbreviation for “identification” is spelled all-uppercase. -> Try: 'IDs' |
| 48:257 | Clarity | ...entence covers five papers. «Evidence per paper: PIKAN supported by the code; PGKAN pa...» | `sentence-length` | Sentence of 44 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 48:612 | Clarity | ...; SOH-KPINN unread (title). «Suggested wording: say what each source supports, for exa...» | `sentence-length` | Sentence of 46 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 48:1094 | Style | ...iu 2025 full text; PI-EKAN abstract]". The clause "none «...» conditions" is supported only for PIKAN and Liu 2025 (re... | `ELLIPSIS` | Consider using the typographical ellipsis character here instead. -> Try: '…' |
| 48:1094 | Typography | ...iu 2025 full text; PI-EKAN abstract]". The clause "none «...» conditions" is supported only for PIKAN and Liu 2025 (re... | `proselint.Typography + Microsoft.Ellipses` | Consider using the '…' symbol instead of '...'. \| In general, don't use an ellipsis. |
| 48:1199 | Style | ...2025 (read) and for PI-EKAN at abstract level; keep [«TO VERIFY»] for PGKAN and SOH-KPINN. S2. Sec. 2.2, first senten... | `Microsoft.Uppercase` | Don't use all uppercase for emphasis. |
| 50:73 | Grammar | ... sentence: "Wang et al. introduced the form on which «most later» work builds." The form is supported (full text). "Mo... | `MOST_COMPARATIVE` | Only “later” (without ‘most’) is used to write the comparative. -> Try: 'later' |
| 50:134 | Grammar | ...er work builds." The form is supported (full text). "«Most later» work" is not: Liu 2025 uses a fixed Verhulst ODE wit... | `MOST_COMPARATIVE` | Only “later” (without ‘Most’) is used to write the comparative. -> Try: 'Later' |
| 50:357 | Style | ...tract- or title-level. Suggested: "Wang et al. proposed «...» ; PIKAN keeps it with KANs" (code reading) and drop the ... | `ELLIPSIS` | Consider using the typographical ellipsis character here instead. -> Try: '…' |
| 50:357 | Typography | ...tract- or title-level. Suggested: "Wang et al. proposed «...» ; PIKAN keeps it with KANs" (code reading) and drop the ... | `proselint.Typography + Microsoft.Ellipses` | Consider using the '…' symbol instead of '...'. \| In general, don't use an ellipsis. |
| 52:90 | Style | ...ce one or both networks by KANs, namely PIKAN and PGKAN «...», PI-EKAN, ... and SOH-KPINN." For SOH-KPINN nothing beyo... | `ELLIPSIS` | Consider using the typographical ellipsis character here instead. -> Try: '…' |
| 52:90 | Typography | ...ce one or both networks by KANs, namely PIKAN and PGKAN «...», PI-EKAN, ... and SOH-KPINN." For SOH-KPINN nothing beyo... | `proselint.Typography + Microsoft.Ellipses` | Consider using the '…' symbol instead of '...'. \| In general, don't use an ellipsis. |
| 52:104 | Style | ... networks by KANs, namely PIKAN and PGKAN ..., PI-EKAN, «...» and SOH-KPINN." For SOH-KPINN nothing beyond its title (... | `ELLIPSIS` | Consider using the typographical ellipsis character here instead. -> Try: '…' |
| 52:104 | Typography | ... networks by KANs, namely PIKAN and PGKAN ..., PI-EKAN, «...» and SOH-KPINN." For SOH-KPINN nothing beyond its title (... | `proselint.Typography + Microsoft.Ellipses` | Consider using the '…' symbol instead of '...'. \| In general, don't use an ellipsis. |
| 52:524 | Clarity | ...confirms a KAN estimator and an adaptive-PDE surrogate. «So »only SOH-KPINN needs the [TO VERIFY] tag. S4. Sec. 3.1 a... | `write-good.So` | Don't start a sentence with 'So '. |
| 52:553 | Style | ...adaptive-PDE surrogate. So only SOH-KPINN needs the [«TO VERIFY»] tag. S4. Sec. 3.1 and 3.2 data counts. Sec. 3.1 "1... | `Microsoft.Uppercase` | Don't use all uppercase for emphasis. |
| 55:376 | Style | ...es (note samsung50e_dataset_paper.md, "the lead's count «...» is consistent"). Add one sentence that gives both counts... | `ELLIPSIS` | Consider using the typographical ellipsis character here instead. -> Try: '…' |
| 55:376 | Typography | ...es (note samsung50e_dataset_paper.md, "the lead's count «...» is consistent"). Add one sentence that gives both counts... | `proselint.Typography + Microsoft.Ellipses` | Consider using the '…' symbol instead of '...'. \| In general, don't use an ellipsis. |
| 56:204 | Style | ...ataset record (DataCite 10.25380/iastate.22582234: "251 «...» cells ... 63 unique conditions. The current release cont... | `ELLIPSIS` | Consider using the typographical ellipsis character here instead. -> Try: '…' |
| 56:204 | Typography | ...ataset record (DataCite 10.25380/iastate.22582234: "251 «...» cells ... 63 unique conditions. The current release cont... | `proselint.Typography + Microsoft.Ellipses` | Consider using the '…' symbol instead of '...'. \| In general, don't use an ellipsis. |
| 56:214 | Style | ...ord (DataCite 10.25380/iastate.22582234: "251 ... cells «...» 63 unique conditions. The current release contains 238 c... | `ELLIPSIS` | Consider using the typographical ellipsis character here instead. -> Try: '…' |
| 56:214 | Typography | ...ord (DataCite 10.25380/iastate.22582234: "251 ... cells «...» 63 unique conditions. The current release contains 238 c... | `proselint.Typography + Microsoft.Ellipses` | Consider using the '…' symbol instead of '...'. \| In general, don't use an ellipsis. |
| 57:44 | Style | ...t is printed. Sec. 3.2 SNL: "61 commercial 18650 cells «...» [1]". The abstract of Preger et al. gives no cell count;... | `ELLIPSIS` | Consider using the typographical ellipsis character here instead. -> Try: '…' |
| 57:44 | Typography | ...t is printed. Sec. 3.2 SNL: "61 commercial 18650 cells «...» [1]". The abstract of Preger et al. gives no cell count;... | `proselint.Typography + Microsoft.Ellipses` | Consider using the '…' symbol instead of '...'. \| In general, don't use an ellipsis. |
| 58:56 | Units and numbers | Sec. 3.1 values such as surface temperature 31.6 and «29.8 C» are our own computation, not the paper's; they are corre... | `temp-bare-C` | Temperature unit written as '29.8 C'. -> Write '29.8 °C' (number, space, degree sign, C). |
| 60:541 | Style | ....1 of [1], motivated by [1])" and keep the existing [«TO VERIFY»] on the exponents. Minor. Sec. 2.1 "neither [Severs... | `Microsoft.Uppercase` | Don't use all uppercase for emphasis. |
| 64:34 | Spelling | ...be tied to a reading. Sec. 2.3 Gasper pair: replace "«bilevel» symbolic regression" and "stress-factor laws" by the a... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. |
| 67:1 | Clarity | «Sentences supported at the stated level (no action): 2.1 ...» | `sentence-length` | Sentence of 55 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 67:84 | Spelling | ...ated level (no action): 2.1 on KAN definition; 2.1 on «jarraya», yuan, wang2026 (titles), peng; 2.2 on Wang F/G residu... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'array', 'arrays', 'Carrara' |
| 67:118 | Spelling | ...AN definition; 2.1 on jarraya, yuan, wang2026 (titles), «peng»; 2.2 on Wang F/G residual; 2.3 on Kuzhiyil, PiDDM, Guo,... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'Peng', 'pen', 'Penn' |
| 67:291 | Punctuation | ...rotocol, capacity definition, stage-2 SOC limit, cells «01-03» check-ups, laboratory aliasing; 4.3 on the KAN layer fo... | `HYPHEN_TO_EN` | If specifying a range, consider using an en dash instead of a hyphen. -> Try: '01–03' |
| 102:1 | Clarity | «Read in full or in part but not topical for the existing ...» | `sentence-length` | Sentence of 58 words (limit 40). -> Split at the logical joint; keep each qualifier attached to its claim. |
| 102:127 | Spelling | ...nly for form): Jiang et al., JES 182, 124592 (CDUA); «Pugalenthi» et al., JES 153, 120944 (PINEAPPLE); Hassanaly et al... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. |
| 102:175 | Spelling | ...UA); Pugalenthi et al., JES 153, 120944 (PINEAPPLE); «Hassanaly» et al. (Gasper is a coauthor), JES 179, 123823 (neura... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'Passably', 'Passingly', 'Husbandly' |
| 106:75 | Spelling | ...e 169, issue 8, article 080518; five authors (Gasper, «Collath», Hesse, Jossen, Smith). preger2020: volume 167, issue... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'Collate', 'Col lath' |
| 106:91 | Spelling | ... article 080518; five authors (Gasper, Collath, Hesse, «Jossen», Smith). preger2020: volume 167, issue 12, article 12... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'Josses', 'Jos sen' |
| 108:32 | Spelling | ...sue 12, article 120532. piekan2026: first author is «Zekariyas» Yohannes ("Yohannes" is the Crossref family name); re... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'Zacharias', 'Zechariah' |
| 108:102 | Spelling | ...nes ("Yohannes" is the Crossref family name); remove "(«Abebe»)" and the instruction to re-check the DOI string (it re... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'Abbé', 'Abbe', 'Abele' |
| 109:107 | Spelling | ....116868 (JES 124); Crossref spelling of author 6 is "«Abdelhadi»". liu2024kan: record "ICLR 2025" with the arXiv id; ... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'Abdelhakim', 'Abdelhalim' |
| 110:50 | Grammar | ...delhadi". liu2024kan: record "ICLR 2025" with the arXiv «id»; no DOI. zhang2025batlinet: add issue 2 and pages 270-2... | `ID_CASING` | This abbreviation for “identification” is spelled all-uppercase. -> Try: 'ID' |

### paper/draft/WRITER_C3_C17_REPORT.md  (working note, not manuscript text)

Per category: Spelling 2, Claim needs evidence 1, Placeholder 4.

| Line | Category | Flagged text | Rule | Suggestion |
|---|---|---|---|---|
| 3:512 | Spelling | ...eady printed in the PREREG (n = 40, w = 0.78, N = 40, k_«cyc» = k_full = 4, k_sto = 2, 30/31/32/33 of 40, rho_0 = 0.03... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'CBC', 'NYC', 'CCC' |
| 3:532 | Spelling | ...PREREG (n = 40, w = 0.78, N = 40, k_cyc = k_full = 4, k_«sto» = 2, 30/31/32/33 of 40, rho_0 = 0.03, power figures from... | `MORFOLOGIK_RULE_EN_GB` | Possible spelling mistake found. -> Try: 'STO', 'to', 'so' |
| 41:13 | Placeholder | [TO VERIFY: ... neighbour] | `open-item` | Unresolved placeholder [TO VERIFY] -> Resolve before submission. |
| 43:174 | Claim needs evidence | ...ebl, Guo; gated conjunction) and the abstract rule on «novelty» (D18 6 / A8, comment `X01_introduction.md:15-18X:22-28... | `claim-novel` | 'novelty' is a claim, not a result. -> Name what differs from which prior work; keep 'novel' only where a search supports it. |
| 52:5 | Placeholder | [AUTHOR: define EOLC from the source] | `open-item` | Unresolved placeholder [AUTHOR] -> Resolve before submission. |
| 53:5 | Placeholder | [RESULT: cells excluded] | `open-item` | Unresolved placeholder [RESULT] -> Resolve before submission. |
| 57:72 | Placeholder | [AUTHOR: add verified references] | `open-item` | Unresolved placeholder [AUTHOR] -> Resolve before submission. |

### paper/draft/refs_used.md  (working note, not manuscript text)

No flags.

### paper/draft/refs_verified.md  (working note, not manuscript text)

Per category: AI-sounding phrasing 2.

| Line | Category | Flagged text | Rule | Suggestion |
|---|---|---|---|---|
| 29:149 | AI-sounding phrasing | ...ign for lithium-ion battery aging: Insights from a «comprehensive» multi-stage study with real-world data. Journal of ... | `ai-vocab-weak` | 'comprehensive' reads as filler; one is fine, a cluster is a machine-writing signature. -> Replace with the specific property (for example 'large', 'complete', 'important because ...') or delete. |
| 55:73 | AI-sounding phrasing | ...; J. Schmalstieg, S. Kabitz, M. Ecker, D. U. Sauer. A «holistic» aging model for Li(NiMnCo)O2 based 18650 lithium-ion ... | `ai-vocab-weak` | 'holistic' reads as filler; one is fine, a cluster is a machine-writing signature. -> Replace with the specific property (for example 'large', 'complete', 'important because ...') or delete. |

## Words LanguageTool does not know

If a word is correct, add it to `tools/prose_rules/dictionary.txt`; otherwise it is a typo.

| Word | Count |
|---|---:|
| PREREG | 8 |
| SOH | 7 |
| SIE | 5 |
| cyc | 2 |
| sto | 2 |
| adaptive-PDE | 2 |
| Prereg | 1 |
| Testpoint | 1 |
| exCU | 1 |
| ISU-ILCC | 1 |
| MAPE | 1 |
| NeurIPS | 1 |
| BatteryLife-processed | 1 |
| bilevel | 1 |
| jarraya | 1 |
| peng | 1 |
| CDUA | 1 |
| Pugalenthi | 1 |
| Hassanaly | 1 |
| Collath | 1 |
| Jossen | 1 |
| Zekariyas | 1 |
| Abebe | 1 |
| Abdelhadi | 1 |

## What this report cannot tell you

- Grammar and style tools make false positives on scientific prose; each row is a prompt to look, not an error. Math, code spans, citations and HTML comments are replaced by neutral tokens before checking, so what the tools read is not the exact source text.
- The AI-phrasing, claim and abbreviation rules are heuristics from the research-humanizer skill's pattern list. A clean result does not prove the text will pass an AI detector.
- The verbatim-run check compares only with the reference texts held under `refs/fulltext`. It is not a plagiarism service; run Elsevier's iThenticate or your university's checker for a similarity score.
- Tables and headings get the word-level rules only; blockquote banners and fenced code are skipped.
- Abbreviation definition is judged on the manuscript files in the order given; the abstract is not a separate file, so Elsevier's rule of defining again in the main text is not enforced.
