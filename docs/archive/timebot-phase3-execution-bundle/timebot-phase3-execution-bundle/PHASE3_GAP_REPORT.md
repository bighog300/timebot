# Repo-Specific Phase 3 Gap Report

## Bottom line

The repository has already started Phase 3, but it is **not complete**. The codebase contains:

- full-text search service and API endpoints
- Qdrant-backed embeddings service
- semantic search endpoints
- relationship-oriented database models
- background embedding task dispatch

However, several Phase 3 deliverables from `docs/MASTER_IMPLEMENTATION_PLAN.md` and `docs/PHASE3_COMPLETE_EXECUTION.md` are still missing or only partially implemented.

## What already exists

### Sprint 9: Full-text search
Present:
- `app/services/search_service.py`
- `app/api/v1/search.py`
- `app/schemas/search.py`
- `Document.search_vector` usage in service code

Implemented behaviors already present:
- text search with PostgreSQL `tsquery`
- ranking via `ts_rank`
- category/source/date/tag/favorite/file type filtering
- primitive highlights from summary/raw text
- suggestions from categories and tags
- facets endpoint in `search.py`

### Sprint 10: Semantic search
Present:
- `app/services/embedding_service.py`
- semantic search endpoints in `app/api/v1/search.py`
- background task `embed_document_task` in `app/workers/tasks.py`
- Qdrant + sentence-transformers dependencies in `requirements.txt`

Implemented behaviors already present:
- embedding generation
- Qdrant collection bootstrap
- vector search
- similar document search by vector lookup
- async embedding after document processing completion

### Phase 3-adjacent data model groundwork
Present:
- `app/models/relationships.py`
- `DocumentRelationship` model
- `ProcessingQueue` task type supports `detect_relationships`
- `DocumentVersion`, `Connection`, `SyncLog`

## What is still missing or incomplete

### 1. Search indexing hardening
Missing or unclear:
- no dedicated `search_indexer.py`
- no query parser implementation
- no explicit migration/index management for `search_vector`
- no reliable snippet/highlight generation from PostgreSQL `ts_headline`
- no search analytics or persisted query telemetry

### 2. Hybrid search
Missing:
- no endpoint that combines lexical and semantic ranking into a single ordered result set
- no score normalization strategy
- no fallback behavior definition when Qdrant is down
- no re-ranking logic across text hits and vector hits

### 3. Relationship detection
Missing:
- no `relationship_detector.py`
- no worker to compute relationships after embeddings exist
- no API to list related documents by stored relationship type
- no persistence flow that writes `DocumentRelationship` rows from actual detection logic
- duplicate detection is only implied, not implemented

### 4. Timeline generation
Missing:
- no `timeline_builder.py`
- no timeline API
- no timeline grouping/aggregation for upload dates, extracted dates, or event entities
- no response schema for timeline visualization consumers

### 5. Insights generation
Missing:
- no `insights_generator.py`
- no `/api/v1/insights` routes
- no dashboard payloads for trends, action items, duplicates, category drift, or relationship summaries

### 6. Category intelligence completion
Partial at best:
- category discovery exists
- but no dedicated `category_intelligence.py`, `category_merger.py`, or `category_analytics.py`
- no merge recommendation workflow
- no override-aware refinement loop
- no analytics endpoints beyond current categories CRUD

### 7. Verification and tests
Missing:
- no test suite for Phase 3 behavior in repo
- no integration tests for search ranking, semantic search, hybrid search, relationships, or insights
- no seeded fixtures for representative corpus testing

## Recommended definition of “Phase 3 complete” for this repo

Phase 3 should be considered complete only when all of the following are true:

1. Lexical search works with filters, facets, suggestions, and reliable result snippets.
2. Hybrid search exists and outperforms lexical-only search for fuzzy queries.
3. Embeddings are generated automatically and can be backfilled safely.
4. Relationships are detected, persisted, queryable, and explainable.
5. Duplicate detection exists and is surfaced through API.
6. Timeline API exists with stable response schema for future frontend work.
7. Insights API exists with dashboard-ready aggregate payloads.
8. Category intelligence includes analytics and merge/refinement recommendations.
9. Phase 3 endpoints have tests and a reproducible validation path.
