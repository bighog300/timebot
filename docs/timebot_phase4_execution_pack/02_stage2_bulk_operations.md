# Stage 2: Bulk Review and Action Operations

## Goal
Allow users to process review queues and action items efficiently.

## API Endpoints
- POST /api/v1/review/items/bulk-resolve
- POST /api/v1/review/items/bulk-dismiss
- POST /api/v1/action-items/bulk-complete
- POST /api/v1/action-items/bulk-dismiss

## Request Shape
```json
{
  "ids": [1, 2, 3],
  "note": "optional reason"
}
```

## Response Shape
```json
{
  "updated_count": 3,
  "skipped_count": 0,
  "items": []
}
```

## Requirements
- choose and document invalid-ID behavior
- avoid mutating already terminal records unless existing single-item behavior does
- create audit events for changed records
- keep operations transactionally safe where practical

## Acceptance Criteria
- users can process multiple review/action records in one request
- status transitions remain valid
- audit trail captures bulk operations
