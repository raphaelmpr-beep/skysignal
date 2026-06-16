"""
RSSFallbackService — multi-source OSINT news feed provider.

Sources:
  Tier 1 — Topic-specific Google News queries (high relevance, 100 items each)
    • UAS / drone security & threats
    • Counter-UAS / C-UAS
    • Drone + critical infrastructure
    • Drone + prison / corrections smuggling
    • Drone + military base incursions

  Tier 2 — Specialist defense & UAS publications (RSS)
    • C4ISRNET       — defense electronics & C-UAS reporting
    • Defense One    — national security + Pentagon UAS policy
    • Breaking Defense — procurement, CUAS programs, threat assessments
    • sUAS News      — UAS industry incidents and near-misses
    • DroneLife      — commercial UAS incidents, FAA enforcement
    • Bellingcat     — open-source investigative (drone warfare, surveillance)

  All articles: review_status=PENDING, confidence_tier=LOW per platform rules.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (compatible; SkySignal/1.1; +https://skysignal.vercel.app)"


def _gnews(query: str) -> str:
    """Build a Google News RSS URL for a query."""
    return (
        f"https://news.google.com/rss/search"
        f"?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    )


# Feed registry — (name, url, category)
FEED_REGISTRY: list[tuple[str, str, str]] = [
    # ── Tier 1: Google News topic queries ─────────────────────────────────────
    ("Google News: UAS threats",     _gnews('UAS drone "unmanned aircraft" security threat incident'), "google-news"),
    ("Google News: C-UAS",           _gnews('counter-drone OR "counter-UAS" OR "drone detection" OR "drone interdiction"'), "google-news"),
    ("Google News: Drone Infra",     _gnews('drone "critical infrastructure" OR "power grid" OR nuclear OR refinery OR pipeline airport'), "google-news"),
    ("Google News: Prison Drone",    _gnews('drone prison jail contraband smuggling'), "google-news"),
    ("Google News: Military Drone",  _gnews('drone incursion "military base" OR "air force base" OR "naval station" OR "army base"'), "google-news"),
    ("Google News: Near Miss",       _gnews('drone "near miss" OR "near-miss" aircraft airplane helicopter'), "google-news"),
    ("Google News: Border Drone",    _gnews('drone border cartel smuggling CBP patrol'), "google-news"),

    # ── Tier 2: Specialist publications ───────────────────────────────────────
    ("C4ISRNET",       "https://www.c4isrnet.com/arc/outboundfeeds/rss/?outputType=xml",  "defense"),
    ("Defense One",    "https://www.defenseone.com/rss/all/",                              "defense"),
    ("Breaking Defense","https://breakingdefense.com/feed/",                               "defense"),
    ("sUAS News",      "https://www.suasnews.com/feed/",                                   "uas-industry"),
    ("DroneLife",      "https://dronelife.com/feed/",                                      "uas-industry"),
    ("Bellingcat",     "https://www.bellingcat.com/feed/",                                 "osint-investigative"),
    ("FlightGlobal",   "https://www.flightglobal.com/rss/",                                "aviation"),
]

# Keywords that must appear in title or description for Tier 2 feeds
# (Google News queries are already filtered by query; specialist feeds need post-filter)
RELEVANCE_KEYWORDS = {
    "drone", "uav", "uas", "unmanned", "quadcopter", "multirotor",
    "sUAS", "suas", "counter-drone", "c-uas", "cuas", "rpas",
    "dji", "phantom", "mavic", "reaper", "predator",
}


class RSSFallbackService:
    """
    Collects OSINT drone/UAS incident articles from a curated multi-source
    RSS pipeline. Falls back gracefully when individual feeds are unavailable.
    """

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

    def _is_relevant(self, title: str, description: str, category: str) -> bool:
        """Google News feeds are pre-filtered by query — always relevant.
        Specialist feeds need keyword matching."""
        if category in ("google-news",):
            return True
        text = f"{title} {description}".lower()
        return any(kw in text for kw in RELEVANCE_KEYWORDS)

    def search(self, query: str, *, days: int, limit: int = 100) -> list[dict]:
        """
        Fetch articles from all feeds, deduplicated by URL.

        Args:
            query:  ignored for Google News feeds (already baked into URLs);
                    used as additional keyword filter on Tier 2 feeds.
            days:   max age in days; articles older than this are dropped.
            limit:  max total articles to return.
        """
        extra_kws = {
            k.lower() for k in query.replace("OR", " ").split()
            if len(k.strip()) > 2
        }
        cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, days))

        rows: list[dict] = []
        seen_urls: set[str] = set()
        feed_stats: dict[str, int] = {}

        with httpx.Client(
            timeout=20.0,
            follow_redirects=True,
            headers={"User-Agent": _UA},
        ) as client:
            for feed_name, feed_url, category in FEED_REGISTRY:
                if len(rows) >= limit:
                    break

                try:
                    response = client.get(feed_url)
                    response.raise_for_status()
                except Exception as exc:
                    logger.warning("Feed unavailable [%s]: %s", feed_name, exc)
                    continue

                try:
                    root = ET.fromstring(response.text)
                except Exception as exc:
                    logger.warning("Feed parse error [%s]: %s", feed_name, exc)
                    continue

                feed_count = 0
                for item in root.findall(".//item"):
                    if len(rows) >= limit:
                        break

                    title = (item.findtext("title") or "").strip()
                    url = (item.findtext("link") or "").strip()
                    pub_raw = (item.findtext("pubDate") or "").strip()
                    description = (item.findtext("description") or "").strip()
                    pub_dt = self._parse_rfc_datetime(pub_raw)

                    if not title or not url or url in seen_urls:
                        continue
                    if pub_dt and pub_dt < cutoff:
                        continue
                    if not self._is_relevant(title, description, category):
                        continue

                    seen_urls.add(url)
                    feed_count += 1
                    rows.append({
                        "title": title,
                        "url": url,
                        "seendate": pub_dt.isoformat() if pub_dt else None,
                        "domain": feed_url,
                        "sourcecountry": "US",
                        "tone": None,
                        "locations": [],
                        "raw": {
                            "provider": "rss_multi",
                            "feed_name": feed_name,
                            "feed_category": category,
                            "feed_url": feed_url,
                            "pubDate": pub_raw,
                            "description": description[:500],
                        },
                    })

                feed_stats[feed_name] = feed_count
                logger.info("Feed [%s]: %d articles collected", feed_name, feed_count)

        logger.info(
            "RSS multi-feed total: %d articles from %d feeds",
            len(rows),
            sum(1 for v in feed_stats.values() if v > 0),
        )
        return rows

    def get_feed_status(self) -> list[dict]:
        """Check all feeds and return their health status."""
        status = []
        with httpx.Client(timeout=10.0, follow_redirects=True, headers={"User-Agent": _UA}) as client:
            for feed_name, feed_url, category in FEED_REGISTRY:
                try:
                    r = client.get(feed_url)
                    root = ET.fromstring(r.text)
                    item_count = len(root.findall(".//item"))
                    status.append({
                        "feed": feed_name,
                        "category": category,
                        "http_status": r.status_code,
                        "items": item_count,
                        "ok": r.status_code == 200,
                    })
                except Exception as exc:
                    status.append({
                        "feed": feed_name,
                        "category": category,
                        "http_status": None,
                        "items": 0,
                        "ok": False,
                        "error": str(exc)[:100],
                    })
        return status
