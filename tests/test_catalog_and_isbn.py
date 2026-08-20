import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models import ReadingSession
from app.services import book_service

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


def _create_book(client: TestClient, **overrides) -> dict:
    payload = {
        "title": "Untitled",
        "author": "Unknown",
        **overrides,
    }
    res = client.post("/api/v1/books", json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def _create_reader(client: TestClient, name: str) -> dict:
    res = client.post("/api/v1/readers", json={"name": name})
    assert res.status_code == 201, res.text
    return res.json()


def _start_session(client: TestClient, book_id: int, reader_id: int, status: str = "reading") -> dict:
    res = client.post(
        "/api/v1/readers/sessions",
        json={"book_id": book_id, "reader_id": reader_id, "status": status},
    )
    assert res.status_code == 201, res.text
    return res.json()


def test_keyword_search_includes_genres_tags(client: TestClient):
    _create_book(
        client,
        title="The Secret Island",
        author="Enid Blyton",
        genres_tags="Adventure, Kids",
    )
    _create_book(
        client,
        title="Quiet Hours",
        author="Someone Else",
        genres_tags="Poetry",
    )

    res = client.get("/api/v1/books", params={"q": "Adventure"})
    assert res.status_code == 200
    titles = [b["title"] for b in res.json()]
    assert titles == ["The Secret Island"]

    empty = client.get("/api/v1/books", params={"q": "NoSuchTag"})
    assert empty.status_code == 200
    assert empty.json() == []


def test_multi_filter_and_combination(client: TestClient):
    hobbit = _create_book(
        client,
        title="The Hobbit",
        author="J.R.R. Tolkien",
        genres_tags="Fantasy, Adventure",
        formats="physical",
        location_room="Office",
    )
    _create_book(
        client,
        title="Narnia",
        author="C.S. Lewis",
        genres_tags="Fantasy",
        formats="physical",
        location_room="Office",
    )
    _create_book(
        client,
        title="Kindle Fantasy",
        author="A. Author",
        genres_tags="Fantasy",
        formats="kindle",
        location_room="Office",
    )
    _create_book(
        client,
        title="Living Room Fantasy",
        author="B. Author",
        genres_tags="Fantasy",
        formats="physical",
        location_room="Living Room",
    )
    _create_book(
        client,
        title="Office SciFi",
        author="C. Author",
        genres_tags="SciFi",
        formats="physical",
        location_room="Office",
    )

    reader = _create_reader(client, "Harleen")
    narnia = client.get("/api/v1/books", params={"q": "Narnia"}).json()[0]
    _start_session(client, narnia["id"], reader["id"], status="reading")

    shared_filters = {
        "q": "Fantasy",
        "genre": "Fantasy",
        "format": "physical",
        "room": "Office",
        "status": "available",
    }
    res = client.get("/api/v1/books", params=shared_filters)
    assert res.status_code == 200
    matches = res.json()
    assert [b["id"] for b in matches] == [hobbit["id"]]

    kindle_miss = client.get(
        "/api/v1/books",
        params={**shared_filters, "format": "epub"},
    )
    assert kindle_miss.status_code == 200
    assert kindle_miss.json() == []


def test_status_derivation_from_sessions(client: TestClient):
    never_started = _create_book(client, title="Never Started", author="A")
    currently = _create_book(client, title="Currently Reading", author="B")
    finished_only = _create_book(client, title="Finished Only", author="C")
    both = _create_book(client, title="Finished And Reading", author="D")

    reader = _create_reader(client, "Aarav")
    other = _create_reader(client, "Parent")

    _start_session(client, currently["id"], reader["id"], status="reading")
    finished_sess = _start_session(client, finished_only["id"], reader["id"], status="reading")
    finish_res = client.put(
        f"/api/v1/readers/sessions/{finished_sess['id']}",
        json={"status": "finished"},
    )
    assert finish_res.status_code == 200

    both_finished = _start_session(client, both["id"], reader["id"], status="reading")
    client.put(f"/api/v1/readers/sessions/{both_finished['id']}", json={"status": "finished"})
    _start_session(client, both["id"], other["id"], status="reading")

    def ids(status: str) -> set[int]:
        res = client.get("/api/v1/books", params={"status": status})
        assert res.status_code == 200
        return {b["id"] for b in res.json()}

    assert never_started["id"] in ids("available")
    assert finished_only["id"] in ids("available")
    assert currently["id"] not in ids("available")
    assert both["id"] not in ids("available")

    assert currently["id"] in ids("reading")
    assert both["id"] in ids("reading")
    assert never_started["id"] not in ids("reading")
    assert finished_only["id"] not in ids("reading")

    assert finished_only["id"] in ids("finished")
    assert never_started["id"] not in ids("finished")
    assert currently["id"] not in ids("finished")
    assert both["id"] not in ids("finished")


def test_invalid_status_returns_422(client: TestClient):
    res = client.get("/api/v1/books", params={"status": "to_read"})
    assert res.status_code == 422


def test_create_requires_title_and_author(client: TestClient):
    missing_title = client.post("/api/v1/books", json={"author": "Only Author"})
    assert missing_title.status_code == 422
    missing_author = client.post("/api/v1/books", json={"title": "Only Title"})
    assert missing_author.status_code == 422


def test_create_book_does_not_call_isbn(client: TestClient):
    source = inspect.getsource(book_service.create_book)
    assert "lookup_isbn" not in source
    assert "isbn_service" not in inspect.getsource(book_service)
    assert "lookup_isbn" not in book_service.__dict__

    with patch("app.services.isbn_service.httpx.AsyncClient") as mock_client:
        res = client.post(
            "/api/v1/books",
            json={"title": "Handwritten Card", "author": "Child Cataloger"},
        )
        assert res.status_code == 201
        mock_client.assert_not_called()


def _mock_async_client(response=None, error=None):
    instance = MagicMock()
    instance.__aenter__ = AsyncMock(return_value=instance)
    instance.__aexit__ = AsyncMock(return_value=False)
    if error is not None:
        instance.get = AsyncMock(side_effect=error)
    else:
        instance.get = AsyncMock(return_value=response)
    return instance


def test_isbn_lookup_success_mocked(client: TestClient):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ISBN:9780547928227": {
            "title": "The Hobbit",
            "authors": [{"name": "J.R.R. Tolkien"}],
            "publish_date": "1937",
            "cover": {"large": "http://covers.example/hobbit.jpg"},
            "number_of_pages": 310,
            "subjects": [{"name": "Fantasy"}, {"name": "Adventure"}],
            "description": "A hobbit goes on an adventure.",
        }
    }

    with patch(
        "app.services.isbn_service.httpx.AsyncClient",
        return_value=_mock_async_client(response=mock_response),
    ):
        res = client.get("/api/v1/isbn/9780547928227")

    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "The Hobbit"
    assert data["author"] == "J.R.R. Tolkien"
    assert data["publication_year"] == 1937
    assert data["isbn"] == "9780547928227"
    assert data["page_count"] == 310
    assert data["cover_url"] == "http://covers.example/hobbit.jpg"
    assert "Fantasy" in data["genres_tags"]
    assert data["formats"] == "physical"
    assert data["summary"] == "A hobbit goes on an adventure."

    catalog = client.get("/api/v1/books")
    assert catalog.status_code == 200
    assert catalog.json() == []


def test_isbn_lookup_404_on_miss(client: TestClient):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}

    with patch(
        "app.services.isbn_service.httpx.AsyncClient",
        return_value=_mock_async_client(response=mock_response),
    ):
        res = client.get("/api/v1/isbn/0000000000")

    assert res.status_code == 404


def test_isbn_lookup_404_on_network_error(client: TestClient):
    with patch(
        "app.services.isbn_service.httpx.AsyncClient",
        return_value=_mock_async_client(error=httpx.ConnectError("offline")),
    ):
        res = client.get("/api/v1/isbn/9780547928227")

    assert res.status_code == 404


def test_delete_book_cascades_sessions(client: TestClient, session: Session):
    book = _create_book(client, title="To Remove", author="Temp")
    reader = _create_reader(client, "Kid")
    reading = _start_session(client, book["id"], reader["id"])

    del_res = client.delete(f"/api/v1/books/{book['id']}")
    assert del_res.status_code == 204
    assert client.get(f"/api/v1/books/{book['id']}").status_code == 404

    session.expire_all()
    remaining = session.exec(
        select(ReadingSession).where(ReadingSession.id == reading["id"])
    ).first()
    assert remaining is None


def test_partial_update_title_author_location(client: TestClient):
    book = _create_book(
        client,
        title="Old Title",
        author="Old Author",
        location_room="Office",
        location_unit="Main Shelf",
        location_shelf="Top",
    )
    res = client.put(
        f"/api/v1/books/{book['id']}",
        json={
            "title": "New Title",
            "author": "New Author",
            "location_room": "Living Room",
            "location_unit": "Kids Shelf",
            "location_shelf": "Bottom",
        },
    )
    assert res.status_code == 200
    updated = res.json()
    assert updated["title"] == "New Title"
    assert updated["author"] == "New Author"
    assert updated["location_room"] == "Living Room"
    assert updated["location_unit"] == "Kids Shelf"
    assert updated["location_shelf"] == "Bottom"

    fetched = client.get(f"/api/v1/books/{book['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "New Title"
    assert fetched.json()["author"] == "New Author"
    assert fetched.json()["location_room"] == "Living Room"


def test_update_and_delete_missing_book_404(client: TestClient):
    assert client.put("/api/v1/books/99999", json={"title": "Ghost"}).status_code == 404
    assert client.delete("/api/v1/books/99999").status_code == 404
