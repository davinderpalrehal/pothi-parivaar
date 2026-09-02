import copy
import pickle

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.main import app
from app.database import get_session
from app.services import book_service, classification_service

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


def test_suggest_lcc_class_matches_a_domain_keyword_in_the_title_alone():
    # 37 of the 46 real books carry no genres_tags at all -- the title is the
    # only signal they have.
    match = classification_service.suggest_lcc_class(
        None, "A Brief Introduction To The Sikh Faith"
    )
    assert match == "BL2017"
    assert match.source == "title"
    assert match.matched_keyword == "sikh"


def test_suggest_lcc_class_checks_genres_before_title():
    match = classification_service.suggest_lcc_class("Hinduism, Rituals", "Sikh Concepts")
    assert match == "BL1100"
    assert match.source == "genres"
    assert match.matched_keyword == "hindu"


def test_suggest_lcc_class_subject_beats_audience():
    # "guru" (BL2017) must be reached before "bed time" (PZ).
    match = classification_service.suggest_lcc_class(
        None, "Bed time stories 4 - Guru Tegh Bahadur ji"
    )
    assert match == "BL2017"
    assert match.matched_keyword == "guru"


def test_domain_table_is_searched_before_the_legacy_table():
    # "biography" -> CT is a legacy entry; the domain "buddha" entry wins.
    assert classification_service.suggest_lcc_class(None, "Gautam Buddha a Biography") == "BQ"


def test_legacy_genre_entries_are_preserved_unchanged():
    assert classification_service.suggest_lcc_class("History, Kids") == "D"
    assert classification_service.suggest_lcc_class("History, Kids", "Some Title") == "D"
    assert classification_service.suggest_lcc_class("Biography") == "CT"
    assert classification_service.suggest_lcc_class("Cooking") == "TX"


@pytest.mark.parametrize(
    "title",
    [
        "Heartland",          # "art"
        "Smart Kids",         # "art"
        "A Part of the Story",  # "art"
        "Charting a Course",  # "art"
        "Wonders of the Earth",  # "art"
        "Particle Physics",   # "art"
        "Lawrence of Arabia",  # "law"
    ],
)
def test_legacy_keywords_are_never_matched_against_a_title(title):
    """GENRE_LCC_MAP entries are bare substrings tuned for curated tags.

    Run against free-text titles they misfire, so the legacy table must stay
    genres-only. Titles are matched by DOMAIN_LCC_MAP alone.
    """
    match = classification_service.suggest_lcc_class(None, title)
    assert match == classification_service.DEFAULT_LCC_CLASS
    assert match.source == "default"
    assert match.matched_keyword is None


@pytest.mark.parametrize(
    "title",
    [
        "A Journey Through Colorado",      # "color"
        "The Temples of Mathura",          # "math"
        "Aftermath of War",                # "math"
        "The Brain Displays Its Power",    # "plays"
        "Traceability in Supply Chains",   # "trace"
        "Watercolor Painting",             # "color"
    ],
)
def test_domain_keywords_match_on_word_boundaries_only(title):
    """Domain keywords are matched as whole words, not bare substrings.

    Every title here embeds a domain keyword inside a longer word and would be
    misclassified by substring matching. This also guards the suffix rule in
    ``_KEYWORD_SUFFIXES``: none of these words is a keyword plus an absorbed
    suffix, so allowing -s/-es/-ism/-ist must not resurrect any of them.
    """
    match = classification_service.suggest_lcc_class(None, title)
    assert match == classification_service.DEFAULT_LCC_CLASS
    assert match.source == "default"
    assert match.matched_keyword is None


@pytest.mark.parametrize(
    "title,expected,expected_keyword",
    [
        ("Indian Comics Anthology", "PN6790", "comic"),
        ("Lives of the Gurus", "BL2017", "guru"),
        ("The Four Vedas", "BL1100", "veda"),
        ("Buddhism Today", "BQ", "buddh"),
        ("Sikhs in Britain", "BL2017", "sikh"),
        ("Reusable stickers", "PZ", "sticker"),
    ],
)
def test_domain_keywords_absorb_regular_inflections(title, expected, expected_keyword):
    """A keyword covers its own -s/-es/-ism/-ist forms.

    The table stores the base form only; the compiled pattern absorbs the
    inflection. Without this, boundary matching would force every plural and
    -ism/-ist form to be enumerated by hand.
    """
    match = classification_service.suggest_lcc_class(None, title)
    assert match == expected
    assert match.matched_keyword == expected_keyword


def test_buddhist_plural_matches_despite_single_suffix_absorption():
    """The suffix rule absorbs one suffix, so "buddh"+ist cannot also take "s".

    A dedicated "buddhist" entry covers the plural; without it *Buddhists in
    Punjab* fell through to the flagged default.
    """
    assert classification_service.suggest_lcc_class(None, "Buddhists in Punjab") == "BQ"
    assert classification_service.suggest_lcc_class(None, "Buddhist Art") == "BQ"
    assert classification_service.suggest_lcc_class(None, "Buddhism Today") == "BQ"


def test_word_boundaries_do_not_break_a_real_multi_word_match():
    # The counterpart to the guard above: boundaries must not cost real hits.
    assert classification_service.suggest_lcc_class(None, "Trace And Color Objects") == "PZ"


@pytest.mark.parametrize(
    "title,expected_keyword",
    [
        ("Bhai Maharaj Singh", "bhai"),
        ("Sakhis of Bhai", "bhai"),
        ("Bhai, Vol 2", "bhai"),
    ],
)
def test_bhai_matches_as_a_whole_word_wherever_it_sits(title, expected_keyword):
    match = classification_service.suggest_lcc_class(None, title)
    assert match == "BL2017"
    assert match.matched_keyword == expected_keyword


def test_bhai_does_not_match_inside_a_longer_word():
    # "Bhairav" is a raga, not Bhai Sahib.
    match = classification_service.suggest_lcc_class(None, "Bhairav Ragas")
    assert match == classification_service.DEFAULT_LCC_CLASS
    assert match.source == "default"


@pytest.mark.parametrize(
    "genres,title,expected,expected_keyword",
    [
        # A curated tag outranks a title match even across tables: the legacy
        # table is exhausted against genres_tags before title is looked at.
        ("Cooking", "Sikh Recipes", "TX", "cooking"),
        ("Biography", "Guru Nanak", "CT", "biography"),
        # ...but a domain hit in genres still beats a legacy hit in genres.
        ("Sikhs, History", "History of the Sikhs. v2", "BL2017", "sikh"),
    ],
)
def test_genres_are_fully_exhausted_before_the_title_is_tried(
    genres, title, expected, expected_keyword
):
    match = classification_service.suggest_lcc_class(genres, title)
    assert match == expected
    assert match.source == "genres"
    assert match.matched_keyword == expected_keyword


def test_lcc_class_match_survives_copy_and_pickle():
    match = classification_service.suggest_lcc_class(None, "A Brief Introduction To The Sikh Faith")
    for clone in (copy.copy(match), copy.deepcopy(match), pickle.loads(pickle.dumps(match))):
        assert clone == "BL2017"
        assert clone.source == "title"
        assert clone.matched_keyword == "sikh"


def test_suggest_lcc_class_flags_the_default_fallback():
    match = classification_service.suggest_lcc_class(None, "To Have And To Hold")
    assert match == classification_service.DEFAULT_LCC_CLASS
    assert match.source == "default"
    assert match.matched_keyword is None

    empty = classification_service.suggest_lcc_class(None, None)
    assert empty == classification_service.DEFAULT_LCC_CLASS
    assert empty.source == "default"


def test_suggest_lcc_class_result_behaves_as_a_plain_string():
    match = classification_service.suggest_lcc_class(None, "COLOURING BOOK FOR DORA")
    assert isinstance(match, str)
    assert str(match) == "PZ"
    assert f"{match}" == "PZ"


# ------------------------------------------------------------------------------
# Corpus fixture -- real titles from the collection, classified with no genres.
# ------------------------------------------------------------------------------

# (title, expected class, expected matched keyword). The keyword is asserted
# too, so the ordering claims in DOMAIN_LCC_MAP are pinned directly rather than
# merely implied by the resulting class.
CORPUS_TITLES: list[tuple[str, str, str]] = [
    ("A Brief Introduction To The Sikh Faith", "BL2017", "sikh"),
    # Subject beats audience: "guru" is reached before "bed time" -> PZ.
    ("Bed time stories 4 - Guru Tegh Bahadur ji", "BL2017", "guru"),
    ("Vedic Eternal Truth Part Two", "BL1100", "vedic"),
    # "buddha" is reached before the legacy "biography" -> CT.
    ("Gautam Buddha a Biography", "BQ", "buddha"),
    ("COLOURING BOOK FOR DORA", "PZ", "colouring"),
    ("Trace And Color Objects", "PZ", "color"),
    ("Power Maths Reception Journal a - 2021 Edition", "QA", "math"),
    ("Time for Spelling", "LB1573", "spelling"),
    ("SUPER LARGE PRINT CROSSWORD Book 7", "GV1507", "crossword"),
    ("Guinness World Records 2002", "AG", "world records"),
    ("Great Plays of Kalidasa", "PK", "kalidasa"),
    ("Hands-On Large Language Models", "QA76", "language models"),
    ("THE HUMAN BODY", "QP", "human body"),
    # "sticker" is reached before "ocean" -> QL.
    ("Ocean Creatures with over 70 reusable stickers!", "PZ", "sticker"),
]

# Genuinely ambiguous titles: these must stay flagged rather than be guessed at.
CORPUS_UNMATCHED_TITLES: list[str] = [
    "My Baby Book: The First Five Years",
    "I Love You This Much",
    "At The Feet Of The Master",
    "To Have And To Hold",
    "TERCENTENARY CELEBRATIONS",
    "Cinderella",
    "Aladdin and the Magic Lamp",
]


@pytest.mark.parametrize("title,expected,expected_keyword", CORPUS_TITLES)
def test_corpus_titles_classify_without_genres(title: str, expected: str, expected_keyword: str):
    match = classification_service.suggest_lcc_class(None, title)
    assert match == expected, f"{title!r} -> {match!r} (keyword {match.matched_keyword!r})"
    assert match.source == "title"
    assert match.matched_keyword == expected_keyword


@pytest.mark.parametrize("title", CORPUS_UNMATCHED_TITLES)
def test_corpus_ambiguous_titles_stay_flagged_as_default(title: str):
    match = classification_service.suggest_lcc_class(None, title)
    assert match == classification_service.DEFAULT_LCC_CLASS
    assert match.source == "default"
    assert match.matched_keyword is None


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


def test_suggest_after_saved_class_uses_updated_genres(client: TestClient):
    book = _create_book(client, title="A Quiet Evening", genres_tags="History")
    first = _suggest(client, book["id"]).json()
    put_res = client.put(
        f"/api/v1/books/{book['id']}",
        json={
            "lcc_call_number": first["lcc_call_number"],
            "cutter_number": first["cutter_number"],
        },
    )
    assert put_res.status_code == 200, put_res.text
    assert put_res.json()["lcc_call_number"] == "D"

    tagged = client.put(
        f"/api/v1/books/{book['id']}",
        json={"genres_tags": "Science Fiction"},
    )
    assert tagged.status_code == 200, tagged.text
    assert tagged.json()["lcc_call_number"] == "D"

    second = _suggest(client, book["id"])
    assert second.status_code == 200, second.text
    body = second.json()
    assert body["lcc_call_number"] == "PZ"
    assert body["lcc_call_number"] != tagged.json()["lcc_call_number"]


def test_book_with_neither_field_set_reads_as_null(client: TestClient):
    book = _create_book(client, title="Plain Book")
    assert book["lcc_call_number"] is None
    assert book["cutter_number"] is None

    fetched = client.get(f"/api/v1/books/{book['id']}")
    assert fetched.json()["lcc_call_number"] is None
    assert fetched.json()["cutter_number"] is None


def test_title_only_suggestion_reaches_the_api_response(client: TestClient):
    book = _create_book(client, title="A Brief Introduction To The Sikh Faith")
    res = _suggest(client, book["id"])
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["lcc_call_number"] == "BL2017"
    assert body["class_source"] == "title"
    assert body["class_matched_keyword"] == "sikh"


def test_unmatched_suggestion_is_marked_default_in_the_api_response(client: TestClient):
    book = _create_book(client, title="To Have And To Hold")
    res = _suggest(client, book["id"])
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["lcc_call_number"] == classification_service.DEFAULT_LCC_CLASS
    assert body["class_source"] == "default"
    assert body["class_matched_keyword"] is None


def test_class_marker_is_not_persisted_by_the_confirm_put(client: TestClient, session: Session):
    book = _create_book(client, title="A Brief Introduction To The Sikh Faith")
    suggestion = _suggest(client, book["id"]).json()
    assert suggestion["class_source"] == "title"

    # Send the markers back deliberately: the dialog does not, but nothing stops
    # another client from echoing the whole suggestion body. They must be
    # ignored rather than accepted onto the book.
    put_res = client.put(
        f"/api/v1/books/{book['id']}",
        json={
            "lcc_call_number": suggestion["lcc_call_number"],
            "cutter_number": suggestion["cutter_number"],
            "class_source": suggestion["class_source"],
            "class_matched_keyword": suggestion["class_matched_keyword"],
        },
    )
    assert put_res.status_code == 200, put_res.text
    saved = put_res.json()
    assert saved["lcc_call_number"] == "BL2017"
    assert saved["cutter_number"] == suggestion["cutter_number"]
    assert "class_source" not in saved
    assert "class_matched_keyword" not in saved

    fetched = client.get(f"/api/v1/books/{book['id']}").json()
    assert fetched["lcc_call_number"] == "BL2017"
    assert "class_source" not in fetched
    assert "class_matched_keyword" not in fetched
    # The markers reached neither the response models nor the stored row.
    stored = book_service.get_book(session, book["id"])
    assert not hasattr(stored, "class_source")
    assert not hasattr(stored, "class_matched_keyword")


def test_classification_never_touches_isbn_service():
    assert "app.services.isbn_service" not in getattr(classification_service, "__dict__", {})
    assert not hasattr(classification_service, "isbn_service")
    assert not hasattr(classification_service, "lookup_isbn")
