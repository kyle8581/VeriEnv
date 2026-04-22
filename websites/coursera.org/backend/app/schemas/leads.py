from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class EbookLeadCreate(BaseModel):
    resource_slug: str = Field(min_length=2, max_length=260)
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    job_title: str = Field(min_length=1, max_length=200)
    work_email: EmailStr
    work_phone: str = Field(min_length=3, max_length=60)
    institution_name: str = Field(min_length=1, max_length=220)
    primary_discipline: str = Field(min_length=1, max_length=120)
    country: str = Field(min_length=2, max_length=2)
    consent_text: str = Field(default="", max_length=5000)


class ContactLeadCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=220)
    email: EmailStr
    institution: str = Field(default="", max_length=220)
    message: str = Field(default="", max_length=8000)

