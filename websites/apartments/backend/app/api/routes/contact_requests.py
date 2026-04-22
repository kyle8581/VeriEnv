from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.contact_request import ContactRequest
from app.models.listing import Listing
from app.models.user import User
from app.schemas import ContactRequestCreate, ContactRequestPublic

router = APIRouter()

# Optional auth: if provided, we associate the request with a user.
_optional_oauth = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def _get_user_from_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        subject = payload.get("sub")
        if not subject:
            return None
    except JWTError:
        return None
    return db.query(User).filter(User.email == subject).one_or_none()


@router.post("/contact-requests", response_model=ContactRequestPublic, status_code=status.HTTP_201_CREATED)
def create_contact_request(
    payload: ContactRequestCreate,
    db: Session = Depends(get_db),
    token: str | None = Depends(_optional_oauth),
):
    listing = db.query(Listing).filter(Listing.id == payload.listing_id).one_or_none()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    user = _get_user_from_token(db, token)
    cr = ContactRequest(
        listing_id=payload.listing_id,
        user_id=user.id if user else None,
        contact_email=str(payload.contact_email),
        contact_name=payload.contact_name,
        message=payload.message,
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)
    return cr

