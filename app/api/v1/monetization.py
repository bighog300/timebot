from datetime import timedelta
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.models.billing import Plan
from app.models.document import Document
from app.models.user import User
from app.services.billing import BillingService
from app.services.subscriptions import ensure_default_free_subscription, get_user_subscription, seed_default_plans
from app.services.usage import get_usage_total

logger = logging.getLogger(__name__)

def usage_payload(db: Session, user: User) -> dict:
    subscription = ensure_default_free_subscription(db, user.id)
    plan = subscription.plan
    limits = (plan.limits_json if plan else {}) or {}
    start = subscription.current_period_start
    end = subscription.current_period_end or (start + timedelta(days=32)).replace(day=1)
    docs_used = db.query(Document).filter(Document.user_id == user.id).count()
    jobs_used = get_usage_total(db, user.id, "processing_jobs_per_month", start, end)
    return {
        "plan": plan.slug if plan else "free",
        "documents": {"used": docs_used, "limit": limits.get("documents_per_month")},
        "processing_jobs": {"used": jobs_used, "limit": limits.get("processing_jobs_per_month")},
        "storage_bytes": {"used": sum((d.file_size or 0) for d in db.query(Document).filter(Document.user_id == user.id).all()), "limit": limits.get("storage_bytes")},
    }


router = APIRouter(tags=["monetization"])
billing_service = BillingService(
    settings.STRIPE_SECRET_KEY,
    settings.STRIPE_WEBHOOK_SECRET,
    settings.STRIPE_PRICE_PRO_MONTHLY,
    settings.STRIPE_PRICE_TEAM_MONTHLY,
    settings.PUBLIC_APP_URL,
)


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


@router.post("/billing/checkout-session")
def create_checkout(payload: CheckoutRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return billing_service.create_checkout_session(db, user, payload.plan)
    except ValueError as exc:
        detail = str(exc)
        if detail == 'Billing not configured':
            raise HTTPException(status_code=400, detail={'code': 'billing_not_configured', 'message': 'Billing is not configured in this environment.'}) from exc
        raise HTTPException(status_code=400, detail=detail) from exc


@router.post("/billing/customer-portal")
def create_customer_portal(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return billing_service.create_customer_portal_session(db, user)


@router.post("/billing/webhook")
async def billing_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
):
    payload = await request.body()
    try:
        event = billing_service.construct_event(payload=payload, signature=stripe_signature)
    except ValueError as exc:
        logger.warning("Billing webhook signature validation failed detail=%s", str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    processed = billing_service.handle_webhook(db, event)
    if not processed:
        logger.warning("Billing webhook not processed event_type=%s", event.get("type"))
        raise HTTPException(status_code=400, detail="Unsupported or invalid webhook event")
    return {"ok": True}
