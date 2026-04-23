# Phase 3 Workplan

## Goal

Complete Phase 3 in a way that is consistent with the existing FastAPI + SQLAlchemy + Celery + Qdrant architecture, while keeping the backend ready for the Phase 4 frontend docs already present in the repo.

## Execution order

### Step 1 — Stabilize search infrastructure
Create:
- `app/services/search_indexer.py`
- `app/services/query_parser.py`

Do:
- formalize parsing of user query text into lexical terms, phrase terms, filters, and safe fallback behavior
- centralize generation and refresh of PostgreSQL search vectors
- add support for PostgreSQL-native snippet generation when available
- keep existing `search_service.py` but refactor it to use parser/indexer helpers

Acceptance criteria:
- lexical search still passes existing endpoint behavior
- search snippets are generated consistently
- malformed query strings do not 500 the API

### Step 2 — Add hybrid search
Extend:
- `app/services/search_service.py`
- `app/api/v1/search.py`
- `app/schemas/search.py`

Do:
- add a `hybrid_search()` method
- merge lexical and semantic hits using normalized scores
- expose endpoint `/api/v1/search/hybrid`
- define fallback behavior when embeddings service is disabled

Acceptance criteria:
- endpoint returns results even if Qdrant is unavailable
- duplicate documents are deduplicated across lexical/vector result sets
- response includes score breakdown fields useful for debugging

### Step 3 — Build relationship detection
Create:
- `app/services/relationship_detector.py`
- worker task for relationship detection in `app/workers/tasks.py`

Do:
- detect `similar_to`, `related_to`, `duplicates`, `references`, and `follows_up` where defensible
- start with deterministic heuristics using embeddings, filename overlap, tag overlap, entity overlap, and date adjacency
- persist to `DocumentRelationship`
- trigger this after embedding creation and also provide a backfill task

Acceptance criteria:
- stored relationships are idempotent
- confidence scores are bounded and traceable
- duplicate candidates are represented distinctly from loose similarity

### Step 4 — Build timeline support
Create:
- `app/services/timeline_builder.py`
- timeline schemas
- timeline endpoints, either in `app/api/v1/insights.py` or dedicated `timeline.py`

Do:
- build timeline events from upload date, document dates in entities, action items with due dates if available, and document relationships
- support aggregation by day/week/month
- support filters by category/source/type

Acceptance criteria:
- endpoint returns stable dashboard-friendly JSON
- documents without extracted dates still appear via upload date fallback

### Step 5 — Build insights API
Create:
- `app/services/insights_generator.py`
- `app/api/v1/insights.py`

Do:
- generate aggregate insights: document volume trends, category distribution, source distribution, action item counts, duplicate clusters, top relationship clusters, recent activity
- expose both overview and drill-down endpoints

Acceptance criteria:
- no frontend-specific assumptions in service layer
- payloads are directly usable by charts/cards in later frontend work

### Step 6 — Finish category intelligence
Create:
- `app/services/category_intelligence.py`
- `app/services/category_merger.py`
- `app/services/category_analytics.py`

Do:
- compute merge candidates from embedding similarity and corpus overlap
- produce refinement recommendations
- separate analytics from mutation logic
- respect user category overrides over AI suggestions

Acceptance criteria:
- merge recommendations are explainable
- analytics endpoints avoid destructive changes

### Step 7 — Testing and ops hardening
Create:
- `tests/test_search.py`
- `tests/test_hybrid_search.py`
- `tests/test_relationships.py`
- `tests/test_timeline.py`
- `tests/test_insights.py`

Do:
- add fixtures and representative document corpus samples
- test disabled-Qdrant behavior
- test relationship idempotency
- test endpoint schemas
- add backfill command or script for embeddings and relationships

Acceptance criteria:
- `pytest` covers the new endpoints/services
- backfill process is documented and safe to rerun
