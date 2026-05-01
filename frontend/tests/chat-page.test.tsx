import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ChatPage } from '@/pages/ChatPage';

const { invalidateChat, streamMock } = vi.hoisted(() => ({
  invalidateChat: vi.fn(),
  streamMock: vi.fn(),
}));

vi.mock('@/hooks/useApi', () => ({
  useChatSessions: () => ({ data: [{ id: 's1', title: 'S1' }] }),
  useCreateChatSession: () => ({ mutateAsync: vi.fn(async () => ({ id: 's1' })) }),
  useChatSession: () => ({ data: { messages: [] }, isLoading: false }),
  useCreateReport: () => ({ mutateAsync: vi.fn(async () => ({ id: 'r1' })) }),
  useInvalidateChatSession: () => invalidateChat,
}));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));
vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api');
  return { ...actual, api: { ...actual.api, sendChatMessageStream: streamMock } };
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('chat page streaming', () => {
  it('uses streaming endpoint and renders chunks/final sources', async () => {
    streamMock.mockImplementationOnce(async (_sessionId, _payload, handlers) => {
      handlers.onEvent({ type: 'chunk', content: 'Hello ' });
      await Promise.resolve();
      handlers.onEvent({ type: 'chunk', content: 'world' });
      await Promise.resolve();
      handlers.onEvent({ type: 'final', content: 'Hello world', source_refs: [{ document_id: 'd1', document_title: 'Doc A' }] });
      await new Promise((resolve) => setTimeout(resolve, 20));
    });

    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    fireEvent.change(screen.getByPlaceholderText('Ask a question'), { target: { value: 'hi' } });
    fireEvent.click(screen.getByText('Send'));

    await waitFor(() => expect(streamMock).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByText('Hello world')).toBeInTheDocument());
    await waitFor(() => expect(invalidateChat).toHaveBeenCalledWith('s1'));
    expect(streamMock).toHaveBeenCalledWith('s1', expect.objectContaining({ message: 'hi' }), expect.any(Object));
  });

  it('disables input while streaming', async () => {
    streamMock.mockImplementationOnce(async (_sessionId, _payload, handlers) => {
      handlers.onEvent({ type: 'chunk', content: 'partial' });
      await new Promise((resolve) => setTimeout(resolve, 10));
    });

    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    const input = screen.getByPlaceholderText('Ask a question');
    const send = screen.getByText('Send');
    fireEvent.change(input, { target: { value: 'hi' } });
    fireEvent.click(send);

    await waitFor(() => expect(send).toBeDisabled());
    expect(input).toBeDisabled();
  });

  it('shows error state on stream failure', async () => {
    streamMock.mockRejectedValueOnce(new Error('network down'));
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    fireEvent.change(screen.getByPlaceholderText('Ask a question'), { target: { value: 'hi' } });
    fireEvent.click(screen.getByText('Send'));

    await waitFor(() => expect(screen.getByText(/Streaming failed\. Retry sending your message\./)).toBeInTheDocument());
  });
});
