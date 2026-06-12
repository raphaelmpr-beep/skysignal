"""
GDELTService — integration with the GDELT 2.0 Doc API.
"""

from __future__ import annotations

import logging
import random
import re
import time
from datetime import datetime, timezone
from datetime import timedelta

import httpx
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class GDELTService:
    """
    Integrates with GDELT for news-derived candidate incidents.

    Production wiring:
      - GET https://api.gdeltproject.org/api/v2/doc/doc
        ?query=drone+UAV&mode=artlist&format=json&startdatetime=...&enddatetime=...
      - Parse ArticleList, extract: url, title, seendate, domain, tone, locations
      - Map to SkySignal incident fields
    """

    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
    MAX_BACKOFF_SECONDS = 8.0

    def __init__(self) -> None:
        self.last_status_code: int | None = None
        self.last_error: str | None = None

    def _parse_seen_date(self, seen_date: str | None) -> datetime | None:
        if not seen_date:
            return None
        raw = str(seen_date).strip()
        try:
            if re.fullmatch(r"\d{14}", raw):
                return datetime.strptime(raw, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    def _extract_lat_lon(self, article: dict) -> tuple[float | None, float | None]:
        # GDELT payloads are not guaranteed to include geocodes in a fixed shape.
        lat = article.get("lat") or article.get("latitude")
        lon = article.get("lon") or article.get("lng") or article.get("longitude")

        if lat is not None and lon is not None:
            try:
                return float(lat), float(lon)
            except (TypeError, ValueError):
                pass

        locations = article.get("locations")
        if isinstance(locations, list):
            for loc in locations:
                if not isinstance(loc, dict):
                    continue
                l1 = loc.get("lat") or loc.get("latitude")
                l2 = loc.get("lon") or loc.get("lng") or loc.get("longitude")
                if l1 is not None and l2 is not None:
                    try:
                        return float(l1), float(l2)
                    except (TypeError, ValueError):
                        continue

        return None, None

    def _parse_compact_utc(self, value: str) -> datetime:
        return datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)

    def _format_compact_utc(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")

    def _window_size_for_span(self, span: timedelta) -> timedelta:
        if span >= timedelta(days=7):
            return timedelta(hours=6)
        if span >= timedelta(days=2):
            return timedelta(hours=4)
        if span >= timedelta(days=1):
            return timedelta(hours=2)
        return timedelta(hours=1)

    def _build_windows(self, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
        if end <= start:
            return [(start, end)]

        step = self._window_size_for_span(end - start)
        windows: list[tuple[datetime, datetime]] = []
        cursor = end
        while cursor > start:
            left = max(start, cursor - step)
            windows.append((left, cursor))
            cursor = left
        return windows

    def _request_with_backoff(
        self,
        *,
        client: httpx.Client,
        params: dict,
        attempts: int = 4,
    ) -> dict | None:
        for attempt in range(1, attempts + 1):
            try:
                resp = client.get(
                    self.BASE_URL,
                    params=params,
                    headers={"User-Agent": "SkySignal/1.0 (+https://skysignal.vercel.app)"},
                )
                self.last_status_code = resp.status_code
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as exc:
                self.last_status_code = exc.response.status_code
                self.last_error = str(exc)

                retryable = exc.response.status_code in (408, 409, 425, 429, 500, 502, 503, 504)
                if not retryable or attempt == attempts:
                    logger.warning("GDELT search request failed: %s", exc)
                    return None

                base_delay = min(self.MAX_BACKOFF_SECONDS, 0.6 * (2 ** (attempt - 1)))
                jitter = random.uniform(0.2, 0.8)
                sleep_for = min(self.MAX_BACKOFF_SECONDS, base_delay + jitter)
                logger.warning(
                    "GDELT request retrying after status=%s attempt=%s/%s sleep=%.2fs",
                    exc.response.status_code,
                    attempt,
                    attempts,
                    sleep_for,
                )
                time.sleep(sleep_for)
            except Exception as exc:
                self.last_error = str(exc)
                if attempt == attempts:
                    logger.warning("GDELT search request failed: %s", exc)
                    return None
                base_delay = min(self.MAX_BACKOFF_SECONDS, 0.4 * (2 ** (attempt - 1)))
                jitter = random.uniform(0.1, 0.6)
                time.sleep(min(self.MAX_BACKOFF_SECONDS, base_delay + jitter))

        return None

    def search(self, query: str, date_from: str, date_to: str, limit: int = 100) -> list[dict]:
        """
        Search GDELT for relevant articles.

        Args:
            query:     Search string, e.g. "drone sighting prison"
            date_from: ISO date string YYYYMMDDHHMMSS
            date_to:   ISO date string YYYYMMDDHHMMSS

        Returns:
            List of normalized article dicts.
        """
        self.last_status_code = None
        self.last_error = None

        base_params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "sort": "DateDesc",
        }

        requested_limit = max(1, min(int(limit), 250))
        candidate_limits = [min(requested_limit, 50), 25, 10, 5]
        candidate_limits = list(dict.fromkeys(candidate_limits))

        try:
            start_dt = self._parse_compact_utc(date_from)
            end_dt = self._parse_compact_utc(date_to)
        except ValueError:
            self.last_error = "Invalid datetime window for GDELT search"
            return []

        windows = self._build_windows(start_dt, end_dt)
        found_rows: list[dict] = []
        seen_urls: set[str] = set()
        had_success = False

        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            for left, right in windows:
                for maxrecords in candidate_limits:
                    params = {
                        **base_params,
                        "startdatetime": self._format_compact_utc(left),
                        "enddatetime": self._format_compact_utc(right),
                        "maxrecords": maxrecords,
                    }
                    payload = self._request_with_backoff(client=client, params=params)
                    if payload is None:
                        # If this combination failed, keep trying with tighter requests.
                        continue

                    had_success = True
                    articles = payload.get("articles") or payload.get("ArticleList") or []
                    if not isinstance(articles, list):
                        continue

                    for row in articles:
                        if not isinstance(row, dict):
                            continue
                        url = str(row.get("url") or "").strip()
                        if url and url in seen_urls:
                            continue
                        if url:
                            seen_urls.add(url)
                        found_rows.append(row)

                        if len(found_rows) >= requested_limit:
                            break

                    if len(found_rows) >= requested_limit:
                        break
                if len(found_rows) >= requested_limit:
                    break

        if had_success and self.last_status_code == 429:
            # Last attempt may have been rate-limited, but we still gathered data.
            self.last_error = None

        if not found_rows:
            return []

        normalized: list[dict] = []
        for row in found_rows:
            if not isinstance(row, dict):
                continue
            url = str(row.get("url") or "").strip()
            title = str(row.get("title") or "").strip()
            if not (url or title):
                continue

            normalized.append(
                {
                    "title": title or "GDELT Candidate Incident",
                    "url": url,
                    "seendate": row.get("seendate") or row.get("seendatetime") or row.get("date"),
                    "domain": row.get("domain") or row.get("sourcecountry") or row.get("sourcename"),
                    "sourcecountry": row.get("sourcecountry"),
                    "tone": row.get("tone"),
                    "locations": row.get("locations") or [],
                    "raw": row,
                }
            )

        return normalized

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

        # Ensure a GDELT source exists for this org.
        gdelt_source = (
            db.query(Source)
            .filter(
                Source.org_id == org_id,
                Source.source_type.ilike("GDELT"),
            )
            .first()
        )
        if not gdelt_source:
            gdelt_source = Source(
                org_id=org_id,
                name="GDELT Event Stream",
                source_type="GDELT",
                url="https://api.gdeltproject.org/api/v2/doc/doc",
                is_official=False,
                reliability_score=55,
                is_active=True,
            )
            db.add(gdelt_source)
            db.flush()

        candidate_urls = [
            str(a.get("url") or "").strip()
            for a in results
            if str(a.get("url") or "").strip()
        ]
        existing_urls = set()
        if candidate_urls:
            existing_urls = {
                u
                for (u,) in db.query(Incident.source_url)
                .filter(
                    Incident.org_id == org_id,
                    Incident.source_url.in_(candidate_urls),
                )
                .all()
                if u
            }

        incident_ids: list[str] = []
        for article in results:
            title = article.get("title", "GDELT Candidate Incident")
            url = str(article.get("url") or "").strip()
            if not url or url in existing_urls:
                continue

            seen_date = article.get("seendate")
            occurred_at = self._parse_seen_date(str(seen_date) if seen_date else None)
            lat, lon = self._extract_lat_lon(article)
            domain = article.get("domain")
            country = article.get("sourcecountry")
            raw_data = article.get("raw") if isinstance(article.get("raw"), dict) else article
            summary = "Candidate incident sourced from GDELT"
            if domain:
                summary += f" ({domain})"
            summary += f". Article: {url}"

            inc = Incident(
                org_id=org_id,
                source_id=gdelt_source.id,
                title=f"[GDELT] {title[:490]}",
                summary=summary,
                review_status="PENDING",
                confidence_score=25,
                confidence_tier="UNVERIFIED",
                incident_type="UNKNOWN",
                severity="UNKNOWN",
                lat=lat,
                lon=lon,
                occurred_at=occurred_at,
                detected_at=datetime.now(timezone.utc),
                source_url=url,
                country=country if isinstance(country, str) and len(country) <= 100 else "US",
                tags=["gdelt", "osint"],
                raw_payload=raw_data,
            )
            db.add(inc)
            db.flush()
            incident_ids.append(inc.id)
            existing_urls.add(url)

        db.commit()
        return incident_ids
