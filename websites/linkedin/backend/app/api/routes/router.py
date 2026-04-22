from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, feed, jobs, search

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(feed.router, prefix="/feed", tags=["feed"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

