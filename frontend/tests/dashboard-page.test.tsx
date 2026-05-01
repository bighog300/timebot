import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { DashboardPage } from '@/pages/DashboardPage';

vi.mock('@/hooks/useApi', () => ({
  useReviewMetrics: () => ({
    isLoading: false,
    isError: false,
    data: {
      open_review_count: 4,
      resolved_review_count: 10,
      dismissed_review_count: 1,
      open_by_type: { low_confidence: 2 },
      open_by_priority: { high: 1, normal: 3 },
    },
  }),
  useActionItemMetrics: () => ({
    isLoading: false,
    isError: false,
    data: { open_count: 5, completed_count: 7, dismissed_count: 1, completion_rate: 0.58, recently_completed_count: 2 },
  }),
  useUsage: () => ({
    data: { plan: 'free', documents: { used: 1, limit: 25 }, reports: { used: 2, limit: 10 }, chat_messages: { used: 3, limit: 200 } },
  }),
  useCreateCheckoutSession: () => ({
    mutateAsync: vi.fn(),
  }),
}));

test('renders metric widgets', () => {
  const qc = new QueryClient();
  render(
    <QueryClientProvider client={qc}>
      <DashboardPage />
    </QueryClientProvider>,
  );

  expect(screen.getByText('Open reviews')).toBeInTheDocument();
  expect(screen.getByText('58%')).toBeInTheDocument();
  expect(screen.getByText('low_confidence')).toBeInTheDocument();
});
