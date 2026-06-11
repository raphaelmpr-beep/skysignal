"""
Map router — /api/map
Returns geo data for map visualization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Incident, InfrastructureAsset, WatchZone
from app.schemas import HeatmapPoint, MapIncident, WatchZoneRead

router = APIRouter()

MAX_POINTS = 5000


# ---------------------------------------------------------------------------
# Map incidents
# ---------------------------------------------------------------------------

@router.get("/incidents", response_model=list[MapIncident])
def map_incidents(
    bbox: Optional[str] = Query(None, description="minLon,minLat,maxLon,maxLat"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    severity: Optional[str] = None,
    incident_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    q = db.query(Incident).filter(
        Incident.org_id == org_id,
        Incident.lat.isnot(None),
        Incident.lon.isnot(None),
    )

    if bbox:
        try:
            min_lon, min_lat, max_lon, max_lat = [float(x) for x in bbox.split(",")]
            q = q.filter(
                Incident.lat >= min_lat,
                Incident.lat <= max_lat,
                Incident.lon >= min_lon,
                Incident.lon <= max_lon,
            )
        except ValueError:
            pass  # ignore malformed bbox

    if date_from:
        q = q.filter(Incident.occurred_at >= date_from)
    if date_to:
        q = q.filter(Incident.occurred_at <= date_to)
    if severity:
        q = q.filter(Incident.severity == severity)
    if incident_type:
        q = q.filter(Incident.incident_type == incident_type)

    items = q.order_by(Incident.occurred_at.desc()).limit(MAX_POINTS).all()
    return [
        MapIncident(
            id=i.id,
            lat=i.lat,
            lon=i.lon,
            incident_type=i.incident_type,
            severity=i.severity,
            confidence_tier=i.confidence_tier,
            occurred_at=i.occurred_at,
            title=i.title,
        )
        for i in items
    ]


# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------

@router.get("/heatmap", response_model=list[HeatmapPoint])
def heatmap(
    bbox: Optional[str] = Query(None, description="minLon,minLat,maxLon,maxLat"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    q = db.query(Incident).filter(
        Incident.org_id == org_id,
        Incident.lat.isnot(None),
        Incident.lon.isnot(None),
    )

    if bbox:
        try:
            min_lon, min_lat, max_lon, max_lat = [float(x) for x in bbox.split(",")]
            q = q.filter(
                Incident.lat >= min_lat,
                Incident.lat <= max_lat,
                Incident.lon >= min_lon,
                Incident.lon <= max_lon,
            )
        except ValueError:
            pass

    if date_from:
        q = q.filter(Incident.occurred_at >= date_from)
    if date_to:
        q = q.filter(Incident.occurred_at <= date_to)

    items = q.limit(MAX_POINTS).all()
    return [
        HeatmapPoint(
            lat=i.lat,
            lon=i.lon,
            weight=round((i.confidence_score or 0) / 100.0, 4),
        )
        for i in items
    ]


# ---------------------------------------------------------------------------
# Watch zones
# ---------------------------------------------------------------------------

@router.get("/watch-zones", response_model=list[WatchZoneRead])
def map_watch_zones(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    zones = (
        db.query(WatchZone)
        .filter(WatchZone.org_id == org_id, WatchZone.is_active == True)
        .all()
    )
    return [WatchZoneRead.model_validate(z) for z in zones]


# ---------------------------------------------------------------------------
# Infrastructure assets
# ---------------------------------------------------------------------------

@router.get("/assets")
def map_assets(
    bbox: Optional[str] = Query(None, description="minLon,minLat,maxLon,maxLat"),
    cisa_sector: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    q = db.query(InfrastructureAsset).filter(
        InfrastructureAsset.lat.isnot(None),
        InfrastructureAsset.lon.isnot(None),
    )

    if bbox:
        try:
            min_lon, min_lat, max_lon, max_lat = [float(x) for x in bbox.split(",")]
            q = q.filter(
                InfrastructureAsset.lat >= min_lat,
                InfrastructureAsset.lat <= max_lat,
                InfrastructureAsset.lon >= min_lon,
                InfrastructureAsset.lon <= max_lon,
            )
        except ValueError:
            pass

    if cisa_sector:
        q = q.filter(InfrastructureAsset.cisa_sector == cisa_sector)

    items = q.limit(MAX_POINTS).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "asset_type": a.asset_type,
            "cisa_sector": a.cisa_sector,
            "lat": a.lat,
            "lon": a.lon,
            "address": a.address,
            "state": a.state,
        }
        for a in items
    ]
