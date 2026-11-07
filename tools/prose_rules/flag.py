"""Shared data types for the prose checker."""
from __future__ import annotations

from dataclasses import dataclass, field

SEVERITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}

# Report categories, in the order they appear in summaries.
CATEGORIES = [
    "Hidden characters",
    "Grammar",
    "Spelling",
    "Punctuation",
    "Paraphrase needed",
    "Claim needs evidence",
    "AI-sounding phrasing",
    "Clarity",
    "Wordiness",
    "Weak or hedged wording",
    "Abbreviation",
    "Units and numbers",
    "Consistency",
    "Typography",
    "Style",
    "Placeholder",
]

# Priority bonus used only to rank the "top 20 to fix first" list.
CATEGORY_PRIORITY = {
    "Hidden characters": 6,
    "Grammar": 5,
    "Spelling": 5,
    "Paraphrase needed": 5,
    "Claim needs evidence": 4,
    "Abbreviation": 4,
    "Punctuation": 3,
    "Units and numbers": 3,
    "AI-sounding phrasing": 3,
    "Clarity": 3,
    "Wordiness": 2,
    "Weak or hedged wording": 2,
    "Consistency": 2,
    "Typography": 1,
    "Style": 1,
    "Placeholder": 0,
}


@dataclass
class Flag:
    file: str
    line: int
    col: int
    start: int  # offset into the original file text
    end: int
    category: str
    rule: str
    message: str
    suggestion: str
    text: str  # short display snippet
    severity: str = "medium"
    source: str = ""  # languagetool | vale | jes | hidden | similarity
    manuscript: bool = True
    extra: dict = field(default_factory=dict)

    @property
    def score(self) -> int:
        return SEVERITY_WEIGHT.get(self.severity, 1) * 10 + CATEGORY_PRIORITY.get(self.category, 0)
