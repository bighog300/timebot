# Timebot — Phased Completion Plan for Codex

> Drop this file into your repo root as `CODEX_PLAN.md`.  
> Each sprint is a single Codex task. Paste the sprint block into Codex's task field exactly as written.  
> Work top-to-bottom. Do not start a sprint until the previous one's definition of done is met.

---

## How to use this plan

1. Open your GitHub repo in Codex.
2. Copy the **Codex prompt** for the current sprint (the block starting with `You are working...`).
3. Paste it as the Codex task. Codex will open a PR against `main`.
4. Review the PR, merge when green, then move to the next sprint.

Codex must have access to the following secrets in your repo:
- `ANTHROPIC_API_KEY` — for AI analysis tests
- `DATABASE_URL` — PostgreSQL test DB (can be SQLite override in CI)
- `REDIS_URL` — Redis for Celery tests (can be fakeredis in CI)

---

## Current state (April 2026)

| Area | Status |
|---|---|
| FastAPI backend, models, DB | ✅ Complete |
| Document upload + processing | ✅ Complete |
| Keyword + semantic + hybrid search | ✅ Complete |
| Celery worker + queue API | ✅ Complete |
| React frontend scaffold (8 pages) | ✅ Complete |
| WebSocket live events | ✅ Complete |
| AI analysis (summary, tags, entities) | ✅ Complete |
| Insights service + timeline | ✅ Partial |
| Connector routes (no real OAuth) | ⚠️ Stubs only |
| AI confidence / review queue UI | ❌ Missing |
| Alembic migrations | ❌ Missing |
| Authentication / auth guards | ❌ Missing |
| .gitignore (pycache, .env) | ❌ Missing |
| Test coverage (backend + frontend) | ❌ Thin |

**Start here: Sprint 0 (housekeeping) before any feature work.**

---

## Sprint 0 — Repo hygiene & critical fixes

**Effort:** Small (1–2 hours)  
**Unlocks:** Everything. These are blockers.

### Codex prompt

```
You are working inside the Timebot repository.

## Mission
Fix four critical repo hygiene issues before any feature work begins.

## Tasks

### 1. Add .gitignore
Create a .gitignore at the repo root covering:
- __pycache__/ and *.pyc
- .env (but not .env.example)
- data/ (runtime storage)
- frontend/node_modules/ and frontend/dist/
- .pytest_cache/ and .coverage
- *.egg-info/

Then run: git rm -r --cached **/__pycache__ and git rm -r --cached **/*.pyc
(Note: Codex should stage these deletions as part of the commit, not run git commands directly — add the removal to the commit by including the files in the deletion list.)

### 2. Fix the AI model string
In app/config.py, change:
  AI_MODEL: str = "claude-sonnet-4-6"
to:
  AI_MODEL: str = "claude-sonnet-4-20250514"

This is the correct Anthropic API model string. The current value causes a runtime error on every AI analysis call.

### 3. Initialise Alembic migrations
- Run: alembic init migrations
- Edit migrations/env.py to import app.models and point at settings.DATABASE_URL
- Generate the initial migration: alembic revision --autogenerate -m "initial schema"
- In app/db/base.py, replace the create_all() call in init_db() with a comment explaining that Alembic now manages schema, but keep create_all() as a fallback for test environments where ALEMBIC_SKIP=true is set
- Update the README.md Database Migrations section to use: alembic upgrade head

### 4. Update stale planning doc
In docs/timebot-stage4-execution-bundle/timebot-stage4-execution-bundle/STAGE4_GAP_REPORT.md, prepend the following at the top of the file:

> **STATUS: RESOLVED (April 2026)**
> The frontend described as missing in this report has since been implemented.
> See frontend/ for the React + TypeScript application.
> This document is kept for historical reference only.

## Definition of done
- .gitignore exists and __pycache__ files are no longer tracked
- AI_MODEL value is "claude-sonnet-4-20250514"
- migrations/ directory exists with an initial migration file
- STAGE4_GAP_REPORT.md has the RESOLVED header
- CI passes
```

---

## Sprint 1 — Backend test foundation

**Effort:** Medium (3–4 hours)  
**Unlocks:** Confident iteration on all future sprints.

### Codex prompt

```
You are working inside the Timebot repository.

## Mission
Build a proper backend test suite covering the critical runtime paths. Tests must run in CI without external services (use SQLite + fakeredis or mocks).

## Context
Currently there is one test file: tests/test_phase3_services.py (195 lines, unit tests with fake DB objects). There are no API-level integration tests and no upload/processing flow tests.

## Tasks

### 1. Test infrastructure
- Add a conftest.py that creates a temporary SQLite database and overrides the get_db() dependency
- Add pytest fixtures for: a test client (FastAPI TestClient), a seeded document, a seeded category
- Add a requirements-test.txt or extend requirements.txt with: pytest-cov, httpx (for async test client)
- Update .github/workflows/ci-backend.yml to run: pytest tests/ --cov=app --cov-report=term-missing

### 2. Health and root endpoint tests (tests/test_api_health.py)
- GET /health returns 200 with status=healthy and database field
- GET / returns 200 with message and docs fields

### 3. Upload and document lifecycle tests (tests/test_api_documents.py)
- POST /api/v1/upload with a valid PDF returns 200 and a document with processing_status=queued
- POST /api/v1/upload with an unsupported file type returns 400
- GET /api/v1/documents returns a list
- GET /api/v1/documents/{id} returns the document
- PUT /api/v1/documents/{id} updates a field
- DELETE /api/v1/documents/{id} removes the document
- POST /api/v1/documents/{id}/reprocess returns 200

For upload tests: use a small in-memory bytes object as the file. Mock the Celery task (mock patch process_document_task.apply_async) so tests do not require a running worker.

### 4. Search endpoint tests (tests/test_api_search.py)
- POST /api/v1/search with query= returns a SearchResponse shape
- POST /api/v1/search/semantic with query= returns a SemanticSearchResponse shape
- GET /api/v1/search/suggestions?q=test returns a list
- GET /api/v1/search/facets returns a dict

### 5. Queue endpoint tests (tests/test_api_queue.py)
- GET /api/v1/queue/stats returns expected keys
- GET /api/v1/queue/items returns a list
- POST /api/v1/queue/retry-failed returns 200

## Constraints
- All tests must pass without a running PostgreSQL, Redis, or Qdrant instance
- Use SQLite (via DATABASE_URL=sqlite:///./test.db in the test environment) and mock external services
- Do not suppress test failures — fix the underlying issues if tests reveal bugs

## Definition of done
- pytest tests/ exits 0
- Coverage is at least 40% on the app/ package
- CI workflow runs the test suite and reports coverage
```

---

## Sprint 2 — AI confidence & review queue (backend)

**Effort:** Medium (3–4 hours)  
**Unlocks:** Sprint 3 (review queue UI), Phase 4 success gate.

### Codex prompt

```
You are working inside the Timebot repository.

## Mission
Add the confidence and review state layer to AI outputs so documents can be reviewed, approved, or overridden by the user.

## Context
Documents currently have: summary, key_points, entities, action_items, ai_tags — all set by AI analysis with no review state. The plan requires a reviewable AI output lifecycle.

## Tasks

### 1. Extend the Document model (app/models/document.py)
Add fields:
- ai_confidence: Float, nullable, default None (0.0–1.0, set by AI analyzer)
- review_status: String, nullable, default "pending" — enum: pending | approved | rejected | edited
- reviewed_at: DateTime with timezone, nullable
- reviewed_by: String, nullable (placeholder for future user ID)
- override_summary: Text, nullable (user-edited summary, takes precedence over summary in responses)
- override_tags: JSONB/JSON, nullable (user-edited tags)

Generate a new Alembic migration: alembic revision --autogenerate -m "add ai confidence and review fields"

### 2. Update the AI analyzer (app/services/ai_analyzer.py)
After parsing the Claude response, compute a confidence score:
- Start at 1.0
- Subtract 0.15 if summary is empty or under 20 words
- Subtract 0.1 for each of key_points, entities, ai_tags that is empty
- Subtract 0.2 if action_items is empty
- Clamp to [0.0, 1.0]
Set document.ai_confidence = computed score after analysis.

Also set document.review_status = "pending" when ai_confidence < 0.75, else "approved".

### 3. Update document schemas (app/schemas/document.py)
Add to DocumentResponse: ai_confidence, review_status, reviewed_at, override_summary, override_tags.
The frontend should display override_summary if set, else summary. Expose both so the UI can show the distinction.

### 4. Add review endpoints (app/api/v1/documents.py)
POST /api/v1/documents/{id}/review
Request body: { "action": "approve" | "reject" | "edit", "override_summary": str | null, "override_tags": list | null }
- Sets review_status, reviewed_at
- If action=edit, stores override_summary and/or override_tags
- Returns updated DocumentResponse

GET /api/v1/documents/review-queue
Query params: status=pending (default), limit=50, skip=0
Returns documents filtered by review_status, ordered by ai_confidence ascending (lowest confidence first)

### 5. Update the queue stats endpoint (app/api/v1/queue.py)
Add to the stats response: pending_review_count (documents with review_status=pending).

### 6. Add tests (tests/test_api_review.py)
- POST /review with action=approve sets review_status=approved
- POST /review with action=edit stores override values
- GET /review-queue returns only pending documents
- ai_confidence is set after a document is processed (mock the AI call)

## Definition of done
- Migration generated and applied in CI (alembic upgrade head in test setup)
- Review endpoints return correct data
- pending_review_count appears in queue stats
- Tests pass
```

---

## Sprint 3 — Review queue UI (frontend)

**Effort:** Medium (3–4 hours)  
**Unlocks:** Phase 4 complete success gate.

### Codex prompt

```
You are working inside the Timebot repository.

## Mission
Build the review queue UI so users can triage low-confidence AI outputs from the frontend.

## Context
The backend now has:
- GET /api/v1/documents/review-queue — returns pending documents ordered by confidence
- POST /api/v1/documents/{id}/review — approve / reject / edit
- queue stats now include pending_review_count

The frontend is in frontend/src/ (React + TypeScript + TanStack Query + Tailwind).

## Tasks

### 1. Extend the API client (frontend/src/services/api.ts)
Add:
- getReviewQueue(): Promise<Document[]> — GET /documents/review-queue
- reviewDocument(id: string, action: 'approve'|'reject'|'edit', overrideSummary?: string, overrideTags?: string[]): Promise<Document> — POST /documents/{id}/review

### 2. Extend the Document type (frontend/src/types/api.ts)
Add to Document:
- ai_confidence: number | null
- review_status: 'pending' | 'approved' | 'rejected' | 'edited' | null
- override_summary: string | null
- override_tags: string[] | null

### 3. Create ReviewQueuePage (frontend/src/pages/ReviewQueuePage.tsx)
Layout:
- Page header: "Review queue" with a count badge (pending_review_count from queue stats)
- If queue is empty: EmptyState with message "All AI outputs are approved"
- List of ReviewQueueCard components, ordered by confidence ascending

ReviewQueueCard shows:
- Document filename and file type badge
- Confidence score as a coloured bar: red <0.5, amber 0.5–0.74, green ≥0.75
- AI-generated summary (or placeholder if empty)
- AI tags as pill badges
- Three action buttons: Approve (green), Reject (red), Edit (outlined)
- Edit opens an inline textarea pre-filled with the current summary and a tags input, with a Save button that calls reviewDocument with action=edit

On approve or reject, remove the card from the list with a fade-out transition.

### 4. Add the route (frontend/src/app/router.tsx)
Add: /review → ReviewQueuePage

### 5. Update the navigation (frontend/src/components/layout/AppShell.tsx)
Add a "Review" nav item with a red badge showing pending_review_count when > 0.
Source the count from the queue stats query that already runs in the app.

### 6. Update QueuePage (frontend/src/pages/QueuePage.tsx)
Add a "Pending review" stat card using pending_review_count from queue stats.
Add a link/button: "Go to review queue →"

### 7. Add frontend tests (frontend/tests/review-queue.test.tsx)
- ReviewQueuePage renders EmptyState when queue is empty
- ReviewQueueCard renders confidence bar at correct colour for low/mid/high confidence
- Approve button calls api.reviewDocument with action=approve

## Definition of done
- /review route renders and fetches real data
- Approve/reject removes the card from the list
- Edit flow saves override and updates the card
- Nav badge shows pending count
- Frontend tests pass (npm run test)
- npm run type-check and npm run build succeed
```

---

## Sprint 4 — Connector OAuth foundation (backend)

**Effort:** Large (5–6 hours)  
**Unlocks:** Phase 3 success gate, real data ingestion.

### Codex prompt

```
You are working inside the Timebot repository.

## Mission
Replace the connector stub routes with a real OAuth provider framework and implement Google Drive as the first working connector.

## Context
The Connection model and basic CRUD routes already exist in:
- app/models/relationships.py (Connection, SyncLog)
- app/api/v1/connections.py (list, connect, disconnect, sync, sync-logs)

Currently connect/disconnect/sync are no-ops that return placeholder responses. There is no OAuth flow, no token storage, and no actual file ingestion.

## Tasks

### 1. Provider abstraction (app/services/connectors/base.py)
Create an abstract BaseConnector class with:
- get_auth_url(connection_id: str) -> str  — returns OAuth URL for this provider
- handle_callback(code: str, state: str) -> dict  — exchanges code for tokens, returns token dict
- sync(db: Session, connection: Connection) -> SyncResult  — fetches new files and queues them for processing
- A SyncResult dataclass: files_found, files_queued, files_skipped, errors

### 2. Google Drive connector (app/services/connectors/gdrive.py)
Implement BaseConnector for Google Drive:
- get_auth_url: construct Google OAuth2 URL with scopes: drive.readonly
  Use GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET from settings
  Redirect URI: {APP_BASE_URL}/api/v1/connections/gdrive/callback
- handle_callback: exchange code for access+refresh tokens using requests to accounts.google.com/o/oauth2/token
  Store encrypted tokens in connection.sync_state (use Fernet from cryptography with ENCRYPTION_KEY from settings)
- sync: call Drive API files.list, download files matching ALLOWED_FILE_TYPES, save to storage, queue via process_document_task
  Track processed file IDs in connection.sync_state to avoid duplicates

### 3. Add settings (app/config.py)
Add:
- GOOGLE_CLIENT_ID: str = ""
- GOOGLE_CLIENT_SECRET: str = ""
- APP_BASE_URL: str = "http://localhost:8000"
- ENCRYPTION_KEY: str = ""  (Fernet key — generate with Fernet.generate_key())

### 4. Update connection routes (app/api/v1/connections.py)
- GET /connections/{type}/auth-url — returns {"url": "..."} for starting OAuth
- GET /connections/{type}/callback?code=...&state=... — OAuth callback, calls handle_callback, updates connection to status=connected
- POST /connections/{type}/sync — calls connector.sync(), updates SyncLog with results
- POST /connections/{type}/disconnect — clears sync_state and tokens, sets status=disconnected

Register a provider registry dict: {"gdrive": GDriveConnector()}, return 422 for unknown providers.
Return 501 with {"detail": "Provider not configured"} if GOOGLE_CLIENT_ID is empty.

### 5. Update .env.example
Add:
  GOOGLE_CLIENT_ID=
  GOOGLE_CLIENT_SECRET=
  APP_BASE_URL=http://localhost:8000
  ENCRYPTION_KEY=   # generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

### 6. Update requirements.txt
Add: cryptography>=42.0.0

### 7. Add tests (tests/test_connectors.py)
- GET /connections/{type}/auth-url returns a URL string (mock settings with a fake client ID)
- GET /connections/gdrive/callback with a mocked token exchange updates connection to connected
- POST /connections/unknown/sync returns 422
- GDriveConnector.sync with a mocked Drive API creates documents and SyncLog entries
- POST /connections/{type}/disconnect clears status

## Definition of done
- auth-url endpoint returns a real Google OAuth URL when GOOGLE_CLIENT_ID is configured
- callback endpoint exchanges code and updates connection status
- sync endpoint calls the Drive API and queues discovered files (mocked in tests)
- 501 returned cleanly when provider is not configured
- Tests pass
- cryptography added to requirements
```

---

## Sprint 5 — Connector UI (frontend)

**Effort:** Medium (3–4 hours)  
**Unlocks:** Users can connect and sync Google Drive from the UI.

### Codex prompt

```
You are working inside the Timebot repository.

## Mission
Update the ConnectionsPage to use the real OAuth flow and sync actions from Sprint 4.

## Context
frontend/src/pages/ConnectionsPage.tsx already exists and renders provider cards.
The backend now has working endpoints:
- GET /connections/{type}/auth-url
- GET /connections/{type}/callback (handled by backend, redirect target)
- POST /connections/{type}/sync
- POST /connections/{type}/disconnect
- GET /connections/{type}/sync-logs

## Tasks

### 1. Extend api.ts
Add:
- getAuthUrl(type: string): Promise<{url: string}> — GET /connections/{type}/auth-url
- getSyncLogs(type: string): Promise<SyncLog[]> — GET /connections/{type}/sync-logs (already in api.ts, verify it exists)

### 2. Update Connection type (frontend/src/types/api.ts)
Ensure Connection includes: id, type, display_name, status, email, last_sync_date, last_sync_status, sync_progress, document_count, is_authenticated.
Add SyncLog type if missing: id, connection_id, started_at, completed_at, status, files_found, files_queued, error_message.

### 3. Rewrite ConnectionsPage (frontend/src/pages/ConnectionsPage.tsx)
Each provider card should show:
- Provider icon (use a simple letter avatar: G for Google Drive, etc.)
- Display name and status badge: connected (green), disconnected (gray), error (red), syncing (amber with spinner)
- If connected: email, last sync date, document count, last sync status
- If connected: "Sync now" button (calls syncProvider, shows loading) and "Disconnect" button
- If disconnected: "Connect" button — calls getAuthUrl then does window.location.href = url to start OAuth
- If status=syncing: show sync_progress as a progress bar

After sync completes, invalidate the connections query so the card refreshes.

### 4. Add SyncLogDrawer component (frontend/src/components/SyncLogDrawer.tsx)
A slide-in panel (or expandable section under the card) showing the last 10 sync logs for a connection.
Triggered by a "View history" link on connected cards.
Each log row: date, status badge, files found/queued counts, error message if any.

### 5. Update AppShell navigation
If any connection has status=error, show a warning indicator on the Connections nav item.

### 6. Add frontend tests (frontend/tests/connections-page.test.tsx)
- Disconnected card renders Connect button
- Connect button calls getAuthUrl and redirects
- Connected card renders Sync now and Disconnect buttons
- SyncLogDrawer renders log entries

## Definition of done
- Connect button initiates OAuth redirect
- Connected card shows real sync data
- Sync now triggers a sync and refreshes the card
- Disconnect clears connection state
- History drawer shows sync logs
- Tests pass, type-check and build succeed
```

---

## Sprint 6 — Actionable insights dashboard (backend + frontend)

**Effort:** Medium (3–4 hours)  
**Unlocks:** Phase 5 success gate.

### Codex prompt

```
You are working inside the Timebot repository.

## Mission
Make the insights dashboard action-oriented: surface what needs attention rather than passive counts.

## Context
- Backend: app/services/insights_service.py has build_dashboard() returning volume_trends, category_distribution, etc.
- Backend: GET /api/v1/insights/overview, /trends, /rollups already exist
- Frontend: frontend/src/pages/InsightsPage.tsx exists but is basic

## Tasks

### 1. Extend insights_service.py
Add to the build_dashboard() return dict:
- needs_review: int — count of documents with review_status=pending
- low_confidence: int — count where ai_confidence < 0.5
- untagged: int — count where ai_tags is empty or null
- failed_processing: int — count with processing_status=failed
- action_items_total: int — total action items across all documents (sum of len(action_items))
- recent_uploads: int — documents uploaded in the last lookback_days

### 2. Add an /api/v1/insights/actions endpoint (app/api/v1/insights.py)
GET /api/v1/insights/actions
Returns: { needs_review, low_confidence, untagged, failed_processing, action_items_total, recent_uploads }
Each field also includes a direct link hint: { count: int, label: str, href: str }
Example: needs_review: { count: 12, label: "Documents pending AI review", href: "/review" }

### 3. Add InsightsResponse schema update (app/schemas/intelligence.py)
Extend InsightsResponse with the action queue fields.

### 4. Add tests (tests/test_api_insights.py)
- GET /insights/overview returns expected keys
- GET /insights/actions returns correct counts for seeded data
- needs_review count matches documents with review_status=pending

### 5. Rewrite InsightsPage (frontend/src/pages/InsightsPage.tsx)
Top section — Action queue cards (2-column grid on desktop, 1-column on mobile):
- Needs review (red badge if > 0) — link to /review
- Low confidence — link to /review?filter=low
- Failed processing — link to /documents?status=failed
- Untagged documents — link to /documents?filter=untagged

Middle section — Trends chart:
- Use the existing /insights/trends data
- Render a simple bar chart using Chart.js showing document uploads by day over the lookback period
- Add a "Last 7 days / 30 days / 90 days" toggle that re-fetches with lookback_days param

Bottom section — Distribution:
- Category distribution as a horizontal bar chart (top 8 categories by count)
- Source distribution as a small donut or pill list

### 6. Add frontend tests (frontend/tests/insights-page.test.tsx)
- Action queue cards render with correct counts
- Needs review card links to /review
- Trend toggle changes lookback_days param

## Definition of done
- /insights/actions returns action-queue data
- InsightsPage shows action-oriented cards that link to relevant pages
- Trend chart renders from real data
- Tests pass, type-check and build succeed
```

---

## Sprint 7 — Authentication (backend)

**Effort:** Large (5–6 hours)  
**Unlocks:** Phase 6 success gate. Required before any shared/production deployment.

### Codex prompt

```
You are working inside the Timebot repository.

## Mission
Add JWT-based authentication. All API endpoints except /health, /docs, and the OAuth callback must require a valid token.

## Tasks

### 1. Add User model (app/models/user.py)
Fields: id (UUID), email (unique), hashed_password, full_name, is_active (bool, default True), created_at, updated_at.
Create Alembic migration.

### 2. Add auth utilities (app/core/security.py)
- hash_password(password: str) -> str using passlib[bcrypt]
- verify_password(plain: str, hashed: str) -> bool
- create_access_token(subject: str, expires_delta: timedelta) -> str using python-jose
- decode_token(token: str) -> dict

Add to settings: SECRET_KEY (required, no default), ACCESS_TOKEN_EXPIRE_MINUTES: int = 60*24 (24 hours), ALGORITHM: str = "HS256"

### 3. Auth routes (app/api/v1/auth.py)
POST /api/v1/auth/register — { email, password, full_name } → creates user, returns token
POST /api/v1/auth/login — { email, password } → returns { access_token, token_type }
GET /api/v1/auth/me — returns current user (requires token)

### 4. Update deps.py (app/api/deps.py)
Add:
- get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User
  Decodes token, fetches user, raises 401 if invalid or inactive.
- Optional: get_optional_user (returns None if no token, for public endpoints)

### 5. Protect all existing routes
In app/main.py (or per-router), add a dependency on get_current_user for all routers EXCEPT:
- GET /health
- GET /
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- GET /api/v1/connections/*/callback (OAuth redirect target)

### 6. Add to requirements.txt
- python-jose[cryptography]>=3.3.0
- passlib[bcrypt]>=1.7.4

### 7. Update .env.example
Add: SECRET_KEY=   # generate with: openssl rand -hex 32

### 8. Add tests (tests/test_api_auth.py)
- POST /auth/register creates user and returns token
- POST /auth/login with correct credentials returns token
- POST /auth/login with wrong password returns 401
- GET /documents without token returns 401
- GET /documents with valid token returns 200
- GET /health without token returns 200 (public)

## Definition of done
- Register and login return valid JWTs
- All non-public endpoints return 401 without a token
- Tests pass
- No existing passing tests broken (update fixtures to include auth header)
```

---

## Sprint 8 — Auth UI & frontend guards

**Effort:** Medium (3–4 hours)  
**Unlocks:** Users can register, log in, and be redirected on session expiry.

### Codex prompt

```
You are working inside the Timebot repository.

## Mission
Add login/register pages and protect all frontend routes behind authentication.

## Context
Backend now has: POST /auth/register, POST /auth/login, GET /auth/me returning JWT tokens.

## Tasks

### 1. Auth store (frontend/src/store/authStore.ts)
Using Zustand (already in package.json or add it):
- State: token: string | null, user: { email, full_name } | null
- Actions: setToken(token), setUser(user), logout() (clears token + user)
- Persist token to localStorage under key "timebot_token"

### 2. Extend api client (frontend/src/services/http.ts)
Add a request interceptor that attaches Authorization: Bearer {token} header from the auth store if a token exists.
Add a response interceptor that calls authStore.logout() and redirects to /login on 401 responses.

### 3. Extend api.ts
Add:
- register(email: string, password: string, fullName: string): Promise<{access_token: string}>
- login(email: string, password: string): Promise<{access_token: string}>
- getMe(): Promise<{email: string, full_name: string}>

### 4. LoginPage (frontend/src/pages/LoginPage.tsx)
- Email and password inputs
- Submit calls api.login(), stores token via authStore.setToken(), redirects to /documents
- "Don't have an account? Register" link
- Show error message on 401

### 5. RegisterPage (frontend/src/pages/RegisterPage.tsx)
- Email, password, full name inputs
- Submit calls api.register(), stores token, redirects to /documents
- "Already have an account? Login" link

### 6. ProtectedRoute component (frontend/src/components/ProtectedRoute.tsx)
Wraps any route. If authStore.token is null, redirects to /login. Otherwise renders the child.

### 7. Update router.tsx
- Add public routes: /login → LoginPage, /register → RegisterPage
- Wrap all existing routes (/, /documents, /search, /queue, /review, /categories, /insights, /connections) in ProtectedRoute

### 8. Update AppShell
Add a user menu in the header: show user email, a "Logout" button that calls authStore.logout() and redirects to /login.

### 9. On app load (frontend/src/main.tsx or App.tsx)
If a stored token exists, call api.getMe() to validate it. If getMe() returns 401, clear the token.

### 10. Add frontend tests
- LoginPage renders email/password fields
- Successful login stores token and redirects
- ProtectedRoute redirects to /login when no token
- Logout clears token and redirects

## Definition of done
- Unauthenticated users land on /login
- Login and register work end-to-end with the real backend
- 401 responses from the API trigger logout and redirect
- User email shown in header
- Tests pass, type-check and build succeed
```

---

## Sprint 9 — Final hardening & release readiness

**Effort:** Medium (3–4 hours)  
**Unlocks:** Production deployment. Phase 6 complete.

### Codex prompt

```
You are working inside the Timebot repository.

## Mission
Final hardening pass: tighten error handling, add E2E smoke tests, fix the README, and prepare for production deployment.

## Tasks

### 1. Error handling audit (backend)
Walk every router file (documents, search, upload, analysis, queue, insights, connections, auth).
For any endpoint that can raise an unhandled exception:
- Wrap in try/except
- Log the error with logger.error("...", exc_info=True)
- Return a JSON HTTPException with a safe client-facing message (no raw stack traces)

Add a global exception handler in app/main.py using @app.exception_handler(Exception) that returns {"detail": "An unexpected error occurred"} with status 500.

### 2. CORS tightening
Update app/main.py: change the ALLOWED_ORIGINS default in .env.example from * to:
  ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
Document in .env.example that production should set this to the real frontend domain.

### 3. Frontend E2E smoke tests (frontend/tests/e2e/smoke.sh)
Update the existing smoke.sh to test the full authenticated flow:
- Register a test user
- Login and extract token
- Upload a test document
- Poll GET /documents until processing_status != queued (max 30s)
- Run a search
- Check /insights/actions returns JSON
- Assert all steps return expected HTTP codes

### 4. Frontend: network error handling
In frontend/src/services/http.ts, add a response interceptor that:
- On network error (no response): shows a toast "Connection lost — check your network"
- On 500: shows a toast "Server error — please try again"

Add a Toast context/component to AppShell if one does not already exist.

### 5. README overhaul
Rewrite README.md to be clean and in order:
1. Project name and one-sentence description
2. Screenshot or architecture diagram placeholder
3. Prerequisites: Docker, Node 20, Python 3.11, Anthropic API key
4. Quick start (Docker Compose, 4 steps)
5. Local development: backend (uvicorn) and frontend (npm run dev) separately
6. Environment variables table (all keys, descriptions, required/optional)
7. Architecture section (the existing diagram, corrected paths)
8. Running tests: pytest and npm run test
9. Database migrations: alembic upgrade head
10. Deployment notes
11. Contributing and License

Remove all "yourusername/your-repo-name" placeholder strings.

### 6. docker-compose production hardening
In docker-compose.yml:
- Set ALLOWED_ORIGINS to use the APP_BASE_URL variable
- Add a healthcheck to the app service using GET /health
- Remove flower from the default compose (move to docker-compose.dev.yml)

### 7. Final test run
Ensure: pytest tests/ passes, npm run test passes, npm run build succeeds, npm run type-check has 0 errors.

## Definition of done
- No unhandled exceptions escape to clients (500s return safe JSON)
- E2E smoke script passes against a running stack
- README is clean and accurate with no placeholder strings
- CI is green across all 6 workflows
- npm run build produces a dist/ with 0 TypeScript errors
```

---

## Phase completion map

| Sprint | Phase gate unlocked |
|---|---|
| 0 — Repo hygiene | Unblocks all future sprints |
| 1 — Backend tests | Engineering baseline |
| 2 — AI confidence (backend) | Phase 4 backend ✅ |
| 3 — Review queue (frontend) | Phase 4 complete ✅ |
| 4 — Connector OAuth (backend) | Phase 3 complete ✅ |
| 5 — Connector UI (frontend) | Phase 3 UI ✅ |
| 6 — Insights dashboard | Phase 5 complete ✅ |
| 7 — Auth backend | Phase 6 backend ✅ |
| 8 — Auth frontend | Phase 6 frontend ✅ |
| 9 — Hardening | Production ready ✅ |

---

## Notes for Codex

- Each sprint is designed to be a single Codex task that opens one PR.
- If Codex cannot complete a task in one session, instruct it to commit what it has with a `wip:` prefix and continue in the next session starting with "continue the previous WIP sprint".
- Codex should always run `pytest tests/` and `npm run test` (from `frontend/`) before marking a sprint done.
- Sprints 4–5 (connector OAuth) require `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to be set as GitHub Actions secrets for integration tests to run against a real provider. Unit tests should mock the HTTP calls and pass without credentials.
- Sprint 7 (auth) will require updating all existing test fixtures to include an `Authorization: Bearer {token}` header. Codex should do this as part of the sprint, not defer it.
