from typing import Literal, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import (
    AuthorRead,
    BookCreate,
    BookRead,
    BookUpdate,
    ClassificationSuggestRequest,
    ClassificationSuggestion,
    Reader,
    ReaderRead,
    ReadingSession,
    ReaderActivityRead,
)
from app.services import book_service, classification_service

router = APIRouter(prefix="/books", tags=["Books"])

CatalogStatus = Literal["available", "reading", "finished"]


@router.get("", response_model=list[BookRead])
def list_books(
    q: Optional[str] = Query(None, description="Search keyword in title, author, summary, ISBN, or tags"),
    genre: Optional[str] = Query(None, description="Filter by genre or tag"),
    room: Optional[str] = Query(None, description="Filter by location room"),
    book_format: Optional[str] = Query(None, alias="format", description="Filter by format"),
    language: Optional[str] = Query(None, description="Filter by primary language (ISO 639-3 code)"),
    reading_status: Optional[CatalogStatus] = Query(
        None,
        alias="status",
        description="Filter by derived reading status: available, reading, or finished",
    ),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[BookRead]:
    """Retrieve list of books matching search/filter criteria. Filters combine with AND."""
    books = book_service.list_books(
        session=session,
        query=q,
        genre=genre,
        room=room,
        book_format=book_format,
        language=language,
        status=reading_status,
        offset=offset,
        limit=limit,
    )
    return [book_service.to_book_read(session, book) for book in books]


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(
    book_in: BookCreate,
    session: Session = Depends(get_session),
) -> BookRead:
    """Create a new book record in the catalog."""
    book = book_service.create_book(session, book_in)
    return book_service.to_book_read(session, book)


@router.get("/{book_id}", response_model=BookRead)
def get_book(
    book_id: int,
    session: Session = Depends(get_session),
) -> BookRead:
    """Retrieve book details by ID."""
    book = book_service.get_book(session, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found",
        )
    return book_service.to_book_read(session, book)


@router.put("/{book_id}", response_model=BookRead)
def update_book(
    book_id: int,
    book_in: BookUpdate,
    session: Session = Depends(get_session),
) -> BookRead:
    """Update fields on an existing book."""
    book = book_service.get_book(session, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found",
        )
    updated = book_service.update_book(session, book, book_in)
    return book_service.to_book_read(session, updated)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    session: Session = Depends(get_session),
) -> None:
    """Delete a book record from the catalog."""
    book = book_service.get_book(session, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found",
        )
    book_service.delete_book(session, book)


@router.post("/{book_id}/classification/suggest", response_model=ClassificationSuggestion)
def suggest_classification(
    book_id: int,
    request: ClassificationSuggestRequest = Body(default_factory=ClassificationSuggestRequest),
    session: Session = Depends(get_session),
) -> ClassificationSuggestion:
    """Compute a heuristic LCC class + Cutter code suggestion for human review.

    Never auto-persisted: classification is title/genres_tags/authors only
    (no ISBN lookup) and the client must confirm via PUT /books/{book_id}.
    """
    book = book_service.get_book(session, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found",
        )
    authors = book_service.list_book_authors(session, book_id)
    try:
        return classification_service.suggest_classification(
            title=book.title,
            genres_tags=book.genres_tags,
            authors=authors,
            primary_author_id=request.primary_author_id,
        )
    except classification_service.AmbiguousAuthorError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Book has multiple authors; primary_author_id is required",
                "authors": [
                    AuthorRead.model_validate(author).model_dump() for author in exc.authors
                ],
            },
        ) from exc
    except classification_service.InvalidPrimaryAuthorError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"primary_author_id {exc.primary_author_id} is not linked to this book",
        ) from exc


@router.get("/{book_id}/sessions", response_model=list[ReaderActivityRead])
def get_book_reading_sessions(
    book_id: int,
    session: Session = Depends(get_session),
) -> list[ReaderActivityRead]:
    """Retrieve all reading sessions (active & finished) for a specific book."""
    book = book_service.get_book(session, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found",
        )
    statement = (
        select(ReadingSession, Reader)
        .where(ReadingSession.book_id == book_id)
        .join(Reader, ReadingSession.reader_id == Reader.id)
        .order_by(ReadingSession.start_date.desc())
    )
    results = session.exec(statement).all()
    book_dto = book_service.to_book_read(session, book)
    items: list[ReaderActivityRead] = []
    for rs, reader in results:
        progress_pct = 0.0
        if book.page_count and book.page_count > 0:
            progress_pct = round(min(100.0, (rs.current_page / book.page_count) * 100), 1)
        items.append(
            ReaderActivityRead(
                id=rs.id,
                book_id=rs.book_id,
                reader_id=rs.reader_id,
                status=rs.status,
                current_page=rs.current_page,
                start_date=rs.start_date,
                finish_date=rs.finish_date,
                notes=rs.notes,
                rating=rs.rating,
                reader=ReaderRead.model_validate(reader),
                book=book_dto,
                progress_percent=progress_pct,
            )
        )
    return items
