# TimeBot GitHub Actions Bundle

This bundle provides a practical starting point for CI/CD in this repo.

## Included
- `.github/workflows/ci-backend.yml`
- `.github/workflows/ci-frontend.yml`
- `.github/workflows/ci-integrated.yml`
- `.github/workflows/docker-validate.yml`
- `.github/workflows/deploy.yml`
- `.github/workflows/nightly.yml`
- `docs/GITHUB_ACTIONS_ROLLOUT_PLAN.md`
- `docs/GITHUB_SECRETS_AND_VARIABLES.md`
- `docs/BRANCH_PROTECTION_CHECKLIST.md`
- `docs/CODEX_PROMPT_GITHUB_ACTIONS.md`

## Intent
These files are tailored to a repo with:
- Python backend
- React/Vite frontend in `frontend/`
- optional Docker deployment path
- current need for strong CI validation before merges

## Notes
- Some commands are placeholders and should be aligned to your exact dependency files and deployment target.
- The integrated workflow assumes the backend can start with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
  and the frontend with `npm run dev -- --host 127.0.0.1 --port 3000`.
- The smoke test uses `frontend/tests/e2e/smoke.sh` if present.

## Recommended rollout order
1. `ci-backend.yml`
2. `ci-frontend.yml`
3. `ci-integrated.yml`
4. branch protection rules
5. `docker-validate.yml`
6. `deploy.yml`
7. `nightly.yml`
