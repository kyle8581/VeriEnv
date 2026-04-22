from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(160), index=True)
    street: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(120), index=True)
    state: Mapped[str] = mapped_column(String(2), index=True)
    postal_code: Mapped[str] = mapped_column(String(20), index=True)

    latitude: Mapped[float] = mapped_column(Float, index=True)
    longitude: Mapped[float] = mapped_column(Float, index=True)

    min_price: Mapped[int] = mapped_column(Integer, index=True)
    max_price: Mapped[int] = mapped_column(Integer, index=True)
    min_beds: Mapped[int] = mapped_column(Integer, index=True)
    max_beds: Mapped[int] = mapped_column(Integer, index=True)

    property_type: Mapped[str] = mapped_column(String(32), index=True)  # apartment|house|condo|townhome
    move_in_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    description: Mapped[str] = mapped_column(Text)
    phone: Mapped[str] = mapped_column(String(32))
    management_name: Mapped[str] = mapped_column(String(120))
    specials: Mapped[str | None] = mapped_column(String(200), nullable=True)

    has_videos: Mapped[bool] = mapped_column(Boolean, default=False)
    has_virtual_tour: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    images = relationship("ListingImage", back_populates="listing", cascade="all, delete-orphan")
    amenities = relationship("Amenity", secondary="listing_amenities", back_populates="listings")


class ListingImage(Base):
    __tablename__ = "listing_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    listing = relationship("Listing", back_populates="images")

