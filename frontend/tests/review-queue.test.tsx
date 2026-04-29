import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, expect, test, vi } from 'vitest';
import { ReviewQueuePage } from '@/pages/ReviewQueuePage';

const mockResolve = vi.fn();
const mockDismiss = vi.fn();
let reviewItems: Array<Record<string, unknown>> = [];

vi.mock('@/hooks/useApi', () => ({
  useReviewItems: () => ({
    data: { items: reviewItems, total_count: reviewItems.length, limit: 20, offset: 0 },
    isLoading: false,
    isError: false,
    isSuccess: true,
  }),
  useResolveReviewItem: () => ({ mutate: mockResolve, isPending: false }),
  useDismissReviewItem: () => ({ mutate: mockDismiss, isPending: false }),
  useBulkResolveReviewItems: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useBulkDismissReviewItems: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, Link: ({ children }: { children: ReactNode }) => <span>{children}</span> };
});

function renderPage() {
  const qc = new QueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <ReviewQueuePage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  reviewItems = [];
  mockResolve.mockReset();
  mockDismiss.mockReset();
});

test('renders empty state when review queue is empty', () => {
  renderPage();
  expect(screen.getByText('No review items for current filters.')).toBeInTheDocument();
});

test('resolve button calls review api with id', () => {
  reviewItems = [
    {
      id: '2',
      document_id: 'doc-1',
      review_type: 'low_confidence',
      status: 'open',
      reason: 'Low confidence',
      payload: { priority: 'high' },
    },
  ];

  renderPage();
  fireEvent.click(screen.getByText('Resolve'));

  expect(mockResolve).toHaveBeenCalledWith({ id: '2' });
});
