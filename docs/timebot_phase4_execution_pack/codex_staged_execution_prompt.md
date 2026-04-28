# Staged Codex Execution Prompt for Timebot Phase 4

Use this prompt for Codex. Execute one stage at a time. Do not jump ahead unless the current stage is complete and tests pass.

---

## Global Context

You are working in the Timebot repo.

Timebot is a document organizer and document intelligence app.

It is NOT:
- a crawler
- a scraper
- a source profiler
- a URL mapper
- a website ingestion system

Do not add or restore anything related to crawler/source-mapping functionality.

Phase 3 already implemented:
- DocumentIntelligence
- DocumentReviewItem
- DocumentActionItem
- review queue APIs
- action item APIs
- intelligence get/regenerate/update APIs
- category approve/override
- persistence of AI intelligence through document processing and manual analysis

Phase 4 is: Review Operations & Relationship Intelligence.

The purpose is to make the review workflow operationally usable through audit trails, bulk actions, metrics, and richer duplicate/relationship review.

---

## General Requirements

Preserve existing functionality:
- upload
- document processing
- text extraction
- AI enrichment
- document intelligence persistence
- categories
- tags
- search
- review queue
- action items
- auth/user flows

Follow existing repo patterns for:
- SQLAlchemy models
- Alembic migrations
- schemas
- services
- API routers
- tests

Run targeted tests after each stage, then run:
pytest -q
python -m compileall app tests

After each stage, report:
1. Summary of changes
2. File-by-file change list
3. Migrations added
4. Tests added/updated and results
5. Known limitations
6. Whether it is safe to proceed to the next stage

---

# Stage 1 Prompt: Review Audit Trail

Implement review audit trail support.

Add a ReviewAuditEvent model and migration.

Track audit events for:
- review item resolved
- review item dismissed
- action item completed
- action item dismissed
- action item updated
- category approved
- category overridden
- intelligence updated

Add service:
- app/services/review_audit.py

Add endpoints:
- GET /api/v1/review/audit
- GET /api/v1/documents/{document_id}/review-audit

Requirements:
- capture actor_id if current user is available
- capture before_json and after_json where practical
- include event_type, note, and created_at
- do not break existing Phase 3 flows
- tests must verify audit events are created by mutations

Suggested tests:
- tests/test_review_audit_phase4.py

Acceptance:
- mutation flows create audit events
- audit endpoints return ordered/filterable events
- pytest passes

---

# Stage 2 Prompt: Bulk Operations

Implement bulk review and action-item operations.

Add endpoints:
- POST /api/v1/review/items/bulk-resolve
- POST /api/v1/review/items/bulk-dismiss
- POST /api/v1/action-items/bulk-complete
- POST /api/v1/action-items/bulk-dismiss

Request shape:
{
  "ids": [1, 2, 3],
  "note": "optional"
}

Response shape:
{
  "updated_count": 3,
  "skipped_count": 0,
  "items": []
}

Requirements:
- choose and document invalid-ID behavior
- do not mutate already terminal records unless existing single-item behavior does
- create audit events for each changed record
- keep operations transactionally safe where practical

Suggested tests:
- tests/test_bulk_review_operations_phase4.py

Acceptance:
- bulk operations work
- audit events created
- invalid and idempotent behavior tested
- pytest passes

---

# Stage 3 Prompt: Metrics and Dashboard Endpoints

Implement dashboard-ready metrics.

Add endpoints:
- GET /api/v1/review/metrics
- GET /api/v1/action-items/metrics

Suggested service:
- app/services/review_metrics.py

Acceptance:
- metrics return correct counts
- empty state returns zeros
- tests cover filtering
- pytest passes

---

# Stage 4 Prompt: Relationship Review

Implement dedicated duplicate/similar/related document review.

Add model:
- DocumentRelationshipReview

Add service:
- app/services/relationship_review.py

Add endpoints:
- GET /api/v1/review/relationships
- GET /api/v1/review/relationships/{relationship_id}
- POST /api/v1/review/relationships/{relationship_id}/confirm
- POST /api/v1/review/relationships/{relationship_id}/dismiss

Requirements:
- prevent duplicate pending relationship review for the same pair/type
- support filtering by status and relationship_type
- create audit events on confirm/dismiss if Stage 1 exists
- do not replace existing DocumentReviewItem duplicate behavior unless needed; bridge gradually

Suggested tests:
- tests/test_relationship_review_phase4.py

Acceptance:
- relationship review lifecycle works
- duplicate pending records prevented
- confirm/dismiss tested
- pytest passes

---

# Stage 5 Prompt: Polish and Regression

Perform Phase 4 hardening.

Tasks:
- add enum validation where appropriate
- check transaction behavior for bulk operations
- ensure audit event consistency
- ensure metrics are stable and tested
- ensure no crawler/source-mapping references exist in runtime code
- update docs/comments if repo has API docs
- run full tests and compile

Commands:
pytest -q
python -m compileall app tests

Acceptance:
- all tests pass
- no crawler/scraper/source-mapping functionality reintroduced
- Phase 3 and Phase 4 workflows are stable
