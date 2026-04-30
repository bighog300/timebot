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
    unobserve() {}
    takeRecords(): ResizeObserverEntry[] {
      return [];
    }
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

  afterEach(() => {
    cleanup();
  });

  it('renders timeline axis ticks and both event types', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([
        { title: 'Due', date: '2025-02-15', confidence: 0.9, document_id: 'd1', document_title: 'doc', source_quote: 'Payment due date', start_date: null, end_date: null },
        { title: 'Term', start_date: '2025-01-01', end_date: '2025-12-31', confidence: 0.8, document_id: 'd1', document_title: 'doc', source_quote: 'term runs from', date: null },
      ]),
    );

    renderPage();

    expect(await screen.findByTestId('timeline-axis')).toBeTruthy();
    expect(screen.getByTestId('timeline-scroll-container').className).toContain('max-h-[calc(100vh-240px)]');
    expect(screen.getAllByText(/2025/).length).toBeGreaterThan(0);
    expect(screen.getByText('Event / Document')).toBeTruthy();
    expect(screen.getByTestId('timeline-range-bar')).toBeTruthy();
    expect(screen.getByTestId('timeline-milestone')).toBeTruthy();
  });

  it('keeps overflow classes constrained to scroll container and avoids min-w-max', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([{ title: 'Due', date: '2025-02-15', confidence: 0.9, document_id: 'd1', document_title: 'doc', source_quote: 'Payment due date', start_date: null, end_date: null }]),
    );
    const { container } = renderPage();
    await screen.findByTestId('timeline-scroll-container');

    const root = container.querySelector('div.w-full.min-w-0.max-w-\\[calc\\(100vw-2rem\\)\\].space-y-3.overflow-hidden') as HTMLElement;
    expect(root.className).toContain('max-w-[calc(100vw-2rem)]');
    expect(root.className).not.toContain('min-w-max');
    expect(screen.getByTestId('timeline-card').className).toContain('max-w-full');
    expect(container.querySelectorAll('.overflow-auto').length).toBe(1);
    expect(container.querySelectorAll('.overflow-x-auto').length).toBe(0);
    expect(container.querySelector('.min-w-max')).toBeNull();
  });

  it('updates zoom state and width scaling and only shows pan hint when scrollable', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([{ title: 'Long Program', start_date: '2025-01-01', end_date: '2025-10-01', confidence: 0.95, document_id: 'd1', document_title: 'doc', source_quote: 'Long range', date: null }]),
    );
    renderPage();

    const axis = await screen.findByTestId('timeline-axis');
    expect(screen.queryByText('Drag or scroll inside the chart to pan timeline.')).toBeNull();
    expect(screen.getByRole('button', { name: 'Fit' }).getAttribute('aria-pressed')).toBe('true');

    const fitWidth = Number((axis as HTMLElement).style.width.replace('px', ''));

    const controls = screen.getByText('Fit').parentElement as HTMLElement;
    fireEvent.click(within(controls).getByRole('button', { name: 'Month' }));
    expect(screen.getByRole('button', { name: 'Month' }).getAttribute('aria-pressed')).toBe('true');
    expect(await screen.findByText('Drag or scroll inside the chart to pan timeline.')).toBeTruthy();

    const monthWidth = Number((screen.getByTestId('timeline-axis') as HTMLElement).style.width.replace('px', ''));
    expect(monthWidth).toBeGreaterThan(fitWidth);

    fireEvent.click(within(controls).getByRole('button', { name: 'Year' }));
    const yearWidth = Number((screen.getByTestId('timeline-axis') as HTMLElement).style.width.replace('px', ''));
    expect(yearWidth).toBeLessThan(monthWidth);
  });

  it('pan buttons scroll the timeline container when chart is scrollable', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([{ title: 'Long Program', start_date: '2025-01-01', end_date: '2025-10-01', confidence: 0.95, document_id: 'd1', document_title: 'doc', source_quote: 'Long range', date: null }]),
    );
    renderPage();
    const scrollContainer = await screen.findByTestId('timeline-scroll-container');
    const scrollByMock = vi.fn();
    (scrollContainer as HTMLDivElement).scrollBy = scrollByMock;

    fireEvent.click(screen.getByRole('button', { name: 'Month' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Pan timeline right' }));
    expect(scrollByMock).toHaveBeenCalled();
  });

  it('does not show empty state when events exist', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([{ title: 'Due', date: '2025-02-15', confidence: 0.9, document_id: 'd1', document_title: 'doc', source_quote: 'Payment due date', start_date: null, end_date: null }]),
    );
    renderPage();
    await screen.findByText('Due');
    expect(screen.queryByText(/No extracted timeline events yet/)).toBeNull();
  });

  it('clicking event navigates to document detail', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue(
      makeTimelineResponse([{ title: 'Due', date: '2025-02-15', confidence: 0.9, document_id: 'doc-123', document_title: 'doc', source_quote: 'Payment due date', start_date: null, end_date: null }]),
    );
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: /Due/i }));
    expect(navigateMock).toHaveBeenCalledWith(expect.stringMatching(/^\/documents\/.+/));
  });
});
