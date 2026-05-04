import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PricingPage } from './PricingPage';

vi.mock('@/hooks/useApi', () => ({
  usePlans: () => ({
    data: [
      {
        slug: 'free',
        name: 'Free',
        price_monthly_cents: 0,
        currency: 'usd',
        limits: { documents_per_month: 10 },
        features: {},
        is_current: true,
      },
      { slug: 'pro', name: 'Pro', price_monthly_cents: 2900, currency: 'usd', limits: {}, features: {}, is_current: false },
    ],
  }),
  useSubscription: () => ({ data: { status: 'active', current_period_start: '2026-05-01', current_period_end: '2026-06-01', plan: { slug: 'free' } } }),
  useUsage: () => ({ data: { messages: { used: 1, limit: 10 }, reports: { used: 0, limit: 2 } } }),
}));

describe('PricingPage', () => {
  it('renders pricing plans and static upgrade CTA', () => {
    render(<MemoryRouter><PricingPage /></MemoryRouter>);
    expect(screen.getByText('Plans & Pricing')).toBeInTheDocument();
    expect(screen.getByText('Free')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Request upgrade' })).toBeInTheDocument();
  });
});
