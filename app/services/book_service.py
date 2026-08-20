from typing import Optional
from sqlmodel import Session, select, or_
from app.models import Book, BookCreate, BookUpdate


def create_book(session: Session, book_in: BookCreate) -> Book:
    """Create a new book record."""
    book = Book.model_validate(book_in)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


def get_book(session: Session, book_id: int) -> Optional[Book]:
    """Retrieve a single book by ID."""
    return session.get(Book, book_id)


def list_books(
    session: Session,
    query: Optional[str] = None,
    genre: Optional[str] = None,
    room: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
) -> list[Book]:
    """List books with optional text search and tag/room filtering."""
    statement = select(Book)

    if query:
        search_pattern = f"%{query}%"
        statement = statement.where(
            or_(
                Book.title.ilike(search_pattern),
                Book.author.ilike(search_pattern),
                Book.summary.ilike(search_pattern),
                Book.isbn.ilike(search_pattern),
            )
        )

    if genre:
        statement = statement.where(Book.genres_tags.ilike(f"%{genre}%"))

    if room:
        statement = statement.where(Book.location_room == room)

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
    """Delete a book from the database."""
    session.delete(book)
    session.commit()
