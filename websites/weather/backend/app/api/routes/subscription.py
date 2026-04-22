from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.user import User


router = APIRouter(tags=["subscription"])


class PlanOut(BaseModel):
    id: str
    name: str
    price_monthly_usd: float
    description: str
    features: list[str]


@router.get("/subscriptions/plans", response_model=list[PlanOut])
def list_plans(session: Session = Depends(get_session)):
    plans = session.exec(select(SubscriptionPlan).order_by(SubscriptionPlan.price_monthly_usd.asc())).all()
    return [
        PlanOut(
            id=str(p.id),
            name=p.name,
            price_monthly_usd=p.price_monthly_usd,
            description=p.description,
            features=p.features or [],
        )
        for p in plans
    ]


class SubscriptionOut(BaseModel):
    id: str
    status: str
    started_at: datetime
    ends_at: datetime | None
    plan: PlanOut


@router.get("/me/subscription", response_model=SubscriptionOut | None)
def get_my_subscription(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    sub = session.exec(
        select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.created_at.desc())
    ).first()
    if not sub:
        return None
    plan = session.get(SubscriptionPlan, sub.plan_id)
    if not plan:
        return None
    return SubscriptionOut(
        id=str(sub.id),
        status=sub.status,
        started_at=sub.started_at,
        ends_at=sub.ends_at,
        plan=PlanOut(
            id=str(plan.id),
            name=plan.name,
            price_monthly_usd=plan.price_monthly_usd,
            description=plan.description,
            features=plan.features or [],
        ),
    )


class SubscribeRequest(BaseModel):
    plan_id: str


@router.post("/me/subscription/subscribe", response_model=SubscriptionOut)
def subscribe(
    payload: SubscribeRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        plan_uuid = uuid.UUID(payload.plan_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid plan_id") from e

    plan = session.get(SubscriptionPlan, plan_uuid)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Cancel any active subs first (simple model)
    subs = session.exec(select(Subscription).where(Subscription.user_id == user.id)).all()
    for s in subs:
        if s.status == "active":
            s.status = "canceled"
            s.ends_at = datetime.now()
            session.add(s)
    session.commit()

    sub = Subscription(user_id=user.id, plan_id=plan.id, status="active", started_at=datetime.now())
    session.add(sub)
    session.commit()
    session.refresh(sub)

    return SubscriptionOut(
        id=str(sub.id),
        status=sub.status,
        started_at=sub.started_at,
        ends_at=sub.ends_at,
        plan=PlanOut(
            id=str(plan.id),
            name=plan.name,
            price_monthly_usd=plan.price_monthly_usd,
            description=plan.description,
            features=plan.features or [],
        ),
    )


@router.post("/me/subscription/cancel")
def cancel_subscription(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    sub = session.exec(
        select(Subscription).where((Subscription.user_id == user.id) & (Subscription.status == "active"))
    ).first()
    if not sub:
        return {"status": "ok"}
    sub.status = "canceled"
    sub.ends_at = datetime.now()
    session.add(sub)
    session.commit()
    return {"status": "ok"}

