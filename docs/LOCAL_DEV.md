# Local development (Docker backend + Vite frontend)

## Fresh setup

### Backend

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"
# paste generated value into AUTH_SECRET_KEY in .env
# set ALLOWED_ORIGINS for your frontend host(s)
docker compose up --build
```

> Migrations run automatically before API startup in Docker (`alembic upgrade head`).
> `OPENAI_API_KEY` can stay blank for boot, register, and login. Add it later for AI enrichment/embeddings.
> Qdrant is started by Docker Compose, but the API/worker now wait only for Qdrant container start (not a healthcheck gate) to avoid blocked startup loops.

### Frontend

```bash
cd frontend
cp .env.example .env
# set VITE_API_URL=http://localhost:8001
npm install
npm run dev -- --host 0.0.0.0 --port 5174
```

## LAN setup

Backend `.env`:

```env
ALLOWED_ORIGINS=http://<LAN_IP>:5174,http://localhost:5174,http://127.0.0.1:5174
```

Frontend `frontend/.env`:

```env
VITE_API_URL=http://<LAN_IP>:8001
VITE_WS_URL=ws://<LAN_IP>:8001
```

Google Drive OAuth (backend `.env`):

```env
GOOGLE_OAUTH_CLIENT_ID=<google-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<google-client-secret>
GOOGLE_OAUTH_REDIRECT_URI=http://<LAN_IP>:5174/connections/callback?provider=gdrive
GOOGLE_OAUTH_SCOPES=openid,email,profile,https://www.googleapis.com/auth/drive.metadata.readonly
```

The Google Drive connector will return HTTP 400 until these values are configured, and the exact `GOOGLE_OAUTH_REDIRECT_URI` must also be added to your Google Cloud OAuth client.

## First login

- Option A: Register via UI.
- Option B (optional): set `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD`, and `INITIAL_ADMIN_NAME` in backend `.env` before startup.

## Troubleshooting

CORS preflight:

```bash
curl -i -X OPTIONS http://localhost:8001/api/v1/auth/register \
  -H "Origin: http://localhost:5174" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,authorization"
```

Health:

```bash
curl http://localhost:8001/health
```

WebSocket URL check:

- If `VITE_WS_URL` is unset, frontend derives `ws://` or `wss://` from `VITE_API_URL`.
- Socket endpoint must be `/api/v1/ws/all`.

Port notes:

- Backend host port is `8001` (container still listens on `8000`) to avoid local conflicts.
- Frontend dev port is `5174` to avoid conflicts with common `5173` usage.


Backend unreachable on 8001:

```bash
curl -i http://localhost:8001/health
docker compose ps
```

If backend is not reachable, confirm container startup logs:

```bash
docker compose logs app --tail=200
```

Frontend dev port mismatch (5174 expected):

```bash
npm --prefix frontend run dev -- --host 0.0.0.0 --port 5174
```

Qdrant dashboard:

- Open `http://localhost:6335/dashboard` in browser.
- API root check: `curl http://localhost:6335/`.
