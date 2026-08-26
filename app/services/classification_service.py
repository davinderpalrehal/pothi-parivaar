"""Heuristic LCC-class and Cutter-code suggestion for a book's shelf key.

Everything here is a small, checked-in heuristic table plus pure functions:
no DB access, no network calls, and never touches ``app/services/isbn_service.py``.
Classification is computed from a book's title, ``genres_tags``, and its
structured authors alone. The tables are deliberately simplified and are not
meant to match a real LCC or Cutter-Sanborn authority table -- see
``_bmad-output/implementation-artifacts/spec-2-1-lcc-cutter-shelf-key.md``
for the rationale.
"""
from __future__ import annotations

import re
from typing import Optional, Sequence

from app.models import Author, ClassificationSuggestion

# ==============================================================================
# Genre -> LCC class heuristic map
# ==============================================================================

# Fallback LCC class used whenever no keyword below matches -- "General Literature".
DEFAULT_LCC_CLASS = "PN"

# Ordered so multi-word / more specific keywords are checked before the generic
# single-word ones they contain (e.g. "science fiction" before "science").
GENRE_LCC_MAP: dict[str, str] = {
    "science fiction": "PZ",
    "sci-fi": "PZ",
    "fantasy": "PZ",
    "mystery": "PZ",
    "adventure": "PZ",
    "fiction": "PZ",
    "history": "D",
    "biography": "CT",
    "philosophy": "B",
    "religion": "BL",
    "psychology": "BF",
    "poetry": "PN",
    "art": "N",
    "music": "M",
    "business": "HF",
    "law": "K",
    "medicine": "R",
    "mathematics": "QA",
    "science": "Q",
    "cooking": "TX",
}


def suggest_lcc_class(genres_tags: Optional[str]) -> str:
    """Return a heuristic LCC class for comma-separated genre tags.

    Matches the first ``GENRE_LCC_MAP`` keyword found (case-insensitive
    substring match) anywhere in ``genres_tags``. Falls back to
    ``DEFAULT_LCC_CLASS`` when ``genres_tags`` is empty or nothing matches --
    never raises.
    """
    text = (genres_tags or "").strip().lower()
    if not text:
        return DEFAULT_LCC_CLASS
    for keyword, lcc_class in GENRE_LCC_MAP.items():
        if keyword in text:
            return lcc_class
    return DEFAULT_LCC_CLASS


# ==============================================================================
# Simplified Cutter code
# ==============================================================================

# a-z -> 2-9 in fixed groups (vowels get low digits, consonant clusters get
# higher ones). Exact digit assignments are an implementation choice; kept in
# one table so they're easy to inspect/adjust later.
CUTTER_DIGIT_TABLE: dict[str, int] = {
    "a": 2, "e": 2, "i": 2, "o": 2, "u": 2, "y": 2,
    "b": 3, "c": 3, "d": 3,
    "f": 4, "g": 4, "h": 4,
    "j": 5, "k": 5, "l": 5,
    "m": 6, "n": 6, "p": 6,
    "q": 7, "r": 7, "s": 7,
    "t": 8, "v": 8, "w": 8,
    "x": 9, "z": 9,
}


def suggest_cutter(source_text: str) -> str:
    """Build a simplified 3-character Cutter code (one letter + two digits).

    Strips non-letters from ``source_text``, uppercases the first remaining
    letter, then maps each subsequent letter through ``CUTTER_DIGIT_TABLE``
    (skipping immediate digit repeats) until two digits are collected.
    Pads with ``"0"`` if the source runs out of letters first, e.g.
    ``"Orwell"`` -> ``"O78"``, ``""`` -> ``"X00"``.
    """
    letters = re.sub(r"[^A-Za-z]", "", source_text or "")
    if not letters:
        return "X00"

    first = letters[0].upper()
    digits: list[str] = []
    last_digit: Optional[str] = None
    for ch in letters[1:].lower():
        digit_value = CUTTER_DIGIT_TABLE.get(ch)
        if digit_value is None:
            continue
        digit = str(digit_value)
        if digit == last_digit:
            continue
        digits.append(digit)
        last_digit = digit
        if len(digits) == 2:
            break
    while len(digits) < 2:
        digits.append("0")
    return f"{first}{''.join(digits)}"


# ==============================================================================
# Combined suggestion
# ==============================================================================

class AmbiguousAuthorError(Exception):
    """Raised when a book has 2+ authors and no ``primary_author_id`` was given."""

    def __init__(self, authors: Sequence[Author]):
        self.authors = list(authors)
        super().__init__("primary_author_id is required when a book has multiple authors")


class InvalidPrimaryAuthorError(Exception):
    """Raised when ``primary_author_id`` does not match any author linked to the book."""

    def __init__(self, primary_author_id: int):
        self.primary_author_id = primary_author_id
        super().__init__(f"primary_author_id {primary_author_id} is not linked to this book")


def resolve_cutter_source(
    title: str,
    authors: Sequence[Author],
    primary_author_id: Optional[int],
) -> str:
    """Pick the text the Cutter code should be derived from.

    Zero authors -> the title. Exactly one author -> that author's last name.
    Multiple authors -> ``primary_author_id`` must match one of them. Any
    ``primary_author_id`` that doesn't apply to the book's actual author
    count/membership is rejected rather than silently ignored.
    """
    if not authors:
        if primary_author_id is not None:
            raise InvalidPrimaryAuthorError(primary_author_id)
        return title
    if len(authors) == 1:
        if primary_author_id is not None and authors[0].id != primary_author_id:
            raise InvalidPrimaryAuthorError(primary_author_id)
        return authors[0].last_name
    if primary_author_id is None:
        raise AmbiguousAuthorError(authors)
    for author in authors:
        if author.id == primary_author_id:
            return author.last_name
    raise InvalidPrimaryAuthorError(primary_author_id)


def suggest_classification(
    title: str,
    genres_tags: Optional[str],
    authors: Sequence[Author],
    primary_author_id: Optional[int] = None,
) -> ClassificationSuggestion:
    """Compute a full shelf-key suggestion: heuristic LCC class + Cutter code.

    Pure and deterministic for the same input. Never persists anything --
    callers write the result to ``Book.lcc_call_number``/``cutter_number``
    only after a human confirms it via the existing ``PUT /books/{id}`` path.
    """
    cutter_source = resolve_cutter_source(title, authors, primary_author_id)
    return ClassificationSuggestion(
        lcc_call_number=suggest_lcc_class(genres_tags),
        cutter_number=suggest_cutter(cutter_source),
    )
