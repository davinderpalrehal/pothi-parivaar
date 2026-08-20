from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import (
    Book,
    BookCreate,
    BookRead,
    BookUpdate,
    Reader,
    ReaderRead,
    ReadingSession,
    ReaderActivityRead,
)
from app.services import book_service

router = APIRouter(prefix="/books", tags=["Books"])

CatalogStatus = Literal["available", "reading", "finished"]


@router.get("", response_model=list[BookRead])
def list_books(
    q: Optional[str] = Query(None, description="Search keyword in title, author, summary, ISBN, or tags"),
    genre: Optional[str] = Query(None, description="Filter by genre or tag"),
    room: Optional[str] = Query(None, description="Filter by location room"),
    book_format: Optional[str] = Query(None, alias="format", description="Filter by format"),
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
    return book_service.list_books(
        session=session,
        query=q,
        genre=genre,
        room=room,
        book_format=book_format,
        status=reading_status,
        offset=offset,
        limit=limit,
    )


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(
    book_in: BookCreate,
    session: Session = Depends(get_session),
) -> BookRead:
    """Create a new book record in the catalog."""
    return book_service.create_book(session, book_in)


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
    return book


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
    return book_service.update_book(session, book, book_in)


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
    book_dto = BookRead.model_validate(book)
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
