# GitHub Actions Rollout Plan

## Objective
Provide branch-protected CI checks for backend, frontend, and integrated smoke validation while keeping deployment safe and explicit.

## Workflows implemented

1. **Backend CI** (`.github/workflows/ci-backend.yml`)
   - Workflow name: `Backend CI`
   - Required job/check: `backend-tests`
   - Triggers: PR, push to `main`, manual dispatch
   - Path filtered for backend files (`app/**`, `tests/**`, `requirements.txt`, Docker files)

2. **Frontend CI** (`.github/workflows/ci-frontend.yml`)
   - Workflow name: `Frontend CI`
   - Required job/check: `frontend-ci`
   - Triggers: PR, push to `main`, manual dispatch
   - Path filtered for frontend files (`frontend/**`)

3. **Integrated Smoke** (`.github/workflows/ci-integrated.yml`)
   - Workflow name: `Integrated Smoke`
   - Required job/check: `integrated-smoke`
   - Triggers: PR, push to `main`, manual dispatch
   - Path filtered for backend/frontend-relevant files
   - Starts backend (`uvicorn app.main:app --host 127.0.0.1 --port 8000`) and frontend (`npm run dev -- --host 127.0.0.1 --port 3000`), waits for readiness, then executes `frontend/tests/e2e/smoke.sh`

4. **Docker Validate** (`.github/workflows/docker-validate.yml`)
   - Workflow name: `Docker Validate`
   - Informational check name: `docker-validate`
   - Triggers on Docker/deployment-relevant file changes
   - Runs `docker compose config` and `docker build`

5. **Deploy** (`.github/workflows/deploy.yml`)
   - Workflow name: `Deploy`
   - Supports manual deploy dispatch and `v*` tags
   - Uses GitHub Environments (`staging` and `production`)
   - Uses per-environment concurrency (`deploy-staging`, `deploy-production`)
   - Currently a safe placeholder with explicit TODO markers

6. **Nightly Validation** (`.github/workflows/nightly.yml`)
   - Workflow name: `Nightly Validation`
   - Runs on schedule (`0 6 * * *`) and manual dispatch
   - Re-runs backend tests and frontend CI suite

## Rollout order

### Phase 1: Required PR checks
Enable these checks as required on `main`:
- `backend-tests`
- `frontend-ci`
- `integrated-smoke`

### Phase 2: Non-blocking confidence checks
Enable but do not require:
- `docker-validate`
- `nightly-backend-tests`
- `nightly-frontend-ci`

### Phase 3: Deploy safety
- Create `staging` and `production` environments
- Require approvals for `production`
- Add environment secrets
- Replace the deploy placeholder with real deploy logic

## Local equivalents for troubleshooting

Backend:
```bash
python -m pip install -r requirements.txt
pytest tests -q
```

Frontend:
```bash
cd frontend
npm install
npm run type-check
npm run lint
npm run test
npm run build
```

Integrated smoke:
```bash
# Terminal 1
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 3000

# Terminal 3 (repo root)
bash frontend/tests/e2e/smoke.sh
```
