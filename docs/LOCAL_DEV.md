# Local development (Docker backend + Vite frontend)

## Fresh setup

### Backend

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"
# paste generated value into AUTH_SECRET_KEY in .env
# set ALLOWED_ORIGINS for your frontend host(s)
docker compose up --build
docker compose exec app alembic upgrade head
```

> `OPENAI_API_KEY` can stay blank for boot, register, and login. Add it later for AI enrichment/embeddings.

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
