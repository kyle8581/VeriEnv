from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.saved_search import SavedSearch
from app.models.user import User
from app.schemas import SavedSearchCreate, SavedSearchPublic

router = APIRouter()


def _to_public(s: SavedSearch) -> SavedSearchPublic:
    try:
        filters = json.loads(s.filters_json) if s.filters_json else {}
    except json.JSONDecodeError:
        filters = {}
    return SavedSearchPublic(
        id=s.id,
        user_id=s.user_id,
        name=s.name,
        query=s.query,
        filters=filters,
        created_at=s.created_at,
    )


@router.get("/saved-searches", response_model=list[SavedSearchPublic])
def list_saved_searches(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(SavedSearch)
        .filter(SavedSearch.user_id == current_user.id)
        .order_by(SavedSearch.created_at.desc())
        .all()
    )
    return [_to_public(i) for i in items]


@router.post("/saved-searches", response_model=SavedSearchPublic, status_code=status.HTTP_201_CREATED)
def create_saved_search(
    payload: SavedSearchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = SavedSearch(
        user_id=current_user.id,
        name=payload.name,
        query=payload.query,
        filters_json=json.dumps(payload.filters, separators=(",", ":"), sort_keys=True),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return _to_public(s)


@router.delete("/saved-searches/{saved_search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_search(
    saved_search_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = (
        db.query(SavedSearch)
        .filter(SavedSearch.id == saved_search_id, SavedSearch.user_id == current_user.id)
        .one_or_none()
    )
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")
    db.delete(s)
    db.commit()

