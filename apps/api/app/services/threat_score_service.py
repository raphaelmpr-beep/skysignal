"""
ThreatScoreService — computes a 0-100 threat score for a geographic location
based on nearby incidents from the SkySignal database.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas import ThreatScoreResult

MILES_TO_METERS = 1609.34

# Factor weights (must sum to 1.0)
WEIGHTS: dict[str, float] = {
    "evidence_confidence": 0.30,
    "incident_density": 0.20,
    "recency": 0.15,
    "facility_proximity": 0.15,
    "severity": 0.10,
    "sector_sensitivity": 0.05,
    "repeat_pattern": 0.05,
}

SEVERITY_SCORES: dict[str, float] = {
    "CRITICAL": 100.0,
    "HIGH": 75.0,
    "MEDIUM": 50.0,
    "LOW": 25.0,
    "INFO": 10.0,
}

SECTOR_SENSITIVITY: dict[str, float] = {
    "MILITARY": 100.0,
    "AVIATION": 100.0,
    "NUCLEAR": 100.0,
    "CRITICAL_INFRA": 100.0,
    "GOVERNMENT": 80.0,
    "CORRECTIONS": 80.0,
    "ENERGY": 70.0,
    "WATER": 70.0,
    "TRANSPORTATION": 65.0,
    "COMMERCIAL": 50.0,
    "RESIDENTIAL": 30.0,
}


def _tier(score: float) -> str:
    if score <= 20:
        return "MINIMAL"
    if score <= 40:
        return "LOW"
    if score <= 60:
        return "MODERATE"
    if score <= 80:
        return "ELEVATED"
    return "HIGH"


class ThreatScoreService:
    def compute_score(
        self,
        lat: float,
        lon: float,
        radius_miles: float,
        time_window_days: int,
        db: Session,
        org_id: str,
    ) -> ThreatScoreResult:
        radius_meters = radius_miles * MILES_TO_METERS
        since = datetime.now(timezone.utc) - timedelta(days=time_window_days)

        # ----------------------------------------------------------------
        # Fetch incidents within radius using PostGIS
        # ----------------------------------------------------------------
        sql = text(
            """
            SELECT
                id,
                confidence_score,
                severity,
                occurred_at,
                proximity_score,
                cisa_sector,
                operational_sector,
                lat,
                lon,
                ST_Distance(
                    ST_MakePoint(lon, lat)::geography,
                    ST_MakePoint(:lon, :lat)::geography
                ) AS dist_meters
            FROM incidents
            WHERE
                org_id = :org_id
                AND lat IS NOT NULL
                AND lon IS NOT NULL
                AND occurred_at >= :since
                AND ST_DWithin(
                    ST_MakePoint(lon, lat)::geography,
                    ST_MakePoint(:lon, :lat)::geography,
                    :radius
                )
            """
        )

        rows = db.execute(
            sql,
            {
                "lat": lat,
                "lon": lon,
                "radius": radius_meters,
                "org_id": org_id,
                "since": since,
            },
        ).fetchall()

        incident_count = len(rows)

        if incident_count == 0:
            factors = {k: 0.0 for k in WEIGHTS}
            return ThreatScoreResult(
                score=0.0,
                tier="MINIMAL",
                factors=factors,
                weights=WEIGHTS,
                explanation="No incidents found within the specified radius and time window.",
                incident_count=0,
            )

        # ----------------------------------------------------------------
        # Factor 1: Evidence Confidence (30%)
        # ----------------------------------------------------------------
        confidence_scores = [r.confidence_score or 0 for r in rows]
        evidence_confidence = sum(confidence_scores) / len(confidence_scores)

        # ----------------------------------------------------------------
        # Factor 2: Incident Density (20%)
        # ----------------------------------------------------------------
        # log-scale: log(count+1)/log(max_ref+1) * 100, capped at 100
        max_ref = 50  # 50 incidents in radius = density score of ~100
        incident_density = min(
            100.0,
            (math.log(incident_count + 1) / math.log(max_ref + 1)) * 100.0,
        )

        # ----------------------------------------------------------------
        # Factor 3: Recency (15%) — exponential decay, half-life = 30 days
        # ----------------------------------------------------------------
        now = datetime.now(timezone.utc)
        half_life_days = 30.0
        recency_weights = []
        for r in rows:
            if r.occurred_at:
                occ = r.occurred_at
                if occ.tzinfo is None:
                    occ = occ.replace(tzinfo=timezone.utc)
                age_days = (now - occ).total_seconds() / 86400.0
                w = math.exp(-math.log(2) * age_days / half_life_days)
                recency_weights.append(w)
            else:
                recency_weights.append(0.0)

        recency_score = (sum(recency_weights) / len(recency_weights)) * 100.0
        recency_score = min(100.0, recency_score)

        # ----------------------------------------------------------------
        # Factor 4: Facility Proximity (15%)
        # Higher score for closer incidents (inverse of distance)
        # ----------------------------------------------------------------
        prox_scores = []
        for r in rows:
            if r.proximity_score is not None:
                prox_scores.append(float(r.proximity_score))
            elif r.dist_meters is not None and r.dist_meters > 0:
                # Normalize: 0 m = 100, radius = 0
                normalized = max(0.0, (1 - r.dist_meters / radius_meters) * 100.0)
                prox_scores.append(normalized)
            else:
                prox_scores.append(50.0)

        facility_proximity = sum(prox_scores) / len(prox_scores) if prox_scores else 0.0

        # ----------------------------------------------------------------
        # Factor 5: Severity (10%)
        # ----------------------------------------------------------------
        sev_vals = [
            SEVERITY_SCORES.get((r.severity or "").upper(), 25.0) for r in rows
        ]
        severity_score = sum(sev_vals) / len(sev_vals)

        # ----------------------------------------------------------------
        # Factor 6: Sector Sensitivity (5%)
        # ----------------------------------------------------------------
        sector_scores = []
        for r in rows:
            cisa = (r.cisa_sector or "").upper()
            op = (r.operational_sector or "").upper()
            s = SECTOR_SENSITIVITY.get(cisa) or SECTOR_SENSITIVITY.get(op) or 50.0
            sector_scores.append(s)
        sector_sensitivity = sum(sector_scores) / len(sector_scores)

        # ----------------------------------------------------------------
        # Factor 7: Repeat Pattern (5%)
        # Cluster incidents that fall within ~1km of each other
        # ----------------------------------------------------------------
        repeat_pattern = _compute_repeat_pattern(rows)

        # ----------------------------------------------------------------
        # Final weighted score
        # ----------------------------------------------------------------
        factors: dict[str, float] = {
            "evidence_confidence": round(evidence_confidence, 2),
            "incident_density": round(incident_density, 2),
            "recency": round(recency_score, 2),
            "facility_proximity": round(facility_proximity, 2),
            "severity": round(severity_score, 2),
            "sector_sensitivity": round(sector_sensitivity, 2),
            "repeat_pattern": round(repeat_pattern, 2),
        }

        final_score = sum(
            factors[k] * WEIGHTS[k] for k in WEIGHTS
        )
        final_score = round(min(100.0, max(0.0, final_score)), 2)
        tier = _tier(final_score)

        explanation = _build_explanation(
            tier=tier,
            score=final_score,
            factors=factors,
            incident_count=incident_count,
            radius_miles=radius_miles,
            time_window_days=time_window_days,
        )

        return ThreatScoreResult(
            score=final_score,
            tier=tier,
            factors=factors,
            weights=WEIGHTS,
            explanation=explanation,
            incident_count=incident_count,
        )


def _compute_repeat_pattern(rows) -> float:
    """
    Cluster incidents within ~1 km. More clusters = higher repeat score.
    Score = fraction of incidents that are in a cluster of 2+ * 100.
    """
    cluster_radius_m = 1000.0
    n = len(rows)
    if n < 2:
        return 0.0

    visited = [False] * n
    in_cluster = [False] * n

    for i in range(n):
        if visited[i]:
            continue
        cluster = [i]
        for j in range(i + 1, n):
            if visited[j]:
                continue
            lat_i, lon_i = rows[i].lat or 0.0, rows[i].lon or 0.0
            lat_j, lon_j = rows[j].lat or 0.0, rows[j].lon or 0.0
            dist = _haversine(lat_i, lon_i, lat_j, lon_j)
            if dist <= cluster_radius_m:
                cluster.append(j)
        if len(cluster) >= 2:
            for idx in cluster:
                in_cluster[idx] = True
        for idx in cluster:
            visited[idx] = True

    clustered = sum(in_cluster)
    return round((clustered / n) * 100.0, 2)


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in meters between two lat/lon points."""
    R = 6_371_000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_explanation(
    tier: str,
    score: float,
    factors: dict[str, float],
    incident_count: int,
    radius_miles: float,
    time_window_days: int,
) -> str:
    lines = [
        f"Facility threat tier: {tier} (score: {score}/100).",
        f"Analysis based on {incident_count} incident(s) within {radius_miles} miles "
        f"over the past {time_window_days} days.",
        "",
        "Factor Breakdown:",
    ]
    for factor, val in factors.items():
        weight = WEIGHTS[factor]
        contribution = round(val * weight, 2)
        lines.append(
            f"  • {factor.replace('_', ' ').title()}: {val}/100 "
            f"(weight {int(weight*100)}%, contribution {contribution})"
        )

    tier_desc = {
        "MINIMAL": "No significant threat activity detected.",
        "LOW": "Limited threat activity. Standard security posture recommended.",
        "MODERATE": "Moderate threat activity. Enhanced monitoring recommended.",
        "ELEVATED": "Significant threat activity. Active countermeasures recommended.",
        "HIGH": "High threat activity. Immediate security review required.",
    }
    lines.append("")
    lines.append(tier_desc.get(tier, ""))
    return "\n".join(lines)
