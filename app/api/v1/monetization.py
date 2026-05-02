from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.models.billing import Plan
from app.models.user import User
from app.services.billing import BillingService
from app.services.monetization import usage_payload
from app.services.subscriptions import ensure_default_free_subscription, get_user_subscription, seed_default_plans

router = APIRouter(tags=["monetization"])
billing_service = BillingService(settings.STRIPE_SECRET_KEY, settings.STRIPE_WEBHOOK_SECRET)


class CheckoutRequest(BaseModel):
    plan: str


@router.get("/me/usage")
def get_me_usage(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return usage_payload(db, user)


@router.get("/usage")
def get_usage(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return usage_payload(db, user)


@router.get("/me/subscription")
def get_me_subscription(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    subscription = ensure_default_free_subscription(db, user.id)
    plan = subscription.plan
    return {
        "status": subscription.status,
        "current_period_start": subscription.current_period_start,
        "current_period_end": subscription.current_period_end,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "plan": {
            "slug": plan.slug if plan else "free",
            "name": plan.name if plan else "Free",
            "price_monthly_cents": plan.price_monthly_cents if plan else 0,
            "currency": plan.currency if plan else "usd",
        },
    }


@router.get("/plans")
def list_plans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    seed_default_plans(db)
    plans = db.query(Plan).filter(Plan.is_active.is_(True)).order_by(Plan.price_monthly_cents.asc()).all()
    current = get_user_subscription(db, user.id)
    current_plan = current.plan.slug if current and current.plan else "free"
    return [
        {
            "slug": plan.slug,
            "name": plan.name,
            "price_monthly_cents": plan.price_monthly_cents,
            "currency": plan.currency,
            "limits": plan.limits_json or {},
            "features": plan.features_json or {},
            "is_current": plan.slug == current_plan,
        }
        for plan in plans
    ]


@router.post("/billing/checkout")
def create_checkout(payload: CheckoutRequest, user: User = Depends(get_current_user)):
    return billing_service.create_checkout_session(user, payload.plan)


@router.post("/billing/webhook")
def billing_webhook(event: dict, db: Session = Depends(get_db)):
    processed = billing_service.handle_webhook(db, event)
    if not processed:
        raise HTTPException(status_code=400, detail="Invalid webhook")
    return {"ok": True}
