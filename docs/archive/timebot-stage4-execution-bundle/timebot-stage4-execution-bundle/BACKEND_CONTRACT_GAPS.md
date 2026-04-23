# Backend Contract Gaps for Stage 4

This file identifies backend work that must be completed or shimmed so the Stage 4 frontend can ship cleanly.

## 1. Connections management API

### Why this matters
The UI design and frontend tech spec assume a first-class Connections page, but there are no connection routes in `app/api/v1`.

### Required endpoints
Implement these under `/api/v1/connections`:
- `GET /connections` — list all configured connections
- `GET /connections/{id}` — get one connection
- `POST /connections/{provider}/connect` — start connect/auth flow or create local stub
- `POST /connections/{id}/disconnect` — disconnect provider
- `POST /connections/{id}/sync` — trigger sync
- `GET /connections/{id}/sync-logs` — recent sync log history
- `PATCH /connections/{id}` — update settings like `auto_sync`, `sync_interval`

### Minimum response shape
Use the existing `Connection` model fields where possible:
- `id`
- `type`
- `status`
- `display_name`
- `email`
- `last_sync_date`
- `last_sync_status`
- `sync_progress`
- `document_count`
- `total_size`
- `auto_sync`
- `sync_interval`
- `is_authenticated`

## 2. Insights API

### Why this matters
The Stage 4 docs assume an Insights page. The backend currently exposes document-level analysis, not collection-level insights.

### Required endpoints
Implement these under `/api/v1/insights`:
- `GET /insights/overview`
- `GET /insights/trends`
- `GET /insights/action-items`
- `GET /insights/entities`
- `GET /insights/categories`

### Minimum capabilities
- aggregate counts by category, source, type, status
- recent uploads trend
- surfaced action items from `Document.action_items`
- entity rollups from `Document.entities`
- top tags from `ai_tags` and `user_tags`

## 3. Relationship browsing API

### Why this matters
Stage 4 wants related documents and connection discovery, but the route tree does not expose relationship browsing APIs.

### Required endpoints
Implement under `/api/v1/relationships` or extend documents/search:
- `GET /documents/{id}/relationships`
- `GET /relationships/graph`
- optionally `POST /relationships/recompute`

### Minimum response shape
- source document id
- target document id
- relationship type
- confidence
- metadata

## 4. Timeline aggregation API

### Why this matters
You can build the timeline from paginated `GET /documents`, but a dedicated endpoint will keep the UI efficient as the collection grows.

### Optional but recommended endpoints
- `GET /timeline`
- `GET /timeline/buckets?granularity=day|week|month`
- `GET /timeline/stats`

### Minimum capabilities
- ordered document feed
- bucket counts by day/week/month
- optional filters by category/source/file_type/status

## 5. Search contract normalization

### Why this matters
The current search APIs are usable, but the frontend should not absorb route inconsistencies.

### What to do
Either:
1. keep current routes and normalize them in a frontend service layer, or
2. refine the backend contract to be cleaner and more consistent.

### Needed guarantees
- stable pagination fields
- consistent typing for facets
- predictable query/filter naming
- similar-document responses reusable by document detail view

## 6. Websocket event contract

### Why this matters
The websocket endpoints exist, but the frontend needs a stable event payload contract.

### Define and document
At minimum, emit a typed event envelope such as:
- `type`
- `document_id`
- `status`
- `message`
- `progress`
- `timestamp`
- `payload`

### Events to support
- queued
- processing_started
- extraction_completed
- analysis_completed
- embedding_completed
- relationship_completed
- failed
- completed

## 7. Document detail enrichment

### Why this matters
The document detail view is one of the core Stage 4 experiences.

### Recommended additions
Either expand `GET /documents/{id}` or add companion endpoints for:
- related/similar documents
- document versions/history
- queue history
- processing diagnostics
- thumbnail URLs / preview metadata

## 8. Authentication / provider handoff

If Stage 4 includes real third-party provider connection flows, backend support must include:
- provider callback routes
- token storage / refresh behavior
- connection status reporting
- failure states that the frontend can render clearly

## Shipping rule

Do not block the initial frontend release on every advanced backend endpoint.

Priority order:
1. documents, upload, search, queue, categories
2. websocket status
3. connections list + sync
4. insights overview
5. relationships and advanced timeline aggregation
