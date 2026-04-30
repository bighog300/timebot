import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { TimelinePage } from './TimelinePage';
import { api } from '@/services/api';

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
    observe() {}
    disconnect() {}
  }

  beforeEach(() => {
    vi.stubGlobal('ResizeObserver', ResizeObserverMock);
    vi.mocked(api.getTimeline).mockReset();
    navigateMock.mockReset();
  });

  afterEach(() => {
    cleanup();
  });

  it('renders timeline axis ticks and both event types', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue({
      total_documents: 1,
      total_events: 2,
      events: [
        { title: 'Due', date: '2025-02-15', confidence: 0.9, document_id: 'd1', document_title: 'doc', source_quote: 'Payment due date', start_date: null, end_date: null },
        { title: 'Term', start_date: '2025-01-01', end_date: '2025-12-31', confidence: 0.8, document_id: 'd1', document_title: 'doc', source_quote: 'term runs from', date: null },
      ],
    } as any);

    renderPage();

    expect(await screen.findByTestId('timeline-axis')).toBeTruthy();
    expect(screen.getByTestId('timeline-scroll-container').className).toContain('max-h-[calc(100vh-240px)]');
    expect(screen.getAllByText(/2025/).length).toBeGreaterThan(0);
    expect(screen.getByText('Event / Document')).toBeTruthy();
    expect(screen.getByTestId('timeline-range-bar')).toBeTruthy();
    expect(screen.getByTestId('timeline-milestone')).toBeTruthy();
  });

  it('keeps overflow classes constrained to scroll container and avoids min-w-max', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue({
      total_documents: 1,
      total_events: 1,
      events: [{ title: 'Due', date: '2025-02-15', confidence: 0.9, document_id: 'd1', document_title: 'doc', source_quote: 'Payment due date', start_date: null, end_date: null }],
    } as any);
    const { container } = renderPage();
    await screen.findByTestId('timeline-scroll-container');

    const root = container.querySelector('div.w-full.max-w-full.min-w-0.space-y-3.overflow-hidden') as HTMLElement;
    expect(root.className).toContain('w-full');
    expect(root.className).not.toContain('min-w-max');
    expect(container.querySelectorAll('.overflow-auto').length).toBe(1);
    expect(container.querySelectorAll('.overflow-x-auto').length).toBe(0);
    expect(container.querySelector('.min-w-max')).toBeNull();
  });

  it('uses Fit mode by default and only shows pan hint when zoomed wider', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue({
      total_documents: 1,
      total_events: 1,
      events: [{ title: 'Long Program', start_date: '2016-01-01', end_date: '2026-01-01', confidence: 0.95, document_id: 'd1', document_title: 'doc', source_quote: 'Long range', date: null }],
    } as any);
    renderPage();

    expect(await screen.findByTestId('timeline-axis')).toBeTruthy();
    expect(screen.queryByText('Drag or scroll inside the chart to pan timeline.')).toBeNull();

    const controls = screen.getByText('Fit').parentElement as HTMLElement;
    fireEvent.click(within(controls).getByRole('button', { name: 'Month' }));
    expect(await screen.findByText('Drag or scroll inside the chart to pan timeline.')).toBeTruthy();
  });

  it('does not show empty state when events exist', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue({
      total_documents: 1,
      total_events: 1,
      events: [{ title: 'Due', date: '2025-02-15', confidence: 0.9, document_id: 'd1', document_title: 'doc', source_quote: 'Payment due date', start_date: null, end_date: null }],
    } as any);
    renderPage();
    await screen.findByText('Due');
    expect(screen.queryByText(/No extracted timeline events yet/)).toBeNull();
  });

  it('clicking event navigates to document detail', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue({
      total_documents: 1,
      total_events: 1,
      events: [{ title: 'Due', date: '2025-02-15', confidence: 0.9, document_id: 'doc-123', document_title: 'doc', source_quote: 'Payment due date', start_date: null, end_date: null }],
    } as any);
    renderPage();
    fireEvent.click(await screen.findByRole('button', { name: /Due/i }));
    expect(navigateMock).toHaveBeenCalledWith(expect.stringMatching(/^\/documents\/.+/));
  });
});
