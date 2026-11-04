#!/bin/bash
# P2 extra: sensitivity to the number of observed points per cell (Samsung check-up cadence is far below 80). Run from ROOT.
PY=.venv/Scripts/python.exe
OUT=runs/pilot_P2/raw
export CUDA_VISIBLE_DEVICES=""
for seed in 0 1 2; do
  for thr in 1 3; do
    for m in hard pinn; do
      $PY -I code/pilots/p2_timing_run.py --root . --model $m --threads $thr --variant base --m_obs 20 --steps 2000 --seed $seed --out $OUT/${m}_m20_t${thr}_s${seed}.json
    done
  done
done
for thr in 1 3; do
  $PY -I code/pilots/p2_timing_run.py --root . --model hard --threads $thr --variant base --m_obs 40 --steps 2000 --seed 0 --out $OUT/hard_m40_t${thr}_s0.json
done
echo ALLDONE2
