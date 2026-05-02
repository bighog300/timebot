import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from './DashboardPage';

vi.mock('@/hooks/useApi', () => ({
  useReviewMetrics: () => ({ isLoading: false, isError: false, data: { open_review_count: 1, resolved_review_count: 1, open_by_type: {}, open_by_priority: {} } }),
  useActionItemMetrics: () => ({ isLoading: false, isError: false, data: { open_count: 1, completion_rate: 0.5 } }),
  useUsage: () => ({ data: { plan: 'free', documents: { used: 1, limit: 10 }, reports: { used: 0, limit: 10 }, chat_messages: { used: 4, limit: 200 } } }),
  useCreateCheckoutSession: () => ({ mutateAsync: vi.fn() }),
}));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));

describe('Dashboard usage card', () => {
  it('renders usage metrics', () => {
    render(<MemoryRouter><DashboardPage /></MemoryRouter>);
    expect(screen.getByText(/Current plan:/i)).toBeInTheDocument();
    expect(screen.getByText(/Documents: 1 \/ 10/)).toBeInTheDocument();
  });
});
