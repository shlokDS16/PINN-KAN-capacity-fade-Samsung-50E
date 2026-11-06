#!/bin/bash
# Freeze-commit runs FB-8 / FB-9 / FB-10 and the full test suite (C15). CPU only, 3 single-thread processes.
cd "/c/Users/Shlok/Downloads/PINN KAN battery paper"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=""
L=runs/freeze_runs/logs; mkdir -p $L
echo "$(date '+%F %T') HEAD $(git rev-parse HEAD) dirty_code_prereg=$(git status --porcelain --untracked-files=no -- code runs/prereg | wc -l)" >> $L/queue.log
run() { c=$1; n=$(basename $c .json); echo "$(date '+%F %T') start $n" >> $L/queue.log
  .venv/Scripts/python.exe -P code/run_pinnkan.py --config $c --runs-dir runs > $L/$n.out 2>&1; rc=$?; echo "$(date '+%F %T') end $n rc=$rc" >> $L/queue.log; }
suite() { for t in code/tests/test_*.py; do r=$(.venv/Scripts/python.exe -P -m pytest $t -q -p no:cacheprovider 2>&1 | tail -1); echo "$t: $r" >> $L/suite.log; done
  echo "$(date '+%F %T') suite done" >> $L/queue.log; }
C=runs/freeze_runs/configs
( for f in 0 1 2 3 4; do run $C/fb8_timing_samsung_B_f${f}_m32.json; done ) &
( for f in 0 1 2 3 4; do run $C/fb8_timing_samsung_B_f${f}_m8.json; done; run $C/fb10_smoke_isu_B0.json; run $C/fb10_smoke_snl_B0.json ) &
( run $C/fb9_nc1_full_synth_m8.json; run $C/fb9_nc1_full_synth_m16.json; run $C/fb9_nc1_full_synth_m32.json; suite ) &
wait; echo "$(date '+%F %T') ALL DONE" >> $L/queue.log
