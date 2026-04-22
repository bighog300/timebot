.PHONY: backend-install migrate backend frontend bootstrap test-backend test-frontend ci-backend ci-frontend ci-integrated-smoke

backend-install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements-dev.txt

migrate:
	alembic upgrade head

backend:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm install && npm run dev

bootstrap:
	./scripts/bootstrap_dev.sh

test-backend:
	pytest tests -q

test-frontend:
	cd frontend && npm run test

ci-backend:
	python -m pip install --upgrade pip
	python -m pip install -r requirements-dev.txt
	pytest tests -q

ci-frontend:
	cd frontend && npm ci
	cd frontend && npm run type-check
	cd frontend && npm run lint
	cd frontend && npm run test
	cd frontend && npm run build

ci-integrated-smoke:
	bash frontend/tests/e2e/smoke.sh
