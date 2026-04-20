# Phase 1 Sprint 3: Search Regression Suite

## Goal
Close correctness gaps in search behavior.

## Scope
- Hybrid search filter enforcement
- Shared filter helper
- DB-backed query tests

## Tasks
- Refactor search filtering into a reusable helper
- Apply equivalent filters to semantic-only hydration path
- Add tests:
  - `tests/services/test_search_service.py`
  - `tests/api/test_search.py`
  - `tests/db/test_search_queries.py`

## Definition of done
- No hybrid result violates requested filters
- DB-backed tests validate joins and filter behavior
