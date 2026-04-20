# GitHub Secrets and Variables

## Repository variables
Use repository variables for non-sensitive defaults.

Suggested variables:
- `PYTHON_VERSION` = `3.11`
- `NODE_VERSION` = `20`
- `FRONTEND_DIR` = `frontend`
- `BACKEND_HOST` = `127.0.0.1`
- `BACKEND_PORT` = `8000`
- `FRONTEND_HOST` = `127.0.0.1`
- `FRONTEND_PORT` = `3000`

## Environment secrets
Use environment secrets for staging/production deploy credentials.

Suggested examples:
- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`
- `REGISTRY_USERNAME`
- `REGISTRY_PASSWORD`
- `CLOUD_API_TOKEN`
- `STAGING_APP_URL`
- `PRODUCTION_APP_URL`

## Notes
- Do not put real secrets in workflow files.
- Prefer GitHub Environments for deploy-stage secrets.
- If the frontend requires runtime env values during build, inject them through workflow `env` or environment-scoped variables.
