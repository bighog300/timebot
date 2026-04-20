# Branch Protection Checklist (`main`)

## Required status checks

Mark these checks as **required**:

- [ ] `backend-tests`
- [ ] `frontend-ci`
- [ ] `integrated-smoke`

These names are job names from:
- `.github/workflows/ci-backend.yml`
- `.github/workflows/ci-frontend.yml`
- `.github/workflows/ci-integrated.yml`

## Recommended non-required checks

Leave these as informational (recommended but not required initially):

- [ ] `docker-validate`
- [ ] `nightly-backend-tests`
- [ ] `nightly-frontend-ci`

## Core branch protection settings

- [ ] Require pull request before merging
- [ ] Require at least 1 approval
- [ ] Dismiss stale approvals when new commits are pushed
- [ ] Require branches to be up to date before merging
- [ ] Restrict force pushes
- [ ] Restrict deletions

## Deployment controls

- [ ] Create and use `staging` environment
- [ ] Create and use `production` environment
- [ ] Require reviewer approval for `production`
- [ ] Keep deploy concurrency enabled per environment

## Rollout order

1. Merge workflows to `main`.
2. Observe a few green runs for each required check.
3. Enable required checks (`backend-tests`, `frontend-ci`, `integrated-smoke`).
4. Enable production environment reviewer gate.
5. Replace deploy placeholder commands with real deployment logic.

## Local parity commands

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
bash frontend/tests/e2e/smoke.sh
```
(Requires backend on `127.0.0.1:8000` and frontend on `127.0.0.1:3000`.)
