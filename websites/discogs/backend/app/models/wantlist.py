from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WantlistItem(Base):
    __tablename__ = "wantlist_items"
    __table_args__ = (UniqueConstraint("user_id", "release_id", name="uq_wantlist_user_release"),)

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    release_id: Mapped[int] = mapped_column(
        ForeignKey("releases.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="wantlist_items")
    release = relationship("Release")

