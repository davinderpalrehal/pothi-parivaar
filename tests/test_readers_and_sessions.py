import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_session, migrate_schema
from app.models import Book, Reader, ReadingSession

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(test_engine)
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


def test_reader_crud_and_validation(client: TestClient):
    # 1. Create reader
    res = client.post(
        "/api/v1/readers",
        json={"name": "Harleen", "avatar_icon": "mdi-star", "age_group": "child-10"},
    )
    assert res.status_code == 201
    reader = res.json()
    reader_id = reader["id"]
    assert reader["name"] == "Harleen"
    assert reader["age_group"] == "child-10"
    assert reader["avatar_icon"] == "mdi-star"

    # 2. Duplicate name rejection
    dup_res = client.post(
        "/api/v1/readers",
        json={"name": "Harleen", "avatar_icon": "mdi-heart"},
    )
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Get reader by ID
    get_res = client.get(f"/api/v1/readers/{reader_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Harleen"

    # 4. Update reader
    put_res = client.put(
        f"/api/v1/readers/{reader_id}",
        json={"name": "Harleen Kaur", "avatar_icon": "mdi-emoticon-happy"},
    )
    assert put_res.status_code == 200
    assert put_res.json()["name"] == "Harleen Kaur"
    assert put_res.json()["avatar_icon"] == "mdi-emoticon-happy"

    # 5. List readers
    list_res = client.get("/api/v1/readers")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 6. Delete reader
    del_res = client.delete(f"/api/v1/readers/{reader_id}")
    assert del_res.status_code == 204

    # 7. Verify deletion
    verify_res = client.get(f"/api/v1/readers/{reader_id}")
    assert verify_res.status_code == 404

    missing_update = client.put("/api/v1/readers/9999", json={"name": "Nobody"})
    assert missing_update.status_code == 404

    missing_delete = client.delete("/api/v1/readers/9999")
    assert missing_delete.status_code == 404


def test_reader_deletion_cleans_up_sessions(client: TestClient):
    reader = client.post("/api/v1/readers", json={"name": "To Remove"}).json()
    book = client.post("/api/v1/books", json={"title": "Session Cleanup", "author": "Tester"}).json()
    client.post(
        "/api/v1/readers/sessions",
        json={"book_id": book["id"], "reader_id": reader["id"]},
    ).json()

    assert client.delete(f"/api/v1/readers/{reader['id']}").status_code == 204
    assert client.get(f"/api/v1/books/{book['id']}/sessions").json() == []


def test_reader_schema_migration_adds_profile_columns():
    legacy_engine = create_engine("sqlite:///:memory:")
    with legacy_engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE reader (id INTEGER PRIMARY KEY, name VARCHAR NOT NULL, avatar_icon VARCHAR)"
        )
        connection.exec_driver_sql(
            "INSERT INTO reader (id, name, avatar_icon) VALUES (1, 'Harleen', 'mdi-star')"
        )
        connection.exec_driver_sql(
            "CREATE TABLE readingsession (id INTEGER PRIMARY KEY, book_id INTEGER, reader_id INTEGER)"
        )
        connection.exec_driver_sql(
            "INSERT INTO readingsession (id, book_id, reader_id) VALUES (1, 10, 1)"
        )

    migrate_schema(legacy_engine)

    with legacy_engine.connect() as connection:
        column_names = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(reader)")}
        assert {"age_group", "created_at"}.issubset(column_names)
        reader_row = connection.exec_driver_sql("SELECT id, name, created_at FROM reader").first()
        assert reader_row[0] == 1
        assert reader_row[1] == "Harleen"
        assert reader_row[2] is not None
        session_column_names = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(readingsession)")}
        assert {"notes", "rating"}.issubset(session_column_names)
        session_row = connection.exec_driver_sql("SELECT id, book_id, reader_id FROM readingsession").first()
        assert session_row == (1, 10, 1)


def test_family_activity_endpoint(client: TestClient):
    # Create 2 readers
    r1 = client.post("/api/v1/readers", json={"name": "Fateh", "age_group": "child-7"}).json()
    r2 = client.post("/api/v1/readers", json={"name": "Davinderpal", "age_group": "adult"}).json()

    # Create 2 books
    b1 = client.post("/api/v1/books", json={"title": "Space Explorer", "author": "Carl Sagan", "page_count": 200}).json()
    b2 = client.post("/api/v1/books", json={"title": "Design Patterns", "author": "Gang of Four", "page_count": 400}).json()

    # Initially no activity
    act_empty = client.get("/api/v1/readers/activity").json()
    assert act_empty == []

    # Start 2 sessions
    client.post(
        "/api/v1/readers/sessions",
        json={"book_id": b1["id"], "reader_id": r1["id"], "current_page": 50},
    )
    client.post(
        "/api/v1/readers/sessions",
        json={"book_id": b2["id"], "reader_id": r2["id"], "current_page": 100},
    )

    # Check activity aggregation
    activity_res = client.get("/api/v1/readers/activity")
    assert activity_res.status_code == 200
    items = activity_res.json()
    assert len(items) == 2

    # Verify progress percent and joined models
    fateh_act = next(i for i in items if i["reader"]["name"] == "Fateh")
    assert fateh_act["book"]["title"] == "Space Explorer"
    assert fateh_act["current_page"] == 50
    assert fateh_act["progress_percent"] == 25.0  # 50 / 200 * 100

    dp_act = next(i for i in items if i["reader"]["name"] == "Davinderpal")
    assert dp_act["book"]["title"] == "Design Patterns"
    assert dp_act["progress_percent"] == 25.0  # 100 / 400 * 100


def test_reading_session_lifecycle_and_book_read_count(client: TestClient):
    reader = client.post("/api/v1/readers", json={"name": "Mum", "age_group": "adult"}).json()
    book = client.post("/api/v1/books", json={"title": "Atomic Habits", "author": "James Clear", "page_count": 300}).json()

    # Initial book read count is 0
    assert book["read_count"] == 0

    # Start reading
    sess_res = client.post(
        "/api/v1/readers/sessions",
        json={"book_id": book["id"], "reader_id": reader["id"], "current_page": 10},
    )
    assert sess_res.status_code == 201
    sess_id = sess_res.json()["id"]

    # Update page progress
    put_page = client.put(f"/api/v1/readers/sessions/{sess_id}", json={"current_page": 150})
    assert put_page.status_code == 200
    assert put_page.json()["current_page"] == 150

    # Page progress past the last page is capped, not rejected.
    too_far = client.put(f"/api/v1/readers/sessions/{sess_id}", json={"current_page": 301})
    assert too_far.status_code == 200
    assert too_far.json()["current_page"] == 300

    # Finish reading session with rating and notes
    finish_res = client.put(
        f"/api/v1/readers/sessions/{sess_id}",
        json={
            "status": "finished",
            "rating": 5,
            "notes": "Excellent book on habit formation!",
        },
    )
    assert finish_res.status_code == 200
    finished_data = finish_res.json()
    assert finished_data["status"] == "finished"
    assert finished_data["rating"] == 5
    assert finished_data["notes"] == "Excellent book on habit formation!"
    assert finished_data["finish_date"] == str(date.today())

    # Verify book read count incremented to 1
    updated_book = client.get(f"/api/v1/books/{book['id']}").json()
    assert updated_book["read_count"] == 1

    # Verify session appears in book sessions endpoint
    book_sessions = client.get(f"/api/v1/books/{book['id']}/sessions").json()
    assert len(book_sessions) == 1
    assert book_sessions[0]["reader"]["name"] == "Mum"
    assert book_sessions[0]["status"] == "finished"
    assert book_sessions[0]["notes"] == "Excellent book on habit formation!"


def test_reader_statistics_and_history(client: TestClient):
    reader = client.post("/api/v1/readers", json={"name": "Eldest", "age_group": "child-10"}).json()
    b1 = client.post("/api/v1/books", json={"title": "Harry Potter 1", "author": "J.K. Rowling", "page_count": 220}).json()
    b2 = client.post("/api/v1/books", json={"title": "Harry Potter 2", "author": "J.K. Rowling", "page_count": 250}).json()

    # Finish Book 1
    s1 = client.post("/api/v1/readers/sessions", json={"book_id": b1["id"], "reader_id": reader["id"]}).json()
    client.put(f"/api/v1/readers/sessions/{s1['id']}", json={"status": "finished", "rating": 5, "notes": "Loved Hogwarts!"})

    # Read Book 2 currently at page 75
    client.post("/api/v1/readers/sessions", json={"book_id": b2["id"], "reader_id": reader["id"], "current_page": 75})

    # Get reader stats
    stats_res = client.get(f"/api/v1/readers/{reader['id']}/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_finished"] == 1
    assert stats["total_reading"] == 1
    assert stats["total_pages_read"] == 220 + 75  # 295
    assert len(stats["active_sessions"]) == 1
    assert len(stats["history"]) == 1
    assert stats["history"][0]["book"]["title"] == "Harry Potter 1"
    assert stats["history"][0]["rating"] == 5
    assert stats["history"][0]["notes"] == "Loved Hogwarts!"


def test_reading_session_error_handling(client: TestClient):
    # Non-existent book
    res_b = client.post("/api/v1/readers/sessions", json={"book_id": 9999, "reader_id": 1})
    assert res_b.status_code == 404

    # Non-existent reader
    b = client.post("/api/v1/books", json={"title": "Test Book", "author": "Tester"}).json()
    res_r = client.post("/api/v1/readers/sessions", json={"book_id": b["id"], "reader_id": 9999})
    assert res_r.status_code == 404

    # Non-existent session update
    res_u = client.put("/api/v1/readers/sessions/9999", json={"current_page": 10})
    assert res_u.status_code == 404

    # Non-existent stats
    res_s = client.get("/api/v1/readers/9999/stats")
    assert res_s.status_code == 404


def test_reader_name_trim_and_update_uniqueness(client: TestClient):
    first = client.post("/api/v1/readers", json={"name": "  Harleen  "})
    assert first.status_code == 201
    assert first.json()["name"] == "Harleen"

    blank = client.post("/api/v1/readers", json={"name": "   "})
    assert blank.status_code == 400

    second = client.post("/api/v1/readers", json={"name": "Fateh"}).json()
    clash = client.put(f"/api/v1/readers/{second['id']}", json={"name": "Harleen"})
    assert clash.status_code == 400
    assert "already exists" in clash.json()["detail"]


def test_duplicate_active_session_rejected(client: TestClient):
    reader = client.post("/api/v1/readers", json={"name": "Davinderpal"}).json()
    book = client.post("/api/v1/books", json={"title": "Cosmos", "author": "Sagan", "page_count": 100}).json()
    first = client.post(
        "/api/v1/readers/sessions",
        json={"book_id": book["id"], "reader_id": reader["id"]},
    )
    assert first.status_code == 201
    duplicate = client.post(
        "/api/v1/readers/sessions",
        json={"book_id": book["id"], "reader_id": reader["id"]},
    )
    assert duplicate.status_code == 400
    assert "already has an active session" in duplicate.json()["detail"]


def test_create_session_caps_start_page(client: TestClient):
    reader = client.post("/api/v1/readers", json={"name": "Mum"}).json()
    book = client.post("/api/v1/books", json={"title": "Short", "author": "A", "page_count": 50}).json()
    res = client.post(
        "/api/v1/readers/sessions",
        json={"book_id": book["id"], "reader_id": reader["id"], "current_page": 80},
    )
    assert res.status_code == 201
    assert res.json()["current_page"] == 50


def test_family_activity_excludes_finished_sessions(client: TestClient):
    r1 = client.post("/api/v1/readers", json={"name": "Fateh"}).json()
    r2 = client.post("/api/v1/readers", json={"name": "Harleen"}).json()
    b1 = client.post("/api/v1/books", json={"title": "Book One", "author": "A", "page_count": 100}).json()
    b2 = client.post("/api/v1/books", json={"title": "Book Two", "author": "B", "page_count": 100}).json()
    s1 = client.post("/api/v1/readers/sessions", json={"book_id": b1["id"], "reader_id": r1["id"]}).json()
    client.post("/api/v1/readers/sessions", json={"book_id": b2["id"], "reader_id": r2["id"]})
    client.put(f"/api/v1/readers/sessions/{s1['id']}", json={"status": "finished"})

    activity = client.get("/api/v1/readers/activity").json()
    assert len(activity) == 1
    assert activity[0]["reader"]["name"] == "Harleen"


def test_book_sessions_include_in_progress_rows(client: TestClient):
    reader = client.post("/api/v1/readers", json={"name": "Eldest"}).json()
    book = client.post("/api/v1/books", json={"title": "In Progress", "author": "A", "page_count": 120}).json()
    client.post(
        "/api/v1/readers/sessions",
        json={"book_id": book["id"], "reader_id": reader["id"], "current_page": 12},
    )
    rows = client.get(f"/api/v1/books/{book['id']}/sessions").json()
    assert len(rows) == 1
    assert rows[0]["status"] == "reading"
    assert rows[0]["current_page"] == 12
    assert rows[0]["reader"]["name"] == "Eldest"


def test_delete_session_removes_activity_and_book_log(client: TestClient):
    reader = client.post("/api/v1/readers", json={"name": "Child"}).json()
    book = client.post("/api/v1/books", json={"title": "Drop Me", "author": "A"}).json()
    sess = client.post(
        "/api/v1/readers/sessions",
        json={"book_id": book["id"], "reader_id": reader["id"]},
    ).json()

    assert client.delete(f"/api/v1/readers/sessions/{sess['id']}").status_code == 204
    assert client.get("/api/v1/readers/activity").json() == []
    assert client.get(f"/api/v1/books/{book['id']}/sessions").json() == []
    assert client.delete("/api/v1/readers/sessions/9999").status_code == 404


def test_delete_reader_decrements_finished_read_count(client: TestClient):
    reader = client.post("/api/v1/readers", json={"name": "To Archive"}).json()
    book = client.post("/api/v1/books", json={"title": "Counted", "author": "A"}).json()
    sess = client.post(
        "/api/v1/readers/sessions",
        json={"book_id": book["id"], "reader_id": reader["id"]},
    ).json()
    client.put(f"/api/v1/readers/sessions/{sess['id']}", json={"status": "finished"})
    assert client.get(f"/api/v1/books/{book['id']}").json()["read_count"] == 1

    assert client.delete(f"/api/v1/readers/{reader['id']}").status_code == 204
    assert client.get(f"/api/v1/books/{book['id']}").json()["read_count"] == 0
    assert client.get(f"/api/v1/books/{book['id']}/sessions").json() == []


def test_delete_book_cascades_sessions(client: TestClient):
    reader = client.post("/api/v1/readers", json={"name": "Keeper"}).json()
    book = client.post("/api/v1/books", json={"title": "Gone", "author": "A"}).json()
    client.post("/api/v1/readers/sessions", json={"book_id": book["id"], "reader_id": reader["id"]})
    assert client.delete(f"/api/v1/books/{book['id']}").status_code == 204
    assert client.get("/api/v1/readers/activity").json() == []


def test_unfinish_clears_finish_date_and_read_count(client: TestClient):
    reader = client.post("/api/v1/readers", json={"name": "Reopen"}).json()
    book = client.post("/api/v1/books", json={"title": "Reopened", "author": "A"}).json()
    sess = client.post(
        "/api/v1/readers/sessions",
        json={"book_id": book["id"], "reader_id": reader["id"]},
    ).json()
    client.put(f"/api/v1/readers/sessions/{sess['id']}", json={"status": "finished"})
    reopened = client.put(
        f"/api/v1/readers/sessions/{sess['id']}",
        json={"status": "reading"},
    )
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "reading"
    assert reopened.json()["finish_date"] is None
    assert client.get(f"/api/v1/books/{book['id']}").json()["read_count"] == 0
