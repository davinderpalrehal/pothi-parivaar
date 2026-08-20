from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import Location, LocationCreate, LocationRead
from app.services.location_service import locations_summary, upsert_location

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("", response_model=list[LocationRead])
def list_locations(session: Session = Depends(get_session)) -> list[LocationRead]:
    """List physical locations registered in the house."""
    return list(session.exec(select(Location)).all())


@router.post(
    "",
    response_model=LocationRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {"description": "Existing location returned", "model": LocationRead},
        201: {"description": "Location created", "model": LocationRead},
    },
)
def create_location(
    location_in: LocationCreate,
    response: Response,
    session: Session = Depends(get_session),
) -> LocationRead:
    """Create a location or return the existing row for the same normalized triple."""
    location, created = upsert_location(
        session, location_in.room, location_in.unit, location_in.shelf
    )
    assert location is not None
    session.commit()
    session.refresh(location)
    if not created:
        response.status_code = status.HTTP_200_OK
    return location


@router.get("/summary")
def get_locations_summary(session: Session = Depends(get_session)) -> dict:
    """Return registry shelves unioned with book occupancy counts."""
    return locations_summary(session)
