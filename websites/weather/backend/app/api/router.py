from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, content, locations, me, subscription, weather


api_router = APIRouter()


@api_router.get("/health")
def health():
    return {"status": "ok"}


api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(content.router)
api_router.include_router(locations.router)
api_router.include_router(weather.router)
api_router.include_router(subscription.router)

