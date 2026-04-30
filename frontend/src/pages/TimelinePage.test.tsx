import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
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
    expect(screen.getByTestId('timeline-scroll-area').className).toContain('max-h-[calc(100vh-240px)]');
    expect(screen.getAllByText(/2025/).length).toBeGreaterThan(0);
    expect(screen.getByText('Event / Document')).toBeTruthy();
    expect(screen.getByTestId('timeline-range-bar')).toBeTruthy();
    expect(screen.getByTestId('timeline-milestone')).toBeTruthy();
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
