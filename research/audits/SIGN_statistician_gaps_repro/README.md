# Reproduction of the statistician's no-regression and recomputation check (SIGN_statistician_gaps.md, item 7)

Synthetic data only (the coder's test grid, invented numbers). CPU, one thread. W = an empty scratch directory.

    export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 PINNKAN_ROOT="<project root>"
    mkdir -p HEAD && git archive 052eefd code | tar -x -C HEAD
    PY=.venv/Scripts/python.exe
    $PY -P gen_grid.py W
    $PY -P run_one.py HEAD/code W an_head head      # code at 052eefd
    $PY -P run_one.py code W an_new new             # working tree, gaps on, NC-2 runs given
    $PY -P run_one.py code W an_off off             # working tree, gaps=False
    $PY -P compare.py W

compare.py strips exactly the coder's registry of new keys and recomputes NC-2, PC-3 (scipy betabinom, a = b = 16.17)
and the G1 pooled mean / seed SD from the raw synthetic files.
