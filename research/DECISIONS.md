# Decision ledger (append-only)

Row format:

### D<NNN> <short name> (<date>, status: proposed | accepted | revised | rejected | superseded by D<MMM>)
- **Decision:**
- **Alternatives and why they lost:**
- **Evidence:** (file paths, debate file)
- **Proposer / opponent / judge:**
- **Re-open if:**

---

### D001 Project folder and venue (2026-11-04, status: accepted)
- **Decision:** project lives in `C:\Users\Shlok\Downloads\PINN KAN battery paper` (own git repo,
  outside the DLM repo); venue Journal of Energy Storage (Elsevier), as Shlok set.
- **Alternatives and why they lost:** inside the DLM repo (mixes projects and their ledgers); inside
  the old battery Paper 2 folder (risks reuse of its retired framing).
- **Evidence:** task brief from the lead session, 2026-11-04.
- **Proposer / opponent / judge:** lead (Shlok's brief; no debate needed).
- **Re-open if:** Shlok names another folder.

### D002 Compute and access for the night of 4-5 Nov (2026-11-04, status: accepted)
- **Decision:** CPU only tonight unless Shlok says "GPU ok"; at most 3 agents at once (3.6 GB RAM
  available at 20:35); no Chrome automation (no browser connected); paywalled full texts listed for
  Shlok to save by hand.
- **Alternatives and why they lost:** short guarded GPU chunks (standing order of 27 Oct: no
  unattended GPU; the CRP-S07 session uses the GPU tonight; PINN+KAN SOH models are small enough for
  CPU); 5 agents (RAM too low; crash history with low free RAM on 17-18 Oct).
- **Evidence:** memories laptop-gpu-crashes, parallel-research-sessions; `nvidia-smi` at 20:30.
- **Proposer / opponent / judge:** lead; rule-driven.
- **Re-open if:** Shlok gives a GPU go-ahead, or RAM frees up.
