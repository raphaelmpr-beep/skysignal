"""
ConfidenceService — recomputes the confidence score for an incident
based on its evidence records, using the corroboration scoring model.

Formula (from corroboration_scoring.md):
  base        = sum(source_credibility * role_multiplier for each evidence row)
  normalized  = min(100, (base / NORMALIZATION_FACTOR) * 100)
  bonus       = min(20, (independent_confirming_source_types - 1) * 10)
  final       = min(100, round(normalized + bonus))

NORMALIZATION_FACTOR = 120 ensures a single OFFICIAL_CONFIRMATION
from FAA (credibility=90) yields ~75 (HIGH), not VERIFIED.
Reaching VERIFIED requires independent corroboration.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Incident, IncidentEvidence, Source

# ── Constants ──────────────────────────────────────────────────────────────
NORMALIZATION_FACTOR = 120.0

ROLE_MULTIPLIERS: dict[str, float] = {
    "OFFICIAL_CONFIRMATION": 1.0,
    "CORROBORATION":         0.6,
    "DISCOVERY":             0.3,
    "CONTRADICTION":        -0.4,
    "DUPLICATE":             0.0,
    "REJECTION_SUPPORT":     0.0,
}

# Tiers ordered high → low so first match wins
TIER_THRESHOLDS = [
    (80, "VERIFIED"),
    (65, "HIGH"),
    (45, "MEDIUM"),
    (25, "LOW"),
    (0,  "UNVERIFIED"),
]

# Roles that count toward the corroboration bonus
CONFIRMING_ROLES = {"OFFICIAL_CONFIRMATION", "CORROBORATION"}

# Roles excluded from score computation
EXCLUDED_ROLES = {"DUPLICATE", "REJECTION_SUPPORT"}


def _tier(score: int) -> str:
    for threshold, label in TIER_THRESHOLDS:
        if score >= threshold:
            return label
    return "UNVERIFIED"


class ConfidenceService:
    """
    Recomputes confidence for an incident from its attached evidence.
    Call recompute() after any insert/update to incident_evidence.
    """

    def recompute(self, incident_id: str, db: Session) -> int:
        """
        Recalculate confidence_score and confidence_tier for incident_id.
        Updates the incident in-place. Returns the new score.
        """
        evidences = (
            db.query(IncidentEvidence)
            .filter(IncidentEvidence.incident_id == incident_id)
            .all()
        )

        if not evidences:
            inc = db.query(Incident).filter(Incident.id == incident_id).first()
            if inc:
                inc.confidence_score = 0
                inc.confidence_tier = "UNVERIFIED"
                db.commit()
            return 0

        # Load sources for credibility lookup
        source_ids = [e.source_id for e in evidences if e.source_id]
        sources_by_id: dict[str, Source] = {}
        if source_ids:
            sources_by_id = {
                s.id: s
                for s in db.query(Source).filter(Source.id.in_(source_ids)).all()
            }

        base = 0.0
        confirming_source_types: set[str] = set()

        for ev in evidences:
            role = (ev.role or "DISCOVERY").upper()
            if role in EXCLUDED_ROLES:
                continue

            multiplier = ROLE_MULTIPLIERS.get(role, 0.0)
            src = sources_by_id.get(ev.source_id) if ev.source_id else None
            credibility = src.credibility_score if (src and src.credibility_score) else 40

            base += credibility * multiplier

            # Track independent source types that are confirming
            if role in CONFIRMING_ROLES and src:
                confirming_source_types.add(src.source_type)

        # Normalize to 0–100
        normalized = min(100.0, (base / NORMALIZATION_FACTOR) * 100.0)

        # Corroboration bonus: +10 per independent confirming source type beyond first
        bonus = min(20, max(0, (len(confirming_source_types) - 1) * 10))

        final = min(100, max(0, round(normalized + bonus)))
        tier = _tier(final)

        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if inc:
            inc.confidence_score = final
            inc.confidence_tier = tier
            db.commit()

        return final

    def upgrade_discovery_to_corroboration(
        self, incident_id: str, db: Session
    ) -> int:
        """
        When a new CORROBORATION or OFFICIAL_CONFIRMATION evidence is added,
        upgrade all existing DISCOVERY rows to CORROBORATION.
        Returns count of rows upgraded.
        """
        rows = (
            db.query(IncidentEvidence)
            .filter(
                IncidentEvidence.incident_id == incident_id,
                IncidentEvidence.role == "DISCOVERY",
            )
            .all()
        )
        for row in rows:
            row.role = "CORROBORATION"
        db.commit()
        return len(rows)

    def check_duplicate(
        self, incident_id: str, url: str | None, source_id: str | None, db: Session
    ) -> bool:
        """
        Returns True if an evidence row with the same url or source_id
        already exists for this incident (duplicate detection).
        """
        q = db.query(IncidentEvidence).filter(
            IncidentEvidence.incident_id == incident_id
        )
        if url:
            q_url = q.filter(IncidentEvidence.url == url).first()
            if q_url:
                return True
        if source_id:
            q_src = q.filter(IncidentEvidence.source_id == source_id).first()
            if q_src:
                return True
        return False
