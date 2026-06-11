"""
Analytics router — /api/analytics
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Incident, Source
from app.schemas import AbComparison, AnalyticsKPI, SankeyData, SankeyLink, TimelinePeriod

router = APIRouter()


def _base_q(org_id: str, db: Session):
    return db.query(Incident).filter(Incident.org_id == org_id)


# ---------------------------------------------------------------------------
# KPI
# ---------------------------------------------------------------------------

@router.get("/kpi", response_model=AnalyticsKPI)
def analytics_kpi(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    q = _base_q(org_id, db)

    total = q.count()
    pending = q.filter(Incident.review_status == "PENDING").count()
    avg_conf_row = db.query(func.avg(Incident.confidence_score)).filter(
        Incident.org_id == org_id
    ).scalar()
    avg_conf = float(avg_conf_row or 0.0)
    high_signal = q.filter(
        Incident.confidence_tier.in_(["VERIFIED", "HIGH"])
    ).count()

    # Incidents by severity
    severity_rows = (
        db.query(Incident.severity, func.count(Incident.id))
        .filter(Incident.org_id == org_id)
        .group_by(Incident.severity)
        .all()
    )
    by_severity = {(r[0] or "UNKNOWN"): r[1] for r in severity_rows}

    # Month comparisons
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = month_start - timedelta(seconds=1)
    last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    this_month = q.filter(Incident.occurred_at >= month_start).count()
    last_month = q.filter(
        Incident.occurred_at >= last_month_start,
        Incident.occurred_at <= last_month_end,
    ).count()

    return AnalyticsKPI(
        total_incidents=total,
        pending_review=pending,
        avg_confidence=round(avg_conf, 2),
        high_signal_count=high_signal,
        incidents_by_severity=by_severity,
        incidents_this_month=this_month,
        incidents_last_month=last_month,
    )


# ---------------------------------------------------------------------------
# Timeline — incidents grouped by week
# ---------------------------------------------------------------------------

@router.get("/timeline", response_model=list[TimelinePeriod])
def analytics_timeline(
    days: int = Query(365, ge=7, le=1095),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (
        db.query(Incident)
        .filter(Incident.org_id == org_id, Incident.occurred_at >= since)
        .order_by(Incident.occurred_at)
        .all()
    )

    # Group by ISO week
    week_counts: dict[str, list[int]] = defaultdict(list)
    for inc in rows:
        if inc.occurred_at:
            key = inc.occurred_at.strftime("%Y-W%V")
            week_counts[key].append(inc.confidence_score or 0)

    result = []
    for period, scores in sorted(week_counts.items()):
        result.append(
            TimelinePeriod(
                period=period,
                count=len(scores),
                avg_confidence=round(sum(scores) / len(scores), 2) if scores else 0.0,
            )
        )
    return result


# ---------------------------------------------------------------------------
# Sector distribution
# ---------------------------------------------------------------------------

@router.get("/sector-distribution")
def sector_distribution(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]

    cisa_rows = (
        db.query(Incident.cisa_sector, func.count(Incident.id))
        .filter(Incident.org_id == org_id)
        .group_by(Incident.cisa_sector)
        .all()
    )
    op_rows = (
        db.query(Incident.operational_sector, func.count(Incident.id))
        .filter(Incident.org_id == org_id)
        .group_by(Incident.operational_sector)
        .all()
    )
    return {
        "cisa_sector": {(r[0] or "UNKNOWN"): r[1] for r in cisa_rows},
        "operational_sector": {(r[0] or "UNKNOWN"): r[1] for r in op_rows},
    }


# ---------------------------------------------------------------------------
# Source distribution
# ---------------------------------------------------------------------------

@router.get("/source-distribution")
def source_distribution(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    # source_type is on the Source model; we reach it via incident_evidence join
    from app.models import IncidentEvidence

    rows = (
        db.query(Source.source_type, func.count(func.distinct(Incident.id)))
        .join(IncidentEvidence, IncidentEvidence.source_id == Source.id)
        .join(Incident, Incident.id == IncidentEvidence.incident_id)
        .filter(Incident.org_id == org_id)
        .group_by(Source.source_type)
        .all()
    )
    return {(r[0] or "UNKNOWN"): r[1] for r in rows}


# ---------------------------------------------------------------------------
# Confidence histogram
# ---------------------------------------------------------------------------

@router.get("/confidence-histogram")
def confidence_histogram(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    rows = (
        db.query(Incident.confidence_tier, func.count(Incident.id))
        .filter(Incident.org_id == org_id)
        .group_by(Incident.confidence_tier)
        .all()
    )
    return {(r[0] or "UNVERIFIED"): r[1] for r in rows}


# ---------------------------------------------------------------------------
# Sankey
# ---------------------------------------------------------------------------

@router.get("/sankey", response_model=SankeyData)
def analytics_sankey(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    source_type → incident_type → cisa_sector → confidence_tier
    """
    from app.models import IncidentEvidence

    rows = (
        db.query(
            Source.source_type,
            Incident.incident_type,
            Incident.cisa_sector,
            Incident.confidence_tier,
            func.count(Incident.id),
        )
        .join(IncidentEvidence, IncidentEvidence.source_id == Source.id)
        .join(Incident, Incident.id == IncidentEvidence.incident_id)
        .filter(Incident.org_id == current_user["org_id"])
        .group_by(
            Source.source_type,
            Incident.incident_type,
            Incident.cisa_sector,
            Incident.confidence_tier,
        )
        .all()
    )

    node_set: set[str] = set()
    links_agg: dict[tuple, int] = defaultdict(int)

    for src_type, inc_type, cisa, conf_tier, cnt in rows:
        s = src_type or "UNKNOWN"
        i = inc_type or "UNKNOWN"
        c = cisa or "UNKNOWN"
        t = conf_tier or "UNVERIFIED"
        node_set.update([s, i, c, t])
        links_agg[(s, i)] += cnt
        links_agg[(i, c)] += cnt
        links_agg[(c, t)] += cnt

    nodes = sorted(node_set)
    links = [
        SankeyLink(source=k[0], target=k[1], value=v)
        for k, v in links_agg.items()
    ]
    return SankeyData(nodes=nodes, links=links)


# ---------------------------------------------------------------------------
# A/B comparison
# ---------------------------------------------------------------------------

@router.get("/ab-comparison", response_model=AbComparison)
def ab_comparison(
    period_a_start: datetime = Query(...),
    period_a_end: datetime = Query(...),
    period_b_start: datetime = Query(...),
    period_b_end: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    q = _base_q(org_id, db)

    def _stats(start: datetime, end: datetime):
        rows = q.filter(
            Incident.occurred_at >= start, Incident.occurred_at <= end
        ).all()
        count = len(rows)
        avg_c = sum(r.confidence_score or 0 for r in rows) / count if count else 0.0
        return count, round(avg_c, 2)

    a_count, a_avg = _stats(period_a_start, period_a_end)
    b_count, b_avg = _stats(period_b_start, period_b_end)

    delta = b_count - a_count
    delta_pct = round((delta / a_count * 100) if a_count else 0.0, 2)

    return AbComparison(
        period_a_label=f"{period_a_start.date()} – {period_a_end.date()}",
        period_b_label=f"{period_b_start.date()} – {period_b_end.date()}",
        period_a_count=a_count,
        period_b_count=b_count,
        period_a_avg_confidence=a_avg,
        period_b_avg_confidence=b_avg,
        delta_count=delta,
        delta_pct=delta_pct,
    )
