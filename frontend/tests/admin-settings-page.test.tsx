import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AdminSubscriptionsPage, AdminBillingPage, AdminLlmProvidersPage, AdminPlansPage } from '@/pages/AdminSettingsPage';
import { AdminSettingsLayout } from '@/pages/admin/AdminSettingsLayout';
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
  useAdminSystemStatus: () => ({ isLoading: false, isError: false, data: { billing_configured: true, stripe_configured: true, stripe_prices_configured: true, environment: 'development', limits_configured: true, features: { insights_enabled: true, category_intelligence_enabled: true, relationship_detection_enabled: true } } }),
  useAdminLlmModels: () => ({ isLoading: false, isError: false, data: { providers: [{ id: 'openai', name: 'OpenAI', configured: true, models: [{ id: 'gpt-4o-mini', name: 'GPT-4o Mini' }] }] } }),
}));

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({ user: { email: 'admin@example.com', role: 'admin' }, loading: false }),
}));

describe('admin settings', () => {
  it('admin settings layout and sub-tabs render', () => {
    render(<MemoryRouter initialEntries={['/admin/settings']}><Routes><Route path='/admin/settings' element={<RequireAdmin><AdminSettingsLayout /></RequireAdmin>} /></Routes></MemoryRouter>);
    expect(screen.getByText('Admin Settings')).toBeInTheDocument();
    expect(screen.getByText('Prompt Analytics')).toBeInTheDocument();
  });

  it('subscriptions table renders and actions call API hooks', async () => {
    render(<MemoryRouter><AdminSubscriptionsPage /></MemoryRouter>);
    fireEvent.click(screen.getByRole('button', { name: 'Toggle plan' }));
    fireEvent.click(screen.getByRole('button', { name: 'Grant usage' }));
    expect(mutatePlan).toHaveBeenCalled();
    expect(mutateUsage).toHaveBeenCalled();
  });

  it('billing/system status renders from backend status endpoint data', () => {
    render(<MemoryRouter><AdminBillingPage /></MemoryRouter>);
    expect(screen.getByText('Billing & system configuration')).toBeInTheDocument();
  });

  it('llm provider panel renders configured state', () => {
    render(<MemoryRouter><AdminLlmProvidersPage /></MemoryRouter>);
    expect(screen.getByText('LLM providers')).toBeInTheDocument();
    expect(screen.getByText('Yes')).toBeInTheDocument();
  });

  it('plans panel shows backend placeholder', () => {
    render(<MemoryRouter><AdminPlansPage /></MemoryRouter>);
    expect(screen.getByText(/Editable plan limits are not yet exposed by the backend/)).toBeInTheDocument();
  });
});
