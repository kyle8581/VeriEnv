from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import (
    PeopleSearchItem,
    PeopleSearchResponse,
    PostSearchItem,
    PostSearchResponse,
    TypeaheadResponse,
    UserPublic,
)
from app.db.models import Post, SearchSuggestion, User
from app.db.session import get_db

router = APIRouter()


def _user_public(u: User) -> UserPublic:
    return UserPublic(
        id=u.id,
        email=None,
        first_name=u.first_name,
        last_name=u.last_name,
        headline=u.headline,
        location=u.location,
        avatar_url=u.avatar_url,
    )


@router.get("/typeahead", response_model=TypeaheadResponse)
def typeahead(
    q: str = Query(min_length=1, max_length=120),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TypeaheadResponse:
    q_norm = q.strip().lower()
    if not q_norm:
        return TypeaheadResponse(suggestions=[])

    stmt = (
        select(SearchSuggestion.query)
        .where(func.lower(SearchSuggestion.query).like(f"{q_norm}%"))
        .order_by(desc(SearchSuggestion.popularity))
        .limit(8)
    )
    suggestions = [row[0] for row in db.execute(stmt).all()]

    # Fallback (keeps UI functional even with minimal seed data)
    if not suggestions:
        suggestions = [
            q_norm,
            f"{q_norm} jobs",
            f"{q_norm} intern",
            f"{q_norm} salary",
            q_norm.replace(" jobs", ""),
        ]
    return TypeaheadResponse(suggestions=suggestions[:8])


@router.get("/people", response_model=PeopleSearchResponse)
def search_people(
    q: str = Query(min_length=1, max_length=120),
    limit: int = Query(default=10, ge=1, le=30),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PeopleSearchResponse:
    q_norm = q.strip().lower()
    stmt = select(User).where(
        or_(
            func.lower(User.first_name).like(f"%{q_norm}%"),
            func.lower(User.last_name).like(f"%{q_norm}%"),
            func.lower(User.headline).like(f"%{q_norm}%"),
        )
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    users = list(db.scalars(stmt.order_by(User.last_name.asc()).limit(limit)).all())
    items = [
        PeopleSearchItem(
            id=u.id,
            first_name=u.first_name,
            last_name=u.last_name,
            headline=u.headline,
            location=u.location,
            avatar_url=u.avatar_url,
        )
        for u in users
    ]
    return PeopleSearchResponse(total=total, items=items)


@router.get("/posts", response_model=PostSearchResponse)
def search_posts(
    q: str = Query(min_length=1, max_length=120),
    limit: int = Query(default=10, ge=1, le=30),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostSearchResponse:
    q_norm = q.strip().lower()
    stmt = select(Post).where(func.lower(Post.body).like(f"%{q_norm}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    posts = list(db.scalars(stmt.order_by(desc(Post.created_at)).limit(limit)).all())
    # Eager load authors
    for p in posts:
        _ = p.author
    items = [
        PostSearchItem(id=p.id, author=_user_public(p.author), body=p.body, image_url=p.image_url, created_at=p.created_at)
        for p in posts
    ]
    return PostSearchResponse(total=total, items=items)

