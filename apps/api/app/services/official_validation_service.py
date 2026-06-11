"""
OfficialValidationService — stub for official source validation.
Searches FAA, DOJ, DHS, FBI, state corrections, and airports for
confirmation of PENDING incidents.
"""

from __future__ import annotations

from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Scoring weights for official match
# ---------------------------------------------------------------------------
SCORE_WEIGHTS = {
    "date_match": 25,
    "location_match": 25,
    "facility_match": 20,
    "incident_type_match": 15,
    "jurisdiction_match": 10,
    "named_entity_match": 5,
}

TOTAL_POSSIBLE = sum(SCORE_WEIGHTS.values())  # 100

# Thresholds
OFFICIAL_CONFIRMATION_THRESHOLD = 80
CORROBORATION_THRESHOLD = 60


class OfficialValidationService:
    """
    Searches official sources (FAA, DOJ, DHS, FBI, state corrections, airports)
    for confirmation of PENDING incidents.

    Scoring per official source match:
        date_match=25       — Reported date aligns with official record
        location_match=25   — Lat/lon or location name matches
        facility_match=20   — Named facility appears in official record
        incident_type_match=15 — Incident type matches official category
        jurisdiction_match=10 — Jurisdiction (state/county) matches
        named_entity_match=5   — Named persons/organizations overlap

    Score interpretation:
        >= 80  → OFFICIAL_CONFIRMATION: add evidence, boost confidence
        60-79  → CORROBORATION: add evidence, moderate boost
        < 60   → Store evidence, no auto-boost

    Production wiring:
        - FAA UAS reporting: https://uas.faa.gov/
        - DOJ press releases API / RSS
        - DHS CISA advisories
        - FBI press release search
        - State DOC (Dept of Corrections) incident logs
        - Airport operator security contacts
    """

    def validate_incident(self, incident_id: str, db: Session) -> dict:
        """
        Attempt to find official confirmation for an incident.

        Args:
            incident_id: UUID of the incident to validate
            db:          SQLAlchemy session

        Returns:
            {
                "official_match_score": int,
                "matches": list[dict],
                "status": str,  # "confirmed", "corroborated", "not_found", "stub"
                "evidence_created": list[str],  # evidence IDs
            }
        """
        # Stub: returns not_found result.
        # In production, fetch incident, query external APIs, compute score.
        return {
            "official_match_score": 0,
            "matches": [],
            "status": "stub",
            "evidence_created": [],
        }

    def _score_match(self, incident, official_record: dict) -> int:
        """
        Score how well an official record matches an incident.
        Returns 0-100.

        This is the production scoring logic — wired to real data in prod.
        """
        score = 0

        # Date match
        if incident.occurred_at and official_record.get("date"):
            try:
                from datetime import datetime, timezone, timedelta
                rec_date = official_record["date"]
                if isinstance(rec_date, str):
                    rec_date = datetime.fromisoformat(rec_date)
                if rec_date.tzinfo is None:
                    rec_date = rec_date.replace(tzinfo=timezone.utc)
                diff = abs((incident.occurred_at - rec_date).total_seconds())
                if diff < 86400:  # within 1 day
                    score += SCORE_WEIGHTS["date_match"]
                elif diff < 604800:  # within 1 week
                    score += SCORE_WEIGHTS["date_match"] // 2
            except Exception:
                pass

        # Location match
        if (
            incident.lat and incident.lon
            and official_record.get("lat") and official_record.get("lon")
        ):
            from app.services.threat_score_service import _haversine
            dist = _haversine(
                incident.lat, incident.lon,
                float(official_record["lat"]), float(official_record["lon"]),
            )
            if dist < 1000:  # within 1 km
                score += SCORE_WEIGHTS["location_match"]
            elif dist < 5000:  # within 5 km
                score += SCORE_WEIGHTS["location_match"] // 2

        # Facility match
        if incident.facility_name and official_record.get("facility"):
            inc_fac = incident.facility_name.lower()
            rec_fac = official_record["facility"].lower()
            if inc_fac in rec_fac or rec_fac in inc_fac:
                score += SCORE_WEIGHTS["facility_match"]

        # Incident type match
        if incident.incident_type and official_record.get("type"):
            if incident.incident_type.lower() in official_record["type"].lower():
                score += SCORE_WEIGHTS["incident_type_match"]

        # Jurisdiction match
        if official_record.get("jurisdiction"):
            state = (official_record.get("state") or "").lower()
            loc = (incident.location_name or "").lower()
            if state and state in loc:
                score += SCORE_WEIGHTS["jurisdiction_match"]

        # Named entity match
        if official_record.get("named_entities") and incident.summary:
            summary_lower = incident.summary.lower()
            for entity in official_record["named_entities"]:
                if entity.lower() in summary_lower:
                    score += SCORE_WEIGHTS["named_entity_match"]
                    break  # only add once

        return min(score, TOTAL_POSSIBLE)
