import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.main import app
from app.database import get_session, migrate_schema
from app.models import Author, Book, BookAuthor, Publisher
from app.services.author_migration import migrate_book_author_strings

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


def test_two_author_create_stores_order_and_derived_author(client: TestClient):
    res = client.post(
        "/api/v1/books",
        json={
            "title": "How to Win Friends",
            "authors": [
                {"first_name": "Dale", "last_name": "Carnegie"},
                {"first_name": "Jane", "last_name": "Doe"},
            ],
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["author"] == "D. Carnegie, J. Doe"
    assert [a["first_name"] for a in body["authors"]] == ["Dale", "Jane"]
    assert [a["last_name"] for a in body["authors"]] == ["Carnegie", "Doe"]
    assert body["publisher"] is None

    fetched = client.get(f"/api/v1/books/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["author"] == "D. Carnegie, J. Doe"
    assert [a["id"] for a in fetched.json()["authors"]] == [a["id"] for a in body["authors"]]


def test_author_missing_first_or_last_name_returns_422(client: TestClient):
    missing_first = client.post(
        "/api/v1/books",
        json={
            "title": "No First",
            "authors": [{"last_name": "Carnegie"}],
        },
    )
    assert missing_first.status_code == 422

    missing_last = client.post(
        "/api/v1/books",
        json={
            "title": "No Last",
            "authors": [{"first_name": "Cher"}],
        },
    )
    assert missing_last.status_code == 422


def test_magazine_title_only_and_optional_publisher(client: TestClient):
    missing_title = client.post("/api/v1/books", json={"publisher_name": "Nat Geo"})
    assert missing_title.status_code == 422

    magazine = client.post(
        "/api/v1/books",
        json={"title": "National Geographic", "publisher_name": "Nat Geo"},
    )
    assert magazine.status_code == 201, magazine.text
    body = magazine.json()
    assert body["author"] == ""
    assert body["authors"] == []
    assert body["publisher"]["name"] == "Nat Geo"

    untitled = client.post("/api/v1/books", json={"title": "Blank Magazine"})
    assert untitled.status_code == 201
    assert untitled.json()["authors"] == []
    assert untitled.json()["publisher"] is None


def test_mononym_last_name_is_single_space(client: TestClient):
    res = client.post(
        "/api/v1/books",
        json={
            "title": "The First Time",
            "authors": [{"first_name": "Cher", "last_name": " "}],
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["author"] == "Cher"
    assert body["authors"][0]["first_name"] == "Cher"
    assert body["authors"][0]["last_name"] == " "


def test_reuse_author_and_publisher_records(client: TestClient, session: Session):
    first = client.post(
        "/api/v1/books",
        json={
            "title": "Book One",
            "authors": [
                {"first_name": "Dale", "middle_name": "B.", "last_name": "Carnegie"}
            ],
            "publisher_name": "Simon & Schuster",
        },
    )
    assert first.status_code == 201, first.text
    second = client.post(
        "/api/v1/books",
        json={
            "title": "Book Two",
            "authors": [
                {"first_name": "Dale", "middle_name": "B.", "last_name": "Carnegie"}
            ],
            "publisher_name": "Simon & Schuster",
        },
    )
    assert second.status_code == 201, second.text
    assert first.json()["authors"][0]["id"] == second.json()["authors"][0]["id"]
    assert first.json()["publisher"]["id"] == second.json()["publisher"]["id"]
    assert session.exec(select(Author)).all().__len__() == 1
    assert session.exec(select(Publisher)).all().__len__() == 1


def test_search_matches_first_name_and_short_form(client: TestClient):
    created = client.post(
        "/api/v1/books",
        json={
            "title": "How to Win Friends",
            "authors": [
                {"first_name": "Dale", "middle_name": "B.", "last_name": "Carnegie"}
            ],
        },
    )
    assert created.status_code == 201
    book_id = created.json()["id"]

    by_first = client.get("/api/v1/books", params={"q": "Dale"})
    assert by_first.status_code == 200
    assert [b["id"] for b in by_first.json()] == [book_id]

    by_middle = client.get("/api/v1/books", params={"q": "B."})
    assert by_middle.status_code == 200
    assert [b["id"] for b in by_middle.json()] == [book_id]

    by_short = client.get("/api/v1/books", params={"q": "D. Carnegie"})
    assert by_short.status_code == 200
    assert [b["id"] for b in by_short.json()] == [book_id]

    none = client.get("/api/v1/books", params={"q": "NoSuchAuthor"})
    assert none.status_code == 200
    assert none.json() == []


def test_hermes_locate_matches_name_parts_and_short_form(client: TestClient):
    created = client.post(
        "/api/v1/books",
        json={
            "title": "How to Win Friends",
            "authors": [
                {"first_name": "Dale", "middle_name": "B.", "last_name": "Carnegie"}
            ],
            "location_room": "Study",
        },
    )
    assert created.status_code == 201
    book_id = created.json()["id"]

    by_first = client.get("/api/v1/hermes/locate/Dale")
    assert by_first.status_code == 200
    assert len(by_first.json()["matches"]) == 1
    assert by_first.json()["matches"][0]["id"] == book_id
    assert by_first.json()["matches"][0]["author"] == "D. Carnegie"

    by_middle = client.get("/api/v1/hermes/locate/B.")
    assert by_middle.status_code == 200
    assert [m["id"] for m in by_middle.json()["matches"]] == [book_id]

    by_short = client.get("/api/v1/hermes/locate/D. Carnegie")
    assert by_short.status_code == 200
    assert len(by_short.json()["matches"]) == 1
    assert by_short.json()["matches"][0]["id"] == book_id

    rec = client.get("/api/v1/hermes/recommend")
    assert rec.status_code == 200
    assert rec.json()["recommendations"][0]["author"] == "D. Carnegie"


def test_remove_one_author_leaves_the_other(client: TestClient):
    created = client.post(
        "/api/v1/books",
        json={
            "title": "Pair",
            "authors": [
                {"first_name": "Dale", "last_name": "Carnegie"},
                {"first_name": "Jane", "last_name": "Doe"},
            ],
        },
    )
    book_id = created.json()["id"]
    updated = client.put(
        f"/api/v1/books/{book_id}",
        json={"authors": [{"first_name": "Jane", "last_name": "Doe"}]},
    )
    assert updated.status_code == 200
    assert updated.json()["author"] == "J. Doe"
    assert len(updated.json()["authors"]) == 1
    assert updated.json()["authors"][0]["first_name"] == "Jane"


def test_legacy_author_string_is_split_and_derived(client: TestClient):
    res = client.post(
        "/api/v1/books",
        json={"title": "The Hobbit", "author": "J.R.R. Tolkien"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["author"] == "J. Tolkien"
    assert body["authors"][0]["first_name"] == "J.R.R."
    assert body["authors"][0]["last_name"] == "Tolkien"


def test_migration_splits_existing_author_strings(session: Session, client: TestClient):
    carnegie = Book(title="How to Win", author="D. Carnegie")
    pair = Book(title="Anthology", author="A, B")
    empty = Book(title="Magazine", author="")
    session.add(carnegie)
    session.add(pair)
    session.add(empty)
    session.commit()
    session.refresh(carnegie)
    session.refresh(pair)
    session.refresh(empty)

    converted = migrate_book_author_strings(session)
    assert converted == 2
    assert migrate_book_author_strings(session) == 0

    session.expire_all()
    carnegie_links = session.exec(
        select(BookAuthor).where(BookAuthor.book_id == carnegie.id)
    ).all()
    assert len(carnegie_links) == 1
    author = session.get(Author, carnegie_links[0].author_id)
    assert author.first_name == "D."
    assert author.last_name == "Carnegie"
    assert session.get(Book, carnegie.id).author == "D. Carnegie"

    pair_authors = session.exec(
        select(Author)
        .join(BookAuthor, BookAuthor.author_id == Author.id)
        .where(BookAuthor.book_id == pair.id)
        .order_by(BookAuthor.display_order)
    ).all()
    assert [(a.first_name, a.last_name) for a in pair_authors] == [
        ("A", " "),
        ("B", " "),
    ]
    assert session.get(Book, pair.id).author == "A, B"

    assert session.exec(select(BookAuthor).where(BookAuthor.book_id == empty.id)).all() == []
    assert session.get(Book, empty.id).author == ""
    assert session.exec(select(Publisher)).all() == []

    by_last = client.get("/api/v1/books", params={"q": "Carnegie"})
    assert by_last.status_code == 200
    assert {b["id"] for b in by_last.json()} == {carnegie.id}

    by_short = client.get("/api/v1/books", params={"q": "D. Carnegie"})
    assert {b["id"] for b in by_short.json()} == {carnegie.id}


def test_migrate_schema_converts_legacy_author_strings():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(Book(title="How to Win", author="D. Carnegie"))
        session.commit()

    migrate_schema(engine)

    with Session(engine) as session:
        book = session.exec(select(Book)).first()
        links = session.exec(select(BookAuthor).where(BookAuthor.book_id == book.id)).all()
        assert len(links) == 1
        author = session.get(Author, links[0].author_id)
        assert author.first_name == "D."
        assert author.last_name == "Carnegie"
        assert book.author == "D. Carnegie"
    SQLModel.metadata.drop_all(engine)


def test_update_echoing_derived_author_keeps_stored_name_parts(client: TestClient):
    created = client.post(
        "/api/v1/books",
        json={
            "title": "How to Win",
            "authors": [{"first_name": "Dale", "last_name": "Carnegie"}],
        },
    )
    book_id = created.json()["id"]
    updated = client.put(
        f"/api/v1/books/{book_id}",
        json={"title": "How to Win Friends", "author": "D. Carnegie"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "How to Win Friends"
    assert updated.json()["authors"][0]["first_name"] == "Dale"
    assert updated.json()["authors"][0]["last_name"] == "Carnegie"


def test_migrate_schema_adds_publisher_id_to_legacy_book():
    legacy_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with legacy_engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE book (
                id INTEGER PRIMARY KEY,
                title VARCHAR NOT NULL,
                author VARCHAR NOT NULL,
                publication_year INTEGER,
                isbn VARCHAR,
                summary VARCHAR,
                cover_url VARCHAR,
                page_count INTEGER,
                genres_tags VARCHAR,
                formats VARCHAR,
                location_room VARCHAR,
                location_unit VARCHAR,
                location_shelf VARCHAR,
                read_count INTEGER DEFAULT 0,
                created_at DATETIME
            )
            """
        )
        connection.exec_driver_sql(
            "INSERT INTO book (id, title, author) VALUES (1, 'How to Win', 'D. Carnegie')"
        )

    SQLModel.metadata.create_all(legacy_engine)
    migrate_schema(legacy_engine)

    with legacy_engine.connect() as connection:
        column_names = {
            row[1] for row in connection.exec_driver_sql("PRAGMA table_info(book)")
        }
        assert "publisher_id" in column_names

    with Session(legacy_engine) as session:
        def get_session_override():
            return session

        app.dependency_overrides[get_session] = get_session_override
        try:
            client = TestClient(app)
            res = client.post(
                "/api/v1/books",
                json={"title": "National Geographic", "publisher_name": "Nat Geo"},
            )
            assert res.status_code == 201, res.text
            assert res.json()["publisher"]["name"] == "Nat Geo"
        finally:
            app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(legacy_engine)
