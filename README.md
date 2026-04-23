# Timebot — AI Document Intelligence Platform

Timebot is an AI-assisted document intelligence platform for uploading, analyzing, searching, and operationalizing documents through a FastAPI backend, React frontend, and background workers.

## Features

- AI-assisted document upload, parsing, and analysis
- Hybrid search and retrieval workflows
- Review queue and confidence-driven processing
- Background processing via Celery workers
- Connector foundations for external providers
- Real-time updates via WebSocket events

## Prerequisites

- Docker + Docker Compose
- Node.js 20+
- Python 3.11+
- Anthropic API key

## Quick Start (Docker)

1. Clone the repository:
   ```bash
   git clone https://github.com/{YOUR_GITHUB_USERNAME}/{YOUR_REPO_NAME}.git
   cd {YOUR_REPO_NAME}
   ```
2. Copy environment template:
   ```bash
   cp .env.example .env
   ```
3. Add your API key(s) in `.env` (at minimum `OPENAI_API_KEY`; set `AI_MODEL` as needed).
4. Start the stack:
   ```bash
   docker compose up --build
   ```
5. Access the app:
   - API: `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - Frontend dev server: `http://localhost:5173`

## Local Development (without Docker)

### Backend

```bash
python -m pip install -r requirements-dev.txt
alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### Background workers

```bash
celery -A app.workers.celery_app worker --loglevel=info -Q documents,maintenance
celery -A app.workers.celery_app beat --loglevel=info
celery -A app.workers.celery_app flower --port=5555
```

## Environment Variables

| Variable | Description | Required | Default |
|---|---|---|---|
| `DEBUG` | Enable debug/reload behavior | No | `false` |
| `APP_HOST` | App host bind address | No | `0.0.0.0` |
| `APP_PORT` | App port | No | `8000` |
| `ALLOWED_ORIGINS` | CORS origins (CSV) | Yes | `http://localhost:5173,http://localhost:3000` |
| `DATABASE_URL` | Postgres connection string | Yes | `postgresql://docuser:docpass@localhost:5432/documents` |
| `ALEMBIC_SKIP` | Test-only migration bypass | No | `false` |
| `REDIS_URL` | Redis connection URL | Yes | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | Yes | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend URL | Yes | `redis://localhost:6379/0` |
| `CELERY_WORKER_CONCURRENCY` | Worker concurrency | No | `4` |
| `CELERY_TASK_MAX_RETRIES` | Max task retries | No | `3` |
| `CELERY_TASK_SERIALIZER` | Celery task serializer | No | `json` |
| `CELERY_RESULT_SERIALIZER` | Celery result serializer | No | `json` |
| `CELERY_ACCEPT_CONTENT` | Accepted Celery payloads | No | `json` |
| `CELERY_TIMEZONE` | Celery timezone | No | `UTC` |
| `CELERY_ENABLE_UTC` | Enable UTC for Celery | No | `true` |
| `CELERY_WORKER_MAX_TASKS_PER_CHILD` | Worker recycle threshold | No | `1000` |
| `CELERY_TASK_TIME_LIMIT` | Hard task timeout seconds | No | `600` |
| `CELERY_TASK_SOFT_TIME_LIMIT` | Soft task timeout seconds | No | `540` |
| `CELERY_TASK_DEFAULT_RETRY_DELAY` | Retry delay seconds | No | `60` |
| `OPENAI_API_KEY` | AI provider API key | Yes | _none_ |
| `OPENAI_MODEL` | OpenAI chat model ID | No | `gpt-4o-mini` |
| `OPENAI_EMBEDDING_MODEL` | Embedding model ID | No | `text-embedding-3-small` |
| `AI_MODEL` | Anthropic-style model setting used by app config | No | `claude-sonnet-4-20250514` |
| `AI_MAX_TOKENS` | Max model output tokens | No | `4096` |
| `AUTH_SECRET_KEY` | JWT signing key | Yes (non-dev) | `dev-insecure-change-me` |
| `AUTH_ALGORITHM` | JWT algorithm | No | `HS256` |
| `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | No | `60` |
| `STORAGE_PATH` | Base file storage path | No | `./data` |
| `UPLOAD_PATH` | Upload directory | No | `./data/uploads` |
| `PROCESSED_PATH` | Processed output directory | No | `./data/processed` |
| `QDRANT_HOST` | Qdrant host | No | `localhost` |
| `QDRANT_PORT` | Qdrant port | No | `6333` |
| `ENABLE_AUTO_CATEGORIZATION` | Enable auto categorization | No | `true` |
| `ENABLE_ENTITY_EXTRACTION` | Enable entity extraction | No | `true` |
| `CATEGORY_CONFIDENCE_THRESHOLD` | Category confidence threshold | No | `0.7` |
| `REVIEW_CONFIDENCE_THRESHOLD` | Review confidence threshold | No | `0.75` |
| `MAX_UPLOAD_SIZE_MB` | Max upload size (MB) | No | `50` |
| `ALLOWED_FILE_TYPES` | Allowed upload file extensions (CSV) | No | `pdf,docx,doc,xlsx,xls,pptx,ppt,txt,jpg,jpeg,png,gif,tiff,bmp` |
| `GOOGLE_OAUTH_CLIENT_ID` | Google OAuth client ID | No | _none_ |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Google OAuth client secret | No | _none_ |
| `GOOGLE_OAUTH_REDIRECT_URI` | OAuth callback URL | No | `http://localhost:5173/connections/callback?provider=gdrive` |
| `GOOGLE_OAUTH_SCOPES` | OAuth scopes (CSV) | No | `openid,email,profile,https://www.googleapis.com/auth/drive.metadata.readonly` |
| `CONNECTOR_TOKEN_ENCRYPTION_KEY` | Fernet key for encrypted connector tokens | Required when connectors enabled | _none_ |

## Architecture

```text
├── app/
│   ├── api/v1/          # Route handlers (documents, search, upload, queue, insights, connections, analysis, websocket)
│   ├── crud/            # Database CRUD helpers
│   ├── db/              # SQLAlchemy engine and session
│   ├── models/          # ORM models (Document, Category, Connection, relationships)
│   ├── prompts/         # Anthropic prompt templates
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # Business logic (AI analyzer, search, text extractor, insights, etc.)
│   ├── workers/         # Celery tasks, beat scheduler, monitoring
│   └── config.py        # Settings (pydantic-settings)
├── frontend/            # React + TypeScript UI (Vite, TanStack Query, Tailwind)
├── docs/                # Planning docs and sprint bundles
├── tests/               # Backend pytest suite
├── schema.sql           # Reference SQL schema (Alembic manages migrations)
├── app.py               # Local dev entry point (python app.py)
├── Dockerfile
└── docker-compose.yml
```

## Running Tests

```bash
pytest tests/ -q
cd frontend && npm run test
```

## Database Migrations

```bash
alembic upgrade head
```

## API Reference

When the app is running, open: `http://localhost:8000/docs`

## WebSocket Events

- `ws://localhost:8000/api/v1/ws`
- `connection_update`
- `connection_sync`
- `queue_update`

## Queue Endpoints

- `GET /api/v1/queue/stats`
- `GET /api/v1/queue/items`
- `POST /api/v1/queue/items/{item_id}/approve`
- `POST /api/v1/queue/items/{item_id}/reject`

## Deployment

### Docker Hub

Build and push using your preferred CI/CD flow or local Docker commands.

### GitHub Container Registry

Tag and push images under `ghcr.io/{YOUR_GITHUB_USERNAME}/{YOUR_REPO_NAME}`.

## GitHub Actions

See `.github/workflows/` for CI/CD pipeline definitions.

## Security Notes

- Use a strong non-default `AUTH_SECRET_KEY` outside local development.
- Restrict `ALLOWED_ORIGINS` to trusted frontend domains.
- Keep OAuth secrets and API keys in a secure secret manager.

## Contributing

1. Create a branch from `main`.
2. Run backend and frontend checks locally.
3. Open a PR with a clear summary and validation notes.

## License

MIT
