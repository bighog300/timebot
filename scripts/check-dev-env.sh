#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-http://localhost:5174}"
API_URL="${API_URL:-http://localhost:8001}"

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; exit 1; }

printf '[1/6] docker compose config... '
docker compose config >/dev/null && pass "compose config" || fail "compose config"

printf '[2/6] backend health... '
curl -fsS "${API_URL}/health" >/dev/null && pass "backend health" || fail "backend health"

printf '[3/6] CORS preflight... '
ALLOW_ORIGIN_HEADER=$(curl -si -X OPTIONS "${API_URL}/api/v1/auth/register" \
  -H "Origin: ${FRONTEND_ORIGIN}" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,authorization" | tr -d '\r' | awk -F': ' 'tolower($1)=="access-control-allow-origin"{print $2; exit}')
[[ "${ALLOW_ORIGIN_HEADER}" == "${FRONTEND_ORIGIN}" ]] && pass "preflight for ${FRONTEND_ORIGIN}" || fail "CORS allow origin mismatch (${ALLOW_ORIGIN_HEADER})"

printf '[4/6] auth register/login smoke... '
EMAIL="timebot-smoke-$(date +%s)@example.com"
PASSWORD="password123"
REGISTER_STATUS=$(curl -s -o /tmp/timebot-register.json -w "%{http_code}" -X POST "${API_URL}/api/v1/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\",\"display_name\":\"Smoke User\"}")
LOGIN_STATUS=$(curl -s -o /tmp/timebot-login.json -w "%{http_code}" -X POST "${API_URL}/api/v1/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}")
[[ "${REGISTER_STATUS}" == "201" && "${LOGIN_STATUS}" == "200" ]] && pass "register/login" || fail "register=${REGISTER_STATUS} login=${LOGIN_STATUS}"

printf '[5/6] qdrant endpoint... '
curl -fsS http://localhost:6335/healthz >/dev/null && pass "qdrant healthz" || fail "qdrant healthz"

printf '[6/6] frontend env file... '
[[ -f frontend/.env ]] && rg -n '^VITE_API_URL=' frontend/.env >/dev/null && pass "frontend env present" || fail "frontend/.env missing or VITE_API_URL unset"
