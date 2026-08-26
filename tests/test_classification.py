import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.main import app
from app.database import get_session
from app.services import classification_service

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
    payload = {"title": "Untitled", **overrides}
    res = client.post("/api/v1/books", json=payload)
    assert res.status_code == 201, res.text
    return res.json()


def _suggest(client: TestClient, book_id: int, primary_author_id: int | None = None):
    body = {"primary_author_id": primary_author_id} if primary_author_id is not None else {}
    return client.post(f"/api/v1/books/{book_id}/classification/suggest", json=body)


# ==============================================================================
# Pure unit tests for the heuristic tables/functions
# ==============================================================================

def test_suggest_lcc_class_matches_keyword_case_insensitively():
    assert classification_service.suggest_lcc_class("History, Kids") == "D"
    assert classification_service.suggest_lcc_class("HISTORY") == "D"


def test_suggest_lcc_class_prefers_more_specific_multi_word_keyword():
    # "science fiction" contains "science"; the more specific entry must win.
    assert classification_service.suggest_lcc_class("Science Fiction") == "PZ"
    assert classification_service.suggest_lcc_class("Science") == "Q"


def test_suggest_lcc_class_falls_back_to_default_when_no_match():
    assert classification_service.suggest_lcc_class(None) == classification_service.DEFAULT_LCC_CLASS
    assert classification_service.suggest_lcc_class("") == classification_service.DEFAULT_LCC_CLASS
    assert classification_service.suggest_lcc_class("Unmatched Tag") == classification_service.DEFAULT_LCC_CLASS


def test_suggest_cutter_is_deterministic_and_shaped_letter_plus_two_digits():
    first = classification_service.suggest_cutter("Orwell")
    second = classification_service.suggest_cutter("Orwell")
    assert first == second
    assert len(first) == 3
    assert first[0] == "O"
    assert first[1:].isdigit()


def test_suggest_cutter_handles_empty_and_non_letter_source():
    assert classification_service.suggest_cutter("") == "X00"
    assert classification_service.suggest_cutter("123!!!") == "X00"


# ==============================================================================
# I/O matrix -- API-level edge cases
# ==============================================================================

def test_zero_authors_cutter_source_is_title(client: TestClient):
    book = _create_book(client, title="A Brief History of Time", genres_tags="History")
    assert book["authors"] == []

    res = _suggest(client, book["id"])
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["lcc_call_number"] == "D"
    assert body["cutter_number"] == classification_service.suggest_cutter("A Brief History of Time")


def test_single_author_cutter_source_is_last_name(client: TestClient):
    book = _create_book(
        client,
        title="Nineteen Eighty-Four",
        authors=[{"first_name": "George", "last_name": "Orwell"}],
        genres_tags="Science Fiction",
    )
    res = _suggest(client, book["id"])
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["lcc_call_number"] == "PZ"
    assert body["cutter_number"] == classification_service.suggest_cutter("Orwell")


def test_multiple_authors_no_choice_returns_422_with_author_list(client: TestClient):
    book = _create_book(
        client,
        title="Good Omens",
        authors=[
            {"first_name": "Terry", "last_name": "Pratchett"},
            {"first_name": "Neil", "last_name": "Gaiman"},
        ],
    )
    res = _suggest(client, book["id"])
    assert res.status_code == 422, res.text
    detail = res.json()["detail"]
    returned_ids = {a["id"] for a in detail["authors"]}
    expected_ids = {a["id"] for a in book["authors"]}
    assert returned_ids == expected_ids
    for author in detail["authors"]:
        assert "id" in author
        assert "last_name" in author
        assert "first_name" in author


def test_multiple_authors_with_valid_choice_uses_that_author(client: TestClient):
    book = _create_book(
        client,
        title="Good Omens",
        authors=[
            {"first_name": "Terry", "last_name": "Pratchett"},
            {"first_name": "Neil", "last_name": "Gaiman"},
        ],
    )
    gaiman_id = next(a["id"] for a in book["authors"] if a["last_name"] == "Gaiman")

    res = _suggest(client, book["id"], primary_author_id=gaiman_id)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["cutter_number"] == classification_service.suggest_cutter("Gaiman")


def test_primary_author_id_not_linked_returns_400(client: TestClient):
    book = _create_book(
        client,
        title="Good Omens",
        authors=[
            {"first_name": "Terry", "last_name": "Pratchett"},
            {"first_name": "Neil", "last_name": "Gaiman"},
        ],
    )
    res = _suggest(client, book["id"], primary_author_id=999999)
    assert res.status_code == 400, res.text


def test_primary_author_id_with_zero_authors_returns_400(client: TestClient):
    book = _create_book(client, title="No Authors Here")
    assert book["authors"] == []
    res = _suggest(client, book["id"], primary_author_id=999999)
    assert res.status_code == 400, res.text


def test_primary_author_id_mismatched_with_single_author_returns_400(client: TestClient):
    book = _create_book(
        client,
        title="Nineteen Eighty-Four",
        authors=[{"first_name": "George", "last_name": "Orwell"}],
    )
    wrong_id = book["authors"][0]["id"] + 999999
    res = _suggest(client, book["id"], primary_author_id=wrong_id)
    assert res.status_code == 400, res.text


def test_primary_author_id_matching_single_author_is_accepted(client: TestClient):
    book = _create_book(
        client,
        title="Nineteen Eighty-Four",
        authors=[{"first_name": "George", "last_name": "Orwell"}],
        genres_tags="Science Fiction",
    )
    author_id = book["authors"][0]["id"]
    res = _suggest(client, book["id"], primary_author_id=author_id)
    assert res.status_code == 200, res.text
    assert res.json()["cutter_number"] == classification_service.suggest_cutter("Orwell")


def test_no_genre_match_falls_back_to_default_class(client: TestClient):
    book = _create_book(client, title="Untitled Ramblings", genres_tags="Zzz Unmapped Tag")
    res = _suggest(client, book["id"])
    assert res.status_code == 200, res.text
    assert res.json()["lcc_call_number"] == classification_service.DEFAULT_LCC_CLASS

    book_no_tags = _create_book(client, title="No Tags At All")
    res_no_tags = _suggest(client, book_no_tags["id"])
    assert res_no_tags.status_code == 200, res_no_tags.text
    assert res_no_tags.json()["lcc_call_number"] == classification_service.DEFAULT_LCC_CLASS


def test_suggest_missing_book_returns_404(client: TestClient):
    res = _suggest(client, 999999)
    assert res.status_code == 404


def test_confirm_flow_persists_via_put_and_shows_on_get(client: TestClient):
    book = _create_book(client, title="A Brief History of Time", genres_tags="History")
    suggestion = _suggest(client, book["id"]).json()

    put_res = client.put(
        f"/api/v1/books/{book['id']}",
        json={
            "lcc_call_number": suggestion["lcc_call_number"],
            "cutter_number": suggestion["cutter_number"],
        },
    )
    assert put_res.status_code == 200, put_res.text
    assert put_res.json()["lcc_call_number"] == suggestion["lcc_call_number"]
    assert put_res.json()["cutter_number"] == suggestion["cutter_number"]

    fetched = client.get(f"/api/v1/books/{book['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["lcc_call_number"] == suggestion["lcc_call_number"]
    assert fetched.json()["cutter_number"] == suggestion["cutter_number"]


def test_book_with_neither_field_set_reads_as_null(client: TestClient):
    book = _create_book(client, title="Plain Book")
    assert book["lcc_call_number"] is None
    assert book["cutter_number"] is None

    fetched = client.get(f"/api/v1/books/{book['id']}")
    assert fetched.json()["lcc_call_number"] is None
    assert fetched.json()["cutter_number"] is None


def test_classification_never_touches_isbn_service():
    assert "app.services.isbn_service" not in getattr(classification_service, "__dict__", {})
    assert not hasattr(classification_service, "isbn_service")
    assert not hasattr(classification_service, "lookup_isbn")
