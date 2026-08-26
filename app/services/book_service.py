from typing import Optional
from sqlmodel import Session, select, or_, col
from app.models import (
    Author,
    AuthorInput,
    AuthorRead,
    Book,
    BookAuthor,
    BookCreate,
    BookRead,
    BookUpdate,
    Publisher,
    PublisherRead,
    ReadingSession,
)
from app.services.location_service import upsert_location
from app.services.name_rules import (
    AuthorName,
    joined_short_forms,
    split_author_string,
)


_BOOK_LINK_FIELDS = {"authors", "publisher_name", "author"}


def _strip_optional_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def _apply_location_strip(book: Book) -> None:
    book.location_room = _strip_optional_str(book.location_room)
    book.location_unit = _strip_optional_str(book.location_unit)
    book.location_shelf = _strip_optional_str(book.location_shelf)


def _sync_location_registry(session: Session, book: Book) -> None:
    room = book.location_room or ""
    if not room:
        return
    upsert_location(session, room, book.location_unit or "", book.location_shelf or "")


def _author_name_from_input(author_in: AuthorInput) -> AuthorName:
    return AuthorName(
        first_name=author_in.first_name,
        last_name=author_in.last_name,
        middle_name=author_in.middle_name,
    )


def get_or_create_author(session: Session, name: AuthorName) -> Author:
    statement = select(Author).where(
        Author.first_name == name.first_name,
        Author.last_name == name.last_name,
    )
    if name.middle_name is None:
        statement = statement.where(col(Author.middle_name).is_(None))
    else:
        statement = statement.where(Author.middle_name == name.middle_name)
    existing = session.exec(statement).first()
    if existing:
        return existing
    author = Author(
        first_name=name.first_name,
        middle_name=name.middle_name,
        last_name=name.last_name,
    )
    session.add(author)
    session.flush()
    return author


def get_or_create_publisher(session: Session, name: str) -> Publisher:
    existing = session.exec(select(Publisher).where(Publisher.name == name)).first()
    if existing:
        return existing
    publisher = Publisher(name=name)
    session.add(publisher)
    session.flush()
    return publisher


def list_book_authors(session: Session, book_id: int) -> list[Author]:
    rows = session.exec(
        select(Author)
        .join(BookAuthor, BookAuthor.author_id == Author.id)
        .where(BookAuthor.book_id == book_id)
        .order_by(BookAuthor.display_order, Author.id)
    ).all()
    return list(rows)


def _dedupe_author_names(names: list[AuthorName]) -> list[AuthorName]:
    """Keep first-seen first/middle/last so one book cannot link the same author twice."""
    unique: list[AuthorName] = []
    seen: set[AuthorName] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        unique.append(name)
    return unique


def _replace_book_authors(session: Session, book: Book, names: list[AuthorName]) -> None:
    existing_links = session.exec(
        select(BookAuthor).where(BookAuthor.book_id == book.id)
    ).all()
    for link in existing_links:
        session.delete(link)
    session.flush()
    unique_names = _dedupe_author_names(names)
    for order, name in enumerate(unique_names):
        author = get_or_create_author(session, name)
        session.add(
            BookAuthor(book_id=book.id, author_id=author.id, display_order=order)
        )
    book.author = joined_short_forms(unique_names)


def _set_publisher(session: Session, book: Book, publisher_name: Optional[str]) -> None:
    cleaned = _strip_optional_str(publisher_name)
    if not cleaned:
        book.publisher_id = None
        return
    publisher = get_or_create_publisher(session, cleaned)
    book.publisher_id = publisher.id


def _names_from_write(
    authors: Optional[list[AuthorInput]],
    author_string: Optional[str],
) -> list[AuthorName]:
    if authors is not None:
        return [_author_name_from_input(item) for item in authors]
    return split_author_string(author_string)


def _current_author_names(session: Session, book: Book) -> list[AuthorName]:
    return [
        AuthorName(
            first_name=author.first_name,
            last_name=author.last_name,
            middle_name=author.middle_name,
        )
        for author in list_book_authors(session, book.id)
    ]


def author_name_book_id_query(pattern: str):
    """Subquery of book ids whose author name parts match ``pattern`` (ILIKE)."""
    return (
        select(BookAuthor.book_id)
        .join(Author, Author.id == BookAuthor.author_id)
        .where(
            or_(
                Author.first_name.ilike(pattern),
                Author.middle_name.ilike(pattern),
                Author.last_name.ilike(pattern),
            )
        )
    )


def to_book_read(session: Session, book: Book) -> BookRead:
    authors = list_book_authors(session, book.id)
    publisher = session.get(Publisher, book.publisher_id) if book.publisher_id else None
    derived = joined_short_forms(
        [
            AuthorName(
                first_name=author.first_name,
                last_name=author.last_name,
                middle_name=author.middle_name,
            )
            for author in authors
        ]
    )
    return BookRead(
        id=book.id,
        title=book.title,
        author=derived,
        authors=[AuthorRead.model_validate(author) for author in authors],
        publisher=PublisherRead.model_validate(publisher) if publisher else None,
        publication_year=book.publication_year,
        isbn=book.isbn,
        summary=book.summary,
        cover_url=book.cover_url,
        page_count=book.page_count,
        genres_tags=book.genres_tags,
        formats=book.formats,
        location_room=book.location_room,
        location_unit=book.location_unit,
        location_shelf=book.location_shelf,
        read_count=book.read_count,
        created_at=book.created_at,
        lcc_call_number=book.lcc_call_number,
        cutter_number=book.cutter_number,
    )


def create_book(session: Session, book_in: BookCreate) -> Book:
    """Create a new book record. Does not call ISBN lookup."""
    data = book_in.model_dump(exclude=_BOOK_LINK_FIELDS)
    book = Book.model_validate(data)
    book.author = ""
    _apply_location_strip(book)
    session.add(book)
    session.flush()
    names = _names_from_write(book_in.authors, book_in.author)
    _replace_book_authors(session, book, names)
    _set_publisher(session, book, book_in.publisher_name)
    _sync_location_registry(session, book)
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
                Book.id.in_(author_name_book_id_query(search_pattern)),
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
    author_string = update_data.pop("author", None)
    authors_were_set = "authors" in update_data
    update_data.pop("authors", None)
    publisher_name_set = "publisher_name" in update_data
    publisher_name = update_data.pop("publisher_name", None)

    for field, value in update_data.items():
        setattr(book, field, value)
    _apply_location_strip(book)

    if authors_were_set:
        names = [_author_name_from_input(item) for item in (book_update.authors or [])]
        _replace_book_authors(session, book, names)
    elif author_string is not None:
        current_derived = joined_short_forms(_current_author_names(session, book))
        if (author_string or "").strip() != current_derived:
            _replace_book_authors(session, book, split_author_string(author_string))

    if publisher_name_set:
        _set_publisher(session, book, publisher_name)

    session.add(book)
    _sync_location_registry(session, book)
    session.commit()
    session.refresh(book)
    return book


def delete_book(session: Session, book: Book) -> None:
    """Delete a book and any reading sessions attached to it."""
    links = session.exec(select(BookAuthor).where(BookAuthor.book_id == book.id)).all()
    for link in links:
        session.delete(link)
    sessions = session.exec(select(ReadingSession).where(ReadingSession.book_id == book.id)).all()
    for reading_session in sessions:
        session.delete(reading_session)
    session.flush()
    session.delete(book)
    session.commit()
