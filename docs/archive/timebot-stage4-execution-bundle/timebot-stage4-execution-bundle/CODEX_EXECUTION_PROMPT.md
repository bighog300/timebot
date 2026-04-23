# Codex Execution Prompt — Stage 4

You are implementing **Stage 4** for this repository.

## Objective
Build the real frontend application for the Document Intelligence Platform and close only the backend gaps required for the frontend to ship.

## Current repo reality
This repo already has a substantial backend in `app/`:
- FastAPI app and route registration in `app/main.py`
- documents routes
- categories routes
- upload route
- analysis routes
- queue routes
- search routes including semantic search and similar documents
- websocket routes
- models for `Connection`, `DocumentRelationship`, `SyncLog`, `ProcessingQueue`, and `DocumentVersion`

The repo also contains frontend documentation under `docs/`, including:
- `FRONTEND_TECH_SPEC.md`
- `FRONTEND_DEV_GUIDE.md`
- `UI_DESIGN_SPEC.md`
- `PHASE4_COMPLETE_EXECUTION.md`
- sample frontend config files in `docs/package.json`, `docs/vite.config.ts`, and `docs/tailwind.config.js`

However, the actual frontend app does **not** exist yet.

## Important instruction
Do **not** blindly implement the old Stage 4 docs as if all assumed APIs already exist.
First inspect the real backend code and align the frontend to current route and schema reality.

## Your process
1. Read `AGENTS.md` and follow it.
2. Inspect current backend routes, schemas, and models before editing.
3. Produce a short plan grouped by milestones.
4. Implement in small, reviewable batches.
5. After each milestone, run the relevant checks.
6. Keep a short running changelog in your responses.

## What to build

### Milestone 0 — Audit and bootstrap
- create `frontend/` as a Vite + React + TypeScript app
- use the frontend docs and sample config as a starting point
- configure Tailwind, React Router, React Query, and a typed API client
- add env-based API base URL configuration

### Milestone 1 — Application shell
Build:
- responsive layout
- header
- navigation/sidebar
- route container
- common UI primitives
- loading, empty, error, modal, toast, and skeleton patterns

### Milestone 2 — Documents and upload
Build:
- document browsing views (timeline plus at least one of grid/list)
- upload flow
- document detail view
- actions for update, favorite, archive, delete, reprocess
- display of summary, key points, tags, entities, action items, metadata

Use the existing backend routes wherever possible.

### Milestone 3 — Search
Build:
- keyword search UI using existing `/api/v1/search`
- semantic search UI using existing `/api/v1/search/semantic`
- suggestions using `/api/v1/search/suggestions`
- facets using `/api/v1/search/facets`
- similar documents view using `/api/v1/search/documents/{id}/similar`

### Milestone 4 — Live processing and queue UX
Build:
- queue stats widgets
- queue page or panel
- websocket client for `/api/v1/ws/all`
- live status updates for processing documents
- retry failed action

If websocket event payloads are underspecified, tighten the backend event contract.

### Milestone 5 — Categories and insights
Build:
- categories browsing page using existing categories route
- insights overview page

If insights collection endpoints do not exist, add minimal backend endpoints under `/api/v1/insights` to support:
- overview counts
- recent trends
- action item rollups
- tag/entity/category summaries

### Milestone 6 — Connections
The UI spec expects provider connections, but no connection routes currently exist in the reviewed route tree.

Add the minimum backend needed under `/api/v1/connections` and build a connections page that supports:
- listing configured providers
- showing status, authentication state, last sync, progress, counts
- triggering connect/disconnect/sync
- viewing sync history if implemented

Do not overengineer third-party auth flows if the repo is not ready. Ship usable local/stateful connection management first, and structure code so real OAuth callbacks can be added cleanly.

### Milestone 7 — Hardening
Add:
- unit tests for critical hooks/components
- E2E smoke tests for upload, search, and detail flows
- accessibility and responsive polish
- docs for local frontend run and build

## Constraints
- Keep API paths under `/api/v1`
- Prefer typed service modules over ad hoc fetch calls
- Do not rewrite working backend architecture without strong reason
- Keep changes coherent, minimal, and production-oriented
- If docs conflict with code, trust the code and update the frontend accordingly

## Deliverables
By the end, the repo should include:
- a real `frontend/` application
- frontend pages for dashboard/timeline, search, categories, insights, and connections
- document upload and detail flows
- real-time processing feedback
- any minimal backend additions required for connections/insights/relationships/timeline aggregation
- tests and updated README/setup instructions

## Definition of done
Stage 4 is complete when a user can:
- open the web app
- upload and browse documents
- watch processing progress live
- search by keyword and semantic mode
- inspect detail views and similar documents
- browse categories and insights
- manage connection states
- use the app on desktop and mobile
- build and test the frontend successfully

## Start now
Begin by:
1. auditing the real route tree and schema shapes
2. creating the frontend app scaffold
3. wiring a typed API layer to the existing backend
4. implementing the shell and documents flow first
