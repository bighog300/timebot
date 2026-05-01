import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { InsightsPage } from '@/pages/InsightsPage';

const mockUseInsightsOverview = vi.fn();
const mockUseStructuredInsights = vi.fn();

vi.mock('@/hooks/useApi', () => ({
  useInsightsOverview: () => mockUseInsightsOverview(),
  useStructuredInsights: () => mockUseStructuredInsights(),
}));

describe('insights structured panel', () => {
  afterEach(() => {
    cleanup();
    mockUseInsightsOverview.mockReset();
    mockUseStructuredInsights.mockReset();
  });

  it('fetches and renders structured insight cards with severity and optional links/evidence', () => {
    mockUseInsightsOverview.mockReturnValue({ data: { action_item_summary: {}, category_distribution: [], recent_activity: [] }, isLoading: false, isError: false });
    mockUseStructuredInsights.mockReturnValue({
      data: [
        {
          type: 'risk',
          title: 'Contract renewal risk',
          description: 'Renewal date is within 15 days with no owner assigned.',
          severity: 'high',
          related_documents: [{ document_id: 'doc-1', title: 'Master Service Agreement' }],
          evidence_refs: [{ source: 'timeline', reference: 'event-17', quote: 'Renewal window starts soon.' }],
        },
      ],
      isLoading: false,
      isError: false,
    });

    render(<InsightsPage />);

    expect(screen.getByText('Contract renewal risk')).toBeInTheDocument();
    expect(screen.getByText('Severity: high')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: 'Master Service Agreement' });
    expect(link).toHaveAttribute('href', '/documents/doc-1');
    expect(screen.getByText(/timeline/)).toBeInTheDocument();
  });

  it('renders empty state when no structured insights exist', () => {
    mockUseInsightsOverview.mockReturnValue({ data: { action_item_summary: {}, category_distribution: [], recent_activity: [] }, isLoading: false, isError: false });
    mockUseStructuredInsights.mockReturnValue({ data: [], isLoading: false, isError: false });

    render(<InsightsPage />);

    expect(screen.getByText('No structured insights available.')).toBeInTheDocument();
  });

  it('does not crash when optional evidence fields are missing', () => {
    mockUseInsightsOverview.mockReturnValue({ data: { action_item_summary: {}, category_distribution: [], recent_activity: [] }, isLoading: false, isError: false });
    mockUseStructuredInsights.mockReturnValue({
      data: [
        {
          type: 'info',
          title: 'Missing evidence fields',
          description: 'Insight with sparse evidence payload.',
          severity: 'low',
          evidence_refs: [{}],
        },
      ],
      isLoading: false,
      isError: false,
    });

    render(<InsightsPage />);

    expect(screen.getByText('Missing evidence fields')).toBeInTheDocument();
    expect(screen.getByText('Evidence reference')).toBeInTheDocument();
  });
});
