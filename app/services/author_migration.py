"""One-time conversion of existing Book.author strings into author records."""

from sqlmodel import Session, select

from app.models import Book, BookAuthor
from app.services.book_service import _replace_book_authors
from app.services.name_rules import split_author_string


def migrate_book_author_strings(session: Session) -> int:
    """Apply name-rules.md to every book that still has no author links.

    Empty or missing ``Book.author`` yields zero authors. ``D. Carnegie``
    becomes first=``D.``, last=``Carnegie``. Idempotent: books that already
    have ``BookAuthor`` rows are left unchanged. Publishers are not created.
    """
    linked_ids = set(session.exec(select(BookAuthor.book_id)).all())
    books = list(session.exec(select(Book)).all())
    converted = 0
    dirty = False
    for book in books:
        if book.id in linked_ids:
            continue
        names = split_author_string(book.author)
        if not names:
            # Empty string is already the zero-author end state.
            if book.author != "":
                book.author = ""
                session.add(book)
                dirty = True
            continue
        _replace_book_authors(session, book, names)
        session.add(book)
        converted += 1
        dirty = True
    if dirty:
        session.commit()
    return converted
