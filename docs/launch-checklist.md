# SkySignal Launch Checklist

## Phase 1: Local MVP (Complete)
- [x] PostgreSQL + PostGIS database schema
- [x] Docker Compose with db + api + web services
- [x] 25 seeded demo incidents (mixed types, sectors, confidence tiers)
- [x] FastAPI backend with all 10 routers
- [x] Threat Reality Score (7-factor weighted algorithm)
- [x] Next.js 14 App Router frontend
- [x] Login with JWT auth + dev bypass
- [x] Dashboard with KPI cards
- [x] Assess Location workflow
- [x] Threat score result page with factor breakdown
- [x] Leaflet map with heatmap, clustering, radius rings
- [x] Incident table with filters and pagination
- [x] Incident detail with evidence stack and SALUTE fields
- [x] Admin review queue
- [x] SALUTE report form
- [x] Analytics with Sankey, timeline, sector distribution
- [x] PDF/HTML report generation
- [x] CISA 16-sector dual taxonomy
- [x] Modified UAS SALUTE framework (E.2 fields)
- [x] Audit log trail on all incident changes
- [x] Data pipeline: PENDING → Review → APPROVED flow

## Phase 2: Beta Hardening (Next)
- [ ] Replace dev auth bypass with proper session management
- [ ] Email/password reset flow
- [ ] Multi-org isolation testing
- [ ] Rate limiting on API (slowapi)
- [ ] Input sanitization and SQL injection audit
- [ ] HTTPS/TLS configuration
- [ ] Proper error pages (404, 500)
- [ ] Structured logging (JSON logs)
- [ ] Health check endpoints for load balancers
- [ ] Database connection pooling (pgBouncer)

## Phase 3: Data Sources
- [ ] FAA UAS Sightings CSV importer (public dataset)
- [ ] GDELT API integration (enable with `ENABLE_GDELT=true`)
- [ ] RSS/news importer (NewsAPI or custom RSS parser)
- [ ] Official press release validator (DOJ/DHS/FBI)
- [ ] DragonSync/WarDragon sensor ingest endpoint (Section B, Addendum v1.1)
- [ ] Automated nightly ingestion cron

## Phase 4: Production Deployment
- [ ] Managed Postgres with PostGIS (Supabase or Neon)
- [ ] API on Railway/Render/ECS with auto-scaling
- [ ] Web on Vercel (git-push deploy)
- [ ] CDN for static assets
- [ ] Rotate all secrets from `.env.example` defaults
- [ ] `NEXTAUTH_SECRET` — generate with: `openssl rand -base64 32`
- [ ] `API_SECRET_KEY` — generate new strong key
- [ ] Database password hardening
- [ ] Set `SKIP_AUTH=false`
- [ ] Sentry error tracking integration
- [ ] Uptime monitoring (Betterstack/UptimeRobot)

## Phase 5: SaaS Hardening
- [ ] Stripe subscription integration
- [ ] Per-org usage metering (incident count, assessments/month)
- [ ] Org invitation flow
- [ ] Role-based access control enforcement audit
- [ ] Webhook outbound notifications for watch zone alerts
- [ ] Export API (CSV/JSON bulk export)
- [ ] Audit log retention policy
- [ ] GDPR/compliance data deletion

## Phase 6: Advanced Features
- [ ] Real-time SSE updates (incidents feed, admin alerts)
- [ ] Mobile-responsive map improvements
- [ ] Named Areas of Interest (NAI) auto-detection (Section G.6, Addendum v1.2)
- [ ] CIRCIA compliance report pre-population
- [ ] Bulk incident import (CSV upload)
- [ ] Saved search + alert rules
- [ ] AntV Infographic summary cards
- [ ] API v2 public endpoint for vetted partners
