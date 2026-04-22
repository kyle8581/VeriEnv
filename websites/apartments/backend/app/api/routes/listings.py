from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.amenity import Amenity
from app.models.listing import Listing
from app.schemas import ListingPublic, ListingSearchResponse

router = APIRouter()


def _parse_query(q: str) -> tuple[str | None, str | None, str | None]:
    """
    Returns (city, state, postal_code) best-effort from a freeform query.
    Examples:
      - "Boston, MA" -> ("Boston", "MA", None)
      - "43220" -> (None, None, "43220")
    """
    raw = (q or "").strip()
    if not raw:
        return None, None, None
    if raw.replace("-", "").isdigit():
        return None, None, raw
    if "," in raw:
        city, state = [p.strip() for p in raw.split(",", 1)]
        return city or None, (state.upper()[:2] if state else None), None
    return raw, None, None


@router.get("/listings", response_model=ListingSearchResponse)
def search_listings(
    q: str = Query(default="", max_length=120),
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    min_beds: int | None = Query(default=None, ge=0),
    max_beds: int | None = Query(default=None, ge=0),
    property_type: str | None = Query(default=None, max_length=32),
    move_in_date: date | None = None,
    has_videos: bool | None = None,
    has_virtual_tour: bool | None = None,
    specials_only: bool | None = None,
    amenity: str | None = Query(default=None, max_length=80),
    sort: str = Query(default="newest", max_length=40),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    city, state, postal = _parse_query(q)

    filters = []
    if city:
        filters.append(Listing.city.ilike(f"%{city}%"))
    if state:
        filters.append(Listing.state == state)
    if postal:
        filters.append(Listing.postal_code.ilike(f"%{postal}%"))
    if min_price is not None:
        filters.append(Listing.max_price >= min_price)
    if max_price is not None:
        filters.append(Listing.min_price <= max_price)
    if min_beds is not None:
        filters.append(Listing.max_beds >= min_beds)
    if max_beds is not None:
        filters.append(Listing.min_beds <= max_beds)
    if property_type:
        filters.append(Listing.property_type == property_type)
    if move_in_date:
        filters.append(or_(Listing.move_in_date.is_(None), Listing.move_in_date <= move_in_date))
    if has_videos is True:
        filters.append(Listing.has_videos.is_(True))
    if has_virtual_tour is True:
        filters.append(Listing.has_virtual_tour.is_(True))
    if specials_only is True:
        filters.append(Listing.specials.is_not(None))
    if amenity:
        filters.append(Listing.amenities.any(Amenity.name == amenity))

    base = db.query(Listing)
    if filters:
        base = base.filter(and_(*filters))

    total = base.count()

    if sort == "price_asc":
        order_by = Listing.min_price.asc()
    elif sort == "price_desc":
        order_by = Listing.max_price.desc()
    else:
        order_by = Listing.created_at.desc()

    items = (
        base.options(selectinload(Listing.images), selectinload(Listing.amenities))
        .order_by(order_by)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return ListingSearchResponse(total=total, items=items)


@router.get("/listings/{listing_id}", response_model=ListingPublic)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = (
        db.query(Listing)
        .options(selectinload(Listing.images), selectinload(Listing.amenities))
        .filter(Listing.id == listing_id)
        .one_or_none()
    )
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing

