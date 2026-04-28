# Stage 4: Dedicated Relationship Review

## Goal
Create a dedicated workflow for duplicate/similar/related document decisions.

## Model: DocumentRelationshipReview

Suggested fields:
- id
- source_document_id
- target_document_id
- relationship_type: duplicate | similar | related
- confidence
- status: pending | confirmed | dismissed
- reason_codes_json
- metadata_json
- created_at
- reviewed_at nullable
- reviewed_by nullable

## API
- GET /api/v1/review/relationships
- GET /api/v1/review/relationships/{relationship_id}
- POST /api/v1/review/relationships/{relationship_id}/confirm
- POST /api/v1/review/relationships/{relationship_id}/dismiss

## Acceptance Criteria
- duplicate/similar document review is no longer only generic metadata
- relationship decisions can be confirmed/dismissed
- duplicate pending relationships are prevented
