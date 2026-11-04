# PINN + KAN battery health paper (Journal of Energy Storage)

Started 2026-11-04 by Claude Code for Shlok Kumar Goenka (VIT Vellore). Lead session: Opus.

## Every session
1. Read `research/progress.md` (RESUME block) and `research/DECISIONS.md`. Nothing else up front.
2. Every agent brief points to `research/CONTRACT.md` (the shared spec). Agents write report files,
   reply in at most 5 lines.
3. Decisions are rows in `research/DECISIONS.md`: append-only; a re-opened decision gets a new row
   that names the one it supersedes.

## Hard rules
- No number in any document unless it comes from a file in `runs/<run-id>/`.
- No citation unless verified by DOI/Crossref and checked against the sentence that cites it.
- Proposer is never validator. Every decision passes a proposer / opponent / judge debate with the
  four questions in CONTRACT.md section 3.
- Retired (Shlok's Paper 2): effect of the evaluation split on SOH/RUL accuracy; conformal or
  uncertainty calibration under chemistry, dataset or lab-to-field shift. Leakage-free evaluation is
  standard practice here, never the contribution.
- AI use is mentioned only in the Declaration of generative AI use (every tool, every use), nowhere
  else: not in Methods, Acknowledgments or the cover letter.
- No Fable. Sonnet for implementers, Haiku for mechanical work, Opus only for the hardest piece or
  a final review. Pass `model` explicitly.
- GPU: 12 GB laptop with a crash history. CPU first. Any GPU job needs Shlok's go-ahead, a check of
  `nvidia-smi`, and a message to the CRP-S07 session (Thenboli review paper) first; never in
  parallel with another session's GPU job.
- Untrusted downloads go to their own directory; Python that reads them runs with `-I`.
