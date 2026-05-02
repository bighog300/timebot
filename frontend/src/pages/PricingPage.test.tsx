import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { PricingPage } from './PricingPage';

const checkoutMutate = vi.fn();

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
      {
        slug: 'pro',
        name: 'Pro',
        price_monthly_cents: 2900,
        currency: 'usd',
        limits: { documents_per_month: 200 },
        features: { billing_configured: false },
        is_current: false,
      },
    ],
  }),
  useSubscription: () => ({ data: { plan: { slug: 'free' } } }),
  useCreateCheckoutSession: () => ({ mutateAsync: checkoutMutate, isPending: false }),
  useCreateCustomerPortalSession: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

describe('PricingPage', () => {
  it('renders pricing plans even when billing is unavailable', () => {
    render(<MemoryRouter><PricingPage /></MemoryRouter>);
    expect(screen.getByText('Plans & Pricing')).toBeInTheDocument();
    expect(screen.getByText('Free')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Billing not configured' })).toBeDisabled();
  });
});
