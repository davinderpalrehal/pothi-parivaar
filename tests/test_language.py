import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.main import app
from app.database import get_session
from app.models import normalize_additional_languages, normalize_language_code

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


# ==============================================================================
# Pure unit tests for the code normalizer
# ==============================================================================

def test_normalize_language_code_trims_and_lowercases():
    assert normalize_language_code("PAN") == "pan"
    assert normalize_language_code("  Pan  ") == "pan"


def test_normalize_language_code_treats_empty_as_none():
    assert normalize_language_code("") is None
    assert normalize_language_code("   ") is None
    assert normalize_language_code(None) is None


@pytest.mark.parametrize("bad", ["punjabi", "pa", "pan1", "p a", "pa-", "ਪੰਜ", "pann"])
def test_normalize_language_code_rejects_non_three_letter_input(bad):
    with pytest.raises(ValueError):
        normalize_language_code(bad)


def test_normalize_language_code_accepts_unknown_but_well_formed_code():
    assert normalize_language_code("zzz") == "zzz"


def test_normalize_additional_languages_trims_and_blanks_to_none():
    assert normalize_additional_languages("  san, hin  ") == "san, hin"
    assert normalize_additional_languages("") is None
    assert normalize_additional_languages("   ") is None
    assert normalize_additional_languages(None) is None


def test_normalize_additional_languages_leaves_free_text_alone():
    # Individual entries are deliberately unvalidated -- see the Design Notes.
    assert normalize_additional_languages("san, hin") == "san, hin"
    assert normalize_additional_languages("punjabi, gurmukhi") == "punjabi, gurmukhi"


# ==============================================================================
# API tests -- one per row of the I/O matrix
# ==============================================================================

def test_create_with_language_stores_lowercase_code(client: TestClient):
    created = _create_book(client, title="X", language="PAN")
    assert created["language"] == "pan"

    fetched = client.get(f"/api/v1/books/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["language"] == "pan"


def test_invalid_code_is_rejected_on_create(client: TestClient):
    res = client.post("/api/v1/books", json={"title": "X", "language": "punjabi"})
    assert res.status_code == 422


def test_invalid_code_is_rejected_on_update(client: TestClient):
    book = _create_book(client, title="X", language="pan")
    res = client.put(f"/api/v1/books/{book['id']}", json={"language": "punjabi"})
    assert res.status_code == 422

    unchanged = client.get(f"/api/v1/books/{book['id']}").json()
    assert unchanged["language"] == "pan"


def test_empty_string_update_clears_language_to_null(client: TestClient):
    book = _create_book(client, title="X", language="pan")
    res = client.put(f"/api/v1/books/{book['id']}", json={"language": ""})
    assert res.status_code == 200
    assert res.json()["language"] is None

    fetched = client.get(f"/api/v1/books/{book['id']}").json()
    assert fetched["language"] is None


def test_omitted_language_reads_back_null(client: TestClient):
    created = _create_book(client, title="No Language")
    assert created["language"] is None
    assert created["additional_languages"] is None


def test_multi_language_round_trips_both_fields(client: TestClient):
    created = _create_book(
        client, title="Multi", language="eng", additional_languages="san, hin"
    )
    assert created["language"] == "eng"
    assert created["additional_languages"] == "san, hin"

    fetched = client.get(f"/api/v1/books/{created['id']}").json()
    assert fetched["language"] == "eng"
    assert fetched["additional_languages"] == "san, hin"


def test_language_filter_narrows_to_matching_primary_language(client: TestClient):
    punjabi = _create_book(client, title="Punjabi Book", language="pan")
    _create_book(client, title="English Book", language="eng")
    _create_book(client, title="Unset Book")

    res = client.get("/api/v1/books", params={"language": "pan"})
    assert res.status_code == 200
    assert [book["id"] for book in res.json()] == [punjabi["id"]]


def test_language_filter_ignores_additional_languages(client: TestClient):
    _create_book(client, title="English plus", language="eng", additional_languages="pan")

    res = client.get("/api/v1/books", params={"language": "pan"})
    assert res.status_code == 200
    assert res.json() == []


def test_language_filter_combines_with_other_filters(client: TestClient):
    match = _create_book(
        client, title="Punjabi History", language="pan", genres_tags="History"
    )
    _create_book(client, title="Punjabi Fiction", language="pan", genres_tags="Fiction")
    _create_book(client, title="English History", language="eng", genres_tags="History")

    res = client.get("/api/v1/books", params={"language": "pan", "genre": "History"})
    assert res.status_code == 200
    assert [book["id"] for book in res.json()] == [match["id"]]


def test_language_filter_normalizes_case_and_padding(client: TestClient):
    punjabi = _create_book(client, title="Punjabi Book", language="pan")
    _create_book(client, title="English Book", language="eng")

    for raw in ["PAN", "  pan  ", "  PaN "]:
        res = client.get("/api/v1/books", params={"language": raw})
        assert res.status_code == 200, res.text
        assert [b["id"] for b in res.json()] == [punjabi["id"]], raw


def test_whitespace_only_language_filter_is_ignored_not_matched_against_blank(
    client: TestClient,
):
    ids = [
        _create_book(client, title="A", language="pan")["id"],
        _create_book(client, title="B", language="eng")["id"],
        _create_book(client, title="C")["id"],
    ]

    res = client.get("/api/v1/books", params={"language": "   "})
    assert res.status_code == 200
    assert sorted(b["id"] for b in res.json()) == sorted(ids)


def test_language_filter_miss_returns_empty_list_not_an_error(client: TestClient):
    _create_book(client, title="Punjabi Book", language="pan")

    res = client.get("/api/v1/books", params={"language": "zzz"})
    assert res.status_code == 200
    assert res.json() == []


def test_unfiltered_list_is_unaffected_by_mixed_languages(client: TestClient):
    ids = [
        _create_book(client, title="A", language="pan")["id"],
        _create_book(client, title="B", language="eng")["id"],
        _create_book(client, title="C")["id"],
    ]

    res = client.get("/api/v1/books")
    assert res.status_code == 200
    assert sorted(book["id"] for book in res.json()) == sorted(ids)


def test_setting_language_does_not_disturb_the_call_number(client: TestClient):
    book = _create_book(
        client,
        title="Classified",
        genres_tags="History",
        authors=[{"first_name": "Dale", "last_name": "Carnegie"}],
    )
    suggest_res = client.post(
        f"/api/v1/books/{book['id']}/classification/suggest", json={}
    )
    assert suggest_res.status_code == 200, suggest_res.text
    suggested = suggest_res.json()

    assign_res = client.put(
        f"/api/v1/books/{book['id']}",
        json={
            "lcc_call_number": suggested["lcc_call_number"],
            "cutter_number": suggested["cutter_number"],
        },
    )
    assert assign_res.status_code == 200, assign_res.text

    before = client.get(f"/api/v1/books/{book['id']}").json()
    # Guard against a vacuous pass: there must be a real call number to preserve.
    assert before["lcc_call_number"] is not None
    assert before["cutter_number"] is not None

    update_res = client.put(f"/api/v1/books/{book['id']}", json={"language": "pan"})
    assert update_res.status_code == 200, update_res.text
    after = client.get(f"/api/v1/books/{book['id']}").json()

    assert after["lcc_call_number"] == before["lcc_call_number"]
    assert after["cutter_number"] == before["cutter_number"]
    assert after["language"] == "pan"


def test_mul_is_stored_as_a_real_primary_language(client: TestClient):
    created = _create_book(client, title="Trilingual Reader", language="MUL")
    assert created["language"] == "mul"

    fetched = client.get(f"/api/v1/books/{created['id']}").json()
    assert fetched["language"] == "mul"

    res = client.get("/api/v1/books", params={"language": "mul"})
    assert res.status_code == 200
    assert [b["id"] for b in res.json()] == [created["id"]]


def test_explicit_json_null_clears_language_and_additional_languages(client: TestClient):
    book = _create_book(
        client, title="X", language="pan", additional_languages="eng, san"
    )
    res = client.put(
        f"/api/v1/books/{book['id']}",
        json={"language": None, "additional_languages": None},
    )
    assert res.status_code == 200, res.text
    assert res.json()["language"] is None
    assert res.json()["additional_languages"] is None

    fetched = client.get(f"/api/v1/books/{book['id']}").json()
    assert fetched["language"] is None
    assert fetched["additional_languages"] is None


def test_whitespace_only_additional_languages_is_stored_as_null(client: TestClient):
    created = _create_book(client, title="X", language="pan", additional_languages="   ")
    assert created["additional_languages"] is None


def test_additional_languages_is_trimmed_but_entries_survive_verbatim(
    client: TestClient,
):
    created = _create_book(
        client, title="X", language="eng", additional_languages="  san, hin  "
    )
    assert created["additional_languages"] == "san, hin"


# ==============================================================================
# Catalog languages endpoint
# ==============================================================================

def test_catalog_languages_reports_held_codes_with_counts(client: TestClient):
    _create_book(client, title="A", language="pan")
    _create_book(client, title="B", language="pan")
    _create_book(client, title="C", language="eng")
    _create_book(client, title="D", language="tam")
    _create_book(client, title="E")

    res = client.get("/api/v1/books/languages")
    assert res.status_code == 200, res.text
    assert res.json() == {
        "languages": [
            {"code": "pan", "book_count": 2},
            {"code": "eng", "book_count": 1},
            {"code": "tam", "book_count": 1},
        ],
        "missing_count": 1,
    }


def test_catalog_languages_includes_codes_outside_the_entry_shortlist(
    client: TestClient,
):
    _create_book(client, title="Tamil Book", language="tam")

    res = client.get("/api/v1/books/languages")
    assert res.status_code == 200
    assert [entry["code"] for entry in res.json()["languages"]] == ["tam"]


def test_catalog_languages_on_an_empty_catalog(client: TestClient):
    res = client.get("/api/v1/books/languages")
    assert res.status_code == 200
    assert res.json() == {"languages": [], "missing_count": 0}


def test_catalog_languages_route_is_not_shadowed_by_the_book_id_route(
    client: TestClient,
):
    """`/books/languages` must resolve before `/books/{book_id}`.

    Declared after it, FastAPI parses "languages" as an int book id and 422s.
    """
    res = client.get("/api/v1/books/languages")
    assert res.status_code == 200, res.text
    assert res.status_code != 422
    assert "languages" in res.json()


def test_catalog_languages_counts_only_the_primary_language(client: TestClient):
    _create_book(client, title="X", language="eng", additional_languages="pan, san")

    res = client.get("/api/v1/books/languages")
    assert res.json()["languages"] == [{"code": "eng", "book_count": 1}]


# ==============================================================================
# missing_language filter
# ==============================================================================

def test_missing_language_filter_returns_only_books_with_no_primary_language(
    client: TestClient,
):
    unset = _create_book(client, title="Unset Book")
    _create_book(client, title="Punjabi Book", language="pan")

    res = client.get("/api/v1/books", params={"missing_language": "true"})
    assert res.status_code == 200
    assert [book["id"] for book in res.json()] == [unset["id"]]


def test_missing_language_filter_matches_a_blank_stored_language(
    session, client: TestClient
):
    """The write validator only stores NULL, but the filter must not rely on it."""
    from app.models import Book

    blank = Book(title="Blank Language", language="")
    session.add(blank)
    session.commit()
    session.refresh(blank)

    res = client.get("/api/v1/books", params={"missing_language": "true"})
    assert res.status_code == 200
    assert [book["id"] for book in res.json()] == [blank.id]


def test_missing_language_combined_with_language_returns_empty(client: TestClient):
    _create_book(client, title="Punjabi Book", language="pan")
    _create_book(client, title="Unset Book")

    res = client.get(
        "/api/v1/books", params={"language": "pan", "missing_language": "true"}
    )
    assert res.status_code == 200
    assert res.json() == []


def test_missing_language_defaults_off_so_the_unfiltered_list_is_unchanged(
    client: TestClient,
):
    _create_book(client, title="Punjabi Book", language="pan")
    _create_book(client, title="Unset Book")

    baseline = client.get("/api/v1/books")
    explicit_false = client.get("/api/v1/books", params={"missing_language": "false"})

    assert baseline.status_code == 200
    assert len(baseline.json()) == 2
    assert explicit_false.json() == baseline.json()


def test_missing_language_combines_with_other_filters(client: TestClient):
    match = _create_book(client, title="Unset History", genres_tags="History")
    _create_book(client, title="Unset Fiction", genres_tags="Fiction")
    _create_book(client, title="Punjabi History", language="pan", genres_tags="History")

    res = client.get(
        "/api/v1/books", params={"missing_language": "true", "genre": "History"}
    )
    assert res.status_code == 200
    assert [book["id"] for book in res.json()] == [match["id"]]
