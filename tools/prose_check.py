#!/usr/bin/env python
"""Local, offline Grammarly-style checker for the journal draft.

Run:  /c/Python314/python.exe -I tools/prose_check.py paper/draft/*.md --out paper/draft/PROSE_CHECK_REPORT.md

Checks (see tools/PROSE_CHECK_README.md):
  1. LanguageTool, local Java server, picky level.
  2. Vale with the proselint, write-good and Microsoft packages.
  3. Journal rules (tools/prose_rules/jes_rules.yml and jes_checks.py).
  4. Hidden and look-alike characters.
It never edits a draft and never calls an online service.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# `python -I` drops the script directory and the user site from sys.path, so add what we need.
for p in (HERE / "bin" / "pylib", HERE):
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _import_spacy():
    try:
        import spacy  # noqa: F401

        return spacy, "importable"
    except ImportError:
        pass
    try:  # -I disables the user site; fall back to it explicitly and say so in the report
        import site

        us = site.getusersitepackages()
        if us and os.path.isdir(us) and us not in sys.path:
            sys.path.append(us)
        import spacy  # noqa: F401

        return spacy, f"user site {us}"
    except Exception:
        return None, "not available"


def main(argv=None) -> int:
    import yaml

    from prose_rules import hidden_chars, jes_checks, lt_runner, report, similarity, vale_runner
    from prose_rules.doc import Doc
    from prose_rules.extract import LineIndex, extract, lint_text
    from prose_rules.flag import Flag

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="Markdown / LaTeX / text files or glob patterns")
    ap.add_argument("--out", help="report path (Markdown); default: print to stdout")
    ap.add_argument("--lang", default="auto", choices=["auto", "en-GB", "en-US"])
    ap.add_argument("--rules", default=str(HERE / "prose_rules" / "jes_rules.yml"))
    ap.add_argument("--dictionary", default=str(HERE / "prose_rules" / "dictionary.txt"))
    ap.add_argument("--vale-exe", default=str(HERE / "bin" / "vale" / ("vale.exe" if os.name == "nt" else "vale")))
    ap.add_argument("--vale-ini", default=str(HERE / "prose_rules" / "vale" / ".vale.ini"))
    ap.add_argument("--lt-path", default="", help="folder holding the LanguageTool download (default: the library cache)")
    ap.add_argument("--sim-dir", action="append", default=None, help="folder of reference texts for the verbatim-run check")
    ap.add_argument("--min-sim-words", type=int, default=10)
    ap.add_argument("--no-lt", action="store_true")
    ap.add_argument("--no-vale", action="store_true")
    ap.add_argument("--no-spacy", action="store_true")
    ap.add_argument("--no-similarity", action="store_true")
    ap.add_argument("--all-manuscript", action="store_true", help="treat every file as manuscript text")
    args = ap.parse_args(argv)

    cfg = yaml.safe_load(Path(args.rules).read_text(encoding="utf-8"))
    rules = jes_checks.Rules(cfg)
    if args.all_manuscript:
        cfg["non_manuscript_files"] = []

    # ---- files
    out_path = Path(args.out).resolve() if args.out else None
    paths = []
    for pat in args.files:
        hits = sorted(glob.glob(pat)) or ([pat] if os.path.exists(pat) else [])
        for h in hits:
            hp = Path(h).resolve()
            if out_path and hp == out_path:
                continue
            if hp.name == "PROSE_CHECK_REPORT.md":
                continue
            if hp.is_file() and hp not in paths:
                paths.append(hp)
    if not paths:
        print("No input files found.", file=sys.stderr)
        return 2

    def disp(p: Path) -> str:
        try:
            return p.relative_to(ROOT).as_posix()
        except ValueError:
            return p.as_posix()

    docs = []
    bom_files = []
    for p in paths:
        data = p.read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            bom_files.append(p.name)
        raw = data.decode("utf-8", errors="replace")
        idx = LineIndex(raw)
        ex = extract(raw, p.name, idx)
        docs.append(Doc(disp(p), raw, idx, ex, jes_checks.is_manuscript_name(p.name, cfg)))

    # ---- language variant
    uk = us = 0
    for d in docs:
        if not d.manuscript:
            continue
        text = " ".join(s.mt.t for s in d.ex.segments if s.lint == "full")
        for a, b in cfg.get("spelling_pairs", []):
            uk += len(re.findall(r"\b\w*" + a + r"\w*", text, re.I))
            us += len(re.findall(r"\b\w*" + b + r"\w*", text, re.I))
    if args.lang == "auto":
        lang = "en-US" if us > uk else "en-GB"
        lang_note = f"auto-detected from the draft: {uk} UK-spelled vs {us} US-spelled words in the paired list"
    else:
        lang, lang_note = args.lang, "set by --lang"

    # ---- spaCy (sentence splitting, rule of three, dangling modifiers, bare 'This')
    nlp, spacy_note, spacy_ver, model_ver = None, "disabled (--no-spacy)", "", ""
    if not args.no_spacy:
        spacy, spacy_note = _import_spacy()
        if spacy is not None:
            try:
                nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
                nlp.max_length = 2_000_000
                spacy_ver = spacy.__version__
                model_ver = f"en_core_web_sm {nlp.meta.get('version', '?')}"
            except Exception as exc:
                spacy_note = f"model en_core_web_sm not loadable ({exc}); regex sentence splitter used"
                nlp = None
        else:
            spacy_note = "spaCy not importable; regex sentence splitter used and the grammar-structure checks are off"

    all_flags: list[Flag] = []

    # ---- 4. hidden characters (raw source, comments and code included)
    for d in docs:
        all_flags += hidden_chars.scan(d.raw, d.path, d.index, d.manuscript)

    # ---- 3. journal rules
    for d in docs:
        all_flags += jes_checks.check_doc(d, rules, nlp)
    all_flags += jes_checks.check_abbreviations(docs, rules)
    all_flags += jes_checks.check_consistency(docs, rules)

    # ---- similarity with reference texts on disk
    sim_info = {"ran": False}
    if not args.no_similarity:
        dirs = [Path(x) for x in args.sim_dir] if args.sim_dir else [ROOT / "refs" / "fulltext"]
        sf, sim_info = similarity.run(docs, dirs, args.min_sim_words)
        all_flags += sf

    # ---- 1. LanguageTool (local server only)
    lt_info = {"ran": False, "error": "skipped (--no-lt)"}
    joined = {}
    if not args.no_lt:
        dpath = Path(args.dictionary)
        words = []
        if dpath.exists():
            for line in dpath.read_text(encoding="utf-8").splitlines():
                line = line.split("#", 1)[0].strip()
                if line:
                    words.append(line)
        lf, lt_info, joined = lt_runner.run(docs, cfg["languagetool"], lang, words, args.lt_path)
        all_flags += lf
        if lt_info.get("error"):
            print(f"WARNING: LanguageTool did not complete: {lt_info['error']}", file=sys.stderr)

    # ---- 2. Vale
    vale_info = {"ran": False, "error": "skipped (--no-vale)"}
    if not args.no_vale:
        vf, vale_info = vale_runner.run(docs, Path(args.vale_exe), Path(args.vale_ini), joined, cfg.get("vale_ignore_text"))
        all_flags += vf
        if vale_info.get("error"):
            print(f"WARNING: Vale did not complete: {vale_info['error']}", file=sys.stderr)

    merged = report.merge_flags(all_flags)

    # ---- report header
    java = ""
    try:
        java = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=30).stderr.splitlines()[0]
    except Exception:
        java = "java not found"
    rules_sha = hashlib.sha256(Path(args.rules).read_bytes()).hexdigest()[:16]
    settings = [
        ("Command", "`python -I tools/prose_check.py " + " ".join(argv if argv is not None else sys.argv[1:]) + f"` ({len(paths)} files checked)"),
        ("Spelling variant", f"{lang} ({lang_note})"),
        ("Python", f"{platform.python_version()} (isolated mode `-I`; project packages from `tools/bin/pylib`)"),
        ("LanguageTool", (
            f"{lt_info.get('server', '?')}; server download version {lt_info.get('download_version', '?')}; "
            f"{lt_info.get('python_package', 'language_tool_python 3.4.0')}; picky level {'on' if lt_info.get('picky') else 'off'}; "
            f"local server only (no public API); {java}"
        ) if lt_info.get("ran") else f"NOT RUN: {lt_info.get('error')}"),
        ("Vale", (
            f"{vale_info.get('version')}; binary SHA256 `{vale_info.get('sha256')}`; styles (proselint, write-good, Microsoft) "
            f"SHA256 `{vale_info.get('styles_sha256')}`"
        ) if vale_info.get("ran") else f"NOT RUN: {vale_info.get('error')}"),
        ("spaCy", f"{spacy_ver or 'n/a'} / {model_ver or 'n/a'} ({spacy_note})"),
        ("Journal rules", f"`tools/prose_rules/jes_rules.yml` (SHA256 prefix `{rules_sha}`) and `jes_checks.py`"),
        ("Similarity", (
            f"verbatim runs of {sim_info.get('min_words')}+ words against {sim_info.get('sources')} reference texts in `refs/fulltext`"
            if sim_info.get("ran") else "not run (no reference texts found or --no-similarity)"
        )),
        ("Hidden characters", "zero-width, bidi, tag, variation selectors, odd spaces, soft hyphen, control, homoglyph; scans the raw file including comments"),
        ("Byte-order marks", ", ".join(bom_files) if bom_files else "none"),
    ]
    limits = [
        "Grammar and style tools make false positives on scientific prose; each row is a prompt to look, not an error. "
        "Math, code spans, citations and HTML comments are replaced by neutral tokens before checking, so what the tools read "
        "is not the exact source text.",
        "The AI-phrasing, claim and abbreviation rules are heuristics from the research-humanizer skill's pattern list. "
        "A clean result does not prove the text will pass an AI detector.",
        "The verbatim-run check compares only with the reference texts held under `refs/fulltext`. It is not a plagiarism "
        "service; run Elsevier's iThenticate or your university's checker for a similarity score.",
        "Tables and headings get the word-level rules only; blockquote banners and fenced code are skipped.",
        "Abbreviation definition is judged on the manuscript files in the order given; the abstract is not a separate file, "
        "so Elsevier's rule of defining again in the main text is not enforced.",
    ]
    meta = {"settings": settings, "limits": limits, "unknown_words": lt_info.get("unknown_words")}
    text = report.write_report(out_path, docs, merged, meta) if out_path else report.write_report(os.devnull, docs, merged, meta)
    if not out_path:
        sys.stdout.write(text)
    n_man = sum(1 for f in merged if f.manuscript)
    print(f"{len(merged)} flags ({n_man} in manuscript files) in {len(docs)} files; "
          f"LT {'ok' if lt_info.get('ran') else 'not run'}, Vale {'ok' if vale_info.get('ran') else 'not run'}"
          + (f"; report: {out_path}" if out_path else ""), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
