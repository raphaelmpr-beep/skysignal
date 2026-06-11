import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    incidents, assessments, sources, evidence,
    map, analytics, reports, admin, salute, auth
)

app = FastAPI(
    title="SkySignal API",
    version="1.0.0",
    description="Drone Threat Intelligence Platform — situational awareness, OSINT analysis, and facility threat scoring.",
)

# ---------------------------------------------------------------------------
# CORS — reads from ALLOWED_ORIGINS env var (comma-separated) or uses defaults
# ---------------------------------------------------------------------------

_default_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://web:3000",
    "https://skysignal.vercel.app",
]

_env_origins = os.getenv("ALLOWED_ORIGINS", "")
_extra = [o.strip() for o in _env_origins.split(",") if o.strip()]
ALLOWED_ORIGINS = list(set(_default_origins + _extra))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/api/auth",        tags=["auth"])
app.include_router(incidents.router,   prefix="/api/incidents",   tags=["incidents"])
app.include_router(assessments.router, prefix="/api/assessments", tags=["assessments"])
app.include_router(sources.router,     prefix="/api/sources",     tags=["sources"])
app.include_router(evidence.router,    prefix="/api/evidence",    tags=["evidence"])
app.include_router(map.router,         prefix="/api/map",         tags=["map"])
app.include_router(analytics.router,   prefix="/api/analytics",   tags=["analytics"])
app.include_router(reports.router,     prefix="/api/reports",     tags=["reports"])
app.include_router(admin.router,       prefix="/api/admin",       tags=["admin"])
app.include_router(salute.router,      prefix="/api/salute",      tags=["salute"])


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": "skysignal-api", "version": "1.0.0"}
