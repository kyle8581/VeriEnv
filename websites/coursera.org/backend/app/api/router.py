from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, catalog, leads


api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(catalog.router, tags=["catalog"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])

