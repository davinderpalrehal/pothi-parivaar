from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func
from app.database import get_session
from app.models import Book, Reader, ReadingSession
from app.services.recommend import get_recommendations

router = APIRouter(prefix="/hermes", tags=["Hermes Agent"])


@router.get("/status")
def get_library_status(session: Session = Depends(get_session)) -> dict:
    """
    Concise library status report designed for Hermes AI agent tool consumption.
    """
    total_books = session.exec(select(func.count(Book.id))).one()
    total_readers = session.exec(select(func.count(Reader.id))).one()

    # Active reading sessions
    active_sessions = session.exec(
        select(ReadingSession).where(ReadingSession.status == "reading")
    ).all()

    active_reading_list = []
    for s in active_sessions:
        book = session.get(Book, s.book_id)
        reader = session.get(Reader, s.reader_id)
        if book and reader:
            active_reading_list.append(
                {
                    "reader": reader.name,
                    "book_title": book.title,
                    "current_page": s.current_page,
                    "total_pages": book.page_count,
                    "location": f"{book.location_room} / {book.location_unit} / {book.location_shelf}",
                }
            )

    return {
        "total_catalog_books": total_books,
        "total_readers": total_readers,
        "active_reading_count": len(active_reading_list),
        "currently_reading": active_reading_list,
    }


@router.get("/recommend")
def recommend_for_hermes(
    reader_name: Optional[str] = Query(None, description="Reader's name (e.g., child or parent)"),
    genre: Optional[str] = Query(None, description="Topic or genre tag filter"),
    limit: int = Query(5, ge=1, le=10),
    session: Session = Depends(get_session),
) -> dict:
    """
    Recommend books for Hermes AI agent to suggest to family members.
    """
    reader_id = None
    if reader_name:
        reader = session.exec(select(Reader).where(Reader.name.ilike(f"%{reader_name}%"))).first()
        if reader:
            reader_id = reader.id

    books = get_recommendations(session=session, reader_id=reader_id, genre=genre, limit=limit)

    recommendations = []
    for b in books:
        recommendations.append(
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "genres": b.genres_tags,
                "summary": b.summary,
                "location": f"{b.location_room or 'Unassigned'} / {b.location_unit or 'Main'} / {b.location_shelf or 'Shelf 1'}",
                "read_count": b.read_count,
            }
        )

    return {
        "reader": reader_name or "General",
        "genre_filter": genre or "Any",
        "count": len(recommendations),
        "recommendations": recommendations,
    }


@router.get("/locate/{book_query}")
def locate_book(
    book_query: str,
    session: Session = Depends(get_session),
) -> dict:
    """
    Locate physical shelf placement for a book by title or keyword.
    """
    pattern = f"%{book_query}%"
    books = session.exec(
        select(Book).where(
            Book.title.ilike(pattern) | Book.author.ilike(pattern)
        )
    ).all()

    matches = []
    for b in books:
        matches.append(
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "location": {
                    "room": b.location_room,
                    "unit": b.location_unit,
                    "shelf": b.location_shelf,
                    "display": f"{b.location_room or 'Unassigned'} -> {b.location_unit or 'Main'} -> {b.location_shelf or 'Shelf'}",
                },
                "read_count": b.read_count,
            }
        )

    return {"query": book_query, "matches": matches}
