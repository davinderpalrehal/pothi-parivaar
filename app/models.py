from datetime import datetime, date, timezone
from typing import Optional
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


class ReadingSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id", index=True)
    reader_id: int = Field(foreign_key="reader.id", index=True)
    status: str = Field(default="reading")  # reading, finished, abandoned
    current_page: int = Field(default=0)
    start_date: Optional[date] = Field(default_factory=date.today)
    finish_date: Optional[date] = None


class Location(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room: str
    unit: str
    shelf: str


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


class ReaderRead(SQLModel):
    id: int
    name: str
    avatar_icon: Optional[str] = "mdi-account"


class ReadingSessionCreate(SQLModel):
    book_id: int
    reader_id: int
    status: Optional[str] = "reading"
    current_page: Optional[int] = 0
    start_date: Optional[date] = None


class ReadingSessionUpdate(SQLModel):
    status: Optional[str] = None
    current_page: Optional[int] = None
    finish_date: Optional[date] = None


class ReadingSessionRead(SQLModel):
    id: int
    book_id: int
    reader_id: int
    status: str
    current_page: int
    start_date: Optional[date] = None
    finish_date: Optional[date] = None


class LocationCreate(SQLModel):
    room: str
    unit: str
    shelf: str


class LocationRead(SQLModel):
    id: int
    room: str
    unit: str
    shelf: str


class HealthResponse(SQLModel):
    status: str
    app: str
