"""
ConfidenceService — recomputes the confidence score for an incident
based on its evidence records.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Incident, IncidentEvidence, Source


def _tier(score: int) -> str:
    if score >= 80:
        return "VERIFIED"
    if score >= 60:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    if score >= 20:
        return "LOW"
    return "UNVERIFIED"


class ConfidenceService:
    def recompute(self, incident_id: str, db: Session) -> int:
        """
        Recalculate confidence score for an incident based on its evidence.

        Scoring rules:
          - OFFICIAL_CONFIRMATION evidence from official source: +40
          - CORROBORATION from official source: +20
          - CORROBORATION from non-official source: +10
          - DISCOVERY only (no other evidence): base 20
          - CONTRADICTION evidence: -15
          - Multiple corroborating sources (2nd, 3rd, 4th+): +5 per additional,
            up to +20

        Score is capped at [0, 100].
        Updates incident.confidence_score and confidence_tier in-place.
        Returns the new score.
        """
        evidences = (
            db.query(IncidentEvidence)
            .filter(IncidentEvidence.incident_id == incident_id)
            .all()
        )

        if not evidences:
            # No evidence — leave at 0
            inc = db.query(Incident).filter(Incident.id == incident_id).first()
            if inc:
                inc.confidence_score = 0
                inc.confidence_tier = "UNVERIFIED"
                db.commit()
            return 0

        # Load associated sources for is_official lookup
        source_ids = [e.source_id for e in evidences if e.source_id]
        sources_by_id: dict[str, Source] = {}
        if source_ids:
            source_objs = db.query(Source).filter(Source.id.in_(source_ids)).all()
            sources_by_id = {s.id: s for s in source_objs}

        score = 0
        corroboration_count = 0
        has_discovery = False

        for ev in evidences:
            ev_type = (ev.evidence_type or "").upper()
            src = sources_by_id.get(ev.source_id) if ev.source_id else None
            is_official = src.is_official if src else False

            if ev_type == "OFFICIAL_CONFIRMATION":
                if is_official:
                    score += 40
                else:
                    score += 20  # claims official confirmation but source isn't verified official

            elif ev_type == "CORROBORATION":
                if is_official:
                    score += 20
                else:
                    score += 10
                corroboration_count += 1

            elif ev_type == "DISCOVERY":
                has_discovery = True
                # Discovery alone gives base score below

            elif ev_type == "CONTRADICTION":
                score -= 15

            # MEDIA and DOCUMENT don't directly affect score unless combined

        # Base score for discovery-only case
        if has_discovery and score == 0:
            score = 20

        # Bonus for multiple corroborating sources (beyond the first)
        if corroboration_count > 1:
            bonus = min(20, (corroboration_count - 1) * 5)
            score += bonus

        score = max(0, min(100, score))
        tier = _tier(score)

        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if inc:
            inc.confidence_score = score
            inc.confidence_tier = tier
            db.commit()

        return score
