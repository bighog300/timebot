# GitHub Secrets and Variables

## Repository variables (recommended)

Configure these in **Settings → Secrets and variables → Actions → Variables**:

- `PYTHON_VERSION` = `3.11`
- `NODE_VERSION` = `20`

> Notes:
> - Workflows provide fallback defaults (`3.11`, `20`) if variables are absent.
> - `FRONTEND_DIR`, host, and port values are currently hardcoded in workflows to match repo structure and Vite config.

## Environment setup

Create two GitHub Environments:
- `staging`
- `production`

Apply protection rules:
- Require reviewers for `production`
- Optionally add a wait timer for `production`

## Environment secrets required for deploy workflow

Set these as **environment-scoped secrets** (at minimum in `staging` and `production`):

- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`

The current deploy workflow is a placeholder and will no-op with a warning when these are missing.

## Optional secrets/variables for future deploy expansion

Only add these when your real deploy process uses them:

- `REGISTRY_USERNAME`
- `REGISTRY_PASSWORD`
- `CLOUD_API_TOKEN`
- `STAGING_APP_URL`
- `PRODUCTION_APP_URL`

## Security notes

- Never commit credentials into workflow YAML.
- Keep long-lived secrets in environment scopes, not repository scopes.
- Prefer short-lived tokens/OIDC where available once deploy logic is implemented.
