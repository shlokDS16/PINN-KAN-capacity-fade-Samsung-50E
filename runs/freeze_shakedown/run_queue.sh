#!/bin/bash
# shake-down queue: 3 single-thread CPU processes, no GPU
cd "/c/Users/Shlok/Downloads/PINN KAN battery paper"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=""
L=runs/freeze_shakedown/logs; mkdir -p $L
run() { c=$1; n=$(basename $c .json); echo "$(date '+%F %T') start $n" >> $L/queue.log
  .venv/Scripts/python.exe -P code/run_pinnkan.py --config $c --runs-dir runs > $L/$n.out 2>&1; rc=$?; echo "$(date '+%F %T') end $n rc=$rc" >> $L/queue.log; }
C=runs/freeze_shakedown/configs
( run $C/timing_samsung_B0_m32.json; run $C/timing_samsung_B0_m8.json; run $C/smoke_snl_B0.json ) &
( run $C/nc1_full_synth_m8.json ) &
( run $C/smoke_isu_B0.json; run $C/nc1_full_synth_m32.json ) &
wait; echo "$(date '+%F %T') ALL DONE" >> $L/queue.log
