"""
Watch Zones router — /api/watch-zones
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import WatchZone
from app.schemas import WatchZoneCreate, WatchZoneRead

router = APIRouter()


@router.get("", response_model=dict)
def list_watch_zones(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    q = db.query(WatchZone).filter(WatchZone.org_id == org_id)
    total = q.count()
    items = q.order_by(WatchZone.created_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [WatchZoneRead.model_validate(wz) for wz in items],
        "skip": skip,
        "limit": limit,
    }


@router.get("/{zone_id}", response_model=WatchZoneRead)
def get_watch_zone(
    zone_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    wz = (
        db.query(WatchZone)
        .filter(WatchZone.id == zone_id, WatchZone.org_id == current_user["org_id"])
        .first()
    )
    if not wz:
        raise HTTPException(status_code=404, detail="Watch zone not found")
    return WatchZoneRead.model_validate(wz)


@router.post("", response_model=WatchZoneRead, status_code=status.HTTP_201_CREATED)
def create_watch_zone(
    body: WatchZoneCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    wz = WatchZone(
        org_id=current_user["org_id"],
        name=body.name,
        description=body.description,
        lat=body.lat,
        lon=body.lon,
        radius_miles=body.radius_miles,
    )
    db.add(wz)
    db.commit()
    db.refresh(wz)
    return WatchZoneRead.model_validate(wz)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watch_zone(
    zone_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    wz = (
        db.query(WatchZone)
        .filter(WatchZone.id == zone_id, WatchZone.org_id == current_user["org_id"])
        .first()
    )
    if not wz:
        raise HTTPException(status_code=404, detail="Watch zone not found")
    db.delete(wz)
    db.commit()
