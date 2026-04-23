# AGENTS.md

## Mission
Complete Stage 4 for this repository by building the real frontend application and only the backend additions required for the UI to ship.

## Repository facts
- Backend is FastAPI under `app/`
- Current route prefixes are under `/api/v1`
- Existing route groups: `documents`, `categories`, `upload`, `analysis`, `queue`, `search`, `websocket`
- Frontend docs exist under `docs/`, but the actual frontend app does not yet exist
- Use the docs as guidance, but trust the current code over older speculative docs

## Non-negotiable rules
1. Read the current backend routes and schemas before editing.
2. Prefer implementing the frontend against existing routes instead of inventing new backend behavior.
3. Add backend routes only where the frontend cannot ship without them.
4. Keep changes incremental and verifiable.
5. After each milestone, run the relevant checks and summarize what changed.

## Priority order
1. frontend app bootstrap
2. app shell and shared primitives
3. documents and upload
4. search and semantic search
5. websocket/queue status
6. categories and insights
7. connections
8. tests and polish

## Required behavior
- Before making broad edits, write a short implementation plan in the task log/response.
- Keep service modules typed and small.
- Do not create giant unstructured files.
- Reuse backend schema shapes wherever practical.
- Prefer clear loading/error states over silent failures.

## Frontend structure target
Create a real `frontend/` app with at least:
- `src/app`
- `src/components`
- `src/features`
- `src/pages` or `src/views`
- `src/services`
- `src/hooks`
- `src/store`
- `src/types`
- `src/lib`
- `src/utils`
- `tests`

## Backend additions allowed
Only add backend work for:
- connections management routes
- insights overview routes
- relationship browsing routes
- timeline aggregation helpers if the UI needs them
- websocket event-contract cleanup

## Commands to prefer
Frontend:
- `npm install`
- `npm run dev`
- `npm run type-check`
- `npm run lint`
- `npm run test`
- `npm run build`

Backend:
- run the existing backend locally without changing unrelated architecture
- keep API paths under `/api/v1`

## Done definition
Done means:
- frontend exists and runs
- primary Stage 4 pages are implemented
- UI works with real backend data
- required backend contract gaps are closed
- tests and build pass
