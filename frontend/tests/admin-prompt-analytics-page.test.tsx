import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';
import { AdminPromptAnalyticsPage } from '@/pages/AdminPromptAnalyticsPage';
import type { PromptExecutionSummary } from '@/types/api';

const summaryMock = vi.fn();
const state: { isLoading: boolean; isError: boolean; data: PromptExecutionSummary | null } = { isLoading: false, isError: false, data: null };

vi.mock('@/hooks/useApi', () => ({
  useAdminPromptExecutionSummary: (filters: unknown) => { summaryMock(filters); return state; },
}));

beforeEach(() => {
  summaryMock.mockClear();
  state.isLoading = false;
  state.isError = false;
  state.data = {
    total_calls: 2, success_rate: 0.5, fallback_rate: 0.5, avg_latency_ms: 100, total_tokens: 1234, total_estimated_cost_usd: 1.25, pricing_unknown_count: 1,
    calls_by_provider: { openai: 2 }, calls_by_model: { 'gpt-4o-mini': 2 }, cost_by_provider: { openai: 1.25 }, cost_by_model: { 'gpt-4o-mini': 1.25 }, calls_by_source: { admin_test: 2 }, failures_by_provider: { openai: 1 }, fallback_by_provider: { openai: 1 },
  };
});

test('renders summary and breakdowns', () => {
  render(<AdminPromptAnalyticsPage />);
  expect(screen.getByText('Prompt Analytics')).toBeInTheDocument();
  expect(screen.getByText(/Total calls:/)).toBeInTheDocument();
  expect(screen.getByText('Calls by provider')).toBeInTheDocument();
  expect(screen.getByText('Fallback usage by provider')).toBeInTheDocument();
});

test('renders empty state', () => {
  state.data = {
    total_calls: 0,
    success_rate: 0.5,
    fallback_rate: 0.5,
    avg_latency_ms: 100,
    total_tokens: 1234,
    total_estimated_cost_usd: 1.25,
    pricing_unknown_count: 1,
    calls_by_provider: { openai: 2 },
    calls_by_model: { 'gpt-4o-mini': 2 },
    cost_by_provider: { openai: 1.25 },
    cost_by_model: { 'gpt-4o-mini': 1.25 },
    calls_by_source: { admin_test: 2 },
    failures_by_provider: { openai: 1 },
    fallback_by_provider: { openai: 1 },
  };
  render(<AdminPromptAnalyticsPage />);
  expect(screen.getByText('No prompt analytics data yet.')).toBeInTheDocument();
});

test('filters update hook args', () => {
  render(<AdminPromptAnalyticsPage />);
  fireEvent.change(screen.getAllByLabelText('provider')[0], { target: { value: 'openai' } });
  expect(summaryMock).toHaveBeenLastCalledWith(expect.objectContaining({ provider: 'openai' }));
});
