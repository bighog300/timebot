from __future__ import annotations

from dataclasses import dataclass
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.billing import Plan, Subscription
from app.models.user import User
from app.services.subscriptions import ensure_default_free_subscription

logger = logging.getLogger(__name__)


@dataclass
class BillingService:
    billing_provider: str
    stripe_enabled: bool
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_price_pro_monthly: str
    stripe_price_business_monthly: str
    app_url: str = "http://localhost:5174"

    def __post_init__(self) -> None:
        pass


    def _ensure_configured(self) -> None:
        if not self.stripe_enabled or self.billing_provider != "stripe":
            raise ValueError("Billing disabled")
        if not self.stripe_secret_key or not self.stripe_price_pro_monthly or not self.stripe_price_business_monthly or not self.stripe_webhook_secret:
            raise ValueError("Billing not configured")

    def _price_id_for_plan(self, plan_slug: str) -> str:
        mapping = {
            "pro": self.stripe_price_pro_monthly,
            "business": self.stripe_price_business_monthly,
        }
        value = mapping.get(plan_slug)
        if not value:
            raise ValueError("Unsupported plan")
        return value

    def _get_or_create_customer(self, db: Session, user: User) -> str:
        subscription = ensure_default_free_subscription(db, user.id)
        if subscription.external_customer_id:
            return subscription.external_customer_id
        import stripe
        stripe.api_key = self.stripe_secret_key
        customer = stripe.Customer.create(email=user.email, name=user.display_name or None, metadata={"user_id": str(user.id)})
        subscription.external_customer_id = customer["id"]
        db.add(subscription)
        db.commit()
        return customer["id"]

    def create_checkout_session(self, db: Session, user: User, plan: str) -> dict[str, str]:
        self._ensure_configured()
        _ = self._price_id_for_plan(plan)
        customer_id = self._get_or_create_customer(db, user)
        import stripe
        stripe.api_key = self.stripe_secret_key
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": self._price_id_for_plan(plan), "quantity": 1}],
            success_url=f"{self.app_url}/pricing?checkout=success",
            cancel_url=f"{self.app_url}/pricing?checkout=cancel",
            client_reference_id=str(user.id),
            metadata={"plan": plan},
        )
        return {"checkout_session_id": session["id"], "checkout_url": session["url"], "plan": plan}

    def create_customer_portal_session(self, db: Session, user: User) -> dict[str, str]:
        self._ensure_configured()
        customer_id = self._get_or_create_customer(db, user)
        import stripe
        stripe.api_key = self.stripe_secret_key
        session = stripe.billing_portal.Session.create(customer=customer_id, return_url=f"{self.app_url}/pricing")
        return {"portal_url": session["url"]}

    def construct_event(self, payload: bytes, signature: str | None) -> dict[str, Any]:
        if not signature:
            raise ValueError("Missing Stripe signature")
        import stripe
        try:
            evt = stripe.Webhook.construct_event(payload=payload, sig_header=signature, secret=self.stripe_webhook_secret)
            return dict(evt)
        except Exception as exc:
            raise ValueError("Invalid Stripe signature") from exc

    def handle_webhook(self, db: Session, event: dict) -> bool:
        event_type = event.get("type")
        obj = (event.get("data") or {}).get("object") or {}
        if event_type == "checkout.session.completed":
            processed = self._upsert_from_checkout(db, obj)
            if not processed:
                logger.warning("Billing webhook ignored checkout event due to missing linkage event_type=%s", event_type)
            return processed
        if event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
            processed = self._upsert_from_subscription(db, obj)
            if not processed:
                logger.warning("Billing webhook ignored subscription event due to missing linkage event_type=%s", event_type)
            return processed
        if event_type in {"invoice.paid", "invoice.payment_failed"}:
            processed = self._upsert_from_invoice(db, obj, event_type)
            if not processed:
                logger.warning("Billing webhook ignored invoice event due to missing linkage event_type=%s", event_type)
            return processed
        return False

    def _find_plan_by_price(self, db: Session, price_id: str | None) -> Plan | None:
        mapping = {self.stripe_price_pro_monthly: "pro", self.stripe_price_business_monthly: "business"}
        slug = mapping.get(price_id)
        if not slug:
            return None
        return db.query(Plan).filter(Plan.slug == slug, Plan.is_active.is_(True)).first()

    def _find_subscription(self, db: Session, customer_id: str | None, user_id: str | None = None) -> Subscription | None:
        query = db.query(Subscription)
        if customer_id:
            row = query.filter(Subscription.external_customer_id == customer_id).order_by(Subscription.created_at.desc()).first()
            if row:
                return row
        if user_id:
            return query.filter(Subscription.user_id == user_id).order_by(Subscription.created_at.desc()).first()
        return None

    def _upsert_from_checkout(self, db: Session, session_obj: dict) -> bool:
        user_id = session_obj.get("client_reference_id")
        customer_id = session_obj.get("customer")
        sub_id = session_obj.get("subscription")
        plan_slug = (session_obj.get("metadata") or {}).get("plan")
        if not (user_id and customer_id and plan_slug):
            return False
        sub = self._find_subscription(db, customer_id=customer_id, user_id=user_id)
        if not sub:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            sub = ensure_default_free_subscription(db, user.id)
        target_plan = db.query(Plan).filter(Plan.slug == plan_slug, Plan.is_active.is_(True)).first()
        if not target_plan:
            return False
        previous_status = sub.status
        previous_plan_id = sub.plan_id
        sub.plan_id = target_plan.id
        sub.external_provider = "stripe"
        sub.billing_provider = "stripe"
        sub.external_customer_id = customer_id
        sub.billing_customer_id = customer_id
        sub.external_subscription_id = sub_id
        sub.billing_subscription_id = sub_id
        sub.status = "active"
        db.add(sub)
        db.commit()
        logger.info("Billing subscription updated source=checkout user_id=%s old_plan_id=%s new_plan_id=%s old_status=%s new_status=%s", sub.user_id, previous_plan_id, sub.plan_id, previous_status, sub.status)
        return True

    def _upsert_from_subscription(self, db: Session, stripe_sub: dict) -> bool:
        customer_id = stripe_sub.get("customer")
        sub_id = stripe_sub.get("id")
        status = stripe_sub.get("status")
        item = ((stripe_sub.get("items") or {}).get("data") or [{}])[0]
        price_id = (item.get("price") or {}).get("id")
        plan = self._find_plan_by_price(db, price_id)
        sub = self._find_subscription(db, customer_id=customer_id)
        if not sub:
            return False
        previous_status = sub.status
        previous_plan_id = sub.plan_id
        if plan:
            sub.plan_id = plan.id
        sub.external_provider = "stripe"
        sub.billing_provider = "stripe"
        sub.external_customer_id = customer_id
        sub.billing_customer_id = customer_id
        sub.external_subscription_id = sub_id
        sub.billing_subscription_id = sub_id
        sub.billing_price_id = price_id
        status_map = {"trialing": "trialing", "active": "active", "past_due": "past_due", "unpaid": "past_due", "canceled": "canceled", "incomplete": "past_due"}
        sub.status = status_map.get(status or "", sub.status)
        cps = stripe_sub.get("current_period_start")
        cpe = stripe_sub.get("current_period_end")
        if cps:
            sub.current_period_start = datetime.fromtimestamp(cps, tz=timezone.utc)
        if cpe:
            sub.current_period_end = datetime.fromtimestamp(cpe, tz=timezone.utc)
            sub.billing_current_period_end = sub.current_period_end
        sub.cancel_at_period_end = bool(stripe_sub.get("cancel_at_period_end", False))
        db.add(sub)
        db.commit()
        logger.info("Billing subscription updated source=stripe_subscription user_id=%s old_plan_id=%s new_plan_id=%s old_status=%s new_status=%s cancel_at_period_end=%s", sub.user_id, previous_plan_id, sub.plan_id, previous_status, sub.status, sub.cancel_at_period_end)
        return True

    def _upsert_from_invoice(self, db: Session, invoice: dict, event_type: str) -> bool:
        sub = self._find_subscription(db, customer_id=invoice.get("customer"))
        if not sub:
            return False
        previous_status = sub.status
        sub.status = "active" if event_type == "invoice.paid" else "past_due"
        db.add(sub)
        db.commit()
        logger.info("Billing subscription updated source=invoice user_id=%s old_status=%s new_status=%s", sub.user_id, previous_status, sub.status)
        return True
