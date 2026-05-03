# Timebot frontend UX upgrade — implementation plan

This plan is written for Codex. Each task is self-contained and sequenced so
that later tasks build on earlier ones with no circular dependencies.
All work is inside `frontend/src/`. No new npm dependencies are required.
Run `npm test` after each task. Tests must stay green throughout.

---

## Context

The full redesigned `AppShell.tsx` already exists in this repo at
`frontend/src/components/layout/AppShell.tsx` (it was delivered separately).
Tasks 1–2 support that file. Tasks 3–6 are independent page-level improvements
identified in the UX audit. Task 7 updates the tests that the earlier tasks
affect.

---

## Task 1 — Add `Icon` component and `ICONS` map

**File to create:** `frontend/src/components/ui/Icon.tsx`

Create a minimal inline-SVG icon component. No icon library is added; all
path data lives in this file so there is no bundle impact beyond what is used.

```tsx
// frontend/src/components/ui/Icon.tsx
import type { SVGProps } from 'react';

export const ICONS = {
  dashboard:      'M3 3h7v7H3zm11 0h7v7h-7zM3 14h7v7H3zm11 7 2.5-5 2.5 5m-4.5-.5h4',
  timeline:       'M3 6h18M3 12h18M3 18h18',
  documents:      'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6',
  search:         'M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z',
  chat:           'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z',
  queue:          'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
  review:         'M9 11l3 3L22 4 M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11',
  relationships:  'M17 20h5v-2a3 3 0 0 0-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 0 1 5.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 0 1 9.288 0',
  actionItems:    'M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2m-6 9 2 2 4-4',
  categories:     'M19 11H5m14 0a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2m14 0V9a2 2 0 0 0-2-2M5 11V9a2 2 0 0 1 2-2m0 0V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2M7 7h10',
  insights:       'M13 2 3 14h9l-1 8 10-12h-9l1-8z',
  connections:    'M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71 M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71',
  reports:        'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l5 5v11a2 2 0 0 1-2 2z',
  notifications:  'M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9 M13.73 21a2 2 0 0 1-3.46 0',
  messages:       'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 0 1-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
  settings:       'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 0 0-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 0 0-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 0 0-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 0 0-1.065-2.572C2.561 14.924 2.561 12.426 4.317 12a1.724 1.724 0 0 0 1.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  workspaces:     'M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z M16 3v4M8 3v4M3 11h18',
  admin:          'M12 15v2m-6 4h12a2 2 0 0 0 2-2v-6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2zm10-10V7a4 4 0 0 0-8 0v4h8z',
  users:          'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
  logout:         'M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3h4a3 3 0 0 1 3 3v1',
  check:          'M20 6L9 17l-5-5',
  x:              'M18 6L6 18M6 6l12 12',
  menu:           'M3 12h18M3 6h18M3 18h18',
  upload:         'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M17 8l-5-5-5 5 M12 3v12',
  mail:           'M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z M22 6l-10 7L2 6',
  chevronRight:   'M9 18l6-6-6-6',
} as const;

export type IconName = keyof typeof ICONS;

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName;
  size?: number;
}

export function Icon({ name, size = 16, ...props }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="shrink-0"
      {...props}
    >
      <path d={ICONS[name]} />
    </svg>
  );
}
```

**Acceptance criteria:**
- File exists at the path above and compiles with `tsc --noEmit`.
- No existing file is modified in this task.

---

## Task 2 — Replace AppShell with the redesigned version

**File to replace:** `frontend/src/components/layout/AppShell.tsx`

Replace the entire file content with the redesigned AppShell. The redesigned
file is provided verbatim below. Copy it exactly — do not paraphrase or
summarise.

Key behavioural changes vs. the original (for reviewer awareness):

| Area | Before | After |
|---|---|---|
| Nav items | 17 flat links | 4 grouped sections + optional Admin section |
| Icons | None | `Icon` from Task 1, 15px in sidebar |
| Mobile nav | Horizontal scroll of all 17 items | 5-tab bottom bar + "More" slide-up drawer |
| Header | Plain text logo, separate search button | Sticky header with wordmark, leading-icon search, user pill |
| Toasts | Clickable `<button>`, no dismiss affordance | Separate `×` dismiss; success auto-dismisses after 4 s; errors persist |
| Onboarding | Plain buttons | Styled cards with icons |
| `aria-label` | Partial | All interactive elements labelled |

The `Toast` component inside AppShell now reads `toast.id` as `number` — this
matches the existing `uiStore` type (`id: number`). The `dismissToast` call
passes `toast.id` directly (no change to store API).

**File content to write** — copy from `frontend/src/components/layout/AppShell.tsx`
that was delivered as the design output in this session. It imports:

```
import { Icon, type IconName } from '@/components/ui/Icon';
```

Ensure this import is present and matches Task 1's export names exactly.
All other imports (`api`, `WORKSPACE_STORAGE_KEY`, `Workspace`, `NavLink`,
`Outlet`, `useNavigate`, `onboarding helpers`, `useUIStore`, `useQueueStats`,
`useAuth`) are unchanged from the original.

**Acceptance criteria:**
- `npm run build` completes without TypeScript errors.
- The existing test `AppShell.admin-nav.test.tsx` still passes. The test
  checks that `Users` nav link appears for admin and is absent for user-role.
  The new AppShell preserves this: admin links are in `ADMIN_GROUP` which is
  only appended when `user?.role === 'admin'`.
- The mobile "More" drawer renders all nav groups (verify by checking the
  drawer renders the same `NavGroupSection` components as the desktop sidebar).

---

## Task 3 — Add `SkeletonCard` to `States.tsx`

**File to modify:** `frontend/src/components/ui/States.tsx`

Append a `SkeletonCard` export after the existing three exports. Do not modify
`LoadingState`, `EmptyState`, or `ErrorState`.

```tsx
/**
 * SkeletonCard — placeholder for a loading card.
 * Use `lines` to control how many content rows to render (default 3).
 * Use `showHeader` (default true) to toggle the title bar placeholder.
 */
export function SkeletonCard({
  lines = 3,
  showHeader = true,
}: {
  lines?: number;
  showHeader?: boolean;
}) {
  return (
    <div
      className="rounded-lg border border-slate-800 bg-slate-900 p-4"
      aria-hidden="true"
      data-testid="skeleton-card"
    >
      {showHeader && (
        <div className="mb-3 h-4 w-2/5 animate-pulse rounded bg-slate-700" />
      )}
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`h-3 animate-pulse rounded bg-slate-800 ${
              i === lines - 1 ? 'w-3/5' : 'w-full'
            }`}
          />
        ))}
      </div>
    </div>
  );
}
```

**Acceptance criteria:**
- `SkeletonCard` is exported from `States.tsx`.
- Existing exports are unchanged.
- `npm test` passes.

---

## Task 4 — Replace `LoadingState` with `SkeletonCard` in `DashboardPage`

**File to modify:** `frontend/src/pages/DashboardPage.tsx`

### 4a — Import `SkeletonCard`

Change the import line:

```tsx
// Before
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';

// After
import { EmptyState, ErrorState, LoadingState, SkeletonCard } from '@/components/ui/States';
```

### 4b — Replace the loading state rendering

Replace this block:

```tsx
{(reviewMetrics.isLoading || actionMetrics.isLoading) && <LoadingState label="Loading dashboard metrics..." />}
```

With:

```tsx
{(reviewMetrics.isLoading || actionMetrics.isLoading) && (
  <div className="grid gap-3 md:grid-cols-4" aria-busy="true" aria-label="Loading metrics">
    <SkeletonCard lines={1} showHeader />
    <SkeletonCard lines={1} showHeader />
    <SkeletonCard lines={1} showHeader />
    <SkeletonCard lines={1} showHeader />
  </div>
)}
```

### 4c — Add visual weight to primary metric cards

Replace the four `<Card>` elements inside `<div className="grid gap-3 md:grid-cols-4">` with:

```tsx
<div className="grid gap-3 md:grid-cols-4">
  {/* Primary — open reviews */}
  <Card>
    <div className="text-xs text-slate-400">Open reviews</div>
    <div className="text-2xl font-semibold">{reviewMetrics.data.open_review_count}</div>
    {reviewMetrics.data.open_review_count > 0 && (
      <div className="mt-1 h-0.5 w-full rounded bg-amber-600/60" />
    )}
  </Card>
  {/* Primary — open action items */}
  <Card>
    <div className="text-xs text-slate-400">Open action items</div>
    <div className="text-2xl font-semibold">{actionMetrics.data.open_count}</div>
    {actionMetrics.data.open_count > 0 && (
      <div className="mt-1 h-0.5 w-full rounded bg-red-600/60" />
    )}
  </Card>
  {/* Secondary — resolved reviews */}
  <Card>
    <div className="text-xs text-slate-400">Resolved reviews</div>
    <div className="text-xl font-semibold text-slate-300">{reviewMetrics.data.resolved_review_count}</div>
  </Card>
  {/* Secondary — completion rate */}
  <Card>
    <div className="text-xs text-slate-400">Completion rate</div>
    <div className="text-xl font-semibold text-slate-300">
      {(actionMetrics.data.completion_rate * 100).toFixed(0)}%
    </div>
  </Card>
</div>
```

Note the reordering: Open reviews and Open action items come first as primary
metrics; Resolved reviews and Completion rate are demoted to secondary (smaller
`text-xl`, muted `text-slate-300`).

**Acceptance criteria:**
- `npm run build` passes.
- `npm test` passes (no existing Dashboard tests assert card order).

---

## Task 5 — Fix `InsightsPage` dark-mode colour bleed

**File to modify:** `frontend/src/pages/InsightsPage.tsx`

Three substitutions are required. Apply each one independently using
search-and-replace on exact strings.

### 5a — Type filter button unselected state

Find:
```
'bg-slate-800 text-white' : 'bg-slate-100 text-slate-700'
```

Replace with:
```
'bg-slate-700 text-white' : 'bg-slate-800/50 text-slate-300 hover:bg-slate-800 hover:text-slate-100'
```

### 5b — Severity label colour

Find:
```
<label className="flex w-full max-w-xs flex-col gap-1 text-xs font-medium text-slate-600">
```

Replace with:
```
<label className="flex w-full max-w-xs flex-col gap-1 text-xs font-medium text-slate-400">
```

### 5c — Severity select element

Find:
```
className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
```

Replace with:
```
className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-slate-500"
```

### 5d — Insight type badge (appears inside each card's `Card` component)

Find:
```
<span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs uppercase tracking-wide">{insight.type}</span>
```

Replace with:
```
<span className="rounded-full bg-slate-800 px-2 py-0.5 text-xs uppercase tracking-wide text-slate-300">{insight.type}</span>
```

### 5e — Insight description paragraph colour

Find:
```
<p className="text-slate-700">{insight.description}</p>
```

Replace with:
```
<p className="text-slate-300">{insight.description}</p>
```

**Acceptance criteria:**
- No `bg-white`, `bg-slate-100`, `text-slate-600`, `text-slate-700`,
  `border-slate-300` remain anywhere in `InsightsPage.tsx`.
- `npm test` passes (the existing `InsightsPage.test.tsx` checks rendering,
  not class names).

---

## Task 6 — Wire `ConfirmModal` into `DocumentDetailPage` destructive actions

**File to modify:** `frontend/src/pages/DocumentDetailPage.tsx`

Currently, the delete action uses `window.confirm` (line ~295) and reprocess
fires immediately. The `ConfirmModal` component exists but is not used here.

### 6a — Add import

Add to the imports block (after the existing `import { Button }` line):

```tsx
import { ConfirmModal } from '@/components/ui/ConfirmModal';
```

### 6b — Add state for which modal is open

After the existing `const [relationshipFilter, setRelationshipFilter]` line,
add:

```tsx
const [confirmAction, setConfirmAction] = useState<'delete' | 'reprocess' | null>(null);
```

### 6c — Replace `window.confirm` delete with modal trigger

Find this block (approximately line 291–299):

```tsx
<Button onClick={() => reprocessMutation.mutate()}>Reprocess</Button>
```
```tsx
<button
  ...
  onClick={() => {
    if (window.confirm('Delete this document permanently?')) {
      deleteMutation.mutate();
    }
  }}
>
  Delete
</button>
```

Replace with:

```tsx
<Button onClick={() => setConfirmAction('reprocess')}>Reprocess</Button>
```
```tsx
<button
  className="rounded border border-red-800 px-3 py-1.5 text-sm text-red-400 hover:border-red-600 hover:text-red-200"
  onClick={() => setConfirmAction('delete')}
>
  Delete
</button>
```

### 6d — Add `ConfirmModal` to JSX

Directly before the final closing `</div>` of the component's return, add:

```tsx
<ConfirmModal
  open={confirmAction === 'reprocess'}
  title="Reprocess document?"
  description="The existing AI summary, tags, and timeline events will be discarded and regenerated. This cannot be undone."
  onConfirm={() => { setConfirmAction(null); reprocessMutation.mutate(); }}
  onCancel={() => setConfirmAction(null)}
/>
<ConfirmModal
  open={confirmAction === 'delete'}
  title="Delete document permanently?"
  description="This document and all associated intelligence data will be permanently deleted. This cannot be undone."
  onConfirm={() => { setConfirmAction(null); deleteMutation.mutate(); }}
  onCancel={() => setConfirmAction(null)}
/>
```

**Acceptance criteria:**
- `window.confirm` no longer appears in `DocumentDetailPage.tsx`.
- Both modals render when their respective buttons are clicked (verified by
  existing `DocumentDetailPage.test.tsx` render tests passing, plus manual
  review).
- `npm test` passes.

---

## Task 7 — Update affected tests

### 7a — Update `AppShell.admin-nav.test.tsx`

**File to modify:** `frontend/src/components/layout/AppShell.admin-nav.test.tsx`

The new AppShell renders nav items inside a `NavGroupSection` for desktop and
inside the mobile drawer. The existing test queries for `'Users'` by text —
this still works because `NavGroupSection` renders `NavLink` elements with
label text. However, the new component also requires mocking `api` since the
header fetches workspaces and notifications.

Add this mock at the top of the mock block:

```tsx
vi.mock('@/services/api', () => ({
  api: {
    listWorkspaces: () => Promise.resolve([]),
    listNotifications: () => Promise.resolve([]),
  },
}));
```

The existing two assertions (`getAllByText('Settings').length > 0` and
`queryByText('Users') === null`) remain unchanged and still pass — the Admin
group is still conditionally rendered.

### 7b — Add a test for `SkeletonCard`

**File to create:** `frontend/src/components/ui/States.test.tsx`

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingState, EmptyState, ErrorState, SkeletonCard } from './States';

describe('States', () => {
  it('LoadingState renders label', () => {
    render(<LoadingState label="Loading data..." />);
    expect(screen.getByText('Loading data...')).toBeTruthy();
  });

  it('EmptyState renders label', () => {
    render(<EmptyState label="Nothing here." />);
    expect(screen.getByText('Nothing here.')).toBeTruthy();
  });

  it('ErrorState renders message', () => {
    render(<ErrorState message="Something went wrong." />);
    expect(screen.getByText('Something went wrong.')).toBeTruthy();
  });

  it('SkeletonCard renders with default props', () => {
    render(<SkeletonCard />);
    expect(screen.getByTestId('skeleton-card')).toBeTruthy();
  });

  it('SkeletonCard renders correct number of line placeholders', () => {
    const { container } = render(<SkeletonCard lines={5} showHeader={false} />);
    // 5 line divs inside the space-y-2 container
    const lines = container.querySelectorAll('.h-3.animate-pulse');
    expect(lines.length).toBe(5);
  });
});
```

### 7c — Add a test for `Icon`

**File to create:** `frontend/src/components/ui/Icon.test.tsx`

```tsx
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { Icon } from './Icon';

describe('Icon', () => {
  it('renders an SVG element', () => {
    const { container } = render(<Icon name="dashboard" />);
    expect(container.querySelector('svg')).toBeTruthy();
  });

  it('applies custom size', () => {
    const { container } = render(<Icon name="search" size={24} />);
    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('width')).toBe('24');
    expect(svg?.getAttribute('height')).toBe('24');
  });

  it('is aria-hidden', () => {
    const { container } = render(<Icon name="settings" />);
    expect(container.querySelector('[aria-hidden="true"]')).toBeTruthy();
  });
});
```

**Acceptance criteria for Task 7:**
- `npm test` exits with zero failures.
- No previously passing test is broken.

---

## Execution order

```
Task 1  →  Task 2  →  Task 3  →  Task 4
                                   ↓
                   Task 5  ←  (independent)
                   Task 6  ←  (independent)
                   Task 7  ←  runs after all above
```

Tasks 5 and 6 are independent of each other and of Tasks 3–4.
Task 7 must run last because it tests code produced by Tasks 1–6.

Run `npm run build && npm test` after Task 7 to confirm a clean final state.

---

## What is explicitly out of scope

The following items were noted in the UX audit but are not included here
because they require product decisions or larger structural changes that go
beyond a targeted code upgrade:

- **DocumentDetailPage tab navigation** — splitting the page into
  Overview / Timeline / Relationships / Activity tabs. Requires agreement on
  which queries to defer until a tab is selected (affects API call count).
- **Chat page session titles** — displaying first-message preview as session
  label. Requires API to return the first message or a generated title field.
- **Consistent `PageTitle` component** — a shared heading component across all
  pages. Low risk but touches every page file; warrants its own PR.
- **Mobile workspace switcher** — currently hidden on small screens. Needs a
  UX decision on where it lives in the new bottom-bar layout.
