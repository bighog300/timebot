import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { ONBOARDING_COMPLETED_KEY, ONBOARDING_STEP_KEY } from '@/components/layout/onboarding';

vi.mock('@/auth/AuthContext', () => ({ useAuth: () => ({ user: { email: 'a@example.com', role: 'editor' }, loading: false, logout: vi.fn() }) }));
vi.mock('@/hooks/useApi', () => ({ useQueueStats: () => ({ data: { pending_review_count: 0 } }) }));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ toasts: [], dismissToast: vi.fn() }) }));

describe('Onboarding flow', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => cleanup());

  it('onboarding shows for first-time users', () => {
    render(<MemoryRouter><AppShell /></MemoryRouter>);
    expect(screen.getByRole('dialog', { name: 'Onboarding' })).toBeInTheDocument();
    expect(screen.getByText('Welcome to Timebot')).toBeInTheDocument();
  });

  it('onboarding does not show after completion', () => {
    window.localStorage.setItem(ONBOARDING_COMPLETED_KEY, 'true');
    render(<MemoryRouter><AppShell /></MemoryRouter>);
    expect(screen.queryByRole('dialog', { name: 'Onboarding' })).not.toBeInTheDocument();
  });

  it('selecting a use case advances step', () => {
    render(<MemoryRouter><AppShell /></MemoryRouter>);
    fireEvent.click(screen.getByRole('button', { name: 'Casework & investigations' }));
    expect(screen.getByText('Great. Add your first document source.')).toBeInTheDocument();
    expect(window.localStorage.getItem(ONBOARDING_STEP_KEY)).toBe('first_action');
  });

  it('completion persists in localStorage', () => {
    render(<MemoryRouter><AppShell /></MemoryRouter>);
    fireEvent.click(screen.getByRole('button', { name: 'Casework & investigations' }));
    fireEvent.click(screen.getByRole('button', { name: 'Upload files' }));
    expect(window.localStorage.getItem(ONBOARDING_COMPLETED_KEY)).toBe('true');
    expect(window.localStorage.getItem(ONBOARDING_STEP_KEY)).toBe('complete');
  });

  it('main app still renders when onboarding is complete', () => {
    window.localStorage.setItem(ONBOARDING_COMPLETED_KEY, 'true');
    render(<MemoryRouter><AppShell /></MemoryRouter>);
    expect(screen.getByText('Document Intelligence Platform')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument();
  });
});
