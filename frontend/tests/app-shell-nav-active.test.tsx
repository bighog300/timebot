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
    expect(screen.getByRole('link', { name: 'Review' }).className).toContain('bg-slate-700');
    expect(screen.getByRole('link', { name: 'Relationships' }).className).not.toContain('bg-slate-700');
  });

  it('highlights Relationships for /review/relationships and not Review', () => {
    render(<MemoryRouter initialEntries={['/review/relationships']}><AppShell /></MemoryRouter>);
    expect(screen.getByRole('link', { name: 'Relationships' }).className).toContain('bg-slate-700');
    expect(screen.getByRole('link', { name: 'Review' }).className).not.toContain('bg-slate-700');
  });

  it('relationships nav points to relationship page', () => {
    render(<MemoryRouter><AppShell /></MemoryRouter>);
    expect(screen.getByRole('link', { name: 'Relationships' }).getAttribute('href')).toBe('/review/relationships');
  });
});
