import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { DashboardPage } from '@/pages/DashboardPage';


const checkoutMutate = vi.fn(async (plan: string) => ({ plan, checkout_session_id: 'stub', checkout_url: 'https://billing.stub' }));

beforeEach(() => {
  checkoutMutate.mockClear();
});

afterEach(() => {
  cleanup();
});

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
  useCreateCheckoutSession: () => ({ mutateAsync: checkoutMutate }),
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


test('renders usage and upgrade CTA, and triggers checkout', async () => {
  const qc = new QueryClient();
  render(<QueryClientProvider client={qc}><DashboardPage /></QueryClientProvider>);
  expect(screen.getAllByText('Current plan:').length).toBeGreaterThan(0);
  expect(screen.getAllByText('Documents: 1 / 25').length).toBeGreaterThan(0);
  const upgrade = screen.getAllByRole('button', { name: 'Upgrade to Pro' })[0];
  expect(upgrade).toBeInTheDocument();
  fireEvent.click(upgrade);
  await waitFor(() => expect(checkoutMutate).toHaveBeenCalledWith('pro'));
});
