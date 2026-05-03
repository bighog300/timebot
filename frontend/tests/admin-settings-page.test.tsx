import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AdminSettingsPage, AdminSubscriptionsPage } from '@/pages/AdminSettingsPage';
import { RequireAdmin } from '@/components/auth/RequireAdmin';

const mutatePlan = vi.fn().mockResolvedValue({});
const mutateUsage = vi.fn().mockResolvedValue({});

vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));
vi.mock('@/hooks/useApi', () => ({
  useAdminSubscriptions: () => ({ isLoading: false, isError: false, data: [{ user_id: 'u1', email: 'a@example.com', subscription_id: 's1', plan_slug: 'free', plan_name: 'Free', status: 'active', cancel_at_period_end: false, usage_credits: {}, limit_overrides: {} }] }),
  useAdminUpdateUserPlan: () => ({ mutateAsync: mutatePlan }),
  useAdminUpdateUsageControls: () => ({ mutateAsync: mutateUsage }),
  useAdminCancelOrDowngrade: () => ({ mutateAsync: vi.fn().mockResolvedValue({}) }),
  useAdminUsageSummary: () => ({ isLoading: false, isError: false, data: { user_id: 'u1', usage: {} } }),
  useAdminAudit: () => ({ isLoading: false, isError: false, data: { items: [] } }),
}));

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({ user: { email: 'admin@example.com', role: 'admin' }, loading: false }),
}));

describe('admin settings', () => {
  it('admin can access admin settings route', () => {
    render(<MemoryRouter initialEntries={['/admin']}><Routes><Route path='/admin' element={<RequireAdmin><AdminSettingsPage /></RequireAdmin>} /></Routes></MemoryRouter>);
    expect(screen.getByText('Admin Settings')).toBeInTheDocument();
  });

  it('subscriptions table renders and actions call API hooks', async () => {
    render(<MemoryRouter><AdminSubscriptionsPage /></MemoryRouter>);
    expect(screen.getByText('a@example.com')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Toggle plan' }));
    fireEvent.click(screen.getByRole('button', { name: 'Grant usage' }));
    expect(mutatePlan).toHaveBeenCalled();
    expect(mutateUsage).toHaveBeenCalled();
  });
});
