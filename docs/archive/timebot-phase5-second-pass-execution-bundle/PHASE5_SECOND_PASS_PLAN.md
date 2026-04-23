# Phase 5 Second-Pass Plan

## Objective
Complete a narrow, high-confidence second pass that resolves the outstanding blockers from the first Phase 5 attempt.

---

## Milestone 0 — Baseline audit and reproducible environment
### Goal
Establish the exact package manager, lockfile, required runtime versions, and current failure modes.

### Tasks
- Inspect repo root and `frontend/` for:
  - `package.json`
  - lockfiles (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`)
  - `.npmrc`
  - `.node-version`, `.nvmrc`, Volta config, engines fields
- Identify intended package manager and standardize on it.
- Document required Node version and Python version.
- Reproduce current failures with exact commands and captured output.

### Exit criteria
- A single documented frontend install path exists.
- Root cause hypotheses are written down for install failures.

---

## Milestone 1 — Unblock frontend dependency installation
### Goal
Make `frontend` dependencies install reliably in a normal development/CI environment.

### Tasks
- Check for private registry configuration, mirror settings, auth assumptions, or broken package references.
- If registry config is broken:
  - fix `.npmrc` / package manager config
  - remove invalid private package references
  - pin compatible versions where needed
- If lockfile is missing or stale:
  - regenerate lockfile using the chosen package manager
- Keep dependency changes minimal and justified.

### Exit criteria
- `cd frontend && <package-manager install>` succeeds in a standard environment.
- Lockfile is present and consistent.
- README reflects the install command.

---

## Milestone 2 — Frontend static validation
### Goal
Get static frontend checks green.

### Tasks
- Run:
  - type-check
  - lint
  - unit tests
  - production build
- Fix:
  - typing mismatches
  - route/import errors
  - dead API typings
  - test setup issues
  - Vite / Tailwind / Vitest config issues
- Add missing scripts if the repo expects them but they are absent.

### Exit criteria
- `type-check`, `lint`, `test`, and `build` all pass.

---

## Milestone 3 — Integrated runtime validation
### Goal
Prove that backend and frontend work together.

### Tasks
- Start backend with required env.
- Start frontend pointed at backend base URL and websocket URL.
- Execute a reproducible smoke flow:
  1. open app shell
  2. load documents page
  3. upload or seed a document if possible
  4. open document detail
  5. run search
  6. view queue state
  7. load categories
  8. load insights
  9. load connections
- Run `frontend/tests/e2e/smoke.sh` or replace it with a better reproducible smoke command if needed.

### Exit criteria
- A documented smoke flow passes end to end.
- Any failures are fixed or clearly logged as scoped follow-up work.

---

## Milestone 4 — Frontend hardening and UI correctness
### Goal
Close the most important user-facing gaps.

### Tasks
- Verify empty/loading/error states on all major pages.
- Verify responsive layout on at least mobile, tablet, desktop widths.
- Verify action feedback:
  - upload
  - delete / archive / favorite / reprocess
  - connection sync/connect/disconnect
- Verify websocket invalidation behavior:
  - queue updates
  - processing updates
  - connection refreshes
- Add targeted tests for risky pages if currently under-tested:
  - SearchPage
  - DocumentDetailPage
  - ConnectionsPage or InsightsPage

### Exit criteria
- Key pages behave correctly under normal and edge states.
- At least a minimal frontend test net covers the highest-risk interactions.

---

## Milestone 5 — Docker and deployment-path validation
### Goal
Make the deployment path verifiable.

### Tasks
- Validate Dockerfiles / compose files / startup commands if present.
- Run:
  - `docker compose config`
  - image build
  - container startup smoke
- Fix:
  - missing env variables
  - bad copy paths
  - broken build stages
  - frontend asset serving assumptions
- If Docker is not part of the intended deployment path, document the actual release path explicitly.

### Exit criteria
- Deployment path is documented and validated, not assumed.

---

## Milestone 6 — Release signoff
### Goal
Produce a final yes/no release recommendation.

### Tasks
- Re-run all checks.
- Update README or release docs.
- Summarize:
  - what passed
  - what remains
  - any accepted risks

### Exit criteria
- Repo is signoff-ready, or there is a precise list of remaining blockers with evidence.
