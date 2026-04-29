# Local development (Docker backend + Vite frontend)

## Backend

1. Copy backend env:
   ```bash
   cp .env.example .env
   ```
2. Set required values in `.env`:
   - `AUTH_SECRET_KEY`
   - `OPENAI_API_KEY`
3. Start infrastructure + API:
   ```bash
   docker compose up --build
   ```
4. Run DB migrations:
   ```bash
   docker compose exec app alembic upgrade head
   ```
5. Verify health:
   ```bash
   curl http://localhost:8001/health
   ```

## Frontend

```bash
cd frontend
cp .env.example .env
# confirm VITE_API_URL=http://localhost:8001
npm install
npm run dev -- --host 0.0.0.0 --port 5174
```

## LAN usage

Use your machine LAN IP (example placeholder `<LAN_IP>`):

- `frontend/.env`
  - `VITE_API_URL=http://<LAN_IP>:8001`
  - `VITE_WS_URL=ws://<LAN_IP>:8001`
- backend `.env`
  - `ALLOWED_ORIGINS=http://<LAN_IP>:5174`

You can include multiple origins in `ALLOWED_ORIGINS` as comma-separated values.
