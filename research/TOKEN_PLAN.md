# Token plan: PREREG freeze to FROZEN (2026-11-06, token-steward)

**Budget.** Weekly 31% (lead's figure; re-read `get_usage` before each dispatch), Fable 0%. Weeks of 10-19 and 10-26 started on Mondays, so
about 60-65% of the week has elapsed (assumption: confirm the reset day): mode FULL, but three paper sessions share the limit.
Cap for this phase: **6 points** (31 -> 37%); stop spawning at 35%, stop at 37%. Opus only where the project rule allows (sign-offs, final gate).

**Biggest cost is the lead, not the agents.** Every lead turn re-sends about 480k of context. At an assumed 25 more turns to FROZEN
that is about 12M tokens read, against about 2.2M for all agents below (sizing). A fresh lead starts near 60-80k. So hand off first (section 4).

## 1. Model per remaining step
| Step | Who | Model | Expect | Note |
|---|---|---|---|---|
| 1a D033 code batch | running coder | sonnet | finish only | Do not resume again (about 530k). If it needs more, a fresh coder gets its report file. |
| 1b D034 code + 276 configs at N = 40 | one fresh coder | sonnet | 250k | Merged: AD1-AD6 code, D035 regeneration, one dispatch. Focused tests only. |
| 2 P3 re-simulation | running statistician | as launched | finish only | Must also cover the skill-test size (D033 re-sign plan item 3); if not, add it here, not as a new agent. |
| 3 PREREG rev. 16 | one fresh designer | sonnet | 250k | One pass: D033 designer items + AD text + D035 (section 16: about 16 -> 32 CPU-h) + C20 stale cells + P3 numbers. Starts when step 2 lands. |
| 4a statistician re-sign | fresh | opus | 150k | Sections 6, 9, 16 + rev. 15 -> 16 diff + simulation files. |
| 4b red-team re-sign | fresh | opus | 180k | Sections 1, 10, 11 + F1-F8 probe scripts + diff. |
| 5 FB-8/9/10 + full suite | lead, local | none | 0 agent | Detached jobs, `keep_awake_while.py`. FB-9 once, at the candidate commit. |
| 6 gate-auditor freeze audit | fresh | opus | 150k | Also refreshes PREFREEZE_STATUS.md (no separate refresh). Scripted checks of pins and hashes. |
| 7 FROZEN | lead | none | 0 | |
| FB-1 / C4 novelty | one agent when PDFs arrive | sonnet | 200k | One dispatch for both; skip if Shlok waives. |

## 2. Merge or skip
- Merge: 1b + regeneration; rev. 16 + C20 pass; PREFREEZE refresh into the audit. Run 1b and step 3 in parallel (2 agents; they touch code and PREREG separately), then diff the title strings in code against section 11 with a script.
- Keep separate: statistician and red-team re-signs (different lenses, proposer is never validator) and the gate auditor. Run 4a and 4b in parallel.
- Skip: a rev. 17. The lead lists every remaining text edit before dispatching the designer. Skip the coder's full `nc1_full` (F7 needs only the short synthetic unit test); the lead's FB-9 is the one full run. Skip the full suite until the candidate commit.
- Reuse vs fresh: fresh for everything above. A fresh agent starts near 40-70k (brief + report + scoped sections); a resumed one re-sends its whole history every turn (rule 11, over about 250k = fresh). The sign reports (14 KB each) plus the D033 judge (8.6 KB) are the re-sign briefs.
- Fix round after a failed sign-off: one batch from the findings only; text-only fix re-checks on sonnet, statistics on opus. Never haiku for a signature.

## 3. Brief-size rules (bytes measured; tokens about bytes / 4)
1. Brief at most 1.5k tokens: task, report path, finish line, 5-line reply, pointers. First line: `research/CONTRACT.md`.
2. PREREG_v4.md is 248 KB (about 62k tokens). Never read it whole. Sections: 1 = 12.6 KB, 10 = 4.5, 11 = 9.9 (red team, about 7k tokens); 9 = 32.5, 6 = 4.3, 16 = 2.5 (statistician, about 10k); 17 and 19-22 = 80 KB change log: no one reads them. Find by `Grep ^## `, then Read offset/limit.
3. Re-signers read `git diff <rev15 commit> -- runs/prereg/PREREG_v4.md` first, then only the cited sections.
4. Code: stats_v4.py 78 KB, stats_step.py 47 KB, stats_rows.py 19 KB. Give file:line pointers from the D033 judge; `graph-memory where/impact` for new symbols. Open cited lines only.
5. DECISIONS.md is 69 KB: read rows D033-D035 (lines 663-710) only.
6. Coders: focused tests with `rtk`, tail 20 lines; the lead runs the full suite once. Reports go to a file (3 KB cap); reply = status, commit, one test line, at most 5 concerns.
7. Dispatch only when no agent is editing the same files (the working tree has 230 uncommitted entries from the running coder).

## 4. Hand-off
- **H1 (now, at the next idle point):** as soon as the D033 coder and the statistician have returned and nothing is in flight (their notifications go to the session that launched them, so never hand off with an agent running). Then the fresh lead dispatches 1b, 3, 4a, 4b, 6. The current lead is past the 250k rule by about 230k.
- **H2:** after FROZEN, before the 32 CPU-h runs. Poll with a background wait, not turns; at most one check every 1-2 h.
- **H3:** before the statistics step and the manuscript (separate sessions; Sonnet writers, one Opus final review).
- Hard stops: 250k per phase, never 850k. Re-check `get_usage` at each boundary.

**Handoff note** (RESUME block in progress.md, at most 40 lines, then `graph-memory sync --note ... --next ...`):
1. Git: branch, last commit SHA, what is uncommitted and who owns it, last test count and date.
2. Agent table: role, model, tokens, report path, commit, status. In flight: none.
3. Next action per remaining step (section 1), with the dispatch pointers (judge file path, line ranges, report files).
4. Ledger: next free decision number (D036), D034 answers, D035 N = 40 and the CPU-h figures, restated power (30 of 40; K1 0.734 / 0.343) still to tell Shlok.
5. Blocked on Shlok: Hallinger PDF or waiver (FB-2, C8), Lucu / Jia PDFs or waiver (C4).
6. Budget: weekly %, Fable %, cap and points used, tokens per agent.
7. Environment: running processes and PIDs, keep-awake, CRLF pin rule (D031), no GPU, other sessions.
8. Start prompt: `graph-memory brief`, then RESUME in progress.md, then dispatch step N. Nothing else.

## 5. Sizing (formula)
New implementers 2 x 350k + reviews 3 x 180k + one re-review 120k = 1.36M; +30% = 1.77M; plus about 0.2M to finish the two running agents and 0.2M for FB-1/C4 = about 2.2M. Tokens-to-points is not yet measured: read points before dispatching 1b and after step 3, then recompute against the 6-point cap.
