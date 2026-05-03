import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, vi, expect } from 'vitest';
import { AdminSystemPage } from './AdminSettingsPage';

vi.mock('@/hooks/useApi', () => ({
  useAdminAudit: () => ({}),
  useAdminSubscriptions: () => ({}),
  useAdminUsageSummary: () => ({}),
  useAdminUpdateUserPlan: () => ({}),
  useAdminUpdateUsageControls: () => ({}),
  useAdminCancelOrDowngrade: () => ({}),
  useAdminSystemStatus: () => ({ isLoading: false, isError: false, data: {} }),
  useAdminLlmModels: () => ({}),
  useAdminPlans: () => ({}),
  useUpdateAdminPlan: () => ({}),
  useResetAdminPlanDefaults: () => ({}),
  useAdminSystemHealth: () => ({ isLoading: false, isError: false, data: { overall_status: 'healthy', database: {status:'healthy'}, redis:{status:'healthy'}, celery:{status:'healthy'}, vector_store:{status:'healthy'}, llm_providers:{openai:{status:'configured'}}, app:{} }, refetch: vi.fn() }),
  useAdminSystemJobs: () => ({ isLoading: false, isError: false, data: { queue_length: 1, active_jobs: 1, failed_jobs: 0, recent_completed_jobs: 2, retry_count: 1, last_error_summary: null }, refetch: vi.fn() }),
  useAdminLlmMetricsSystem: () => ({ isLoading: false, isError: false, data: { total_calls: 10, success_count: 9, error_count: 1, error_rate: 0.1, provider_breakdown: {}, model_breakdown: {}, fallback_usage: 1, latency_percentiles_ms: {}, cost_totals: {} }, refetch: vi.fn() }),
}));

describe('AdminSystemPage observability', () => {
  it('renders observability status sections', () => {
    render(<MemoryRouter><AdminSystemPage /></MemoryRouter>);
    expect(screen.getByText('System observability')).toBeTruthy();
    expect(screen.getByText(/Overall status:/)).toBeTruthy();
    expect(screen.getByText(/Job queues/)).toBeTruthy();
    expect(screen.getByText(/LLM error rates/)).toBeTruthy();
  });
});
