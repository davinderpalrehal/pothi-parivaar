from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import (
    Book,
    BookRead,
    Reader,
    ReaderCreate,
    ReaderRead,
    ReaderUpdate,
    ReadingSession,
    ReadingSessionCreate,
    ReadingSessionRead,
    ReadingSessionUpdate,
    ReaderActivityRead,
    ReaderStatsRead,
)

router = APIRouter(prefix="/readers", tags=["Readers"])


def _normalize_reader_name(name: Optional[str]) -> str:
    cleaned = (name or "").strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reader name is required",
        )
    return cleaned


def _clamp_page(current_page: Optional[int], book: Book) -> int:
    page = 0 if current_page is None else current_page
    if page < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current page cannot be negative",
        )
    if book.page_count is not None and page > book.page_count:
        return book.page_count
    return page


def _adjust_read_count(session: Session, book: Optional[Book], delta: int) -> None:
    if not book:
        return
    book.read_count = max(0, book.read_count + delta)
    session.add(book)


@router.get("", response_model=list[ReaderRead])
def list_readers(session: Session = Depends(get_session)) -> list[ReaderRead]:
    """List all family reader profiles."""
    return list(session.exec(select(Reader).order_by(Reader.name)).all())


@router.post("", response_model=ReaderRead, status_code=status.HTTP_201_CREATED)
def create_reader(
    reader_in: ReaderCreate,
    session: Session = Depends(get_session),
) -> ReaderRead:
    """Create a new reader profile."""
    name = _normalize_reader_name(reader_in.name)
    existing = session.exec(select(Reader).where(Reader.name == name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reader with name '{name}' already exists",
        )
    reader = Reader.model_validate(reader_in)
    reader.name = name
    session.add(reader)
    session.commit()
    session.refresh(reader)
    return reader


@router.get("/activity", response_model=list[ReaderActivityRead])
def get_family_activity(session: Session = Depends(get_session)) -> list[ReaderActivityRead]:
    """Get active reading sessions across all family members (FR-14)."""
    statement = (
        select(ReadingSession, Reader, Book)
        .where(ReadingSession.status == "reading")
        .join(Reader, ReadingSession.reader_id == Reader.id)
        .join(Book, ReadingSession.book_id == Book.id)
        .order_by(ReadingSession.start_date.desc())
    )
    results = session.exec(statement).all()
    activity_items: list[ReaderActivityRead] = []
    for rs, reader, book in results:
        progress_pct = 0.0
        if book.page_count and book.page_count > 0:
            progress_pct = round(min(100.0, (rs.current_page / book.page_count) * 100), 1)
        activity_items.append(
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
                book=BookRead.model_validate(book),
                progress_percent=progress_pct,
            )
        )
    return activity_items


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


@router.put("/{reader_id}", response_model=ReaderRead)
def update_reader(
    reader_id: int,
    reader_update: ReaderUpdate,
    session: Session = Depends(get_session),
) -> ReaderRead:
    """Update a reader profile."""
    reader = session.get(Reader, reader_id)
    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reader with id {reader_id} not found",
        )
    update_data = reader_update.model_dump(exclude_unset=True)
    if "name" in update_data:
        update_data["name"] = _normalize_reader_name(update_data["name"])
        if update_data["name"] != reader.name:
            existing = session.exec(select(Reader).where(Reader.name == update_data["name"])).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Reader with name '{update_data['name']}' already exists",
                )
    for field, value in update_data.items():
        setattr(reader, field, value)
    session.add(reader)
    session.commit()
    session.refresh(reader)
    return reader


@router.delete("/{reader_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reader(reader_id: int, session: Session = Depends(get_session)):
    """Delete a reader profile and cascade delete associated sessions."""
    reader = session.get(Reader, reader_id)
    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reader with id {reader_id} not found",
        )
    sessions = session.exec(select(ReadingSession).where(ReadingSession.reader_id == reader_id)).all()
    for s in sessions:
        if s.status == "finished":
            _adjust_read_count(session, session.get(Book, s.book_id), -1)
        session.delete(s)
    # Flush child deletion first; SQLite enforces the foreign-key constraint
    # immediately and SQLAlchemy otherwise may delete the parent first.
    session.flush()
    session.delete(reader)
    session.commit()
    return None


@router.get("/{reader_id}/stats", response_model=ReaderStatsRead)
def get_reader_stats(reader_id: int, session: Session = Depends(get_session)) -> ReaderStatsRead:
    """Get aggregated statistics and reading history for a reader."""
    reader = session.get(Reader, reader_id)
    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reader with id {reader_id} not found",
        )

    statement = (
        select(ReadingSession, Book)
        .where(ReadingSession.reader_id == reader_id)
        .join(Book, ReadingSession.book_id == Book.id)
        .order_by(ReadingSession.start_date.desc())
    )
    results = session.exec(statement).all()

    active_items: list[ReaderActivityRead] = []
    history_items: list[ReaderActivityRead] = []
    total_pages_read = 0
    total_finished = 0
    total_reading = 0

    reader_dto = ReaderRead.model_validate(reader)

    for rs, book in results:
        book_dto = BookRead.model_validate(book)
        progress_pct = 0.0
        if book.page_count and book.page_count > 0:
            progress_pct = round(min(100.0, (rs.current_page / book.page_count) * 100), 1)

        item = ReaderActivityRead(
            id=rs.id,
            book_id=rs.book_id,
            reader_id=rs.reader_id,
            status=rs.status,
            current_page=rs.current_page,
            start_date=rs.start_date,
            finish_date=rs.finish_date,
            notes=rs.notes,
            rating=rs.rating,
            reader=reader_dto,
            book=book_dto,
            progress_percent=progress_pct,
        )

        if rs.status == "reading":
            total_reading += 1
            total_pages_read += rs.current_page
            active_items.append(item)
        elif rs.status == "finished":
            total_finished += 1
            total_pages_read += (book.page_count or rs.current_page)
            history_items.append(item)
        else:
            total_pages_read += rs.current_page
            history_items.append(item)

    return ReaderStatsRead(
        reader=reader_dto,
        total_reading=total_reading,
        total_finished=total_finished,
        total_pages_read=total_pages_read,
        active_sessions=active_items,
        history=history_items,
    )


@router.get("/{reader_id}/sessions", response_model=list[ReadingSessionRead])
def list_reader_sessions(
    reader_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    session: Session = Depends(get_session),
) -> list[ReadingSessionRead]:
    """List reading sessions for a given reader."""
    reader = session.get(Reader, reader_id)
    if not reader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reader with id {reader_id} not found",
        )
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

    session_status = session_in.status or "reading"
    if session_status == "reading":
        existing_active = session.exec(
            select(ReadingSession).where(
                ReadingSession.book_id == session_in.book_id,
                ReadingSession.reader_id == session_in.reader_id,
                ReadingSession.status == "reading",
            )
        ).first()
        if existing_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reader already has an active session for this book",
            )

    current_page = _clamp_page(session_in.current_page, book)
    reading_session = ReadingSession(
        book_id=session_in.book_id,
        reader_id=session_in.reader_id,
        status=session_status,
        current_page=current_page,
        start_date=session_in.start_date or date.today(),
        notes=session_in.notes,
        rating=session_in.rating,
    )
    if reading_session.status == "finished":
        reading_session.finish_date = date.today()
        _adjust_read_count(session, book, 1)
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
    book = session.get(Book, reading_session.book_id)
    if "current_page" in update_data:
        if update_data["current_page"] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current page cannot be null",
            )
        if book:
            update_data["current_page"] = _clamp_page(update_data["current_page"], book)
        elif update_data["current_page"] < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current page cannot be negative",
            )
    if "status" in update_data and update_data["status"] == "finished" and reading_session.status != "finished":
        _adjust_read_count(session, book, 1)
        if not update_data.get("finish_date"):
            update_data["finish_date"] = date.today()

    if "status" in update_data and reading_session.status == "finished" and update_data["status"] != "finished":
        _adjust_read_count(session, book, -1)
        update_data.setdefault("finish_date", None)

    for field, value in update_data.items():
        setattr(reading_session, field, value)

    session.add(reading_session)
    session.commit()
    session.refresh(reading_session)
    return reading_session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, session: Session = Depends(get_session)):
    """Delete a reading session."""
    reading_session = session.get(ReadingSession, session_id)
    if not reading_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reading session with id {session_id} not found",
        )
    if reading_session.status == "finished":
        _adjust_read_count(session, session.get(Book, reading_session.book_id), -1)
    session.delete(reading_session)
    session.commit()
    return None
