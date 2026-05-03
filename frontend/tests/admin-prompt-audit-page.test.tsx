import { render, screen } from '@testing-library/react';
import { AdminPromptAuditPage } from '@/pages/AdminPromptAuditPage';
import { vi } from 'vitest';

vi.mock('@/hooks/useApi', () => ({
  useAdminPromptExecutions: () => ({ isLoading: false, isError: false, data: [{ id:'1', prompt_template_id:null, purpose:null, actor_user_id:null, provider:'openai', model:'gpt-4o-mini', fallback_used:true, primary_error:null, latency_ms:10, input_tokens:null, output_tokens:null, total_tokens:12, success:true, error_message:null, source:'admin_test', created_at:new Date().toISOString() }] })
}));

test('audit list renders', () => { render(<AdminPromptAuditPage />); expect(screen.getByText('Prompt Audit Log')).toBeInTheDocument(); expect(screen.getByText('Yes')).toBeInTheDocument(); });
