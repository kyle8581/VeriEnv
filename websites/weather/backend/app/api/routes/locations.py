from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.location import Location, SavedLocation
from app.models.user import User


router = APIRouter(tags=["locations"])


class LocationOut(BaseModel):
    name: str
    state: str | None
    country: str
    zip_code: str | None
    latitude: float
    longitude: float
    timezone: str
    slug: str


def _score(loc: Location, q: str) -> int:
    ql = q.lower().strip()
    name = loc.name.lower()
    score = 0
    if loc.zip_code and loc.zip_code == ql:
        score += 100
    if name == ql:
        score += 50
    if name.startswith(ql):
        score += 25
    if ql in name:
        score += 10
    if loc.state and loc.state.lower() == ql:
        score += 5
    return score


@router.get("/locations/search", response_model=list[LocationOut])
def search_locations(
    q: str = Query(min_length=1, max_length=120),
    limit: int = Query(default=10, ge=1, le=25),
    session: Session = Depends(get_session),
):
    q = q.strip()
    q_digits = re.sub(r"[^0-9]", "", q)

    stmt = select(Location)
    if q_digits and len(q_digits) >= 3:
        stmt = stmt.where(Location.zip_code.like(f"{q_digits}%"))
    else:
        stmt = stmt.where(Location.name.ilike(f"%{q}%"))

    candidates = session.exec(stmt.limit(50)).all()
    candidates.sort(key=lambda l: _score(l, q_digits or q), reverse=True)
    candidates = candidates[:limit]

    return [
        LocationOut(
            name=l.name,
            state=l.state,
            country=l.country,
            zip_code=l.zip_code,
            latitude=l.latitude,
            longitude=l.longitude,
            timezone=l.timezone,
            slug=l.slug,
        )
        for l in candidates
    ]


@router.get("/locations/{slug}", response_model=LocationOut)
def get_location(slug: str, session: Session = Depends(get_session)):
    loc = session.exec(select(Location).where(Location.slug == slug)).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return LocationOut(
        name=loc.name,
        state=loc.state,
        country=loc.country,
        zip_code=loc.zip_code,
        latitude=loc.latitude,
        longitude=loc.longitude,
        timezone=loc.timezone,
        slug=loc.slug,
    )


class SaveLocationRequest(BaseModel):
    location_slug: str


@router.get("/me/locations", response_model=list[LocationOut])
def list_saved_locations(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    rows = session.exec(select(SavedLocation).where(SavedLocation.user_id == user.id)).all()
    if not rows:
        return []
    loc_ids = [r.location_id for r in rows]
    locs = session.exec(select(Location).where(Location.id.in_(loc_ids))).all()
    # stable order: newest first based on SavedLocation.created_at
    loc_by_id = {l.id: l for l in locs}
    rows.sort(key=lambda r: r.created_at, reverse=True)
    out: list[LocationOut] = []
    for r in rows:
        l = loc_by_id.get(r.location_id)
        if not l:
            continue
        out.append(
            LocationOut(
                name=l.name,
                state=l.state,
                country=l.country,
                zip_code=l.zip_code,
                latitude=l.latitude,
                longitude=l.longitude,
                timezone=l.timezone,
                slug=l.slug,
            )
        )
    return out


@router.post("/me/locations", response_model=LocationOut)
def save_location(
    payload: SaveLocationRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    loc = session.exec(select(Location).where(Location.slug == payload.location_slug)).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    existing = session.exec(
        select(SavedLocation).where(
            (SavedLocation.user_id == user.id) & (SavedLocation.location_id == loc.id)
        )
    ).first()
    if not existing:
        session.add(SavedLocation(user_id=user.id, location_id=loc.id))
        session.commit()

    return LocationOut(
        name=loc.name,
        state=loc.state,
        country=loc.country,
        zip_code=loc.zip_code,
        latitude=loc.latitude,
        longitude=loc.longitude,
        timezone=loc.timezone,
        slug=loc.slug,
    )


@router.delete("/me/locations/{slug}")
def remove_saved_location(
    slug: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    loc = session.exec(select(Location).where(Location.slug == slug)).first()
    if not loc:
        return {"status": "ok"}
    existing = session.exec(
        select(SavedLocation).where(
            (SavedLocation.user_id == user.id) & (SavedLocation.location_id == loc.id)
        )
    ).first()
    if existing:
        session.delete(existing)
        session.commit()
    return {"status": "ok"}

