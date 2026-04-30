import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AdminChatbotSettingsPage } from '@/pages/AdminChatbotSettingsPage';

const mutateUpdate = vi.fn(async () => ({}));
const mutateReset = vi.fn(async () => ({}));
vi.mock('@/hooks/useApi', () => ({
  useChatbotSettings: () => ({ data: { system_prompt:'a', retrieval_prompt:'b', report_prompt:'c', citation_prompt:'d', default_report_template:'e', model:'gpt', temperature:0.2, max_tokens:500, max_documents:6, allow_full_text_retrieval:false }, isLoading:false }),
  useUpdateChatbotSettings: () => ({ mutateAsync: mutateUpdate }),
  useResetChatbotSettings: () => ({ mutateAsync: mutateReset }),
}));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));

afterEach(() => { cleanup(); mutateUpdate.mockClear(); mutateReset.mockClear(); });

describe('admin chatbot settings', () => {
  it('save calls api', async () => { render(<AdminChatbotSettingsPage />); fireEvent.click(screen.getByText('Save')); expect(mutateUpdate).toHaveBeenCalled(); });
  it('reset defaults calls api', async () => { render(<AdminChatbotSettingsPage />); fireEvent.click(screen.getAllByText('Reset defaults')[0]); fireEvent.click(screen.getByText('Confirm')); expect(mutateReset).toHaveBeenCalled(); });
});
