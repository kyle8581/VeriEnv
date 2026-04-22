from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class GenreOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None

    class Config:
        from_attributes = True


class StyleOut(BaseModel):
    id: int
    genre_id: int
    name: str
    slug: str

    class Config:
        from_attributes = True


class ReleaseCardOut(BaseModel):
    id: int
    title: str
    artist: str | None = None
    cover_image_url: str | None = None
    year: int | None = None


class TrackOut(BaseModel):
    position: str
    title: str
    duration_seconds: int | None = None


class ReleaseDetailOut(BaseModel):
    id: int
    title: str
    year: int | None = None
    released_date: date | None = None
    country: str | None = None
    notes: str | None = None
    cover_image_url: str | None = None

    artists: list[dict]  # {name, role}
    labels: list[dict]  # {name, catalog_no}
    genres: list[str]
    styles: list[str]
    formats: list[dict]  # {name, qty, text}
    tracks: list[TrackOut]

    have_count: int
    want_count: int
    for_sale_count: int
    lowest_price_cents: int | None = None
    currency: str = "USD"


class ChartBarOut(BaseModel):
    label: str
    value: int


class GenreStatsOut(BaseModel):
    releases_by_decade: list[ChartBarOut]
    top_submitters: list[ChartBarOut]


class GenreOverviewOut(BaseModel):
    genre: GenreOut
    styles: list[str]
    most_collected: list[ReleaseCardOut]
    early_releases: list[ReleaseCardOut]
    stats: GenreStatsOut
    most_sold_this_month: list[ReleaseCardOut]
    related_styles: list[str]


class HomeOut(BaseModel):
    hero_title: str
    hero_image_url: str
    hero_tiles: list[dict]
    banner: dict
    trending_releases: list[ReleaseCardOut]
    most_expensive_sold: list[dict]
    newly_added: list[ReleaseCardOut]

