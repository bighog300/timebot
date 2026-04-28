# Stage 5: Polish, Hardening, and Regression Pass

## Goal
Stabilize the Phase 4 feature set and ensure it remains aligned with Timebot's document organizer scope.

## Tasks
- add enum validation where missing
- ensure no duplicate open review item regressions
- ensure audit event consistency
- ensure bulk operations are transactionally safe
- ensure metrics endpoints are performant enough for current scale
- update API docs/comments if the repo has them
- run full regression suite

## Hard No
Do not reintroduce:
- crawler
- scraping
- source profiling
- source mapping
- URL families
- crawl runs
- crawl pages

## Validation Commands
```bash
pytest -q
python -m compileall app tests
```
