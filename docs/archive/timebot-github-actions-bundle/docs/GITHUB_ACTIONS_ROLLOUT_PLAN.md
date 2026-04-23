# GitHub Actions Rollout Plan

## Objective
Implement reliable CI/CD for this repository without overcomplicating the initial rollout.

## Phase 1 — PR Safety
Add:
- backend CI
- frontend CI

Make both required checks on pull requests to `main`.

### Success criteria
- Python tests run on every relevant PR
- frontend install, type-check, lint, test, and build run on every frontend PR
- failures block merge

## Phase 2 — Integration Confidence
Add:
- integrated backend + frontend smoke workflow

### Success criteria
- PRs verify the app boots end to end
- smoke flow catches broken API/base URL/runtime issues

## Phase 3 — Deployment Validation
Add:
- Docker validation workflow

### Success criteria
- Docker config is syntactically valid
- images can build
- startup assumptions are checked

## Phase 4 — Controlled Deployments
Add:
- deployment workflow with staging and production environments

### Success criteria
- deploys are environment-gated
- production requires approval
- only one deploy per environment runs at a time

## Phase 5 — Ongoing Confidence
Add:
- nightly workflow

### Success criteria
- scheduled builds continue to validate repo health
- slower checks do not block every PR but still run regularly
