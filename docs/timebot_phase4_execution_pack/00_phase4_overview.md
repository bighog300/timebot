# Phase 4 Overview: Review Operations & Relationship Intelligence

## Goal
Make Timebot's document intelligence workflow operationally useful at scale.

Phase 3 created the core intelligence and review loop. Phase 4 should add:
- auditability
- bulk operations
- metrics
- duplicate/relationship review
- dashboard-ready APIs

## Preserve Existing Product Scope
Keep Timebot focused on:
- document organization
- AI-assisted categorization
- tags
- action items
- review workflow
- search and insights

Do not add:
- crawling
- scraping
- source profiling
- URL mapping
- website ingestion

## Main Deliverables
1. Audit trail for review/action/intelligence mutations
2. Bulk resolve/dismiss/complete APIs
3. Review and action item metrics
4. Dedicated relationship review workflow
5. Tests and regression coverage

## Suggested New Models
- ReviewAuditEvent
- DocumentRelationshipReview

## Suggested New Services
- app/services/review_audit.py
- app/services/review_metrics.py
- app/services/relationship_review.py
