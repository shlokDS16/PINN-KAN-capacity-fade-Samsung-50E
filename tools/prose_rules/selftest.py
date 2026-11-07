"""Positive-control self-test: python -I tools/prose_rules/selftest.py

Builds a small Markdown file that contains one known instance of each detector (the hidden
characters are written with escapes, so this source file stays clean), runs the checker on it and
fails if any expected rule is missing from the report.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOLS))

SAMPLE = (
    "# 1. Test\n\n"
    "The model plays a crucial role, and we delve into a robust, seamless tapestry. It is worth noting that the "
    "novel method outperforms all baselines, in order to be clear.\n\n"
    "Cells were cycled at 35 C and 3.6V; the temperature of 25 was held.  Two spaces here, and a bare This opens.\n\n"
    "The the model uses PINN and RMSE to assess it's results, which is significant. The PINN is trained on cells.\n\n"
    "Zero​width, bidi ‮ mark, tag \U000e0041, non-breaking space in a word, "
    "Cyrillic Раython, \"straight\" and “curly” quotes.\n\n"
    "He go to the store yesterday and buy a apples.\n\n"
    + ("This sentence keeps going with many plain words to pass the forty word limit and it does not stop "
       "until we have written more than forty words in a single unbroken run of text for the test, and then it goes on for several more plain words so that the count passes forty. ") + "\n"
)

EXPECT = [
    "zero-width", "bidi-control", "tag-char", "odd-space", "homoglyph-mixed-script",
    "ai-vocab-core", "significance-inflation", "claim-novel", "claim-outperform", "wordy-phrase",
    "temp-bare-C", "unit-no-space", "quantity-without-unit", "double-space", "contraction",
    "abbr-undefined", "claim-significant", "quote-style", "sentence-length",
]


def main() -> int:
    import prose_check

    with tempfile.TemporaryDirectory(prefix="prose_selftest_") as tmp:
        src = Path(tmp) / "sample.md"
        out = Path(tmp) / "report.md"
        src.write_text(SAMPLE, encoding="utf-8")
        prose_check.main([str(src), "--out", str(out), "--all-manuscript", "--no-similarity"])
        rep = out.read_text(encoding="utf-8")
    missing = [r for r in EXPECT if f"`{r}" not in rep and f"+ {r}" not in rep and f" {r}`" not in rep]
    lt_ok = "| Grammar |" in rep or "| Spelling |" in rep
    vale_ok = "write-good." in rep or "proselint." in rep or "Microsoft." in rep
    for r in missing:
        print("MISSING journal/hidden rule:", r)
    if not lt_ok:
        print("MISSING: no LanguageTool grammar or spelling flag (is Java available?)")
    if not vale_ok:
        print("MISSING: no Vale flag")
    print("selftest:", "FAIL" if (missing or not lt_ok or not vale_ok) else "PASS")
    return 1 if (missing or not lt_ok or not vale_ok) else 0


if __name__ == "__main__":
    sys.exit(main())
