from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.favorite import Favorite
from app.models.listing import Listing
from app.models.user import User
from app.schemas import ListingPublic

router = APIRouter()


@router.get("/favorites", response_model=list[ListingPublic])
def list_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    favs = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    listing_ids = [f.listing_id for f in favs]
    if not listing_ids:
        return []
    return (
        db.query(Listing)
        .options(selectinload(Listing.images), selectinload(Listing.amenities))
        .filter(Listing.id.in_(listing_ids))
        .all()
    )


@router.post("/favorites/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_favorite(listing_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exists = db.query(Listing.id).filter(Listing.id == listing_id).one_or_none()
    if not exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    already = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.listing_id == listing_id)
        .one_or_none()
    )
    if already:
        return

    db.add(Favorite(user_id=current_user.id, listing_id=listing_id))
    db.commit()


@router.delete("/favorites/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(listing_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fav = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.listing_id == listing_id)
        .one_or_none()
    )
    if not fav:
        return
    db.delete(fav)
    db.commit()

