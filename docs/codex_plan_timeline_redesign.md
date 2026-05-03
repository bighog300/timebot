# Codex implementation plan — Timeline page redesign

## Overview

`TimelinePage.tsx` needs six targeted UX/UI improvements. Each section below
describes exactly what to change, the precise location in the file, and what
tests to update or add. No other files need to change.

Work through the tasks in order — each one is independently testable. Do not
refactor any logic that is not explicitly mentioned.

---

## Task 1 — Confidence chips in the label column

### What to change

Replace the three plain-text lines that currently render confidence, signal
strength, and category with a row of compact coloured chips. Each chip is a
`<span>` rendered inside a shared `<div className="flex flex-wrap gap-1 mt-1">`.

**Chip styles** — add a shared helper above the component:

```tsx
const CONFIDENCE_CHIP: Record<'strong' | 'medium' | 'weak', string> = {
  strong: 'border-green-600 bg-green-50 text-green-800 dark:bg-green-950 dark:text-green-200',
  medium: 'border-amber-500 bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-200',
  weak:   'border-red-500  bg-red-50  text-red-800  dark:bg-red-950  dark:text-red-200',
};
const CHIP_BASE = 'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] leading-4';
```

**Confidence chip** — render only when `primaryConfidenceLabel` is non-null.
The coloured dot before the percentage encodes the signal tier:

```tsx
{primaryConfidenceLabel && signalStrengthLabel && (
  <span
    className={`${CHIP_BASE} ${CONFIDENCE_CHIP[signalStrengthLabel]}`}
    data-testid="confidence-chip"
  >
    <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-current" />
    {primaryConfidenceLabel}
  </span>
)}
```

**Category chip** — render when `categoryLabel` is non-null, in slate:

```tsx
{categoryLabel && (
  <span className={`${CHIP_BASE} border-slate-600 bg-slate-800 text-slate-200`}>
    {categoryLabel}
  </span>
)}
```

Remove the three old `<div>` lines that rendered `Type: …`, `Confidence: …`,
and `Signal: …` as plain text. Keep the milestone and insight-linked badges
exactly as they are — do not change their markup.

Apply the same chip treatment to the **mobile card** label section, replacing
the equivalent plain-text spans there.

### Tests to update

The following existing tests assert the old plain-text format. Update their
`findByText` / `getByText` calls to match the new chip text:

- `'shows source document title, type, and confidence when available'`
  — remove the `getByText('Type: Governance')` and
  `getByText('Confidence: 77%')` assertions. Add:
  ```ts
  expect(screen.getByTestId('confidence-chip')).toBeTruthy();
  expect(screen.getByTestId('confidence-chip').textContent).toContain('77%');
  ```

- `'renders signal strength label when confidence is present'`
  — the assertion `getByText('Signal: medium')` no longer applies.
  Replace with:
  ```ts
  const chip = screen.getByTestId('confidence-chip');
  expect(chip.textContent).toContain('77%');
  ```

- `'handles missing confidence signal strength safely'`
  — the assertion `queryByText(/Signal:/)` still holds because we only render
  the chip when both `primaryConfidenceLabel` and `signalStrengthLabel` are
  non-null. No change needed.

- `'handles missing confidence without crashing or fabricating values'`
  — `queryByText(/Confidence:/)` still holds. No change needed.

### New test to add

```ts
it('renders confidence chip with correct tier colour class for strong, medium, weak', async () => {
  vi.mocked(api.getTimeline).mockResolvedValue(
    makeTimelineResponse([
      { title: 'Strong Event', date: '2025-02-01', confidence: 0.9, document_id: 'd1', document_title: 'A.pdf', source_quote: 'q', start_date: null, end_date: null },
    ]),
  );
  renderPage();
  const chip = await screen.findByTestId('confidence-chip');
  expect(chip.className).toMatch(/green/);
  expect(chip.textContent).toContain('90%');
});
```

---

## Task 2 — Approximate date bars

### What to change

In the chart row's bar-cell, the current code renders either a milestone
diamond or a solid `bg-blue-500` bar. Add a third case: when
`getTimelineUncertaintyLabel(item.event)` returns `'Approximate date'` or
`'Month only'` or `'Date uncertain'`, render the bar with reduced opacity and
a dashed border instead of a solid fill.

Add a helper just before the return in the chart row map:

```tsx
const uncertaintyLabel = getTimelineUncertaintyLabel(item.event);
const isApproximate = uncertaintyLabel === 'Approximate date'
  || uncertaintyLabel === 'Month only'
  || uncertaintyLabel === 'Date uncertain';
```

Replace the milestone/bar conditional with:

```tsx
{item.isMilestone ? (
  <div
    className="absolute h-3 w-3 -translate-x-1/2 rotate-45 rounded-[1px] bg-emerald-400"
    style={{ left: startX, marginTop: 25 }}
    data-testid="timeline-milestone"
  />
) : isApproximate ? (
  <div
    className="absolute h-3 rounded border border-dashed border-blue-400 bg-blue-500/50"
    style={{ left: startX, width, marginTop: 25 }}
    data-testid="timeline-range-bar-approximate"
  />
) : (
  <div
    className="absolute h-3 rounded bg-blue-500"
    style={{ left: startX, width, marginTop: 25 }}
    data-testid="timeline-range-bar"
  />
)}
```

### Tests to update

- `'renders non-milestone events without milestone badge'` — this event has no
  uncertainty metadata, so `data-testid="timeline-range-bar"` still renders.
  No change needed.

### New tests to add

```ts
it('renders approximate bar style for events with uncertain date precision', async () => {
  vi.mocked(api.getTimeline).mockResolvedValue(
    makeTimelineResponse([
      { title: 'Approx Event', date: '2025-03-01', date_precision: 'approximate',
        confidence: 0.6, document_id: 'd1', document_title: 'Doc.pdf',
        source_quote: 'q', start_date: null, end_date: null },
    ]),
  );
  renderPage();
  await screen.findByText('Approx Event');
  expect(screen.getByTestId('timeline-range-bar-approximate')).toBeTruthy();
  expect(screen.queryByTestId('timeline-range-bar')).toBeNull();
});

it('renders solid bar for events with exact date precision', async () => {
  vi.mocked(api.getTimeline).mockResolvedValue(
    makeTimelineResponse([
      { title: 'Exact Event', date: '2025-03-15', date_precision: 'day',
        confidence: 0.9, document_id: 'd1', document_title: 'Doc.pdf',
        source_quote: 'q', start_date: null, end_date: null },
    ]),
  );
  renderPage();
  await screen.findByText('Exact Event');
  expect(screen.getByTestId('timeline-range-bar')).toBeTruthy();
  expect(screen.queryByTestId('timeline-range-bar-approximate')).toBeNull();
});
```

---

## Task 3 — Today line

### What to change

After the chart `ticks` array is built inside the `chart` useMemo, compute
`todayX` and include it in the returned object:

```tsx
const today = new Date();
const todayX = today >= paddedMin && today <= paddedMax
  ? dateToX(today)
  : null;

return { width, ticks, dateToX, availableTimelineWidth, isScrollable: width > availableTimelineWidth + 8, todayX };
```

In the axis header's tick `<div>` section, after the existing ticks map, add:

```tsx
{chart.todayX !== null && (
  <div
    className="absolute inset-y-0 w-px bg-orange-500"
    style={{ left: chart.todayX }}
    data-testid="timeline-today-line"
  >
    <span className="absolute top-1 -translate-x-1/2 whitespace-nowrap rounded bg-orange-100 px-1 text-[9px] font-medium text-orange-800 dark:bg-orange-950 dark:text-orange-200">
      today
    </span>
  </div>
)}
```

Add the same `todayX` line to each chart row's bar-cell, after the tick
grid-lines map, so the today line runs through the full chart height:

```tsx
{chart.todayX !== null && (
  <div
    className="absolute inset-y-0 w-px bg-orange-500/40"
    style={{ left: chart.todayX }}
    aria-hidden="true"
  />
)}
```

### New test to add

```ts
it('renders a today line when current date falls within the chart range', async () => {
  const pastDate = new Date();
  pastDate.setFullYear(pastDate.getFullYear() - 1);
  const futureDate = new Date();
  futureDate.setFullYear(futureDate.getFullYear() + 1);

  vi.mocked(api.getTimeline).mockResolvedValue(
    makeTimelineResponse([
      {
        title: 'Spanning Event',
        start_date: pastDate.toISOString().slice(0, 10),
        end_date: futureDate.toISOString().slice(0, 10),
        confidence: 0.9, document_id: 'd1', document_title: 'Doc.pdf',
        source_quote: 'q', date: null,
      },
    ]),
  );
  renderPage();
  await screen.findByText('Spanning Event');
  expect(screen.getByTestId('timeline-today-line')).toBeTruthy();
});
```

---

## Task 4 — Gap banner

### What to change

Remove the existing gaps block:

```tsx
{gaps.length ? (
  <div className="rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2">
    <div className="space-y-1">
      {gaps.map((gap, idx) => (
        <p key={...} className="text-xs text-slate-300">
          No activity for {gap.gap_duration_days} days ({gap.start_date} → {gap.end_date})
        </p>
      ))}
    </div>
  </div>
) : null}
```

Replace it with a single-line banner that shows the largest gap and a count of
the rest. Sort gaps by `gap_duration_days` descending before rendering.

```tsx
{gaps.length ? (() => {
  const sorted = [...gaps].sort((a, b) => b.gap_duration_days - a.gap_duration_days);
  const primary = sorted[0];
  const remaining = sorted.length - 1;
  return (
    <div
      className="flex items-center gap-2 rounded-md border border-amber-600/50 bg-amber-500/10 px-3 py-2"
      data-testid="timeline-gap-banner"
    >
      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" aria-hidden="true" />
      <p className="text-xs text-amber-200">
        Gap: {primary.gap_duration_days} days with no activity —{' '}
        {primary.start_date} → {primary.end_date}
      </p>
      {remaining > 0 && (
        <span className="ml-auto shrink-0 text-xs text-amber-400">
          +{remaining} more
        </span>
      )}
    </div>
  );
})() : null}
```

### Tests to update

The existing test `'renders gap labels when response includes timeline gaps'`
asserts:

```ts
expect(await screen.findByText('No activity for 59 days (2025-01-01 → 2025-03-01)')).toBeTruthy();
```

Update it to match the new banner text:

```ts
expect(await screen.findByTestId('timeline-gap-banner')).toBeTruthy();
expect(screen.getByTestId('timeline-gap-banner').textContent).toContain('59 days');
expect(screen.getByTestId('timeline-gap-banner').textContent).toContain('2025-01-01');
expect(screen.getByTestId('timeline-gap-banner').textContent).toContain('2025-03-01');
```

### New test to add

```ts
it('gap banner shows the largest gap first and indicates remaining count', async () => {
  vi.mocked(api.getTimeline).mockResolvedValue({
    ...makeTimelineResponse([
      { title: 'Kickoff', date: '2025-01-01', confidence: 0.9,
        document_id: 'd1', document_title: 'Doc', source_quote: 'K',
        start_date: null, end_date: null },
    ]),
    gaps: [
      { start_date: '2025-02-01', end_date: '2025-02-10', gap_duration_days: 9 },
      { start_date: '2025-03-01', end_date: '2025-04-20', gap_duration_days: 50 },
      { start_date: '2025-05-01', end_date: '2025-05-08', gap_duration_days: 7 },
    ],
  });
  renderPage();
  const banner = await screen.findByTestId('timeline-gap-banner');
  expect(banner.textContent).toContain('50 days');
  expect(banner.textContent).toContain('+2 more');
});
```

---

## Task 5 — Event count and chart legend

### What to change

**Event count in the page header** — on the line that currently renders
`<h1 className="text-xl font-semibold">Timeline</h1>`, wrap the heading and
add a count alongside it:

```tsx
<div className="flex items-baseline gap-3">
  <h1 className="text-xl font-semibold">Timeline</h1>
  <span className="text-sm text-slate-400" data-testid="timeline-event-count">
    {groupedEvents.length} events
  </span>
</div>
```

Note: `groupedEvents.length` is the count of unique event groups (after
deduplication), not the raw event count. This is the right number to show
because it reflects what the user sees in the chart.

**Legend footer** — add a legend row as the last child inside the chart
scroll container's inner `<div>`, after the `groupedEvents.map(...)` block:

```tsx
<div className="sticky left-0 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-slate-700 bg-slate-900 px-4 py-2" data-testid="timeline-legend">
  <span className="text-[10px] font-medium uppercase tracking-wide text-slate-500">Legend</span>
  <span className="flex items-center gap-1.5 text-[11px] text-slate-300">
    <span className="inline-block h-2 w-5 rounded-sm bg-blue-500" />
    Range event
  </span>
  <span className="flex items-center gap-1.5 text-[11px] text-slate-300">
    <span className="inline-block h-2.5 w-2.5 rotate-45 rounded-[1px] bg-emerald-400" />
    Milestone
  </span>
  <span className="flex items-center gap-1.5 text-[11px] text-slate-300">
    <span className="inline-block h-2 w-5 rounded-sm border border-dashed border-blue-400 bg-blue-500/50" />
    Approximate date
  </span>
  <span className="flex items-center gap-1.5 text-[11px] text-slate-400 ml-auto">
    <span className="inline-block h-1.5 w-1.5 rounded-full bg-green-500" /> Strong
    <span className="ml-2 inline-block h-1.5 w-1.5 rounded-full bg-amber-500" /> Medium
    <span className="ml-2 inline-block h-1.5 w-1.5 rounded-full bg-red-500" /> Weak
  </span>
</div>
```

### New tests to add

```ts
it('shows event count in the page header', async () => {
  vi.mocked(api.getTimeline).mockResolvedValue(
    makeTimelineResponse([
      { title: 'Event A', date: '2025-01-01', confidence: 0.9, document_id: 'd1', document_title: 'A', source_quote: 'q', start_date: null, end_date: null },
      { title: 'Event B', date: '2025-02-01', confidence: 0.8, document_id: 'd2', document_title: 'B', source_quote: 'q', start_date: null, end_date: null },
    ]),
  );
  renderPage();
  const countEl = await screen.findByTestId('timeline-event-count');
  expect(countEl.textContent).toContain('2 events');
});

it('renders the chart legend', async () => {
  vi.mocked(api.getTimeline).mockResolvedValue(
    makeTimelineResponse([
      { title: 'Some Event', date: '2025-01-01', confidence: 0.9, document_id: 'd1', document_title: 'A', source_quote: 'q', start_date: null, end_date: null },
    ]),
  );
  renderPage();
  await screen.findByTestId('timeline-legend');
  expect(screen.getByTestId('timeline-legend').textContent).toContain('Milestone');
  expect(screen.getByTestId('timeline-legend').textContent).toContain('Approximate date');
});
```

---

## Task 6 — Search and category filter

### What to change

Add two new pieces of state at the top of the component, after the existing
state declarations:

```tsx
const [searchQuery, setSearchQuery] = useState('');
const [activeCategory, setActiveCategory] = useState<string | null>(null);
```

**Derive the unique category list** from the normalised events (add to the
existing `useMemo` chain, after `groupedEvents`):

```tsx
const availableCategories = useMemo(() => {
  const seen = new Set<string>();
  groupedEvents.forEach((g) => {
    const cat = g.primary.event.category?.trim();
    if (cat) seen.add(cat);
  });
  return Array.from(seen).sort();
}, [groupedEvents]);
```

**Derive the filtered groups** (add after `availableCategories`):

```tsx
const filteredGroups = useMemo(() => {
  const q = searchQuery.trim().toLowerCase();
  return groupedEvents.filter((group) => {
    if (activeCategory && group.primary.event.category?.trim() !== activeCategory) return false;
    if (!q) return true;
    const title = (group.primary.event.title ?? '').toLowerCase();
    const doc = (group.primary.event.document_title ?? '').toLowerCase();
    return title.includes(q) || doc.includes(q);
  });
}, [groupedEvents, searchQuery, activeCategory]);
```

Replace every reference to `groupedEvents` in the JSX with `filteredGroups`,
**except** for the event-count badge in the header, which should still show the
total: `groupedEvents.length`.

**Toolbar** — replace the existing zoom-controls `<div>` with:

```tsx
<div className="flex flex-wrap items-center gap-2" data-testid="timeline-toolbar">
  <input
    type="search"
    placeholder="Filter events…"
    value={searchQuery}
    onChange={(e) => setSearchQuery(e.target.value)}
    className="rounded-md border border-slate-600 bg-slate-800 px-3 py-1 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
    aria-label="Filter timeline events"
    data-testid="timeline-search-input"
  />
  {availableCategories.length > 0 && (
    <>
      <button
        type="button"
        onClick={() => setActiveCategory(null)}
        className={`rounded-full border px-3 py-1 text-xs ${activeCategory === null ? 'border-blue-400 bg-blue-500/20 text-blue-200' : 'border-slate-600 text-slate-300 hover:bg-slate-800'}`}
        aria-pressed={activeCategory === null}
        data-testid="timeline-filter-all"
      >
        All
      </button>
      {availableCategories.map((cat) => (
        <button
          key={cat}
          type="button"
          onClick={() => setActiveCategory((prev) => (prev === cat ? null : cat))}
          className={`rounded-full border px-3 py-1 text-xs ${activeCategory === cat ? 'border-blue-400 bg-blue-500/20 text-blue-200' : 'border-slate-600 text-slate-300 hover:bg-slate-800'}`}
          aria-pressed={activeCategory === cat}
          data-testid={`timeline-filter-${cat.toLowerCase().replace(/\s+/g, '-')}`}
        >
          {cat}
        </button>
      ))}
    </>
  )}
  <div className="ml-auto flex items-center gap-1">
    {ZOOM_OPTIONS.map((option) => (
      <button
        key={option.mode}
        type="button"
        onClick={() => setZoomMode(option.mode)}
        className={`rounded-md border px-3 py-1 text-xs ${zoomMode === option.mode ? 'border-blue-400 bg-blue-500/20 text-blue-200' : 'border-slate-600 text-slate-300 hover:bg-slate-800'}`}
        aria-pressed={zoomMode === option.mode}
      >
        {option.label}
      </button>
    ))}
    {chart.isScrollable ? (
      <>
        <button type="button" className="rounded-md border border-slate-600 px-2 py-1 text-xs text-slate-300 hover:bg-slate-800" onClick={() => panTimeline('left')} aria-label="Pan timeline left">←</button>
        <button type="button" className="rounded-md border border-slate-600 px-2 py-1 text-xs text-slate-300 hover:bg-slate-800" onClick={() => panTimeline('right')} aria-label="Pan timeline right">→</button>
      </>
    ) : null}
  </div>
</div>
```

### Tests to update

- `'updates zoom state and width scaling and only shows pan hint when scrollable'`
  — the zoom buttons are now inside `data-testid="timeline-toolbar"` instead of
  being found via `screen.getByText('Fit').parentElement`. Update the selector:
  ```ts
  const toolbar = await screen.findByTestId('timeline-toolbar');
  fireEvent.click(within(toolbar).getByRole('button', { name: 'Month' }));
  ```

### New tests to add

```ts
it('filters events by search query matching title', async () => {
  vi.mocked(api.getTimeline).mockResolvedValue(
    makeTimelineResponse([
      { title: 'Contract Signed', date: '2025-01-01', confidence: 0.9, document_id: 'd1', document_title: 'A.pdf', source_quote: 'q', start_date: null, end_date: null },
      { title: 'Invoice Paid',    date: '2025-02-01', confidence: 0.8, document_id: 'd2', document_title: 'B.pdf', source_quote: 'q', start_date: null, end_date: null },
    ]),
  );
  renderPage();
  const input = await screen.findByTestId('timeline-search-input');
  fireEvent.change(input, { target: { value: 'contract' } });
  expect(screen.getByText('Contract Signed')).toBeTruthy();
  expect(screen.queryByText('Invoice Paid')).toBeNull();
});

it('filters events by search query matching document title', async () => {
  vi.mocked(api.getTimeline).mockResolvedValue(
    makeTimelineResponse([
      { title: 'Deadline', date: '2025-01-01', confidence: 0.9, document_id: 'd1', document_title: 'Annual_Report.pdf', source_quote: 'q', start_date: null, end_date: null },
      { title: 'Kickoff',  date: '2025-02-01', confidence: 0.8, document_id: 'd2', document_title: 'Project_Plan.pdf',  source_quote: 'q', start_date: null, end_date: null },
    ]),
  );
  renderPage();
  const input = await screen.findByTestId('timeline-search-input');
  fireEvent.change(input, { target: { value: 'annual' } });
  expect(screen.getByText('Deadline')).toBeTruthy();
  expect(screen.queryByText('Kickoff')).toBeNull();
});

it('filters events by active category', async () => {
  vi.mocked(api.getTimeline).mockResolvedValue(
    makeTimelineResponse([
      { title: 'Agreement',  date: '2025-01-01', confidence: 0.9, category: 'contract', document_id: 'd1', document_title: 'A.pdf', source_quote: 'q', start_date: null, end_date: null },
      { title: 'Payment Due', date: '2025-02-01', confidence: 0.8, category: 'invoice',  document_id: 'd2', document_title: 'B.pdf', source_quote: 'q', start_date: null, end_date: null },
    ]),
  );
  renderPage();
  const contractBtn = await screen.findByTestId('timeline-filter-contract');
  fireEvent.click(contractBtn);
  expect(screen.getByText('Agreement')).toBeTruthy();
  expect(screen.queryByText('Payment Due')).toBeNull();
});

it('shows All events when All filter is clicked after category filter', async () => {
  vi.mocked(api.getTimeline).mockResolvedValue(
    makeTimelineResponse([
      { title: 'Agreement',   date: '2025-01-01', confidence: 0.9, category: 'contract', document_id: 'd1', document_title: 'A.pdf', source_quote: 'q', start_date: null, end_date: null },
      { title: 'Payment Due', date: '2025-02-01', confidence: 0.8, category: 'invoice',  document_id: 'd2', document_title: 'B.pdf', source_quote: 'q', start_date: null, end_date: null },
    ]),
  );
  renderPage();
  fireEvent.click(await screen.findByTestId('timeline-filter-contract'));
  expect(screen.queryByText('Payment Due')).toBeNull();
  fireEvent.click(screen.getByTestId('timeline-filter-all'));
  expect(screen.getByText('Agreement')).toBeTruthy();
  expect(screen.getByText('Payment Due')).toBeTruthy();
});

it('event count in header always reflects total groups, not filtered result', async () => {
  vi.mocked(api.getTimeline).mockResolvedValue(
    makeTimelineResponse([
      { title: 'Agreement',   date: '2025-01-01', confidence: 0.9, category: 'contract', document_id: 'd1', document_title: 'A.pdf', source_quote: 'q', start_date: null, end_date: null },
      { title: 'Payment Due', date: '2025-02-01', confidence: 0.8, category: 'invoice',  document_id: 'd2', document_title: 'B.pdf', source_quote: 'q', start_date: null, end_date: null },
    ]),
  );
  renderPage();
  const countEl = await screen.findByTestId('timeline-event-count');
  expect(countEl.textContent).toContain('2 events');
  fireEvent.click(await screen.findByTestId('timeline-filter-contract'));
  expect(screen.getByTestId('timeline-event-count').textContent).toContain('2 events');
});
```

---

## Acceptance criteria

Run the full test file after all six tasks are complete:

```
pnpm vitest run src/pages/TimelinePage.test.tsx
```

All tests must pass. No test may be deleted — only updated where explicitly
instructed above.

The implementation must not touch any file other than
`frontend/src/pages/TimelinePage.tsx` and
`frontend/src/pages/TimelinePage.test.tsx`.
