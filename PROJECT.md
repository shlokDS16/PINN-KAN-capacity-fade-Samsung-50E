# PINN + KAN capacity-fade paper — Journal of Energy Storage (Elsevier)

- **Target journal:** Journal of Energy Storage (JES), ISSN 2352-152X. Build every section, figure and sentence for JES.
- **Paper:** a PINN whose dynamics combine a calendar term (Arrhenius x KAN of storage SOC) and a cycling term (KAN over T,
  SOC window, DoD, C-rates), trained on Samsung INR21700-50E storage + cycling cells, forecasting capacity fade at held-out
  conditions. Design R2; the title comes from the closed outcome table (PREREG_v4 section 11) after the runs.
- **Author:** Shlok Kumar Goenka (VIT Vellore); co-authors not yet recorded (ask Shlok).
- **State 2026-11-07:** FROZEN at ce0cc0d (PREREG_v4 rev. 24; gate auditor FREEZE OK; verify_freeze passes). HEAD must
  not move. **Campaign running since 2026-11-07 12:21** (Shlok's go-ahead): item (f), then 276 confirmatory configs on 3 CPU
  lanes, `runs/confirmatory/run_campaign.py`; progress (return codes only) in `runs/confirmatory/campaign_status.json`.
  Do not read any score before the campaign ends (stop rule 6); pause with `runs/confirmatory/STOP`; keep the charger in.
  Item (f) done 13:35 (5/5 rc 0, `runs/item_f/item_f_dependence.json`). Worker count is live in `runs/confirmatory/LANES`
  (1-3): set to 1 at 13:36 so the CRP-S09 ACME GPU queue has its 6 GB of free RAM; back to 3 when that queue is done.
- **Read next:** `research/PROJECT_CONTEXT.md` (full context pack: goal, state, plan, workstreams, rules), then only what your
  task needs. Never move HEAD of the main checkout or edit `code/` / `runs/prereg/` there after FROZEN: use a branch worktree.
- **Obsidian:** `Projects/PINN KAN battery paper/knowledge/HUB.md` (context, every decision, entities, exemplars, audits).
