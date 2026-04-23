# Environment Triage Guide

Use this when the second Codex pass encounters install or validation failures.

## A. Frontend install fails with 403 / registry errors
### Check
- `frontend/.npmrc`
- repo-root `.npmrc`
- environment variables for npm auth or registry override
- `package.json` dependencies pointing to private scopes
- CI-specific registry settings leaking into local config

### Fix patterns
- Replace private registry with public npm registry if packages are public
- Remove stale auth-only config from local development setup
- Pin dependency versions that still exist publicly
- Regenerate lockfile after cleanup

### Do not do
- Do not silently delete dependencies without verifying actual usage
- Do not switch package managers unless there is a concrete reason

---

## B. Type-check fails
### Common causes
- API type drift
- missing nullable handling
- route param typing issues
- React Query data shape assumptions
- environment variable typings

### Fix patterns
- align shared types with real backend responses
- narrow unknown values at edges
- add explicit null/undefined handling
- fix import paths and Vite alias settings

---

## C. Unit tests fail
### Common causes
- missing test setup providers
- router/query client wrappers absent
- DOM API mocks not installed
- brittle text assertions

### Fix patterns
- add a shared test renderer/provider wrapper
- stabilize mocks for API hooks
- assert on user-visible semantics rather than incidental structure

---

## D. Build fails
### Common causes
- unresolved imports
- incorrect `baseUrl` / alias config
- dynamic env access at build time
- CSS/Tailwind content config omissions

### Fix patterns
- fix aliases in Vite + tsconfig
- validate env loading through one utility
- ensure Tailwind content includes all source paths

---

## E. E2E smoke fails
### Check
- backend actually running
- frontend actually running on expected host/port
- correct API base URL and websocket URL
- seed data or upload path available

### Fix patterns
- make smoke script start from documented assumptions
- improve readiness/wait logic
- fail with actionable diagnostics

---

## F. Docker unavailable in execution environment
If Docker CLI is unavailable where Codex runs:
- still inspect Dockerfile / compose definitions
- fix obvious build-path issues statically
- document exact commands to run in a Docker-capable environment
- do not falsely claim deployment validation passed
