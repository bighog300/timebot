import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { TimelinePage } from './TimelinePage';
import { api } from '@/services/api';

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
  it('renders milestone and range rows', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue({
      total_documents: 1,
      total_events: 2,
      events: [
        { title: 'Due', date: '2025-02-15', confidence: 0.9, document_id: 'd1', document_title: 'doc', source_quote: 'Payment due date', start_date: null, end_date: null },
        { title: 'Term', start_date: '2025-01-01', end_date: '2025-12-31', confidence: 0.8, document_id: 'd1', document_title: 'doc', source_quote: 'term runs from', date: null },
      ],
    } as any);
    renderPage();
    expect(await screen.findByText('Due')).toBeTruthy();
    expect(await screen.findByText('Term')).toBeTruthy();
  });

  it('renders empty state only when no events', async () => {
    vi.mocked(api.getTimeline).mockResolvedValue({ total_documents: 1, total_events: 0, events: [] } as any);
    renderPage();
    expect(await screen.findByText(/No extracted timeline events yet/)).toBeTruthy();
  });
});
