from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.router import api_router
from app.core.config import settings
from app.db.init_db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    allow_origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    app.include_router(api_router, prefix=settings.api_prefix)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    return app


app = create_app()

