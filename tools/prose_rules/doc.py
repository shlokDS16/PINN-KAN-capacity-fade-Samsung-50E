"""Document container and helpers shared by all checkers."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .extract import Extraction, LineIndex, MappedText, Segment
from .flag import Flag


@dataclass
class Doc:
    path: str
    raw: str
    index: LineIndex
    ex: Extraction
    manuscript: bool = True
    flags: List[Flag] = field(default_factory=list)
    sentences: dict = field(default_factory=dict)  # id(segment) -> list[(start, end)] in segment text


def snippet(t: str, a: int, b: int, width: int = 120) -> str:
    """Flagged span marked with guillemets, with a little context, at most `width` characters."""
    a = max(0, min(a, len(t)))
    b = max(a, min(b, len(t)))
    span = t[a:b].replace("\n", " ")
    truncated = len(span) > 60
    if truncated:
        span = span[:57] + "..."
    room = max(0, width - len(span) - 4)
    left_n = min(a, room // 2)
    right_n = 0 if truncated else min(len(t) - b, room - left_n)
    left = t[a - left_n : a].replace("\n", " ")
    right = t[b : b + right_n].replace("\n", " ")
    pre = ("..." if a - left_n > 0 else "") + left
    post = right + ("..." if (b + right_n < len(t) and not truncated) else "")
    out = f"{pre}«{span}»{post}"
    out = re.sub(r"\s+", " ", out)
    return out if len(out) <= width + 6 else out[: width + 3] + "..."


def make_flag(
    doc: Doc,
    mt: MappedText,
    a: int,
    b: int,
    category: str,
    rule: str,
    message: str,
    suggestion: str,
    severity: str,
    source: str,
    **extra,
) -> Flag:
    start, end = mt.orig_span(a, b)
    line, col = doc.index.locate(start)
    return Flag(
        doc.path, line, col, start, end, category, rule, message, suggestion,
        snippet(mt.t, a, b), severity, source, doc.manuscript, dict(extra),
    )


def in_quotes(t: str, pos: int) -> bool:
    """True when `pos` sits between a pair of quotation marks inside this segment."""
    before = t[:pos]
    if before.count('"') % 2 == 1:
        return True
    return before.rfind("“") > before.rfind("”")
