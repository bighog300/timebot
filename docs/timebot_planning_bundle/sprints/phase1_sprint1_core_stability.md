# Phase 1 Sprint 1: Core Stability

## Goal
Fix the highest-risk runtime issues and add direct regression coverage.

## Scope
- Search suggestions import/runtime fix
- Upload error sanitization
- Health status correctness
- Initial API tests

## Tasks
- Patch `app/services/search_service.py` missing imports and validate route behavior
- Replace raw upload exception details with generic client-safe responses
- Update `/health` to reflect dependency status
- Add tests:
  - `tests/api/test_search_suggestions.py`
  - `tests/api/test_upload.py`
  - `tests/api/test_health.py`

## Definition of done
- Runtime-broken routes are fixed
- Tests fail before fixes and pass after
- No raw exception strings leak to clients
