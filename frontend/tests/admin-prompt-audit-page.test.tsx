import { render, screen } from '@testing-library/react';
import { AdminPromptAuditPage } from '@/pages/AdminPromptAuditPage';
import { beforeEach, expect, test, vi } from 'vitest';

type PromptAuditHookState = {
  isLoading: boolean;
  isError: boolean;
  data: unknown;
};

type PromptAuditSummaryState = {
  data: { total_estimated_cost_usd: number } | null;
};

const mockState: PromptAuditHookState = {
  isLoading: false,
  isError: false,
  data: [{ id:'1', prompt_template_id:null, purpose:null, actor_user_id:null, provider:'openai', model:'gpt-4o-mini', fallback_used:true, primary_error:null, latency_ms:10, input_tokens:null, output_tokens:null, total_tokens:12, success:true, error_message:null, source:'admin_test', created_at:new Date().toISOString() }],
};

const summaryState: PromptAuditSummaryState = { data: { total_estimated_cost_usd: 1.23 } };

vi.mock('@/hooks/useApi', () => ({
  useAdminPromptExecutions: () => mockState,
  useAdminPromptExecutionSummary: () => summaryState,
}));

beforeEach(() => {
  summaryState.data = { total_estimated_cost_usd: 1.23 };
});

test('audit list renders', () => {
  mockState.isLoading = false;
  mockState.isError = false;
  mockState.data = [{ id:'1', prompt_template_id:null, purpose:null, actor_user_id:null, provider:'openai', model:'gpt-4o-mini', fallback_used:true, primary_error:null, latency_ms:10, input_tokens:null, output_tokens:null, total_tokens:12, success:true, error_message:null, source:'admin_test', estimated_cost_usd:0.000123, currency:'USD', pricing_known:true, created_at:new Date().toISOString() }];

  render(<AdminPromptAuditPage />);
  expect(screen.getByText('Prompt Audit Log')).toBeInTheDocument();
  expect(screen.getByText('Yes')).toBeInTheDocument();
  expect(screen.getByText('USD 0.000123')).toBeInTheDocument();
});

test('audit empty state renders', () => {
  mockState.isLoading = false;
  mockState.isError = false;
  mockState.data = [];

  render(<AdminPromptAuditPage />);
  expect(screen.getByText('No prompt executions yet.')).toBeInTheDocument();
});

test('audit error state renders', () => {
  mockState.isLoading = false;
  mockState.isError = true;
  mockState.data = null;

  render(<AdminPromptAuditPage />);
  expect(screen.getByText('Failed to load prompt executions')).toBeInTheDocument();
});


test('unknown pricing renders fallback label', () => {
  mockState.isLoading = false;
  mockState.isError = false;
  mockState.data = [{ id:'2', prompt_template_id:null, purpose:null, actor_user_id:null, provider:'openai', model:'unknown', fallback_used:false, primary_error:null, latency_ms:10, input_tokens:null, output_tokens:null, total_tokens:12, success:true, error_message:null, source:'admin_test', estimated_cost_usd:null, currency:'USD', pricing_known:false, created_at:new Date().toISOString() }];

  render(<AdminPromptAuditPage />);
  expect(screen.getByText('pricing unknown')).toBeInTheDocument();
});
