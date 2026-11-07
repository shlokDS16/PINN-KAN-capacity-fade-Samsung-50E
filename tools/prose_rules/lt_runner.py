"""LanguageTool through a LOCAL server only (language_tool_python). Never uses the public API."""
from __future__ import annotations

import re
import subprocess
from collections import Counter
from typing import Dict, List, Tuple

from .doc import Doc, make_flag
from .extract import MappedText, lint_text
from .flag import Flag

CHUNK = 12000
IDENT_RX = re.compile(r"[A-Za-z]*\d|_|[a-z][A-Z]|[A-Z]{2,}|^[A-Z][a-z]*[A-Z]")


def map_category(lt_cat: str, issue: str, rule_id: str) -> Tuple[str, str]:
    c = (lt_cat or "").upper()
    if c == "TYPOS" or issue == "misspelling":
        return "Spelling", "high"
    if c in ("GRAMMAR", "CONFUSED_WORDS", "SEMANTICS", "CASING", "NONSTANDARD_PHRASES"):
        return "Grammar", "high"
    if c == "PUNCTUATION":
        return "Punctuation", "medium"
    if c in ("TYPOGRAPHY", "WHITESPACE"):
        return "Typography", "low"
    if c in ("REDUNDANCY", "PLAIN_ENGLISH"):
        return "Wordiness", "medium"
    if c in ("BRITISH_ENGLISH", "AMERICAN_ENGLISH", "BRITISH_ENGLISH_STYLE"):
        return "Consistency", "medium"
    if c == "COMPOUNDING":
        return "Punctuation", "medium"
    if c in ("REPETITIONS_STYLE", "REPETITIONS"):
        return "Clarity", "low"
    if c in ("STYLE", "COLLOCATIONS", "WIKIPEDIA", "CREATIVE_WRITING", "TONE"):
        return "Style", "low"
    if issue == "grammar":
        return "Grammar", "high"
    if issue in ("typographical", "whitespace"):
        return "Typography", "low"
    if issue == "style":
        return "Style", "low"
    return "Grammar", "medium"


def server_version(tool) -> str:
    """The server reports version None for release zips, so name the folder and hash the jar."""
    try:
        import hashlib

        from language_tool_python.utils import get_language_tool_directory

        d = get_language_tool_directory()
        jar = d / "languagetool-server.jar"
        sha = hashlib.sha256(jar.read_bytes()).hexdigest() if jar.exists() else "?"
        return (
            f"LanguageTool {tool.language_tool_download_version} (folder `{d.name}`, "
            f"official release zip checked against SHA-256 by language_tool_python; server jar SHA-256 `{sha}`)"
        )
    except Exception as exc:  # pragma: no cover
        return f"LanguageTool {tool.language_tool_download_version} (details unavailable: {exc})"


def run(docs: List[Doc], cfg: dict, language: str, dictionary: List[str], lt_path: str = "") -> Tuple[List[Flag], dict, Dict[int, MappedText]]:
    info: dict = {"ran": False, "language": language}
    joined_by_doc: Dict[int, MappedText] = {}
    flags: List[Flag] = []
    try:
        import os

        if lt_path:
            os.environ["LTP_PATH"] = lt_path
        import language_tool_python as ltp

        info["python_package"] = f"language_tool_python {getattr(ltp, '__version__', '3.4.0')}"
        tool = ltp.LanguageTool(
            language, new_spellings=dictionary or None, new_spellings_persist=False
        )  # remote_server is never passed: local Java server only
    except Exception as exc:
        info["error"] = f"{type(exc).__name__}: {exc}"
        return flags, info, joined_by_doc
    try:
        tool.picky = bool(cfg.get("picky", True))
        tool.disabled_rules = set(cfg.get("disabled_rules", []))
        if cfg.get("disabled_categories"):
            tool.disabled_categories = set(cfg["disabled_categories"])
        info["server"] = server_version(tool)
        info["download_version"] = tool.language_tool_download_version
        info["picky"] = tool.picky
        info["ran"] = True
        ignore = set(cfg.get("ignore_rules", []))
        ignore_text = {k: re.compile(v) for k, v in (cfg.get("ignore_rule_text") or {}).items()}
        unknown: Counter = Counter()
        rule_counts: Counter = Counter()
        for di, d in enumerate(docs):
            joined, ranges = lint_text(d.ex.segments)
            joined_by_doc[di] = joined
            if not joined.t.strip():
                continue
            # chunk at segment boundaries
            chunks, cur_start = [], 0
            for (a, b, _s) in ranges:
                if b - cur_start > CHUNK and a > cur_start:
                    chunks.append((cur_start, a))
                    cur_start = a
            chunks.append((cur_start, len(joined.t)))
            for ca, cb in chunks:
                text = joined.t[ca:cb]
                for m in tool.check(text):
                    a = ca + m.offset
                    b = a + m.error_length
                    span = joined.t[a:b]
                    if m.rule_id in ignore or span.strip() in ("X", "Author", "[1]"):
                        continue
                    if m.rule_id in ignore_text and ignore_text[m.rule_id].search(span):
                        continue
                    cat, sev = map_category(m.category, m.rule_issue_type, m.rule_id)
                    if cat == "Spelling":
                        word = span.strip()
                        unknown[word] += 1
                        if cfg.get("ignore_spelling_identifiers", True) and IDENT_RX.search(word):
                            continue
                    rule_counts[m.rule_id] += 1
                    sug = ", ".join(f"'{r}'" for r in (m.replacements or [])[:3])
                    f = make_flag(
                        d, joined, a, b, cat, m.rule_id, m.message.strip(), ("Try: " + sug) if sug else "", sev,
                        "languagetool", lt_category=m.category, lt_issue=m.rule_issue_type,
                    )
                    flags.append(f)
        info["unknown_words"] = unknown
        info["rule_counts"] = rule_counts
    except Exception as exc:
        info["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            tool.close()
        except Exception:
            pass
    return flags, info, joined_by_doc
