import { render, screen, waitFor } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { AuthProvider, useAuth } from '@/auth/AuthContext';

const getMock = vi.fn();
vi.mock('@/services/http', () => ({ http: { defaults: { headers: { common: {} } }, get: (...args: unknown[]) => getMock(...args), post: vi.fn() } }));

function Probe() {
  const { user, loading } = useAuth();
  return <div>{loading ? 'loading' : user?.email ?? 'none'}</div>;
}

test('hydrates session from stored token', async () => {
  localStorage.setItem('timebot.auth.token', 'token-1');
  getMock.mockResolvedValue({ data: { id: '1', email: 'hydrated@example.com', display_name: 'Hydrated', is_active: true, created_at: new Date().toISOString() } });

  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  );

  await waitFor(() => expect(screen.getByText('hydrated@example.com')).toBeInTheDocument());
  localStorage.clear();
});


test('clears stored token when /auth/me returns 401', async () => {
  localStorage.setItem('timebot.auth.token', 'stale-token');
  getMock.mockRejectedValueOnce(new Error('401'));

  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  );

  await waitFor(() => expect(screen.getByText('none')).toBeInTheDocument());
  expect(localStorage.getItem('timebot.auth.token')).toBeNull();
});
