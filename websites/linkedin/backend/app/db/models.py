from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class WorkMode(str, enum.Enum):
    onsite = "onsite"
    hybrid = "hybrid"
    remote = "remote"


class EmploymentType(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    internship = "internship"


class ExperienceLevel(str, enum.Enum):
    internship = "internship"
    entry = "entry"
    mid = "mid"
    senior = "senior"
    director = "director"
    executive = "executive"


class ReactionType(str, enum.Enum):
    like = "like"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    headline: Mapped[str] = mapped_column(String(180), default="")
    location: Mapped[str] = mapped_column(String(120), default="")
    avatar_url: Mapped[str] = mapped_column(String(500), default="")
    banner_url: Mapped[str] = mapped_column(String(500), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship()


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    industry: Mapped[str] = mapped_column(String(120), default="")
    size_label: Mapped[str] = mapped_column(String(60), default="")
    headquarters: Mapped[str] = mapped_column(String(120), default="")
    website_url: Mapped[str] = mapped_column(String(300), default="")
    about: Mapped[str] = mapped_column(Text, default="")
    logo_url: Mapped[str] = mapped_column(String(500), default="")

    jobs: Mapped[list["Job"]] = relationship(back_populates="company")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    location: Mapped[str] = mapped_column(String(120), index=True)
    work_mode: Mapped[WorkMode] = mapped_column(Enum(WorkMode), index=True)
    employment_type: Mapped[EmploymentType] = mapped_column(Enum(EmploymentType), index=True)
    experience_level: Mapped[ExperienceLevel] = mapped_column(Enum(ExperienceLevel), index=True)

    promoted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    actively_recruiting: Mapped[bool] = mapped_column(Boolean, default=True)

    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(3), default="USD")

    skills_csv: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    apply_url: Mapped[str] = mapped_column(String(500), default="")

    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)

    company: Mapped["Company"] = relationship(back_populates="jobs")
    applications: Mapped[list["JobApplication"]] = relationship(back_populates="job")

    __table_args__ = (
        CheckConstraint("salary_min IS NULL OR salary_min >= 0", name="salary_min_nonneg"),
        CheckConstraint("salary_max IS NULL OR salary_max >= 0", name="salary_max_nonneg"),
    )


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_saved_job"),)


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    status: Mapped[str] = mapped_column(String(40), default="submitted")
    cover_letter: Mapped[str] = mapped_column(Text, default="")

    job: Mapped["Job"] = relationship(back_populates="applications")

    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_application_once"),)


class JobAlert(Base):
    __tablename__ = "job_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    query: Mapped[str] = mapped_column(String(200), default="")
    location: Mapped[str] = mapped_column(String(120), default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    body: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)

    author: Mapped["User"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post")
    reactions: Mapped[list["Reaction"]] = relationship(back_populates="post")


class Reaction(Base):
    __tablename__ = "reactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    type: Mapped[ReactionType] = mapped_column(Enum(ReactionType), default=ReactionType.like)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    post: Mapped["Post"] = relationship(back_populates="reactions")

    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_reaction_once"),)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)

    post: Mapped["Post"] = relationship(back_populates="comments")


class SearchSuggestion(Base):
    __tablename__ = "search_suggestions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    query: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    popularity: Mapped[int] = mapped_column(Integer, default=0, index=True)

