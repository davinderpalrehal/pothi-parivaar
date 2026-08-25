"""Split and display rules for author strings (name-rules.md)."""

from dataclasses import dataclass
from typing import Optional


MONONYM_LAST = " "


@dataclass(frozen=True)
class AuthorName:
    first_name: str
    last_name: str
    middle_name: Optional[str] = None


def split_author_string(raw: Optional[str]) -> list[AuthorName]:
    """Split a stored or API author string into name parts.

    1. Split on ``,`` and trim; drop empty segments.
    2. Split each segment on ASCII space; drop empty tokens.
    3. No tokens → skip. One token → mononym (last is a single space).
    4. Two or more → first / last tokens, leftover tokens as middle.
    """
    if raw is None:
        return []

    authors: list[AuthorName] = []
    for segment in raw.split(","):
        segment = segment.strip()
        if not segment:
            continue
        tokens = [token for token in segment.split(" ") if token]
        if not tokens:
            continue
        if len(tokens) == 1:
            authors.append(AuthorName(first_name=tokens[0], last_name=MONONYM_LAST))
            continue
        middle = " ".join(tokens[1:-1]) or None
        authors.append(
            AuthorName(first_name=tokens[0], last_name=tokens[-1], middle_name=middle)
        )
    return authors


def author_short_form(first_name: str, last_name: str) -> str:
    """Catalog short form: ``D. Carnegie``, or the first name as-is for a mononym."""
    if last_name == MONONYM_LAST:
        return first_name
    if not first_name:
        return last_name
    return f"{first_name[0]}. {last_name}"


def joined_short_forms(names: list[AuthorName]) -> str:
    """Comma-separated short forms in the given order."""
    return ", ".join(
        author_short_form(name.first_name, name.last_name) for name in names
    )
