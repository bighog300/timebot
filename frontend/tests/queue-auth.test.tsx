import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, expect, test, vi } from 'vitest';
import { AuthProvider, useAuth } from '@/auth/AuthContext';
import { useQueueStats } from '@/hooks/useApi';

const { getMock, postMock, commonHeaders } = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
  commonHeaders: {} as Record<string, string>,
}));

vi.mock('@/services/http', () => ({
  http: {
    defaults: { headers: { common: commonHeaders } },
    get: (...args: unknown[]) => getMock(...args),
    post: (...args: unknown[]) => postMock(...args),
  },
}));

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  localStorage.clear();
  getMock.mockReset();
  postMock.mockReset();
  delete commonHeaders.Authorization;
});

test('does not fetch queue stats before auth is ready', async () => {
  getMock.mockResolvedValue({ data: { queued: 0, processing: 0, completed: 0, failed: 0, total: 0, pending_review_count: 0 } });

  const { result } = renderHook(() => useQueueStats(), { wrapper });

  await waitFor(() => expect(result.current.fetchStatus).toBe('idle'));
  expect(getMock).not.toHaveBeenCalled();
});

test('fetches queue stats with bearer token after login', async () => {
  postMock.mockResolvedValue({
    data: {
      access_token: 'token-abc',
      user: { id: '1', email: 'user@example.com', display_name: 'User', is_active: true, created_at: new Date().toISOString() },
    },
  });

  getMock.mockImplementation((url: string) => {
    if (url === '/queue/stats') {
      return Promise.resolve({ data: { queued: 1, processing: 2, completed: 3, failed: 0, total: 6, pending_review_count: 0 } });
    }
    return Promise.resolve({ data: { id: '1', email: 'user@example.com', display_name: 'User', is_active: true, created_at: new Date().toISOString() } });
  });

  const { result } = renderHook(
    () => {
      const { login } = useAuth();
      const stats = useQueueStats();
      return { login, stats };
    },
    { wrapper },
  );

  await result.current.login('user@example.com', 'password');

  await waitFor(() => expect(result.current.stats.isSuccess).toBe(true));
  expect(commonHeaders.Authorization).toBe('Bearer token-abc');
  expect(getMock).toHaveBeenCalledWith('/queue/stats');
});
