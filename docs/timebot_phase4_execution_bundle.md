# Timebot Phase 4 Execution Bundle — Performance & Scalability

## Purpose

Phase 4 improves Timebot’s runtime performance, scalability, and operational resilience without changing product scope.

Timebot remains a document intelligence application that works only on:

- uploaded documents
- Gmail-imported emails
- extracted artifacts

Do **not** add crawling, scraping, external web ingestion, URL indexing, or source mapping.

---

# Phase 4 Goals

## Primary Goals

1. Reduce chat and retrieval latency.
2. Reduce duplicate database and AI work.
3. Improve background processing reliability.
4. Improve operational visibility for processing failures.
5. Preserve all existing user-facing behavior.

## Non-Goals

Do **not**:

- redesign the UI
- add new ingestion sources
- add multi-AI provider support
- add monetization
- add regionalization
- rewrite the retrieval system
- change public API contracts unless explicitly required

---

# Required Verification Commands

After each task, run:

```bash
pytest -q
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

If a task is backend-only, at minimum run:

```bash
pytest -q
```

If a task is frontend-only, run:

```bash
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

---

# Phase 4 Sprint Structure

## Sprint 9 — Retrieval Performance & Caching

### Sprint Goal

Improve response latency and reduce repeated work in chat retrieval and document intelligence reads.

### Main Themes

- cache safe retrieval results
- avoid duplicate relationship/timeline queries
- reduce N+1 query patterns
- preserve grounding and citations
- add measurable performance logs

---

## Sprint 10 — Background Processing & Throughput

### Sprint Goal

Make ingestion and AI processing more resilient, observable, and scalable.

### Main Themes

- queue prioritization
- retry behavior
- failure visibility
- batch-safe processing
- idempotency safeguards

---

# Sprint 9 — Task 1: Retrieval Query Optimization

## Codex Prompt

```text
You are working on Timebot, a production FastAPI + React document intelligence app.

Task: Optimize chat retrieval database access without changing retrieval behavior.

Context:
- Chat retrieval uses summaries, timeline events, relationships, optional snippets/full text, and source_refs.
- Recent work added structured retrieval context formatting.
- Retrieval grounding and citations must remain unchanged.

Requirements:
1. Inspect app/services/chat_retrieval.py and related models/API call paths.
2. Identify avoidable duplicate queries or N+1 query patterns.
3. Optimize using existing SQLAlchemy patterns:
   - eager loading where appropriate
   - batched queries
   - fewer per-document lookups
4. Preserve existing ranking, returned items, source_refs, and formatted context content.
5. Do not change API response contracts.
6. Do not add Redis or external cache in this task.
7. Add lightweight timing logs around retrieval if not already present.

Tests:
- Add/update backend tests verifying:
  1. chat retrieval still returns summaries
  2. timeline events are still included
  3. relationships are still included
  4. source_refs are unchanged
  5. formatted context still contains expected labeled sections

Run:
pytest -q

Report:
- what was optimized
- files changed
- tests added/updated
- test results
- any remaining performance risks
```

## Acceptance Criteria

- Retrieval behavior remains equivalent.
- Source citations remain intact.
- Tests confirm formatted context still includes all expected sections.
- No external cache introduced yet.

---

# Sprint 9 — Task 2: Safe In-Process Retrieval Cache

## Codex Prompt

```text
You are working on Timebot, a production FastAPI + React document intelligence app.

Task: Add a safe, small in-process cache for chat retrieval results.

Context:
- Chat retrieval may repeat similar work during the same session.
- We want a low-risk cache before introducing Redis.
- Retrieval must remain user-isolated and grounded.

Requirements:
1. Add a small TTL-based in-process cache for chat retrieval results.
2. Cache key must include:
   - user_id
   - session_id where relevant
   - query text
   - retrieval options such as include_full_text/include_timeline/include_relationships if present
3. Cache value may include retrieval payload and source_refs.
4. TTL should be short and configurable, e.g. 60–300 seconds.
5. Add explicit invalidation or bypass when documents are updated/imported if a safe existing signal exists.
   - If no safe signal exists, keep TTL short and document limitation.
6. Do not cache across users.
7. Do not cache API keys, prompts, or raw secrets.
8. Preserve existing retrieval behavior and response contracts.
9. Add logs for cache hit/miss.

Tests:
- Add backend tests verifying:
  1. identical query/options for same user can hit cache
  2. different users do not share cache
  3. different options do not share cache
  4. source_refs are preserved from cached result
  5. cache miss path still works

Run:
pytest -q

Report:
- cache design
- cache key fields
- files changed
- tests added
- test results
- limitations/follow-up
```

## Acceptance Criteria

- Cache is user-isolated.
- Cache does not alter citations.
- Cache has short TTL.
- Tests prove no cross-user leakage.

---

# Sprint 9 — Task 3: Relationship Query Optimization

## Codex Prompt

```text
You are working on Timebot, a production FastAPI + React document intelligence app.

Task: Optimize relationship retrieval/display queries.

Context:
- Relationship UX now includes filters, grouping, confidence, explainability, and inline review actions.
- Relationship APIs must remain compatible with the frontend.

Requirements:
1. Inspect relationship-related endpoints/services:
   - document relationships API
   - review queue APIs
   - relationship detection/read paths
2. Reduce avoidable N+1 queries and duplicate relationship lookups.
3. Preserve response schemas and frontend behavior.
4. Ensure explanation_metadata remains included.
5. Ensure status/review fields remain included.
6. Do not change review semantics.

Tests:
- Add/update backend tests verifying:
  1. document relationship endpoint still returns grouped/expected relationships
  2. explanation_metadata is preserved
  3. review status is preserved
  4. structural relationships still appear
  5. AI relationships still appear

Run:
pytest -q

Report:
- optimizations made
- files changed
- tests added/updated
- test results
- remaining risks
```

## Acceptance Criteria

- Relationship API behavior unchanged.
- Metadata and review statuses preserved.
- No frontend regressions.

---

# Sprint 9 — Task 4: Performance Logging Baseline

## Codex Prompt

```text
You are working on Timebot, a production FastAPI + React document intelligence app.

Task: Add minimal performance logging baseline for retrieval-heavy flows.

Requirements:
1. Add structured timing logs for:
   - chat retrieval duration
   - chat model call duration if already measurable
   - report generation duration
   - document intelligence persistence duration
2. Use existing logging patterns.
3. Do not log:
   - user message content
   - document text
   - snippets
   - summaries
   - secrets/API keys
4. Include safe metadata where available:
   - user_id
   - session_id/report_id/document_id
   - duration_ms
   - item counts
   - success/failure
5. Do not add external observability service.

Tests:
- Add backend tests where practical verifying:
  1. success logs include duration_ms
  2. failure logs include success=false
  3. raw content is not logged

Run:
pytest -q

Report:
- flows instrumented
- files changed
- tests added
- test results
- limitations/follow-up
```

## Acceptance Criteria

- Logs are structured enough for later JSON log formatting.
- No sensitive content is logged.
- Existing behavior unchanged.

---

# Sprint 10 — Task 1: Processing Failure Visibility

## Codex Prompt

```text
You are working on Timebot, a production FastAPI + React document intelligence app.

Task: Improve visibility into document processing failures.

Context:
- Timebot uses background processing/Celery for ingestion and AI tasks.
- Users/admins need clearer processing status and failure reasons.

Requirements:
1. Inspect existing document processing status fields and queue/admin APIs.
2. Ensure failed processing records store a safe failure reason.
3. Do not store raw model responses, document text, or secrets in failure messages.
4. Add/update an admin or existing queue/status response to expose:
   - status
   - safe error message
   - updated_at/failed_at where available
5. Preserve existing processing behavior.
6. Do not add a new UI unless a small existing status display can be improved safely.

Tests:
- Add backend tests verifying:
  1. processing failure stores safe error reason
  2. status API exposes safe error reason
  3. raw document content is not included in failure reason
  4. successful processing behavior is unchanged

Run:
pytest -q

Report:
- files changed
- tests added
- test results
- limitations/follow-up
```

## Acceptance Criteria

- Failures become diagnosable.
- No sensitive content leaks.
- No processing flow regression.

---

# Sprint 10 — Task 2: Idempotent Processing Guards

## Codex Prompt

```text
You are working on Timebot, a production FastAPI + React document intelligence app.

Task: Strengthen idempotency in document processing.

Context:
- Rebuilds, retries, and duplicate imports can trigger repeated processing.
- Existing duplicate prevention exists for Gmail/import paths, but processing should be robust.

Requirements:
1. Inspect document processing and intelligence persistence paths.
2. Add safeguards so repeated processing of the same document does not create duplicate:
   - timeline events
   - relationships
   - artifacts
   - reports, if applicable
3. Preserve existing deduplication behavior.
4. Do not retroactively delete existing duplicates.
5. Add logs when duplicate-safe behavior skips repeated work.
6. Avoid broad rewrites.

Tests:
- Add backend tests verifying:
  1. repeated processing does not duplicate timeline events
  2. repeated processing does not duplicate structural relationships
  3. repeated processing preserves existing summaries/intelligence
  4. retry path remains safe

Run:
pytest -q

Report:
- files changed
- tests added
- test results
- limitations/follow-up
```

## Acceptance Criteria

- Retrying processing is safe.
- Duplicate artifacts/intelligence are not created.
- Existing data is preserved.

---

# Sprint 10 — Task 3: Queue Prioritization Review

## Codex Prompt

```text
You are working on Timebot, a production FastAPI + React document intelligence app.

Task: Review and improve background task queue prioritization where practical.

Context:
- Timebot uses Celery workers for processing and AI tasks.
- We want high-value user-visible tasks to avoid being blocked by lower-priority work.

Requirements:
1. Inspect Celery task definitions and queue configuration.
2. Identify whether separate queues/priorities already exist.
3. If low-risk, assign or document queue separation for:
   - ingestion
   - AI analysis
   - report generation
   - maintenance/backfill tasks
4. Do not break local/test execution.
5. Preserve existing task names and call sites unless migration-safe.
6. Add comments/documentation for queue behavior.

Tests:
- Add/update tests where practical verifying task routing/config does not break imports.
- At minimum, ensure full backend test suite passes.

Run:
pytest -q

Report:
- current queue state
- changes made
- files changed
- test results
- limitations/follow-up
```

## Acceptance Criteria

- Queue behavior is clearer.
- No task import or worker configuration regressions.
- If actual routing changes are too risky, document findings and leave safe TODOs.

---

# Sprint 10 — Task 4: Processing Admin Summary

## Codex Prompt

```text
You are working on Timebot, a production FastAPI + React document intelligence app.

Task: Add a lightweight admin processing summary.

Requirements:
1. Add or extend an admin API endpoint to return processing summary counts:
   - pending
   - processing
   - completed
   - failed
   - recently failed count
2. Include only safe metadata.
3. Do not expose document contents.
4. Preserve admin-only access.
5. Add a simple admin UI card if an admin dashboard/page already exists.
6. Keep UI minimal.

Tests:
- Backend tests:
  1. admin can retrieve processing summary
  2. non-admin cannot retrieve processing summary
  3. counts are accurate for sample statuses
- Frontend tests if UI added:
  1. processing summary card renders
  2. failed count renders

Run:
pytest -q
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build

Report:
- files changed
- tests added
- test results
- limitations/follow-up
```

## Acceptance Criteria

- Admin can see processing health at a glance.
- Counts are safe and accurate.
- No content leakage.

---

# Phase 4 Final Verification Prompt

Use this after all Sprint 9 and Sprint 10 tasks are complete.

```text
Perform a final verification pass for Phase 4 — Performance & Scalability.

Scope:
- retrieval query optimization
- in-process retrieval cache
- relationship query optimization
- performance logging
- processing failure visibility
- idempotent processing guards
- queue prioritization review
- admin processing summary

Tasks:
1. Run:
   pytest -q
   npm --prefix frontend run lint
   npm --prefix frontend run test -- --run
   npm --prefix frontend run build

2. Inspect for regressions:
   - auth/role guards preserved
   - no web crawling/source mapping added
   - no cross-user cache leakage
   - citations/source_refs preserved
   - prompt fallback behavior preserved
   - existing chat/report/timeline/relationship flows still work
   - processing retries do not duplicate intelligence
   - logs do not include raw user/document content

3. Report:
   - final test results
   - notable files changed
   - any risks before merge
   - recommended follow-up tickets
```

---

# Phase 4 Definition of Done

Phase 4 is complete when:

- backend tests pass
- frontend lint/tests/build pass
- retrieval remains grounded and citation-preserving
- repeated queries are measurably cheaper or logged
- processing failures are visible and safe
- repeated processing is more idempotent
- no new product scope was introduced
- no sensitive content is logged or exposed
- admin has basic operational visibility

---

# Recommended Follow-Up After Phase 4

After Phase 4, proceed to:

## Phase 5 — Intelligence Depth

Suggested sprints:

1. Relationship Intelligence Upgrade
2. Timeline Intelligence Upgrade

Focus areas:

- stronger relationship scoring
- document clusters
- fuzzy timeline event merging
- milestone detection
- missing timeline gap detection
