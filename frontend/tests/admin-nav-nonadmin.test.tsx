import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';

vi.mock('@/auth/AuthContext', () => ({ useAuth: () => ({ user: { email: 'u@example.com', role: 'editor' }, loading: false, logout: vi.fn() }) }));
vi.mock('@/hooks/useApi', () => ({ useQueueStats: () => ({ data: { pending_review_count: 0 } }) }));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ toasts: [], dismissToast: vi.fn() }) }));

describe('admin nav', () => {
  it('is hidden for non-admin users', () => {
    render(<MemoryRouter><AppShell /></MemoryRouter>);
    expect(screen.queryByRole('link', { name: 'Admin' })).not.toBeInTheDocument();
  });
});
