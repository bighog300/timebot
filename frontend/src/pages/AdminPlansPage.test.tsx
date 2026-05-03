import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AdminPlansPage } from './AdminSettingsPage';

const pushToast = vi.fn();
const mutateAsync = vi.fn();

vi.mock('@/store/uiStore', () => ({
  useUIStore: () => ({ pushToast }),
}));

vi.mock('@/hooks/useApi', () => ({
  useAdminPlans: () => ({
    isLoading: false,
    isError: false,
    data: [{
      id: 'plan-1', slug: 'free', name: 'Free', price_monthly_cents: 0, currency: 'usd', is_active: true,
      limits_json: { documents_per_month: 10, storage_bytes: 1024, processing_jobs_per_month: 5, stale_limit: 99 },
      features_json: { insights_enabled: true, stale_feature: true },
    }],
  }),
  useUpdateAdminPlan: () => ({ mutateAsync }),
  useResetAdminPlanDefaults: () => ({ mutateAsync: vi.fn() }),
  useAdminAudit: () => ({}), useAdminSubscriptions: () => ({}), useAdminUsageSummary: () => ({}), useAdminUpdateUserPlan: () => ({}), useAdminUpdateUsageControls: () => ({}), useAdminCancelOrDowngrade: () => ({}), useAdminSystemStatus: () => ({}), useAdminLlmModels: () => ({}), useAdminSystemHealth: () => ({}), useAdminSystemJobs: () => ({}), useAdminLlmMetricsSystem: () => ({}),
}));

describe('AdminPlansPage save behavior', () => {
  beforeEach(() => {
    vi.stubGlobal('confirm', vi.fn(() => true));
    pushToast.mockReset();
    mutateAsync.mockReset();
  });

  it('shows safe error toast on backend 422 and does not throw uncaught promise', async () => {
    mutateAsync.mockRejectedValueOnce({ response: { data: { detail: "Unknown limit key 'stale_limit'." } }, message: 'Request failed' });
    render(<MemoryRouter><AdminPlansPage /></MemoryRouter>);

    fireEvent.click(screen.getByText('Save'));

    await waitFor(() => expect(pushToast).toHaveBeenCalledWith(expect.stringContaining("Failed to update plan: Unknown limit key"), 'error'));
  });
});
