# skysignal-api v1.1.0 — source_tag filter
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("skysignal")
from app.routers import (
    incidents, assessments, sources, evidence,
    map, analytics, reports, admin, salute, auth, watch_zones
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
app.include_router(watch_zones.router, prefix="/api/watch-zones", tags=["watch-zones"])


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error", "error": str(exc)[:500]},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": f"{type(exc).__name__}: {str(exc)[:400]}"},
    )


@app.get("/health", tags=["health"])
def health():
    """Health check — always returns 200 so Railway doesn't kill a healthy process.
    DB connectivity reported in payload but does NOT affect HTTP status."""
    from app.db import engine
    from sqlalchemy import text
    db_status = "ok"
    db_error = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health DB check failed: {e}")
        db_status = "unreachable"
        db_error = str(e)[:200]
    payload = {"status": "ok", "service": "skysignal-api", "version": "1.1.0", "db": db_status}
    if db_error:
        payload["db_error"] = db_error
    return payload


@app.get("/health/db", tags=["health"])
def health_db():
    """Test database connectivity — useful for diagnosing Railway connection issues."""
    from app.db import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), version()"))
            row = result.fetchone()
            return {
                "status": "ok",
                "database": row[0],
                "pg_version": row[1][:60],
                "db_url_host": engine.url.host,
            }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "error": str(e)[:500]},
        )

