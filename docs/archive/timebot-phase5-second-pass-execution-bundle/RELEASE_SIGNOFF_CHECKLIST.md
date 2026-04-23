# Release Signoff Checklist

Mark release-ready only when the following are true.

## Backend
- [ ] `pytest -q` passes
- [ ] new insights/connections behavior is covered by tests where appropriate
- [ ] config/import fallbacks behave as intended and are documented

## Frontend install and static validation
- [ ] package manager is standardized
- [ ] install succeeds
- [ ] `type-check` passes
- [ ] `lint` passes
- [ ] `test` passes
- [ ] `build` passes

## Runtime validation
- [ ] backend starts from docs
- [ ] frontend starts from docs
- [ ] documents page works
- [ ] document detail works
- [ ] search works
- [ ] queue page works
- [ ] categories page works
- [ ] insights page works
- [ ] connections page works

## Live updates
- [ ] websocket connection is stable
- [ ] queue updates refresh UI
- [ ] processing events refresh UI
- [ ] connection actions refresh UI safely

## UX hardening
- [ ] loading states checked
- [ ] empty states checked
- [ ] error states checked
- [ ] destructive actions provide clear feedback
- [ ] responsive layout checked on key breakpoints

## Deployment path
- [ ] Docker / deployment path validated or explicitly documented as unverified
- [ ] required env vars documented
- [ ] build/start commands documented
- [ ] release notes summarize accepted risks, if any

## Final decision
- [ ] Ready to release
- [ ] Not ready — blockers recorded with evidence
