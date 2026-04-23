# Stage 4 Workplan

## Goal
Build a production-ready React frontend for the existing backend and close the minimum backend gaps required for the UI to ship.

## Delivery strategy
Implement Stage 4 in milestones. Each milestone should end with:
- code committed
- lint and type-check passing
- targeted tests added
- manual smoke path verified

## Milestone 0 — Repo and contract audit
- confirm current backend routes against docs
- generate frontend API contract map
- identify Phase 3 outputs that Stage 4 depends on
- create `frontend/` app and basic tooling

### Exit criteria
- `frontend/` exists
- app runs locally
- API base URL is configurable
- route inventory is documented in code comments or docs

## Milestone 1 — Frontend foundation
- initialize Vite + React + TypeScript app
- add Tailwind and theme tokens
- set up React Router
- set up React Query
- set up Zustand stores
- create app shell
- create core primitives: button, input, card, modal, toast, skeleton, tabs, tooltip

### Exit criteria
- app shell renders
- navigation works
- no hardcoded API URLs
- dark theme / base theme applied

## Milestone 2 — Documents and upload
- create timeline/grid/list document browsing
- create upload workflow
- create document detail drawer/page
- support update, favorite, archive, delete, reprocess actions
- render key metadata, summary, key points, action items, entities, tags

### Exit criteria
- user can upload a document and see it appear
- user can open a detail view
- user can reprocess, favorite, archive, and delete from the UI

## Milestone 3 — Search experience
- implement search page
- keyword and semantic modes
- facets and filters
- suggestions and popular searches
- similar documents section

### Exit criteria
- user can run keyword search
- user can run semantic search
- facets and filters narrow results correctly
- similar docs open from detail view

## Milestone 4 — Queue and live processing UX
- implement queue dashboard widgets
- connect websocket client to `/api/v1/ws/all`
- add live processing progress and status badges
- auto-refresh affected documents when processing completes
- surface retry failed action

### Exit criteria
- upload or reprocess visibly changes status live
- queue stats and health render
- failed documents can be retried from UI

## Milestone 5 — Categories and insights
- build categories browser
- build insights overview dashboard
- render category counts, trends, action items, top tags/entities
- add placeholder states if advanced endpoints are not yet available

### Exit criteria
- categories page is usable
- insights overview is populated from real API data or explicit shim endpoints

## Milestone 6 — Connections
- add backend connection routes if missing
- build connections page
- render status, last sync, progress, document counts
- trigger connect/disconnect/sync actions
- show sync logs/history if available

### Exit criteria
- user can see all providers
- sync state is observable
- connection failures are visible and recoverable

## Milestone 7 — Hardening and test coverage
- responsive polish
- accessibility pass
- error handling pass
- unit tests and E2E tests
- production build optimization
- docs for local run and deployment

### Exit criteria
- build passes
- tests pass
- manual smoke checklist passes on desktop and mobile widths

## Recommended implementation order inside the frontend
1. app shell
2. API client and types
3. documents list + detail
4. upload
5. search
6. websocket queue status
7. categories
8. insights
9. connections
10. polish and tests

## Scope control rules
- ship with existing backend contracts when possible
- add backend endpoints only when UI-critical
- do not overbuild provider auth before the connections page can at least render local/mock-safe states
- prefer small, typed service modules over giant general-purpose clients
