# SkySignal — Drone Threat Intelligence Platform

> Drone Threat Common Operating Picture for critical infrastructure security teams.
> OSINT analysis, incident mapping, confidence scoring, and facility-level threat assessment reports.

## What is SkySignal?

SkySignal is a multi-tenant SaaS platform that helps security professionals determine how real the
drone threat is around a specific facility, address, or geographic area. It ingests OSINT and
official-source data, maps incidents, scores credibility using a 7-factor algorithm, and generates
Drone Threat Reality Score reports (0–100).

**Compliance scope:** Situational awareness, OSINT analysis, mapping, and reporting only.
This platform does not include and must never include drone interception, jamming, exploitation,
weaponization, targeting, or countermeasure execution capabilities.

## Quick Start (Local Dev — 3 commands)

### Prerequisites
- Docker Desktop with Docker Compose v2
- Node.js 20+ (for local web dev)
- Python 3.11+ (for local API dev)

### Option A: Full Docker (recommended)
```bash
git clone <repo-url> skysignal
cd skysignal
cp .env.example .env
docker compose up --build
```
Then open: http://localhost:3000

### Option B: Local dev (faster iteration)
```bash
# Terminal 1: Database only
docker compose up db

# Terminal 2: FastAPI
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../../.env.example .env
uvicorn main:app --reload --port 8000

# Terminal 3: Next.js
cd apps/web
npm install
cp ../../.env.example .env.local
npm run dev
```

### Seed the database
```bash
cd packages/database
python seed/seed.py
```
Or via Docker:
```bash
docker compose exec api python /app/seed.py
```

## Default Credentials
| Email | Password | Role |
|---|---|---|
| admin@skysignal.dev | demo1234 | Org Admin |

Or use the **Dev Login** button on the login page (only available when `SKIP_AUTH=true`).

## Primary User Workflow

1. Login at http://localhost:3000/login
2. Dashboard shows 25 seeded incidents and KPI cards
3. Click **Assess Location** → enter an address → select radius + time window → **Run Assessment**
4. View Threat Reality Score (0–100) with full factor breakdown
5. Save as Watch Zone, Generate PDF Report
6. Navigate to **Map** for full COP view with heatmap
7. **Admin → Review Queue** shows PENDING candidate incidents

## Architecture

```
apps/
  web/          Next.js 14 App Router (TypeScript, Tailwind, shadcn/ui)
  api/          FastAPI (Python 3.11, SQLAlchemy 2.0, PostGIS)
packages/
  database/
    migrations/ PostgreSQL + PostGIS schema migrations
    seed/       Demo data (25 incidents, 3 watch zones)
  shared/
    types/      TypeScript domain types (shared between web and API clients)
    constants/  Shared enumerations and scoring constants
docker-compose.yml
```

## Drone Threat Reality Score

A facility-level 0–100 score composed of 7 weighted factors:

| Factor | Weight | Description |
|---|---|---|
| Evidence Confidence | 30% | Avg confidence score of nearby incidents |
| Incident Density | 20% | Log-normalized incident count within radius |
| Recency | 15% | Exponential decay weighting recent incidents higher |
| Facility Proximity | 15% | Average distance of incidents to facility center |
| Severity | 10% | Weighted avg by severity level |
| Sector Sensitivity | 5% | CISA sector criticality multiplier |
| Repeat Pattern | 5% | Clustering of incidents in same micro-area |

Score tiers: 0–20 Minimal · 21–40 Low · 41–60 Moderate · 61–80 Elevated · 81–100 High

## Data Pipeline

```
Manual SALUTE → PENDING incident → Admin review → APPROVED
GDELT/RSS/News → PENDING candidate (LOW confidence) → Official validation → Admin review → APPROVED
Official press/FAA → can auto-boost confidence if official_match_score ≥ 80
```

**Data principle:** No GDELT/RSS/News result becomes a confirmed incident automatically.
All news-sourced candidates enter `review_status=PENDING`, `confidence_tier=UNVERIFIED`.

## API Endpoints

Base URL: http://localhost:8000

| Method | Path | Description |
|---|---|---|
| POST | /api/auth/login | Login → JWT |
| GET | /api/incidents | List incidents with filters |
| GET | /api/incidents/{id} | Incident detail + evidence |
| POST | /api/assessments | Create facility assessment |
| GET | /api/map/incidents | Map-optimized incident points |
| GET | /api/map/heatmap | Heatmap weight points |
| GET | /api/analytics/kpi | KPI dashboard data |
| GET | /api/analytics/sankey | Source→Type→Sector→Outcome flow |
| GET | /api/admin/review-queue | Pending review queue |
| POST | /api/salute | Submit SALUTE report |

Full interactive docs: http://localhost:8000/docs (FastAPI auto-generated)

## Environment Variables

See `.env.example` for all variables. Key ones:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (PostGIS required) |
| `NEXTAUTH_SECRET` | JWT signing secret — **change in production!** |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | Optional. Leave blank to use OpenStreetMap (Leaflet default) |
| `SKIP_AUTH` | Set to `"true"` for dev bypass — **never in production** |
| `ENABLE_GDELT` | Enable GDELT news ingestion pipeline |
| `ENABLE_RSS_IMPORTER` | Enable RSS/news feed importer |

## Deployment (Post-MVP)

**Recommended production stack:**
- Database: Supabase or Neon (managed Postgres with PostGIS)
- API: Railway, Render, or AWS ECS
- Web: Vercel (Next.js native)
- Ensure `SKIP_AUTH=false` and rotate all secrets from `.env.example` defaults

```bash
# Build production images
docker compose -f docker-compose.prod.yml up --build
```

## Adding Live Data Sources

Data source stubs live in `apps/api/app/services/`:
- `gdelt_service.py` — Wire to GDELT API (endpoint documented in file)
- `official_validation_service.py` — Wire to FAA DroneZone, DOJ press releases
- Enable with `ENABLE_GDELT=true` / `ENABLE_RSS_IMPORTER=true` in `.env`

## Safety & Compliance

This platform is for situational awareness and OSINT analysis only.
Do not add, and do not accept pull requests that add:
- Drone jamming, interception, or neutralization logic
- Remote access to drone control systems
- Targeting systems or fire control integration
- Any countermeasure execution (reporting fields only)
