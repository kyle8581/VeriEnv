from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Artist, MarketplaceListing, Release, ReleaseArtist, User
from app.schemas.marketplace import ListingOut, ListingsPageOut


router = APIRouter(tags=["marketplace"])


def _release_header(db: Session, release_id: int) -> dict:
    r = db.get(Release, release_id)
    if not r:
        raise HTTPException(status_code=404, detail="Release not found")

    artist = db.execute(
        select(Artist.name)
        .join(ReleaseArtist, ReleaseArtist.artist_id == Artist.id)
        .where(ReleaseArtist.release_id == release_id)
        .where(ReleaseArtist.role == "Main")
        .order_by(ReleaseArtist.position.asc())
        .limit(1)
    ).scalar_one_or_none()

    return {"id": r.id, "title": r.title, "artist": artist, "cover_image_url": r.cover_image_url}


@router.get("/releases/{release_id}/listings", response_model=ListingsPageOut)
def listings(
    release_id: int,
    media_condition: str | None = None,
    sleeve_condition: str | None = None,
    ships_from: str | None = None,
    min_rating: float | None = None,
    sort: str = Query(default="price_asc", pattern="^(price_asc|price_desc|newest)$"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ListingsPageOut:
    header = _release_header(db, release_id)

    stmt = (
        select(MarketplaceListing, User)
        .join(User, User.id == MarketplaceListing.seller_user_id)
        .where(MarketplaceListing.release_id == release_id)
        .where(MarketplaceListing.status == "active")
    )
    if media_condition:
        stmt = stmt.where(MarketplaceListing.media_condition == media_condition)
    if sleeve_condition:
        stmt = stmt.where(MarketplaceListing.sleeve_condition == sleeve_condition)
    if ships_from:
        stmt = stmt.where(MarketplaceListing.ships_from == ships_from)
    if min_rating is not None:
        stmt = stmt.where(User.seller_rating >= min_rating)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = int(db.execute(count_stmt).scalar_one())

    if sort == "price_desc":
        stmt = stmt.order_by(MarketplaceListing.price_cents.desc(), MarketplaceListing.created_at.desc())
    elif sort == "newest":
        stmt = stmt.order_by(MarketplaceListing.created_at.desc(), MarketplaceListing.price_cents.asc())
    else:
        stmt = stmt.order_by(asc(MarketplaceListing.price_cents), MarketplaceListing.created_at.desc())

    rows = db.execute(stmt.offset(offset).limit(limit)).all()
    items = [
        ListingOut(
            id=listing.id,
            release_id=listing.release_id,
            seller={"username": user.username, "seller_rating": user.seller_rating, "location": user.location},
            media_condition=listing.media_condition,
            sleeve_condition=listing.sleeve_condition,
            price_cents=listing.price_cents,
            currency=listing.currency,
            ships_from=listing.ships_from,
            comments=listing.comments,
            quantity=listing.quantity,
            status=listing.status,
            created_at=listing.created_at,
        )
        for listing, user in rows
    ]

    return ListingsPageOut(release=header, total=total, items=items)

