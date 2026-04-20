# AGENTS.md

## Mission
Make a **second-pass Phase 5 hardening run** that closes the remaining validation and release-readiness gaps without redesigning the system.

## Current repo context
- Phase 3 is already implemented or in late completion.
- Stage 4 frontend exists and major pages / routes are implemented.
- A first Phase 5 pass already hardened backend imports/config and improved backend tests.
- Backend tests passed in the last pass.
- Remaining risk is now mostly around frontend validation, integrated runtime behavior, and deployment validation.

## Non-goals
- Do not rewrite architecture.
- Do not replace frameworks or libraries unless installation is impossible and you can prove the replacement is smaller-risk than keeping the current stack.
- Do not broaden scope into Stage 6.

## Working style
- Inspect before editing.
- Prefer small diffs.
- Keep API contracts stable unless a bug forces a change.
- Add or update tests when fixing behavior.
- Record assumptions in commit messages or README updates.
- If environment tooling is missing, add graceful diagnostics and fallback instructions rather than silently skipping checks.

## Priority order
1. Unblock frontend install and package resolution
2. Get frontend type-check / lint / tests / build green
3. Run real backend+frontend E2E validation
4. Verify websocket-driven flows and UI state handling
5. Validate Docker / deployment path
6. Patch findings and re-run validation

## Expected deliverables
- Working frontend install path
- Passing backend and frontend checks
- At least one reproducible integrated smoke flow
- Clear deployment validation results
- Updated docs for local setup and release verification
