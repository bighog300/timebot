import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InsightsPage } from './InsightsPage';
import { MemoryRouter } from 'react-router-dom';

vi.mock('@/hooks/useApi', () => ({
  useInsightsAccess: vi.fn(),
  useInsightsOverview: vi.fn(),
  useStructuredInsights: vi.fn(),
}));

import { useInsightsAccess, useInsightsOverview, useStructuredInsights } from '@/hooks/useApi';

describe('InsightsPage gating and severity prioritization', () => {
  beforeEach(() => {
    vi.mocked(useInsightsAccess).mockReturnValue({ insightsEnabled: true, isLoading: false } as never);
    vi.mocked(useInsightsOverview).mockReturnValue({ data: { action_item_summary: {}, category_distribution: [], recent_activity: [] }, isLoading: false, isError: false } as never);
  });

  it('shows upgrade prompt for free users', () => {
    vi.mocked(useInsightsAccess).mockReturnValue({ insightsEnabled: false, isLoading: false } as never);
    vi.mocked(useStructuredInsights).mockReturnValue({ data: [], isLoading: false, isError: false } as never);

    render(<MemoryRouter><InsightsPage /></MemoryRouter>);
    expect(screen.getByText('Upgrade required')).toBeInTheDocument();
  });

  it('sorts insights by severity and keeps filtering working for pro users', async () => {
    vi.mocked(useStructuredInsights).mockReturnValue({
      data: [
        { type: 'risk', title: 'Low Item', severity: 'low', description: 'd' },
        { type: 'risk', title: 'High Item', severity: 'high', description: 'd' },
        { type: 'risk', title: 'Medium Item', severity: 'medium', description: 'd' },
      ],
      isLoading: false,
      isError: false,
    } as never);

    render(<MemoryRouter><InsightsPage /></MemoryRouter>);

    const sectionText = screen.getByRole('region', { name: 'Structured insights' }).textContent ?? '';
    expect(sectionText.indexOf('High Item')).toBeLessThan(sectionText.indexOf('Medium Item'));
    expect(sectionText.indexOf('Medium Item')).toBeLessThan(sectionText.indexOf('Low Item'));

    await userEvent.selectOptions(screen.getByLabelText('Severity filter'), 'low');
    expect(screen.getByText('Low Item')).toBeTruthy();
    expect(screen.queryByText('High Item')).toBeNull();
  });
});
