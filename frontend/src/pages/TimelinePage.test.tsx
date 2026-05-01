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

vi.mock('@/services/api', () => ({ api: { getTimeline: vi.fn() } }));

function renderPage() {
  const qc = new QueryClient();
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
    expect(screen.getByText('Type: Governance')).toBeTruthy();
    expect(screen.getByText('Confidence: 77%')).toBeTruthy();
  });



  it('renders signal strength label when confidence is present', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Board Approval', date: '2025-04-02', confidence: 0.77, document_id: 'd1', document_title: 'Board Minutes.pdf', category: 'Governance', source_quote: 'Approved', start_date: null, end_date: null },
      ]),
    );

    renderPage();
    expect(await screen.findByText('Signal: medium')).toBeTruthy();
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
    expect(screen.getByText('Approximate date')).toBeTruthy();
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
    expect(await screen.findByText('Milestone')).toBeTruthy();
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
    expect(screen.queryByText('Milestone')).toBeNull();
    expect(screen.getByTestId('timeline-range-bar')).toBeTruthy();
  });

  it('updates zoom state and width scaling and only shows pan hint when scrollable', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([{ title: 'Long Program', start_date: '2025-01-01', end_date: '2025-10-01', confidence: 0.95, document_id: 'd1', document_title: 'doc', source_quote: 'Long range', date: null }]),
    );
    renderPage();

    const axis = await screen.findByTestId('timeline-axis');
    expect(screen.queryByText('Drag or scroll inside the chart to pan timeline.')).toBeNull();
    const fitWidth = Number((axis as HTMLElement).style.width.replace('px', ''));

    const controls = screen.getByText('Fit').parentElement as HTMLElement;
    fireEvent.click(within(controls).getByRole('button', { name: 'Month' }));
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
    expect(await screen.findByText('No activity for 59 days (2025-01-01 → 2025-03-01)')).toBeTruthy();
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
});
