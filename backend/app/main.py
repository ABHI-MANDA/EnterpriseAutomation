"""Enterprise Real Estate Command Center - FastAPI Backend Application."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, SessionLocal
from backend.app.services.seed_service import seed_database

# Routers
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.records import router as records_router
from backend.app.api.v1.crm_operations import router as crm_ops_router
from backend.app.api.v1.crm_sync import router as crm_sync_router
from backend.app.api.v1.events import router as events_router
from backend.app.api.v1.agents import router as agents_router
from backend.app.api.v1.dashboards import router as dashboards_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.reports import router as reports_router

def init_app_database():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)

init_app_database()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Centralized Real Estate Intelligence & Operations Command Center"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def apply_security_headers(req: Request, call_next):
    resp = await call_next(req)
    resp.headers.update({
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload"
    })
    return resp

# Health Check
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

# Register V1 API Routers
v1_prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=v1_prefix)
app.include_router(analytics_router, prefix=v1_prefix)
app.include_router(records_router, prefix=v1_prefix)
app.include_router(crm_ops_router, prefix=v1_prefix)
app.include_router(crm_sync_router, prefix=v1_prefix)
app.include_router(events_router, prefix=v1_prefix)
app.include_router(agents_router, prefix=v1_prefix)
app.include_router(dashboards_router, prefix=v1_prefix)
app.include_router(audit_router, prefix=v1_prefix)
app.include_router(reports_router, prefix=v1_prefix)

# Mount frontend directory if exists
frontend_dir = os.environ.get("FRONTEND_DIR", os.path.join(os.path.dirname(__file__), "../../frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
