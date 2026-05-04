import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PricingPage } from './PricingPage';
import { ChatPage } from './ChatPage';

vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));
vi.mock('@/services/api', () => ({
  api: { sendChatMessageStream: vi.fn().mockRejectedValue({ response: { status: 402, data: { detail: { error: 'upgrade_required', feature: 'chat_send', required_plan: 'pro', message: 'Upgrade to continue' } } } }) },
  getErrorDetail: () => 'upgrade_required',
}));
vi.mock('@/hooks/useApi', () => ({
  usePlans: () => ({ data: [
    { slug:'free', name:'Free', price_monthly_cents:0, limits:{}, features:{}, is_current:true },
    { slug:'pro', name:'Pro', price_monthly_cents:2900, limits:{}, features:{}, is_current:false },
    { slug:'business', name:'Business', price_monthly_cents:9900, limits:{}, features:{}, is_current:false },
  ]}),
  useSubscription: () => ({ data: { status: 'active', current_period_start: '2026-05-01', current_period_end: '2026-06-01', plan: { slug: 'free' } } }),
  useUsage: () => ({ data: { messages: { used: 1, limit: 10 }, reports: { used: 0, limit: 2 } } }),
  useBillingStatus: () => ({ data: { enabled: false, provider: 'manual' } }),
  useCreateCheckoutSession: () => ({ isPending: false, mutateAsync: vi.fn() }),
  useChatSessions: () => ({ data: [{ id: 's1', title: 'A', is_archived: false, is_deleted: false }] }),
  useChatSession: () => ({ data: { id:'s1', is_archived:false, is_deleted:false, messages:[], linked_document_ids:[] } }),
  useAssistants: () => ({ data: [{ id:'a1', name:'Legal Assistant', required_plan:'pro', locked:true }] }),
  useCreateChatSession: () => ({ mutateAsync: vi.fn() }),
  useUpdateChatSession: () => ({ mutate: vi.fn(), mutateAsync: vi.fn() }),
  useDeleteChatSession: () => ({ mutate: vi.fn() }),
}));

describe('monetization ux', () => {
  it('upgrade renders plans and billing status', () => {
    render(<MemoryRouter><PricingPage /></MemoryRouter>);
    expect(screen.getByText('Plans & Pricing')).toBeInTheDocument();
    expect(screen.getByText('Business')).toBeInTheDocument();
    expect(screen.getByText(/Subscription status:/i)).toBeInTheDocument();
  });


  it('manual billing mode shows request-upgrade and contact-admin CTAs', () => {
    render(<MemoryRouter><PricingPage /></MemoryRouter>);
    expect(screen.getByText(/Billing mode:/i)).toHaveTextContent('Manual billing mode');
    expect(screen.getByRole('button', { name: 'Request upgrade' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Contact Admin' })).toBeInTheDocument();
  });

  it('locked assistant links to upgrade and send upgrade modal opens', async () => {
    render(<MemoryRouter><ChatPage /></MemoryRouter>);
    fireEvent.click(screen.getByText('Send'));
    expect(await screen.findByRole('heading', { name: 'Upgrade required' })).toBeInTheDocument();
    const viewPlansLinks = screen.getAllByRole('link', { name: 'View plans' });
    expect(viewPlansLinks.some((link) => link.getAttribute('href')?.includes('/upgrade'))).toBe(true);
  });
});
