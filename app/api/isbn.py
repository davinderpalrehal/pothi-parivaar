from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.services.isbn_service import lookup_isbn

router = APIRouter(prefix="/isbn", tags=["ISBN Lookup"])


class IsbnLookupRead(BaseModel):
    """Advisory metadata returned by ISBN lookup. Never persisted automatically."""

    title: str = ""
    author: str = ""
    publication_year: Optional[int] = None
    isbn: Optional[str] = None
    summary: Optional[str] = None
    cover_url: Optional[str] = None
    page_count: Optional[int] = None
    genres_tags: Optional[str] = None
    formats: Optional[str] = "physical"


@router.get("/{isbn_code}", response_model=IsbnLookupRead)
async def get_isbn_metadata(isbn_code: str) -> IsbnLookupRead:
    """
    Look up book details by ISBN from Open Library.
    Acts strictly as an advisory pre-fill service.
    """
    metadata = await lookup_isbn(isbn_code)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metadata found for ISBN: {isbn_code}",
        )
    return metadata
