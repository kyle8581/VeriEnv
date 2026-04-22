from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import CompanyOut, JobListItem, JobOut, JobSearchResponse
from app.db.models import (
    Company,
    EmploymentType,
    ExperienceLevel,
    Job,
    JobAlert,
    JobApplication,
    SavedJob,
    User,
    WorkMode,
)
from app.db.session import get_db

router = APIRouter()


def _skills_list(skills_csv: str) -> list[str]:
    return [s.strip() for s in (skills_csv or "").split(",") if s.strip()]


def _company_out(c: Company) -> CompanyOut:
    return CompanyOut(id=c.id, name=c.name, industry=c.industry, size_label=c.size_label, logo_url=c.logo_url)


def _job_list_item(db: Session, *, job: Job, viewer_id: str) -> JobListItem:
    saved = (
        db.scalar(
            select(func.count())
            .select_from(SavedJob)
            .where(SavedJob.user_id == viewer_id, SavedJob.job_id == job.id)
        )
        or 0
    ) > 0
    return JobListItem(
        id=job.id,
        title=job.title,
        location=job.location,
        work_mode=job.work_mode,
        promoted=job.promoted,
        actively_recruiting=job.actively_recruiting,
        posted_at=job.posted_at,
        company=_company_out(job.company),
        viewer_saved=saved,
    )


def _job_out(db: Session, *, job: Job, viewer_id: str) -> JobOut:
    saved = (
        db.scalar(
            select(func.count())
            .select_from(SavedJob)
            .where(SavedJob.user_id == viewer_id, SavedJob.job_id == job.id)
        )
        or 0
    ) > 0
    applied = (
        db.scalar(
            select(func.count())
            .select_from(JobApplication)
            .where(JobApplication.user_id == viewer_id, JobApplication.job_id == job.id)
        )
        or 0
    ) > 0
    applicants = db.scalar(select(func.count()).select_from(JobApplication).where(JobApplication.job_id == job.id)) or 0
    return JobOut(
        id=job.id,
        title=job.title,
        location=job.location,
        work_mode=job.work_mode,
        employment_type=job.employment_type,
        experience_level=job.experience_level,
        promoted=job.promoted,
        actively_recruiting=job.actively_recruiting,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        skills=_skills_list(job.skills_csv),
        description=job.description,
        apply_url=job.apply_url,
        posted_at=job.posted_at,
        applicants_count=applicants,
        company=_company_out(job.company),
        viewer_saved=saved,
        viewer_applied=applied,
    )


@router.get("/search", response_model=JobSearchResponse)
def search_jobs(
    query: str = Query(default="", max_length=120),
    location: str = Query(default="", max_length=120),
    work_mode: list[WorkMode] | None = Query(default=None),
    employment_type: list[EmploymentType] | None = Query(default=None),
    experience_level: list[ExperienceLevel] | None = Query(default=None),
    date_posted_days: int | None = Query(default=None, ge=1, le=60),
    limit: int = Query(default=10, ge=1, le=30),
    offset: int = Query(default=0, ge=0, le=5000),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobSearchResponse:
    filters = []
    if query.strip():
        qn = query.strip().lower()
        filters.append(func.lower(Job.title).like(f"%{qn}%"))
    if location.strip():
        ln = location.strip().lower()
        filters.append(func.lower(Job.location).like(f"%{ln}%"))
    if work_mode:
        filters.append(Job.work_mode.in_(work_mode))
    if employment_type:
        filters.append(Job.employment_type.in_(employment_type))
    if experience_level:
        filters.append(Job.experience_level.in_(experience_level))
    if date_posted_days is not None:
        cutoff = datetime.now(UTC) - timedelta(days=date_posted_days)
        filters.append(Job.posted_at >= cutoff)

    stmt = select(Job).join(Company, Company.id == Job.company_id)
    if filters:
        stmt = stmt.where(and_(*filters))

    # LinkedIn-like ordering: most recent first, promoted interleaved naturally via "promoted desc"
    stmt = stmt.order_by(desc(Job.promoted), desc(Job.posted_at))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    jobs = list(db.scalars(stmt.offset(offset).limit(limit)).all())
    for j in jobs:
        _ = j.company
    return JobSearchResponse(total=total, items=[_job_list_item(db, job=j, viewer_id=user.id) for j in jobs])


@router.get("/alerts/me")
def list_alerts(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    alerts = list(
        db.scalars(select(JobAlert).where(JobAlert.user_id == user.id).order_by(desc(JobAlert.created_at))).all()
    )
    return [
        {"id": a.id, "query": a.query, "location": a.location, "enabled": a.enabled, "created_at": a.created_at.isoformat()}
        for a in alerts
    ]


@router.post("/alerts/toggle")
def toggle_alert(
    query: str = Query(default="", max_length=120),
    location: str = Query(default="", max_length=120),
    enabled: bool = True,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(JobAlert).where(JobAlert.user_id == user.id, JobAlert.query == query, JobAlert.location == location)
    alert = db.scalar(stmt)
    if alert is None:
        alert = JobAlert(user_id=user.id, query=query, location=location, enabled=enabled)
        db.add(alert)
        db.commit()
        return {"enabled": enabled}
    alert.enabled = enabled
    db.add(alert)
    db.commit()
    return {"enabled": enabled}


@router.post("/{job_id}/save")
def save_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    job = db.scalar(select(Job.id).where(Job.id == job_id))
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    db.add(SavedJob(user_id=user.id, job_id=job_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    return {"saved": True}


@router.delete("/{job_id}/save")
def unsave_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    sj = db.scalar(select(SavedJob).where(SavedJob.user_id == user.id, SavedJob.job_id == job_id))
    if sj is not None:
        db.delete(sj)
        db.commit()
    return {"saved": False}


@router.post("/{job_id}/apply")
def apply(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    job = db.scalar(select(Job.id).where(Job.id == job_id))
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    db.add(JobApplication(user_id=user.id, job_id=job_id, cover_letter=""))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    return {"applied": True}


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> JobOut:
    job = db.scalar(select(Job).where(Job.id == job_id))
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    _ = job.company
    return _job_out(db, job=job, viewer_id=user.id)

