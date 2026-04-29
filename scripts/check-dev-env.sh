#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/5] docker compose config"
docker compose config >/dev/null

echo "[2/5] backend health endpoint"
curl -fsS http://localhost:8001/health >/dev/null

echo "[3/5] qdrant endpoint"
curl -fsS http://localhost:6335/collections >/dev/null

echo "[4/5] frontend env variables"
if [[ ! -f frontend/.env ]]; then
  echo "frontend/.env is missing (copy from frontend/.env.example)" >&2
  exit 1
fi
rg -n '^VITE_API_URL=' frontend/.env >/dev/null

echo "[5/5] CORS preflight /api/v1/auth/register"
ORIGIN="${CHECK_ORIGIN:-http://localhost:5174}"
ALLOW_ORIGIN_HEADER=$(curl -si -X OPTIONS "http://localhost:8001/api/v1/auth/register" \
  -H "Origin: ${ORIGIN}" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" | tr -d '\r' | awk -F': ' 'tolower($1)=="access-control-allow-origin"{print $2; exit}')

if [[ -z "${ALLOW_ORIGIN_HEADER}" ]]; then
  echo "Missing Access-Control-Allow-Origin for origin ${ORIGIN}" >&2
  exit 1
fi

echo "All checks passed."
