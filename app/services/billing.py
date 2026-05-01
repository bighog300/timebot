from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.user import User


@dataclass
class BillingService:
    stripe_secret_key: str
    stripe_webhook_secret: str

    def create_checkout_session(self, user: User, plan: str) -> dict:
        return {
            "checkout_session_id": f"stub_{user.id}_{plan}",
            "checkout_url": f"https://billing.stub/checkout/{user.id}?plan={plan}",
            "plan": plan,
        }

    def handle_webhook(self, db: Session, event: dict) -> bool:
        event_type = event.get("type")
        data = (event.get("data") or {}).get("object") or {}
        if event_type != "checkout.session.completed":
            return False
        user_id = data.get("client_reference_id")
        plan = data.get("metadata", {}).get("plan")
        if not user_id or not plan:
            return False
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        user.plan = plan
        db.add(user)
        db.commit()
        return True
