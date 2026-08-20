from typing import Optional
from sqlmodel import Session, select
from app.models import Book, ReadingSession


def get_recommendations(
    session: Session,
    reader_id: Optional[int] = None,
    genre: Optional[str] = None,
    limit: int = 5,
) -> list[Book]:
    """
    Generate book recommendations for a reader or general topic.
    Prioritizes books with 0 read_count or matching genre tags.
    """
    statement = select(Book)

    if genre:
        statement = statement.where(Book.genres_tags.ilike(f"%{genre}%"))

    # Exclude books currently being read by the reader if reader_id is provided
    if reader_id:
        active_sessions = session.exec(
            select(ReadingSession.book_id).where(
                ReadingSession.reader_id == reader_id,
                ReadingSession.status == "reading",
            )
        ).all()
        if active_sessions:
            statement = statement.where(Book.id.not_in(active_sessions))

    # Order by unread books first, then id
    statement = statement.order_by(Book.read_count.asc(), Book.id.desc()).limit(limit)
    return list(session.exec(statement).all())
