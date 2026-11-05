"""Download the full Samsung INR21700-50E release (figshare 25975315) with resume and MD5 checks.

Two stages reuse serial names (TP_k03_01.zip exists twice), so every file is saved as
<stem>__f<figshare file id>.zip in data/raw/samsung50e_full/. Resumes from the bytes on disk
(curl -C -). Stop: create data/STOP_SAMSUNG_FULL. Log: data/logs/samsung_full.log.
"""
import concurrent.futures as cf
import csv, datetime as dt, hashlib, os, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "raw", "samsung50e_full")
LOG = os.path.join(DATA, "logs", "samsung_full.log")
STOP = os.path.join(DATA, "STOP_SAMSUNG_FULL")
UA = "Mozilla/5.0 (research data download; resumable)"
WORKERS = 16


def log(msg):
    with open(LOG, "a", encoding="utf8") as f:
        f.write(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")


def rows():
    with open(os.path.join(DATA, "DEFERRED_URLS.tsv"), encoding="utf8") as f:
        out = [r for r in csv.DictReader(f, delimiter="\t") if r["dataset"].startswith("samsung50e")]
    for r in out:
        fid = r["url"].rstrip("/").split("/")[-1]
        stem, ext = os.path.splitext(r["file"])
        r["target"] = os.path.join(OUT, f"{stem}__f{fid}{ext}")
    return sorted(out, key=lambda r: int(r["bytes"] or 0))


def md5_ok(path, spec):
    algo, want = spec.split(":", 1)
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest() == want


def fetch(r):
    p, part, size = r["target"], r["target"] + ".part", int(r["bytes"] or 0)
    for attempt in range(1, 40):
        if os.path.exists(STOP):
            return "stopped"
        have = os.path.getsize(part) if os.path.exists(part) else 0
        if size and have > size:
            os.remove(part)
            have = 0
        if not (size and have >= size):
            rc = subprocess.run(["curl", "-f", "-L", "-sS", "-A", UA, "-C", "-", "--connect-timeout", "30",
                                 "--speed-limit", "2000", "--speed-time", "120", "-o", part, r["url"]],
                                capture_output=True, text=True).returncode
            if rc == 33 and os.path.exists(part):
                os.remove(part)
                continue
        have = os.path.getsize(part) if os.path.exists(part) else 0
        if size and have >= size:
            if md5_ok(part, r["checksum"]):
                os.replace(part, p)
                return "ok"
            log(f"md5 mismatch {os.path.basename(p)} (attempt {attempt}); restarting file")
            os.remove(part)
        time.sleep(min(10 * attempt, 300))
    return "failed"


def main():
    os.makedirs(OUT, exist_ok=True)
    todo = [r for r in rows() if not os.path.exists(r["target"])]
    log(f"start: {len(todo)} files to fetch")
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        for r, res in zip(todo, ex.map(fetch, todo)):
            log(f"{res} {os.path.basename(r['target'])} {int(r['bytes'] or 0)/1e6:.1f} MB")
    left = [r for r in rows() if not os.path.exists(r["target"])]
    log(f"finished: {len(left)} files missing")
    if not left:
        open(os.path.join(DATA, "logs", "samsung_full.DONE"), "w").close()


if __name__ == "__main__":
    main()
