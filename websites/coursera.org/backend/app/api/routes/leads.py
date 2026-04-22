from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.leads import ContactLead, EbookLead
from app.schemas.common import Message
from app.schemas.leads import ContactLeadCreate, EbookLeadCreate


router = APIRouter()


@router.post("/ebook", response_model=Message)
def submit_ebook_lead(payload: EbookLeadCreate, db: Session = Depends(get_db)) -> Message:
    lead = EbookLead(
        resource_slug=payload.resource_slug,
        first_name=payload.first_name,
        last_name=payload.last_name,
        job_title=payload.job_title,
        work_email=str(payload.work_email).lower(),
        work_phone=payload.work_phone,
        institution_name=payload.institution_name,
        primary_discipline=payload.primary_discipline,
        country=payload.country.upper(),
        consent_text=payload.consent_text,
    )
    db.add(lead)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Idempotent-ish: treat duplicate as success
        return Message(message="Already submitted")
    return Message(message="Submitted")


@router.post("/contact", response_model=Message)
def submit_contact_lead(payload: ContactLeadCreate, db: Session = Depends(get_db)) -> Message:
    lead = ContactLead(
        full_name=payload.full_name,
        email=str(payload.email).lower(),
        institution=payload.institution,
        message=payload.message,
    )
    db.add(lead)
    db.commit()
    return Message(message="Submitted")

