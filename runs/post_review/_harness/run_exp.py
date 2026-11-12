"""python -P run_exp.py <exp> [workers=16] [--only variant1,variant2]   (POST-HOC EXPLORATORY, D048)
Runs every (variant, fold, m) job of the experiment in a process pool (1 thread each); jobs with a condition_scores.json are skipped (resumable)."""
import multiprocessing as mp
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def work(task):
    exp, variant, f, m = task
    import harness as H
    import experiments as E
    t0 = time.time()
    try:
        if H.is_done(exp, variant, f, m):
            return task, "skip", 0.0
        kw = E.build(exp, variant, f, m)
        if kw is None:
            return task, "same_as_reference", 0.0
        if "custom" in kw:
            kw["custom"](exp, variant, f, m)
        else:
            H.run_job(exp, variant, f, m, **kw)
        return task, "ok", time.time() - t0
    except Exception as e:  # noqa: BLE001  (a failed job stays on disk and is listed)
        jd = H.job_dir(exp, variant, f, m)
        os.makedirs(jd, exist_ok=True)
        with open(os.path.join(jd, "FAILED.txt"), "w", encoding="utf8") as fh:
            fh.write(traceback.format_exc())
        return task, f"FAILED {type(e).__name__}: {e}", time.time() - t0


if __name__ == "__main__":
    exp = sys.argv[1]
    nw = int(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else 16
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    import experiments as E
    import harness as H
    tasks = [(exp, v, f, m) for m in (32, 8) for v in E.variants(exp) if (only is None or v in only) for f in range(5)]
    print(f"{exp}: {len(tasks)} jobs, {nw} workers", flush=True)
    ctx = mp.get_context("spawn")
    t0 = time.time()
    res = []
    with ctx.Pool(nw) as pool:
        for task, st, secs in pool.imap_unordered(work, tasks, chunksize=1):
            res.append((task, st, secs))
            print(f"[{time.time() - t0:7.0f}s] {task[1]} f{task[2]} m{task[3]}: {st} ({secs:.0f} s)", flush=True)
    H.shas_for(os.path.join(H.OUT, exp))
    bad = [r for r in res if r[1].startswith("FAILED")]
    print(f"done {len(res)} jobs in {time.time() - t0:.0f} s; failed {len(bad)}", flush=True)

