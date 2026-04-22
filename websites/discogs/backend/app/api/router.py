from __future__ import annotations

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.account import router as account_router
from app.api.catalog import router as catalog_router
from app.api.marketplace import router as marketplace_router


router = APIRouter()

router.include_router(auth_router)
router.include_router(account_router)
router.include_router(catalog_router)
router.include_router(marketplace_router)

@router.get("/healthz")
def healthz() -> dict:
    return {"ok": True}

