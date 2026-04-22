from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import (
    Artist,
    CartItem,
    CollectionItem,
    MarketplaceListing,
    Order,
    OrderItem,
    Release,
    ReleaseArtist,
    User,
    WantlistItem,
)
from app.schemas.cart import CartAddIn, CartItemOut, CartListingOut, CartOut
from app.schemas.catalog import ReleaseCardOut
from app.schemas.order import OrderOut
from app.schemas.sell import ListingCreateIn, ListingUpdateIn


router = APIRouter(tags=["account"])


def _main_artist_name(db: Session, release_id: int) -> str | None:
    return db.execute(
        select(Artist.name)
        .join(ReleaseArtist, ReleaseArtist.artist_id == Artist.id)
        .where(ReleaseArtist.release_id == release_id)
        .where(ReleaseArtist.role == "Main")
        .order_by(ReleaseArtist.position.asc())
        .limit(1)
    ).scalar_one_or_none()


@router.get("/me/collection", response_model=list[ReleaseCardOut])
def my_collection(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[ReleaseCardOut]:
    ids = [r[0] for r in db.execute(select(CollectionItem.release_id).where(CollectionItem.user_id == user.id)).all()]
    if not ids:
        return []
    rows = (
        db.execute(select(Release.id, Release.title, Release.cover_image_url, Release.year).where(Release.id.in_(ids)))
        .mappings()
        .all()
    )
    by_id = {r["id"]: r for r in rows}
    return [
        ReleaseCardOut(
            id=i,
            title=by_id[i]["title"],
            artist=_main_artist_name(db, i),
            cover_image_url=by_id[i]["cover_image_url"],
            year=by_id[i]["year"],
        )
        for i in ids
        if i in by_id
    ]


@router.post("/me/collection/{release_id}")
def add_to_collection(release_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    if not db.get(Release, release_id):
        raise HTTPException(status_code=404, detail="Release not found")
    exists = db.get(CollectionItem, {"user_id": user.id, "release_id": release_id})
    if exists:
        return {"ok": True}
    db.add(CollectionItem(user_id=user.id, release_id=release_id))
    db.commit()
    return {"ok": True}


@router.delete("/me/collection/{release_id}")
def remove_from_collection(release_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    db.execute(delete(CollectionItem).where(CollectionItem.user_id == user.id, CollectionItem.release_id == release_id))
    db.commit()
    return {"ok": True}


@router.get("/me/wantlist", response_model=list[ReleaseCardOut])
def my_wantlist(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[ReleaseCardOut]:
    ids = [r[0] for r in db.execute(select(WantlistItem.release_id).where(WantlistItem.user_id == user.id)).all()]
    if not ids:
        return []
    rows = (
        db.execute(select(Release.id, Release.title, Release.cover_image_url, Release.year).where(Release.id.in_(ids)))
        .mappings()
        .all()
    )
    by_id = {r["id"]: r for r in rows}
    return [
        ReleaseCardOut(
            id=i,
            title=by_id[i]["title"],
            artist=_main_artist_name(db, i),
            cover_image_url=by_id[i]["cover_image_url"],
            year=by_id[i]["year"],
        )
        for i in ids
        if i in by_id
    ]


@router.post("/me/wantlist/{release_id}")
def add_to_wantlist(release_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    if not db.get(Release, release_id):
        raise HTTPException(status_code=404, detail="Release not found")
    exists = db.get(WantlistItem, {"user_id": user.id, "release_id": release_id})
    if exists:
        return {"ok": True}
    db.add(WantlistItem(user_id=user.id, release_id=release_id))
    db.commit()
    return {"ok": True}


@router.delete("/me/wantlist/{release_id}")
def remove_from_wantlist(release_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    db.execute(delete(WantlistItem).where(WantlistItem.user_id == user.id, WantlistItem.release_id == release_id))
    db.commit()
    return {"ok": True}


@router.get("/cart", response_model=CartOut)
def cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CartOut:
    rows = (
        db.execute(
            select(CartItem, MarketplaceListing, Release, User.username)
            .join(MarketplaceListing, MarketplaceListing.id == CartItem.listing_id)
            .join(Release, Release.id == MarketplaceListing.release_id)
            .join(User, User.id == MarketplaceListing.seller_user_id)
            .where(CartItem.user_id == user.id)
            .order_by(CartItem.created_at.desc())
        )
        .all()
    )
    items: list[CartItemOut] = []
    total = 0
    for ci, listing, rel, seller_username in rows:
        total += listing.price_cents * ci.quantity
        items.append(
            CartItemOut(
                id=ci.id,
                quantity=ci.quantity,
                listing=CartListingOut(
                    listing_id=listing.id,
                    release_id=rel.id,
                    release_title=rel.title,
                    seller_username=seller_username,
                    price_cents=listing.price_cents,
                    currency=listing.currency,
                ),
            )
        )
    return CartOut(items=items, total_cents=total, currency="USD")


@router.post("/cart/items", status_code=201, response_model=CartOut)
def cart_add(
    payload: CartAddIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> CartOut:
    listing = db.get(MarketplaceListing, payload.listing_id)
    if not listing or listing.status != "active":
        raise HTTPException(status_code=404, detail="Listing not found")
    if payload.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be >= 1")

    existing = db.scalar(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.listing_id == payload.listing_id)
    )
    if existing:
        existing.quantity = min(existing.quantity + payload.quantity, 99)
    else:
        db.add(CartItem(user_id=user.id, listing_id=payload.listing_id, quantity=payload.quantity))
    db.commit()
    return cart(db=db, user=user)


@router.delete("/cart/items/{cart_item_id}")
def cart_remove(cart_item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    db.execute(delete(CartItem).where(CartItem.user_id == user.id, CartItem.id == cart_item_id))
    db.commit()
    return {"ok": True}


@router.post("/checkout", response_model=OrderOut)
def checkout(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> OrderOut:
    items = db.scalars(select(CartItem).where(CartItem.user_id == user.id)).all()
    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    listing_ids = [i.listing_id for i in items]
    listings = db.scalars(select(MarketplaceListing).where(MarketplaceListing.id.in_(listing_ids))).all()
    listing_by_id = {l.id: l for l in listings}

    total = 0
    order = Order(buyer_user_id=user.id, total_cents=0, currency="USD", status="paid")
    db.add(order)
    db.flush()

    for ci in items:
        listing = listing_by_id.get(ci.listing_id)
        if not listing or listing.status != "active":
            raise HTTPException(status_code=400, detail="A listing in your cart is no longer available")
        total += listing.price_cents * ci.quantity
        db.add(OrderItem(order_id=order.id, listing_id=listing.id, price_cents=listing.price_cents, quantity=ci.quantity))
        listing.status = "sold"

    order.total_cents = total

    # clear cart
    db.execute(delete(CartItem).where(CartItem.user_id == user.id))
    db.commit()
    db.refresh(order)

    out_items = [
        {"listing_id": it.listing_id, "price_cents": it.price_cents, "quantity": it.quantity} for it in order.items
    ]
    return OrderOut(
        id=order.id,
        status=order.status,
        total_cents=order.total_cents,
        currency=order.currency,
        created_at=order.created_at,
        items=out_items,  # pydantic will coerce
    )


@router.get("/me/listings")
def my_listings(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    rows = (
        db.execute(
            select(MarketplaceListing, Release.title)
            .join(Release, Release.id == MarketplaceListing.release_id)
            .where(MarketplaceListing.seller_user_id == user.id)
            .order_by(MarketplaceListing.created_at.desc())
        )
        .all()
    )
    return {
        "items": [
            {
                "id": l.id,
                "release_id": l.release_id,
                "release_title": title,
                "media_condition": l.media_condition,
                "sleeve_condition": l.sleeve_condition,
                "price_cents": l.price_cents,
                "currency": l.currency,
                "ships_from": l.ships_from,
                "quantity": l.quantity,
                "status": l.status,
                "created_at": l.created_at,
            }
            for l, title in rows
        ]
    }


@router.post("/me/listings", status_code=201)
def create_listing(
    payload: ListingCreateIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    if not db.get(Release, payload.release_id):
        raise HTTPException(status_code=404, detail="Release not found")

    listing = MarketplaceListing(
        release_id=payload.release_id,
        seller_user_id=user.id,
        media_condition=payload.media_condition,
        sleeve_condition=payload.sleeve_condition,
        price_cents=payload.price_cents,
        currency=payload.currency,
        ships_from=payload.ships_from,
        comments=payload.comments,
        quantity=payload.quantity,
        status="active",
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return {"id": listing.id}


@router.patch("/me/listings/{listing_id}")
def update_listing(
    listing_id: int, payload: ListingUpdateIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    listing = db.get(MarketplaceListing, listing_id)
    if not listing or listing.seller_user_id != user.id:
        raise HTTPException(status_code=404, detail="Listing not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(listing, field, value)
    db.commit()
    return {"ok": True}


@router.delete("/me/listings/{listing_id}")
def delete_listing(listing_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    listing = db.get(MarketplaceListing, listing_id)
    if not listing or listing.seller_user_id != user.id:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.status = "inactive"
    db.commit()
    return {"ok": True}

