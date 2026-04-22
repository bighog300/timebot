# Timebot

AI-assisted document intelligence platform with upload/search, review workflow, user auth, and connector foundations.

## Architecture / UI preview

> Add latest architecture diagram or UI screenshot here before external release.

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 14+
- Redis 7+
- Anthropic API key

## Quick start (Docker Compose)

1. Copy env template:
   ```bash
   cp .env.example .env
   ```
2. Set required secrets in `.env` (at minimum `ANTHROPIC_API_KEY`, `AUTH_SECRET_KEY`).
3. Start stack:
   ```bash
   docker compose up --build
   ```
4. Run migrations (from app container shell or local environment):
   ```bash
   alembic upgrade head
   ```

API: `http://localhost:8000`  
Frontend (dev): `http://localhost:5173`

## Local development

### Minimal bootstrap (recommended)

```bash
./scripts/bootstrap_dev.sh
```

This installs backend deps, creates `.env` if missing, and runs `alembic upgrade head`.

### Backend

```bash
python -m pip install -r requirements-dev.txt
alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

## Environment variables

| Key | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | SQLAlchemy + Alembic database connection |
| `REDIS_URL` | Yes | Redis cache + Celery broker default |
| `CELERY_BROKER_URL` | Yes | Celery broker URL |
| `CELERY_RESULT_BACKEND` | Yes | Celery result backend |
| `ANTHROPIC_API_KEY` | Yes for AI features | Claude API key |
| `AI_MODEL` | Optional | Claude model id (`claude-sonnet-4-20250514`) |
| `AUTH_SECRET_KEY` | Yes outside local dev | JWT signing secret |
| `AUTH_ALGORITHM` | Optional | JWT algorithm (default `HS256`) |
| `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Access token TTL |
| `ALLOWED_ORIGINS` | Yes | CSV of frontend origins for CORS |
| `GOOGLE_OAUTH_CLIENT_ID` | Optional | Google Drive OAuth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Optional | Google Drive OAuth secret |
| `GOOGLE_OAUTH_REDIRECT_URI` | Optional | OAuth callback URL |
| `GOOGLE_OAUTH_SCOPES` | Optional | OAuth scopes list |
| `CONNECTOR_TOKEN_ENCRYPTION_KEY` | Required when connectors are used | Fernet key used to encrypt connector `access_token`/`refresh_token` values at rest |
| `QDRANT_HOST` / `QDRANT_PORT` | Optional | Semantic search backend |
| `STORAGE_PATH`, `UPLOAD_PATH`, `PROCESSED_PATH` | Optional | File storage locations |
| `ALEMBIC_SKIP` | Optional (test-only) | Enables fallback `create_all` for isolated tests |

See `.env.example` for the full list and safe local defaults.

### Connector token encryption key

- Generate a key with:
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- Set `CONNECTOR_TOKEN_ENCRYPTION_KEY` before using connector OAuth callback/sync flows.
- Runtime intentionally fails for connector token operations if this key is missing/invalid.
- If upgrading an existing environment that already has plaintext connector tokens, run:
  ```bash
  python scripts/reencrypt_connector_tokens.py
  ```
  after setting `CONNECTOR_TOKEN_ENCRYPTION_KEY`.

## Migrations (Alembic is authoritative)

```bash
alembic upgrade head
```

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
```

## Running tests

### Backend

```bash
pytest tests -q
```

### Frontend

```bash
cd frontend
npm run type-check
npm run test
npm run build
```

## Architecture

```text
app/
  api/v1/           FastAPI routes (auth, documents, queue, connectors, insights)
  models/           SQLAlchemy models (users, documents, relationships)
  services/         Domain services (AI analysis, auth, connectors, search)
  workers/          Celery tasks / monitoring
migrations/         Alembic config + migration versions
frontend/           React + TypeScript client
tests/              Backend tests
```

## Deployment notes

- Run migrations (`alembic upgrade head`) during each deploy before serving traffic.
- Use production-only `AUTH_SECRET_KEY` and strict `ALLOWED_ORIGINS` values.
- Configure HTTPS, secret manager integration, and real deployment automation (current deploy workflow is a placeholder).
- Review known deferred items in `docs/RELEASE_READINESS.md` before production launch.

## Known limitations and production handoff

See `docs/RELEASE_READINESS.md` for clear split between complete, partial, and deferred hardening work.

## Contributing

1. Create a feature branch.
2. Run backend/frontend checks locally.
3. Open a PR with test evidence.

## License

MIT
