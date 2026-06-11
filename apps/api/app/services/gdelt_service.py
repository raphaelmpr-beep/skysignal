"""
GDELTService — stub for GDELT integration.
Wire to the GDELT 2.0 API in production.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session


class GDELTService:
    """
    Integrates with GDELT for news-derived candidate incidents.
    Currently a stub — returns empty results and no-ops on creation.

    Production wiring:
      - GET https://api.gdeltproject.org/api/v2/doc/doc
        ?query=drone+UAV&mode=artlist&format=json&startdatetime=...&enddatetime=...
      - Parse ArticleList, extract: url, title, seendate, domain, tone, locations
      - Map to SkySignal incident fields
    """

    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    def search(self, query: str, date_from: str, date_to: str) -> list[dict]:
        """
        Search GDELT for relevant articles.

        Args:
            query:     Search string, e.g. "drone sighting prison"
            date_from: ISO date string YYYYMMDDHHMMSS
            date_to:   ISO date string YYYYMMDDHHMMSS

        Returns:
            List of article dicts (empty in stub).
        """
        # Stub: returns empty list. Wire to GDELT API in production.
        return []

    def create_candidate_incidents(
        self, results: list[dict], org_id: str, db: Session
    ) -> list[str]:
        """
        Creates PENDING incidents from GDELT article results.

        Each result dict is expected to have keys:
          - title, url, seendate, domain, locations (list of dicts with lat/lon)

        Returns:
            List of newly created incident IDs.
        """
        from app.models import Incident, Source

        if not results:
            return []

        # Ensure a GDELT source exists
        gdelt_source = db.query(Source).filter(Source.name == "GDELT").first()
        if not gdelt_source:
            gdelt_source = Source(
                name="GDELT",
                source_type="NEWS",
                url="https://www.gdeltproject.org",
                is_official=False,
                reliability_score=40,
            )
            db.add(gdelt_source)
            db.flush()

        incident_ids: list[str] = []
        for article in results:
            title = article.get("title", "GDELT Candidate Incident")
            url = article.get("url", "")
            seen_date = article.get("seendate")
            locations = article.get("locations", [])

            lat = None
            lon = None
            if locations:
                first_loc = locations[0]
                lat = first_loc.get("lat")
                lon = first_loc.get("lon")

            occurred_at = None
            if seen_date:
                try:
                    occurred_at = datetime.strptime(seen_date[:14], "%Y%m%d%H%M%S").replace(
                        tzinfo=timezone.utc
                    )
                except (ValueError, TypeError):
                    pass

            inc = Incident(
                org_id=org_id,
                title=f"[GDELT] {title[:490]}",
                summary=f"Candidate incident sourced from GDELT. Article: {url}",
                review_status="PENDING",
                confidence_score=0,
                confidence_tier="UNVERIFIED",
                incident_type="UNKNOWN",
                severity="UNKNOWN",
                lat=lat,
                lon=lon,
                occurred_at=occurred_at,
                source_url=url,
                external_id=f"gdelt:{url[:200]}",
                raw_data=article,
            )
            db.add(inc)
            db.flush()
            incident_ids.append(inc.id)

        db.commit()
        return incident_ids
