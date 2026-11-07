"""Vale (official binary) with the proselint, write-good and Microsoft packages."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List

from .doc import Doc, in_quotes, make_flag
from .extract import MappedText, lint_text
from .flag import Flag

CAT = [
    (r"Wordiness|TooWordy|Needless|Airlinese|CorporateSpeak|RASSyndrome", "Wordiness", None),
    (r"Hedging|Weasel|Adverbs|Very|Hyperbole|Uncomparables|But$", "Weak or hedged wording", None),
    (r"Illusions", "Grammar", "high"),
    (r"ThereIs|So$|Jargon", "Clarity", None),
    (r"Dashes|Ellipses|Spacing|Typography|ExclamationPoints|Suspended", "Typography", None),
    (r"Contractions", "Style", None),
    (r"P-Value|Nonwords|Malapropisms|Spelling|Skunked|Archaisms", "Style", "medium"),
]
SEV = {"error": "medium", "warning": "low", "suggestion": "low"}


def categorize(check: str):
    for pat, cat, sev in CAT:
        if re.search(pat, check):
            return cat, sev
    return "Style", None


def styles_hash(styles: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(styles.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(styles)).replace("\\", "/").encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def version_info(vale_exe: Path, ini: Path) -> dict:
    info = {}
    try:
        info["version"] = subprocess.run([str(vale_exe), "--version"], capture_output=True, text=True, timeout=30).stdout.strip()
        info["sha256"] = hashlib.sha256(vale_exe.read_bytes()).hexdigest()
        info["styles_sha256"] = styles_hash(ini.parent / "styles")
        info["config"] = str(ini)
    except Exception as exc:
        info["error"] = str(exc)
    return info


def run(docs: List[Doc], vale_exe: Path, ini: Path, joined_by_doc: Dict[int, MappedText], ignore_text: dict = None) -> (List[Flag], dict):
    info = version_info(vale_exe, ini)
    flags: List[Flag] = []
    if not vale_exe.exists() or "error" in info:
        info["ran"] = False
        info.setdefault("error", f"Vale binary not found at {vale_exe}")
        return flags, info
    with tempfile.TemporaryDirectory(prefix="prose_vale_") as tmp:
        files = {}
        for di, d in enumerate(docs):
            joined = joined_by_doc.get(di)
            if joined is None:
                joined, _ = lint_text(d.ex.segments)
                joined_by_doc[di] = joined
            p = Path(tmp) / f"doc{di:02d}.txt"
            p.write_text(joined.t, encoding="utf-8", newline="\n")
            files[str(p)] = di
        cmd = [str(vale_exe), f"--config={ini}", "--output=JSON", *files.keys()]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=600)
        out = proc.stdout.strip()
        if not out:
            info["ran"] = proc.returncode in (0, 1)
            info["error"] = proc.stderr.strip()[:400] if proc.stderr else ""
            return flags, info
        data = json.loads(out)
    info["ran"] = True
    ignore_rx = {k: re.compile(v, re.I) for k, v in (ignore_text or {}).items()}
    skip_in_quotes = re.compile(r"Very|Weasel|Adverbs|Hyperbole|Hedging|Cliches")
    for path, alerts in data.items():
        di = files.get(path)
        if di is None:  # Vale may normalise the path; match by file name
            di = next((v for k, v in files.items() if os.path.basename(k) == os.path.basename(path)), None)
        if di is None:
            continue
        d, joined = docs[di], joined_by_doc[di]
        line_starts = [0]
        for i, ch in enumerate(joined.t):
            if ch == "\n":
                line_starts.append(i + 1)
        for al in alerts:
            ln = al["Line"] - 1
            if ln >= len(line_starts):
                continue
            a = line_starts[ln] + al["Span"][0] - 1
            b = line_starts[ln] + al["Span"][1]
            match = al.get("Match", "")
            if joined.t[a:b] != match:
                k = joined.t.find(match, line_starts[ln])
                if k < 0:
                    continue
                a, b = k, k + len(match)
            if skip_in_quotes.search(al["Check"]) and in_quotes(joined.t, a):
                continue
            if match.strip() in ("X", "Author"):
                continue
            if al["Check"] in ignore_rx and ignore_rx[al["Check"]].search(match.strip()):
                continue
            cat, sev_override = categorize(al["Check"])
            sev = sev_override or SEV.get(al["Severity"], "low")
            sug = ""
            if al.get("Action", {}).get("Name") == "replace" and al["Action"].get("Params"):
                sug = "Try: " + ", ".join(f"'{p}'" for p in al["Action"]["Params"][:3])
            f = make_flag(d, joined, a, b, cat, al["Check"], al["Message"], sug, sev, "vale")
            flags.append(f)
    return flags, info
