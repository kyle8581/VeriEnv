from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.init_db import create_all, seed_if_empty
from app.db.session import SessionLocal


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)

    # CORS (default: allow local frontend port)
    allow_origins = [str(o) for o in settings.CORS_ORIGINS]
    if not allow_origins:
        allow_origins = [f"http://127.0.0.1:{settings.BACKEND_PORT + 1}", f"http://localhost:{settings.BACKEND_PORT + 1}",
        "http://localhost:12182",
        "http://127.0.0.1:12182"
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    @app.on_event("startup")
    def _startup() -> None:
        create_all()
        if settings.SEED_ON_STARTUP:
            with SessionLocal() as db:
                seed_if_empty(db)

    return app


app = create_app()

