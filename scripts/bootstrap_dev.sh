#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from template; update secrets before shared/prod use."
fi

alembic upgrade head

echo "Backend ready. Start services with:"
echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "  (new shell) cd frontend && npm install && npm run dev"
