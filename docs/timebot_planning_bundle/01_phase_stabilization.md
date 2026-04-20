# Phase 1: Stabilization & Hardening

## Objective
Make the existing application safe, predictable, and test-covered.

## Scope
- Runtime bug fixes
- Upload and storage hardening
- Error handling cleanup
- Health endpoint correctness
- Lifecycle consistency
- Critical regression coverage

## Workstreams
1. Search suggestions runtime fix
2. Upload error sanitization
3. Accurate health reporting
4. Hybrid search filter enforcement
5. Streaming upload size enforcement
6. Processing status correctness
7. Document deletion cleanup
8. Coverage expansion for API/service/DB paths

## Deliverables
- Stable core endpoints
- Reliable processing lifecycle
- Safe file handling
- No raw internal exception leakage
- Green regression suite

## Exit criteria
- Known bugs fixed
- Route-level tests cover runtime-sensitive endpoints
- Upload/delete/processing/search regressions covered
