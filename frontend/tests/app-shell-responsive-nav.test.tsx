import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';

vi.mock('@/auth/AuthContext', () => ({ useAuth: () => ({ user: { email: 'a@example.com', role: 'editor' }, loading: false, logout: vi.fn() }) }));
vi.mock('@/hooks/useApi', () => ({ useQueueStats: () => ({ data: { pending_review_count: 0 } }) }));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ toasts: [], dismissToast: vi.fn() }) }));

describe('AppShell responsive navigation', () => {
  it('renders both mobile and desktop navigation controls', () => {
    render(<MemoryRouter><AppShell /></MemoryRouter>);

    expect(screen.getByRole('navigation', { name: 'Mobile' })).toBeInTheDocument();
    expect(screen.getByRole('complementary', { name: 'Desktop' })).toBeInTheDocument();
  });

  it('keeps routes unchanged for key links', () => {
    render(<MemoryRouter><AppShell /></MemoryRouter>);

    expect(screen.getAllByRole('link', { name: 'Dashboard' })[0]).toHaveAttribute('href', '/dashboard');
    expect(screen.getAllByRole('link', { name: 'Review' })[0]).toHaveAttribute('href', '/review');
    expect(screen.getAllByRole('link', { name: 'Relationships' })[0]).toHaveAttribute('href', '/review/relationships');
  });

  it('uses safe main-content layout classes', () => {
    render(<MemoryRouter><AppShell /></MemoryRouter>);
    const main = document.querySelector('main');
    expect(main).not.toBeNull();
    expect(main!.className).toContain('min-w-0');
    expect(main!.className).toContain('overflow-x-auto');
    expect(main!.className).toContain('p-3');
    expect(main!.className).toContain('sm:p-4');
    expect(main!.className).toContain('md:p-5');
  });
});
