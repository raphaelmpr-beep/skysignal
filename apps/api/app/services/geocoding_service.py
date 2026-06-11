"""
GeocodingService — tiered geocoding for SkySignal.

Tier 1: Nominatim (OpenStreetMap) — free, no API key required
Tier 2: US Census Geocoder — free, US addresses only
Tier 3: Manual / fallback — returns None for unknown addresses
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"


class GeocodingService:
    """
    Geocodes addresses to lat/lon coordinates.
    Uses a two-tier fallback strategy.

    Usage:
        svc = GeocodingService()
        result = await svc.geocode("1600 Pennsylvania Ave NW, Washington DC")
        # {"lat": 38.897699, "lon": -77.036551, "display_name": "...", "confidence": 0.8}
    """

    async def geocode(self, address: str) -> Optional[dict]:
        """
        Returns {lat, lon, display_name, confidence} or None if not found.
        Tries Nominatim first, then Census geocoder.
        """
        result = await self._nominatim(address)
        if result:
            return result

        result = await self._census_geocoder(address)
        if result:
            return result

        logger.warning("Geocoding failed for address: %s", address)
        return None

    # ------------------------------------------------------------------
    # Tier 1: Nominatim
    # ------------------------------------------------------------------

    async def _nominatim(self, address: str) -> Optional[dict]:
        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }
        headers = {
            "User-Agent": "SkySignal/1.0 (contact@skysignal.io)",
            "Accept-Language": "en",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(NOMINATIM_URL, params=params, headers=headers)
                resp.raise_for_status()
                results = resp.json()
                if results:
                    r = results[0]
                    return {
                        "lat": float(r["lat"]),
                        "lon": float(r["lon"]),
                        "display_name": r.get("display_name", address),
                        "confidence": 0.85,
                        "source": "nominatim",
                    }
        except Exception as exc:
            logger.debug("Nominatim geocoding error: %s", exc)
        return None

    # ------------------------------------------------------------------
    # Tier 2: US Census Geocoder
    # ------------------------------------------------------------------

    async def _census_geocoder(self, address: str) -> Optional[dict]:
        params = {
            "address": address,
            "benchmark": "Public_AR_Current",
            "format": "json",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(CENSUS_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
                matches = (
                    data.get("result", {})
                    .get("addressMatches", [])
                )
                if matches:
                    m = matches[0]
                    coords = m.get("coordinates", {})
                    return {
                        "lat": float(coords.get("y", 0)),
                        "lon": float(coords.get("x", 0)),
                        "display_name": m.get("matchedAddress", address),
                        "confidence": 0.70,
                        "source": "census",
                    }
        except Exception as exc:
            logger.debug("Census geocoder error: %s", exc)
        return None

    # ------------------------------------------------------------------
    # Batch geocoding (for bulk imports)
    # ------------------------------------------------------------------

    async def geocode_batch(self, addresses: list[str]) -> list[Optional[dict]]:
        """
        Geocode multiple addresses sequentially.
        Returns list aligned with input, None for failures.
        """
        results = []
        for addr in addresses:
            result = await self.geocode(addr)
            results.append(result)
        return results
