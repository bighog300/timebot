# Validation Matrix

## 1. Backend validation
### Commands
- `pytest -q`

### Pass criteria
- Test suite passes
- No import-time failures
- No regressions in search, timeline, insights, relationships, config boot

---

## 2. Frontend installation
### Commands
Use the repo's chosen package manager consistently:
- `cd frontend && npm install`
or
- `cd frontend && pnpm install --frozen-lockfile`
or
- `cd frontend && yarn install --frozen-lockfile`

### Pass criteria
- Install succeeds without private-registry/auth surprises
- Lockfile matches package manager
- No unresolved packages

---

## 3. Frontend static checks
### Commands
- `cd frontend && npm run type-check`
- `cd frontend && npm run lint`
- `cd frontend && npm run test`
- `cd frontend && npm run build`

### Pass criteria
- All commands exit 0
- No TypeScript errors
- No lint failures of substance
- Build outputs production artifacts

---

## 4. Integrated runtime smoke
### Commands
Use the actual app startup commands for this repo.
Examples:
- backend start command
- `cd frontend && npm run dev`
- `bash frontend/tests/e2e/smoke.sh`

### Pass criteria
- App shell loads
- At least one successful request on each major Stage 4 page:
  - documents
  - search
  - queue
  - categories
  - insights
  - connections
- No fatal runtime exceptions in browser console/server logs

---

## 5. Websocket/live updates
### Validate
- document processing event invalidates/refetches correct queries
- queue changes refresh queue UI
- connection events refresh connections UI
- payload fields `event_version` and `timestamp` are consumed safely

### Pass criteria
- No broken live-refresh loops
- No stale UI after events
- No runtime crash on unexpected event payloads

---

## 6. Docker / deployment path
### Commands
- `docker compose config`
- `docker build -t timebot-phase5-check .`
- any compose or run commands required by repo

### Pass criteria
- Config resolves
- Build succeeds
- App starts with documented env
- Release path is reproducible

---

## 7. Documentation
### Validate
- setup instructions
- required env vars
- frontend install command
- backend/frontend run commands
- release verification steps

### Pass criteria
- A new developer can follow docs without guessing
