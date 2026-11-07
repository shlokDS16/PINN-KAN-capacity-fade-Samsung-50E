"""Detect hidden or look-alike characters in the raw source. Report only; never fixes."""
from __future__ import annotations

import re
import unicodedata
from typing import List

from .extract import LineIndex
from .flag import Flag

ZERO_WIDTH = {
    0x200B: "ZERO WIDTH SPACE",
    0x200C: "ZERO WIDTH NON-JOINER",
    0x200D: "ZERO WIDTH JOINER",
    0x2060: "WORD JOINER",
    0x2061: "FUNCTION APPLICATION",
    0x2062: "INVISIBLE TIMES",
    0x2063: "INVISIBLE SEPARATOR",
    0x2064: "INVISIBLE PLUS",
    0xFEFF: "ZERO WIDTH NO-BREAK SPACE (BOM)",
    0x180E: "MONGOLIAN VOWEL SEPARATOR",
    0x034F: "COMBINING GRAPHEME JOINER",
    0x115F: "HANGUL CHOSEONG FILLER",
    0x1160: "HANGUL JUNGSEONG FILLER",
    0x3164: "HANGUL FILLER",
    0xFFA0: "HALFWIDTH HANGUL FILLER",
}
BIDI = {
    0x200E: "LEFT-TO-RIGHT MARK",
    0x200F: "RIGHT-TO-LEFT MARK",
    0x061C: "ARABIC LETTER MARK",
    0x202A: "LEFT-TO-RIGHT EMBEDDING",
    0x202B: "RIGHT-TO-LEFT EMBEDDING",
    0x202C: "POP DIRECTIONAL FORMATTING",
    0x202D: "LEFT-TO-RIGHT OVERRIDE",
    0x202E: "RIGHT-TO-LEFT OVERRIDE",
    0x2066: "LEFT-TO-RIGHT ISOLATE",
    0x2067: "RIGHT-TO-LEFT ISOLATE",
    0x2068: "FIRST STRONG ISOLATE",
    0x2069: "POP DIRECTIONAL ISOLATE",
}
ODD_SPACES = {
    0x00A0: "NO-BREAK SPACE",
    0x1680: "OGHAM SPACE MARK",
    0x2007: "FIGURE SPACE",
    0x2008: "PUNCTUATION SPACE",
    0x2009: "THIN SPACE",
    0x200A: "HAIR SPACE",
    0x202F: "NARROW NO-BREAK SPACE",
    0x205F: "MEDIUM MATHEMATICAL SPACE",
    0x3000: "IDEOGRAPHIC SPACE",
}
for _cp in range(0x2000, 0x2007):
    ODD_SPACES[_cp] = unicodedata.name(chr(_cp), "SPACE")
OTHER_INVISIBLE = {
    0x00AD: "SOFT HYPHEN",
    0x2028: "LINE SEPARATOR",
    0x2029: "PARAGRAPH SEPARATOR",
    0xFFFC: "OBJECT REPLACEMENT CHARACTER",
    0xFFFD: "REPLACEMENT CHARACTER (encoding damage)",
}
LOOKALIKE_PUNCT = {
    0x2011: "NON-BREAKING HYPHEN",
    0x2044: "FRACTION SLASH",
    0x2215: "DIVISION SLASH",
    0x2216: "SET MINUS",
    0xFF0F: "FULLWIDTH SOLIDUS",
    0x01C3: "LATIN LETTER RETROFLEX CLICK",
    0x2024: "ONE DOT LEADER",
    0x2236: "RATIO",
    0xFF1A: "FULLWIDTH COLON",
    0xFF0C: "FULLWIDTH COMMA",
}
# characters after which a no-break space is normal
NBSP_NEXT_OK = re.compile(r"[\d%°]")
NBSP_PREV_WORD_OK = {
    "fig.", "figs.", "figure", "table", "section", "sec.", "eq.", "eqs.", "equation", "ref.", "refs.",
    "appendix", "chapter", "no.", "vol.", "pp.", "p.", "al.", "dr.", "mr.", "ms.", "prof.",
}
CONFUSABLE_SCRIPTS = {"CYRILLIC", "ARMENIAN", "CHEROKEE", "COPTIC", "GEORGIAN", "HEBREW", "ARABIC"}
WORD = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*", re.U)


def _script(ch: str) -> str:
    try:
        return unicodedata.name(ch).split()[0]
    except ValueError:
        return "UNKNOWN"


def _ctx(raw: str, i: int, n: int = 1) -> str:
    a, b = max(0, i - 30), min(len(raw), i + n + 30)
    pre = raw[a:i].replace("\n", " ")
    post = raw[i + n : b].replace("\n", " ")
    return pre + "[" + "".join(f"U+{ord(c):04X}" for c in raw[i : i + n]) + "]" + post


def scan(raw: str, path: str, index: LineIndex, manuscript: bool = True) -> List[Flag]:
    flags: List[Flag] = []

    def add(i: int, n: int, rule: str, msg: str, sug: str, sev: str, name: str = ""):
        line, col = index.locate(i)
        flags.append(
            Flag(path, line, col, i, i + n, "Hidden characters", rule, msg, sug, _ctx(raw, i, n)[:120], sev,
                 "hidden", manuscript)
        )

    n = len(raw)
    for i, ch in enumerate(raw):
        cp = ord(ch)
        if cp < 0x80 and (cp >= 0x20 or ch in "\t\n\r"):
            if cp == 0x7F:
                add(i, 1, "control-char", "DEL control character", "Delete it.", "high")
            continue
        if cp < 0x20 or 0x7F <= cp <= 0x9F:
            add(i, 1, "control-char", f"Control character U+{cp:04X}", "Delete it.", "high")
        elif cp in ZERO_WIDTH:
            if cp == 0xFEFF and i == 0:
                add(i, 1, "bom", "Byte-order mark at start of file (harmless for most tools)",
                    "Save as UTF-8 without BOM if a tool complains.", "low")
            else:
                add(i, 1, "zero-width", f"{ZERO_WIDTH[cp]} (U+{cp:04X}) is invisible and splits words for tools",
                    "Delete it.", "high")
        elif cp in BIDI:
            add(i, 1, "bidi-control", f"{BIDI[cp]} (U+{cp:04X}) can reorder text on screen (Trojan Source class)",
                "Delete it unless the text is genuinely right-to-left.", "high")
        elif 0xE0000 <= cp <= 0xE007F:
            add(i, 1, "tag-char", f"Unicode tag character U+{cp:05X} (invisible; used to smuggle text)",
                "Delete it.", "high")
        elif 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF:
            add(i, 1, "variation-selector", f"Variation selector U+{cp:04X} (invisible)",
                "Delete it unless it follows an emoji or CJK character.", "medium")
        elif cp in OTHER_INVISIBLE:
            add(i, 1, "invisible-other", f"{OTHER_INVISIBLE[cp]} (U+{cp:04X})", "Delete or replace it.",
                "medium" if cp != 0xFFFD else "high")
        elif cp in ODD_SPACES:
            prev_tok = re.search(r"(\S+)$", raw[max(0, i - 12) : i])
            prev_word = prev_tok.group(1).lower().strip("()[],;:") if prev_tok else ""
            nxt = raw[i + 1 : i + 2]
            ok = cp in (0x00A0, 0x202F) and (
                NBSP_NEXT_OK.match(nxt or " ") or prev_word in NBSP_PREV_WORD_OK or prev_word[-1:].isdigit()
            )
            if cp == 0x00A0 and ok:
                continue  # normal use: between a number and its unit, or after Fig./Section
            sev = "medium" if cp in (0x00A0, 0x202F, 0x2009) else "high"
            add(i, 1, "odd-space",
                f"{ODD_SPACES[cp]} (U+{cp:04X}) in a position where a plain space is expected",
                "Replace with a normal space.", sev)
        elif cp in LOOKALIKE_PUNCT:
            add(i, 1, "lookalike-punct", f"{LOOKALIKE_PUNCT[cp]} (U+{cp:04X}) looks like ASCII punctuation",
                "Replace with the ASCII character unless intended.", "medium")
        elif 0xFF01 <= cp <= 0xFF5E:
            add(i, 1, "fullwidth", f"Fullwidth form U+{cp:04X} ({unicodedata.name(ch, '?')})",
                "Replace with the ASCII character.", "medium")
        elif 0x1D400 <= cp <= 0x1D7FF:
            add(i, 1, "math-alphanumeric", f"Mathematical alphanumeric symbol U+{cp:05X} typed as text",
                "Use plain letters, or LaTeX for math.", "low")

    # Homoglyphs: letters from a confusable script inside, or mixed into, Latin words
    for m in WORD.finditer(raw):
        w = m.group(0)
        if w.isascii():
            continue
        scripts = {}
        for off, ch in enumerate(w):
            if ch.isalpha():
                scripts.setdefault(_script(ch), []).append(off)
        if not scripts:
            continue
        has_latin = "LATIN" in scripts
        for sc in list(scripts):
            if sc in CONFUSABLE_SCRIPTS or (sc == "GREEK" and has_latin):
                if sc == "GREEK" and len(w) <= 3 and w[0] in "µμ":  # micro prefix before a unit, e.g. µm
                    continue
                for off in scripts[sc][:1]:
                    i = m.start() + off
                    if has_latin:
                        add(i, 1, "homoglyph-mixed-script",
                            f"Word mixes Latin with {sc.title()} letters ({w!r}); possible look-alike character",
                            "Retype the word with Latin letters.", "high")
                    else:
                        add(i, 1, "non-latin-script",
                            f"{sc.title()} letters in a Latin-script manuscript ({w!r})",
                            "Check that this is intended (for example an author's name).", "medium")
                    break
    return flags
