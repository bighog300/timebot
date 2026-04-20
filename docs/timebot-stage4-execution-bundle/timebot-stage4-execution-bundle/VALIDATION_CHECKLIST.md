# Stage 4 Validation Checklist

## Foundation
- [ ] `frontend/` exists in the repo root
- [ ] `npm install` or equivalent succeeds
- [ ] `npm run dev` starts the frontend
- [ ] `npm run build` succeeds
- [ ] `npm run type-check` succeeds
- [ ] `npm run lint` succeeds

## App shell
- [ ] layout renders correctly on desktop
- [ ] layout works on mobile widths
- [ ] navigation routes work
- [ ] loading, empty, and error states exist
- [ ] toasts/modals/tooltips/skeletons function

## Documents
- [ ] document feed loads from backend
- [ ] timeline view works
- [ ] grid or list alternative view works
- [ ] document detail opens and renders metadata
- [ ] update/favorite/archive actions work
- [ ] delete action works
- [ ] reprocess action works

## Upload and processing
- [ ] upload flow succeeds
- [ ] uploaded document appears in feed
- [ ] processing status updates are visible
- [ ] websocket updates are handled gracefully
- [ ] failed processing can be retried

## Search
- [ ] keyword search works
- [ ] semantic search works
- [ ] suggestions render
- [ ] facets render
- [ ] filters apply correctly
- [ ] similar documents render from detail view

## Categories and insights
- [ ] categories page loads
- [ ] category counts are visible
- [ ] insights overview loads
- [ ] trends/cards/widgets render from real data
- [ ] action items and tags/entities are visible where supported

## Connections
- [ ] connections page loads
- [ ] provider cards render
- [ ] connect/disconnect actions behave correctly
- [ ] sync action behaves correctly
- [ ] sync history or logs render if implemented

## Quality
- [ ] core hooks/components have unit tests
- [ ] smoke E2E tests exist for upload, search, and detail flows
- [ ] keyboard navigation works for major actions
- [ ] color contrast and focus states are acceptable
- [ ] network failures produce usable UI errors

## Release readiness
- [ ] README updated with frontend setup
- [ ] environment variables documented
- [ ] API contract assumptions documented
- [ ] no placeholder or mock data ships unintentionally
