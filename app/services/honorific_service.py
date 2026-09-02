"""Honorific list: uniqueness on tokens+role, seed, and Book.author refresh."""

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import Author, Book, BookAuthor, Honorific
from app.services.honorific_seed import HONORIFIC_SEED
from app.services.name_rules import AuthorName, HonorificRule, joined_short_forms

HONORIFIC_TOKEN_ROLE_INDEX = "ix_honorific_tokens_role_normalized"
HONORIFIC_TOKEN_ROLE_INDEX_SQL = (
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_honorific_tokens_role_normalized "
    "ON honorific (lower(trim(tokens)), lower(trim(role)))"
)


def normalize_tokens(tokens: str) -> str:
    return " ".join((tokens or "").split())


def _norm_key(tokens: str, role: str) -> tuple[str, str]:
    parts = [
        token[:-1].lower() if token.lower().endswith(".") else token.lower()
        for token in normalize_tokens(tokens).split(" ")
        if token
    ]
    return (" ".join(parts), (role or "").strip().lower())


def honorific_to_rule(row: Honorific) -> HonorificRule:
    parts = tuple(token for token in normalize_tokens(row.tokens).split(" ") if token)
    role = "suffix" if (row.role or "").strip().lower() == "suffix" else "prefix"
    return HonorificRule(tokens=parts, role=role, abbreviation=row.abbreviation or "")


def load_enabled_honorifics(session: Session) -> list[HonorificRule]:
    rows = session.exec(select(Honorific).where(Honorific.enabled == True)).all()  # noqa: E712
    return [honorific_to_rule(row) for row in rows]


def find_honorific(session: Session, tokens: str, role: str) -> Optional[Honorific]:
    target = _norm_key(tokens, role)
    for row in session.exec(select(Honorific)).all():
        if _norm_key(row.tokens, row.role) == target:
            return row
    return None


def list_honorifics(session: Session) -> list[Honorific]:
    return list(
        session.exec(
            select(Honorific).order_by(Honorific.role, Honorific.tokens, Honorific.id)
        ).all()
    )


def seed_honorifics_if_empty(session: Session) -> int:
    existing = session.exec(select(Honorific.id)).first()
    if existing is not None:
        return 0
    count = 0
    for tokens, role, abbreviation in HONORIFIC_SEED:
        session.add(
            Honorific(
                tokens=tokens,
                role=role,
                abbreviation=abbreviation,
                enabled=True,
            )
        )
        count += 1
    session.flush()
    return count


def refresh_book_author_projections(session: Session) -> None:
    rules = load_enabled_honorifics(session)
    books = list(session.exec(select(Book)).all())
    for book in books:
        authors = session.exec(
            select(Author)
            .join(BookAuthor, BookAuthor.author_id == Author.id)
            .where(BookAuthor.book_id == book.id)
            .order_by(BookAuthor.display_order, Author.id)
        ).all()
        names = [
            AuthorName(
                first_name=author.first_name,
                last_name=author.last_name,
                middle_name=author.middle_name,
            )
            for author in authors
        ]
        book.author = joined_short_forms(names, rules)
        session.add(book)
    session.flush()


def create_honorific(
    session: Session,
    tokens: str,
    role: str,
    abbreviation: str = "",
    enabled: bool = True,
) -> Honorific:
    cleaned = normalize_tokens(tokens)
    if find_honorific(session, cleaned, role):
        raise ValueError("duplicate tokens and role")
    row = Honorific(
        tokens=cleaned,
        role=role,
        abbreviation=abbreviation or "",
        enabled=enabled,
    )
    try:
        with session.begin_nested():
            session.add(row)
            session.flush()
    except IntegrityError as exc:
        if find_honorific(session, cleaned, role):
            raise ValueError("duplicate tokens and role") from exc
        raise
    refresh_book_author_projections(session)
    return row


def update_honorific(
    session: Session,
    row: Honorific,
    tokens: Optional[str] = None,
    role: Optional[str] = None,
    abbreviation: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> Honorific:
    next_tokens = normalize_tokens(tokens) if tokens is not None else row.tokens
    next_role = role if role is not None else row.role
    duplicate = find_honorific(session, next_tokens, next_role)
    if duplicate and duplicate.id != row.id:
        raise ValueError("duplicate tokens and role")
    row.tokens = next_tokens
    row.role = next_role
    if abbreviation is not None:
        row.abbreviation = abbreviation
    if enabled is not None:
        row.enabled = enabled
    session.add(row)
    try:
        with session.begin_nested():
            session.flush()
    except IntegrityError as exc:
        raise ValueError("duplicate tokens and role") from exc
    refresh_book_author_projections(session)
    return row


def delete_honorific(session: Session, row: Honorific) -> None:
    session.delete(row)
    session.flush()
    refresh_book_author_projections(session)
