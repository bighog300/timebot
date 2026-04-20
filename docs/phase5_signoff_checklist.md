# Phase 5 Final Signoff Checklist

## Purpose

Determine whether the repository is **release-ready** after Phase 5
hardening.

------------------------------------------------------------------------

## Blocking Rule

If ANY required item fails → Phase 5 is NOT complete.

------------------------------------------------------------------------

## 1. Environment Setup

### Backend

-   [ ] Install dependencies: `pip install -r requirements.txt`

### Frontend

-   [ ] Install dependencies:\

``` bash
cd frontend
npm install
```

-   [ ] No registry/proxy errors

------------------------------------------------------------------------

## 2. Backend Validation

-   [ ] `pytest -q` passes
-   [ ] Backend starts:

``` bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

------------------------------------------------------------------------

## 3. Frontend Validation

``` bash
cd frontend
npm run type-check
npm run lint
npm run test
npm run build
```

-   [ ] All pass

------------------------------------------------------------------------

## 4. E2E Runtime

-   [ ] Documents page loads

-   [ ] Search works

-   [ ] Queue updates

-   [ ] Insights load

-   [ ] Connections actions work

-   [ ] Smoke test:

``` bash
bash frontend/tests/e2e/smoke.sh
```

------------------------------------------------------------------------

## 5. Websockets

-   [ ] Live updates refresh UI
-   [ ] No crashes on bad payloads

------------------------------------------------------------------------

## 6. UX Hardening

-   [ ] Loading states
-   [ ] Empty states
-   [ ] Error states
-   [ ] Responsive layout

------------------------------------------------------------------------

## 7. Deployment

-   [ ] Docker build or documented deploy path

------------------------------------------------------------------------

## 8. Final Decision

-   [ ] ✅ Ready
-   [ ] ❌ Not Ready

## If not ready, list blockers:

-   
-   
