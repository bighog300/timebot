import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { TimelinePage } from './TimelinePage';
import { api } from '@/services/api';
import type { TimelineResponse } from '@/types/api';

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigateMock };
});

vi.mock('@/services/api', () => ({ api: { getTimeline: vi.fn(), getStructuredInsights: vi.fn() } }));

vi.mock('@/hooks/useApi', () => ({
  useInsightsAccess: () => ({ authReady: true, insightsEnabled: true }),
}));


const mockMatchMedia = (matches: boolean) => {
  vi.stubGlobal('matchMedia', vi.fn().mockImplementation(() => ({
    matches,
    media: '(max-width: 767px)',
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })));
};

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { gcTime: 0 }, mutations: { gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <TimelinePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('TimelinePage', () => {
  class ResizeObserverMock {
    constructor() {}
    observe() {}
    disconnect() {}
  }

  const makeTimelineResponse = (events: TimelineResponse['events']): TimelineResponse => ({
    total_documents: 1,
    total_events: events.length,
    events,
    gaps: [],
  });

  beforeEach(() => {
    vi.stubGlobal('ResizeObserver', ResizeObserverMock);
    vi.mocked(api.getTimeline).mockReset();
    vi.mocked(api.getStructuredInsights).mockReset();
    vi.mocked(api.getStructuredInsights).mockResolvedValue([]);
    mockMatchMedia(false);
    navigateMock.mockReset();
  });

  afterEach(() => cleanup());

  it('groups similar events by normalized title and shows grouped source count', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Payment Due!', date: '2025-02-15', confidence: 0.9, document_id: 'd1', document_title: 'Doc A', source_quote: 'A', start_date: null, end_date: null },
        { title: ' payment due ', date: '2025-02-16', confidence: 0.86, document_id: 'd2', document_title: 'Doc B', source_quote: 'B', start_date: null, end_date: null },
      ]),
    );
    renderPage();
    await screen.findByText('Payment Due!');
    expect(screen.getByText('2 events')).toBeTruthy();
    expect(screen.getByText('2 documents')).toBeTruthy();
  });

  it('shows source document title, type, and confidence when available', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Board Approval', date: '2025-04-02', confidence: 0.77, document_id: 'd1', document_title: 'Board Minutes.pdf', category: 'Governance', source_quote: 'Approved', start_date: null, end_date: null },
      ]),
    );

    renderPage();
    expect(await screen.findByText('Board Minutes.pdf')).toBeTruthy();
    expect(screen.getByTestId('confidence-chip')).toBeTruthy();
    expect(screen.getByTestId('confidence-chip').textContent).toContain('77%');
  });



  it('renders signal strength label when confidence is present', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Board Approval', date: '2025-04-02', confidence: 0.77, document_id: 'd1', document_title: 'Board Minutes.pdf', category: 'Governance', source_quote: 'Approved', start_date: null, end_date: null },
      ]),
    );

    renderPage();
    const chip = await screen.findByTestId('confidence-chip');
    expect(chip.textContent).toContain('77%');
  });
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

  it('handles missing confidence signal strength safely', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Notice Sent', date: '2025-04-03', confidence: null, metadata: null, document_id: 'd1', document_title: 'Notice Letter.pdf', source_quote: 'Sent', start_date: null, end_date: null },
      ]),
    );

    renderPage();
    expect(await screen.findByText('Notice Sent')).toBeTruthy();
    expect(screen.queryByText(/Signal:/)).toBeNull();
  });
  it('handles missing confidence without crashing or fabricating values', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Notice Sent', date: '2025-04-03', confidence: null, metadata: null, document_id: 'd1', document_title: 'Notice Letter.pdf', source_quote: 'Sent', start_date: null, end_date: null },
      ]),
    );

    renderPage();
    expect(await screen.findByText('Notice Sent')).toBeTruthy();
    expect(screen.queryByText(/Confidence:/)).toBeNull();
  });

  it('expands grouped events and shows source details', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Audit Complete', date: '2025-04-04', confidence: 0.92, date_precision: 'month', document_id: 'd1', document_title: 'Audit A', category: 'Compliance', source: 'internal', source_quote: 'done', start_date: null, end_date: null },
        { title: 'audit complete', date: '2025-04-05', confidence: 0.81, metadata: { is_approximate: true }, document_id: 'd2', document_title: 'Audit B', category: 'Compliance', source: 'external', source_quote: 'done 2', start_date: null, end_date: null },
      ]),
    );

    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: 'Show' }));
    expect(screen.getByText('Audit A: 2025-04-04')).toBeTruthy();
    expect(screen.getByText('Audit B: 2025-04-05')).toBeTruthy();
    expect(screen.getAllByText(/Type: Compliance/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Source: internal/)).toBeTruthy();
    expect(screen.getAllByText('Month only').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Approximate date').length).toBeGreaterThan(0);
  });


  it('renders exact date events normally when precision metadata marks day-level precision', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Signed Contract', date: '2025-04-10', date_precision: 'day', confidence: 0.91, document_id: 'd1', document_title: 'Contract.pdf', source_quote: 'signed', start_date: null, end_date: null },
      ]),
    );

    renderPage();
    expect(await screen.findByText('Signed Contract')).toBeTruthy();
    expect(screen.getByText('Exact date')).toBeTruthy();
  });

  it('renders uncertainty labels when event metadata indicates approximate or uncertain dates', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Market Launch', date: '2025-04', date_precision: 'month', confidence: 0.7, document_id: 'd1', document_title: 'Roadmap.pdf', source_quote: 'April launch', start_date: null, end_date: null },
        { title: 'Regulatory Decision', date: '2025-05-01', metadata: { date_uncertain: true }, confidence: 0.6, document_id: 'd2', document_title: 'Memo.pdf', source_quote: 'pending', start_date: null, end_date: null },
      ]),
    );

    renderPage();
    expect(await screen.findByText('Market Launch')).toBeTruthy();
    expect(screen.getAllByText('Month only').length).toBeGreaterThan(0);
    expect(screen.getByText('Date uncertain')).toBeTruthy();
  });
  it('clicking event navigates to document detail', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([{ title: 'Due', date: '2025-02-15', confidence: 0.9, document_id: 'doc-123', document_title: 'doc', source_quote: 'Payment due date', start_date: null, end_date: null }]),
    );
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: /Due/i }));
    expect(navigateMock).toHaveBeenCalledWith(expect.stringMatching(/^\/documents\/.+/));
  });

  it('grouped event primary remains navigable', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Filing Sent', date: '2025-04-01', confidence: 0.8, document_id: 'doc-a', document_title: 'A', source_quote: 'sent', start_date: null, end_date: null },
        { title: 'filing sent', date: '2025-04-02', confidence: 0.7, document_id: 'doc-b', document_title: 'B', source_quote: 'sent again', start_date: null, end_date: null },
      ]),
    );
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: /Open document for timeline event Filing Sent/i }));
    expect(navigateMock).toHaveBeenCalledWith('/documents/doc-a');
  });

  it('expanded grouped source events show document links', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Audit Complete', date: '2025-04-04', confidence: 0.92, document_id: 'd1', document_title: 'Audit A', source_quote: 'done', start_date: null, end_date: null },
        { title: 'audit complete', date: '2025-04-05', confidence: 0.81, document_id: 'd2', document_title: 'Audit B', source_quote: 'done 2', start_date: null, end_date: null },
      ]),
    );
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: 'Show' }));
    fireEvent.click(screen.getAllByRole('button', { name: /Open document for grouped timeline source event audit complete/i })[0]);
    expect(navigateMock).toHaveBeenCalledWith('/documents/d1');
  });

  it('renders mobile stacked cards with expandable grouped events and document links', async () => {
    mockMatchMedia(true);
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Audit Complete', date: '2025-04-04', confidence: 0.92, is_milestone: true, document_id: 'd1', document_title: 'Audit A', source_quote: 'done', start_date: null, end_date: null },
        { title: 'audit complete', date: '2025-04-05', confidence: 0.81, metadata: { is_approximate: true }, document_id: 'd2', document_title: 'Audit B', source_quote: 'done 2', start_date: null, end_date: null },
      ]),
    );

    renderPage();
    expect(await screen.findByTestId('timeline-mobile-list')).toBeTruthy();
    fireEvent.click(screen.getAllByRole('button', { name: 'Show' })[0]);
    expect(screen.getByTestId('timeline-mobile-group-expanded')).toBeTruthy();
    expect(screen.getAllByText('Milestone').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Approximate date').length).toBeGreaterThan(0);

    fireEvent.click(screen.getAllByRole('button', { name: /Open document for grouped timeline source event audit complete/i })[0]);
    expect(navigateMock).toHaveBeenCalledWith('/documents/d1');
  });

  it('missing document_id is safe', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([{ title: 'No Doc', date: '2025-04-06', confidence: 0.5, document_id: '', document_title: 'Unknown', source_quote: 'n/a', start_date: null, end_date: null } as TimelineResponse['events'][number]]),
    );
    renderPage();
    await screen.findByText('No Doc');
    expect(screen.queryByRole('button', { name: /Open document for timeline event/i })).toBeNull();
    expect(() => fireEvent.click(screen.getByText('No Doc'))).not.toThrow();
    expect(navigateMock).not.toHaveBeenCalled();
  });

  it('renders milestone badge when event is flagged as milestone', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Launch Complete', date: '2025-03-01', confidence: 0.91, is_milestone: true, milestone_reason: 'high_confidence, keyword', document_id: 'doc-1', document_title: 'Roadmap.pdf', source_quote: 'launched', start_date: null, end_date: null },
      ]),
    );
    renderPage();
    expect((await screen.findAllByText('Milestone')).length).toBeGreaterThan(0);
    expect(screen.getByTestId('timeline-milestone')).toBeTruthy();
  });

  it('renders non-milestone events without milestone badge', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'General Update', date: '2025-03-02', confidence: 0.4, is_milestone: false, document_id: 'doc-2', document_title: 'Notes.pdf', source_quote: 'update', start_date: null, end_date: null },
      ]),
    );
    renderPage();
    expect(await screen.findByText('General Update')).toBeTruthy();
    expect(screen.getAllByText('Milestone').length).toBe(1);
    expect(screen.getByTestId('timeline-range-bar')).toBeTruthy();
  });
  it('renders approximate bar style for events with uncertain date precision', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Approx Event', date: '2025-03-01', date_precision: 'approximate', confidence: 0.6, document_id: 'd1', document_title: 'Doc.pdf', source_quote: 'q', start_date: null, end_date: null },
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
        { title: 'Exact Event', date: '2025-03-15', date_precision: 'day', confidence: 0.9, document_id: 'd1', document_title: 'Doc.pdf', source_quote: 'q', start_date: null, end_date: null },
      ]),
    );
    renderPage();
    await screen.findByText('Exact Event');
    expect(screen.getByTestId('timeline-range-bar')).toBeTruthy();
    expect(screen.queryByTestId('timeline-range-bar-approximate')).toBeNull();
  });
  it('renders a today line when current date falls within the chart range', async () => {
    const pastDate = new Date();
    pastDate.setFullYear(pastDate.getFullYear() - 1);
    const futureDate = new Date();
    futureDate.setFullYear(futureDate.getFullYear() + 1);
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Spanning Event', start_date: pastDate.toISOString().slice(0, 10), end_date: futureDate.toISOString().slice(0, 10), confidence: 0.9, document_id: 'd1', document_title: 'Doc.pdf', source_quote: 'q', date: null },
      ]),
    );
    renderPage();
    await screen.findByText('Spanning Event');
    expect(screen.getByTestId('timeline-today-line')).toBeTruthy();
  });

  it('updates zoom state and width scaling and only shows pan hint when scrollable', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([{ title: 'Long Program', start_date: '2025-01-01', end_date: '2025-10-01', confidence: 0.95, document_id: 'd1', document_title: 'doc', source_quote: 'Long range', date: null }]),
    );
    renderPage();

    const axis = await screen.findByTestId('timeline-axis');
    expect(screen.queryByText('Drag or scroll inside the chart to pan timeline.')).toBeNull();
    const fitWidth = Number((axis as HTMLElement).style.width.replace('px', ''));

    const toolbar = await screen.findByTestId('timeline-toolbar');
    fireEvent.click(within(toolbar).getByRole('button', { name: 'Month' }));
    expect(await screen.findByText('Drag or scroll inside the chart to pan timeline.')).toBeTruthy();

    const monthWidth = Number((screen.getByTestId('timeline-axis') as HTMLElement).style.width.replace('px', ''));
    expect(monthWidth).toBeGreaterThan(fitWidth);
  });

  it('renders gap labels when response includes timeline gaps', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue({
      ...makeTimelineResponse([{ title: 'Kickoff', date: '2025-01-01', confidence: 0.9, document_id: 'd1', document_title: 'Doc', source_quote: 'K', start_date: null, end_date: null }]),
      gaps: [{ start_date: '2025-01-01', end_date: '2025-03-01', gap_duration_days: 59 }],
    });
    renderPage();
    expect(await screen.findByTestId('timeline-gap-banner')).toBeTruthy();
    expect(screen.getByTestId('timeline-gap-banner').textContent).toContain('59 days');
    expect(screen.getByTestId('timeline-gap-banner').textContent).toContain('2025-01-01');
    expect(screen.getByTestId('timeline-gap-banner').textContent).toContain('2025-03-01');
  });
  it('gap banner shows the largest gap first and indicates remaining count', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue({
      ...makeTimelineResponse([{ title: 'Kickoff', date: '2025-01-01', confidence: 0.9, document_id: 'd1', document_title: 'Doc', source_quote: 'K', start_date: null, end_date: null }]),
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
      makeTimelineResponse([{ title: 'Some Event', date: '2025-01-01', confidence: 0.9, document_id: 'd1', document_title: 'A', source_quote: 'q', start_date: null, end_date: null }]),
    );
    renderPage();
    await screen.findByTestId('timeline-legend');
    expect(screen.getByTestId('timeline-legend').textContent).toContain('Milestone');
    expect(screen.getByTestId('timeline-legend').textContent).toContain('Approximate date');
  });
  it('filters events by search query matching title', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Contract Signed', date: '2025-01-01', confidence: 0.9, document_id: 'd1', document_title: 'A.pdf', source_quote: 'q', start_date: null, end_date: null },
        { title: 'Invoice Paid', date: '2025-02-01', confidence: 0.8, document_id: 'd2', document_title: 'B.pdf', source_quote: 'q', start_date: null, end_date: null },
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
        { title: 'Kickoff', date: '2025-02-01', confidence: 0.8, document_id: 'd2', document_title: 'Project_Plan.pdf', source_quote: 'q', start_date: null, end_date: null },
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
        { title: 'Agreement', date: '2025-01-01', confidence: 0.9, category: 'contract', document_id: 'd1', document_title: 'A.pdf', source_quote: 'q', start_date: null, end_date: null },
        { title: 'Payment Due', date: '2025-02-01', confidence: 0.8, category: 'invoice', document_id: 'd2', document_title: 'B.pdf', source_quote: 'q', start_date: null, end_date: null },
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
        { title: 'Agreement', date: '2025-01-01', confidence: 0.9, category: 'contract', document_id: 'd1', document_title: 'A.pdf', source_quote: 'q', start_date: null, end_date: null },
        { title: 'Payment Due', date: '2025-02-01', confidence: 0.8, category: 'invoice', document_id: 'd2', document_title: 'B.pdf', source_quote: 'q', start_date: null, end_date: null },
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
        { title: 'Agreement', date: '2025-01-01', confidence: 0.9, category: 'contract', document_id: 'd1', document_title: 'A.pdf', source_quote: 'q', start_date: null, end_date: null },
        { title: 'Payment Due', date: '2025-02-01', confidence: 0.8, category: 'invoice', document_id: 'd2', document_title: 'B.pdf', source_quote: 'q', start_date: null, end_date: null },
      ]),
    );
    renderPage();
    const countEl = await screen.findByTestId('timeline-event-count');
    expect(countEl.textContent).toContain('2 events');
    fireEvent.click(await screen.findByTestId('timeline-filter-contract'));
    expect(screen.getByTestId('timeline-event-count').textContent).toContain('2 events');
  });

  it('does not crash when gaps are missing in timeline response', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue({
      total_documents: 1,
      total_events: 1,
      events: [{ title: 'Kickoff', date: '2025-01-01', confidence: 0.9, document_id: 'd1', document_title: 'Doc', source_quote: 'K', start_date: null, end_date: null }],
    } as TimelineResponse);
    renderPage();
    expect(await screen.findByText('Kickoff')).toBeTruthy();
    expect(screen.queryByText(/No activity for/)).toBeNull();
  });

  it('marks timeline events linked to structured insights and shows insight types', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { event_id: 'evt-1', title: 'Linked Event', date: '2025-01-01', confidence: 0.9, document_id: 'd1', document_title: 'Doc A', source_quote: 'L', start_date: null, end_date: null },
      ]),
    );
    vi.mocked(api.getStructuredInsights).mockResolvedValue([
      { type: 'risk', title: 'Risky', description: 'desc', severity: 'high', related_event_ids: ['evt-1'] },
      { type: 'change', title: 'Changed', description: 'desc', severity: 'medium', related_event_ids: ['evt-1'] },
    ]);
    renderPage();
    expect(await screen.findByText('Insight-linked')).toBeTruthy();
    expect(screen.getAllByText('Insight: risk').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Insight: change').length).toBeGreaterThan(0);
  });

  it('leaves non-linked timeline events unaffected', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { event_id: 'evt-2', title: 'Unlinked Event', date: '2025-01-02', confidence: 0.7, document_id: 'd2', document_title: 'Doc B', source_quote: 'U', start_date: null, end_date: null },
      ]),
    );
    vi.mocked(api.getStructuredInsights).mockResolvedValue([
      { type: 'risk', title: 'Risky', description: 'desc', severity: 'high', related_event_ids: ['evt-1'] },
    ]);
    renderPage();
    await screen.findByText('Unlinked Event');
    expect(screen.queryByText('Insight-linked')).toBeNull();
    expect(screen.queryByText('Insight: risk')).toBeNull();
  });

  it('does not crash when related_event_ids are missing from insights', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { event_id: 'evt-3', title: 'Event C', date: '2025-01-03', confidence: 0.8, document_id: 'd3', document_title: 'Doc C', source_quote: 'C', start_date: null, end_date: null },
      ]),
    );
    vi.mocked(api.getStructuredInsights).mockResolvedValue([
      { type: 'risk', title: 'Risky', description: 'desc', severity: 'high' },
    ]);
    renderPage();
    expect(await screen.findByText('Event C')).toBeTruthy();
    expect(screen.queryByText('Insight-linked')).toBeNull();
  });
});
