import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
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
        messages: [
          { id: 'm-user', role: 'user', content: 'User question with enough text to check readability and spacing.' },
          { id: 'm1', role: 'assistant', content: 'Long long response content that should wrap on small screens', source_refs: [{ document_id: 'doc-1', document_title: 'Very Long Citation Title', source_type: 'email', snippet: 'Citation preview text to keep readable in small cards.' }, { title: 'Fallback title only citation' }] },
        ],
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



  it('keeps user and assistant messages visually distinct', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    const userMessage = screen.getByTestId('chat-message-user');
    const assistantMessage = screen.getByTestId('chat-message-assistant');
    expect(userMessage.className).toContain('ml-auto');
    expect(assistantMessage.className).toContain('mr-auto');
    expect(userMessage.className).not.toEqual(assistantMessage.className);
  });

  it('renders citation cards in narrow-friendly container', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    expect(screen.getAllByText('Citations (2)').length).toBeGreaterThan(0);
    expect(screen.getByText('Very Long Citation Title').className).toContain('break-words');
    expect(screen.getByText('email')).toBeTruthy();
    expect(screen.getByText('Citation preview text to keep readable in small cards.')).toBeTruthy();
  });

  it('supports explicit citation expand/collapse interactions', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    const toggle = screen.getByRole('button', { name: /Citations \(2\)/ });
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('Very Long Citation Title')).toBeNull();
    fireEvent.click(toggle);
    expect(screen.getByText('Very Long Citation Title')).toBeTruthy();
  });

  it('keeps citation links targeting document detail when document_id exists', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    const link = screen.getByRole('link', { name: /Very Long Citation Title/ });
    expect(link.getAttribute('href')).toBe('/documents/doc-1');
  });

  it('does not crash when optional citation fields are missing', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    expect(screen.getByText('Fallback title only citation')).toBeTruthy();
    expect(screen.queryByText('Untitled source')).toBeNull();
  });

  it('keeps input and send controls available while messages exist', () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    expect(screen.getAllByPlaceholderText('Ask a question').length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: 'Send' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Generate report from this conversation/answer' })).toBeTruthy();
  });
});
