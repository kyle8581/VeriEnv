from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import ORMModel, Timestamped


class PartnerPublic(Timestamped):
    id: int
    name: str
    slug: str
    logo_url: str
    kind: str


class InstitutionPublic(Timestamped):
  id: int
  name: str
  slug: str
  country: str
  website_url: str


class CoursePublic(Timestamped):
    id: int
    title: str
    slug: str
    headline: str
    description: str
    level: str
    language: str
    duration_hours: int
    skills_csv: str
    image_url: str
    partner: PartnerPublic


class CourseListItem(ORMModel):
    id: int
    title: str
    slug: str
    headline: str
    level: str
    language: str
    duration_hours: int
    skills_csv: str
    image_url: str
    partner_name: str
    partner_slug: str


class CourseListResponse(BaseModel):
    items: list[CourseListItem]
    total: int


class ResourcePublic(Timestamped):
    id: int
    kind: str
    title: str
    slug: str
    summary: str
    body_md: str
    hero_image_url: str
    cta_label: str


class ResourceListResponse(BaseModel):
    items: list[ResourcePublic]
    total: int

