# Responsive QA Checklist

Use this checklist during Task 10 and before merging.

## Global

- [ ] No page has obvious horizontal overflow at mobile width.
- [ ] Main content containers use `min-w-0` where inside flex/grid.
- [ ] Long document titles, snippets, citations, and insight text wrap safely.
- [ ] Action bars use `flex-wrap`.
- [ ] Touch targets are reasonably sized.
- [ ] Desktop layouts remain dense and useful.
- [ ] Mobile layouts are stacked and readable.
- [ ] Admin-only routes remain guarded.
- [ ] No backend changes were introduced.

## AppShell

- [ ] Desktop nav renders as expected.
- [ ] Mobile nav is compact.
- [ ] Admin links only show for admins.
- [ ] Main content does not overflow.

## Documents

- [ ] Upload controls visible on mobile.
- [ ] Gmail import controls visible on mobile.
- [ ] Document clusters stack cleanly.
- [ ] Onboarding hints still render.
- [ ] First-document success panel still works.

## Chat

- [ ] Sticky input remains usable.
- [ ] Streaming text does not jump excessively.
- [ ] Citations expand/collapse.
- [ ] Citation links work.
- [ ] Follow-up suggestions wrap.
- [ ] Open in Timeline / Relationships shortcuts wrap.

## Timeline

- [ ] Desktop Gantt remains available.
- [ ] Mobile list/cards render.
- [ ] Grouped events expand.
- [ ] Milestones render.
- [ ] Gaps render.
- [ ] Signal strength renders.
- [ ] Document links work.

## Document Detail / Relationships

- [ ] Relationship filters wrap or collapse.
- [ ] Confirm/Reject actions remain touch-friendly.
- [ ] Why related details remain readable.
- [ ] Cluster link remains visible when available.
- [ ] Missing metadata remains safe.

## Reports

- [ ] Structured sections stack.
- [ ] Edit textarea fits mobile width.
- [ ] Save/Cancel buttons wrap.
- [ ] Markdown/PDF downloads remain visible.
- [ ] Report insights render.

## Insights

- [ ] Type filters wrap.
- [ ] Severity filter is usable.
- [ ] Insight cards are readable.
- [ ] Document/timeline links remain visible.
- [ ] Empty states render.

## Admin

- [ ] Admin summary cards stack.
- [ ] Prompt templates page usable.
- [ ] Prompt sandbox textarea does not overflow.
- [ ] Processing summary readable.
