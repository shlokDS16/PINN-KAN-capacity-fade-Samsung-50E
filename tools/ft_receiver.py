"""Localhost-only receiver: a browser page POSTs article text here and it is saved in refs/fulltext/.

Used because Chrome blocks repeated automatic downloads from one site. Binds 127.0.0.1 only.
Run: .venv/Scripts/python.exe -P tools/ft_receiver.py   (stop with Ctrl+C or by killing the process)
"""
import os, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "refs", "fulltext")
ALLOWED = ("https://www.sciencedirect.com", "https://pubs.acs.org", "https://iopscience.iop.org",
           "https://www.mdpi.com", "https://ieeexplore.ieee.org")


class H(BaseHTTPRequestHandler):
    def _cors(self):
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.headers.get("Origin", "") not in ALLOWED:
            self.send_response(403)
            self.end_headers()
            return
        name = parse_qs(urlparse(self.path).query).get("name", ["unnamed.txt"])[0]
        name = re.sub(r"[^A-Za-z0-9_.-]", "_", os.path.basename(name))[:120]
        if not name.endswith((".txt", ".pdf")):
            name += ".txt"
        n = int(self.headers.get("Content-Length", "0"))
        if n > 60_000_000:
            self.send_response(413)
            self.end_headers()
            return
        data = self.rfile.read(n)
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(data)
        self.send_response(200)
        self._cors()
        self.end_headers()
        self.wfile.write(f"saved {name} {len(data)}".encode())

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    ThreadingHTTPServer(("127.0.0.1", 8765), H).serve_forever()
