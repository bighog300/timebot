# TimeBot Phase 5 Second-Pass Execution Bundle

This bundle is for a **focused second Codex pass on Phase 5**.

## Goal
Close the remaining Phase 5 blockers and get the repo to a credible **release-candidate / signoff-ready** state.

## The unresolved items this bundle targets
1. Frontend dependency install and package-manager / registry issues
2. Frontend type-check, lint, test, and production build validation
3. Real end-to-end validation with backend + frontend running together
4. Frontend hardening and UI state verification
5. Docker / deployment-path validation

## Files
- `CODEX_EXECUTION_PROMPT.md` — prompt to give Codex
- `AGENTS.md` — repo-specific execution rules for Codex
- `PHASE5_SECOND_PASS_PLAN.md` — milestone plan
- `VALIDATION_MATRIX.md` — exact checks and pass criteria
- `ENVIRONMENT_TRIAGE.md` — install / registry / package-manager recovery guidance
- `RELEASE_SIGNOFF_CHECKLIST.md` — final signoff list

## Recommended use
1. Put `AGENTS.md` in the repo root if you want Codex to consistently follow it.
2. Give `CODEX_EXECUTION_PROMPT.md` to Codex.
3. Have Codex execute milestone-by-milestone and commit after each stable checkpoint.
