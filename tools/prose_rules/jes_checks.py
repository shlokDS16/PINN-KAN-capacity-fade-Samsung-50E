"""Journal-specific checks: AI tells, claim words, length limits, abbreviations, consistency, units."""
from __future__ import annotations

import bisect
import fnmatch
import re
import statistics
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

from .doc import Doc, in_quotes, make_flag, snippet
from .extract import MappedText, Segment
from .flag import Flag

WORD_RX = re.compile(r"[A-Za-z0-9À-ɏµΩ°][\w’'./\-]*")
PROTECT = ["et al.", "e.g.", "i.e.", "Fig.", "Figs.", "Eq.", "Eqs.", "vs.", "approx.", "cf.", "No.", "Sec.", "Ref.", "Refs.", "ca.", "resp."]
ADV_CONN = re.compile(r"^(?:Moreover|Furthermore|Additionally|In addition|Notably|Importantly|Besides)\b")
HEDGE_WORDS = re.compile(r"\b(?:may|might|could|possibly|potentially|perhaps|probably|seems?|appears?|suggests?|likely)\b", re.I)


# ----------------------------------------------------------------------------- helpers

def is_manuscript_name(name: str, cfg: dict) -> bool:
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    return not any(fnmatch.fnmatch(base, pat) for pat in cfg.get("non_manuscript_files", []))


def regex_sentences(t: str) -> List[Tuple[int, int]]:
    s = t
    for p in PROTECT:
        s = s.replace(p, p.replace(".", "\u0001"))
    spans, start = [], 0
    for m in re.finditer(r"(?<=[.?!])[\"”)\]]*\s+(?=[A-Z\[(\"“X0-9])", s):
        spans.append((start, m.start() + len(m.group(0).rstrip())))
        start = m.end()
    spans.append((start, len(t)))
    return [(a, b) for a, b in spans if t[a:b].strip()]


def count_words(s: str) -> int:
    s = re.sub(r"\[\d+\]", "", s)
    return len(WORD_RX.findall(s))


class Rules:
    """Compiled rule set from jes_rules.yml."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.word_rules = []
        for r in cfg.get("word_rules", []):
            f = 0 if r.get("case") else re.I
            rx = re.compile(r"(?<!\w)(?:" + "|".join(r["words"]) + r")(?!\w)", f)
            skip = re.compile(r["skip_if"], re.I) if r.get("skip_if") else None
            self.word_rules.append((r, rx, skip))
        self.opener_rules = [(r, re.compile(r["pattern"], re.I)) for r in cfg.get("opener_rules", [])]
        self.unit_rules = [
            (r, re.compile(r["pattern"], 0 if r.get("case") else re.I)) for r in cfg.get("unit_rules", [])
        ]
        self.lim = cfg.get("limits", {})
        self.label_rx = [re.compile(p) for p in cfg.get("label_patterns", [])]
        self.known_abbr = set(cfg.get("known_abbreviations", []))


def _fmt(msg: str, m: re.Match) -> str:
    return msg.replace("{m}", m.group(0).strip())


# ----------------------------------------------------------------------------- per-document

def check_doc(doc: Doc, rules: Rules, nlp=None) -> List[Flag]:
    flags: List[Flag] = []
    lim = rules.lim
    segs = [s for s in doc.ex.segments if s.lint in ("full", "light") and s.mt.t.strip()]
    full = [s for s in segs if s.lint == "full"]

    spdocs: Dict[int, object] = {}
    if nlp is not None and full:
        for s, d in zip(full, nlp.pipe([s.mt.t for s in full], batch_size=16)):
            spdocs[id(s)] = d

    for seg in segs:
        t = seg.mt.t
        if seg.lint == "full":
            sp = spdocs.get(id(seg))
            sent_spans = [(x.start_char, x.end_char) for x in sp.sents] if sp is not None else regex_sentences(t)
        else:
            sent_spans = [(0, len(t))]
        starts = [a for a, _ in sent_spans]

        def sent_of(pos: int) -> Tuple[int, int]:
            i = max(0, bisect.bisect_right(starts, pos) - 1)
            return sent_spans[i]

        ai_hits: List[Tuple[int, int, str]] = []

        # ---- word / phrase rules
        for r, rx, skip in rules.word_rules:
            for m in rx.finditer(t):
                a, b = m.span()
                sa, sb = sent_of(a)
                if skip is not None and skip.search(t[sa:sb]):
                    continue
                if in_quotes(t, a):
                    continue
                flags.append(
                    make_flag(doc, seg.mt, a, b, r["category"], r["id"], _fmt(r["message"], m),
                              r["suggestion"], r["severity"], "jes")
                )
                if r["category"] == "AI-sounding phrasing":
                    ai_hits.append((a, b, m.group(0).lower()))

        # ---- AI cluster
        if seg.lint == "full" and len(ai_hits) >= lim.get("ai_cluster_threshold", 3):
            words = sorted({w for _, _, w in ai_hits})
            flags.append(
                make_flag(doc, seg.mt, 0, min(len(t), 80), "AI-sounding phrasing", "ai-cluster",
                          f"{len(ai_hits)} machine-writing tells in one paragraph ({', '.join(words[:6])}).",
                          "Rewrite the paragraph from the data: specific nouns, numbers, one claim per sentence.",
                          "high", "jes")
            )

        if seg.lint != "full":
            _unit_pass(doc, seg, rules, flags)
            _em_dash(doc, seg, flags)
            continue

        # ---- sentence-level checks
        lens = []
        adv_openers = []
        for sa, sb in sent_spans:
            sent = t[sa:sb]
            n = count_words(sent)
            lens.append(n)
            if n > lim.get("sentence_very_long_words", 60):
                sev = "high"
            elif n > lim.get("sentence_max_words", 40):
                sev = "medium"
            else:
                sev = ""
            if sev:
                flags.append(
                    make_flag(doc, seg.mt, sa, min(sb, sa + 90), "Clarity", "sentence-length",
                              f"Sentence of {n} words (limit {lim.get('sentence_max_words', 40)}).",
                              "Split at the logical joint; keep each qualifier attached to its claim.", sev, "jes")
                )
            for r, rx in rules.opener_rules:
                m = rx.match(sent)
                if not m:
                    continue
                if r.get("cluster_min"):
                    adv_openers.append((sa, sa + m.end(), r, m))
                    continue
                flags.append(
                    make_flag(doc, seg.mt, sa, sa + m.end(), r["category"], r["id"],
                              _fmt(r["message"], m).replace("{v}", m.group(0).split()[1] if " " in m.group(0) else ""),
                              r["suggestion"], r["severity"], "jes")
                )
            hedges = HEDGE_WORDS.findall(sent)
            if len(hedges) >= 3:
                flags.append(
                    make_flag(doc, seg.mt, sa, min(sb, sa + 90), "Weak or hedged wording", "hedge-count",
                              f"{len(hedges)} hedge words in one sentence ({', '.join(sorted({h.lower() for h in hedges}))}).",
                              "Keep the one hedge that matches the evidence; state measured facts without hedges.",
                              "medium", "jes")
                )
        for r_ in {x[2]["id"] for x in adv_openers}:
            group = [x for x in adv_openers if x[2]["id"] == r_]
            if len(group) >= group[0][2]["cluster_min"]:
                for sa, ea, r, m in group:
                    flags.append(
                        make_flag(doc, seg.mt, sa, ea, r["category"], r["id"], _fmt(r["message"], m),
                                  r["suggestion"], r["severity"], "jes")
                    )

        # ---- paragraph-level
        words = sum(lens)
        if seg.kind == "para" and words > lim.get("paragraph_max_words", 200):
            flags.append(
                make_flag(doc, seg.mt, 0, min(len(t), 90), "Clarity", "paragraph-length",
                          f"Paragraph of {words} words (limit {lim.get('paragraph_max_words', 200)}).",
                          "Split at a change of sub-topic; one idea per paragraph.", "medium", "jes")
            )
        if len(lens) >= lim.get("uniform_cadence_min_sentences", 6):
            mean = statistics.mean(lens)
            cv = statistics.pstdev(lens) / mean if mean else 1
            if cv < lim.get("uniform_cadence_cv", 0.28):
                flags.append(
                    make_flag(doc, seg.mt, 0, min(len(t), 90), "AI-sounding phrasing", "uniform-cadence",
                              f"Flat sentence rhythm ({len(lens)} sentences, length CV {cv:.2f}).",
                              "Vary sentence length; merge short claims, split one long one.", "low", "jes")
                )

        # ---- spaCy-based
        sp = spdocs.get(id(seg))
        if sp is not None:
            _spacy_checks(doc, seg, sp, flags)
        _em_dash(doc, seg, flags)
        _unit_pass(doc, seg, rules, flags)

    for a, b in doc.ex.double_spaces:
        line, col = doc.index.locate(a)
        ctx = doc.raw[max(0, a - 30) : b + 30].replace("\n", " ")
        flags.append(
            Flag(doc.path, line, col, a, b, "Typography", "double-space", f"{b - a} spaces in a row.",
                 "Use a single space.", re.sub(r"\s+", " ", ctx)[:120], "low", "jes", doc.manuscript)
        )

    # placeholders
    for a, b, label in doc.ex.placeholders:
        line, col = doc.index.locate(a)
        txt = re.sub(r"\s+", " ", doc.raw[a:b])
        flags.append(
            Flag(doc.path, line, col, a, b, "Placeholder", "open-item",
                 f"Unresolved placeholder [{label}]", "Resolve before submission.", txt[:120], "medium", "jes",
                 doc.manuscript)
        )
    return flags


def _spacy_checks(doc: Doc, seg: Segment, sp, flags: List[Flag]) -> None:
    toks = list(sp)
    triples = []
    for i in range(len(toks) - 4):
        a, c1, b = toks[i], toks[i + 1], toks[i + 2]
        pat = None
        if c1.text == "," and a.pos_ in ("ADJ", "NOUN", "VERB") and b.pos_ == a.pos_:
            if toks[i + 3].text == "," and i + 5 < len(toks) and toks[i + 4].lower_ in ("and", "or") and toks[i + 5].pos_ == a.pos_:
                pat = (i, i + 6)
            elif toks[i + 3].lower_ in ("and", "or") and i + 4 < len(toks) and toks[i + 4].pos_ == a.pos_:
                pat = (i, i + 5)
        if pat and all(re.fullmatch(r"[A-Za-z][a-z\-]+", toks[k].text) for k in (pat[0], pat[0] + 2, pat[1] - 1)):
            if a.pos_ == "VERB" and not all(toks[k].tag_ == "VBG" for k in (pat[0], pat[0] + 2, pat[1] - 1)):
                continue
            triples.append(pat)
    for s, e in triples:
        if toks[s].pos_ == "ADJ":
            flags.append(
                make_flag(doc, seg.mt, toks[s].idx, toks[e - 1].idx + len(toks[e - 1].text), "AI-sounding phrasing",
                          "rule-of-three-adj", "Three adjectives in a row (rule of three).",
                          "Keep the descriptors the data supports; drop the rest.", "low", "jes")
            )
    if len(triples) >= 2:
        flags.append(
            make_flag(doc, seg.mt, toks[triples[1][0]].idx,
                      toks[triples[1][1] - 1].idx + len(toks[triples[1][1] - 1].text), "AI-sounding phrasing",
                      "rule-of-three-repeat", f"{len(triples)} three-item series in one paragraph.",
                      "Vary the list length to what the content has.", "low", "jes")
        )
    for sent in sp.sents:
        st = [t for t in sent if not t.is_space]
        if not st:
            continue
        f = st[0]
        if f.lower_ in ("this", "these", "those", "that") and f.dep_ in ("nsubj", "nsubjpass", "dobj", "pobj") \
                and (len(st) < 2 or st[1].pos_ in ("AUX", "VERB", "ADV", "PART")):
            flags.append(
                make_flag(doc, seg.mt, f.idx, f.idx + len(f.text), "Clarity", "bare-demonstrative",
                          f"Bare '{f.text}' opening a sentence: antecedent may be unclear.",
                          f"Add the noun: '{f.text} <noun> ...'.", "low", "jes")
            )
        if f.tag_ == "VBG" and f.pos_ == "VERB" and f.dep_ == "advcl" and f.lower_ not in (
            "following", "regarding", "depending", "according", "including", "given", "assuming", "considering",
            "concerning", "pending", "excluding", "during",
        ):
            comma = next((k for k, t in enumerate(st[:14]) if t.text == ","), None)
            if comma is not None:
                root = sent.root
                subj = next((c for c in root.children if c.dep_ in ("nsubj", "nsubjpass", "expl")), None)
                if subj is not None and subj.lower_ not in ("we", "i", "they", "one", "it", "there", "this", "that"):
                    flags.append(
                        make_flag(doc, seg.mt, f.idx, st[comma].idx + 1, "Grammar", "dangling-modifier",
                                  f"Possible dangling modifier: '{f.text} ...' should share its subject with "
                                  f"'{subj.text}'.",
                                  "Give the modifier its own subject ('Using X, we ...') or recast the clause.",
                                  "medium", "jes")
                    )


def _em_dash(doc: Doc, seg: Segment, flags: List[Flag]) -> None:
    t = seg.mt.t
    hits = [m for m in re.finditer(r"—|(?<=\s)--(?=\s)", t)]
    for m in hits:
        sev = "medium" if len(hits) >= 2 else "low"
        flags.append(
            make_flag(doc, seg.mt, m.start(), m.end(), "Typography", "em-dash",
                      "Em dash" + (f" (chain of {len(hits)})" if len(hits) >= 2 else "") + " used as punctuation.",
                      "Use a comma, colon, brackets or a second sentence.", sev, "jes")
        )


def _unit_pass(doc: Doc, seg: Segment, rules: Rules, flags: List[Flag]) -> None:
    t = seg.mt.t
    for r, rx in rules.unit_rules:
        if r.get("consistency_with"):
            continue
        for m in rx.finditer(t):
            if in_quotes(t, m.start()):
                continue
            num = m.group(1) if m.groups() else ""
            unit = m.group(2) if m.lastindex and m.lastindex >= 2 else ""
            msg = r["message"].replace("{m}", m.group(0))
            sug = r["suggestion"].replace("{n}", num).replace("{u}", unit)
            flags.append(
                make_flag(doc, seg.mt, m.start(), m.end(), "Units and numbers", r["id"], msg, sug, r["severity"],
                          "jes")
            )


# ----------------------------------------------------------------------------- corpus level

ABBR_RX = re.compile(
    r"(?<![\w/\-.])([A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*|[A-Z]{2,}(?:-[A-Za-z0-9]+)*)s?(?![\w])"
)
NAME_LIKE = re.compile(r"^[A-Z][a-z]{2,}[A-Z]|\d{3,}")  # LightGBM, BatLiNet, INR21700: product or model names
DEF_A = re.compile(r"\b([A-Za-z][\w\-]*(?:[ \-][A-Za-z][\w\-]*){1,9})\s*\((?:[A-Za-z ]+, )?([A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*|[A-Z]{2,})s?\)")
DEF_B = re.compile(r"\b([A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*|[A-Z]{2,})s?\s*\(([A-Za-z][\w\-]*(?: [\w\-]+){1,9})\)")


def _initials_ok(abbr: str, phrase: str) -> bool:
    letters = "".join(w[0].lower() for w in re.split(r"[\s\-]+", phrase) if w)
    a = abbr.lower().rstrip("s")
    if not letters or letters[0] != a[0]:
        return False
    j = 0
    for ch in a:
        k = letters.find(ch, j)
        if k < 0:
            return False
        j = k + 1
    return True


def _trim_phrase(abbr: str, phrase: str) -> str:
    """Shortest run of words just before the parenthesis whose initials spell the abbreviation."""
    words = [w for w in re.split(r"[\s]+", phrase) if w]
    n_letters = len(abbr.rstrip("s"))
    for n in range(max(1, n_letters - 2), min(len(words), n_letters + 4) + 1):
        cand = " ".join(words[-n:])
        if _initials_ok(abbr, cand):
            return cand
    return " ".join(words[-n_letters:])


def check_abbreviations(docs: List[Doc], rules: Rules) -> List[Flag]:
    """First use of an abbreviation must be expanded (definition at or before first use)."""
    flags: List[Flag] = []
    order = [d for d in docs if d.manuscript]
    uses: Dict[str, Tuple[Doc, Segment, int, int]] = {}
    defs: Dict[str, Tuple[int, int, str]] = {}  # abbr -> (doc rank, offset, expansion)
    counts: Counter = Counter()
    expansions: Dict[str, str] = {}
    pos_rank = {}
    for di, d in enumerate(order):
        for seg in d.ex.segments:
            if seg.lint != "full":
                continue
            t = seg.mt.t
            for m in DEF_A.finditer(t):
                ab = m.group(2)
                phrase = _trim_phrase(ab, m.group(1))
                if ab not in defs and (_initials_ok(ab, phrase) or (ab.isupper() and len(ab) >= 3)):
                    defs[ab] = (di, seg.mt.m[m.start(2)], phrase)
                    expansions[ab] = phrase
            for m in DEF_B.finditer(t):
                ab, phrase = m.group(1), m.group(2)
                if ab not in defs and _initials_ok(ab, phrase):
                    defs[ab] = (di, seg.mt.m[m.start(1)], phrase)
                    expansions[ab] = phrase
            for m in ABBR_RX.finditer(t):
                ab = re.sub(r"(?:-[a-z]{3,})+$", "", m.group(1))  # KAN-valued -> KAN
                if ab in rules.known_abbr or any(rx.match(ab) for rx in rules.label_rx) or len(ab) < 2:
                    continue
                if re.fullmatch(r"[A-Z][a-z]+[A-Z]?", ab) or NAME_LIKE.search(ab):  # words and product names
                    continue
                if in_quotes(t, m.start()):
                    continue
                counts[ab] += 1
                key = (di, seg.mt.m[m.start(1)])
                if ab not in pos_rank or key < pos_rank[ab]:
                    uses[ab] = (d, seg, m.start(1), m.end(1))
                    pos_rank[ab] = key
    for ab, (d, seg, a, b) in sorted(uses.items(), key=lambda kv: pos_rank[kv[0]]):
        first_key = pos_rank[ab]
        d_def = defs.get(ab)
        n = counts[ab]
        if d_def is None:
            flags.append(
                make_flag(d, seg.mt, a, b, "Abbreviation", "abbr-undefined",
                          f"'{ab}' is never expanded in the manuscript text ({n} use{'s' if n != 1 else ''}).",
                          f"Write the full term at first use, then '({ab})'.",
                          "high" if n >= 3 else "medium", "jes")
            )
        else:
            def_key = (d_def[0], d_def[1])
            if def_key > first_key:
                dd = order[d_def[0]]
                dl, _ = dd.index.locate(d_def[1])
                flags.append(
                    make_flag(d, seg.mt, a, b, "Abbreviation", "abbr-before-definition",
                              f"'{ab}' is used before it is expanded (expanded in {dd.path.rsplit('/', 1)[-1]} line {dl}).",
                              f"Move the expansion '{d_def[2]} ({ab})' to this first use.", "medium", "jes")
                )
    # expansion repeated after the abbreviation was defined
    for ab, (di, off, phrase) in defs.items():
        rx = re.compile(
            r"(?<!\w)" + r"[\s\-]+".join(re.escape(w) for w in re.split(r"[\s\-]+", phrase) if w) + r"(?!\w)", re.I
        )
        seen = 0
        for dj, d in enumerate(order):
            for seg in d.ex.segments:
                if seg.lint != "full":
                    continue
                for m in rx.finditer(seg.mt.t):
                    if (dj, seg.mt.m[m.start()]) <= (di, off + 60):
                        continue
                    if seen < 2:
                        flags.append(
                            make_flag(d, seg.mt, m.start(), m.end(), "Consistency", "abbr-expansion-repeated",
                                      f"'{phrase}' is written out again after '{ab}' was defined.",
                                      f"Use '{ab}' (journals re-expand only in the abstract and captions).", "low", "jes")
                        )
                    seen += 1
    return flags


STOP_FIRST = {
    "in", "on", "of", "to", "at", "by", "for", "as", "an", "a", "the", "and", "or", "with", "from", "per", "off", "out",
    "up", "no", "so", "all", "one", "two", "three", "four", "five", "six", "if", "is", "it", "be", "we", "can", "are",
}


def check_consistency(docs: List[Doc], rules: Rules) -> List[Flag]:
    flags: List[Flag] = []
    man = [d for d in docs if d.manuscript]
    segs = [(d, s) for d in man for s in d.ex.segments if s.lint in ("full", "light") and s.kind != "table"]
    hy = re.compile(r"(?<![\w\-])([A-Za-z]{2,})-([A-Za-z]{2,})(?:-([A-Za-z]{2,}))?(?![\w\-])")
    forms: Dict[Tuple[str, ...], Dict[str, List]] = defaultdict(lambda: defaultdict(list))
    vocab: Counter = Counter()
    bigrams: Dict[Tuple[str, str], List] = defaultdict(list)
    for d, s in segs:
        t = s.mt.t
        for w in re.findall(r"[A-Za-z]{3,}", t):
            vocab[w.lower()] += 1
        for m in hy.finditer(t):
            parts = tuple(p.lower() for p in m.groups() if p)
            if parts[0] in STOP_FIRST:
                continue
            forms[parts]["hyphen"].append((d, s, m.start(), m.end(), m.group(0)))
        for m in re.finditer(r"(?<![\w\-])([A-Za-z]{2,})\s+([A-Za-z]{2,})(?![\w\-])", t):
            bigrams[(m.group(1).lower(), m.group(2).lower())].append((d, s, m.start(), m.end(), m.group(0)))
    for parts, got in forms.items():
        # spaced and joined variants of an observed hyphenated term
        sp = bigrams.get(parts, []) if len(parts) == 2 else []
        if len(parts) == 3:
            sp = [x for x in bigrams.get(parts[:2], []) if x]  # three-part terms: skip spaced matching
            sp = []
        joined = "".join(parts)
        jn = [] if len(parts) != 2 else [
            (d, s, m.start(), m.end(), m.group(0))
            for d, s in segs
            for m in re.finditer(r"(?<![\w\-])" + re.escape(joined) + r"(?![\w\-])", s.mt.t, re.I)
        ]
        variants = {"hyphen": got["hyphen"], "spaced": sp, "joined": jn}
        present = {k: v for k, v in variants.items() if v}
        if len(present) < 2:
            continue
        ranked = sorted(present.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        major = ranked[0][0]
        desc = ", ".join(f"'{v[0][4]}' x{len(v)}" for _, v in ranked)
        for kind, occ in ranked[1:]:
            for d, s, a, b, txt in occ[:4]:
                flags.append(
                    make_flag(d, s.mt, a, b, "Consistency", "term-variant",
                              f"Inconsistent spelling of one term: {desc}.",
                              f"Use one form throughout (most frequent: {major}). A hyphen is right only before a noun.",
                              "low", "jes")
                )
    # UK / US pairs
    for uk, us in rules.cfg.get("spelling_pairs", []):
        rx_uk = re.compile(r"\b\w*" + uk + r"\w*", re.I)
        rx_us = re.compile(r"\b\w*" + us + r"\w*", re.I)
        hits_uk = [(d, s, m) for d, s in segs for m in rx_uk.finditer(s.mt.t)]
        hits_us = [(d, s, m) for d, s in segs for m in rx_us.finditer(s.mt.t)]
        if hits_uk and hits_us:
            minority = hits_us if len(hits_us) <= len(hits_uk) else hits_uk
            for d, s, m in minority[:6]:
                flags.append(
                    make_flag(d, s.mt, m.start(), m.end(), "Consistency", "spelling-variant",
                              f"UK and US spelling mixed ('{hits_uk[0][2].group(0)}' x{len(hits_uk)} vs "
                              f"'{hits_us[0][2].group(0)}' x{len(hits_us)}).",
                              "Use the journal's variant throughout.", "medium", "jes")
                )
    # percent spacing
    for r, rx in rules.unit_rules:
        if not r.get("consistency_with"):
            continue
        other = re.compile(r["consistency_with"])
        a_hits = [(d, s, m) for d, s in segs for m in rx.finditer(s.mt.t)]
        b_hits = [(d, s, m) for d, s in segs for m in other.finditer(s.mt.t)]
        if a_hits and b_hits:
            minority = a_hits if len(a_hits) <= len(b_hits) else b_hits
            for d, s, m in minority[:8]:
                flags.append(
                    make_flag(d, s.mt, m.start(), m.end(), "Units and numbers", "percent-spacing",
                              f"Percent written both as '10%' ({len(a_hits)}) and '10 %' ({len(b_hits)}).",
                              "Use one style throughout.", "low", "jes")
                )
    # quotation marks
    straight = [(d, s, m) for d, s in segs for m in re.finditer(r'"', s.mt.t)]
    curly = [(d, s, m) for d, s in segs for m in re.finditer(r"[“”]", s.mt.t)]
    if straight and curly:
        minority = straight if len(straight) <= len(curly) else curly
        for d, s, m in minority[:8]:
            flags.append(
                make_flag(d, s.mt, m.start(), m.end(), "Typography", "quote-style",
                          f"Straight ({len(straight)}) and curly ({len(curly)}) double quotes are mixed.",
                          "Use one style throughout.", "medium", "jes")
            )
    ap_s = [(d, s, m) for d, s in segs for m in re.finditer(r"\w'\w", s.mt.t)]
    ap_c = [(d, s, m) for d, s in segs for m in re.finditer(r"\w’\w", s.mt.t)]
    if ap_s and ap_c:
        minority = ap_s if len(ap_s) <= len(ap_c) else ap_c
        for d, s, m in minority[:8]:
            flags.append(
                make_flag(d, s.mt, m.start(), m.end(), "Typography", "apostrophe-style",
                          f"Straight ({len(ap_s)}) and curly ({len(ap_c)}) apostrophes are mixed.",
                          "Use one style throughout.", "medium", "jes")
            )
    return flags
