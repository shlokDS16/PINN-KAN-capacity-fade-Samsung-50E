"""Merge flags from all tools and write the Markdown report."""
from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from typing import Dict, List

from .doc import Doc
from .flag import CATEGORIES, CATEGORY_PRIORITY, Flag, SEVERITY_WEIGHT

STYLE_FAMILY = {
    "Wordiness", "Weak or hedged wording", "AI-sounding phrasing", "Style", "Claim needs evidence", "Clarity",
}


def _family(cat: str) -> str:
    return "style" if cat in STYLE_FAMILY else cat


def merge_flags(flags: List[Flag]) -> List[Flag]:
    """Collapse overlapping flags from different tools into one row listing every rule."""
    flags = sorted(flags, key=lambda f: (f.file, f.start, -(f.end - f.start)))
    out: List[Flag] = []
    for f in flags:
        merged = False
        for c in reversed(out[-12:]):
            if c.file != f.file:
                break
            if c.end <= f.start:
                continue
            ov = min(c.end, f.end) - max(c.start, f.start)
            short = max(1, min(c.end - c.start, f.end - f.start))
            if ov / short >= 0.5 and _family(c.category) == _family(f.category):
                keep, other = (c, f) if c.score >= f.score else (f, c)
                if keep is f:
                    out[out.index(c)] = f
                keep.rule = " + ".join(dict.fromkeys(keep.rule.split(" + ") + other.rule.split(" + ")))
                if other.message and other.message not in keep.message:
                    keep.message = (keep.message + " | " + other.message)[:400]
                if not keep.suggestion and other.suggestion:
                    keep.suggestion = other.suggestion
                keep.source = "+".join(dict.fromkeys(keep.source.split("+") + other.source.split("+")))
                keep.start, keep.end = min(c.start, f.start), max(c.end, f.end)
                merged = True
                break
        if not merged:
            out.append(f)
    return sorted(out, key=lambda f: (f.file, f.line, f.col))


def _esc(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _row(f: Flag, with_file: bool = False) -> str:
    sug = f.message.strip()
    if f.suggestion:
        sug += " -> " + f.suggestion
    sug = sug[:260]
    first = f"{f.file.rsplit('/', 1)[-1]}:{f.line}" if with_file else f"{f.line}:{f.col}"
    return f"| {first} | {f.category} | {_esc(f.text)} | `{_esc(f.rule)}` | {_esc(sug)} |"


def top_n(flags: List[Flag], n: int = 20, per_cat: int = 5) -> List[Flag]:
    pool = [f for f in flags if f.manuscript and f.category != "Placeholder"]
    pool.sort(key=lambda f: (-f.score, f.file, f.line))
    out, cats, lines = [], Counter(), set()
    for f in pool:
        if cats[f.category] >= per_cat or (f.file, f.line) in lines:
            continue
        out.append(f)
        cats[f.category] += 1
        lines.add((f.file, f.line))
        if len(out) >= n:
            break
    return out


def write_report(path, docs: List[Doc], flags: List[Flag], meta: dict) -> str:
    L: List[str] = []
    ap = L.append
    ap("# Prose check report")
    ap("")
    ap(f"Generated {dt.date.today().isoformat()} by `tools/prose_check.py`. Nothing in the drafts was edited; "
       "every row is a suggestion for you to accept, rephrase or dismiss.")
    ap("")
    ap("## How this run was configured")
    ap("")
    for k, v in meta.get("settings", []):
        ap(f"- **{k}:** {v}")
    ap("")
    man_docs = [d for d in docs if d.manuscript]
    work_docs = [d for d in docs if not d.manuscript]
    by_file_cat: Dict[str, Counter] = defaultdict(Counter)
    for f in flags:
        by_file_cat[f.file][f.category] += 1

    ap("## Summary")
    ap("")
    ap(f"Manuscript files: {len(man_docs)} (counted in the ranking). Working notes: {len(work_docs)} "
       "(checked, shown separately, left out of the top 20).")
    ap("")
    ap("| Category | Manuscript | Working notes |")
    ap("|---|---:|---:|")
    cm = Counter(f.category for f in flags if f.manuscript)
    cw = Counter(f.category for f in flags if not f.manuscript)
    for c in CATEGORIES:
        if cm[c] or cw[c]:
            ap(f"| {c} | {cm[c]} | {cw[c]} |")
    ap(f"| **Total** | **{sum(cm.values())}** | **{sum(cw.values())}** |")
    ap("")
    ap("| File | " + " | ".join(["Flags", "High", "Medium", "Low"]) + " |")
    ap("|---|---:|---:|---:|---:|")
    for d in docs:
        fl = [f for f in flags if f.file == d.path]
        sv = Counter(f.severity for f in fl)
        tag = "" if d.manuscript else " (working note)"
        ap(f"| {d.path.rsplit('/', 1)[-1]}{tag} | {len(fl)} | {sv['high']} | {sv['medium']} | {sv['low']} |")
    ap("")
    src = Counter()
    for f in flags:
        for s in f.source.split("+"):
            src[s] += 1
    ap("Flags by tool (a merged row counts once per tool): " + ", ".join(f"{k} {v}" for k, v in sorted(src.items())) + ".")
    ap("")

    ap("## Top 20 to fix first")
    ap("")
    ap("Ranked by severity, then by what a referee notices first (hidden characters, grammar and spelling, "
       "verbatim text, unsupported claims, undefined abbreviations). At most 5 per category and one per line. "
       "Placeholders are excluded; they are listed in `00_open_items.md` and in the tables below.")
    ap("")
    ap("| # | Where | Category | Flagged text | Rule | Why and suggestion |")
    ap("|---:|---|---|---|---|---|")
    for i, f in enumerate(top_n(flags), 1):
        sug = f.message.strip() + ((" -> " + f.suggestion) if f.suggestion else "")
        ap(f"| {i} | {f.file.rsplit('/', 1)[-1]}:{f.line} | {f.category} | {_esc(f.text)} | `{_esc(f.rule)}` | {_esc(sug[:240])} |")
    ap("")

    ap("## Flags by file")
    ap("")
    ap("Line:column refers to the source file. Flagged text is the cleaned prose (math shown as X, "
       "citations as [1]) with the flagged span between \u00ab \u00bb.")
    ap("")
    for d in docs:
        fl = [f for f in flags if f.file == d.path]
        ap(f"### {d.path}" + ("" if d.manuscript else "  (working note, not manuscript text)"))
        ap("")
        if not fl:
            ap("No flags.")
            ap("")
            continue
        cc = Counter(f.category for f in fl)
        ap("Per category: " + ", ".join(f"{c} {cc[c]}" for c in CATEGORIES if cc[c]) + ".")
        ap("")
        ap("| Line | Category | Flagged text | Rule | Suggestion |")
        ap("|---|---|---|---|---|")
        for f in sorted(fl, key=lambda x: (x.line, x.col)):
            ap(_row(f))
        ap("")

    unk = meta.get("unknown_words")
    if unk:
        ap("## Words LanguageTool does not know")
        ap("")
        ap("If a word is correct, add it to `tools/prose_rules/dictionary.txt`; otherwise it is a typo.")
        ap("")
        ap("| Word | Count |")
        ap("|---|---:|")
        for w, n in unk.most_common(60):
            ap(f"| {_esc(w)} | {n} |")
        ap("")

    ap("## What this report cannot tell you")
    ap("")
    for line in meta.get("limits", []):
        ap(f"- {line}")
    ap("")
    text = "\n".join(L)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return text
