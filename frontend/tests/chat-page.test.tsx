import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ChatPage } from '@/pages/ChatPage';

const sendMutate = vi.fn(async()=>({}));
vi.mock('@/hooks/useApi', () => ({ useChatSessions: () => ({ data:[{id:'s1',title:'S1'}] }), useCreateChatSession: () => ({ mutateAsync: vi.fn(async()=>({id:'s1'})) }), useChatSession: () => ({ data:{messages:[{id:'m1', role:'assistant', content:'hello', source_refs:[{document_id:'d1', document_title:'Doc A'}]}]} }), useSendChatMessage: () => ({ mutateAsync: sendMutate, isPending:false }), useCreateReport: () => ({ mutateAsync: vi.fn(async()=>({id:'r1'})) }) }));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));

describe('chat page', () => {
  it('sends and renders answer/source links', async () => { render(<MemoryRouter><ChatPage/></MemoryRouter>); expect(screen.getByText('hello')).toBeInTheDocument(); expect(screen.getByRole('link',{name:'Doc A'}).getAttribute('href')).toBe('/documents/d1'); fireEvent.change(screen.getByPlaceholderText('Ask a question'), {target:{value:'hi'}}); fireEvent.click(screen.getByText('Send')); expect(sendMutate).toHaveBeenCalled(); });
});
