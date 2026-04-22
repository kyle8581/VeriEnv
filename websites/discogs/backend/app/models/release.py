from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(240), index=True, nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    released_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    country: Mapped[str | None] = mapped_column(String(80), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    submitted_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationships
    tracks = relationship("Track", back_populates="release", cascade="all, delete-orphan", order_by="Track.position")
    artists = relationship("ReleaseArtist", back_populates="release", cascade="all, delete-orphan")
    labels = relationship("ReleaseLabel", back_populates="release", cascade="all, delete-orphan")
    genres = relationship("ReleaseGenre", back_populates="release", cascade="all, delete-orphan")
    styles = relationship("ReleaseStyle", back_populates="release", cascade="all, delete-orphan")
    formats = relationship("ReleaseFormat", back_populates="release", cascade="all, delete-orphan")

    listings = relationship("MarketplaceListing", back_populates="release", cascade="all, delete-orphan")


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"), index=True, nullable=False)

    position: Mapped[str] = mapped_column(String(30), nullable=False)  # e.g. "A1", "1"
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    release = relationship("Release", back_populates="tracks")


class ReleaseArtist(Base):
    __tablename__ = "release_artists"
    __table_args__ = (UniqueConstraint("release_id", "artist_id", "role", name="uq_release_artist_role"),)

    release_id: Mapped[int] = mapped_column(
        ForeignKey("releases.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    artist_id: Mapped[int] = mapped_column(
        ForeignKey("artists.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(80), primary_key=True, nullable=False)  # "Main", "Featuring", etc.
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    release = relationship("Release", back_populates="artists")
    artist = relationship("Artist")


class ReleaseLabel(Base):
    __tablename__ = "release_labels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"), index=True, nullable=False)
    label_id: Mapped[int] = mapped_column(ForeignKey("labels.id", ondelete="CASCADE"), index=True, nullable=False)
    catalog_no: Mapped[str | None] = mapped_column(String(60), nullable=True)

    release = relationship("Release", back_populates="labels")
    label = relationship("Label")


class ReleaseGenre(Base):
    __tablename__ = "release_genres"

    release_id: Mapped[int] = mapped_column(
        ForeignKey("releases.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    genre_id: Mapped[int] = mapped_column(
        ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )

    release = relationship("Release", back_populates="genres")
    genre = relationship("Genre")


class ReleaseStyle(Base):
    __tablename__ = "release_styles"

    release_id: Mapped[int] = mapped_column(
        ForeignKey("releases.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    style_id: Mapped[int] = mapped_column(
        ForeignKey("styles.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )

    release = relationship("Release", back_populates="styles")
    style = relationship("Style")


class ReleaseFormat(Base):
    __tablename__ = "release_formats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(40), nullable=False)  # Vinyl, CD, Cassette, File, etc.
    qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    text: Mapped[str | None] = mapped_column(String(200), nullable=True)  # e.g. "LP, Album, Reissue"

    release = relationship("Release", back_populates="formats")

