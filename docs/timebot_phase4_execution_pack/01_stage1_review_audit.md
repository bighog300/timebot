# Stage 1: Review Audit Trail

## Goal
Track who did what to review items, action items, category decisions, and intelligence overrides.

## Model: ReviewAuditEvent

Suggested fields:
- id
- document_id nullable
- review_item_id nullable
- action_item_id nullable
- intelligence_id nullable
- event_type
- actor_id nullable
- before_json nullable
- after_json nullable
- note nullable
- created_at

## Service
Create:
- app/services/review_audit.py

Suggested functions:
- record_event(...)
- list_events(...)
- list_document_events(document_id)
- list_review_item_events(review_item_id)
- list_action_item_events(action_item_id)

## API
Add:
- GET /api/v1/review/audit
- GET /api/v1/documents/{document_id}/review-audit

## Integration Points
Record audit events when:
- review item resolved
- review item dismissed
- action item completed
- action item dismissed
- action item updated
- category approved
- category overridden
- intelligence patched

## Acceptance Criteria
- important review/action/category mutations produce audit events
- audit endpoints return ordered, filterable results
- existing Phase 3 behavior remains unchanged except audit side effects
