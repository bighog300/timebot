import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InsightsPage } from './InsightsPage';

vi.mock('@/hooks/useApi', () => ({
  useInsightsOverview: vi.fn(),
  useStructuredInsights: vi.fn(),
}));

import { useInsightsOverview, useStructuredInsights } from '@/hooks/useApi';

describe('InsightsPage severity prioritization', () => {
  beforeEach(() => {
    vi.mocked(useInsightsOverview).mockReturnValue({ data: { action_item_summary: {}, category_distribution: [], recent_activity: [] }, isLoading: false, isError: false } as never);
  });

  it('sorts insights by severity and keeps filtering working', async () => {
    vi.mocked(useStructuredInsights).mockReturnValue({
      data: [
        { type: 'risk', title: 'Low Item', severity: 'low', description: 'd' },
        { type: 'risk', title: 'High Item', severity: 'high', description: 'd' },
        { type: 'risk', title: 'Medium Item', severity: 'medium', description: 'd' },
      ],
      isLoading: false,
      isError: false,
    } as never);

    render(<InsightsPage />);

    const sectionText = screen.getByRole('region', { name: 'Structured insights' }).textContent ?? '';
    expect(sectionText.indexOf('High Item')).toBeLessThan(sectionText.indexOf('Medium Item'));
    expect(sectionText.indexOf('Medium Item')).toBeLessThan(sectionText.indexOf('Low Item'));

    await userEvent.selectOptions(screen.getByLabelText('Severity filter'), 'low');
    expect(screen.getByText('Low Item')).toBeTruthy();
    expect(screen.queryByText('High Item')).toBeNull();
  });

  it('renders severity badge and does not crash when severity is missing', () => {
    vi.mocked(useStructuredInsights).mockReturnValue({
      data: [
        { type: 'risk', title: 'Unknown Severity', description: 'd' },
      ],
      isLoading: false,
      isError: false,
    } as never);

    render(<InsightsPage />);
    expect(screen.getByText('Unknown Severity')).toBeTruthy();
    expect(screen.getByText('Severity: Unknown')).toBeTruthy();
  });
});
