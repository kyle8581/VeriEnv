from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Partner(Base):
    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True)
    logo_url: Mapped[str] = mapped_column(String(1000))
    kind: Mapped[str] = mapped_column(String(50), default="university")  # university|industry

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    courses: Mapped[list["Course"]] = relationship(back_populates="partner")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(220), index=True)
    slug: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    headline: Mapped[str] = mapped_column(String(280))
    description: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(50), default="Beginner")
    language: Mapped[str] = mapped_column(String(50), default="English")
    duration_hours: Mapped[int] = mapped_column(Integer, default=10)
    skills_csv: Mapped[str] = mapped_column(String(1000), default="")
    image_url: Mapped[str] = mapped_column(String(1000))

    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id"))
    partner: Mapped[Partner] = relationship(back_populates="courses")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(50), default="ebook")  # ebook|event|article
    title: Mapped[str] = mapped_column(String(240), index=True)
    slug: Mapped[str] = mapped_column(String(260), unique=True, index=True)
    summary: Mapped[str] = mapped_column(String(500))
    body_md: Mapped[str] = mapped_column(Text, default="")
    hero_image_url: Mapped[str] = mapped_column(String(1000))
    cta_label: Mapped[str] = mapped_column(String(100), default="Explore")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

