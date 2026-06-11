#!/usr/bin/env python3
"""
SkySignal MVP — Database Seed Script
Populates the database with demo organization, admin user, sources,
25 realistic drone incidents, watch zones, and a facility assessment.

Usage:
    DATABASE_URL=postgresql://skysignal:skysignal@localhost:5432/skysignal python seed.py
"""

import json
import os
import uuid
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from psycopg2.extras import execute_values, register_uuid
from psycopg2.extensions import register_adapter, adapt

# Register UUID adapter so psycopg2 sends uuid.UUID objects as proper UUID type
register_uuid()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://skysignal:skysignal@localhost:5432/skysignal",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def new_id() -> str:
    return str(uuid.uuid4())


def bcrypt_hash(password: str) -> str:
    """Return bcrypt hash for the given password."""
    try:
        from passlib.hash import bcrypt as _bcrypt  # type: ignore
        return _bcrypt.hash(password)
    except ImportError:
        # Fallback: use hashlib (not secure — for local dev only)
        import hashlib
        return "$2b$12$" + hashlib.sha256(password.encode()).hexdigest()[:53]


def make_point_sql(lon: float, lat: float) -> str:
    """Return a PostGIS geography literal for inline SQL."""
    return f"ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)"


# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

INCIDENTS_JSON_PATH = os.path.join(os.path.dirname(__file__), "seed_incidents.json")

with open(INCIDENTS_JSON_PATH, "r") as fh:
    INCIDENTS_RAW = json.load(fh)


def seed(conn):
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # 1. Organization
    # ------------------------------------------------------------------
    org_id = new_id()
    cur.execute(
        """
        INSERT INTO organizations (id, name, slug, plan, is_active, settings)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (slug) DO UPDATE
            SET name = EXCLUDED.name,
                plan = EXCLUDED.plan,
                updated_at = NOW()
        RETURNING id
        """,
        (org_id, "SkySignal Demo", "demo", "enterprise", True, json.dumps({})),
    )
    row = cur.fetchone()
    org_id = str(row[0])
    print(f"[org]  organization id = {org_id}")

    # ------------------------------------------------------------------
    # 2. Admin User
    # ------------------------------------------------------------------
    user_id = new_id()
    password_hash = bcrypt_hash("demo1234")
    cur.execute(
        """
        INSERT INTO users (id, organization_id, email, name, password_hash, role, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email) DO UPDATE
            SET name = EXCLUDED.name,
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                updated_at = NOW()
        RETURNING id
        """,
        (
            user_id,
            org_id,
            "admin@skysignal.dev",
            "SkySignal Admin",
            password_hash,
            "ORG_ADMIN",
            True,
        ),
    )
    row = cur.fetchone()
    user_id = str(row[0])
    print(f"[user] admin user id = {user_id}")

    # ------------------------------------------------------------------
    # 3. Sources
    # ------------------------------------------------------------------
    sources = [
        {
            "id": new_id(),
            "organization_id": org_id,
            "name": "Manual SALUTE Report",
            "source_type": "MANUAL",
            "base_url": None,
            "feed_url": None,
            "credibility_score": 75,
            "is_official": False,
            "is_active": True,
            "fetch_config": {},
        },
        {
            "id": new_id(),
            "organization_id": org_id,
            "name": "GDELT Event Stream (Stub)",
            "source_type": "GDELT",
            "base_url": "https://api.gdeltproject.org/api/v2/tv/tv",
            "feed_url": "https://api.gdeltproject.org/api/v2/tv/tv",
            "credibility_score": 55,
            "is_official": False,
            "is_active": False,
            "fetch_config": {"keywords": ["drone", "UAS", "unmanned aerial"], "mode": "ArtList"},
        },
        {
            "id": new_id(),
            "organization_id": org_id,
            "name": "FAA UAS Sightings Report",
            "source_type": "FAA",
            "base_url": "https://www.faa.gov/uas/resources/public_records/uas_sightings_report",
            "feed_url": "https://www.faa.gov/uas/resources/public_records/uas_sightings_report",
            "credibility_score": 90,
            "is_official": True,
            "is_active": True,
            "fetch_config": {"format": "xlsx", "frequency_hours": 24},
        },
        {
            "id": new_id(),
            "organization_id": org_id,
            "name": "RSS News Feed — Drone Incidents",
            "source_type": "RSS",
            "base_url": "https://news.google.com/rss/search?q=drone+incident+security",
            "feed_url": "https://news.google.com/rss/search?q=drone+incident+security",
            "credibility_score": 45,
            "is_official": False,
            "is_active": False,
            "fetch_config": {"max_items": 50, "frequency_minutes": 30},
        },
    ]

    source_ids = {}
    for s in sources:
        cur.execute(
            """
            INSERT INTO sources
              (id, organization_id, name, source_type, base_url, feed_url,
               credibility_score, is_official, is_active, fetch_config)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id, name
            """,
            (
                s["id"],
                s["organization_id"],
                s["name"],
                s["source_type"],
                s["base_url"],
                s["feed_url"],
                s["credibility_score"],
                s["is_official"],
                s["is_active"],
                json.dumps(s["fetch_config"]),
            ),
        )
        row = cur.fetchone()
        if row:
            source_ids[s["source_type"]] = str(row[0])
            print(f"[src]  {row[1]} => {row[0]}")

    # Pick source IDs to assign to incidents
    manual_src_id = source_ids.get("MANUAL")
    faa_src_id = source_ids.get("FAA")

    # ------------------------------------------------------------------
    # 4. Incidents (25 realistic incidents from seed_incidents.json)
    # ------------------------------------------------------------------
    incident_ids = []
    for idx, inc in enumerate(INCIDENTS_RAW):
        inc_id = new_id()
        lat = inc["latitude"]
        lon = inc["longitude"]

        # Choose source
        if "FAA" in inc.get("tags", []) or "ASRS" in inc.get("source_url", ""):
            src_id = faa_src_id
        else:
            src_id = manual_src_id

        occurred_at = inc.get("occurred_at", "2024-01-01T00:00:00Z")

        cur.execute(
            f"""
            INSERT INTO incidents
              (id, organization_id, title, summary, incident_type,
               operational_sector, severity, confidence_score, confidence_tier,
               review_status, occurred_at,
               latitude, longitude,
               location_name, city, region, country,
               source_id, source_url,
               drone_type, drone_make, drone_model, altitude_agl,
               tags, classification_json, is_public)
            VALUES
              (%s, %s, %s, %s, %s,
               %s, %s, %s, %s,
               %s, %s,
               %s, %s,
               %s, %s, %s, %s,
               %s, %s,
               %s, %s, %s, %s,
               %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
            """,
            (
                inc_id,
                org_id,
                inc["title"],
                inc.get("summary", ""),
                inc["incident_type"],
                inc.get("operational_sector"),
                inc["severity"],
                inc["confidence_score"],
                inc["confidence_tier"],
                inc["review_status"],
                occurred_at,
                lat,
                lon,
                inc.get("location_name", ""),
                inc.get("city", ""),
                inc.get("region", "US"),
                inc.get("country", "US"),
                src_id,
                inc.get("source_url", ""),
                inc.get("drone_type"),
                inc.get("drone_make"),
                inc.get("drone_model"),
                inc.get("altitude_agl"),
                inc.get("tags", []),
                json.dumps({}),
                inc["review_status"] == "APPROVED",
            ),
        )
        row = cur.fetchone()
        if row:
            incident_ids.append(str(row[0]))
            print(f"[inc]  [{idx+1:02d}] {inc['title'][:60]} => {row[0]}")

    print(f"\n[inc]  Total incidents inserted: {len(incident_ids)}")

    # ------------------------------------------------------------------
    # 5. Watch Zones (3)
    # ------------------------------------------------------------------
    watch_zones_data = [
        {
            "id": new_id(),
            "organization_id": org_id,
            "created_by": user_id,
            "name": "MacDill AFB Perimeter Watch",
            "description": "Active watch zone around MacDill Air Force Base — Tampa, FL",
            "facility_name": "MacDill Air Force Base",
            "address": "MacDill AFB, Tampa, FL 33621",
            "latitude": 27.8493,
            "longitude": -82.5219,
            "radius_miles": 10.0,
            "alert_on_new_incident": True,
            "is_active": True,
            "cisa_sector": "DEFENSE_INDUSTRIAL_BASE",
            "operational_sector": "MILITARY",
        },
        {
            "id": new_id(),
            "organization_id": org_id,
            "created_by": user_id,
            "name": "JFK Airport Perimeter Watch",
            "description": "Active watch zone around John F. Kennedy International Airport",
            "facility_name": "JFK International Airport",
            "address": "Queens, New York, NY 11430",
            "latitude": 40.6413,
            "longitude": -73.7781,
            "radius_miles": 5.0,
            "alert_on_new_incident": True,
            "is_active": True,
            "cisa_sector": "TRANSPORTATION_SYSTEMS",
            "operational_sector": "AVIATION",
        },
        {
            "id": new_id(),
            "organization_id": org_id,
            "created_by": user_id,
            "name": "US Capitol Secure Zone",
            "description": "Monitor P-56 restricted airspace for any UAS incursions near the US Capitol",
            "facility_name": "US Capitol Building",
            "address": "First St SE, Washington, DC 20004",
            "latitude": 38.8899,
            "longitude": -77.0091,
            "radius_miles": 3.0,
            "alert_on_new_incident": True,
            "is_active": True,
            "cisa_sector": "GOVERNMENT_FACILITIES",
            "operational_sector": "GOVERNMENT",
        },
    ]

    wz_ids = []
    for wz in watch_zones_data:
        lat = wz["latitude"]
        lon = wz["longitude"]
        cur.execute(
            f"""
            INSERT INTO watch_zones
              (id, organization_id, created_by, name, description, facility_name, address,
               latitude, longitude, radius_miles,
               alert_on_new_incident, is_active, cisa_sector, operational_sector)
            VALUES
              (%s, %s, %s, %s, %s, %s, %s,
               %s, %s, %s,
               %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
            """,
            (
                wz["id"],
                wz["organization_id"],
                wz["created_by"],
                wz["name"],
                wz["description"],
                wz["facility_name"],
                wz["address"],
                lat,
                lon,
                wz["radius_miles"],
                wz["alert_on_new_incident"],
                wz["is_active"],
                wz["cisa_sector"],
                wz["operational_sector"],
            ),
        )
        row = cur.fetchone()
        if row:
            wz_ids.append(str(row[0]))
            print(f"[wz]   {wz['name']} => {row[0]}")

    # ------------------------------------------------------------------
    # 6. Facility Assessment — MacDill AFB
    # ------------------------------------------------------------------
    # Find MacDill incident IDs (incidents near Tampa)
    cur.execute(
        """
        SELECT id FROM incidents
        WHERE organization_id = %s
          AND latitude BETWEEN 27.4 AND 28.3
          AND longitude BETWEEN -83.0 AND -82.0
        """,
        (org_id,),
    )
    nearby_rows = cur.fetchall()
    nearby_ids = [str(r[0]) for r in nearby_rows]

    assessment_id = new_id()
    macdill_wz_id = wz_ids[0] if wz_ids else None

    cur.execute(
        """
        INSERT INTO facility_assessments
          (id, organization_id, requested_by, facility_name, address,
           latitude, longitude, radius_miles, time_window_days,
           threat_reality_score, score_tier,
           factor_evidence_confidence, factor_incident_density,
           factor_recency, factor_facility_proximity,
           factor_severity, factor_sector_sensitivity, factor_repeat_pattern,
           incident_count, nearby_incident_ids,
           cisa_sector, operational_sector,
           score_explanation, raw_factors, status, watch_zone_id)
        VALUES
          (%s, %s, %s, %s, %s,
           %s, %s, %s, %s,
           %s, %s,
           %s, %s,
           %s, %s,
           %s, %s, %s,
           %s, %s,
           %s, %s,
           %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING id
        """,
        (
            assessment_id,
            org_id,
            user_id,
            "MacDill Air Force Base",
            "MacDill AFB, Tampa, FL 33621",
            27.8493,
            -82.5219,
            10.0,
            180,
            # Scores
            72, "ELEVATED",
            # Factor scores
            80, 60,
            75, 85,
            70, 95, 65,
            # Context
            len(nearby_ids),
            [uuid.UUID(x) for x in nearby_ids] if nearby_ids else [],
            "DEFENSE_INDUSTRIAL_BASE",
            "MILITARY",
            (
                "MacDill AFB presents an ELEVATED threat reality score of 72/100. "
                "A persistent fixed-wing UAS surveillance incident was confirmed on 18 Apr 2024, "
                "with no operator identified. The facility's sector sensitivity (MILITARY) "
                "contributes significantly to the composite score. Recommend continued "
                "active monitoring and coordination with AFSFC. "
                "No kinetic attacks recorded within the watch radius."
            ),
            json.dumps({
                "evidence_confidence": 80,
                "incident_density": 60,
                "recency": 75,
                "facility_proximity": 85,
                "severity": 70,
                "sector_sensitivity": 95,
                "repeat_pattern": 65,
            }),
            "COMPLETED",
            macdill_wz_id,
        ),
    )
    row = cur.fetchone()
    if row:
        print(f"[asmnt] MacDill AFB assessment => {row[0]}")

    conn.commit()
    cur.close()
    print("\n[seed] Done. Database seeded successfully.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"[seed] Connecting to: {DATABASE_URL}")
    conn = psycopg2.connect(DATABASE_URL)
    try:
        seed(conn)
    except Exception as exc:
        conn.rollback()
        raise
    finally:
        conn.close()
