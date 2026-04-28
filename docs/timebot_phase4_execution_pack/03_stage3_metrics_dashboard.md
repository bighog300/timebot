# Stage 3: Metrics and Dashboard Endpoints

## Goal
Expose dashboard-ready metrics for review operations and action items.

## Endpoints
- GET /api/v1/review/metrics
- GET /api/v1/action-items/metrics

## Review Metrics
Return:
- open_review_count
- resolved_review_count
- dismissed_review_count
- open_by_type
- open_by_priority
- average_age_hours
- oldest_open_items
- recently_resolved_count
- low_confidence_category_count
- uncategorized_count

## Action Item Metrics
Return:
- open_count
- completed_count
- dismissed_count
- overdue_count if due dates exist
- completion_rate
- recently_completed_count

## Acceptance Criteria
- frontend can build a review dashboard without custom aggregation
- metrics are deterministic and tested
