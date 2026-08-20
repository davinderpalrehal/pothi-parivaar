from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import Book, Location, LocationCreate, LocationRead

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("", response_model=list[LocationRead])
def list_locations(session: Session = Depends(get_session)) -> list[LocationRead]:
    """List physical locations registered in the house."""
    return list(session.exec(select(Location)).all())


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(
    location_in: LocationCreate,
    session: Session = Depends(get_session),
) -> LocationRead:
    """Create a new physical room/unit/shelf location."""
    location = Location.model_validate(location_in)
    session.add(location)
    session.commit()
    session.refresh(location)
    return location


@router.get("/summary")
def get_locations_summary(session: Session = Depends(get_session)) -> dict:
    """Return distinct rooms and physical location distribution with book counts."""
    books = session.exec(select(Book)).all()
    rooms_map: dict[str, list[dict]] = {}

    for book in books:
        room = book.location_room or "Unassigned"
        unit = book.location_unit or "Default Unit"
        shelf = book.location_shelf or "Default Shelf"
        key = f"{unit} - {shelf}"

        if room not in rooms_map:
            rooms_map[room] = []

        # Find existing unit/shelf entry
        entry = next((e for e in rooms_map[room] if e["shelf_key"] == key), None)
        if entry:
            entry["book_count"] += 1
        else:
            rooms_map[room].append(
                {"unit": unit, "shelf": shelf, "shelf_key": key, "book_count": 1}
            )

    return {"locations": rooms_map, "total_books": len(books)}
