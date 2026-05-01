import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ChatPage } from '@/pages/ChatPage';
import type { ChatMessage } from '@/types/api';

const mocks = vi.hoisted(() => ({
  invalidateChat: vi.fn(),
  streamMock: vi.fn(),
  messagesMock: vi.fn<() => ChatMessage[]>(() => []),
}));

vi.mock('@/hooks/useApi', () => ({
  useChatSessions: () => ({ data: [{ id: 's1', title: 'S1' }] }),
  useCreateChatSession: () => ({ mutateAsync: vi.fn(async () => ({ id: 's1' })) }),
  useChatSession: () => ({ data: { messages: mocks.messagesMock() }, isLoading: false }),
  useCreateReport: () => ({ mutateAsync: vi.fn(async () => ({ id: 'r1' })) }),
  useInvalidateChatSession: () => mocks.invalidateChat,
}));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));
vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api');
  return { ...actual, api: { ...actual.api, sendChatMessageStream: mocks.streamMock } };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('chat page streaming', () => {
  it('uses streaming endpoint and renders chunks/final sources', async () => {
    mocks.streamMock.mockImplementationOnce(async (_sessionId, _payload, handlers) => {
      handlers.onEvent({ type: 'chunk', content: 'Hello ' });
      await Promise.resolve();
      handlers.onEvent({ type: 'chunk', content: 'world' });
      await Promise.resolve();
      handlers.onEvent({ type: 'final', content: 'Hello world', source_refs: [{ document_id: 'd1', document_title: 'Doc A', source_type: 'document', snippet: 'Snippet A' }] });
      await new Promise((resolve) => setTimeout(resolve, 20));
    });

    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    fireEvent.change(screen.getByPlaceholderText('Ask a question'), { target: { value: 'hi' } });
    fireEvent.click(screen.getByText('Send'));

    await waitFor(() => expect(mocks.streamMock).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByText('Hello world')).toBeInTheDocument());
    expect(screen.getByText(/^(Citations|Sources) \(1\)$/)).toBeInTheDocument();
    expect(screen.getByText('Doc A')).toBeInTheDocument();
    expect(screen.getByText('Snippet A')).toBeInTheDocument();
    await waitFor(() => expect(mocks.invalidateChat).toHaveBeenCalledWith('s1'));
    expect(mocks.streamMock).toHaveBeenCalledWith('s1', expect.objectContaining({ message: 'hi' }), expect.any(Object));
  });

  it('renders persisted assistant source refs and excludes user citations', () => {
    mocks.messagesMock.mockReturnValueOnce([
      { id: 'm1', session_id: 's1', role: 'user', content: 'Question', created_at: '2026-01-01T00:00:00Z', source_refs: [{ document_id: 'd-user', document_title: 'Should Not Show' }] },
      { id: 'm2', session_id: 's1', role: 'assistant', content: 'Answer', created_at: '2026-01-01T00:00:01Z', source_refs: [{ document_id: 'd2', document_title: 'Doc B', kind: 'email', preview: 'Preview B' }] },
    ]);

    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    expect(screen.getByText(/^(Citations|Sources) \(1\)$/)).toBeInTheDocument();
    expect(screen.getByText('Doc B')).toBeInTheDocument();
    expect(screen.getByText('Preview B')).toBeInTheDocument();
    expect(screen.queryByText('Should Not Show')).not.toBeInTheDocument();
  });

  it('allows citation section to collapse and expand', () => {
    mocks.messagesMock.mockReturnValueOnce([
      { id: 'm2', session_id: 's1', role: 'assistant', content: 'Answer', created_at: '2026-01-01T00:00:01Z', source_refs: [{ document_id: 'd2', document_title: 'Doc B', snippet: 'Snippet B' }] },
    ]);
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    const citationSummary = screen.getByText(/^(Citations|Sources) \(1\)$/);
    const details = citationSummary.closest('details');
    expect(details).toHaveAttribute('open');
    fireEvent.click(citationSummary);
    expect(details).not.toHaveAttribute('open');
    fireEvent.click(citationSummary);
    expect(details).toHaveAttribute('open');
  });

  it('handles missing optional citation fields safely', () => {
    mocks.messagesMock.mockReturnValueOnce([
      { id: 'm2', session_id: 's1', role: 'assistant', content: 'Answer', created_at: '2026-01-01T00:00:01Z', source_refs: [{}] },
    ]);
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    expect(screen.getByText(/^(Citations|Sources) \(1\)$/)).toBeInTheDocument();
    expect(screen.getByText('Untitled source')).toBeInTheDocument();
  });

  it('disables input while streaming', async () => {
    let resolveStream!: () => void;
    const streamDone = new Promise<void>((resolve) => {
      resolveStream = resolve;
    });

    mocks.streamMock.mockImplementationOnce(async (_sessionId, _payload, handlers) => {
      handlers.onEvent({ type: 'chunk', content: 'partial' });
      await streamDone;
    });

    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    const input = screen.getByPlaceholderText('Ask a question');
    const send = screen.getByText('Send');
    fireEvent.change(input, { target: { value: 'hi' } });
    fireEvent.click(send);

    await waitFor(() => {
      expect(send).toBeDisabled();
      expect(input).toBeDisabled();
    });

    resolveStream();
    await waitFor(() => expect(send).not.toBeDisabled());
  });

  it('shows error state on stream failure', async () => {
    mocks.streamMock.mockRejectedValueOnce(new Error('network down'));
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    fireEvent.change(screen.getByPlaceholderText('Ask a question'), { target: { value: 'hi' } });
    fireEvent.click(screen.getByText('Send'));

    await waitFor(() => expect(screen.getByText(/Streaming failed\. Retry sending your message\./)).toBeInTheDocument());
  });
});
