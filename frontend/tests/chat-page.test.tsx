import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ChatPage } from '@/pages/ChatPage';

const mocks = vi.hoisted(() => ({ invalidate: vi.fn(), create: vi.fn().mockResolvedValue({ id: 's1' }), stream: vi.fn().mockResolvedValue(undefined) }));

vi.mock('@/hooks/useApi', () => ({
  useChatSessions: () => ({ data: [{ id: 's1', title: 'Case prep', assistant_id: 'a2', is_archived: false, is_deleted: false }] }),
  useAssistants: () => ({ data: [{ id: 'a1', name: 'General Assistant', required_plan: 'free', enabled: true, default_prompt_template_id: 't1' }, { id: 'a2', name: 'South African Legal Defense Expert', required_plan: 'pro', enabled: true, default_prompt_template_id: 't2', locked: true }] }),
  useChatPromptTemplates: () => ({ data: [{ id: 't1', name: 'General chat template', type: 'chat', locked: false }, { id: 't2', name: 'Legal Strategy & Defense Report', type: 'chat', locked: false }] }),
  useCreateChatSession: () => ({ mutateAsync: mocks.create }),
  useDeleteChatSession: () => ({ mutate: vi.fn() }),
  useUpdateChatSession: () => ({ mutate: vi.fn(), mutateAsync: vi.fn() }),
  useDocuments: () => ({ data: [{ id: 'd1', filename: 'evidence.pdf' }] }),
  useChatSession: () => ({ data: { id: 's1', assistant_id: 'a2', prompt_template_id: 't2', linked_document_ids: ['d1'], messages: [] } }),
  useInvalidateChatSession: () => mocks.invalidate,
}));
vi.mock('@/services/api', () => ({ api: { sendChatMessageStream: mocks.stream }, getErrorDetail: () => 'error' }));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));

describe('chat advisor/template flow', () => {
  it('shows advisor label in sidebar and header plus template', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    expect(screen.getByText('South African Legal Defense Expert')).toBeInTheDocument();
    expect(screen.getByText(/Template: Legal Strategy & Defense Report/)).toBeInTheDocument();
  });

  it('auto-selects default template when assistant selected', async () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    fireEvent.click(screen.getByText('New Chat'));
    fireEvent.change(screen.getByDisplayValue('Select assistant'), { target: { value: 'a1' } });
    const templateSelect = screen.getAllByRole('combobox')[1] as HTMLSelectElement;
    expect(templateSelect.value).toBe('t1');
  });

  it('stream send invalidates session', async () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    fireEvent.change(screen.getByPlaceholderText('Ask a question'), { target: { value: 'hello' } });
    fireEvent.click(screen.getByText('Send'));
    await waitFor(() => expect(mocks.invalidate).toHaveBeenCalledWith('s1'));
  });
});
