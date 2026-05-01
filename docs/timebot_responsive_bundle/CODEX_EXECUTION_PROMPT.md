# Responsive Web + Mobile Completion — Single Execution Prompt

Paste this into Codex when uploading the responsive bundle to the repo.

```text
You are working on Timebot, a production FastAPI + React document intelligence application.

Execute the Responsive Web + Mobile Completion Bundle.

Important:
This is NOT a mobile-only redesign. Preserve Timebot as a powerful desktop web application while improving tablet and mobile usability.

Hard guardrails:
- Do not change backend unless absolutely required.
- Do not change API contracts.
- Do not remove desktop functionality.
- Do not add crawling, scraping, URL ingestion, source mapping, or external web features.
- Preserve auth/admin guards.
- Preserve chat streaming, citations, source_refs, reports, insights, timeline, relationships, clusters, and onboarding behavior.
- Keep changes incremental and test after each task.

Execution order:
1. Responsive AppShell + Navigation
2. Shared Responsive Layout Primitives
3. Documents Page Responsive Completion
4. Chat Page Responsive Completion
5. Timeline Adaptive Desktop/Mobile View
6. Relationships Responsive Completion
7. Reports Responsive Completion
8. Insights Page Responsive Completion
9. Admin Responsive Completion
10. Final Responsive QA Pass

After each task, run:
npm --prefix frontend run lint
npm --prefix frontend run test -- --run
npm --prefix frontend run build

If any test/lint/build failure occurs:
- stop
- fix it
- rerun checks
- do not proceed until green

Reporting for each task:
- what changed
- why
- files touched
- tests added/updated
- test results
- limitations/follow-up

Final report:
- final lint/test/build results
- pages reviewed
- remaining responsive gaps
- confirmation that desktop behavior remains preserved

Begin with Task 1 only.
```
