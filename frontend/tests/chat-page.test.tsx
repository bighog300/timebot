import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { ChatPage } from '@/pages/ChatPage';

vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));
vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api');
  return { ...actual, api: { ...actual.api, sendChatMessageStream: vi.fn(async () => undefined) } };
});
vi.mock('@/hooks/useApi', () => ({
  useChatSessions: () => ({ data: [{ id: 'a1', title: 'Active', is_archived: false }, { id: 'r1', title: 'Archived', is_archived: true }] }),
  useAssistants: () => ({ data: [{ id: 'as1', name: 'General Assistant', description: '', required_plan: 'free', enabled: true }] }),
  useCreateChatSession: () => ({ mutateAsync: vi.fn(async () => ({ id: 'new1' })) }),
  useUpdateChatSession: () => ({ mutateAsync: vi.fn(async () => ({})), mutate: vi.fn() }),
  useDeleteChatSession: () => ({ mutate: vi.fn() }),
  useChatSession: () => ({ data: { id: 'a1', assistant_id: 'as1', messages: [], is_archived: false } }),
}));

describe('chat ux', () => {
  it('shows active/archived sections and assistant in header', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    expect(screen.getByText('Active chats')).toBeInTheDocument();
    expect(screen.getByText('Archived chats')).toBeInTheDocument();
    expect(screen.getByText(/Assistant: General Assistant/)).toBeInTheDocument();
  });

  it('opens create modal', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    fireEvent.click(screen.getByText('New Chat'));
    expect(screen.getByText('Create chat')).toBeInTheDocument();
  });
});
