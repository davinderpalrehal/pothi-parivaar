import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.main import app
from app.database import get_session, migrate_schema
from app.models import Book, Location
from app.services import location_service
from app.services.location_service import (
    LOCATION_TRIPLE_INDEX,
    find_location,
    upsert_location,
)

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(test_engine)
    migrate_schema(test_engine)
    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _create_book(client: TestClient, **overrides) -> dict:
    payload = {
        "title": "Untitled",
        "author": "Unknown",
        **overrides,
    }
    res = client.post("/api/v1/books", json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def _summary_chip(rooms: dict, room_name: str, unit: str, shelf: str) -> dict:
    room_key = next(k for k in rooms if k.lower() == room_name.lower())
    return next(
        chip
        for chip in rooms[room_key]
        if (chip["unit"] or "").lower() == unit.lower()
        and (chip["shelf"] or "").lower() == shelf.lower()
        and chip.get("shelf_key") != location_service.OCCUPANCY_UNASSIGNED_KEY
    )


def test_pick_existing_does_not_duplicate_registry(client: TestClient):
    first = client.post(
        "/api/v1/locations",
        json={"room": "Office", "unit": "Main Shelf", "shelf": "Top"},
    )
    assert first.status_code == 201
    book = _create_book(
        client,
        title="Cataloged",
        author="A",
        location_room="Office",
        location_unit="Main Shelf",
        location_shelf="Top",
    )
    assert book["location_room"] == "Office"
    assert book["location_unit"] == "Main Shelf"
    assert book["location_shelf"] == "Top"
    rows = client.get("/api/v1/locations").json()
    assert len(rows) == 1
    assert rows[0]["id"] == first.json()["id"]


def test_empty_book_location_skips_upsert(client: TestClient):
    book = _create_book(client, title="Loose", author="Floor")
    assert book["location_room"] is None
    assert client.get("/api/v1/locations").json() == []


def test_type_new_on_book_save_upserts_once(client: TestClient):
    _create_book(
        client,
        title="One",
        author="A",
        location_room="Kitchen",
        location_unit="Isle",
        location_shelf="Top",
    )
    _create_book(
        client,
        title="Two",
        author="B",
        location_room="Kitchen",
        location_unit="Isle",
        location_shelf="Top",
    )
    rows = client.get("/api/v1/locations").json()
    assert len(rows) == 1
    assert rows[0]["room"] == "Kitchen"


def test_book_keeps_typed_casing_not_registry_casing(client: TestClient):
    client.post(
        "/api/v1/locations",
        json={"room": "office", "unit": "main", "shelf": "1"},
    )
    book = _create_book(
        client,
        title="Cased",
        author="A",
        location_room="Office",
        location_unit="Main",
        location_shelf="1",
    )
    assert book["location_room"] == "Office"
    assert book["location_unit"] == "Main"
    office = client.get("/api/v1/books", params={"room": "Office"}).json()
    office_lower = client.get("/api/v1/books", params={"room": "office"}).json()
    assert len(office) == 1
    assert office_lower == []


def test_direct_registry_create_is_idempotent(client: TestClient):
    payload = {"room": "Office", "unit": "Main", "shelf": "2"}
    first = client.post("/api/v1/locations", json=payload)
    second = client.post("/api/v1/locations", json=payload)
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert len(client.get("/api/v1/locations").json()) == 1


def test_case_variant_post_returns_same_id(client: TestClient):
    first = client.post(
        "/api/v1/locations",
        json={"room": "Office", "unit": "Main Shelf", "shelf": "Top"},
    )
    second = client.post(
        "/api/v1/locations",
        json={"room": "office", "unit": "main shelf", "shelf": "top"},
    )
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_blank_room_returns_422(client: TestClient):
    assert client.post("/api/v1/locations", json={"room": "", "unit": "A", "shelf": "B"}).status_code == 422
    assert client.post("/api/v1/locations", json={"room": "   ", "unit": "", "shelf": ""}).status_code == 422
    assert client.post("/api/v1/locations", json={"unit": "A", "shelf": "B"}).status_code == 422


def test_room_only_shelf_count_zero_then_one(client: TestClient):
    created = client.post("/api/v1/locations", json={"room": "Attic"})
    assert created.status_code == 201
    assert created.json()["unit"] == ""
    assert created.json()["shelf"] == ""

    summary = client.get("/api/v1/locations/summary").json()
    chip = _summary_chip(summary["locations"], "Attic", "", "")
    assert chip["book_count"] == 0
    assert chip["label"]
    assert chip["label"] != " / "

    _create_book(client, title="Stored", author="A", location_room="Attic")
    summary = client.get("/api/v1/locations/summary").json()
    chip = _summary_chip(summary["locations"], "Attic", "", "")
    assert chip["book_count"] == 1


def test_summary_unions_registry_and_occupancy(client: TestClient):
    client.post(
        "/api/v1/locations",
        json={"room": "Office", "unit": "Main", "shelf": "Empty"},
    )
    _create_book(
        client,
        title="Placed",
        author="A",
        location_room="Living Room",
        location_unit="Kids",
        location_shelf="Bottom",
    )
    _create_book(client, title="Lost", author="B")

    summary = client.get("/api/v1/locations/summary").json()
    rooms = summary["locations"]
    empty = _summary_chip(rooms, "Office", "Main", "Empty")
    assert empty["book_count"] == 0
    occupied = _summary_chip(rooms, "Living Room", "Kids", "Bottom")
    assert occupied["book_count"] == 1
    occupancy = rooms[location_service.OCCUPANCY_UNASSIGNED_KEY]
    assert occupancy[0]["book_count"] == 1
    assert occupancy[0]["shelf_key"] == location_service.OCCUPANCY_UNASSIGNED_KEY
    assert occupancy[0]["label"] == "Unassigned"
    assert summary["total_books"] == 2


def test_unassigned_bucket_does_not_merge_with_registry_unassigned(client: TestClient):
    client.post(
        "/api/v1/locations",
        json={"room": "Unassigned", "unit": "Main", "shelf": "1"},
    )
    _create_book(client, title="No Room", author="A")
    _create_book(
        client,
        title="Named Unassigned",
        author="B",
        location_room="Unassigned",
        location_unit="Main",
        location_shelf="1",
    )
    rooms = client.get("/api/v1/locations/summary").json()["locations"]
    registry = _summary_chip(rooms, "Unassigned", "Main", "1")
    occupancy = rooms[location_service.OCCUPANCY_UNASSIGNED_KEY]
    assert registry["book_count"] == 1
    assert occupancy[0]["book_count"] == 1
    assert occupancy[0]["shelf_key"] == location_service.OCCUPANCY_UNASSIGNED_KEY
    assert all(
        chip.get("shelf_key") != location_service.OCCUPANCY_UNASSIGNED_KEY
        for chip in rooms["Unassigned"]
    )


def test_mixed_case_occupancy_one_summary_chip(client: TestClient):
    client.post(
        "/api/v1/locations",
        json={"room": "Office", "unit": "Main", "shelf": "1"},
    )
    _create_book(
        client,
        title="Lower",
        author="A",
        location_room="office",
        location_unit="main",
        location_shelf="1",
    )
    rooms = client.get("/api/v1/locations/summary").json()["locations"]
    office_keys = [key for key in rooms if key.lower() == "office"]
    assert len(office_keys) == 1
    chips = [
        chip
        for chip in rooms[office_keys[0]]
        if chip.get("shelf_key") != location_service.OCCUPANCY_UNASSIGNED_KEY
    ]
    assert len(chips) == 1
    assert chips[0]["book_count"] == 1


def test_create_location_openapi_advertises_200_and_201(client: TestClient):
    spec = client.get("/openapi.json").json()
    responses = spec["paths"]["/api/v1/locations"]["post"]["responses"]
    assert "200" in responses
    assert "201" in responses


def test_update_book_upserts_location(client: TestClient):
    book = _create_book(client, title="Move me", author="A")
    res = client.put(
        f"/api/v1/books/{book['id']}",
        json={
            "location_room": "Study",
            "location_unit": "Desk",
            "location_shelf": "Left",
        },
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Move me"
    rows = client.get("/api/v1/locations").json()
    assert len(rows) == 1
    assert rows[0]["room"] == "Study"


def test_upsert_location_skips_empty_room(session: Session):
    loc, created = upsert_location(session, "   ", "Main", "1")
    session.commit()
    assert loc is None
    assert created is False
    assert session.exec(select(Location)).all() == []


def test_upsert_recovers_from_integrity_error(session: Session, monkeypatch: pytest.MonkeyPatch):
    loc, created = upsert_location(session, "Office", "A", "1")
    session.commit()
    assert created is True

    calls = {"n": 0}
    real_find = find_location

    def flaky_find(sess, room, unit="", shelf=""):
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return real_find(sess, room, unit, shelf)

    monkeypatch.setattr(location_service, "find_location", flaky_find)
    recovered, created_again = location_service.upsert_location(session, "office", "a", "1")
    session.commit()
    assert created_again is False
    assert recovered.id == loc.id


def test_migrate_schema_legacy_location_table():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(
            Book(
                title="Legacy",
                author="A",
                location_room="Den",
                location_unit=None,
                location_shelf=None,
            )
        )
        session.add(Location(room="Office", unit="Main", shelf="1"))
        session.add(Location(room="office", unit="Main", shelf="1"))
        session.commit()

    with engine.connect() as connection:
        before = connection.exec_driver_sql(
            f"SELECT sql FROM sqlite_master WHERE type='index' AND name='{LOCATION_TRIPLE_INDEX}'"
        ).first()
        assert before is None

    migrate_schema(engine)

    with engine.connect() as connection:
        row = connection.exec_driver_sql(
            f"SELECT sql FROM sqlite_master WHERE type='index' AND name='{LOCATION_TRIPLE_INDEX}'"
        ).first()
        assert row is not None
        sql = row[0].lower()
        assert "lower(trim(room))" in sql
        assert "lower(trim(unit))" in sql
        assert "lower(trim(shelf))" in sql

    with Session(engine) as session:
        locations = list(session.exec(select(Location)).all())
        office_rows = [
            loc
            for loc in locations
            if loc.room.lower() == "office" and loc.unit.lower() == "main" and loc.shelf.lower() == "1"
        ]
        assert len(office_rows) == 1
        den = find_location(session, "Den", "", "")
        assert den is not None
        assert den.unit == ""
        assert den.shelf == ""


def test_padded_book_location_is_stripped_and_upserted_once(client: TestClient):
    book = _create_book(
        client,
        title="Padded",
        author="A",
        location_room="  Office  ",
        location_unit="  Main  ",
        location_shelf="  Top  ",
    )
    assert book["location_room"] == "Office"
    assert book["location_unit"] == "Main"
    assert book["location_shelf"] == "Top"
    rows = client.get("/api/v1/locations").json()
    assert len(rows) == 1
    assert rows[0]["room"] == "Office"
    assert rows[0]["unit"] == "Main"
    assert rows[0]["shelf"] == "Top"
    matched = client.get("/api/v1/books", params={"room": "Office"}).json()
    assert len(matched) == 1
    assert matched[0]["id"] == book["id"]

    updated = client.put(
        f"/api/v1/books/{book['id']}",
        json={
            "location_room": " Office ",
            "location_unit": " Main ",
            "location_shelf": " Top ",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["location_room"] == "Office"
    assert updated.json()["location_unit"] == "Main"
    assert updated.json()["location_shelf"] == "Top"
    assert len(client.get("/api/v1/locations").json()) == 1
    matched = client.get("/api/v1/books", params={"room": "Office"}).json()
    assert len(matched) == 1


def test_whitespace_only_book_room_skips_upsert(client: TestClient):
    book = _create_book(
        client,
        title="Spaces",
        author="A",
        location_room="   ",
        location_unit="  ",
        location_shelf="  ",
    )
    assert book["location_room"] is None
    assert book["location_unit"] is None
    assert book["location_shelf"] is None
    assert client.get("/api/v1/locations").json() == []


def test_post_location_strips_padded_room(client: TestClient):
    res = client.post(
        "/api/v1/locations",
        json={"room": " Office ", "unit": " Main ", "shelf": " Top "},
    )
    assert res.status_code == 201
    assert res.json()["room"] == "Office"
    assert res.json()["unit"] == "Main"
    assert res.json()["shelf"] == "Top"


def test_duplicate_post_location_keeps_original_casing(client: TestClient):
    first = client.post(
        "/api/v1/locations",
        json={"room": "Office", "unit": "Main", "shelf": "2"},
    )
    second = client.post(
        "/api/v1/locations",
        json={"room": "office", "unit": "main", "shelf": "2"},
    )
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["room"] == "Office"
    assert second.json()["unit"] == "Main"
    assert second.json()["shelf"] == "2"


def test_title_only_put_leaves_location_and_skips_blank_registry(client: TestClient):
    empty = _create_book(client, title="Old Empty", author="A")
    empty_put = client.put(f"/api/v1/books/{empty['id']}", json={"title": "New Empty"})
    assert empty_put.status_code == 200
    assert empty_put.json()["location_room"] is None
    assert empty_put.json()["location_unit"] is None
    assert empty_put.json()["location_shelf"] is None
    assert client.get("/api/v1/locations").json() == []

    placed = _create_book(
        client,
        title="Old Placed",
        author="B",
        location_room="Office",
        location_unit="Main",
        location_shelf="1",
    )
    placed_put = client.put(f"/api/v1/books/{placed['id']}", json={"title": "New Placed"})
    assert placed_put.status_code == 200
    assert placed_put.json()["location_room"] == "Office"
    assert placed_put.json()["location_unit"] == "Main"
    assert placed_put.json()["location_shelf"] == "1"
    rows = client.get("/api/v1/locations").json()
    assert len(rows) == 1
    assert rows[0]["room"] == "Office"
    assert rows[0]["unit"] == "Main"
    assert rows[0]["shelf"] == "1"


def test_occupancy_unassigned_does_not_increment_registry_unassigned(client: TestClient):
    client.post(
        "/api/v1/locations",
        json={"room": "Unassigned", "unit": "Main", "shelf": "1"},
    )
    _create_book(client, title="No Room", author="A")
    rooms = client.get("/api/v1/locations/summary").json()["locations"]
    registry = _summary_chip(rooms, "Unassigned", "Main", "1")
    assert registry["book_count"] == 0
    occupancy = rooms[location_service.OCCUPANCY_UNASSIGNED_KEY]
    assert occupancy[0]["book_count"] == 1
    assert location_service.OCCUPANCY_UNASSIGNED_KEY not in [
        chip.get("shelf_key") for chip in rooms["Unassigned"]
    ]
    assert rooms["Unassigned"] is not occupancy
