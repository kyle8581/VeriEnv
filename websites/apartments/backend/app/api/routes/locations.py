from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.location import Location
from app.schemas import LocationPublic

router = APIRouter()


@router.get("/locations", response_model=list[LocationPublic])
def search_locations(
    query: str = Query(default="", max_length=120),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    q = (query or "").strip()
    if not q:
        return (
            db.query(Location)
            .order_by(Location.name.asc())
            .limit(limit)
            .all()
        )

    like = f"%{q}%"
    return (
        db.query(Location)
        .filter(or_(Location.name.ilike(like), Location.state.ilike(like)))
        .order_by(Location.name.asc())
        .limit(limit)
        .all()
    )

