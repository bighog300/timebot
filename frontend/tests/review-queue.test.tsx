import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, expect, test, vi } from 'vitest';
import { ReviewQueuePage } from '@/pages/ReviewQueuePage';
import type { Document } from '@/types/api';

const mockMutateAsync = vi.fn();
let queueData: Document[] = [];
let pendingCount = 0;

vi.mock('@/hooks/useApi', () => ({
  useReviewQueue: () => ({ data: queueData, isLoading: false, isError: false, isSuccess: true }),
  useQueueStats: () => ({ data: { pending_review_count: pendingCount } }),
  useReviewDocument: () => ({ mutateAsync: mockMutateAsync, isPending: false }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, Link: ({ children }: { children: ReactNode }) => <span>{children}</span> };
});

function mkDoc(overrides: Partial<Document>): Document {
  return {
    id: '1',
    filename: 'a.pdf',
    file_type: 'pdf',
    file_size: 1,
    source: 'upload',
    upload_date: new Date().toISOString(),
    processing_status: 'completed',
    ai_tags: ['ai'],
    user_tags: [],
    is_favorite: false,
    is_archived: false,
    ...overrides,
  };
}

function renderPage() {
  const qc = new QueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <ReviewQueuePage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  document.body.innerHTML = '';
  queueData = [];
  pendingCount = 0;
  mockMutateAsync.mockReset();
  mockMutateAsync.mockResolvedValue({});
});

test('renders empty state when review queue is empty', () => {
  renderPage();
  expect(screen.getByText('All AI outputs are approved')).toBeInTheDocument();
});

test('renders confidence bar at red for low confidence', () => {
  queueData = [mkDoc({ ai_confidence: 0.4, review_status: 'pending', summary: 'Summary' })];
  pendingCount = 1;

  const { container } = renderPage();
  expect(container.querySelector('.bg-red-500')).toBeInTheDocument();
});

test('approve button calls review api with approve action', () => {
  queueData = [mkDoc({ id: '2', ai_confidence: 0.3, review_status: 'pending', summary: 'Summary' })];
  pendingCount = 1;

  renderPage();
  fireEvent.click(screen.getAllByText('Approve')[0]);

  expect(mockMutateAsync).toHaveBeenCalledWith(expect.objectContaining({ id: '2', action: 'approve' }));
});
