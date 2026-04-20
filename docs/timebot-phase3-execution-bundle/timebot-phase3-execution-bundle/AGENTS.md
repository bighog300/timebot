# AGENTS.md

## Repository purpose
Backend for an AI-powered document intelligence platform built with FastAPI, SQLAlchemy, Celery, Redis, PostgreSQL, and Qdrant.

## Current objective
Complete **Phase 3: Search & Intelligence** without starting frontend implementation work.

## Important directories
- `app/api/v1/` — FastAPI route modules
- `app/models/` — SQLAlchemy models
- `app/schemas/` — Pydantic request/response schemas
- `app/services/` — business logic and AI/search services
- `app/workers/` — Celery tasks
- `docs/` — implementation plans and execution docs

## Ground rules
1. Do not invent infrastructure that is not already compatible with the current stack.
2. Prefer incremental refactors over large rewrites.
3. Keep API shapes stable unless a schema improvement is required.
4. Preserve current behavior for existing endpoints wherever possible.
5. When adding a new Phase 3 feature, also add tests or at minimum a clear validation path.
6. Avoid frontend work; Phase 4 is out of scope.
7. Keep fallback behavior explicit when optional services like Qdrant are unavailable.

## What done means for this task
- lexical search is hardened
- hybrid search exists
- relationships are detected and persisted
- timeline and insights endpoints exist
- category intelligence is completed enough for Phase 3 scope
- tests and/or validation commands are added
- docs updated where necessary

## How to work
1. Read `docs/MASTER_IMPLEMENTATION_PLAN.md` and `docs/PHASE3_COMPLETE_EXECUTION.md`.
2. Inspect existing implementations before adding new files.
3. Produce a short execution plan before editing.
4. Implement in small coherent commits/patches.
5. Run relevant tests or verification commands after each major step.
6. End with a concise summary of what changed, what remains, and how it was verified.
