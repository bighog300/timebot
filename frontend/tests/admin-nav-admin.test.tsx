import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';

vi.mock('@/auth/AuthContext', () => ({ useAuth: () => ({ user: { email: 'a@example.com', role: 'admin' }, loading: false, logout: vi.fn() }) }));
vi.mock('@/hooks/useApi', () => ({ useQueueStats: () => ({ data: { pending_review_count: 0 } }) }));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ toasts: [], dismissToast: vi.fn() }) }));

describe('admin nav', () => {
  it('appears for admin', () => {
    render(<MemoryRouter><AppShell /></MemoryRouter>);
    expect(screen.getAllByRole('link', { name: 'Admin Overview' }).length).toBeGreaterThan(0);
  });
});
