from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import (
    Book,
    Reader,
    ReaderCreate,
    ReaderRead,
    ReadingSession,
    ReadingSessionCreate,
    ReadingSessionRead,
    ReadingSessionUpdate,
)

router = APIRouter(prefix="/readers", tags=["Readers"])


@router.get("", response_model=list[ReaderRead])
def list_readers(session: Session = Depends(get_session)) -> list[ReaderRead]:
    """List all family reader profiles."""
    return list(session.exec(select(Reader)).all())


@router.post("", response_model=ReaderRead, status_code=status.HTTP_201_CREATED)
def create_reader(
    reader_in: ReaderCreate,
    session: Session = Depends(get_session),
) -> ReaderRead:
    """Create a new reader profile."""
    existing = session.exec(select(Reader).where(Reader.name == reader_in.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reader with name '{reader_in.name}' already exists",
        )
    reader = Reader.model_validate(reader_in)
    session.add(reader)
    session.commit()
    session.refresh(reader)
    return reader


@router.get("/{reader_id}", response_model=ReaderRead)
def get_reader(reader_id: int, session: Session = Depends(get_session)) -> ReaderRead:
    """Get reader profile by ID."""
    reader = session.get(Reader, reader_id)
    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reader with id {reader_id} not found",
        )
    return reader


@router.get("/{reader_id}/sessions", response_model=list[ReadingSessionRead])
def list_reader_sessions(
    reader_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    session: Session = Depends(get_session),
) -> list[ReadingSessionRead]:
    """List reading sessions for a given reader."""
    statement = select(ReadingSession).where(ReadingSession.reader_id == reader_id)
    if status_filter:
        statement = statement.where(ReadingSession.status == status_filter)
    return list(session.exec(statement).all())


@router.post("/sessions", response_model=ReadingSessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    session_in: ReadingSessionCreate,
    session: Session = Depends(get_session),
) -> ReadingSessionRead:
    """Start or create a reading session for a book and reader."""
    book = session.get(Book, session_in.book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {session_in.book_id} not found",
        )
    reader = session.get(Reader, session_in.reader_id)
    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reader with id {session_in.reader_id} not found",
        )

    reading_session = ReadingSession(
        book_id=session_in.book_id,
        reader_id=session_in.reader_id,
        status=session_in.status or "reading",
        current_page=session_in.current_page or 0,
        start_date=session_in.start_date or date.today(),
    )
    session.add(reading_session)
    session.commit()
    session.refresh(reading_session)
    return reading_session


@router.put("/sessions/{session_id}", response_model=ReadingSessionRead)
def update_session(
    session_id: int,
    session_update: ReadingSessionUpdate,
    session: Session = Depends(get_session),
) -> ReadingSessionRead:
    """Update progress or finish a reading session."""
    reading_session = session.get(ReadingSession, session_id)
    if not reading_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reading session with id {session_id} not found",
        )

    update_data = session_update.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] == "finished" and reading_session.status != "finished":
        # Increment read count on parent book
        book = session.get(Book, reading_session.book_id)
        if book:
            book.read_count += 1
            session.add(book)
        if not update_data.get("finish_date"):
            update_data["finish_date"] = date.today()

    for field, value in update_data.items():
        setattr(reading_session, field, value)

    session.add(reading_session)
    session.commit()
    session.refresh(reading_session)
    return reading_session
