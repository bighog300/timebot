import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { DashboardPage } from '@/pages/DashboardPage';

type UsagePayload = { plan?: string; documents?: { used?: number; limit?: number }; reports?: { used?: number; limit?: number }; chat_messages?: { used?: number; limit?: number } } | undefined;
const usageMock = vi.hoisted(() => ({ value: undefined as UsagePayload }));

vi.mock('@/hooks/useApi', () => ({
  useReviewMetrics: () => ({ isLoading: false, isError: false, data: { open_review_count: 0, resolved_review_count: 0, dismissed_review_count: 0, open_by_type: {}, open_by_priority: {} } }),
  useActionItemMetrics: () => ({ isLoading: false, isError: false, data: { open_count: 0, completed_count: 0, dismissed_count: 0, completion_rate: 0, recently_completed_count: 0 } }),
  useUsage: () => ({ data: usageMock.value }),
  useCreateCheckoutSession: () => ({ mutateAsync: vi.fn() }),
}));

test('usage UI tolerates missing and partial payload', () => {
  const qc = new QueryClient();
  usageMock.value = undefined;
  const { rerender } = render(<QueryClientProvider client={qc}><DashboardPage /></QueryClientProvider>);
  expect(screen.getByText('Documents: 0 / ∞')).toBeInTheDocument();

  usageMock.value = { plan: 'free', documents: { used: 4, limit: 25 } };
  rerender(<QueryClientProvider client={qc}><DashboardPage /></QueryClientProvider>);
  expect(screen.getByText('Documents: 4 / 25')).toBeInTheDocument();
  expect(screen.getByText('Reports: 0 / ∞')).toBeInTheDocument();
});
