"""Read members of a remote ZIP without downloading the whole archive (HTTP range requests).

Usage:
  python -I tools/zip_range_fetch.py list  <url> <out.tsv>
  python -I tools/zip_range_fetch.py fetch <url> <outdir> <member> [<member> ...]
Reads go through a seekable file object that issues one Range request per read, with retries, so
zipfile only downloads the central directory and the members asked for. Members are written to
<outdir>/<basename>.part and renamed when complete; an existing complete file is skipped.
"""
import io, os, sys, time, urllib.request, zipfile

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def resolve(url):
    # presigned storage URLs often refuse HEAD, so ask for one byte and read Content-Range
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Range": "bytes=0-0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.geturl(), int(r.headers["Content-Range"].rsplit("/", 1)[1])


class HttpRangeFile(io.RawIOBase):
    def __init__(self, url):
        self.src = url
        self.url, self.size = resolve(url)
        self.pos = 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def readinto(self, b):
        n = min(len(b), self.size - self.pos)
        if n <= 0:
            return 0
        data = self._get(self.pos, self.pos + n - 1)
        b[: len(data)] = data
        self.pos += len(data)
        return len(data)

    def _get(self, a, z):
        wait = 15
        while True:
            try:
                req = urllib.request.Request(self.url, headers={"User-Agent": UA, "Range": f"bytes={a}-{z}"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    return r.read()
            except Exception as e:  # presigned redirect may expire: re-resolve, then retry
                print(f"retry after {type(e).__name__}: {e}", file=sys.stderr)
                time.sleep(wait)
                wait = min(wait * 2, 600)
                try:
                    self.url, _ = resolve(self.src)
                except Exception:
                    pass


def main():
    mode, url = sys.argv[1], sys.argv[2]
    zf = zipfile.ZipFile(io.BufferedReader(HttpRangeFile(url), buffer_size=1 << 16))
    if mode == "list":
        with open(sys.argv[3], "w", encoding="utf8") as f:
            f.write("member\tcompressed\tuncompressed\n")
            for i in zf.infolist():
                f.write(f"{i.filename}\t{i.compress_size}\t{i.file_size}\n")
        print(len(zf.infolist()), "members listed")
        return
    outdir = sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    for m in sys.argv[4:]:
        dst = os.path.join(outdir, os.path.basename(m))
        if os.path.exists(dst):
            print("have", m)
            continue
        with zf.open(m) as src, open(dst + ".part", "wb") as out:
            while chunk := src.read(1 << 20):
                out.write(chunk)
        os.replace(dst + ".part", dst)
        print("fetched", m, os.path.getsize(dst))


if __name__ == "__main__":
    main()
