# Morning status for Shlok: PINN + KAN battery paper for JES (written 4 Nov 23:15; updated overnight)

Folder: `C:\Users\Shlok\Downloads\PINN KAN battery paper` (own git repo). Budget: weekly usage 5% at
start, 6% at 22:00 (see the end of this file for the latest); Fable 0%. CPU only, no GPU used.

## 1. What is decided (all rows in research/DECISIONS.md, with alternatives and reasons)
- **Topic and title (D005, after a full debate: proposer, opponent, Codex panel, judge).** A PINN
  (solution network with a physics residual) whose dynamics add a calendar-ageing term (Arrhenius in
  temperature, KAN function of storage state of charge) to a cycle-ageing term (KAN over temperature, SOC
  window, depth of discharge and C-rates), trained on storage and cycling cells together, forecasting the
  capacity of cells at ageing conditions never seen in training, from their first check-ups.
  Preferred title: *Physics-informed neural networks with Kolmogorov-Arnold stress functions forecast
  calendar and cycle ageing of lithium-ion cells at untested conditions* (two alternatives in
  debates/D010_topic/04_judge.md; the word "forecast" stays only if the main result wins).
- **Why not the first idea (plain PINN+KAN SOH on XJTU/TJU/MIT/HUST):** already published twice in JES
  by the USTC group (PIKAN, JES 153, 120860; PGKAN, JES 182, 124768). Their code shows loss weights picked
  on the test set and per-cell whole-life scaling, so they cannot forecast; our paper targets that gap.
- **Novelty (D006):** "novel as a combination" (confidence 0.6): no PINN or KAN work on this dataset, no
  KAN battery paper with a calendar term or coupled calendar + cycle stress functions. Comparators we must
  beat: the dataset authors' own JES model (Stroebl et al., JES 142, 119552) and PiDDM (arXiv 2607.29095).
- **Data (D005):** Samsung INR21700-50E (Stroebl et al., Sci. Data 11, 1020, 2024; 279 EV-format cells,
  storage + cycling arms, 3 temperatures) primary; ISU-ILCC (251 cells, 63 cycling conditions) secondary;
  Sandia SNL external check. Your old datasets (XJTU/TJU/MIT/HUST) are not used, as you preferred.
- **Pre-set outcomes, so results cannot be spun:** the KAN is called better only if it beats an
  interaction GAM; if a plain integrated ODE beats the PINN, you choose the framing (see section 3).
- **Figures (D003, your instruction):** figure and table forms follow the best JES papers; catalogue in
  notes/exemplars/FIGURE_FORMS.md, blueprint in notes/exemplars/BLUEPRINT.md (in progress).

## 2. Needs you (sign-in or yes)
1. **VIT e-gateway: save PDFs into `refs/pdf/`.** List with links: `refs/PAYWALLED_FOR_SHLOK.md`
   (31 of your 35 references, plus exemplars). Most urgent, in this order: PIKAN (doi
   10.1016/j.est.2026.120860), PGKAN (10.1016/j.est.2026.124768), Stroebl et al. JES 142, 119552 and
   their 2026 JES follow-up, JES 182, 125097 (cites our dataset), then the rest of the list.
2. **Samsung 50E data on a fast network (if the overnight fetch is incomplete; see section 4).** Full
   release is 10.29 GB at https://doi.org/10.6084/m9.figshare.25975315 ("Download all"); put the zip
   files in `data/raw/samsung50e_full/`. Tonight the link ran at 2-75 KB/s, so only the small check-up
   files are being fetched.
3. **Approve the title and framing** (section 1), or tell me what to change.

## 3. Open questions (decided by pre-registered tests, then put to you)
- If the plain integrated ODE beats the PINN (pilot P5 / confirmatory test), do you want the paper framed
  as "physics-informed KAN" with the PINN as a comparison? (Your brief says PINN + KAN; the judge kept the
  PINN central but fixed this rule in advance.)

## 4. Overnight work (updated as it finishes)
- Pilots: P0 Samsung file layout GO (capacity computable from check-up files); P1 data checks GO; P2 fit
  timing GO (PINN about 16-19 s per fit on CPU); P3 headroom, P4 KAN vs GAM (synthetic), P5 PINN vs hard
  ODE (synthetic): running.
- Downloads: Samsung check-up files for all 279 cells by range requests (status:
  data/SAMSUNG_CU_STATUS.md; log data/logs/samsung_cu.log). Bulk downloader paused (data/STOP_DOWNLOADS)
  because of the slow link.
- References read in full so far: 8 (refs 8, 11, 15, 23, 29, 30, 31, 33), plus the Samsung dataset paper
  and the ISU dataset paper; notes in notes/papers/.
