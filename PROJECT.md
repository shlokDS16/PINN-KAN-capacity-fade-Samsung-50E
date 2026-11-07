# PINN + KAN capacity-fade paper — Journal of Energy Storage (Elsevier)

- **Target journal:** Journal of Energy Storage (JES), ISSN 2352-152X. Build every section, figure and sentence for JES.
- **Paper:** a PINN whose dynamics combine a calendar term (Arrhenius x KAN of storage SOC) and a cycling term (KAN over T,
  SOC window, DoD, C-rates), trained on Samsung INR21700-50E storage + cycling cells, forecasting capacity fade at held-out
  conditions. Design R2; the title comes from the closed outcome table (PREREG_v4 section 11) after the runs.
- **Author:** Shlok Kumar Goenka (VIT Vellore); co-authors not yet recorded (ask Shlok).
- **State 2026-11-07:** prereg rev. 23 signed by statistician and red team; candidate freeze commit d13a8c6; freeze runs
  repeating; then record commit, gate audit, FROZEN. Confirmatory runs (~37 CPU-h) need Shlok's go-ahead.
- **Read next:** `research/PROJECT_CONTEXT.md` (full context pack: goal, state, plan, workstreams, rules), then only what your
  task needs. Never move HEAD of the main checkout or edit `code/` / `runs/prereg/` there after FROZEN: use a branch worktree.
- **Obsidian:** `Projects/PINN KAN battery paper/knowledge/HUB.md` (context, every decision, entities, exemplars, audits).
