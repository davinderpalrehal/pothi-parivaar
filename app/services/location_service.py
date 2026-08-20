"""Location registry helpers: case-insensitive upsert and occupancy summary."""

from typing import Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import Book, Location

OCCUPANCY_UNASSIGNED_KEY = "__occupancy_unassigned__"
OCCUPANCY_UNASSIGNED_ROOM = "Unassigned"
LOCATION_TRIPLE_INDEX = "ix_location_triple_normalized"
LOCATION_TRIPLE_INDEX_SQL = (
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_location_triple_normalized "
    "ON location (lower(trim(room)), lower(trim(unit)), lower(trim(shelf)))"
)


def _norm_part(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def normalized_triple(
    room: Optional[str], unit: Optional[str], shelf: Optional[str]
) -> tuple[str, str, str]:
    return (_norm_part(room), _norm_part(unit), _norm_part(shelf))


def shelf_label(unit: Optional[str], shelf: Optional[str]) -> str:
    """Usable chip text; empty unit/shelf must not render as ' / '."""
    unit_text = (unit or "").strip()
    shelf_text = (shelf or "").strip()
    if unit_text and shelf_text:
        return f"{unit_text} / {shelf_text}"
    if unit_text:
        return unit_text
    if shelf_text:
        return shelf_text
    return "Room"


def find_location(
    session: Session,
    room: str,
    unit: str = "",
    shelf: str = "",
) -> Optional[Location]:
    """Match a registry row on the stripped, lowercased triple."""
    room_n, unit_n, shelf_n = normalized_triple(room, unit, shelf)
    return session.exec(
        select(Location).where(
            func.lower(func.trim(Location.room)) == room_n,
            func.lower(func.trim(Location.unit)) == unit_n,
            func.lower(func.trim(Location.shelf)) == shelf_n,
        )
    ).first()


def upsert_location(
    session: Session,
    room: str,
    unit: Optional[str] = "",
    shelf: Optional[str] = "",
) -> tuple[Optional[Location], bool]:
    """Insert the triple or return the existing row. Created is True on insert.

    Callers that need a row must pass a non-blank room (already validated).
    A stripped-empty room does not insert.
    """
    room_s = (room or "").strip()
    unit_s = (unit or "").strip()
    shelf_s = (shelf or "").strip()
    if not room_s:
        return None, False
    existing = find_location(session, room_s, unit_s, shelf_s)
    if existing:
        return existing, False

    location = Location(room=room_s, unit=unit_s, shelf=shelf_s)
    try:
        with session.begin_nested():
            session.add(location)
            session.flush()
    except IntegrityError:
        existing = find_location(session, room_s, unit_s, shelf_s)
        if existing:
            return existing, False
        raise
    return location, True


def locations_summary(session: Session) -> dict:
    """Union registry shelves with Book occupancy using the normalized triple key."""
    merged: dict[tuple[str, str, str], dict] = {}

    for loc in session.exec(select(Location)).all():
        key = normalized_triple(loc.room, loc.unit, loc.shelf)
        merged[key] = {
            "room": loc.room,
            "unit": loc.unit or "",
            "shelf": loc.shelf or "",
            "book_count": 0,
        }

    books = list(session.exec(select(Book)).all())
    unassigned_count = 0
    for book in books:
        room = (book.location_room or "").strip()
        if not room:
            unassigned_count += 1
            continue
        unit = (book.location_unit or "").strip()
        shelf = (book.location_shelf or "").strip()
        key = normalized_triple(room, unit, shelf)
        if key in merged:
            merged[key]["book_count"] += 1
        else:
            merged[key] = {
                "room": book.location_room.strip() if book.location_room else room,
                "unit": unit,
                "shelf": shelf,
                "book_count": 1,
            }

    rooms_map: dict[str, list[dict]] = {}
    room_key_to_display: dict[str, str] = {}
    for entry in merged.values():
        room_norm = _norm_part(entry["room"])
        display_room = room_key_to_display.setdefault(room_norm, entry["room"])
        rooms_map.setdefault(display_room, []).append(_shelf_entry(entry))

    if unassigned_count:
        occupancy_chip = {
            "unit": "",
            "shelf": "",
            "shelf_key": OCCUPANCY_UNASSIGNED_KEY,
            "book_count": unassigned_count,
            "label": OCCUPANCY_UNASSIGNED_ROOM,
        }
        rooms_map[OCCUPANCY_UNASSIGNED_KEY] = [occupancy_chip]

    return {"locations": rooms_map, "total_books": len(books)}


def _shelf_entry(entry: dict) -> dict:
    unit = entry["unit"]
    shelf = entry["shelf"]
    room = entry["room"]
    return {
        "unit": unit,
        "shelf": shelf,
        "shelf_key": "|".join(normalized_triple(room, unit, shelf)),
        "book_count": entry["book_count"],
        "label": shelf_label(unit, shelf),
    }
