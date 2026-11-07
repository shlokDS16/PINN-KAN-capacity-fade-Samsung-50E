"""Strip Markdown / LaTeX markup from a manuscript and keep a character map back to the source.

The checkers see only prose. Every character of the cleaned text carries the start and end
offset of the source span it came from, so any flag maps back to file:line:column.
Math becomes the token "X", code spans "X", citations "[1]", author placeholders "X".
"""
from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple


class MappedText:
    """A string plus, for every character, the source span [m, e) it came from."""

    __slots__ = ("t", "m", "e")

    def __init__(self, t: str, m: Optional[List[int]] = None, e: Optional[List[int]] = None):
        self.t = t
        self.m = m if m is not None else list(range(len(t)))
        self.e = e if e is not None else [x + 1 for x in self.m]

    def __len__(self) -> int:
        return len(self.t)

    def slice(self, a: int, b: int) -> "MappedText":
        return MappedText(self.t[a:b], self.m[a:b], self.e[a:b])

    def orig_span(self, a: int, b: int) -> Tuple[int, int]:
        if not self.t:
            return (0, 0)
        a = max(0, min(a, len(self.t) - 1))
        b = max(a + 1, min(b, len(self.t)))
        return (self.m[a], self.e[b - 1])

    def replace_spans(self, spans: List[Tuple[int, int, str]]) -> "MappedText":
        """spans: sorted, non-overlapping (start, end, replacement) in current coordinates."""
        t: List[str] = []
        m: List[int] = []
        e: List[int] = []
        pos = 0
        for s, en, r in spans:
            t.append(self.t[pos:s])
            m.extend(self.m[pos:s])
            e.extend(self.e[pos:s])
            if r == self.t[s:en]:
                t.append(r)
                m.extend(self.m[s:en])
                e.extend(self.e[s:en])
            elif r:
                src_s, src_e = self.m[s], self.e[en - 1]
                k = self.t[s:en].find(r)
                if k >= 0:  # replacement is a verbatim part of the match: keep exact mapping
                    t.append(r)
                    m.extend(self.m[s + k : s + k + len(r)])
                    e.extend(self.e[s + k : s + k + len(r)])
                else:
                    t.append(r)
                    m.extend([src_s] * len(r))
                    e.extend([src_e] * len(r))
            pos = en
        t.append(self.t[pos:])
        m.extend(self.m[pos:])
        e.extend(self.e[pos:])
        return MappedText("".join(t), m, e)

    def sub(self, rx, repl) -> "MappedText":
        rx = re.compile(rx) if isinstance(rx, str) else rx
        spans = []
        for mt in rx.finditer(self.t):
            r = repl(mt) if callable(repl) else mt.expand(repl)
            spans.append((mt.start(), mt.end(), r))
        return self.replace_spans(spans) if spans else self

    def lines(self) -> List["MappedText"]:
        out, pos = [], 0
        for part in self.t.split("\n"):
            out.append(self.slice(pos, pos + len(part)))
            pos += len(part) + 1
        return out


@dataclass
class Segment:
    kind: str  # para | list | heading | table | quote | math
    mt: MappedText
    lint: str  # full | light | none
    first_line: int = 0


@dataclass
class Extraction:
    segments: List[Segment] = field(default_factory=list)
    placeholders: List[Tuple[int, int, str]] = field(default_factory=list)  # source spans
    double_spaces: List[Tuple[int, int]] = field(default_factory=list)  # source spans of 2+ spaces


class LineIndex:
    def __init__(self, text: str):
        self.starts = [0]
        for i, ch in enumerate(text):
            if ch == "\n":
                self.starts.append(i + 1)
        self.n = len(text)

    def locate(self, offset: int) -> Tuple[int, int]:
        offset = max(0, min(offset, self.n))
        i = bisect.bisect_right(self.starts, offset) - 1
        return i + 1, offset - self.starts[i] + 1


# ---------------------------------------------------------------------------------------
# Markdown

PH_OPEN = re.compile(r"\[(?=[A-Z][A-Z0-9 _/\-]{2,}:)")
CITE = re.compile(r"\[(?:[^\[\]]*?)(?<![\w])-?@[A-Za-z0-9_][\w:.#$%&+?<>~/\-]*[^\[\]]*\]")
INLINE_MATH = re.compile(r"(?<![\\$\w])\$(?![\s$])((?:\\\$|[^$])*?)(?<![\s\\])\$(?!\d)")
DISPLAY_MATH = re.compile(r"\$\$.+?\$\$", re.S)
LATEX_ENV = re.compile(
    r"\\begin\{(equation|align|gather|multline|eqnarray|displaymath)\*?\}.*?\\end\{\1\*?\}", re.S
)
LATEX_BRACKET = re.compile(r"\\\[.+?\\\]", re.S)
FENCE = re.compile(r"^[ \t]*(```|~~~)[^\n]*\n.*?^[ \t]*\1[^\n]*$", re.S | re.M)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
CODE_SPAN = re.compile(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.S)
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?")
LINK = re.compile(r"\[([^\[\]]+)\]\((?:[^()]|\([^()]*\))*\)")
AUTOLINK = re.compile(r"<(?:https?|ftp)://[^>\s]+>|(?<![\w(])https?://[^\s)\]>]+")
FOOTNOTE_REF = re.compile(r"\[\^[^\]]+\]")
HTML_TAG = re.compile(r"</?[A-Za-z][^>\n]*>")
ATTRS = re.compile(r"\{[#.][^}\n]*\}")
ENTITY = {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"'}
ENTITY_RX = re.compile("|".join(map(re.escape, ENTITY)))
ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!$%&|~<>^])")
BOLD = re.compile(r"(\*\*|__)(?=\S)((?:(?!\n\n).)+?)(?<=\S)\1", re.S)
STRIKE = re.compile(r"~~(?=\S)((?:(?!\n\n).)+?)(?<=\S)~~", re.S)
ITALIC_STAR = re.compile(r"(?<![\w*\\])\*(?![\s*])((?:(?!\n\n).)+?)(?<![\s*\\])\*(?![\w*])", re.S)
ITALIC_UND = re.compile(r"(?<![\w\\])_(?![\s_])((?:(?!\n\n).)+?)(?<![\s_\\])_(?![\w])", re.S)
HEADING = re.compile(r"^(\s{0,3})(#{1,6})\s+(.*?)(\s+#+\s*)?$")
LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d{1,3}[.)])\s+")
HRULE = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
DIV_FENCE = re.compile(r"^\s*:{3,}.*$")


def _find_placeholders(mt: MappedText, record: List[Tuple[int, int, str]]) -> MappedText:
    spans = []
    last_end = -1
    for mt_open in PH_OPEN.finditer(mt.t):
        s = mt_open.start()
        if s < last_end:
            continue
        depth, i, n = 0, s, len(mt.t)
        while i < n:
            ch = mt.t[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        else:
            continue
        end = i + 1
        label = mt.t[s + 1 : mt.t.find(":", s)]
        a, b = mt.orig_span(s, end)
        record.append((a, b, label))
        spans.append((s, end, "X"))
        last_end = end
    return mt.replace_spans(spans) if spans else mt


def _math_repl(mt: re.Match) -> str:
    return mt.group(0) if "\n\n" in mt.group(0) else "X"


def _clean_inline(mt: MappedText, record: List[Tuple[int, int, str]]) -> MappedText:
    mt = mt.sub(HTML_COMMENT, "")
    mt = mt.sub(FENCE, "")
    mt = mt.sub(DISPLAY_MATH, " X ")
    mt = mt.sub(LATEX_ENV, " X ")
    mt = mt.sub(LATEX_BRACKET, " X ")
    mt = mt.sub(CODE_SPAN, "X")
    mt = mt.sub(INLINE_MATH, _math_repl)
    mt = _find_placeholders(mt, record)
    mt = mt.sub(CITE, "[1]")
    mt = mt.sub(r"(?<![\w@\\])@[A-Za-z][\w:.\-]*[\w]", "Author")
    mt = mt.sub(IMAGE, "")
    mt = mt.sub(LINK, lambda m: m.group(1))
    mt = mt.sub(AUTOLINK, "X")
    mt = mt.sub(FOOTNOTE_REF, "")
    mt = mt.sub(HTML_TAG, "")
    mt = mt.sub(ENTITY_RX, lambda m: ENTITY[m.group(0)])
    mt = mt.sub(ATTRS, "")
    mt = mt.sub(ESCAPE, lambda m: m.group(1))
    for rx in (BOLD, STRIKE):
        mt = mt.sub(rx, lambda m: m.group(m.lastindex))
    mt = mt.sub(ITALIC_STAR, lambda m: m.group(1))
    mt = mt.sub(ITALIC_UND, lambda m: m.group(1))
    return mt


def _collapse_spaces(mt: MappedText, ex: Extraction) -> MappedText:
    """Record runs of 2+ spaces that really are in the source, then collapse all runs to one space."""
    for m in re.finditer(r"(?<=\S)( {2,})(?=\S)", mt.t):
        a, b = m.span(1)
        ls = mt.t.rfind("\n", 0, a) + 1
        head = mt.t[ls:a]
        if head.lstrip().startswith("|") or re.fullmatch(r"\s*(?:[-*+]|\d{1,3}[.)])", head):
            continue
        consecutive = all(mt.m[i + 1] == mt.m[i] + 1 for i in range(a - 1, b))
        if consecutive and mt.m[b] == mt.m[b - 1] + 1:
            ex.double_spaces.append((mt.m[a], mt.e[b - 1]))
    return mt.sub(r"(?<=\S) {2,}(?=\S)", " ")


def _join_mapped(parts: List[MappedText], sep: str) -> MappedText:
    t, m, e = [], [], []
    for i, p in enumerate(parts):
        if i and parts[i - 1].t:
            prev = parts[i - 1]
            t.append(sep)
            m.extend([prev.m[-1]] * len(sep))
            e.extend([prev.e[-1]] * len(sep))
        t.append(p.t)
        m.extend(p.m)
        e.extend(p.e)
    return MappedText("".join(t), m, e)


def _merge_math(segs: List[Segment]) -> List[Segment]:
    """A display equation joins the sentence it belongs to, so grammar tools see one sentence."""
    out: List[Segment] = []
    i = 0
    while i < len(segs):
        s = segs[i]
        if s.kind == "math" and out and out[-1].kind == "para":
            prev = out[-1]
            joined = _join_mapped([prev.mt, MappedText("X", [s.mt.m[0]], [s.mt.e[-1]])], " ")
            nxt = segs[i + 1] if i + 1 < len(segs) else None
            if nxt is not None and nxt.kind == "para" and nxt.mt.t[:1].islower():
                joined = _join_mapped([joined, nxt.mt], " ")
                i += 1
            else:
                last = len(joined.t) - 1
                joined = MappedText(joined.t + ".", joined.m + [joined.m[last]], joined.e + [joined.e[last]])
            out[-1] = Segment("para", joined, "full", prev.first_line)
        elif s.kind == "math":
            pass
        else:
            out.append(s)
        i += 1
    return out


def extract_markdown(raw: str, index: LineIndex) -> Extraction:
    ex = Extraction()
    mt = MappedText(raw)
    # YAML front matter
    if raw.startswith("---\n"):
        end = raw.find("\n---", 4)
        if end > 0:
            mt = mt.sub(re.compile(r"\A---\n.*?\n---[^\n]*", re.S), "")
    mt = _clean_inline(mt, ex.placeholders)
    mt = _collapse_spaces(mt, ex)

    segs: List[Segment] = []
    para: List[MappedText] = []
    item: List[MappedText] = []
    quote: List[MappedText] = []

    def first_line_of(x: MappedText) -> int:
        return index.locate(x.m[0])[0] if x.t else 0

    def flush_para():
        nonlocal para
        if para:
            j = _join_mapped(para, "\n")
            kind = "math" if j.t.strip() == "X" else "para"
            segs.append(Segment(kind, j, "none" if kind == "math" else "full", first_line_of(j)))
            para = []

    def flush_item():
        nonlocal item
        if item:
            j = _join_mapped(item, "\n")
            segs.append(Segment("list", j, "full", first_line_of(j)))
            item = []

    def flush_quote():
        nonlocal quote
        if quote:
            j = _join_mapped(quote, "\n")
            segs.append(Segment("quote", j, "none", first_line_of(j)))
            quote = []

    def flush_all():
        flush_para()
        flush_item()
        flush_quote()

    for line in mt.lines():
        raw_line = line.t.rstrip("\r")
        line = line.slice(0, len(raw_line))
        s = raw_line.strip()
        if not s:
            flush_all()
            continue
        if HRULE.match(raw_line) or DIV_FENCE.match(raw_line):
            flush_all()
            continue
        h = HEADING.match(raw_line)
        if h:
            flush_all()
            body = line.slice(h.start(3), h.end(3))
            segs.append(Segment("heading", body, "light", first_line_of(body)))
            continue
        if s.startswith("|"):
            flush_all()
            if TABLE_SEP.match(raw_line):
                continue
            cells = line.sub(r"^\s*\||\|\s*$", "").sub(r"\s*\|\s*", " ; ")
            segs.append(Segment("table", cells, "light", first_line_of(cells)))
            continue
        if s.startswith(">"):
            flush_para()
            flush_item()
            body = line.sub(r"^\s*>+\s?", "")
            quote.append(body)
            continue
        li = LIST_ITEM.match(raw_line)
        if li:
            flush_all()
            item.append(line.slice(li.end(), len(raw_line)))
            continue
        if item and raw_line[:1] in (" ", "\t"):
            item.append(line.sub(r"^\s+", ""))
            continue
        flush_item()
        flush_quote()
        para.append(line)
    flush_all()
    ex.segments = _merge_math(segs)
    return ex


# ---------------------------------------------------------------------------------------
# LaTeX (best effort)

TEX_COMMENT = re.compile(r"(?<!\\)%[^\n]*")
TEX_SECTION = re.compile(r"\\(?:sub)*(?:section|paragraph)\*?\{([^}]*)\}")
TEX_CITE = re.compile(r"\\(?:cite[a-z]*|parencite|textcite|autocite)\*?(?:\[[^\]]*\])*\{[^}]*\}")
TEX_REF = re.compile(r"\\(?:ref|eqref|autoref|cref|Cref|pageref)\{[^}]*\}")
TEX_DROP_CMD = re.compile(r"\\(?:label|vspace|hspace|noindent|centering|newpage|clearpage|bibliographystyle|bibliography|input|include)\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?")
TEX_WRAP = re.compile(r"\\(?:textbf|textit|emph|textrm|textsc|texttt|underline|mbox|text)\{([^{}]*)\}")
TEX_ENV_DROP = re.compile(r"\\begin\{(figure|table|tabular|equation|align|lstlisting|verbatim)\*?\}.*?\\end\{\1\*?\}", re.S)


def extract_tex(raw: str, index: LineIndex) -> Extraction:
    ex = Extraction()
    mt = MappedText(raw)
    b = raw.find("\\begin{document}")
    if b >= 0:
        mt = mt.slice(b + len("\\begin{document}"), len(raw))
    mt = mt.sub(TEX_COMMENT, "")
    mt = mt.sub(TEX_ENV_DROP, " X ")
    mt = mt.sub(DISPLAY_MATH, " X ")
    mt = mt.sub(LATEX_BRACKET, " X ")
    mt = mt.sub(INLINE_MATH, _math_repl)
    mt = _find_placeholders(mt, ex.placeholders)
    mt = mt.sub(TEX_CITE, "[1]")
    mt = mt.sub(TEX_REF, "1")
    mt = mt.sub(TEX_DROP_CMD, "")
    for _ in range(3):
        mt = mt.sub(TEX_WRAP, lambda m: m.group(1))
    mt = mt.sub(r"\\(?:begin|end)\{[^}]*\}", "")
    mt = mt.sub(r"\\item\s*", "- ")
    mt = mt.sub(r"~", " ")
    mt = mt.sub(r"``|''", '"')
    mt = mt.sub(r"\\&", "&").sub(r"\\%", "%").sub(r"\\_", "_")
    para: List[MappedText] = []

    def flush():
        nonlocal para
        if para:
            j = _join_mapped(para, "\n")
            segs.append(Segment("para", j, "full", index.locate(j.m[0])[0]))
            para = []

    segs: List[Segment] = []
    for line in mt.lines():
        s = line.t.strip()
        if not s:
            flush()
            continue
        sec = TEX_SECTION.search(line.t)
        if sec and line.t.strip().startswith("\\"):
            flush()
            body = line.slice(sec.start(1), sec.end(1))
            segs.append(Segment("heading", body, "light", index.locate(body.m[0])[0] if body.t else 0))
            continue
        if s.startswith("\\"):
            flush()
            continue
        para.append(line)
    flush()
    ex.segments = _merge_math(segs)
    return ex


def extract_plain(raw: str, index: LineIndex) -> Extraction:
    ex = Extraction()
    mt = _find_placeholders(MappedText(raw), ex.placeholders)
    para: List[MappedText] = []
    segs: List[Segment] = []

    def flush():
        nonlocal para
        if para:
            j = _join_mapped(para, "\n")
            segs.append(Segment("para", j, "full", index.locate(j.m[0])[0]))
            para = []

    for line in mt.lines():
        if not line.t.strip():
            flush()
        else:
            para.append(line)
    flush()
    ex.segments = segs
    return ex


def extract(raw: str, path: str, index: LineIndex) -> Extraction:
    p = path.lower()
    if p.endswith(".tex"):
        return extract_tex(raw, index)
    if p.endswith((".md", ".markdown", ".qmd")):
        return extract_markdown(raw, index)
    return extract_plain(raw, index)


def lint_text(segs: List[Segment], levels=("full",)) -> Tuple[MappedText, List[Tuple[int, int, Segment]]]:
    """Concatenate segments for the grammar tools. Returns text and (start, end, segment) ranges."""
    parts, ranges, pos = [], [], 0
    chosen = [s for s in segs if s.lint in levels and s.mt.t.strip()]
    for i, s in enumerate(chosen):
        if i:
            pos += 2
        ranges.append((pos, pos + len(s.mt.t), s))
        pos += len(s.mt.t)
        parts.append(s.mt)
    return _join_mapped(parts, "\n\n"), ranges
