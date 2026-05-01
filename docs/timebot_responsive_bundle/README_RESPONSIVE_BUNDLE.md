# Timebot Responsive Web + Mobile Completion Bundle

## Purpose

Complete responsive web + mobile polish for Timebot while preserving the desktop web experience.

This is **not** a mobile-only redesign. Timebot should remain:

- a powerful desktop web application for deep document analysis
- a usable tablet experience for review workflows
- a focused mobile web experience for browsing, chat, and quick actions

## Scope

This bundle covers:

1. App shell and navigation responsiveness
2. Shared responsive layout primitives
3. Documents page responsive polish
4. Chat page responsive polish
5. Timeline adaptive desktop/mobile behavior
6. Relationships responsive polish
7. Reports responsive polish
8. Admin responsive polish
9. Final responsive QA pass

## Hard Guardrails

Do **not**:

- change backend APIs
- add new backend functionality
- remove existing desktop functionality
- make Timebot mobile-only
- add unrelated product features
- add crawling/scraping/URL ingestion
- break auth/admin guards
- break citations, insights, reports, timeline, relationships, or chat streaming

## Required Commands

After each task:

```bash
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build
```

Backend tests are not required unless backend files are changed, which should not happen in this bundle.

## Design Direction

Use adaptive responsive design:

| Device | Intent |
|---|---|
| Desktop | Dense analysis, multi-panel, power-user workflows |
| Tablet | Review, touch-friendly exploration |
| Mobile | Focused browsing, chat, quick actions |

## Responsive Principles

- Use `min-w-0` on flex/grid children.
- Use `break-words`, `whitespace-pre-wrap`, and safe overflow handling for long text.
- Avoid wide tables on mobile; use cards or horizontal scroll only when unavoidable.
- Use `flex-wrap` for action bars and filters.
- Keep primary actions reachable on mobile.
- Preserve desktop density where useful.
- Do not hide important features; adapt layout instead.

## Definition of Done

This bundle is complete when:

- all major pages work on desktop and mobile widths
- no obvious horizontal overflow exists
- desktop UX is not degraded
- mobile navigation is usable
- all frontend tests/lint/build pass
- no backend changes are required
