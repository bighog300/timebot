import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { SettingsLayoutPage } from '@/pages/settings/SettingsLayoutPage';
import { SettingsAccountPage } from '@/pages/settings/SettingsAccountPage';
import { SettingsBillingPage } from '@/pages/settings/SettingsBillingPage';
import { SettingsUsagePage } from '@/pages/settings/SettingsUsagePage';

const mockPortal = vi.fn();

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({ user: { email: 'user@example.com', display_name: 'Test User', role: 'editor' } }),
}));

vi.mock('@/store/uiStore', () => ({
  useUIStore: (selector: (state: { pushToast: (msg: string, type?: string) => void }) => unknown) => selector({ pushToast: vi.fn() }),
}));

vi.mock('@/hooks/useApi', () => ({
  useSubscription: () => ({
    isLoading: false,
    isError: false,
    data: { status: 'inactive', current_period_start: null, current_period_end: null, cancel_at_period_end: false, plan: { slug: 'free', name: 'Free', price_monthly_cents: 0, currency: 'usd' } },
  }),
  usePlans: () => ({
    isLoading: false,
    isError: false,
    data: [{ slug: 'free', price_monthly_cents: 0, features: { billing_configured: false } }],
  }),
  useCreateCustomerPortalSession: () => ({ isPending: false, mutateAsync: mockPortal }),
  useUsage: () => ({
    isLoading: false,
    isError: false,
    data: { plan: 'free', documents: { used: 1, limit: 25 }, reports: { used: 2, limit: 10 }, chat_messages: { used: 3, limit: 200 } },
  }),
}));

function renderSettings(path = '/settings/account') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/settings" element={<SettingsLayoutPage />}>
          <Route index element={<SettingsAccountPage />} />
          <Route path="account" element={<SettingsAccountPage />} />
          <Route path="billing" element={<SettingsBillingPage />} />
          <Route path="usage" element={<SettingsUsagePage />} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe('settings pages', () => {
  it('normal user can render settings and account page', () => {
    renderSettings('/settings/account');
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Account & profile')).toBeInTheDocument();
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
  });

  it('billing page renders subscription status and unavailable state', () => {
    renderSettings('/settings/billing');
    expect(screen.getByText('Billing & subscription')).toBeInTheDocument();
    expect(screen.getByText('No active subscription yet. You are currently on the free plan.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Billing unavailable' })).toBeDisabled();
  });

  it('usage page renders usage summary', () => {
    renderSettings('/settings/usage');
    expect(screen.getByText('Personal usage')).toBeInTheDocument();
    expect(screen.getByText('Documents: 1 / 25')).toBeInTheDocument();
    expect(screen.getByText('Reports: 2 / 10')).toBeInTheDocument();
  });

  it('does not show admin-only controls', () => {
    renderSettings('/settings/account');
    expect(screen.queryByText('Prompt Templates')).not.toBeInTheDocument();
    expect(screen.queryByText('Chatbot Settings')).not.toBeInTheDocument();
  });
});
