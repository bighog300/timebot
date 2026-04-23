#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
HEALTH_URL="$BASE_URL/health"
ROOT_URL="$BASE_URL/"

echo "Waiting for backend health endpoint: $HEALTH_URL"
for _ in {1..45}; do
  if curl -fsS "$HEALTH_URL" >/tmp/timebot-health.json; then
    break
  fi
  sleep 2
done

health_status=$(python - <<'PY2'
import json
from pathlib import Path
try:
    data = json.loads(Path('/tmp/timebot-health.json').read_text())
    print(data.get('status', ''))
except Exception:
    print('')
PY2
)
if [[ "$health_status" != "healthy" ]]; then
  echo "Health endpoint did not report healthy status"
  cat /tmp/timebot-health.json
  exit 1
fi

http_code=$(curl -sS -o /tmp/timebot-root.json -w '%{http_code}' "$ROOT_URL")
if [[ "$http_code" != "200" ]]; then
  echo "Expected root endpoint HTTP 200, got: $http_code"
  cat /tmp/timebot-root.json
  exit 1
fi

echo "Smoke check passed: /health and / responded successfully"
