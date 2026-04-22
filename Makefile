.PHONY: backend-install migrate backend frontend bootstrap test-backend test-frontend

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
