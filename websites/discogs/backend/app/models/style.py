from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Style(Base):
    __tablename__ = "styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(80), index=True, nullable=False)

    genre = relationship("Genre", back_populates="styles")

