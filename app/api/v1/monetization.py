from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.models.user import User
from app.services.billing import BillingService
from app.services.monetization import usage_payload

router = APIRouter(tags=["monetization"])
billing_service = BillingService(settings.STRIPE_SECRET_KEY, settings.STRIPE_WEBHOOK_SECRET)


class CheckoutRequest(BaseModel):
    plan: str


@router.get("/usage")
def get_usage(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return usage_payload(db, user)


@router.post("/billing/checkout")
def create_checkout(payload: CheckoutRequest, user: User = Depends(get_current_user)):
    return billing_service.create_checkout_session(user, payload.plan)


@router.post("/billing/webhook")
def billing_webhook(event: dict, db: Session = Depends(get_db)):
    processed = billing_service.handle_webhook(db, event)
    if not processed:
        raise HTTPException(status_code=400, detail="Invalid webhook")
    return {"ok": True}
