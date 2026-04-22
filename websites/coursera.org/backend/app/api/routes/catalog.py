from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.models.catalog import Course, Partner, Resource
from app.models.institution import Institution
from app.schemas.catalog import (
    CourseListItem,
    CourseListResponse,
    CoursePublic,
    InstitutionPublic,
    PartnerPublic,
    ResourceListResponse,
    ResourcePublic,
)


router = APIRouter()


@router.get("/partners", response_model=list[PartnerPublic])
def list_partners(db: Session = Depends(get_db)) -> list[Partner]:
    return list(db.scalars(select(Partner).order_by(Partner.name.asc())))


@router.get("/institutions", response_model=list[InstitutionPublic])
def list_institutions(db: Session = Depends(get_db)) -> list[Institution]:
    return list(db.scalars(select(Institution).order_by(Institution.name.asc())))


@router.get("/courses", response_model=CourseListResponse)
def list_courses(
    q: str | None = None,
    partner: str | None = None,
    level: str | None = None,
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> CourseListResponse:
    stmt = select(Course, Partner).join(Partner, Partner.id == Course.partner_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Course.title.ilike(like)) | (Course.headline.ilike(like)) | (Course.skills_csv.ilike(like)))
    if partner:
        stmt = stmt.where(Partner.slug == partner)
    if level:
        stmt = stmt.where(Course.level == level)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(Course.title.asc()).limit(limit).offset(offset)).all()

    items: list[CourseListItem] = []
    for course, p in rows:
        items.append(
            CourseListItem(
                id=course.id,
                title=course.title,
                slug=course.slug,
                headline=course.headline,
                level=course.level,
                language=course.language,
                duration_hours=course.duration_hours,
                skills_csv=course.skills_csv,
                image_url=course.image_url,
                partner_name=p.name,
                partner_slug=p.slug,
            )
        )
    return CourseListResponse(items=items, total=total)


@router.get("/courses/{slug}", response_model=CoursePublic)
def get_course(slug: str, db: Session = Depends(get_db)) -> Course:
    stmt = select(Course).options(joinedload(Course.partner)).where(Course.slug == slug)
    course = db.scalar(stmt)
    if not course:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/resources", response_model=ResourceListResponse)
def list_resources(
    kind: str | None = None,
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ResourceListResponse:
    stmt = select(Resource)
    if kind:
        stmt = stmt.where(Resource.kind == kind)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = list(db.scalars(stmt.order_by(Resource.created_at.desc()).limit(limit).offset(offset)))
    return ResourceListResponse(items=items, total=total)


@router.get("/resources/{slug}", response_model=ResourcePublic)
def get_resource(slug: str, db: Session = Depends(get_db)) -> Resource:
    res = db.scalar(select(Resource).where(Resource.slug == slug))
    if not res:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Resource not found")
    return res

