from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, contact_requests, favorites, health, listings, locations, saved_searches

api_router = APIRouter(prefix="/api")

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(locations.router, tags=["locations"])
api_router.include_router(listings.router, tags=["listings"])
api_router.include_router(favorites.router, tags=["favorites"])
api_router.include_router(saved_searches.router, tags=["saved-searches"])
api_router.include_router(contact_requests.router, tags=["contact-requests"])

