import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RelationshipReviewPage } from '@/pages/RelationshipReviewPage';

const mockUseRelationshipReviews = vi.fn();

vi.mock('@/hooks/useApi', () => ({
  useRelationshipReviews: (status: string) => mockUseRelationshipReviews(status),
  useConfirmRelationshipReview: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDismissRelationshipReview: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

vi.mock('@/hooks/useRoleAccess', () => ({ useRoleAccess: () => ({ canMutate: true }) }));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => vi.fn() }));

function renderPage() {
  return render(
    <MemoryRouter>
      <QueryClientProvider client={new QueryClient()}>
        <RelationshipReviewPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

describe('RelationshipReviewPage', () => {
  it('renders relationship items returned by API', () => {
    mockUseRelationshipReviews.mockReturnValue({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: [
        {
          id: 'rel-1',
          source_document_id: 'doc-a',
          target_document_id: 'doc-b',
          source_document_title: 'Source Doc',
          target_document_title: 'Target Doc',
          source_document_snippet: 'Source snippet text',
          target_document_snippet: 'Target snippet text',
          relationship_type: 'related',
          confidence: 0.88,
          status: 'pending',
        },
      ],
    });

    renderPage();

    expect(screen.getByText('Source Doc')).toBeInTheDocument();
    expect(screen.getByText('Target Doc')).toBeInTheDocument();
    expect(screen.getByText('Source snippet text')).toBeInTheDocument();
    expect(screen.getByText('Target snippet text')).toBeInTheDocument();
    expect(screen.queryByText('No relationships to review')).not.toBeInTheDocument();
  });

  it('shows empty state only when API returns an empty array', () => {
    mockUseRelationshipReviews.mockReturnValue({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: [],
    });

    renderPage();

    expect(screen.getByText('No relationships to review')).toBeInTheDocument();
  });
});
