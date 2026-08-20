from fastapi import APIRouter, HTTPException, status
from app.services.isbn_service import lookup_isbn

router = APIRouter(prefix="/isbn", tags=["ISBN Lookup"])


@router.get("/{isbn_code}")
async def get_isbn_metadata(isbn_code: str):
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
