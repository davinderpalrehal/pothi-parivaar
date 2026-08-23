from typing import Generator
from sqlalchemy import event, Engine
from sqlmodel import SQLModel, create_engine, Session
from app.config import settings
from app.services.author_migration import migrate_book_author_strings
from app.services.location_service import LOCATION_TRIPLE_INDEX_SQL

# Create SQLite engine
connect_args = {"check_same_thread": False}
engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args=connect_args,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and normal synchronous writing for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


def migrate_schema(db_engine: Engine) -> None:
    """Apply additive SQLite upgrades required by newer model fields.

    SQLModel's ``create_all`` creates missing tables but intentionally does not
    add columns to existing ones. These additive upgrades keep a family's
    existing local catalog usable when reader-profile fields are introduced,
    and install the case-insensitive location triple unique index.
    """
    with db_engine.begin() as connection:
        reader_columns = {
            row[1] for row in connection.exec_driver_sql("PRAGMA table_info(reader)")
        }
        if reader_columns:
            if "age_group" not in reader_columns:
                connection.exec_driver_sql("ALTER TABLE reader ADD COLUMN age_group VARCHAR")
            if "created_at" not in reader_columns:
                connection.exec_driver_sql("ALTER TABLE reader ADD COLUMN created_at DATETIME")
            connection.exec_driver_sql(
                "UPDATE reader SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"
            )
        session_columns = {
            row[1] for row in connection.exec_driver_sql("PRAGMA table_info(readingsession)")
        }
        if session_columns:
            if "notes" not in session_columns:
                connection.exec_driver_sql("ALTER TABLE readingsession ADD COLUMN notes VARCHAR")
            if "rating" not in session_columns:
                connection.exec_driver_sql("ALTER TABLE readingsession ADD COLUMN rating INTEGER")

        location_table = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='location'"
        ).first()
        book_table = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='book'"
        ).first()
        if location_table:
            connection.exec_driver_sql("UPDATE location SET unit = '' WHERE unit IS NULL")
            connection.exec_driver_sql("UPDATE location SET shelf = '' WHERE shelf IS NULL")
            if book_table:
                connection.exec_driver_sql(
                    """
                    INSERT INTO location (room, unit, shelf)
                    SELECT b.room, b.unit, b.shelf FROM (
                      SELECT
                        TRIM(location_room) AS room,
                        TRIM(COALESCE(location_unit, '')) AS unit,
                        TRIM(COALESCE(location_shelf, '')) AS shelf
                      FROM book
                      WHERE location_room IS NOT NULL AND TRIM(location_room) != ''
                      GROUP BY
                        lower(trim(location_room)),
                        lower(trim(COALESCE(location_unit, ''))),
                        lower(trim(COALESCE(location_shelf, '')))
                    ) b
                    WHERE NOT EXISTS (
                      SELECT 1 FROM location l
                      WHERE lower(trim(l.room)) = lower(b.room)
                        AND lower(trim(l.unit)) = lower(b.unit)
                        AND lower(trim(l.shelf)) = lower(b.shelf)
                    )
                    """
                )
            connection.exec_driver_sql(
                """
                DELETE FROM location
                WHERE id NOT IN (
                  SELECT MIN(id) FROM location
                  GROUP BY lower(trim(room)), lower(trim(unit)), lower(trim(shelf))
                )
                """
            )
            connection.exec_driver_sql(LOCATION_TRIPLE_INDEX_SQL)

        if book_table:
            book_columns = {
                row[1] for row in connection.exec_driver_sql("PRAGMA table_info(book)")
            }
            if "publisher_id" not in book_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE book ADD COLUMN publisher_id INTEGER"
                )
        bookauthor_table = connection.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='bookauthor'"
        ).first()

    if book_table and bookauthor_table:
        with Session(db_engine) as session:
            migrate_book_author_strings(session)


def init_db() -> None:
    """Create database tables and apply safe additive schema upgrades."""
    SQLModel.metadata.create_all(engine)
    migrate_schema(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency for providing database sessions."""
    with Session(engine) as session:
        yield session
