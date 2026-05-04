.PHONY: backend-install migrate backend frontend bootstrap test-backend test-frontend ci-backend ci-frontend ci-integrated-smoke deploy-push

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
	cd frontend && npm run test:frontend:unit

ci-backend:
	python -m pip install --upgrade pip
	python -m pip install -r requirements-dev.txt
	pytest tests -q

ci-frontend:
	cd frontend && npm ci
	cd frontend && npm run typecheck
	cd frontend && npm run lint
	cd frontend && npm run build

ci-integrated-smoke:
	bash frontend/tests/e2e/smoke.sh


deploy-push:
	@if [ "${ALLOW_IMAGE_PUSH}" != "1" ]; then \
		echo "Image push disabled. Set ALLOW_IMAGE_PUSH=1 only for intentional deploys."; \
		exit 1; \
	fi
	@if [ -z "${IMAGE}" ]; then echo "Set IMAGE=<image:tag>"; exit 1; fi
	./scripts/deploy-push.sh "${IMAGE}"
