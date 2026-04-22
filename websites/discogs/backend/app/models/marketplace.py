from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"), index=True, nullable=False)
    seller_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    media_condition: Mapped[str] = mapped_column(String(40), nullable=False)  # Mint, NM, VG+, VG, G, etc.
    sleeve_condition: Mapped[str] = mapped_column(String(40), nullable=False)

    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    ships_from: Mapped[str] = mapped_column(String(80), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active|sold|inactive

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    release = relationship("Release", back_populates="listings")
    seller = relationship("User", back_populates="listings")

