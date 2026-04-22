#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
EMAIL="smoke.$(date +%s)@example.com"
PASSWORD="Passw0rd!123"
DISPLAY_NAME="Smoke User"

require_jq() {
  if ! command -v jq >/dev/null 2>&1; then
    echo "jq is required for smoke.sh" >&2
    exit 1
  fi
}

require_jq

echo "[1/7] Register"
register_payload=$(jq -n --arg email "$EMAIL" --arg password "$PASSWORD" --arg display_name "$DISPLAY_NAME" '{email:$email,password:$password,display_name:$display_name}')
register_resp=$(curl -sS -w '\n%{http_code}' -H 'Content-Type: application/json' -d "$register_payload" "$BASE_URL/api/v1/auth/register")
register_body=$(echo "$register_resp" | head -n -1)
register_code=$(echo "$register_resp" | tail -n1)
[[ "$register_code" == "201" ]]

echo "[2/7] Login"
login_payload=$(jq -n --arg email "$EMAIL" --arg password "$PASSWORD" '{email:$email,password:$password}')
login_resp=$(curl -sS -w '\n%{http_code}' -H 'Content-Type: application/json' -d "$login_payload" "$BASE_URL/api/v1/auth/login")
login_body=$(echo "$login_resp" | head -n -1)
login_code=$(echo "$login_resp" | tail -n1)
[[ "$login_code" == "200" ]]
TOKEN=$(echo "$login_body" | jq -r '.access_token')
[[ -n "$TOKEN" && "$TOKEN" != "null" ]]

auth_header=( -H "Authorization: Bearer $TOKEN" )

echo "[3/7] Upload"
pdf_file=$(mktemp /tmp/timebot-smoke-XXXXXX.pdf)
printf '%s' '%PDF-1.1
1 0 obj<<>>endobj
trailer<<>>
%%EOF' > "$pdf_file"
upload_resp=$(curl -sS -w '\n%{http_code}' "${auth_header[@]}" -F "file=@$pdf_file;type=application/pdf" "$BASE_URL/api/v1/upload")
rm -f "$pdf_file"
upload_body=$(echo "$upload_resp" | head -n -1)
upload_code=$(echo "$upload_resp" | tail -n1)
[[ "$upload_code" == "202" ]]
DOC_ID=$(echo "$upload_body" | jq -r '.id')
[[ -n "$DOC_ID" && "$DOC_ID" != "null" ]]

echo "[4/7] Poll document processing"
for _ in {1..30}; do
  doc_resp=$(curl -sS "${auth_header[@]}" "$BASE_URL/api/v1/documents/$DOC_ID")
  status=$(echo "$doc_resp" | jq -r '.processing_status')
  if [[ "$status" == "completed" || "$status" == "failed" ]]; then
    break
  fi
  sleep 1
done
[[ "$status" == "completed" || "$status" == "failed" ]]

echo "[5/7] Search"
search_resp=$(curl -sS -w '\n%{http_code}' "${auth_header[@]}" -X POST "$BASE_URL/api/v1/search?query=smoke&limit=5&skip=0")
search_code=$(echo "$search_resp" | tail -n1)
[[ "$search_code" == "200" ]]

echo "[6/7] Insights actions"
insights_resp=$(curl -sS -w '\n%{http_code}' "${auth_header[@]}" "$BASE_URL/api/v1/insights/overview")
insights_body=$(echo "$insights_resp" | head -n -1)
insights_code=$(echo "$insights_resp" | tail -n1)
[[ "$insights_code" == "200" ]]
echo "$insights_body" | jq . >/dev/null

echo "[7/7] Frontend shell"
curl -fsS http://127.0.0.1:3000/ >/dev/null

echo "smoke flow completed"
