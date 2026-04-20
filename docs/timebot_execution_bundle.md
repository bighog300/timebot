# Timebot Execution Bundle

## Objective
Stabilize the repo by fixing production-facing issues, then upgrade test coverage to catch real runtime failures.

---

## Execution rules
- Every fix must include at least one regression test
- Prefer small PRs
- API tests for runtime behavior, service tests for logic
- Do not expand scope beyond listed issues

---

## Branch sequence
1. fix/search-suggestions-runtime
2. fix/upload-error-sanitization-health
3. fix/hybrid-search-filter-enforcement
4. fix/streaming-upload-size-enforcement
5. fix/document-processing-status-semantics
6. fix/document-delete-cleanup
7. test/search-db-and-api-coverage

---

## Workstream summary

### 1. Fix search suggestions runtime
- Add missing imports (Category, case)
- Add API test for /search/suggestions

### 2. Upload + health fixes
- Remove raw exception leakage
- Fix health endpoint status
- Add tests for both

### 3. Hybrid search filtering
- Ensure semantic results respect filters
- Add regression tests

### 4. Streaming upload enforcement
- Replace full read with chunked streaming
- Enforce size during upload
- Add storage tests

### 5. Processing status correctness
- Mark failed extraction as failed
- Add processor tests

### 6. Deletion cleanup
- Remove all artifacts + embeddings
- Add cleanup tests

### 7. Coverage upgrade
- API tests: search, suggestions, upload, delete, health
- Service tests: search, storage, processor, cleanup
- DB tests: joins + filters

---

## Acceptance checklist
- Suggestions endpoint works and tested
- Hybrid search respects filters
- Upload size enforced during streaming
- No raw errors exposed
- Processing failures not marked completed
- Delete cleans all artifacts
- Health reflects real state

---

## Run all tests
pytest tests/api -q
pytest tests/services -q
pytest tests/db -q
pytest -q
