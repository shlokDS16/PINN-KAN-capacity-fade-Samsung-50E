# Project context pack: PINN + KAN capacity-fade paper (read this first)

Every session and sub-session on this project reads this file before anything else. It says what we are
writing, for which journal, where the work stands and what comes next. Last updated 2026-11-07 by the lead
session. The Obsidian mirror is `C:\Users\Shlok\Downloads\obsidian\Claude code obsidian\Projects\PINN KAN battery paper\context\`.
Details live in the files named here; read only the ones your task needs.

## 1. Goal and venue
- **Journal: Journal of Energy Storage (JES), Elsevier, ISSN 2352-152X** (D001). Every display item, section
  and sentence is built for JES. The aim is the strongest paper in our niche the journal has published.
- **Author guide:** `notes/JES_guide_for_authors_2026-11-04.md`. **Style guide:** `notes/exemplars/JES_STYLE_GUIDE.md`.
  **What JES rewards, and where its best papers are weak:** `notes/exemplars/BLUEPRINT_v2.md`. Exemplar notes:
  `notes/exemplars/deep/` (Stroebl 2026, Lucu 2020 A/B, Richardson 2019, Guo 2022, PIKAN, PGKAN, KA-CRNN).
- **Author:** Shlok Kumar Goenka (VIT Vellore). Co-authors and the corresponding author are not yet recorded;
  ask Shlok, never guess.
- **Topic:** a physics-informed neural network whose degradation dynamics combine a storage (calendar) term
  (Arrhenius, Kolmogorov-Arnold network (KAN) of storage SOC) with a cycling term (KAN over temperature, SOC window,
  DoD and C-rates). It is trained jointly on storage and cycling cells and forecasts the capacity retention of
  cells at held-out stress conditions from their first check-ups (D005, D016).
- **Design R2** (`debates/D016_roles/02_judge.md`): data-efficiency grid m = 8/16/32 cycling conditions x k = 0/2/full
  check-ups (g1 = (8, 2) headline cell, g4 = (32, full)); PINN attribution by an ablation ladder; KAN closed-form law
  against an equally simplified GAM law; a closed outcome table of titles T1-T9 (PREREG_v4 section 11, approved by
  Shlok, D017/D019/D030). **The title is chosen by the table after the runs, never by hand.**
- **Data:** Samsung INR21700-50E (Stroebl et al., JES 142, 119552) is primary: 279 cells, 40 cycling + 19 storage
  conditions, 3 labs. ISU-ILCC is secondary and SNL is a check. NASA/CALCE is a descriptive addendum (D022).
- **Novelty (claim the combination only):** a closed-form PINN-KAN law with calendar and cycle ageing together, the
  check-up (k) axis, and paired condition-level tests. Nearest prior work: PIKAN, PGKAN (JES 2026), KA-CRNN
  (JES 158, 121853), PiDDM (arXiv 2607.29095), Lucu 2020 A/B (learning curves; D029). See `notes/papers/PRIORART_SUMMARY.md`.

## 2. State on 2026-11-07
- **Preregistration:** `runs/prereg/PREREG_v4.md` rev. 23. Statistician and red team have both SIGNED every row,
  including the C-rate ablation row 9.9 (u) (D041). Section 11 sha256 `001b1c79...c9e5` must never change.
- **Freeze:** candidate commit `d13a8c6`. The freeze-commit runs (FB-8, FB-8b, FB-9, FB-10, test suite, head comparison)
  are being repeated there now (`runs/freeze_runs/run_all_d13a8c6.sh`, log `runs/freeze_runs/logs/queue.log`).
  Then: record commit (rev. 24), gate-auditor check, `runs/freeze_runs/write_frozen.py` writes `runs/prereg/FROZEN`
  (untracked) and runs `verify_freeze`. The lead session does these steps; no other session touches them.
- **After FROZEN:** the item (f) runs, then the confirmatory runs (about 32 CPU-h plus 4-5 CPU-h for row (u)).
  **They need Shlok's go-ahead with the charger in.**
- **Manuscript:** drafts of sections 1-5 in `paper/draft/` (outcome-independent text only). Prose check report:
  `paper/draft/PROSE_CHECK_REPORT.md` (232 flags). Figures are SYNTHETIC demos in `paper/figures/` until the runs exist.
- **Exemplars:** 9 paywalled JES papers are still unread (`refs/PAYWALLED_FOR_SHLOK.md`). ScienceDirect gives full
  text only on VIT Wi-Fi in the daytime, through the e-gateway in Claude in Chrome.

## 3. Plan and workstreams
| Stream | Owner | Where | Done when |
|---|---|---|---|
| Freeze (record commit, audit, FROZEN) | lead session | main checkout | `verify_freeze` passes; HEAD = FROZEN commit |
| Confirmatory runs and statistics step | lead, after Shlok's go-ahead | main checkout | strict statistics step outputs in `runs/` |
| Manuscript: blueprint gaps, outcome-independent text, prose QA | writing sub-session | branch worktree `writing` | sections pass prose_check, humanizer, hidden-unicode |
| Paywalled exemplars: read and fold into the blueprint | exemplar sub-session | branch worktree `exemplars` | 9 deep notes, BLUEPRINT_v2 and style guide updated |
| Results text, figures from real runs, title from the table | lead + writer | after the runs | numbers all traced to `runs/` files |
| Novelty re-check (condition (d)) | novelty auditor | within 7 days of submission | verdict file |
| Submission package (JES Word template, highlights, graphical abstract, declarations) | lead + writer | last | render-checked PDF and Word |

## 4. Rules every session follows
- **Never move HEAD of the main checkout** (`C:\Users\Shlok\Downloads\PINN KAN battery paper`) once FROZEN exists, and
  never edit tracked files under `code/` or `runs/prereg/` there (D031; the guard refuses every run otherwise).
  Sub-sessions work in their own branch worktree: `git -C "<repo>" worktree add "<repo>-<name>" -b <name> d13a8c6`.
- **Never open Samsung retention values or any test fold before FROZEN.** The code guard enforces it; do not work around it.
- **No number in any document unless it comes from a file in `runs/<run-id>/`.** A number not yet available is written
  `[RESULT: what, file, field]`. No citation unless verified (DOI/Crossref) and checked against its sentence (`paper/draft/refs_verified.md`).
- **Claim sentences, titles and tier words are fixed** by PREREG_v4 sections 11 and 11a; never paraphrase them.
- **Retired topics** (Shlok's earlier paper): the effect of the evaluation split on SOH/RUL accuracy; conformal or
  uncertainty calibration under shift. Leakage-free evaluation is standard practice here, never a contribution.
- **AI use** is stated only in the Declaration of generative AI use (every tool, every use), nowhere else.
- **Prose QA on every text:** `research-humanizer` skill, `hidden-unicode` scan, then `tools/prose_check.py`
  (LanguageTool + Vale + JES rules; `tools/PROSE_CHECK_README.md`). Give Shlok the flagged passages with file:line.
- **Models:** no Fable. Sonnet for implementers, Haiku for mechanical work, Opus for the hardest piece or a final
  review; pass `model` explicitly. At most 3 agents at once per session. Proposer is never validator.
- **Compute:** CPU only unless Shlok says "GPU ok"; CRP sessions use the GPU. Keep our CPU jobs near 3 GB RAM.
- **Python:** call `.venv/Scripts/python.exe -P` with `</dev/null`; never a bare `python -` (it hangs). Untrusted
  downloads run with `-I` in their own directory. Use Write/Edit, not heredocs, for code with backslashes.
- **Browser:** never enter credentials, solve CAPTCHAs or answer Cloudflare checks; ask Shlok.
- **Decisions:** append-only rows in `research/DECISIONS.md` (D001-D041 so far); a re-opened decision gets a new row.

## 5. Where things are
- Shared spec for agents: `research/CONTRACT.md`. Running log: `research/progress.md`. Decisions: `research/DECISIONS.md`.
- Audits and signatures: `research/audits/`. Debates: `debates/`. Paper drafts: `paper/draft/`. Code: `code/pinnkan/`.
- Code graph: `graphify-out/` and the vault's `MODULE_MAP.md`; ask `graph-memory where <symbol>` before grepping.
- Writing agent: `.claude/agents/jes-research-writer.md`. Morning status for Shlok: `status/STATUS_MORNING.md`.
