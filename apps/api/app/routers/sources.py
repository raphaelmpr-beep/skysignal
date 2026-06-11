"""
Sources router — /api/sources
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Source
from app.schemas import SourceCreate, SourceRead, SourceUpdate

router = APIRouter()


def _source_or_404(source_id: str, db: Session) -> Source:
    s = db.query(Source).filter(Source.id == source_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Source not found")
    return s


# ---------------------------------------------------------------------------
# List sources
# ---------------------------------------------------------------------------

@router.get("", response_model=dict)
def list_sources(
    skip: int = 0,
    limit: int = 100,
    source_type: str | None = None,
    is_official: bool | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    q = db.query(Source)
    if source_type:
        q = q.filter(Source.source_type == source_type)
    if is_official is not None:
        q = q.filter(Source.is_official == is_official)
    total = q.count()
    items = q.order_by(Source.name).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [SourceRead.model_validate(s) for s in items],
        "skip": skip,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# Create source
# ---------------------------------------------------------------------------

@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_source(
    body: SourceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    src = Source(**body.model_dump())
    db.add(src)
    db.commit()
    db.refresh(src)
    return SourceRead.model_validate(src)


# ---------------------------------------------------------------------------
# Update source
# ---------------------------------------------------------------------------

@router.patch("/{source_id}", response_model=SourceRead)
def update_source(
    source_id: str,
    body: SourceUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    src = _source_or_404(source_id, db)
    updates = body.model_dump(exclude_none=True)
    for k, v in updates.items():
        setattr(src, k, v)
    db.commit()
    db.refresh(src)
    return SourceRead.model_validate(src)
