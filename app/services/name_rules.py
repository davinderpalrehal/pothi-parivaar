"""Split and display rules for author strings (name-rules.md)."""

from dataclasses import dataclass
from typing import Literal, Optional, Sequence


MONONYM_LAST = " "
HonorificRole = Literal["prefix", "suffix"]


@dataclass(frozen=True)
class AuthorName:
    first_name: str
    last_name: str
    middle_name: Optional[str] = None


@dataclass(frozen=True)
class HonorificRule:
    tokens: tuple[str, ...]
    role: HonorificRole
    abbreviation: str


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


def _space_tokens(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [token for token in value.split(" ") if token]


def reconstruct_tokens(first_name: str, last_name: str, middle_name: Optional[str] = None) -> list[str]:
    tokens = _space_tokens(first_name) + _space_tokens(middle_name)
    if last_name != MONONYM_LAST:
        tokens.extend(_space_tokens(last_name))
    return tokens


def _norm_token(token: str) -> str:
    stripped = token.strip().lower()
    if stripped.endswith("."):
        stripped = stripped[:-1]
    return stripped


def _tokens_match(sequence: Sequence[str], start: int, honorific_tokens: Sequence[str]) -> bool:
    count = len(honorific_tokens)
    if start < 0 or start + count > len(sequence):
        return False
    return all(
        _norm_token(sequence[start + index]) == _norm_token(honorific_tokens[index])
        for index in range(count)
    )


def _peel_honorifics(
    tokens: list[str], honorifics: Sequence[HonorificRule]
) -> tuple[list[str], list[str], list[str]]:
    remaining = list(tokens)
    prefix_abbrevs: list[str] = []
    suffix_abbrevs: list[str] = []
    enabled = [rule for rule in honorifics if rule.tokens]
    prefixes = sorted(
        [rule for rule in enabled if rule.role == "prefix"],
        key=lambda rule: len(rule.tokens),
        reverse=True,
    )
    suffixes = sorted(
        [rule for rule in enabled if rule.role == "suffix"],
        key=lambda rule: len(rule.tokens),
        reverse=True,
    )

    while remaining:
        matched = False
        for rule in prefixes:
            if _tokens_match(remaining, 0, rule.tokens):
                remaining = remaining[len(rule.tokens) :]
                if rule.abbreviation:
                    prefix_abbrevs.append(rule.abbreviation)
                matched = True
                break
        if matched:
            continue
        for rule in suffixes:
            start = len(remaining) - len(rule.tokens)
            if _tokens_match(remaining, start, rule.tokens):
                remaining = remaining[:start]
                if rule.abbreviation:
                    suffix_abbrevs.append(rule.abbreviation)
                matched = True
                break
        if not matched:
            break
    suffix_abbrevs.reverse()
    return remaining, prefix_abbrevs, suffix_abbrevs


def _join_parts(*parts: Sequence[str] | str) -> str:
    tokens: list[str] = []
    for part in parts:
        if isinstance(part, str):
            if part:
                tokens.append(part)
        else:
            tokens.extend(token for token in part if token)
    return " ".join(tokens)


def author_short_form(
    first_name: str,
    last_name: str,
    middle_name: Optional[str] = None,
    honorifics: Optional[Sequence[HonorificRule]] = None,
) -> str:
    """Catalog short form including peeled honorifics (name-rules.md)."""
    rules = list(honorifics or [])
    reconstructed = reconstruct_tokens(first_name, last_name, middle_name)
    personal, prefixes, suffixes = _peel_honorifics(reconstructed, rules)

    if not personal:
        return _join_parts(prefixes, suffixes) or first_name

    if last_name == MONONYM_LAST and len(personal) == 1:
        core = personal[0]
    else:
        core = f"{personal[0][0]}. {personal[-1]}" if personal[0] else personal[-1]

    return _join_parts(prefixes, core, suffixes)


def joined_short_forms(
    names: list[AuthorName],
    honorifics: Optional[Sequence[HonorificRule]] = None,
) -> str:
    """Comma-separated short forms in the given order."""
    return ", ".join(
        author_short_form(
            name.first_name,
            name.last_name,
            name.middle_name,
            honorifics,
        )
        for name in names
    )
