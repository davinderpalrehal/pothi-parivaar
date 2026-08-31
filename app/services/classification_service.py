"""Heuristic LCC-class and Cutter-code suggestion for a book's shelf key.

Everything here is a small, checked-in heuristic table plus pure functions:
no DB access, no network calls, and never touches ``app/services/isbn_service.py``.
Classification is computed from a book's title, ``genres_tags``, and its
structured authors alone. The class heuristic reads ``genres_tags`` first and
then falls back to the *title*, because most of this collection carries no
genre tags at all; the Cutter code still comes from the author/title source
picked by :func:`resolve_cutter_source`. The tables are deliberately
simplified and are not meant to match a real LCC or Cutter-Sanborn authority
table -- see
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


# ==============================================================================
# Domain-tuned keyword -> LCC class map
# ==============================================================================

# Searched *before* ``GENRE_LCC_MAP`` so this library's own subjects win over
# the generic literary buckets. Order is the design and is load-bearing twice
# over:
#   * specific before generic -- "language models" before "computer",
#     "world records" before the plain reference classes;
#   * subject before audience -- a juvenile book about a Sikh subject is
#     ``BL2017``, not ``PZ``, so every Sikh keyword precedes "bed time" and
#     friends.
# Deliberately excluded: proper names of individual works ("cinderella",
# "aladdin"). That set is unbounded, and those titles are meant to fall through
# and be flagged for a human instead.
DOMAIN_LCC_MAP: tuple[tuple[str, str], ...] = (
    # Sikh religion -- the largest part of the collection.
    ("gurbani", "BL2017"),
    ("sikhism", "BL2017"),
    ("sikh", "BL2017"),
    ("guru", "BL2017"),
    ("gurmukhi", "BL2017"),
    ("gurmukh", "BL2017"),
    ("guramukha", "BL2017"),
    ("bhai", "BL2017"),
    ("sahibzada", "BL2017"),
    ("bara maha", "BL2017"),
    ("khalsa", "BL2017"),
    # Other Indic religion.
    ("hindu", "BL1100"),
    ("vedic", "BL1100"),
    ("veda", "BL1100"),
    ("buddha", "BQ"),
    # "buddhist" before the "buddh" base: the suffix rule absorbs only ONE
    # suffix, so "buddh"+ist cannot also take the plural in "Buddhists".
    ("buddhist", "BQ"),
    ("buddh", "BQ"),
    # Juvenile / activity.
    ("colouring", "PZ"),
    ("coloring", "PZ"),
    ("color", "PZ"),
    ("trace", "PZ"),
    ("sticker", "PZ"),
    ("storybook", "PZ"),
    ("bed time", "PZ"),
    ("bedtime", "PZ"),
    ("activity book", "PZ"),
    ("juvenile", "PZ"),
    ("fairy", "PZ8"),
    ("children", "PZ"),
    # Schoolwork / workbooks.
    ("math", "QA"),
    ("workbook", "LB"),
    ("spelling", "LB1573"),
    ("crossword", "GV1507"),
    # Reference.
    ("world records", "AG"),
    ("wonders of the world", "AG"),
    ("wonders of the word", "AG"),
    ("encyclopedia", "AE"),
    # Comics and Indic literature.
    ("comic", "PN6790"),
    ("kalidasa", "PK"),
    ("panjabi", "PK"),
    ("punjabi", "PK"),
    ("plays", "PK"),
    # Science and technology.
    ("language models", "QA76"),
    ("computer", "QA76"),
    ("human body", "QP"),
    ("ocean", "QL"),
)

# Compiled once at import: matching runs on every suggest call, and rebuilding
# ~50 patterns per call would be pure waste.
#
# Word-boundary matching (not bare substring) is what makes the domain table
# safe against free-text titles. Verified false positives it kills:
# "A Journey Through Colorado" (color), "The Temples of Mathura" / "Aftermath
# of War" (math), "The Brain Displays Its Power" (plays), "Traceability in
# Supply Chains" (trace), "Watercolor Painting" (color).
#
# Regular plural/-ism/-ist inflections are absorbed by the pattern below, so
# they are NOT enumerated here. Only forms the suffix rule cannot reach are
# listed separately: "vedic" (not "veda"+suffix), "gurmukhi" (not
# "gurmukh"+suffix), "colouring"/"coloring" (-ing is not a suffix the rule
# absorbs), and "buddha" alongside the "buddh" base.
# Absorbs the common inflections of a keyword so the table does not have to
# enumerate them: "comic" reaches *Indian Comics Anthology*, "guru" reaches
# *Lives of the Gurus*, "veda" reaches *The Four Vedas*, "buddh" reaches
# *Buddhism Today*. It does NOT loosen the boundary guard -- every false
# positive listed above stays default, because none of them is the keyword
# plus one of these suffixes.
_KEYWORD_SUFFIXES = r"(?:s|es|ism|ist)?"

_DOMAIN_PATTERNS: tuple[tuple[re.Pattern[str], str, str], ...] = tuple(
    (
        re.compile(rf"\b{re.escape(keyword)}{_KEYWORD_SUFFIXES}\b", re.IGNORECASE),
        keyword,
        lcc_class,
    )
    for keyword, lcc_class in DOMAIN_LCC_MAP
)

# Values ``LccClassMatch.source`` can take: which text produced the match, or
# ``"default"`` when nothing did.
CLASS_SOURCE_GENRES = "genres"
CLASS_SOURCE_TITLE = "title"
CLASS_SOURCE_DEFAULT = "default"


class LccClassMatch(str):
    """An LCC class plus the provenance of the keyword that produced it.

    Subclasses ``str`` on purpose: the value *is* the class, so every existing
    caller and assertion that treats the result as a plain string keeps
    working, while ``source``/``matched_keyword`` let the UI tell a real match
    apart from the ``DEFAULT_LCC_CLASS`` fallback.

    **Known limitation:** only the instance itself carries the provenance. Any
    ``str`` operation -- ``.upper()``, ``.strip()``, slicing, concatenation,
    ``"".join(...)`` -- returns a plain ``str`` and silently drops ``source``
    and ``matched_keyword``. Read the attributes off the returned object
    before transforming it. Copying and pickling *are* supported, via
    ``__getnewargs__``.
    """

    source: str
    matched_keyword: Optional[str]

    def __new__(
        cls,
        lcc_class: str,
        source: str = CLASS_SOURCE_DEFAULT,
        matched_keyword: Optional[str] = None,
    ) -> "LccClassMatch":
        instance = super().__new__(cls, lcc_class)
        instance.source = source
        instance.matched_keyword = matched_keyword
        return instance

    def __getnewargs__(self) -> tuple[str, str, Optional[str]]:
        # copy.copy / copy.deepcopy / pickle reconstruct str subclasses through
        # __new__; without this they'd call it with the class string alone.
        return (str(self), self.source, self.matched_keyword)


def _match_domain_table(text: str, source: str) -> Optional["LccClassMatch"]:
    """First domain-table keyword occurring as a whole word in ``text``."""
    for pattern, keyword, lcc_class in _DOMAIN_PATTERNS:
        if pattern.search(text):
            return LccClassMatch(lcc_class, source, keyword)
    return None


def suggest_lcc_class(
    genres_tags: Optional[str],
    title: Optional[str] = None,
) -> LccClassMatch:
    """Return a heuristic LCC class for a book's genre tags and/or title.

    ``genres_tags`` is exhausted first -- through ``DOMAIN_LCC_MAP`` and then
    ``GENRE_LCC_MAP`` -- and only if it yields nothing is ``title`` tried,
    against the domain table alone. Genre tags are the deliberate, curated
    signal, so any tag match outranks a title match: a book tagged "Cooking"
    stays ``TX`` even when its title mentions a Sikh subject.

    Within the domain table order is the design -- specific before generic and
    subject before audience -- so "Bed time stories 4 - Guru Tegh Bahadur ji"
    reaches ``BL2017`` rather than ``PZ``.

    ``GENRE_LCC_MAP`` is deliberately **never** matched against ``title``. Its
    entries are bare substrings tuned for a curated tag vocabulary, so against
    free text they misfire badly -- "art" hits *Heartland*, *Smart Kids* and
    *A Part of the Story*; "law" hits *Lawrence of Arabia*. Titles are matched
    only by the domain table, whose keywords are matched on word boundaries.

    Falls back to ``DEFAULT_LCC_CLASS`` with ``source == "default"`` when both
    inputs are empty or nothing matches -- never raises. The result is a
    ``str`` subclass, so it compares equal to the bare class string.
    """
    genres_text = (genres_tags or "").strip().lower()
    title_text = (title or "").strip().lower()

    if genres_text:
        match = _match_domain_table(genres_text, CLASS_SOURCE_GENRES)
        if match is not None:
            return match
        # Legacy table: genre tags only -- see the docstring for why.
        for keyword, lcc_class in GENRE_LCC_MAP.items():
            if keyword in genres_text:
                return LccClassMatch(lcc_class, CLASS_SOURCE_GENRES, keyword)

    if title_text:
        match = _match_domain_table(title_text, CLASS_SOURCE_TITLE)
        if match is not None:
            return match

    return LccClassMatch(DEFAULT_LCC_CLASS, CLASS_SOURCE_DEFAULT, None)


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

    ``title`` feeds both halves: the class heuristic falls back to it when
    ``genres_tags`` yields nothing, and it is the Cutter source for an
    author-less book. Pure and deterministic for the same input. Never persists anything --
    callers write the result to ``Book.lcc_call_number``/``cutter_number``
    only after a human confirms it via the existing ``PUT /books/{id}`` path.
    """
    cutter_source = resolve_cutter_source(title, authors, primary_author_id)
    lcc_class = suggest_lcc_class(genres_tags, title)
    return ClassificationSuggestion(
        lcc_call_number=str(lcc_class),
        cutter_number=suggest_cutter(cutter_source),
        class_source=lcc_class.source,
        class_matched_keyword=lcc_class.matched_keyword,
    )
