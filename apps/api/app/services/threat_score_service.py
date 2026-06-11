"""
ThreatScoreService — computes a 0-100 threat score for a geographic location
based on nearby incidents from the SkySignal database.
No PostGIS required — uses haversine distance in Python.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import Incident
from app.schemas import ThreatScoreResult

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

# Map operational_sector to sensitivity (incidents don't have cisa_sector)
OP_SECTOR_SENSITIVITY: dict[str, float] = {
    "MILITARY": 100.0,
    "AVIATION": 100.0,
    "NUCLEAR": 100.0,
    "GOVERNMENT": 80.0,
    "CORRECTIONS": 80.0,
    "ENERGY": 70.0,
    "WATER": 70.0,
    "TRANSPORTATION": 65.0,
    "COMMERCIAL": 50.0,
    "RESIDENTIAL": 30.0,
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in meters between two lat/lon points."""
    R = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


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
        radius_meters = radius_miles * 1609.34
        since = datetime.now(timezone.utc) - timedelta(days=time_window_days)

        # Fetch incidents in rough bounding box first (cheap), then filter by haversine
        deg_per_mile = 1.0 / 69.0
        margin = radius_miles * deg_per_mile * 1.2

        candidates = (
            db.query(Incident)
            .filter(
                Incident.org_id == org_id,
                Incident.lat.isnot(None),
                Incident.lon.isnot(None),
                Incident.occurred_at >= since,
                Incident.lat.between(lat - margin, lat + margin),
                Incident.lon.between(lon - margin, lon + margin),
            )
            .all()
        )

        # Filter to exact radius
        rows = []
        for inc in candidates:
            dist = _haversine(lat, lon, inc.lat, inc.lon)
            if dist <= radius_meters:
                rows.append((inc, dist))

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

        # Factor 1: Evidence Confidence (30%)
        confidence_scores = [r[0].confidence_score or 0 for r in rows]
        evidence_confidence = sum(confidence_scores) / len(confidence_scores)

        # Factor 2: Incident Density (20%)
        max_ref = 50
        incident_density = min(
            100.0,
            (math.log(incident_count + 1) / math.log(max_ref + 1)) * 100.0,
        )

        # Factor 3: Recency (15%) — exponential decay, half-life = 30 days
        now = datetime.now(timezone.utc)
        half_life_days = 30.0
        recency_weights = []
        for inc, _ in rows:
            if inc.occurred_at:
                occ = inc.occurred_at
                if occ.tzinfo is None:
                    occ = occ.replace(tzinfo=timezone.utc)
                age_days = (now - occ).total_seconds() / 86400.0
                w = math.exp(-math.log(2) * age_days / half_life_days)
                recency_weights.append(w)
            else:
                recency_weights.append(0.0)
        recency_score = min(100.0, (sum(recency_weights) / len(recency_weights)) * 100.0)

        # Factor 4: Facility Proximity (15%) — inverse of normalized distance
        prox_scores = []
        for inc, dist_m in rows:
            normalized = max(0.0, (1 - dist_m / radius_meters) * 100.0)
            prox_scores.append(normalized)
        facility_proximity = sum(prox_scores) / len(prox_scores) if prox_scores else 0.0

        # Factor 5: Severity (10%)
        sev_vals = [
            SEVERITY_SCORES.get((r[0].severity or "").upper(), 25.0) for r in rows
        ]
        severity_score = sum(sev_vals) / len(sev_vals)

        # Factor 6: Sector Sensitivity (5%)
        sector_scores = []
        for inc, _ in rows:
            op = (inc.operational_sector or "").upper()
            s = OP_SECTOR_SENSITIVITY.get(op, 50.0)
            sector_scores.append(s)
        sector_sensitivity = sum(sector_scores) / len(sector_scores)

        # Factor 7: Repeat Pattern (5%)
        inc_list = [r[0] for r in rows]
        repeat_pattern = _compute_repeat_pattern(inc_list)

        factors: dict[str, float] = {
            "evidence_confidence": round(evidence_confidence, 2),
            "incident_density": round(incident_density, 2),
            "recency": round(recency_score, 2),
            "facility_proximity": round(facility_proximity, 2),
            "severity": round(severity_score, 2),
            "sector_sensitivity": round(sector_sensitivity, 2),
            "repeat_pattern": round(repeat_pattern, 2),
        }

        final_score = sum(factors[k] * WEIGHTS[k] for k in WEIGHTS)
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


def _compute_repeat_pattern(incidents: list) -> float:
    n = len(incidents)
    if n < 2:
        return 0.0
    cluster_radius_m = 1000.0
    visited = [False] * n
    in_cluster = [False] * n
    for i in range(n):
        if visited[i]:
            continue
        cluster = [i]
        for j in range(i + 1, n):
            if visited[j]:
                continue
            dist = _haversine(
                incidents[i].lat or 0.0, incidents[i].lon or 0.0,
                incidents[j].lat or 0.0, incidents[j].lon or 0.0,
            )
            if dist <= cluster_radius_m:
                cluster.append(j)
        if len(cluster) >= 2:
            for idx in cluster:
                in_cluster[idx] = True
        for idx in cluster:
            visited[idx] = True
    clustered = sum(in_cluster)
    return round((clustered / n) * 100.0, 2)


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
        "ELEVATED": "Significant threat activity. Active monitoring recommended.",
        "HIGH": "High threat activity. Immediate security review required.",
    }
    lines.append("")
    lines.append(tier_desc.get(tier, ""))
    return "\n".join(lines)
