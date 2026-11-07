#!/bin/bash
# Freeze-commit repeat at the candidate commit: FB-8/FB-9/FB-10 and the suite (run_queue.sh), then FB-8b and the head comparison.
# CPU only, at most 3 single-thread processes at a time.
cd "/c/Users/Shlok/Downloads/PINN KAN battery paper"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=""
bash runs/freeze_runs/run_queue.sh </dev/null
L=runs/freeze_runs/logs; mkdir -p runs/freeze_runs/fb8b
echo "$(date '+%F %T') FB-8b start HEAD $(git rev-parse HEAD)" >> $L/queue.log
( .venv/Scripts/python.exe -P runs/freeze_runs/fb8b_convergence.py 0 1 </dev/null > runs/freeze_runs/fb8b/lane1.out 2>&1 ) &
( .venv/Scripts/python.exe -P runs/freeze_runs/fb8b_convergence.py 2 3 </dev/null > runs/freeze_runs/fb8b/lane2.out 2>&1 ) &
( .venv/Scripts/python.exe -P runs/freeze_runs/fb8b_convergence.py 4 </dev/null > runs/freeze_runs/fb8b/lane3.out 2>&1 ) &
wait
echo "$(date '+%F %T') FB-8b done" >> $L/queue.log
.venv/Scripts/python.exe -P code/tests/head_comparison.py --base 052eefd </dev/null > runs/freeze_runs/head_comparison.out 2>&1
echo "$(date '+%F %T') head_comparison rc=$? ; EVERYTHING DONE" >> $L/queue.log
