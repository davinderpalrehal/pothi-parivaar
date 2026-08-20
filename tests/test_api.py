import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models import Book, Reader, ReadingSession

# In-memory SQLite engine for tests
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


def test_health_check(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "pothi-parivaar"


def test_book_crud_lifecycle(client: TestClient):
    # 1. Create a book
    create_payload = {
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "publication_year": 1937,
        "isbn": "9780547928227",
        "genres_tags": "Fantasy, Adventure",
        "location_room": "Living Room",
        "location_unit": "Main Shelf",
        "location_shelf": "Top",
    }
    response = client.post("/api/v1/books", json=create_payload)
    assert response.status_code == 201
    created_book = response.json()
    book_id = created_book["id"]
    assert created_book["title"] == "The Hobbit"
    assert created_book["author"] == "J.R.R. Tolkien"
    assert created_book["read_count"] == 0

    # 2. List books
    list_res = client.get("/api/v1/books")
    assert list_res.status_code == 200
    books = list_res.json()
    assert len(books) == 1
    assert books[0]["id"] == book_id

    # 3. Search book by title query
    search_res = client.get("/api/v1/books?q=Hobbit")
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1

    # 4. Update book
    update_res = client.put(f"/api/v1/books/{book_id}", json={"page_count": 310})
    assert update_res.status_code == 200
    assert update_res.json()["page_count"] == 310

    # 5. Delete book
    del_res = client.delete(f"/api/v1/books/{book_id}")
    assert del_res.status_code == 204

    # 6. Verify deleted
    get_res = client.get(f"/api/v1/books/{book_id}")
    assert get_res.status_code == 404


def test_reader_and_reading_session(client: TestClient):
    # Create reader
    reader_res = client.post("/api/v1/readers", json={"name": "Aarav", "avatar_icon": "mdi-star"})
    assert reader_res.status_code == 201
    reader_id = reader_res.json()["id"]

    # Create book
    book_res = client.post("/api/v1/books", json={"title": "Panchatantra", "author": "Vishnu Sharma"})
    assert book_res.status_code == 201
    book_id = book_res.json()["id"]

    # Start session
    session_res = client.post(
        "/api/v1/readers/sessions",
        json={"book_id": book_id, "reader_id": reader_id, "current_page": 25},
    )
    assert session_res.status_code == 201
    session_id = session_res.json()["id"]
    assert session_res.json()["status"] == "reading"

    # Finish reading session
    finish_res = client.put(
        f"/api/v1/readers/sessions/{session_id}",
        json={"status": "finished", "current_page": 100},
    )
    assert finish_res.status_code == 200
    assert finish_res.json()["status"] == "finished"

    # Verify book read count incremented
    book_check = client.get(f"/api/v1/books/{book_id}").json()
    assert book_check["read_count"] == 1


def test_hermes_endpoints(client: TestClient):
    # Add a book
    client.post(
        "/api/v1/books",
        json={
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "location_room": "Study",
            "location_unit": "Desk Shelf",
            "location_shelf": "Level 1",
            "genres_tags": "Programming, Tech",
        },
    )

    # Hermes status
    status_res = client.get("/api/v1/hermes/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["total_catalog_books"] == 1

    # Hermes locate
    locate_res = client.get("/api/v1/hermes/locate/Clean")
    assert locate_res.status_code == 200
    matches = locate_res.json()["matches"]
    assert len(matches) == 1
    assert matches[0]["location"]["room"] == "Study"

    # Hermes recommend
    rec_res = client.get("/api/v1/hermes/recommend?genre=Tech")
    assert rec_res.status_code == 200
    assert len(rec_res.json()["recommendations"]) == 1
