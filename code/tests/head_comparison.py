"""Re-runnable no-regression comparison of the statistics step against an earlier commit (STATS_GAPS_REPORT.md; statistician item 7, F6).

    .venv/Scripts/python.exe -P code/tests/head_comparison.py [--base 052eefd]

Exports `git archive <base> code` to a scratch directory, builds the synthetic complete grid of test_pk_stats_gaps_g1_g8.py (invented numbers), runs `run_stats_v4` of the BASE code and of the
working tree on it (same grid, same item (f) file, CPU, one thread), and compares contrasts_v4_B.json, controls.json and physval_11a.json after removing exactly the registered new keys
(`strip_*` of the test module). Prints IDENTICAL / DIFFERENT per file and exits 1 on any difference. Not a pytest file (the suite loop does not run it); run it, together with the whole suite, at
the candidate frozen commit."""
import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("OMP_NUM_THREADS", "1")


def worker(mode, root, tmp):
    sys.path.insert(0, os.path.join(root, "code"))
    from pinnkan import stats_step as ss
    dirs = json.load(open(os.path.join(tmp, "dirs.json")))
    fdir, sha = json.load(open(os.path.join(tmp, "f.json")))
    kw = dict(item_f_dir=fdir, item_f_sha256=sha, physval=True)
    if mode == "new":
        ss.run_stats_v4(os.path.join(tmp, "an_new"), dirs, negative_runs=json.load(open(os.path.join(tmp, "neg.json"))), **kw)
    else:
        ss.run_stats_v4(os.path.join(tmp, "an_old"), dirs, **kw)
    print(mode, "used", ss.__file__)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="052eefd")
    ap.add_argument("--worker", nargs=3, metavar=("MODE", "ROOT", "TMP"))
    a = ap.parse_args()
    if a.worker:
        return worker(*a.worker)
    sys.path.insert(0, os.path.join(ROOT, "code"))
    sys.path.insert(0, HERE)
    import test_pk_stats_gaps_g1_g8 as T
    tmp = tempfile.mkdtemp(prefix="head_cmp_")
    old = os.path.join(tmp, "old")
    os.makedirs(old)
    arch = subprocess.run(["git", "archive", a.base, "code"], cwd=ROOT, capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", old], input=arch.stdout, check=True)
    os.makedirs(os.path.join(tmp, "g"))
    dirs = T.make_grid(os.path.join(tmp, "g"))
    f, sha = T._item_f(tmp, dirs)
    neg = T.make_negative(tmp, dirs)
    for n, v in (("dirs", dirs), ("f", [f, sha]), ("neg", neg)):
        json.dump(v, open(os.path.join(tmp, n + ".json"), "w"))
    me = os.path.abspath(__file__)
    subprocess.run([sys.executable, "-P", me, "--worker", "old", old, tmp], cwd=old, check=True)
    subprocess.run([sys.executable, "-P", me, "--worker", "new", ROOT, tmp], cwd=ROOT, check=True)
    bad = 0
    for name, strip in (("contrasts_v4_B.json", T.strip_contrasts), ("controls.json", T.strip_controls), ("physval_11a.json", T.strip_physval)):
        a_ = json.load(open(os.path.join(tmp, "an_old", name)))
        b_ = json.load(open(os.path.join(tmp, "an_new", name)))
        same = T._canon(a_) == T._canon(strip(b_))
        bad += not same
        print(f"{name}: {'IDENTICAL' if same else 'DIFFERENT'} ({len(T._canon(a_))} characters, base {a.base})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
