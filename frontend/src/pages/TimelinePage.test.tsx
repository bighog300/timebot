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

  it('handles missing confidence without crashing or fabricating values', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Notice Sent', date: '2025-04-03', confidence: null, document_id: 'd1', document_title: 'Notice Letter.pdf', source_quote: 'Sent', start_date: null, end_date: null },
      ]),
    );

    renderPage();
    expect(await screen.findByText('Notice Sent')).toBeTruthy();
    expect(screen.queryByText(/Confidence:/)).toBeNull();
  });

  it('expands grouped events and shows source details', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Audit Complete', date: '2025-04-04', confidence: 0.92, document_id: 'd1', document_title: 'Audit A', category: 'Compliance', source: 'internal', source_quote: 'done', start_date: null, end_date: null },
        { title: 'audit complete', date: '2025-04-05', confidence: 0.81, document_id: 'd2', document_title: 'Audit B', category: 'Compliance', source: 'external', source_quote: 'done 2', start_date: null, end_date: null },
      ]),
    );

    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: 'Show' }));
    expect(screen.getByText('Audit A: 2025-04-04')).toBeTruthy();
    expect(screen.getByText('Audit B: 2025-04-05')).toBeTruthy();
    expect(screen.getAllByText(/Type: Compliance/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Source: internal/)).toBeTruthy();
  });

  it('clicking event navigates to document detail', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([{ title: 'Due', date: '2025-02-15', confidence: 0.9, document_id: 'doc-123', document_title: 'doc', source_quote: 'Payment due date', start_date: null, end_date: null }]),
    );
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: /Due/i }));
    expect(navigateMock).toHaveBeenCalledWith(expect.stringMatching(/^\/documents\/.+/));
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
});
