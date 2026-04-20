# Codex Execution Prompt for Timebot

Use this prompt at the start of any execution cycle.

---

You are working inside the Timebot repository.

## Mission
Implement the scoped sprint plan completely, with production-quality code, focused tests, and minimal unrelated changes.

## Working rules
- Read the repository structure before editing
- Prefer existing patterns over introducing new abstractions unless a refactor is necessary for correctness
- Fix root causes, not symptoms
- Every code change must include or update tests
- Keep PR-sized changes small and coherent
- Avoid breaking public API contracts unless the sprint explicitly requires it
- If you need to change a behavior contract, update tests and inline docs/comments accordingly

## Quality bar
- Code builds
- Existing tests pass
- New tests cover the added or fixed behavior
- Error handling is client-safe
- Logging is useful but not noisy
- Delete flows are idempotent where relevant
- Search/filter behavior is consistent

## Execution process
1. Inspect relevant files for the scoped sprint
2. Summarize the implementation plan in repo-specific terms
3. Make code changes
4. Add or update tests
5. Run targeted tests first
6. Run the broader suite that covers touched areas
7. Report:
   - what changed
   - why it changed
   - tests added/updated
   - any follow-up risks or deferred items

## Constraints
- Do not rewrite unrelated modules
- Do not introduce speculative features outside the sprint scope
- Do not suppress failing tests without fixing the underlying behavior
- Do not expose raw exceptions to clients

## Repo-specific priorities
- Protect upload/process/search/delete correctness
- Favor route-level tests for runtime-sensitive endpoints
- Favor service tests for branch logic
- Use DB-backed tests when validating ORM query correctness
- Preserve clear separation between API, services, models, and workers

## Output format
At the end of execution, provide:
1. Summary of changes
2. File-by-file change list
3. Test results
4. Known follow-ups

---

## Sprint scope placeholder
Replace this section each time with the current sprint doc.

Example:
- Sprint: Phase 1 Sprint 1: Core Stability
- Scope:
  - fix search suggestions runtime path
  - sanitize upload errors
  - fix health endpoint semantics
  - add API regression tests
