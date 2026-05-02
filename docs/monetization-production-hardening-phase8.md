# Monetization Production Hardening (Phase 8)

## Required environment variables
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_PRO_MONTHLY`
- `STRIPE_PRICE_TEAM_MONTHLY`
- `PUBLIC_APP_URL`

## Stripe setup
1. Create products/plans in Stripe for Pro and Team monthly subscriptions.
2. Copy each recurring price id into `STRIPE_PRICE_PRO_MONTHLY` and `STRIPE_PRICE_TEAM_MONTHLY`.
3. Set `PUBLIC_APP_URL` to your deployed frontend origin so checkout/portal return URLs resolve.

## Plan configuration
Default plans are seeded by `seed_default_plans` in `app.services.subscriptions` and used by limit enforcement for:
- `documents_per_month`
- `processing_jobs_per_month`
- `storage_bytes`

## Webhook setup
1. Configure Stripe webhook endpoint: `POST /api/v1/billing/webhook`.
2. Subscribe to events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
3. Copy Stripe signing secret to `STRIPE_WEBHOOK_SECRET`.
4. Signature header `Stripe-Signature` is required; invalid/missing signatures are rejected.

## Local development billing flow
1. Start backend/frontend with Stripe test keys.
2. Register a user (free subscription auto-created).
3. Visit `/pricing`.
4. Click **Upgrade** to create checkout session and redirect to Stripe-hosted checkout.
5. Complete checkout in Stripe test mode.
6. Send webhook events (Stripe CLI or dashboard replay) to update subscription status/plan.
7. Return to dashboard and verify updated limits.

## Test commands
- `pytest tests/test_billing_phase5.py tests/test_monetization_phase8_integration.py`
- `pytest`
- `cd frontend && npm test -- PricingPage.test.tsx`
