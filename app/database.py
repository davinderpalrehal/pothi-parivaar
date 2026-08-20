from typing import Generator
from sqlalchemy import event, Engine
from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

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
    existing local catalog usable when reader-profile fields are introduced.
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


def init_db() -> None:
    """Create database tables and apply safe additive schema upgrades."""
    SQLModel.metadata.create_all(engine)
    migrate_schema(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency for providing database sessions."""
    with Session(engine) as session:
        yield session
