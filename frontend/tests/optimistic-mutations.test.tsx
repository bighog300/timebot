import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, expect, test, vi } from 'vitest';
import { useResolveReviewItem, useUpdateUserRole } from '@/hooks/useApi';
import { api } from '@/services/api';

const authState = { token: 'token', loading: false };
vi.mock('@/auth/AuthContext', () => ({ useAuth: () => authState }));

let qc: QueryClient;
function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

beforeEach(() => {
  qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  vi.restoreAllMocks();
});

test('resolve review item applies optimistic UI immediately', async () => {
  qc.setQueryData(['review-items', 'open', 0, 20], {
    items: [{ id: 'r1', document_id: 'd1', review_type: 'low_confidence', status: 'open', reason: null, payload: {}, created_at: '', updated_at: '', resolved_at: null, dismissed_at: null }],
    total_count: 1,
    limit: 20,
    offset: 0,
  });

  let release!: () => void;
  vi.spyOn(api, 'resolveReviewItem').mockImplementation(
    () => new Promise((resolve) => { release = () => resolve({} as never); }),
  );

  const { result } = renderHook(() => useResolveReviewItem(), { wrapper });

  act(() => {
    result.current.mutate({ id: 'r1' });
  });

  await waitFor(() => expect((qc.getQueryData(['review-items', 'open', 0, 20]) as { items: unknown[] }).items).toHaveLength(0));

  release();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
});

test('role update rollback restores state on failure', async () => {
  qc.setQueryData(['admin-users', 0, 20], {
    items: [{ id: 'u1', role: 'viewer', email: 'a@x.com', display_name: 'A', created_at: '' }],
    total_count: 1,
    limit: 20,
    offset: 0,
  });

  vi.spyOn(api, 'updateAdminUserRole').mockRejectedValue(new Error('boom'));
  const { result } = renderHook(() => useUpdateUserRole(), { wrapper });

  await expect(result.current.mutateAsync({ userId: 'u1', role: 'admin' })).rejects.toThrow('boom');

  const data = qc.getQueryData(['admin-users', 0, 20]) as { items: Array<{ role: string }> };
  expect(data.items[0].role).toBe('viewer');
});
