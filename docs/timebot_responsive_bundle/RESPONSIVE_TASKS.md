# Responsive Completion Tasks

## Task 1 — Responsive AppShell + Navigation

```text
Proceed with Responsive Bundle Task 1 only.

Task: Improve AppShell responsive navigation for desktop and mobile.

Requirements:
- Preserve existing routes and auth/admin guards.
- Desktop:
  - keep current sidebar/navigation behavior where appropriate.
  - preserve admin-only navigation visibility.
- Mobile:
  - collapse navigation into a compact top menu or bottom nav.
  - navigation must not consume excessive vertical space.
  - navigation should be touch-friendly.
- Main layout:
  - ensure content wrapper uses min-w-0.
  - apply responsive padding.
  - avoid horizontal page overflow.
- Do not redesign individual pages yet.
- Do not change backend.

Tests:
- desktop navigation still renders.
- mobile navigation controls render.
- admin links still only show for admin users.
- main content renders.
- routes remain unchanged.

Run:
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build

Report:
- files changed
- tests added
- test results
- limitations/follow-up
```

---

## Task 2 — Shared Responsive Layout Primitives

```text
Proceed with Responsive Bundle Task 2 only.

Task: Add reusable responsive layout helpers.

Requirements:
- Add lightweight frontend components/helpers where useful:
  - ResponsivePage
  - PageHeader
  - ResponsiveGrid
  - ResponsiveActionBar
  - StickyMobileActionBar if needed
- Use existing Tailwind/style conventions.
- Do not add a new design-system dependency.
- Convert only obvious duplicated patterns in 1–2 pages initially.
- Preserve page behavior.
- Do not change backend.

Tests:
- helper components render children correctly.
- expected responsive classes exist.
- converted pages still render.

Run:
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build

Report:
- files changed
- tests added
- test results
- limitations/follow-up
```

---

## Task 3 — Documents Page Responsive Completion

```text
Proceed with Responsive Bundle Task 3 only.

Task: Complete responsive polish for Documents page.

Requirements:
- Desktop:
  - preserve dense document browsing.
  - keep upload, Gmail import, clusters, onboarding hints, and first-document success panel.
- Mobile:
  - use stacked card/list behavior.
  - avoid horizontal overflow.
  - make upload/import actions easy to reach.
  - ensure document clusters stack cleanly.
- Preserve:
  - onboarding hints.
  - first-document success panel.
  - document clusters.
  - existing document links/actions.
- Do not change backend.

Tests:
- documents render in responsive card/list layout.
- upload/Gmail controls remain accessible.
- onboarding hints still render.
- clusters still render.
- no mobile test assumptions rely on wide table-only layout.

Run:
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build

Report:
- files changed
- tests added
- test results
- limitations/follow-up
```

---

## Task 4 — Chat Page Responsive Completion

```text
Proceed with Responsive Bundle Task 4 only.

Task: Complete responsive polish for Chat page.

Requirements:
- Desktop:
  - preserve comfortable wide chat reading.
  - keep citations, follow-ups, shortcuts, streaming, and message grouping.
- Mobile:
  - sticky input remains accessible.
  - messages use available width without overflow.
  - citations collapse cleanly.
  - follow-ups and shortcuts wrap cleanly.
- Preserve:
  - streaming behavior.
  - citations.
  - follow-up suggestions.
  - cross-feature shortcuts.
  - source_refs behavior.
- Do not change backend.

Tests:
- sticky input remains present.
- long messages wrap safely.
- citations still expand/collapse.
- follow-ups and shortcuts render/wrap.
- streaming tests still pass.

Run:
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build

Report:
- files changed
- tests added
- test results
- limitations/follow-up
```

---

## Task 5 — Timeline Adaptive Desktop/Mobile View

```text
Proceed with Responsive Bundle Task 5 only.

Task: Complete responsive polish for Timeline page.

Requirements:
- Desktop:
  - preserve existing Gantt/timeline visualization.
  - preserve zoom, grouping, milestones, gaps, signal labels, and document navigation.
- Mobile:
  - provide or improve a stacked timeline list/card view.
  - event cards should be tappable.
  - grouped events should expand cleanly.
  - document navigation links remain usable.
  - gap/milestone/signal labels remain readable.
- Do not remove existing desktop chart behavior.
- Do not change backend.

Tests:
- desktop timeline chart still renders.
- mobile-friendly event list/card structure renders.
- grouped expansion still works.
- milestones/gaps/signal labels still render.
- document navigation links still work.

Run:
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build

Report:
- files changed
- tests added
- test results
- limitations/follow-up
```

---

## Task 6 — Relationships Responsive Completion

```text
Proceed with Responsive Bundle Task 6 only.

Task: Complete responsive polish for relationship review and document relationship cards.

Requirements:
- Desktop:
  - preserve filters, grouping, review actions, explainability details, and cluster navigation.
- Mobile:
  - stack relationship cards.
  - filters should wrap or collapse cleanly.
  - Confirm/Reject actions must remain touch-friendly.
  - Why related details must remain readable.
- Preserve:
  - inline review actions.
  - cluster navigation.
  - confidence display.
  - explanation metadata behavior.
  - missing metadata safety.
- Do not change backend.

Tests:
- filters render responsively.
- relationship cards stack safely.
- Confirm/Reject actions still render.
- Why related details still expand.
- cluster link still appears when available.
- missing metadata remains safe.

Run:
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build

Report:
- files changed
- tests added
- test results
- limitations/follow-up
```

---

## Task 7 — Reports Responsive Completion

```text
Proceed with Responsive Bundle Task 7 only.

Task: Complete responsive polish for Reports page.

Requirements:
- Desktop:
  - preserve structured sections, editing, insights, markdown fallback, and export actions.
- Mobile:
  - report sections stack cleanly.
  - edit textarea is usable.
  - Markdown/PDF download actions wrap cleanly.
  - insight cards remain readable.
- Preserve:
  - section editing.
  - save/cancel.
  - markdown fallback.
  - PDF + Markdown download.
  - report insights.
- Do not change backend.

Tests:
- structured sections render.
- edit controls remain usable.
- download actions still render.
- markdown fallback still works.
- long report content wraps safely.
- insight section remains readable if present.

Run:
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build

Report:
- files changed
- tests added
- test results
- limitations/follow-up
```

---

## Task 8 — Insights Page Responsive Completion

```text
Proceed with Responsive Bundle Task 8 only.

Task: Complete responsive polish for Insights page.

Requirements:
- Desktop:
  - preserve overview cards, structured insight cards, filters, severity filtering, and navigation actions.
- Mobile:
  - filters should wrap/stack cleanly.
  - insight cards should be readable.
  - document/timeline links should remain touch-friendly.
- Preserve:
  - type filters.
  - severity filter.
  - empty states.
  - evidence/source references.
- Do not change backend.

Tests:
- insight filters render responsively.
- severity filter remains usable.
- insight cards wrap safely.
- document/timeline navigation links remain visible.
- empty state still renders.

Run:
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build

Report:
- files changed
- tests added
- test results
- limitations/follow-up
```

---

## Task 9 — Admin Responsive Completion

```text
Proceed with Responsive Bundle Task 9 only.

Task: Complete responsive polish for Admin pages.

Requirements:
- Admin dashboard cards should stack on mobile.
- Prompt template table/form should remain usable on narrow screens.
- Prompt sandbox textarea should not overflow.
- Processing summary card should remain readable.
- Preserve admin-only guards.
- Do not change backend.

Tests:
- admin dashboard renders responsively.
- prompt templates page still renders.
- sandbox form remains usable.
- processing summary card renders.
- non-admin guard still works.

Run:
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build

Report:
- files changed
- tests added
- test results
- limitations/follow-up
```

---

## Task 10 — Final Responsive QA Pass

```text
Proceed with Responsive Bundle Task 10 only.

Task: Final responsive QA pass.

Requirements:
- Review major pages:
  - Documents
  - Chat
  - Timeline
  - Document Detail
  - Relationships
  - Reports
  - Insights
  - Admin
- Fix obvious responsive overflow issues.
- Ensure common patterns:
  - min-w-0
  - break-words
  - overflow-hidden or overflow-x-auto where appropriate
  - flex-wrap for action bars
  - responsive padding
  - touch-friendly buttons/links
- Do not change backend.
- Do not add new product features.

Run:
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build

Report:
- final test results
- pages reviewed
- responsive issues fixed
- remaining limitations
```
