"""
RSSFallbackService — lightweight OSINT fallback provider when GDELT is throttled.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import httpx

logger = logging.getLogger(__name__)


class RSSFallbackService:
    """Collects fallback OSINT articles from public RSS feeds."""

    FEEDS = [
        "https://news.google.com/rss/search?q=drone+OR+uav+OR+unmanned+aircraft&hl=en-US&gl=US&ceid=US:en",
        "https://www.bing.com/news/search?q=drone+uav&format=RSS",
    ]

    def _parse_rfc_datetime(self, raw: str | None) -> datetime | None:
        if not raw:
            return None
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    def search(self, query: str, *, days: int, limit: int = 25) -> list[dict]:
        keywords = [k.lower() for k in query.replace("OR", " ").split() if len(k.strip()) > 2]
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, days))

        rows: list[dict] = []
        seen_urls: set[str] = set()

        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            for feed in self.FEEDS:
                try:
                    response = client.get(
                        feed,
                        headers={"User-Agent": "SkySignal/1.0 (+https://skysignal.vercel.app)"},
                    )
                    response.raise_for_status()
                except Exception as exc:
                    logger.warning("RSS fallback feed failed %s: %s", feed, exc)
                    continue

                try:
                    root = ET.fromstring(response.text)
                except Exception as exc:
                    logger.warning("RSS fallback parse failed %s: %s", feed, exc)
                    continue

                for item in root.findall(".//item"):
                    title = (item.findtext("title") or "").strip()
                    url = (item.findtext("link") or "").strip()
                    pub_raw = (item.findtext("pubDate") or "").strip()
                    pub_dt = self._parse_rfc_datetime(pub_raw)

                    if not title or not url or url in seen_urls:
                        continue
                    if pub_dt and pub_dt < cutoff:
                        continue

                    text = f"{title} {url}".lower()
                    if keywords and not any(k in text for k in keywords):
                        continue

                    seen_urls.add(url)
                    rows.append(
                        {
                            "title": title,
                            "url": url,
                            "seendate": pub_dt.isoformat() if pub_dt else None,
                            "domain": feed,
                            "sourcecountry": "US",
                            "tone": None,
                            "locations": [],
                            "raw": {
                                "provider": "rss_fallback",
                                "feed": feed,
                                "pubDate": pub_raw,
                                "description": (item.findtext("description") or "").strip(),
                            },
                        }
                    )
                    if len(rows) >= limit:
                        return rows

        return rows
