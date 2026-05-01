import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';

vi.mock('@/auth/AuthContext', () => ({ useAuth: () => ({ user: { email: 'a@example.com', role: 'editor' }, loading: false, logout: vi.fn() }) }));
vi.mock('@/hooks/useApi', () => ({ useQueueStats: () => ({ data: { pending_review_count: 0 } }) }));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ toasts: [], dismissToast: vi.fn() }) }));

afterEach(() => cleanup());

describe('AppShell nav active states', () => {
  it('highlights Review for /review and not Relationships', () => {
    render(<MemoryRouter initialEntries={['/review']}><AppShell /></MemoryRouter>);
    expect(screen.getAllByRole('link', { name: 'Review' })[0].className).toContain('bg-slate-700');
    expect(screen.getAllByRole('link', { name: 'Relationships' })[0].className).not.toContain('bg-slate-700');
  });

  it('highlights Relationships for /review/relationships and not Review', () => {
    render(<MemoryRouter initialEntries={['/review/relationships']}><AppShell /></MemoryRouter>);
    expect(screen.getAllByRole('link', { name: 'Relationships' })[0].className).toContain('bg-slate-700');
    expect(screen.getAllByRole('link', { name: 'Review' })[0].className).not.toContain('bg-slate-700');
  });

  it('highlights Chat for /chat', () => {
    render(<MemoryRouter initialEntries={['/chat']}><AppShell /></MemoryRouter>);
    expect(screen.getAllByRole('link', { name: 'Chat' })[0].className).toContain('bg-slate-700');
  });

  it('highlights Reports for /reports', () => {
    render(<MemoryRouter initialEntries={['/reports']}><AppShell /></MemoryRouter>);
    expect(screen.getAllByRole('link', { name: 'Reports' })[0].className).toContain('bg-slate-700');
  });

  it('relationships nav points to relationship page', () => {
    render(<MemoryRouter><AppShell /></MemoryRouter>);
    expect(screen.getAllByRole('link', { name: 'Relationships' })[0].getAttribute('href')).toBe('/review/relationships');
  });
});
