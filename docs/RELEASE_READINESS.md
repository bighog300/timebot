# Timebot Release Readiness (April 22, 2026)

## Complete and working

- FastAPI backend with JWT auth, user-scoped documents, AI review workflow, queue stats, and connector endpoints.
- React frontend with auth guards, review queue, queue, connections, and shared app shell.
- Alembic is the schema authority and should be used for all schema changes.
- Targeted backend and frontend test suites exist for auth/review/connectors and major UI pages.

## Partially implemented / limited

- Connector OAuth is implemented for Google Drive foundations, but provider breadth and sync depth remain limited.
- Frontend smoke flow validates core paths, but does not represent exhaustive production monitoring or full browser E2E coverage.
- Docker deployment workflow is still a deployment placeholder and needs environment-specific rollout logic.

## Deferred hardening items (must be addressed before production launch)

1. **Connector token encryption at rest is not implemented yet** (`connections.access_token` / `refresh_token` are stored plaintext in DB).
2. **Refresh-token rotation/revocation hardening is incomplete** (basic token usage works, full lifecycle hardening is pending).
3. **Security policy hardening remains**: set strict CORS origins per environment, rotate strong `AUTH_SECRET_KEY`, and enforce HTTPS + secret management outside `.env`.
4. **Operational hardening remains**: structured central logging, rate-limiting, and production alerting are not fully implemented in this repository.
