# Codex Execution Prompt — Complete Phase 3 for This Repo

You are working inside the repository root of `timebot-main`.

Your job is to **finish Phase 3: Search & Intelligence** based on the existing codebase, not to restart it from scratch.

## First, gather context
Read these files before making edits:
- `docs/MASTER_IMPLEMENTATION_PLAN.md`
- `docs/PHASE3_COMPLETE_EXECUTION.md`
- `app/services/search_service.py`
- `app/services/embedding_service.py`
- `app/api/v1/search.py`
- `app/models/document.py`
- `app/models/relationships.py`
- `app/workers/tasks.py`
- `app/services/category_discovery.py`

Then produce a short plan that lists:
1. what Phase 3 pieces already exist
2. what is missing
3. the exact implementation order you will follow

## Scope
Complete the remaining backend work for Phase 3 only.

Do **not** build the frontend.
Do **not** rewrite the app architecture.
Do **not** remove working endpoints unless replacing them with a compatible improvement.

## Existing state you must respect
This repo already has:
- lexical search service and API
- semantic search service and API via Qdrant
- relationship-related SQLAlchemy models
- Celery processing tasks
- category discovery service

The repo does **not** yet fully implement:
- hybrid search
- relationship detection and persistence flow
- timeline builder and timeline endpoints
- insights generator and insights endpoints
- category intelligence analytics/merge/refinement layer
- Phase 3 test coverage

## Required deliverables

### A. Harden lexical search
Add or refactor as needed to provide:
- robust query parsing
- safer and more explainable ranking
- better snippets/highlights
- search indexing helper(s) if needed
- preserved compatibility with current search endpoints

Potential files:
- `app/services/query_parser.py`
- `app/services/search_indexer.py`
- updates to `app/services/search_service.py`

### B. Add hybrid search
Implement a combined lexical + semantic search flow.

Requirements:
- create a service method for hybrid search
- expose a dedicated API endpoint
- normalize and merge scores from both systems
- deduplicate result sets by document id
- degrade gracefully when embedding/Qdrant is unavailable
- return useful score breakdown metadata for debugging

### C. Implement relationship detection
Create a relationship detection service that uses deterministic heuristics first.

Use a mix of:
- embedding similarity
- title/filename similarity
- tag overlap
- entity overlap
- date adjacency or follow-up patterns
- duplicate detection heuristics

Persist results into `DocumentRelationship`.
Add Celery task support and a safe backfill path.

### D. Implement timeline support
Create a timeline builder and API that can power a future frontend.

Requirements:
- events sourced from upload dates and extracted entity dates
- grouping by day/week/month
- filters by category/source/file type
- stable response schema
- sensible fallback when extracted dates are absent

### E. Implement insights API
Create dashboard-ready insight generation.

Include:
- document volume trends
- category/source distributions
- action item summaries
- duplicate clusters
- relationship summaries
- recent activity

### F. Finish category intelligence for Phase 3
Build backend-only category intelligence helpers.

Include:
- category analytics
- merge recommendations
- refinement suggestions based on corpus signals
- respect for user overrides over AI defaults

### G. Add tests and verification
Add test coverage for the new Phase 3 behavior.
At minimum cover:
- lexical search behavior
- hybrid search fallback behavior
- relationship persistence and idempotency
- timeline output shape
- insights output shape

If full tests are blocked by current project setup, add the most realistic tests possible and document the remaining verification steps clearly.

## Constraints
- Prefer small focused files over giant service classes.
- Keep type hints throughout.
- Reuse existing models and schemas where reasonable.
- Add new schemas when response shapes become nontrivial.
- Avoid breaking current routes.
- Be explicit about any new environment variables or dependencies.
- Keep all logic backend-only and Phase-3-scoped.

## Quality bar
Before finishing:
1. run tests if available
2. run any lightweight verification you can
3. summarize all changed files
4. list unresolved risks or follow-ups
5. confirm whether Phase 3 is now complete, and if not, what remains

## Output format at the end
Return:
- summary of completed work
- files changed
- tests/verification run
- known gaps
- next recommended step
