# SkySignal Architecture

## Stack Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Browser                                                    │
│  Next.js 14 App Router  (TypeScript, Tailwind, shadcn/ui)  │
│  Port 3000                                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (fetch / API routes)
┌──────────────────────────▼──────────────────────────────────┐
│  FastAPI  (Python 3.11)                                     │
│  SQLAlchemy 2.0 ORM   Pydantic v2 schemas                   │
│  Port 8000                                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ psycopg2
┌──────────────────────────▼──────────────────────────────────┐
│  PostgreSQL 15 + PostGIS 3                                  │
│  Port 5432                                                  │
└─────────────────────────────────────────────────────────────┘
```

All three services are orchestrated by `docker-compose.yml` at the repo root.

---

## Frontend (Next.js 14)

### App Router structure

```
apps/web/app/
  (auth)/
    login/page.tsx           — Login form
  (dashboard)/
    layout.tsx               — Sidebar + header shell
    dashboard/page.tsx       — KPI cards, recent incidents
    incidents/
      page.tsx               — Filtered, paginated incident table
      [id]/page.tsx          — Incident detail + evidence stack
    assessments/
      new/page.tsx           — Location input + radius/window form
      [id]/page.tsx          — Score result + factor breakdown
    map/page.tsx             — Leaflet COP map with heatmap
    analytics/page.tsx       — Sankey, timeline, sector charts
    reports/page.tsx         — Generated report list
    sources/page.tsx         — Data source management
    admin/
      review/page.tsx        — PENDING incident queue
      settings/page.tsx      — Org settings
  api/
    auth/login/route.ts      — Next.js API route proxies login to FastAPI
  layout.tsx                 — Root layout (fonts, providers)
  globals.css                — Tailwind base styles
```

### Rendering strategy

- All dashboard pages are **client components** (`"use client"`) — data is fetched client-side via custom hooks (`useIncidents`, `useAssessment`, etc.) that call the FastAPI backend directly through `lib/api.ts`.
- The login page is a client component; auth state is stored in `localStorage` (JWT token + user object).
- The root `layout.tsx` wraps the app in providers (toast, etc.).
- The Next.js API route `/api/auth/login` acts as a thin proxy to avoid CORS issues when the browser calls the FastAPI backend.

### Key libraries

| Library | Purpose |
|---|---|
| Tailwind CSS | Utility-first styling |
| shadcn/ui | Pre-built accessible component library |
| Leaflet + react-leaflet | Interactive maps |
| leaflet.heat | Heatmap layer |
| leaflet.markercluster | Incident clustering at zoom |
| Recharts | KPI and analytics charts |
| d3-sankey | Sankey flow diagram |

---

## Backend (FastAPI)

### Router map

```
apps/api/
  main.py                  — App factory, router registration, CORS
  app/
    auth.py                — JWT creation, get_current_user dependency
    db.py                  — SQLAlchemy engine + session factory + Base
    models.py              — SQLAlchemy 2.0 ORM models
    schemas.py             — Pydantic v2 request/response schemas
    routers/
      auth.py              — POST /api/auth/login
      incidents.py         — CRUD + filter + pagination
      evidence.py          — Evidence CRUD per incident
      assessments.py       — Facility assessment creation + history
      map.py               — /map/incidents, /map/heatmap
      analytics.py         — KPI, Sankey, timeline, A/B comparison
      admin.py             — Review queue, approve/reject, audit log
      salute.py            — SALUTE report submission + list
      reports.py           — Report generation (PDF/HTML)
      sources.py           — Source CRUD
    services/
      threat_score_service.py       — 7-factor scoring engine
      confidence_service.py         — Evidence-driven confidence recompute
      geocoding_service.py          — Address → lat/lon (Nominatim)
      report_generation_service.py  — HTML template → WeasyPrint PDF
      gdelt_service.py              — GDELT ingestion stub
      official_validation_service.py — Official source match scoring stub
```

### Authentication

SkySignal uses **stateless JWT auth** (no sessions, no cookies):

1. Client `POST /api/auth/login` with `{email, password}`.
2. FastAPI verifies credentials against `users.password_hash` (bcrypt).
3. Returns `{access_token, token_type, user}`.
4. Client stores token in `localStorage` (via `lib/auth.ts`).
5. All subsequent API calls include `Authorization: Bearer <token>`.
6. `get_current_user` dependency decodes the JWT and returns the user context.
7. Every router injects `get_current_user` to enforce authentication and extract `org_id` for multi-tenant scoping.

**Dev bypass:** Setting `SKIP_AUTH=true` in `.env` makes `get_current_user` return a hardcoded demo user without JWT verification. This must never be enabled in production.

### Multi-tenancy

Every database query is scoped to `org_id` extracted from the JWT. There is no cross-org data leakage by design — all queries include `.filter(Model.org_id == current_user["org_id"])`.

---

## Database (PostgreSQL + PostGIS)

### Migrations

Migrations are plain SQL files run in order:

| File | Purpose |
|---|---|
| `001_initial_schema.sql` | Core schema: orgs, users, sources, incidents, evidence, SALUTE, watch zones, assessments, alerts, reports, audit logs |
| `002_cisa_mapping.sql` | CISA 16-sector enum, `cisa_sector` column on incidents, `sector_cisa_mapping` table, auto-assign trigger |
| `003_salute_schema.sql` | PostGIS geography on SALUTE reports, attachments table, SALUTE templates |

### Spatial queries

Incidents store both raw `latitude`/`longitude` float columns and a PostGIS `GEOGRAPHY(POINT, 4326)` column named `location`. The threat score service uses `ST_DWithin` for radius queries and `ST_Distance` to compute per-incident proximity scores:

```sql
SELECT id, confidence_score, severity, occurred_at,
       ST_Distance(
         ST_MakePoint(lon, lat)::geography,
         ST_MakePoint(:lon, :lat)::geography
       ) AS dist_meters
FROM incidents
WHERE
  org_id = :org_id
  AND occurred_at >= :since
  AND ST_DWithin(
    ST_MakePoint(lon, lat)::geography,
    ST_MakePoint(:lon, :lat)::geography,
    :radius_meters
  )
```

---

## Threat Reality Score Algorithm

The 7-factor algorithm is implemented in `apps/api/app/services/threat_score_service.py`.

### Inputs
- Facility latitude/longitude
- Search radius in miles
- Time window in days
- All APPROVED incidents within those constraints

### Factor computation

| Factor | Weight | Method |
|---|---|---|
| Evidence Confidence | 30% | Simple average of `confidence_score` across nearby incidents |
| Incident Density | 20% | `log(count+1) / log(51)` × 100 — log scale with reference max of 50 incidents |
| Recency | 15% | Exponential decay: `e^(−ln(2)×age_days/30)` per incident, averaged × 100 |
| Facility Proximity | 15% | `(1 − dist/radius)` × 100 per incident, averaged |
| Severity | 10% | CRITICAL=100, HIGH=75, MEDIUM=50, LOW=25, INFORMATIONAL=10; averaged |
| Sector Sensitivity | 5% | Lookup table: MILITARY/AVIATION/NUCLEAR=100, down to RESIDENTIAL=30 |
| Repeat Pattern | 5% | Fraction of incidents within 1 km micro-clusters × 100 |

### Final score

```
score = Σ(factor_score × weight)   capped to [0, 100]
```

### Tiers

| Range | Tier |
|---|---|
| 0–20 | MINIMAL |
| 21–40 | LOW |
| 41–60 | MODERATE |
| 61–80 | ELEVATED |
| 81–100 | HIGH |

---

## Data Pipeline

```
                                 ┌──────────────────────┐
  Manual SALUTE form ────────────►  salute_reports       │
                                 │  review_status=PENDING │
                                 └──────────┬───────────┘
                                            │ Admin triage
                                            ▼
                                 ┌──────────────────────┐
  GDELT / RSS / NewsAPI ─────────►  incidents            │
  (ENABLE_GDELT=true)            │  confidence_tier=     │
                                 │  UNVERIFIED           │
                                 │  review_status=PENDING │
                                 └──────────┬───────────┘
                                            │
  Official press / FAA ─────────► official_validation_service
  (official_match_score ≥ 80)              │ auto-boosts confidence_score
                                            │
                                 ┌──────────▼───────────┐
                                 │  Admin Review Queue   │
                                 │  /admin/review        │
                                 └──────────┬───────────┘
                                            │ Approve / Reject
                                 ┌──────────▼───────────┐
                                 │  review_status=       │
                                 │  APPROVED             │
                                 │  (visible on map,     │
                                 │   in assessments)     │
                                 └──────────────────────┘
```

**Invariant:** Only APPROVED incidents contribute to threat scores and map visualization. PENDING and REJECTED incidents are never surfaced to non-admin users.

---

## Confidence Scoring

Implemented in `apps/api/app/services/confidence_service.py`.

The confidence score (0–100) is recomputed whenever evidence is added or updated:

1. Start at 0.
2. `OFFICIAL_CONFIRMATION` from an official source: +40.
3. `OFFICIAL_CONFIRMATION` from a non-official source: +20.
4. `CORROBORATION` from an official source: +20.
5. `CORROBORATION` from non-official: +10.
6. 2nd/3rd/4th corroborating source: +5 each (max +20 bonus).
7. Any `CONTRADICTION` evidence: −15.
8. No evidence: score = 0 (UNVERIFIED).

Score maps to tier: ≥80 = VERIFIED, ≥60 = HIGH, ≥40 = MEDIUM, ≥20 = LOW, <20 = UNVERIFIED.

---

## Deployment Options

### Local (Docker Compose)
```bash
docker compose up --build
```
Services: `db` (PostGIS), `api` (FastAPI), `web` (Next.js).

### Production (recommended)

| Component | Service |
|---|---|
| Database | Supabase (managed Postgres + PostGIS) or Neon |
| API | Railway, Render, or AWS ECS with Docker image |
| Web | Vercel (Next.js native deployment) |

**Required environment changes for production:**
- `SKIP_AUTH=false`
- `NEXTAUTH_SECRET` — rotate with `openssl rand -base64 32`
- `API_SECRET_KEY` — generate new strong random key
- `DATABASE_URL` — point to managed Postgres instance
- `NEXTAUTH_URL` — set to your production domain

### Build production Docker images
```bash
docker compose -f docker-compose.prod.yml up --build
```
The web Dockerfile uses a multi-stage build (deps → builder → runner) targeting the Next.js standalone output mode for minimal image size.
