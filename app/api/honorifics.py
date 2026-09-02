from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.models import Honorific, HonorificCreate, HonorificRead, HonorificUpdate
from app.services.honorific_service import (
    create_honorific,
    delete_honorific,
    list_honorifics,
    update_honorific,
)

router = APIRouter(prefix="/honorifics", tags=["Honorifics"])


@router.get("", response_model=list[HonorificRead])
def get_honorifics(session: Session = Depends(get_session)) -> list[HonorificRead]:
    """List the household honorific list, including disabled rows."""
    return list_honorifics(session)


@router.post("", response_model=HonorificRead, status_code=status.HTTP_201_CREATED)
def post_honorific(
    honorific_in: HonorificCreate,
    session: Session = Depends(get_session),
) -> HonorificRead:
    """Add a prefix or suffix honorific. Duplicate tokens+role is rejected."""
    try:
        row = create_honorific(
            session,
            honorific_in.tokens,
            honorific_in.role,
            honorific_in.abbreviation,
            honorific_in.enabled,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    session.commit()
    session.refresh(row)
    return row


@router.put("/{honorific_id}", response_model=HonorificRead)
def put_honorific(
    honorific_id: int,
    honorific_in: HonorificUpdate,
    session: Session = Depends(get_session),
) -> HonorificRead:
    """Change tokens, role, abbreviation, or enabled. Duplicate tokens+role is rejected."""
    row = session.get(Honorific, honorific_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Honorific not found")
    data = honorific_in.model_dump(exclude_unset=True)
    try:
        row = update_honorific(
            session,
            row,
            tokens=data.get("tokens"),
            role=data.get("role"),
            abbreviation=data.get("abbreviation"),
            enabled=data.get("enabled"),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    session.commit()
    session.refresh(row)
    return row


@router.delete("/{honorific_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_honorific(
    honorific_id: int,
    session: Session = Depends(get_session),
) -> None:
    row = session.get(Honorific, honorific_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Honorific not found")
    delete_honorific(session, row)
    session.commit()
