from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.db import get_session
from app.models.content import Article, Category, Deal, Photo


router = APIRouter(prefix="/content", tags=["content"])


class CategoryOut(BaseModel):
    name: str
    slug: str


class ArticleOut(BaseModel):
    title: str
    slug: str
    summary: str
    hero_image_url: str
    is_video: bool
    source: str
    reading_minutes: int
    published_at: datetime
    category: CategoryOut


class ArticleDetailOut(ArticleOut):
    body_md: str


class PhotoOut(BaseModel):
    id: str
    title: str
    image_url: str
    caption: str | None
    published_at: datetime


class DealOut(BaseModel):
    id: str
    title: str
    image_url: str
    provider: str
    price_usd: float | None
    badge: str | None
    cta_url: str


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(session: Session = Depends(get_session)):
    cats = session.exec(select(Category).order_by(Category.name.asc())).all()
    return [CategoryOut(name=c.name, slug=c.slug) for c in cats]


@router.get("/articles", response_model=list[ArticleOut])
def list_articles(
    session: Session = Depends(get_session),
    category: str | None = Query(default=None, description="Category slug"),
    kind: Literal["all", "video"] = Query(default="all"),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    stmt = select(Article).order_by(Article.published_at.desc()).offset(offset).limit(limit)
    if category:
        cat = session.exec(select(Category).where(Category.slug == category)).first()
        if not cat:
            return []
        stmt = stmt.where(Article.category_id == cat.id)
    if kind == "video":
        stmt = stmt.where(Article.is_video == True)  # noqa: E712

    articles = session.exec(stmt).all()
    if not articles:
        return []

    cat_ids = {a.category_id for a in articles}
    cats = session.exec(select(Category).where(Category.id.in_(cat_ids))).all()
    cat_by_id = {c.id: c for c in cats}

    out: list[ArticleOut] = []
    for a in articles:
        c = cat_by_id.get(a.category_id)
        out.append(
            ArticleOut(
                title=a.title,
                slug=a.slug,
                summary=a.summary,
                hero_image_url=a.hero_image_url,
                is_video=a.is_video,
                source=a.source,
                reading_minutes=a.reading_minutes,
                published_at=a.published_at,
                category=CategoryOut(name=c.name if c else "Unknown", slug=c.slug if c else "unknown"),
            )
        )
    return out


@router.get("/articles/{slug}", response_model=ArticleDetailOut)
def article_detail(slug: str, session: Session = Depends(get_session)):
    a = session.exec(select(Article).where(Article.slug == slug)).first()
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    c = session.get(Category, a.category_id)
    return ArticleDetailOut(
        title=a.title,
        slug=a.slug,
        summary=a.summary,
        body_md=a.body_md,
        hero_image_url=a.hero_image_url,
        is_video=a.is_video,
        source=a.source,
        reading_minutes=a.reading_minutes,
        published_at=a.published_at,
        category=CategoryOut(name=c.name if c else "Unknown", slug=c.slug if c else "unknown"),
    )


@router.get("/photos", response_model=list[PhotoOut])
def list_photos(
    session: Session = Depends(get_session),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    photos = session.exec(
        select(Photo).order_by(Photo.published_at.desc()).offset(offset).limit(limit)
    ).all()
    return [
        PhotoOut(
            id=str(p.id),
            title=p.title,
            image_url=p.image_url,
            caption=p.caption,
            published_at=p.published_at,
        )
        for p in photos
    ]


@router.get("/deals", response_model=list[DealOut])
def list_deals(
    session: Session = Depends(get_session),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    deals = session.exec(select(Deal).order_by(Deal.created_at.desc()).offset(offset).limit(limit)).all()
    return [
        DealOut(
            id=str(d.id),
            title=d.title,
            image_url=d.image_url,
            provider=d.provider,
            price_usd=d.price_usd,
            badge=d.badge,
            cta_url=d.cta_url,
        )
        for d in deals
    ]

