from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session
from app.database import get_session
from app.models import BookCreate, BookRead, BookUpdate
from app.services import book_service

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("", response_model=list[BookRead])
def list_books(
    q: Optional[str] = Query(None, description="Search keyword in title, author, summary, or ISBN"),
    genre: Optional[str] = Query(None, description="Filter by genre or tag"),
    room: Optional[str] = Query(None, description="Filter by location room"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[BookRead]:
    """Retrieve list of books matching search/filter criteria."""
    return book_service.list_books(
        session=session,
        query=q,
        genre=genre,
        room=room,
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
