import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppShell } from './AppShell';

vi.mock('@/auth/AuthContext', () => ({ useAuth: vi.fn() }));
vi.mock('@/hooks/useApi', () => ({ useQueueStats: () => ({ data: { pending_review_count: 0 } }) }));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ toasts: [], dismissToast: vi.fn() }) }));

import { useAuth } from '@/auth/AuthContext';

describe('AppShell admin nav', () => {
  it('shows admin users link only for admin', () => {
    vi.mocked(useAuth).mockReturnValue({ user: { email: 'a', role: 'admin' }, logout: vi.fn() } as never);
    const { rerender } = render(<MemoryRouter><AppShell /></MemoryRouter>);
    expect(screen.getAllByText('Users').length).toBeGreaterThan(0);

    vi.mocked(useAuth).mockReturnValue({ user: { email: 'b', role: 'user' }, logout: vi.fn() } as never);
    rerender(<MemoryRouter><AppShell /></MemoryRouter>);
    expect(screen.queryByText('Users')).toBeNull();
  });
});
