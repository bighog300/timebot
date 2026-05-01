import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ChatPage } from './ChatPage';

vi.mock('@/hooks/useApi', () => ({
  useChatSessions: vi.fn(),
  useCreateChatSession: vi.fn(),
  useChatSession: vi.fn(),
  useInvalidateChatSession: vi.fn(),
  useCreateReport: vi.fn(),
}));

vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));
vi.mock('@/services/api', () => ({ api: { sendChatMessageStream: vi.fn() }, getErrorDetail: () => 'error' }));

import { useChatSessions, useCreateChatSession, useChatSession, useInvalidateChatSession, useCreateReport } from '@/hooks/useApi';

describe('ChatPage mobile layout', () => {
  beforeEach(() => {
    vi.mocked(useChatSessions).mockReturnValue({ data: [{ id: 'sess-1', title: 'Session one' }] } as never);
    vi.mocked(useCreateChatSession).mockReturnValue({ mutateAsync: vi.fn().mockResolvedValue({ id: 'sess-1' }) } as never);
    vi.mocked(useInvalidateChatSession).mockReturnValue(vi.fn() as never);
    vi.mocked(useCreateReport).mockReturnValue({ mutateAsync: vi.fn() } as never);
    vi.mocked(useChatSession).mockReturnValue({
      data: {
        messages: [{ id: 'm1', role: 'assistant', content: 'Long long response content that should wrap on small screens', source_refs: [{ document_id: 'doc-1', document_title: 'Very Long Citation Title', snippet: 'Citation preview text to keep readable in small cards.' }] }],
      },
      isLoading: false,
    } as never);
  });

  afterEach(() => {
    cleanup();
  });

  it('applies mobile-friendly wrapping and scroll layout classes', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    expect(screen.getByTestId('chat-message-list').className).toContain('overflow-y-auto');
    expect(screen.getByTestId('chat-input-panel').className).toContain('sticky');
    expect(screen.getByText(/Long long response/).className).toContain('break-words');
  });

  it('renders citation cards in narrow-friendly container', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    expect(screen.getAllByText('Citations (1)').length).toBeGreaterThan(0);
    expect(screen.getByText('Very Long Citation Title').className).toContain('break-words');
    expect(screen.getByText('Citation preview text to keep readable in small cards.')).toBeTruthy();
  });

  it('keeps input and send controls available while messages exist', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    expect(screen.getAllByPlaceholderText('Ask a question').length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: 'Send' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Generate report from this conversation/answer' })).toBeTruthy();
  });
});
