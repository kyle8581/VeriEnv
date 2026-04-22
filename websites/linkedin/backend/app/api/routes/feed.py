from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import (
    CommentCreateRequest,
    CommentOut,
    PaginatedPosts,
    PostCreateRequest,
    PostOut,
    UserPublic,
)
from app.db.models import Comment, Post, Reaction, ReactionType, User
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


def _post_out(db: Session, *, post: Post, viewer_id: str) -> PostOut:
    reactions_count = db.scalar(select(func.count()).select_from(Reaction).where(Reaction.post_id == post.id)) or 0
    comments_count = db.scalar(select(func.count()).select_from(Comment).where(Comment.post_id == post.id)) or 0
    viewer_has_liked = (
        db.scalar(
            select(func.count())
            .select_from(Reaction)
            .where(Reaction.post_id == post.id, Reaction.user_id == viewer_id, Reaction.type == ReactionType.like)
        )
        or 0
    ) > 0
    return PostOut(
        id=post.id,
        author=_user_public(post.author),
        body=post.body,
        image_url=post.image_url,
        created_at=post.created_at,
        reactions_count=reactions_count,
        comments_count=comments_count,
        viewer_has_liked=viewer_has_liked,
    )


@router.get("", response_model=PaginatedPosts)
def get_feed(
    limit: int = Query(default=10, ge=1, le=30),
    cursor: datetime | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedPosts:
    stmt = select(Post).order_by(desc(Post.created_at), desc(Post.id)).limit(limit + 1)
    if cursor is not None:
        stmt = stmt.where(Post.created_at < cursor)

    posts = list(db.scalars(stmt).all())
    next_cursor: str | None = None
    if len(posts) > limit:
        last = posts[limit - 1]
        next_cursor = last.created_at.isoformat()
        posts = posts[:limit]

    # Eager-load authors (SQLite + small dataset: acceptable)
    for p in posts:
        _ = p.author

    return PaginatedPosts(items=[_post_out(db, post=p, viewer_id=user.id) for p in posts], next_cursor=next_cursor)


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostOut:
    post = Post(author_id=user.id, body=payload.body, image_url=payload.image_url)
    db.add(post)
    db.commit()
    db.refresh(post)
    post.author = user
    return _post_out(db, post=post, viewer_id=user.id)


@router.post("/posts/{post_id}/like")
def toggle_like(
    post_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    post = db.scalar(select(Post).where(Post.id == post_id))
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    existing = db.scalar(select(Reaction).where(Reaction.post_id == post_id, Reaction.user_id == user.id))
    if existing is not None:
        db.delete(existing)
        db.commit()
        return {"liked": False}

    reaction = Reaction(post_id=post_id, user_id=user.id, type=ReactionType.like)
    db.add(reaction)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    return {"liked": True}


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
def list_comments(
    post_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CommentOut]:
    _ = user  # auth-only
    stmt = (
        select(Comment, User)
        .join(User, User.id == Comment.author_id)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
    )
    out: list[CommentOut] = []
    for c, author in db.execute(stmt).all():
        out.append(CommentOut(id=c.id, author=_user_public(author), body=c.body, created_at=c.created_at))
    return out


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: str,
    payload: CommentCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommentOut:
    post = db.scalar(select(Post).where(Post.id == post_id))
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    c = Comment(post_id=post_id, author_id=user.id, body=payload.body)
    db.add(c)
    db.commit()
    db.refresh(c)
    return CommentOut(id=c.id, author=_user_public(user), body=c.body, created_at=c.created_at)

