#!/bin/bash
# P2 driver: sequential timed fits (one process each), CPU only. Run from ROOT.
PY=.venv/Scripts/python.exe
OUT=runs/pilot_P2/raw
mkdir -p $OUT
export CUDA_VISIBLE_DEVICES=""
for seed in 0 1 2; do
  for thr in 1 3; do
    for m in hard pinn; do
      $PY -I code/pilots/p2_timing_run.py --root . --model $m --threads $thr --variant base --steps 2000 --seed $seed --out $OUT/${m}_base_t${thr}_s${seed}.json
    done
  done
done
for thr in 1 3; do
  for m in hard pinn; do
    $PY -I code/pilots/p2_timing_run.py --root . --model $m --threads $thr --variant scale279 --steps 2000 --seed 0 --out $OUT/${m}_scale279_t${thr}_s0.json
  done
done
for thr in 1 3; do
  $PY -I code/pilots/p2_timing_run.py --root . --model pinn --threads $thr --variant fullcycle --steps 2000 --seed 0 --out $OUT/pinn_fullcycle_t${thr}_s0.json
done
echo ALLDONE
