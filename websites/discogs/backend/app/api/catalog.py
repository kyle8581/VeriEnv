from __future__ import annotations

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import (
    Artist,
    CollectionItem,
    Genre,
    Label,
    MarketplaceListing,
    Order,
    OrderItem,
    Release,
    ReleaseArtist,
    ReleaseFormat,
    ReleaseGenre,
    ReleaseLabel,
    ReleaseStyle,
    Style,
    Track,
    WantlistItem,
)
from app.schemas.catalog import (
    ChartBarOut,
    GenreOut,
    GenreOverviewOut,
    GenreStatsOut,
    HomeOut,
    ReleaseCardOut,
    ReleaseDetailOut,
    TrackOut,
)


router = APIRouter(tags=["catalog"])


def _main_artist_subq() -> Select:
    ra = ReleaseArtist
    a = Artist
    return (
        select(ra.release_id.label("release_id"), a.name.label("artist_name"))
        .join(a, a.id == ra.artist_id)
        .where(ra.role == "Main")
        .order_by(ra.position.asc())
        .subquery()
    )


def _release_card_rows(db: Session, release_ids: list[int]) -> list[ReleaseCardOut]:
    if not release_ids:
        return []

    main_artist = _main_artist_subq()
    rows = (
        db.execute(
            select(Release.id, Release.title, Release.cover_image_url, Release.year, main_artist.c.artist_name)
            .join(main_artist, main_artist.c.release_id == Release.id, isouter=True)
            .where(Release.id.in_(release_ids))
        )
        .mappings()
        .all()
    )

    by_id = {
        r["id"]: ReleaseCardOut(
            id=r["id"],
            title=r["title"],
            artist=r.get("artist_name"),
            cover_image_url=r.get("cover_image_url"),
            year=r.get("year"),
        )
        for r in rows
    }
    return [by_id[i] for i in release_ids if i in by_id]


@router.get("/home", response_model=HomeOut)
def home(db: Session = Depends(get_db)) -> HomeOut:
    main_artist = _main_artist_subq()

    # Banner targets seeded DSOTM if present
    banner_release = db.scalar(select(Release).where(Release.title == "The Dark Side Of The Moon"))
    banner = {
        "title": "PINK FLOYD / THE DARK SIDE OF THE MOON",
        "subtitle": "OUT NOW",
        "image_url": "https://images.unsplash.com/photo-1485579149621-3123dd979885?auto=format&fit=crop&w=1400&q=80",
        "release_id": banner_release.id if banner_release else None,
    }

    # Trending: most wanted
    trending_ids = [
        r[0]
        for r in db.execute(
            select(WantlistItem.release_id, func.count().label("c"))
            .group_by(WantlistItem.release_id)
            .order_by(desc("c"))
            .limit(6)
        ).all()
    ]
    trending = _release_card_rows(db, trending_ids)

    # Newly added
    newly_added_rows = (
        db.execute(
            select(Release.id)
            .order_by(Release.created_at.desc())
            .limit(8)
        )
        .all()
    )
    newly_added_ids = [r[0] for r in newly_added_rows]
    newly_added = _release_card_rows(db, newly_added_ids)

    # Most expensive sold this month (by order item price)
    since = datetime.now(timezone.utc) - timedelta(days=31)
    expensive_rows = (
        db.execute(
            select(OrderItem.price_cents, Release.id, Release.title, Release.cover_image_url, main_artist.c.artist_name)
            .join(Order, Order.id == OrderItem.order_id)
            .join(MarketplaceListing, MarketplaceListing.id == OrderItem.listing_id, isouter=True)
            .join(Release, Release.id == MarketplaceListing.release_id, isouter=True)
            .join(main_artist, main_artist.c.release_id == Release.id, isouter=True)
            .where(Order.created_at >= since)
            .where(Release.id.is_not(None))
            .order_by(OrderItem.price_cents.desc())
            .limit(6)
        )
        .mappings()
        .all()
    )
    most_expensive_sold = [
        {
            "release": ReleaseCardOut(
                id=r["id"],
                title=r["title"],
                artist=r.get("artist_name"),
                cover_image_url=r.get("cover_image_url"),
            ).model_dump(),
            "price_cents": r["price_cents"],
            "currency": "USD",
        }
        for r in expensive_rows
    ]

    return HomeOut(
        hero_title="10 Essential Synth-Pop Albums",
        hero_image_url="https://images.unsplash.com/photo-1511379938547-c1f69419868d?auto=format&fit=crop&w=1600&q=80",
        hero_tiles=[
            {
                "title": "Explore new releases on Discogs",
                "subtitle": "Weekly discovery from the community",
                "image_url": "https://images.unsplash.com/photo-1524678606370-a47ad25cb82a?auto=format&fit=crop&w=600&q=80",
            },
            {
                "title": "All-Ages Album of the Week",
                "subtitle": "Handpicked spotlight",
                "image_url": "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?auto=format&fit=crop&w=600&q=80",
            },
            {
                "title": "Start selling on Discogs",
                "subtitle": "List items and reach collectors",
                "image_url": "https://images.unsplash.com/photo-1514924013411-cbf25faa35bb?auto=format&fit=crop&w=600&q=80",
            },
        ],
        banner=banner,
        trending_releases=trending,
        most_expensive_sold=most_expensive_sold,
        newly_added=newly_added,
    )


@router.get("/genres", response_model=list[GenreOut])
def list_genres(db: Session = Depends(get_db)) -> list[GenreOut]:
    return list(db.scalars(select(Genre).order_by(Genre.name.asc())).all())


@router.get("/genres/{slug}/overview", response_model=GenreOverviewOut)
def genre_overview(slug: str, db: Session = Depends(get_db)) -> GenreOverviewOut:
    genre = db.scalar(select(Genre).where(Genre.slug == slug))
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")

    # style names
    style_names = [s.name for s in db.scalars(select(Style).where(Style.genre_id == genre.id).order_by(Style.name)).all()]

    # most collected in this genre
    most_collected_ids = [
        r[0]
        for r in db.execute(
            select(CollectionItem.release_id, func.count().label("c"))
            .join(ReleaseGenre, ReleaseGenre.release_id == CollectionItem.release_id)
            .where(ReleaseGenre.genre_id == genre.id)
            .group_by(CollectionItem.release_id)
            .order_by(desc("c"))
            .limit(6)
        ).all()
    ]

    # early releases
    early_ids = [
        r[0]
        for r in db.execute(
            select(Release.id)
            .join(ReleaseGenre, ReleaseGenre.release_id == Release.id)
            .where(ReleaseGenre.genre_id == genre.id)
            .where(Release.year.is_not(None))
            .order_by(Release.year.asc())
            .limit(6)
        ).all()
    ]

    # stats: releases by decade, top submitters
    decade_rows = (
        db.execute(
            select(((Release.year / 10) * 10).label("decade"), func.count().label("c"))
            .join(ReleaseGenre, ReleaseGenre.release_id == Release.id)
            .where(ReleaseGenre.genre_id == genre.id)
            .where(Release.year.is_not(None))
            .group_by("decade")
            .order_by("decade")
        )
        .all()
    )
    releases_by_decade = [ChartBarOut(label=f"{int(d)}s", value=int(c)) for d, c in decade_rows]

    submit_rows = (
        db.execute(
            select(Release.submitted_by_user_id, func.count().label("c"))
            .join(ReleaseGenre, ReleaseGenre.release_id == Release.id)
            .where(ReleaseGenre.genre_id == genre.id)
            .where(Release.submitted_by_user_id.is_not(None))
            .group_by(Release.submitted_by_user_id)
            .order_by(desc("c"))
            .limit(6)
        )
        .all()
    )
    # For the chart, emit opaque contributor labels (seed uses many)
    top_submitters = [ChartBarOut(label=str(uid)[:8], value=int(c)) for uid, c in submit_rows]

    # most sold this month
    since = datetime.now(timezone.utc) - timedelta(days=31)
    sold_ids = [
        r[0]
        for r in db.execute(
            select(MarketplaceListing.release_id, func.count().label("c"))
            .join(OrderItem, OrderItem.listing_id == MarketplaceListing.id)
            .join(Order, Order.id == OrderItem.order_id)
            .join(ReleaseGenre, ReleaseGenre.release_id == MarketplaceListing.release_id)
            .where(Order.created_at >= since)
            .where(ReleaseGenre.genre_id == genre.id)
            .group_by(MarketplaceListing.release_id)
            .order_by(desc("c"))
            .limit(7)
        ).all()
    ]

    return GenreOverviewOut(
        genre=GenreOut.model_validate(genre),
        styles=style_names,
        most_collected=_release_card_rows(db, most_collected_ids),
        early_releases=_release_card_rows(db, early_ids),
        stats=GenreStatsOut(releases_by_decade=releases_by_decade, top_submitters=top_submitters),
        most_sold_this_month=_release_card_rows(db, sold_ids),
        related_styles=style_names[:12],
    )


@router.get("/releases/{release_id}", response_model=ReleaseDetailOut)
def release_detail(release_id: int, db: Session = Depends(get_db)) -> ReleaseDetailOut:
    r = db.get(Release, release_id)
    if not r:
        raise HTTPException(status_code=404, detail="Release not found")

    # Joined metadata
    artists = (
        db.execute(
            select(Artist.name, ReleaseArtist.role)
            .join(ReleaseArtist, ReleaseArtist.artist_id == Artist.id)
            .where(ReleaseArtist.release_id == r.id)
            .order_by(ReleaseArtist.position.asc())
        )
        .all()
    )
    label_rows = (
        db.execute(
            select(ReleaseLabel.catalog_no, Label.name)
            .join(Label, Label.id == ReleaseLabel.label_id)
            .where(ReleaseLabel.release_id == r.id)
        )
        .all()
    )

    genres = (
        db.execute(
            select(Genre.name)
            .join(ReleaseGenre, ReleaseGenre.genre_id == Genre.id)
            .where(ReleaseGenre.release_id == r.id)
        )
        .all()
    )
    styles = (
        db.execute(
            select(Style.name)
            .join(ReleaseStyle, ReleaseStyle.style_id == Style.id)
            .where(ReleaseStyle.release_id == r.id)
        )
        .all()
    )
    formats = db.scalars(select(ReleaseFormat).where(ReleaseFormat.release_id == r.id)).all()
    tracks = db.scalars(select(Track).where(Track.release_id == r.id).order_by(Track.position)).all()

    have_count = db.scalar(select(func.count()).select_from(CollectionItem).where(CollectionItem.release_id == r.id)) or 0
    want_count = db.scalar(select(func.count()).select_from(WantlistItem).where(WantlistItem.release_id == r.id)) or 0

    active_listings = db.execute(
        select(func.count(), func.min(MarketplaceListing.price_cents))
        .where(MarketplaceListing.release_id == r.id)
        .where(MarketplaceListing.status == "active")
    ).one()
    for_sale_count = int(active_listings[0] or 0)
    lowest_price = active_listings[1]

    return ReleaseDetailOut(
        id=r.id,
        title=r.title,
        year=r.year,
        released_date=r.released_date,
        country=r.country,
        notes=r.notes,
        cover_image_url=r.cover_image_url,
        artists=[{"name": n, "role": role} for n, role in artists],
        labels=[{"name": name, "catalog_no": cat} for cat, name in label_rows],
        genres=[g[0] for g in genres],
        styles=[s[0] for s in styles],
        formats=[{"name": f.name, "qty": f.qty, "text": f.text} for f in formats],
        tracks=[TrackOut(position=t.position, title=t.title, duration_seconds=t.duration_seconds) for t in tracks],
        have_count=have_count,
        want_count=want_count,
        for_sale_count=for_sale_count,
        lowest_price_cents=lowest_price,
        currency="USD",
    )


@router.get("/search", response_model=list[ReleaseCardOut])
def search(q: str, db: Session = Depends(get_db)) -> list[ReleaseCardOut]:
    q = q.strip()
    if not q:
        return []
    main_artist = _main_artist_subq()
    rows = (
        db.execute(
            select(Release.id, Release.title, Release.cover_image_url, Release.year, main_artist.c.artist_name)
            .join(main_artist, main_artist.c.release_id == Release.id, isouter=True)
            .where(Release.title.ilike(f"%{q}%") | main_artist.c.artist_name.ilike(f"%{q}%"))
            .order_by(Release.year.desc().nullslast(), Release.title.asc())
            .limit(30)
        )
        .mappings()
        .all()
    )
    return [
        ReleaseCardOut(
            id=r["id"],
            title=r["title"],
            artist=r.get("artist_name"),
            cover_image_url=r.get("cover_image_url"),
            year=r.get("year"),
        )
        for r in rows
    ]

