from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EbookLead(Base):
    __tablename__ = "ebook_leads"
    __table_args__ = (UniqueConstraint("resource_slug", "work_email", name="uq_ebook_lead"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    resource_slug: Mapped[str] = mapped_column(String(260), index=True)
    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120))
    job_title: Mapped[str] = mapped_column(String(200))
    work_email: Mapped[str] = mapped_column(String(320), index=True)
    work_phone: Mapped[str] = mapped_column(String(60))
    institution_name: Mapped[str] = mapped_column(String(220))
    primary_discipline: Mapped[str] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(2))
    consent_text: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContactLead(Base):
    __tablename__ = "contact_leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(220))
    email: Mapped[str] = mapped_column(String(320), index=True)
    institution: Mapped[str] = mapped_column(String(220), default="")
    message: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

