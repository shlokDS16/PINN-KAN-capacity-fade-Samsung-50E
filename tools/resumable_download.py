"""Resumable download manager for flaky networks.

Reads data/DEFERRED_URLS.tsv (dataset, file, bytes, checksum, url), downloads one file at a time
with curl, resuming from the bytes already on disk (curl -C -). On any failure it waits (with
backoff) until the network answers again and resumes. Verifies size and checksum, then renames
<file>.part to <file>. Writes data/DOWNLOAD_STATUS.md and data/logs/downloader.log after every step.
Quiet window 00:05-00:30 (network switch): no traffic. Files listed in SKIP are left for a decision.
Stop it by creating data/STOP_DOWNLOADS.
"""
import csv, hashlib, os, subprocess, sys, time, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
QUEUE = os.path.join(DATA, "DEFERRED_URLS.tsv")
STATUS = os.path.join(DATA, "DOWNLOAD_STATUS.md")
LOG = os.path.join(DATA, "logs", "downloader.log")
STOP = os.path.join(DATA, "STOP_DOWNLOADS")
# Tonight's whitelist (about 6 GB, D004): everything else in the queue waits for a dataset decision.
ALLOW = ["isu_ilcc", "tju", "hust", "xjtu"]
SKIP = {"Cycling_json.zip", "RPT_json.zip"}  # 10 GB and 0.9 GB: need a decision first
PRIORITY = ["isu_ilcc", "tju", "hust", "xjtu"]  # first match wins
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def nbytes(r):
    try:
        return int(r.get("bytes") or 0)
    except ValueError:
        return 0  # unknown size: completion is judged by curl's exit code


def log(msg):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    with open(LOG, "a", encoding="utf8") as f:
        f.write(line + "\n")


def quiet_window():
    now = dt.datetime.now().time()
    return dt.time(0, 5) <= now <= dt.time(0, 30)


def online():
    r = subprocess.run(["curl", "-s", "-o", os.devnull, "-m", "15", "-w", "%{http_code}",
                        "https://zenodo.org"], capture_output=True, text=True)
    return r.stdout.strip() not in ("", "000")


def digest(path, spec):
    algo, want = spec.split(":", 1)
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest() == want.lower()


def read_list(name, default):
    """One entry per line in data/<name>; re-read every loop so it can change while running."""
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf8") as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def load_queue():
    global ALLOW, PRIORITY, SKIP
    ALLOW = PRIORITY = read_list("DOWNLOAD_ALLOW.txt", ALLOW)  # file order = priority order
    SKIP = set(read_list("DOWNLOAD_SKIP.txt", sorted(SKIP)))
    with open(QUEUE, encoding="utf8") as f:
        rows = [r for r in csv.DictReader(f, delimiter="\t") if r.get("url")
                and any(r["dataset"].startswith(a) for a in ALLOW)]
    rank = lambda r: next((i for i, p in enumerate(PRIORITY) if r["dataset"].startswith(p)), 99)
    return sorted(rows, key=lambda r: (rank(r), nbytes(r)))


def target(r):
    d = os.path.join(DATA, "raw", r["dataset"])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, r["file"])


def write_status(rows, current=None, note=""):
    lines = [f"# Download status (updated {dt.datetime.now():%Y-%m-%d %H:%M:%S})", "",
             "Resumes from the bytes on disk after every drop. Stop: create data/STOP_DOWNLOADS.", "",
             f"{note}", "", "| dataset | file | size MB | done MB | % | state |", "|---|---|---|---|---|---|"]
    for r in rows:
        p = target(r)
        size = nbytes(r)
        if r["file"] in SKIP:
            state, have = "skipped (needs decision)", 0
        elif os.path.exists(p):
            state, have = "verified", size
        else:
            have = os.path.getsize(p + ".part") if os.path.exists(p + ".part") else 0
            state = "downloading" if r is current else ("partial" if have else "queued")
            if os.path.exists(p + ".bad"):
                state += " (checksum failed earlier)"
        pct = 100 * have / size if size else 0
        lines.append(f"| {r['dataset']} | {r['file']} | {size/1e6:.1f} | {have/1e6:.1f} | {pct:.0f} | {state} |")
    tmp = STATUS + ".tmp"
    try:  # a reader holding the file must never stop the download
        with open(tmp, "w", encoding="utf8") as f:
            f.write("\n".join(lines) + "\n")
        os.replace(tmp, STATUS)
    except OSError:
        pass


def fetch(r, rows):
    p, part, size = target(r), target(r) + ".part", nbytes(r)
    wait, failures = 30, 0
    while True:
        if os.path.exists(STOP):
            return False
        while quiet_window():
            write_status(rows, r, "Paused for the 00:05-00:30 network switch.")
            time.sleep(60)
        if not online():
            write_status(rows, r, f"Network down; retrying in {wait}s.")
            log(f"offline; wait {wait}s ({r['file']})")
            time.sleep(wait)
            wait = min(wait * 2, 600)
            continue
        wait = 30
        have = os.path.getsize(part) if os.path.exists(part) else 0
        if size and have > size:
            log(f"{r['file']}: part larger than expected, restarting")
            os.remove(part)
            have = 0
        write_status(rows, r, f"Downloading {r['file']} from {have/1e6:.1f} MB.")
        log(f"start {r['file']} at {have} of {size}")
        cmd = ["curl", "-L", "-sS", "-A", UA, "-C", "-", "--connect-timeout", "30",
               "--speed-limit", "500", "--speed-time", "180", "-o", part, r["url"]]
        rate = read_list("DOWNLOAD_RATE.txt", [])  # e.g. "30k": leaves bandwidth for the agents
        if rate:
            cmd[1:1] = ["--limit-rate", rate[0]]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        while proc.poll() is None:  # refresh the status file while curl runs
            time.sleep(30)
            now = os.path.getsize(part) if os.path.exists(part) else 0
            write_status(rows, r, f"Downloading {r['file']}: {now/1e6:.1f} of {size/1e6:.1f} MB.")
        rc = subprocess.CompletedProcess(cmd, proc.returncode, "", proc.stderr.read() if proc.stderr else "")
        have = os.path.getsize(part) if os.path.exists(part) else 0
        log(f"curl rc={rc.returncode} {r['file']} now {have} {rc.stderr.strip()[:200]}")
        if rc.returncode == 33:  # server refused range: start over once
            os.remove(part)
            continue
        complete = (size and have >= size) or (not size and rc.returncode == 0 and have > 0)
        if complete:
            if not r.get("checksum") or digest(part, r["checksum"]):
                for _ in range(10):  # antivirus or a stray handle can hold the file briefly
                    try:
                        os.replace(part, p)
                        break
                    except PermissionError:
                        time.sleep(10)
                else:
                    raise PermissionError(f"cannot rename {part}")
                log(f"verified {r['file']}")
                return True
            failures += 1
            log(f"checksum mismatch {r['file']} (failure {failures})")
            os.replace(part, p + ".bad") if failures >= 2 else os.remove(part)
            if failures >= 2:
                return False
            continue
        time.sleep(15)  # partial: resume after a short pause


def main():
    log("downloader started")
    while True:
        rows = load_queue()  # re-read so new rows added by agents are picked up
        todo = [r for r in rows if r["file"] not in SKIP and not os.path.exists(target(r))
                and not os.path.exists(target(r) + ".bad")]
        if not todo or os.path.exists(STOP):
            write_status(rows, None, "All queued files verified." if not todo else "Stopped by STOP_DOWNLOADS.")
            log("downloader finished")
            open(os.path.join(DATA, "logs", "downloader.DONE"), "w").close()
            return
        try:
            fetch(todo[0], rows)
        except Exception as e:  # never die on a transient error; the outer loop also restarts us
            log(f"error {type(e).__name__}: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
