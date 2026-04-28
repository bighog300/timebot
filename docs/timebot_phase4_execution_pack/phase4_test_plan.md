# Phase 4 Test Plan

## Unit Tests
- audit event creation
- audit filtering
- bulk operation transition rules
- metrics aggregation
- relationship review status transitions

## Integration Tests
- review resolve creates audit event
- review dismiss creates audit event
- action complete creates audit event
- category override creates audit event
- bulk resolve works
- bulk dismiss works
- metrics endpoints return expected totals
- relationship confirm/dismiss works

## Regression Tests
- no duplicate open review items
- no crawler/source-mapping imports
- existing document intelligence endpoints still work
- existing action item endpoints still work
- existing review endpoints still work

## Suggested Test Files
- tests/test_review_audit_phase4.py
- tests/test_bulk_review_operations_phase4.py
- tests/test_review_metrics_phase4.py
- tests/test_relationship_review_phase4.py
