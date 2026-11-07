"""Local similarity check: verbatim word runs shared with the reference texts held in refs/.

This is not a plagiarism service. It compares the draft only with the full texts of the cited
papers that are already on disk, which is where an accidental near-copy is most likely.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

from .doc import Doc, make_flag
from .flag import Flag

TOK = re.compile(r"[A-Za-z0-9]+")
SHINGLE = 6


def _tokens(text: str) -> List[Tuple[str, int, int]]:
    return [(m.group(0).lower(), m.start(), m.end()) for m in TOK.finditer(text)]


def build_index(dirs: List[Path]) -> Tuple[Dict[Tuple[str, ...], List[Tuple[int, int]]], List[Tuple[str, List[str]]]]:
    sources: List[Tuple[str, List[str]]] = []
    for d in dirs:
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            if p.suffix.lower() in (".txt", ".md") and p.is_file() and p.stat().st_size < 3_000_000:
                try:
                    txt = p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                sources.append((p.name, [t for t, _, _ in _tokens(txt)]))
    idx: Dict[Tuple[str, ...], List[Tuple[int, int]]] = {}
    for si, (_, toks) in enumerate(sources):
        for i in range(len(toks) - SHINGLE + 1):
            idx.setdefault(tuple(toks[i : i + SHINGLE]), []).append((si, i))
    return idx, sources


def run(docs: List[Doc], dirs: List[Path], min_words: int = 10) -> Tuple[List[Flag], dict]:
    idx, sources = build_index(dirs)
    info = {"sources": len(sources), "min_words": min_words}
    flags: List[Flag] = []
    if not sources:
        info["ran"] = False
        return flags, info
    info["ran"] = True
    for d in docs:
        for seg in d.ex.segments:
            if seg.lint != "full":
                continue
            toks = _tokens(seg.mt.t)
            words = [t for t, _, _ in toks]
            i = 0
            while i <= len(words) - SHINGLE:
                hits = idx.get(tuple(words[i : i + SHINGLE]))
                if not hits:
                    i += 1
                    continue
                best = (0, "")  # run length, source
                for si, pos in hits:
                    src = sources[si][1]
                    n = SHINGLE
                    while i + n < len(words) and pos + n < len(src) and words[i + n] == src[pos + n]:
                        n += 1
                    if n > best[0]:
                        best = (n, sources[si][0])
                n, name = best
                if n >= min_words:
                    a, b = toks[i][1], toks[i + n - 1][2]
                    sev = "high" if n >= 15 else "medium"
                    flags.append(
                        make_flag(d, seg.mt, a, b, "Paraphrase needed", "verbatim-run",
                                  f"{n} consecutive words match '{name}' word for word.",
                                  "Paraphrase in your own structure, or put it in quotation marks with a citation.",
                                  sev, "similarity", source_file=name)
                    )
                    i += n
                else:
                    i += 1
    return flags, info
