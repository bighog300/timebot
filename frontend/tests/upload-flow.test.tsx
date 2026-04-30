import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook } from '@testing-library/react';
import type { ReactNode } from 'react';
import { expect, test, vi } from 'vitest';
import { useUploadDocument } from '@/hooks/useApi';
import { api } from '@/services/api';

const authState = { token: null as string | null, loading: false };

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => authState,
}));

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

test('upload mutation blocks when auth token is missing', async () => {
  authState.loading = false;
  authState.token = null;
  const spy = vi.spyOn(api, 'uploadDocument');
  const { result } = renderHook(() => useUploadDocument(), { wrapper });

  await expect(result.current.mutateAsync(new File(['x'], 'x.txt'))).rejects.toThrow('You must be logged in');
  expect(spy).not.toHaveBeenCalled();
  spy.mockRestore();
});
