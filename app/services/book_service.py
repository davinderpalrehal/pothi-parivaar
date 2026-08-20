from typing import Optional
from sqlmodel import Session, select, or_
from app.models import Book, BookCreate, BookUpdate, ReadingSession


def create_book(session: Session, book_in: BookCreate) -> Book:
    """Create a new book record. Does not call ISBN lookup."""
    book = Book.model_validate(book_in)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


def get_book(session: Session, book_id: int) -> Optional[Book]:
    """Retrieve a single book by ID."""
    return session.get(Book, book_id)


def _session_book_ids(session: Session, session_status: str) -> set[int]:
    rows = session.exec(
        select(ReadingSession.book_id).where(ReadingSession.status == session_status)
    ).all()
    return set(rows)


def list_books(
    session: Session,
    query: Optional[str] = None,
    genre: Optional[str] = None,
    room: Optional[str] = None,
    book_format: Optional[str] = None,
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
) -> list[Book]:
    """List books with optional keyword search and AND filters."""
    statement = select(Book)

    if query:
        search_pattern = f"%{query}%"
        statement = statement.where(
            or_(
                Book.title.ilike(search_pattern),
                Book.author.ilike(search_pattern),
                Book.summary.ilike(search_pattern),
                Book.isbn.ilike(search_pattern),
                Book.genres_tags.ilike(search_pattern),
            )
        )

    if genre:
        statement = statement.where(Book.genres_tags.ilike(f"%{genre}%"))

    if room:
        statement = statement.where(Book.location_room == room)

    if book_format:
        statement = statement.where(Book.formats.ilike(f"%{book_format}%"))

    if status:
        reading_ids = _session_book_ids(session, "reading")
        if status == "reading":
            if not reading_ids:
                return []
            statement = statement.where(Book.id.in_(reading_ids))
        elif status == "finished":
            finished_ids = _session_book_ids(session, "finished") - reading_ids
            if not finished_ids:
                return []
            statement = statement.where(Book.id.in_(finished_ids))
        elif status == "available":
            if reading_ids:
                statement = statement.where(Book.id.not_in(reading_ids))

    statement = statement.offset(offset).limit(limit).order_by(Book.id.desc())
    return list(session.exec(statement).all())


def update_book(session: Session, book: Book, book_update: BookUpdate) -> Book:
    """Update fields on an existing book."""
    update_data = book_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


def delete_book(session: Session, book: Book) -> None:
    """Delete a book and any reading sessions attached to it."""
    sessions = session.exec(select(ReadingSession).where(ReadingSession.book_id == book.id)).all()
    for reading_session in sessions:
        session.delete(reading_session)
    session.flush()
    session.delete(book)
    session.commit()
