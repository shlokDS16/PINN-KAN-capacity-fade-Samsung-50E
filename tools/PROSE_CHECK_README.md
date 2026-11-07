# Prose checker (local Grammarly-style review)

`tools/prose_check.py` checks the manuscript prose for grammar, spelling, punctuation, clarity, wordiness,
machine-sounding phrasing, unsupported claims, abbreviations, units, consistency and hidden characters. It runs
offline once set up, never edits a draft, and writes a Markdown report.

## Run

```
/c/Python314/python.exe -I tools/prose_check.py paper/draft/*.md --out paper/draft/PROSE_CHECK_REPORT.md
/c/Python314/python.exe -I tools/prose_rules/selftest.py      # positive-control test, prints PASS or FAIL
```

Inputs may be `.md`, `.tex` or `.txt` (best effort for LaTeX). The output file is never read as input.
Useful flags: `--lang auto|en-GB|en-US` (default `auto`), `--no-lt`, `--no-vale`, `--no-spacy`, `--no-similarity`,
`--all-manuscript` (treat working notes as manuscript), `--sim-dir DIR` (reference texts, default `refs/fulltext`),
`--lt-path DIR`, `--min-sim-words N` (default 10).

A run on `paper/draft/*.md` (10 files, about 115 KB) takes about 30 seconds.

## What it checks

| Layer | Tool | Notes |
|---|---|---|
| Grammar, spelling, punctuation, style | LanguageTool, local Java server, picky level | `language_tool_python` starts `languagetool-server.jar` on 127.0.0.1. `remote_server` is never passed, so there is no fallback to the public API: if the server cannot start, the report says "NOT RUN" and the run continues without it. |
| Wordiness, weasel words, cliches, repeated words, hedging | Vale with the `proselint`, `write-good` and `Microsoft` packages | Rules tuned in `tools/prose_rules/vale/.vale.ini`. |
| Journal rules | `tools/prose_rules/jes_rules.yml` and `jes_checks.py` | See below. |
| Hidden characters | `tools/prose_rules/hidden_chars.py` | Reports only. Scans the raw file, including comments and code. |
| Verbatim runs against cited papers | `tools/prose_rules/similarity.py` | 10 or more consecutive words shared with a text in `refs/fulltext`. Not a plagiarism service. |

Markdown and LaTeX are stripped before the grammar tools see the text: HTML comments, fenced code, front matter, math
(becomes `X`), code spans (`X`), pandoc citations (`[1]`), `[AUTHOR: ...]` and `[RESULT: ...]` placeholders (`X`),
links, emphasis marks, headings and table syntax. Every character keeps a map to its source offset, so each flag is
reported as `line:column` of the original file. Display equations join the sentence around them. Blockquote banners
and fenced code are skipped; headings and tables get only the word-level rules.

### Journal rules (`jes_rules.yml`, `jes_checks.py`)

- AI-tell vocabulary and phrases, taken from the `research-humanizer` skill (`references/ai-patterns-academic.md`,
  section B and patterns A1-A7, C2-C9, D1-D4), plus the words in the brief: delve, crucial, pivotal, showcase,
  underscore, leverage, robust (not flagged next to a statistical noun), seamless, intricate, realm, tapestry,
  "it is worth noting", "plays a crucial role". Three or more tells in one paragraph also raise a cluster flag.
- Rule of three (three adjectives; repeated three-item series), em-dash use and chains, trailing participles,
  negative parallelism, additive-connective stacking, flat sentence rhythm (length CV below 0.28).
- Claim words that need evidence: novel, first, "to the best of our knowledge", significant (silent when a test, p value
  or interval is in the sentence), outperforms or superior (silent when the sentence has a number), magnitude words,
  state-of-the-art without a citation, "prove".
- Length limits: sentence over 40 words (high over 60), paragraph over 200 words.
- Abbreviations: first use must be expanded, `Expansion (ABBR)` or `ABBR (expansion)`, checked across the manuscript
  files in the order given. Also reports "used before expanded" and "expansion written out again after definition".
  Labels such as `A15`, `PC-1`, product names such as `LightGBM`, and the list in `known_abbreviations` are exempt.
- Consistency: hyphen, space and joined forms of one term (closed-form / closed form), UK and US spelling pairs,
  `10 %` versus `10%`, straight versus curly quotes and apostrophes. Reported on the less frequent variant.
- Units and numbers: bare `35 C` (write `35 °C`), no space before a unit (`3.6V`), a physical quantity followed by a
  number with no unit ("temperature of 25").
- Style: contractions, double spaces (only spaces really present in the source), bare "This" opening a sentence,
  possible dangling modifier ("Using X, the error ..."), "There is/are" and "It is ... that" openers.
- Placeholders: every `[AUTHOR: ...]`, `[RESULT: ...]` style marker is listed once.
- Words inside quotation marks are not flagged by the style rules.

### Hidden characters

Zero-width characters, bidi controls (Trojan Source class), Unicode tag characters, variation selectors, soft hyphen,
control characters, replacement character, odd spaces (a no-break space is accepted between a number and its unit, a
following `%`, or after `Fig.`, `Section`, `Table`, `Eq.`), look-alike punctuation, fullwidth forms, mathematical
alphanumerics, and homoglyphs (Latin words mixed with Cyrillic or Greek letters; non-Latin scripts in a Latin text).
Nothing is fixed automatically.

## Rule choices

- **Spelling variant:** en-GB. The checker counts UK and US forms from a paired list in `jes_rules.yml`; this draft has
  16 UK forms (normalised, generalisation, optimisation, parametrisation, ...) and no US form, so `--lang auto` selects
  en-GB. LanguageTool rules `OXFORD_SPELLING_Z_NOT_S` (asks for -ize), `SERIAL_COMMA_ON` (the draft consistently omits
  the Oxford comma), `REP_PASSIVE_VOICE` (no passive-voice ban; passive is normal in Methods), and the curly-quote
  rules (handled by the typography check) are disabled.
- **Vale:** `write-good.Passive` and `E-Prime` off. `Microsoft.Contractions` is off because that style asks for
  contractions. Microsoft rules about UI text, dates, headings, units, first person and the like are off. In
  `write-good.TooWordy` single ordinary scientific words (evaluate, maximum, therefore, equivalent, ...) are ignored and
  only phrases and pompous words are kept. Details and the full list are in `.vale.ini` and `vale_ignore_text`.
- **LanguageTool misfires ignored:** `PEE_INSTALLED` (per-seed), `MULTIPLICATION_SIGN` on `D*`, `THE_SUPERLATIVE` on
  "least squares", `POSSESSIVE_APOSTROPHE` on the verb "beats". Spelling flags on identifier-shaped tokens (A15,
  LightGBM, k_full) are dropped.
- **Dictionary:** `tools/prose_rules/dictionary.txt`, one correct word per line (model names, authors, services). The
  report ends with the words LanguageTool did not know; add the correct ones there.
- **Working notes** (`00_open_items.md`, `CITATION_AUDIT.md`, `WRITER_*`, `refs_*`; list in `jes_rules.yml`) are
  checked and shown, but left out of the abbreviation and consistency pass and of the top-20 list.
- **Ranking:** score = severity weight (high 3, medium 2, low 1) x 10 + category priority (hidden characters 6;
  grammar, spelling, verbatim text 5; claims and abbreviations 4; ...). At most 5 per category and one per line.
- Duplicate flags from different tools on the same span are merged into one row that lists every rule.

To add a rule, append an entry to `word_rules` in `jes_rules.yml` (a regex list, category, severity, message,
suggestion, optional `skip_if` on the sentence). To silence a rule, add it to `languagetool.disabled_rules`,
`languagetool.ignore_rules`, `vale_ignore_text` or `.vale.ini`.

## Install on a new machine

1. Java 11 or newer (here: Temurin 17.0.19) and Python 3.10 or newer (here: 3.14.3 at `C:\Python314`).
2. Pure-Python dependencies into the project (so `-I` works): 
   `python -m pip install --target tools/bin/pylib language_tool_python==3.4.0 pyyaml`
3. Vale: download the official `vale_<version>_Windows_64-bit.zip` and `vale_<version>_checksums.txt` from the Vale
   release page, compare the SHA-256, unzip to `tools/bin/vale/`, then
   `tools/bin/vale/vale.exe --config=tools/prose_rules/vale/.vale.ini sync` (fetches the three style packages into
   `tools/prose_rules/vale/styles/`, which is committed so later runs need no network).
4. LanguageTool: the first run of `language_tool_python` downloads the official LanguageTool release zip to
   `~/.cache/language_tool_python/` and checks it against the SHA-256 in the library's `integrity.toml`. Use
   `--lt-path DIR` or `LTP_PATH` to keep it elsewhere.
5. Optional, for sentence parsing (rule of three, dangling modifiers, bare "This"): spaCy with `en_core_web_sm`. Under
   `-I` the user site is not searched, so `prose_check.py` adds the interpreter's user-site directory itself when spaCy
   is not importable and prints that in the report header. Without spaCy a regex sentence splitter is used and those
   three checks are skipped.
6. `python -I tools/prose_rules/selftest.py` should print `selftest: PASS`.

`tools/bin/` has its own `.gitignore` (binaries and the package folder are not committed).

## Versions and checksums (this machine, 2026-11-06)

| Component | Version | Checksum or source |
|---|---|---|
| Python | 3.14.3 | `C:\Python314` |
| Java | OpenJDK Temurin 17.0.19+10 | `java -version` |
| language_tool_python | 3.4.0 | PyPI, installed to `tools/bin/pylib` |
| LanguageTool server | 6.8 (folder `LanguageTool-6.8`) | server jar SHA-256 `f6d4a95d7756c5db334c255d77306b2b0f3cdb4a4621b7301bff7e8fa7c714fd`; the library checks the downloaded zip against its own `integrity.toml`. The cache already held 6.8, so this run downloaded nothing. |
| Vale | 3.26.0 | release zip SHA-256 `c42f4b413aa29b6b36fa4e3ac0c18322588a54ac860db4c84b8255997f7d1ec2` (matches the release `checksums.txt` and GitHub's asset digest); `vale.exe` SHA-256 `a4e0b17ea31fb61f3117f3171af502ff95f3467ca60d7097e6aa909928078c30`. Source: `github.com/vale-cli/vale/releases/tag/v3.26.0` (`errata-ai/vale` redirects there). |
| Vale packages | proselint (Vale port 0.1.0), write-good, Microsoft | fetched by `vale sync`; SHA-256 over the synced `styles/` tree `2e8a2c09b96e7a01547e7f9cd4b62959d90bdc579171f0111d5f4e7a8bf8f137` (changes if the rule files change) |
| PyYAML | 6.0.3 | `tools/bin/pylib` |
| spaCy / model | 3.8.13 / `en_core_web_sm` 3.8.0 | user site |
| proselint (PyPI) | 0.16.0 available, not installed | the Vale proselint package covers it; installing both would duplicate flags |

## Limits

- Grammar and style tools misfire on scientific prose; every row is a prompt to look. Math, code, citations and
  comments are replaced by neutral tokens, so the tools read an approximation of the text.
- The AI-phrasing and claim rules are heuristics. A clean report does not prove an AI detector will pass the text.
- The verbatim check compares only with texts under `refs/fulltext`. Run iThenticate or the university checker for a
  real similarity score.
- Elsevier's rule to define abbreviations separately in the abstract and the main text is not enforced (the abstract is
  not a separate file).
