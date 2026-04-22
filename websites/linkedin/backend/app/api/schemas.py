from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.db.models import EmploymentType, ExperienceLevel, WorkMode


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserPublic(BaseModel):
    id: str
    email: EmailStr | None = None
    first_name: str
    last_name: str
    headline: str
    location: str
    avatar_url: str


class PostCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    image_url: str = Field(default="", max_length=500)


class CommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: str
    author: UserPublic
    body: str
    created_at: datetime


class PostOut(BaseModel):
    id: str
    author: UserPublic
    body: str
    image_url: str
    created_at: datetime
    reactions_count: int
    comments_count: int
    viewer_has_liked: bool


class PaginatedPosts(BaseModel):
    items: list[PostOut]
    next_cursor: str | None = None


class CompanyOut(BaseModel):
    id: str
    name: str
    industry: str
    size_label: str
    logo_url: str


class JobOut(BaseModel):
    id: str
    title: str
    location: str
    work_mode: WorkMode
    employment_type: EmploymentType
    experience_level: ExperienceLevel
    promoted: bool
    actively_recruiting: bool
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str
    skills: list[str]
    description: str
    apply_url: str
    posted_at: datetime
    applicants_count: int
    company: CompanyOut
    viewer_saved: bool = False
    viewer_applied: bool = False


class JobListItem(BaseModel):
    id: str
    title: str
    location: str
    work_mode: WorkMode
    promoted: bool
    actively_recruiting: bool
    posted_at: datetime
    company: CompanyOut
    viewer_saved: bool


class JobSearchResponse(BaseModel):
    total: int
    items: list[JobListItem]


class TypeaheadResponse(BaseModel):
    suggestions: list[str]


class PeopleSearchItem(BaseModel):
    id: str
    first_name: str
    last_name: str
    headline: str
    location: str
    avatar_url: str


class PeopleSearchResponse(BaseModel):
    total: int
    items: list[PeopleSearchItem]


class PostSearchItem(BaseModel):
    id: str
    author: UserPublic
    body: str
    image_url: str
    created_at: datetime


class PostSearchResponse(BaseModel):
    total: int
    items: list[PostSearchItem]

