# Timebot Execution Bundle

## Objective
Stabilize the repo by fixing the production-facing issues already identified, then raise test coverage in the exact areas where the current suite misses runtime failures.

---

## Execution rules
- Every bug fix must land with at least one regression test.
- Prefer small PRs that each leave the repo green.
- Use API tests for route/runtime behavior and service tests for branch logic.
- Do not expand scope beyond the issues listed here until the regression gaps are closed.

---

## Recommended branch sequence
1. `fix/search-suggestions-runtime`
2. `fix/upload-error-sanitization-health`
3. `fix/hybrid-search-filter-enforcement`
4. `fix/streaming-upload-size-enforcement`
5. `fix/document-processing-status-semantics`
6. `fix/document-delete-cleanup`
7. `test/search-db-and-api-coverage`

If preferred, combine 1 and 2 into a single stabilization PR, but keep 3 through 6 separate.

---

## Workstream 1: Search suggestions runtime fix

### Problem
`GET /api/v1/search/suggestions` fails at runtime because `Category` and `case` are used in `app/services/search_service.py` without imports.

### Files to change
- `app/services/search_service.py`
- likely existing search API test files under `tests/`

### Code changes
- Add missing imports:
  - `from sqlalchemy import case`
  - `from app.models.category import Category`
- Run the endpoint path locally and verify it returns a normal response.

### Tests to add
Create or extend:
- `tests/api/test_search_suggestions.py`

Add cases for:
- successful query returns `200`
- empty query behavior
- no-match behavior
- basic schema assertions

### Acceptance criteria
- endpoint no longer raises `NameError`
- a route-level test fails without the import fix and passes with it

### Suggested commands
```bash
pytest tests/api/test_search_suggestions.py -q
```

---

## Workstream 2: Upload error sanitization and health semantics

### Problem A
Upload exceptions are returned to clients using raw exception text.

### Problem B
`/health` always reports overall healthy even when dependencies fail.

### Files to change
- `app/api/v1/upload.py`
- `app/main.py`
- possibly shared logging/config utilities

### Code changes
#### Upload
- replace `detail=str(e)` with a generic message
- log full exception server-side with stack trace

Example target behavior:
- client gets `500` with `"Upload processing failed"` or equivalent
- logs retain root cause

#### Health
- derive top-level status from dependency checks
- use a clear contract, for example:
  - `healthy`: all critical dependencies pass
  - `degraded`: API is up but one critical dependency fails
  - `unhealthy`: optional if startup/runtime contract uses it

### Tests to add
Create or extend:
- `tests/api/test_upload.py`
- `tests/api/test_health.py`

Add cases for:
- mocked upload-processing failure returns generic error
- raw exception message is not exposed
- healthy dependency state returns `healthy`
- failed DB state returns `degraded` or `unhealthy`, matching the chosen contract

### Acceptance criteria
- no raw internal exception strings in HTTP 500 responses
- `/health` reflects real dependency state

### Suggested commands
```bash
pytest tests/api/test_upload.py tests/api/test_health.py -q
```

---

## Workstream 3: Hybrid search filter enforcement

### Problem
Hybrid search applies filters to lexical results, but semantic-only results can bypass those filters before merge.

### Files to change
- `app/services/search_service.py`
- any search schema/helpers if filters are parsed elsewhere

### Code changes
#### Preferred implementation
Refactor shared filter logic into a helper such as:
- `apply_document_filters(query, filters)`

Use that helper in:
- lexical query path
- semantic hydration query for `missing_ids`
- any other query path that returns `Document` rows under the same filter contract

#### Better long-term follow-up
- move filterable metadata into Qdrant payload and filter in vector search too
- not required for this stabilization pass

### Tests to add
Create or extend:
- `tests/services/test_search_service.py`
- `tests/api/test_search.py`
- optionally `tests/db/test_search_queries.py`

Add cases for:
- source filter respected in hybrid mode
- category filter respected in hybrid mode
- date-range filter respected in hybrid mode
- semantic-only match that would have leaked before the fix is excluded now

### Acceptance criteria
- no hybrid result violates requested filters
- regression tests cover semantic-only leakage path

### Suggested commands
```bash
pytest tests/services/test_search_service.py tests/api/test_search.py -q
```

---

## Workstream 4: Streaming upload size enforcement

### Problem
Uploads are fully read into memory before size validation, so configured file-size limits do not protect memory.

### Files to change
- `app/services/storage.py`
- upload tests under `tests/`

### Code changes
Rewrite save logic to stream file content in chunks.

### Target behavior
- read chunks incrementally
- count total bytes while writing
- stop immediately if max size is exceeded
- delete partial file on failure
- return saved path and final size only on success

### Sketch
```python
async def save_upload(self, file: UploadFile) -> tuple[Path, int]:
    dest = ...
    size = 0
    try:
        async with aiofiles.open(dest, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise ValueError("File too large")
                await f.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    return dest, size
```

### Tests to add
Create or extend:
- `tests/services/test_storage.py`
- `tests/api/test_upload.py`

Add cases for:
- valid small upload succeeds
- oversized upload fails
- partial file is removed after failure
- implementation handles chunked reads rather than relying on one full read

### Acceptance criteria
- oversized uploads are rejected during streaming
- no partial artifact remains after rejection

### Suggested commands
```bash
pytest tests/services/test_storage.py tests/api/test_upload.py -q
```

---

## Workstream 5: Processing status semantics

### Problem
Document processing can end as `completed` even when extraction failed and no usable text was produced.

### Files to change
- `app/services/document_processor.py`
- `app/services/text_extractor.py`
- model/status helpers if present

### Code changes
- explicitly distinguish extraction failure from successful extraction
- set terminal failure status when extractor fails, for example:
  - `failed`
  - or `failed_extraction` if the repo already supports subtype statuses
- keep empty-but-valid file behavior explicit and tested

### Decision to make
Choose and document one contract:
1. empty extracted text from a valid document is allowed and still `completed`
2. extractor failure or parse failure becomes `failed`

### Tests to add
Create or extend:
- `tests/services/test_document_processor.py`

Add cases for:
- extractor succeeds -> status `completed`
- extractor fails -> status `failed`
- empty valid document behavior follows chosen contract

### Acceptance criteria
- processing status reflects actual extraction outcome
- failures no longer appear as successful completions

### Suggested commands
```bash
pytest tests/services/test_document_processor.py -q
```

---

## Workstream 6: Deletion cleanup consistency

### Problem
Deleting a document removes only the original file, not all derived artifacts or vector index state.

### Files to change
- `app/api/v1/documents.py`
- or introduce `app/services/document_cleanup.py`
- embedding service integration points

### Code changes
Delete all associated artifacts when a document is deleted:
- original upload
- extracted text file
- thumbnail
- Qdrant embedding/index entry

### Implementation notes
- make cleanup idempotent
- missing file or missing embedding must not fail the delete request
- prefer moving deletion logic into a dedicated service if the endpoint currently does too much

### Tests to add
Create or extend:
- `tests/api/test_documents_delete.py`
- `tests/services/test_document_cleanup.py`

Add cases for:
- original file removed
- derived text removed
- thumbnail removed
- embedding deletion called
- missing artifact does not cause delete failure

### Acceptance criteria
- no stale file or index artifacts remain after deletion

### Suggested commands
```bash
pytest tests/api/test_documents_delete.py tests/services/test_document_cleanup.py -q
```

---

## Workstream 7: Coverage upgrade for runtime and query behavior

### Objective
Add the tests most likely to catch the exact class of bugs already found.

### Test structure target
```text
tests/
  api/
    test_health.py
    test_search.py
    test_search_suggestions.py
    test_upload.py
    test_documents_delete.py
  services/
    test_search_service.py
    test_storage.py
    test_document_processor.py
    test_document_cleanup.py
  db/
    test_search_queries.py
```

### Minimum API coverage to add
#### `tests/api/test_search.py`
- search returns `200`
- pagination behavior
- filters flow through correctly
- hybrid mode respects filters

#### `tests/api/test_search_suggestions.py`
- endpoint returns `200`
- response shape
- no-match behavior

#### `tests/api/test_upload.py`
- successful upload
- oversized upload
- processing failure returns generic error

#### `tests/api/test_documents_delete.py`
- delete success path
- delete with missing derived artifact still succeeds

#### `tests/api/test_health.py`
- healthy path
- degraded/unhealthy dependency path

### Minimum service coverage to add
#### `tests/services/test_search_service.py`
- helper-level filter behavior
- hybrid merge/rerank respects filters
- semantic-only leakage regression

#### `tests/services/test_storage.py`
- chunked save success
- size limit failure mid-stream
- partial cleanup on exception

#### `tests/services/test_document_processor.py`
- extraction success path
- extraction failure path
- chosen empty-text contract

#### `tests/services/test_document_cleanup.py`
- file deletion idempotency
- vector deletion call behavior

### DB-backed tests to add
#### `tests/db/test_search_queries.py`
Use seeded records to verify actual SQLAlchemy query behavior for:
- category joins
- source filter
- date range filter
- suggestion generation path

### Acceptance criteria
- route-level runtime failures are caught by tests
- query construction errors are caught by DB-backed tests
- logic branches are covered in fast unit/service tests

---

## Recommended implementation order

### PR 1: Stabilize broken runtime paths
Includes:
- Workstream 1
- Workstream 2

### PR 2: Fix search correctness
Includes:
- Workstream 3
- search API/service tests

### PR 3: Harden uploads
Includes:
- Workstream 4
- upload/storage tests

### PR 4: Fix processing lifecycle
Includes:
- Workstream 5
- processor tests

### PR 5: Fix deletion lifecycle
Includes:
- Workstream 6
- cleanup/delete tests

### PR 6: DB-backed query regression suite
Includes:
- Workstream 7 DB tests
- any residual API test gaps

---

## Merge checklist for every PR
- tests added before or with the fix
- `pytest -q` passes
- new targeted test file passes in isolation
- no raw internal exception text in API responses
- no endpoint known to be runtime-broken without coverage
- docstrings/comments updated if behavior contract changed

---

## Final acceptance gate for the repo
The bundle is complete when all of the following are true:
- `/api/v1/search/suggestions` has route coverage and passes
- hybrid search cannot bypass filters
- upload size limits are enforced during streaming
- upload failures do not leak internals
- processing failures do not end as `completed`
- delete removes all derived artifacts and index state
- `/health` accurately reports dependency state
- DB-backed search tests cover joins and filter behavior

---

## One-shot validation command set
```bash
pytest tests/api -q
pytest tests/services -q
pytest tests/db -q
pytest -q
```

---

## Optional follow-up after stabilization
Only after this bundle lands:
- centralize processing status values into an enum
- centralize search filter application into a reusable query builder
- add structured logging around upload/process/delete lifecycle
- add vector-payload filtering in Qdrant for long-term search consistency
```

