import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { InsightsPage } from '@/pages/InsightsPage';

const mockUseInsightsOverview = vi.fn();
const mockUseStructuredInsights = vi.fn();

const mockUseInsightsAccess = vi.fn();

vi.mock('@/hooks/useApi', () => ({
  useInsightsAccess: () => mockUseInsightsAccess(),
  useInsightsOverview: () => mockUseInsightsOverview(),
  useStructuredInsights: () => mockUseStructuredInsights(),
}));

describe('insights structured panel', () => {
  afterEach(() => {
    cleanup();
    mockUseInsightsAccess.mockReset();
    mockUseInsightsOverview.mockReset();
    mockUseStructuredInsights.mockReset();
  });

  it('fetches and renders structured insight cards with severity and optional links/evidence', () => {
    mockUseInsightsAccess.mockReturnValue({ insightsEnabled: true, isLoading: false });
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
    expect(screen.getByText('Severity: High')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: 'Master Service Agreement' });
    expect(link).toHaveAttribute('href', '/documents/doc-1');
    expect(screen.getByText(/timeline/)).toBeInTheDocument();
  });

  it('applies type and severity filters and keeps related links/evidence visible', () => {
    mockUseInsightsAccess.mockReturnValue({ insightsEnabled: true, isLoading: false });
    mockUseInsightsOverview.mockReturnValue({ data: { action_item_summary: {}, category_distribution: [], recent_activity: [] }, isLoading: false, isError: false });
    mockUseStructuredInsights.mockReturnValue({
      data: [
        {
          type: 'risk',
          title: 'Risk insight',
          description: 'A high risk issue.',
          severity: 'high',
          related_documents: [{ document_id: 'doc-2', title: 'Risk Document' }],
          evidence_refs: [{ source: 'document', reference: 'sec-1' }],
        },
        {
          type: 'change',
          title: 'Change insight',
          description: 'A medium change issue.',
          severity: 'medium',
          related_documents: [{ document_id: 'doc-3', title: 'Change Document' }],
          evidence_refs: [{ source: 'timeline', reference: 'chg-1' }],
        },
      ],
      isLoading: false,
      isError: false,
    });

    render(<InsightsPage />);

    fireEvent.click(screen.getByRole('button', { name: 'Risks' }));
    expect(screen.getByText('Risk insight')).toBeInTheDocument();
    expect(screen.queryByText('Change insight')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Risk Document' })).toHaveAttribute('href', '/documents/doc-2');
    expect(screen.getByText(/document • sec-1/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Severity filter'), { target: { value: 'medium' } });
    expect(screen.getByText('No insights match the selected filters.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'All' }));
    expect(screen.getByText('Change insight')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Change Document' })).toHaveAttribute('href', '/documents/doc-3');
    expect(screen.getByText(/timeline • chg-1/)).toBeInTheDocument();
  });

  it('renders empty state when no structured insights exist', () => {
    mockUseInsightsAccess.mockReturnValue({ insightsEnabled: true, isLoading: false });
    mockUseInsightsOverview.mockReturnValue({ data: { action_item_summary: {}, category_distribution: [], recent_activity: [] }, isLoading: false, isError: false });
    mockUseStructuredInsights.mockReturnValue({ data: [], isLoading: false, isError: false });

    render(<InsightsPage />);

    expect(screen.getByText('No structured insights available.')).toBeInTheDocument();
  });

  it('does not crash when optional evidence fields are missing', () => {
    mockUseInsightsAccess.mockReturnValue({ insightsEnabled: true, isLoading: false });
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

  it('renders document links from related_document_ids when available', () => {
    mockUseInsightsAccess.mockReturnValue({ insightsEnabled: true, isLoading: false });
    mockUseInsightsOverview.mockReturnValue({ data: { action_item_summary: {}, category_distribution: [], recent_activity: [] }, isLoading: false, isError: false });
    mockUseStructuredInsights.mockReturnValue({
      data: [
        {
          type: 'risk',
          title: 'Document id references',
          description: 'Links should be generated from ids.',
          severity: 'medium',
          related_document_ids: ['doc-11', 'doc-12'],
        },
      ],
      isLoading: false,
      isError: false,
    });

    render(<InsightsPage />);

    expect(screen.getByRole('link', { name: 'doc-11' })).toHaveAttribute('href', '/documents/doc-11');
    expect(screen.getByRole('link', { name: 'doc-12' })).toHaveAttribute('href', '/documents/doc-12');
  });

  it('renders timeline navigation from related_event_ids when available', () => {
    mockUseInsightsAccess.mockReturnValue({ insightsEnabled: true, isLoading: false });
    mockUseInsightsOverview.mockReturnValue({ data: { action_item_summary: {}, category_distribution: [], recent_activity: [] }, isLoading: false, isError: false });
    mockUseStructuredInsights.mockReturnValue({
      data: [
        {
          type: 'milestone',
          title: 'Timeline references',
          description: 'Timeline links should be rendered from event ids.',
          severity: 'low',
          related_event_ids: ['event-1', 'event 2'],
        },
      ],
      isLoading: false,
      isError: false,
    });

    render(<InsightsPage />);

    expect(screen.getByRole('link', { name: 'View event event-1' })).toHaveAttribute('href', '/timeline?eventId=event-1');
    expect(screen.getByRole('link', { name: 'View event event 2' })).toHaveAttribute('href', '/timeline?eventId=event%202');
  });

  it('does not crash when related ids are missing', () => {
    mockUseInsightsAccess.mockReturnValue({ insightsEnabled: true, isLoading: false });
    mockUseInsightsOverview.mockReturnValue({ data: { action_item_summary: {}, category_distribution: [], recent_activity: [] }, isLoading: false, isError: false });
    mockUseStructuredInsights.mockReturnValue({
      data: [
        {
          type: 'change',
          title: 'No related ids',
          description: 'Renders without related id arrays.',
          severity: 'low',
        },
      ],
      isLoading: false,
      isError: false,
    });

    render(<InsightsPage />);

    expect(screen.getByText('No related ids')).toBeInTheDocument();
    expect(screen.queryByText('Document links')).not.toBeInTheDocument();
    expect(screen.queryByText('Timeline')).not.toBeInTheDocument();
  });
});
