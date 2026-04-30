# Timebot

AI-assisted document intelligence platform with upload/search, review workflow, user auth, and connector foundations.

## Architecture / UI preview

> Add latest architecture diagram or UI screenshot here before external release.

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 14+
- Redis 7+
- OpenAI API key

## Quick start (Docker Compose)

1. Copy env template:
   ```bash
   cp .env.example .env
   ```
2. Set required secrets in `.env` (at minimum `AUTH_SECRET_KEY`). `OPENAI_API_KEY` can be blank for boot/auth.
3. Start stack:
   ```bash
   docker compose up --build
   ```
4. Migrations run automatically on app startup in Docker (`alembic upgrade head` via `scripts/start-app.sh`).
5. Qdrant is started by Compose, but app/worker dependencies use `service_started` so API startup is not blocked by Qdrant healthcheck fragility.

API: `http://localhost:8001`  
Frontend (dev): `http://localhost:5174`

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
npm run dev -- --host 0.0.0.0 --port 5174
```


Detailed Docker + frontend + LAN setup steps: see `docs/LOCAL_DEV.md`.

CORS example for local + LAN dev:

```env
ALLOWED_ORIGINS=http://localhost:5174,http://127.0.0.1:5174,http://192.168.1.50:5174
```

## Environment variables

| Key | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | SQLAlchemy + Alembic database connection |
| `REDIS_URL` | Yes | Redis cache + Celery broker default |
| `CELERY_BROKER_URL` | Yes | Celery broker URL |
| `CELERY_RESULT_BACKEND` | Yes | Celery result backend |
| `OPENAI_API_KEY` | Yes for AI features | OpenAI API key for analysis + embeddings |
| `OPENAI_MODEL` | Optional | Chat model id (default `gpt-4o-mini`) |
| `OPENAI_EMBEDDING_MODEL` | Optional | Embedding model id (default `text-embedding-3-small`) |
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

## AI provider model

- The backend is now **OpenAI-only** for document analysis, category discovery, and semantic embeddings.
- Local transformer embedding runtime paths were removed (no `sentence-transformers`, Torch/CUDA/NVIDIA dependency chain in the app path).
- Qdrant remains the vector database for semantic search.


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

## AI Pipeline Validation

- **No-key mode (`OPENAI_API_KEY=`)**:
  - Backend and auth flows should still boot/work.
  - Upload + text extraction still run.
  - Document processing completes, but `processing_error` is populated with an AI-unavailable message and intelligence endpoints can remain empty.
  - Regenerate intelligence endpoint returns `503` with actionable guidance to configure `OPENAI_API_KEY`.
  - Semantic search degrades gracefully to empty semantic results; keyword search remains available.
- **With-key mode**:
  - Upload should produce summary, key points/tags/entities, suggested category, review items, and action items.
  - Relationship detection/review queue endpoints should function based on available source documents.
- **Manual validation checklist**:
  1. Upload a small PDF.
  2. Confirm summary/category/intelligence appear on the document detail view.
  3. Confirm review queue + action item lifecycle actions work.
  4. Confirm relationship review empty/success states.
  5. Confirm search returns uploaded docs (keyword; semantic when embeddings are enabled).
  6. Confirm dashboard/review/action metrics load and update.
  7. Repeat with blank `OPENAI_API_KEY` and confirm graceful AI-unavailable behavior.

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

## Admin panel (Plan B)

- Seeded initial admin behavior: if `INITIAL_ADMIN_EMAIL` + `INITIAL_ADMIN_PASSWORD` are configured, startup seed ensures that account exists and is promoted to `admin` (idempotent).
- Access `/admin` after login with an account whose role is `admin`.
- Current capabilities:
  - User list with pagination.
  - Role updates (`viewer` / `editor` / `admin`) with last-admin demotion protection.
  - Admin audit explorer for role-change events.
  - System metrics (users, documents, processing, review/action/relationship pending counts).
- Known limitations:
  - Admin audit currently tracks admin role-management actions only.
  - Admin panel pagination is basic next/prev only.
