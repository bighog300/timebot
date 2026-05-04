import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ChatPage } from '@/pages/ChatPage';

const { pushToast, sendChatMessageStream, createMutateAsync, updateMutateAsync, updateMutate, deleteMutate } = vi.hoisted(() => ({
  pushToast: vi.fn(),
  sendChatMessageStream: vi.fn(async () => undefined),
  createMutateAsync: vi.fn(async () => ({ id: 'new1' })),
  updateMutateAsync: vi.fn(async () => ({})),
  updateMutate: vi.fn(),
  deleteMutate: vi.fn(),
}));

let sessionsData: any[] = [];
let chatSessionData: any = {};

vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast }) }));
vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api');
  return {
    ...actual,
    api: { ...actual.api, sendChatMessageStream },
    getErrorDetail: (e: unknown) => String((e as Error)?.message || e || 'error'),
  };
});
vi.mock('@/hooks/useApi', () => ({
  useChatSessions: () => ({ data: sessionsData, isLoading: false, error: null }),
  useAssistants: () => ({ data: [{ id: 'as1', name: 'General Assistant', description: '', required_plan: 'free', enabled: true }] }),
  useCreateChatSession: () => ({ mutateAsync: createMutateAsync }),
  useUpdateChatSession: () => ({ mutateAsync: updateMutateAsync, mutate: updateMutate }),
  useDeleteChatSession: () => ({ mutate: deleteMutate }),
  useChatSession: () => ({ data: chatSessionData, isLoading: false, error: null }),
}));

describe('chat ux regressions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionsData = [
      { id: 'a1', title: 'Active', is_archived: false, is_deleted: false },
      { id: 'r1', title: 'Archived', is_archived: true, is_deleted: false },
    ];
    chatSessionData = {
      id: 'a1',
      title: 'Active',
      assistant_id: 'as1',
      prompt_template_id: 'pt-1',
      linked_document_ids: ['doc-1', 'doc-2'],
      is_archived: false,
      is_deleted: false,
      messages: [
        { id: 'm1', role: 'user', content: 'hello' },
        { id: 'm2', role: 'assistant', content: 'world', metadata_json: { document_references: [{ document_title: 'Ref One' }] } },
      ],
    };
  });

  it('lists sessions, selects archived session, and loads/render messages with context panel', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    expect(screen.getByText('Active chats')).toBeInTheDocument();
    expect(screen.getByText('Archived chats')).toBeInTheDocument();
    expect(screen.getByText('hello')).toBeInTheDocument();
    expect(screen.getByText('world')).toBeInTheDocument();
    expect(screen.getAllByText(/Assistant: General Assistant/).length).toBeGreaterThan(0);
    expect(screen.getByText('Prompt template: pt-1')).toBeInTheDocument();
    expect(screen.getByText('Linked docs: doc-1, doc-2')).toBeInTheDocument();
    expect(screen.getByText('Last response refs: Ref One')).toBeInTheDocument();

    chatSessionData = { ...chatSessionData, id: 'r1', is_archived: true, title: 'Archived' };
    fireEvent.click(screen.getByRole('button', { name: 'Archived' }));
    expect(screen.getByText(/read-only/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ask a question')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Send' })).toBeDisabled();
  });

  it('create modal sends assistant_id, prompt_template_id, linked_document_ids', async () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    fireEvent.click(screen.getByText('New Chat'));
    fireEvent.change(screen.getByPlaceholderText('title'), { target: { value: 'Created Chat' } });
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'as1' } });
    fireEvent.change(screen.getByPlaceholderText('prompt template id'), { target: { value: 'pt-new' } });
    fireEvent.change(screen.getByPlaceholderText('linked documents comma-separated'), { target: { value: 'doc-a, doc-b' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    await waitFor(() => expect(createMutateAsync).toHaveBeenCalledWith({
      title: 'Created Chat',
      assistant_id: 'as1',
      prompt_template_id: 'pt-new',
      linked_document_ids: ['doc-a', 'doc-b'],
    }));
  });

  it('sends message and handles 402 upgrade_required', async () => {
    sendChatMessageStream.mockResolvedValueOnce(undefined);
    sendChatMessageStream.mockRejectedValueOnce(new Error('402 upgrade_required'));
    render(<MemoryRouter><ChatPage /></MemoryRouter>);

    fireEvent.change(screen.getByPlaceholderText('Ask a question'), { target: { value: 'Question 1' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send' }));
    await waitFor(() => expect(sendChatMessageStream).toHaveBeenCalledWith('a1', { message: 'Question 1' }, expect.any(Object)));

    fireEvent.change(screen.getByPlaceholderText('Ask a question'), { target: { value: 'Question 2' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send' }));
    await waitFor(() => expect(screen.getByText('Upgrade required')).toBeInTheDocument());
    expect(pushToast).toHaveBeenCalled();
  });

  it('delete requires confirmation and stale selected chat is cleared after delete', () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const { rerender } = render(<MemoryRouter><ChatPage /></MemoryRouter>);
    fireEvent.click(screen.getByRole('button', { name: 'Active' }));
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    expect(confirmSpy).toHaveBeenCalledWith('Delete chat?');
    expect(deleteMutate).not.toHaveBeenCalled();

    confirmSpy.mockReturnValue(true);
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    expect(deleteMutate).toHaveBeenCalledWith('a1');

    sessionsData = [{ id: 'r1', title: 'Archived', is_archived: true, is_deleted: false }];
    chatSessionData = { ...chatSessionData, id: 'r1', is_archived: true, is_deleted: false, messages: [] };
    rerender(<MemoryRouter><ChatPage /></MemoryRouter>);
    expect(screen.queryByRole('button', { name: 'Active' })).toBeNull();
    expect(screen.getByText(/read-only/)).toBeInTheDocument();
  });

  it('archive uses update mutation and rename ignores empty names', async () => {
    const promptSpy = vi.spyOn(window, 'prompt').mockReturnValue('');
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    fireEvent.click(screen.getByRole('button', { name: 'Archive' }));
    expect(updateMutate).toHaveBeenCalledWith({ sessionId: 'a1', payload: { is_archived: true } });

    fireEvent.click(screen.getByRole('button', { name: 'Rename' }));
    expect(promptSpy).toHaveBeenCalled();
    expect(updateMutateAsync).not.toHaveBeenCalled();
  });
});
