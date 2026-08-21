from datetime import datetime, date, timezone
from typing import Literal, Optional
from pydantic import field_validator
from sqlmodel import SQLModel, Field


# ==============================================================================
# Database Table Models
# ==============================================================================

class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    author: str = Field(index=True)
    publication_year: Optional[int] = None
    isbn: Optional[str] = Field(default=None, index=True)
    summary: Optional[str] = None
    cover_url: Optional[str] = None
    page_count: Optional[int] = None
    genres_tags: Optional[str] = None
    formats: Optional[str] = "physical"
    location_room: Optional[str] = None
    location_unit: Optional[str] = None
    location_shelf: Optional[str] = None
    read_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Reader(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    avatar_icon: Optional[str] = "mdi-account"
    age_group: Optional[str] = None  # e.g. "child-10", "child-7", "adult"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReadingSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    reader_id: int = Field(foreign_key="reader.id", index=True)
    status: str = Field(default="reading")  # reading, finished, abandoned
    current_page: int = Field(default=0)
    start_date: Optional[date] = Field(default_factory=date.today)
    finish_date: Optional[date] = None
    notes: Optional[str] = None
    rating: Optional[int] = None  # 1-5 rating on completion


class Location(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room: str
    unit: str = ""
    shelf: str = ""


# ==============================================================================
# Request / Response Schemas
# ==============================================================================

class BookCreate(SQLModel):
    title: str
    author: str
    publication_year: Optional[int] = None
    isbn: Optional[str] = None
    summary: Optional[str] = None
    cover_url: Optional[str] = None
    page_count: Optional[int] = None
    genres_tags: Optional[str] = None
    formats: Optional[str] = "physical"
    location_room: Optional[str] = None
    location_unit: Optional[str] = None
    location_shelf: Optional[str] = None


class BookUpdate(SQLModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publication_year: Optional[int] = None
    isbn: Optional[str] = None
    summary: Optional[str] = None
    cover_url: Optional[str] = None
    page_count: Optional[int] = None
    genres_tags: Optional[str] = None
    formats: Optional[str] = None
    location_room: Optional[str] = None
    location_unit: Optional[str] = None
    location_shelf: Optional[str] = None
    read_count: Optional[int] = None


class BookRead(SQLModel):
    id: int
    title: str
    author: str
    publication_year: Optional[int] = None
    isbn: Optional[str] = None
    summary: Optional[str] = None
    cover_url: Optional[str] = None
    page_count: Optional[int] = None
    genres_tags: Optional[str] = None
    formats: Optional[str] = "physical"
    location_room: Optional[str] = None
    location_unit: Optional[str] = None
    location_shelf: Optional[str] = None
    read_count: int = 0
    created_at: datetime


class ReaderCreate(SQLModel):
    name: str
    avatar_icon: Optional[str] = "mdi-account"
    age_group: Optional[str] = None


class ReaderUpdate(SQLModel):
    name: Optional[str] = None
    avatar_icon: Optional[str] = None
    age_group: Optional[str] = None


class ReaderRead(SQLModel):
    id: int
    name: str
    avatar_icon: Optional[str] = "mdi-account"
    age_group: Optional[str] = None
    created_at: Optional[datetime] = None


class ReadingSessionCreate(SQLModel):
    book_id: int
    reader_id: int
    status: Literal["to_read", "reading", "finished", "abandoned"] = "reading"
    current_page: Optional[int] = 0
    start_date: Optional[date] = None
    notes: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class ReadingSessionUpdate(SQLModel):
    status: Optional[Literal["to_read", "reading", "finished", "abandoned"]] = None
    current_page: Optional[int] = None
    finish_date: Optional[date] = None
    notes: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class ReadingSessionRead(SQLModel):
    id: int
    book_id: int
    reader_id: int
    status: str
    current_page: int
    start_date: Optional[date] = None
    finish_date: Optional[date] = None
    notes: Optional[str] = None
    rating: Optional[int] = None


class ReaderActivityRead(SQLModel):
    id: int
    book_id: int
    reader_id: int
    status: str
    current_page: int
    start_date: Optional[date] = None
    finish_date: Optional[date] = None
    notes: Optional[str] = None
    rating: Optional[int] = None
    reader: ReaderRead
    book: BookRead
    progress_percent: float = 0.0


class ReaderStatsRead(SQLModel):
    reader: ReaderRead
    total_reading: int
    total_finished: int
    total_pages_read: int
    active_sessions: list[ReaderActivityRead]
    history: list[ReaderActivityRead]


class LocationCreate(SQLModel):
    room: str
    unit: str = ""
    shelf: str = ""

    @field_validator("room")
    @classmethod
    def room_must_not_be_blank(cls, value: str) -> str:
        stripped = (value or "").strip()
        if not stripped:
            raise ValueError("room must not be blank")
        return stripped

    @field_validator("unit", "shelf", mode="before")
    @classmethod
    def blank_unit_shelf(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()


class LocationRead(SQLModel):
    id: int
    room: str
    unit: str
    shelf: str


class HealthResponse(SQLModel):
    status: str
    app: str
