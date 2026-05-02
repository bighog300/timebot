import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PricingPage } from './PricingPage';

vi.mock('@/hooks/useApi', () => ({
  usePlans: () => ({ data: [{ slug: 'free', name: 'Free', price_monthly_cents: 0, currency: 'usd', limits: { documents_per_month: 10 }, features: {}, is_current: true }] }),
  useSubscription: () => ({ data: { plan: { slug: 'free' } } }),
}));

describe('PricingPage', () => {
  it('renders pricing plans', () => {
    render(<MemoryRouter><PricingPage /></MemoryRouter>);
    expect(screen.getByText('Plans & Pricing')).toBeInTheDocument();
    expect(screen.getByText('Free')).toBeInTheDocument();
  });
});
