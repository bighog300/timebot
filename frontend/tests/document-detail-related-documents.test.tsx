import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DocumentDetailPage } from '@/pages/DocumentDetailPage';

const mockUseDocumentRelationships = vi.fn();

vi.mock('@/services/api', () => ({
  api: {
    getDocument: vi.fn(async () => ({ id: 'doc-1', filename: 'Doc 1', processing_status: 'completed', is_favorite: false, is_archived: false })),
    findSimilar: vi.fn(async () => ({ results: [] })),
    updateDocument: vi.fn(), reprocessDocument: vi.fn(), deleteDocument: vi.fn(),
  },
}));

vi.mock('@/hooks/useApi', () => ({
  useDocumentIntelligence: () => ({ isLoading: false, isError: false, isSuccess: true, data: null }),
  useCategories: () => ({ data: [] }),
  useDocumentActionItems: () => ({ isLoading: false, isError: false, isSuccess: true, data: [] }),
  useDocumentAuditHistory: () => ({ isLoading: false, isError: false, isSuccess: true, data: [] }),
  usePatchDocumentIntelligence: () => ({ mutate: vi.fn() }),
  useApproveDocumentCategory: () => ({ mutate: vi.fn() }),
  useOverrideDocumentCategory: () => ({ mutate: vi.fn() }),
  useDocumentRelationships: () => mockUseDocumentRelationships(),
}));

vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/documents/doc-1']}>
      <QueryClientProvider client={new QueryClient()}>
        <Routes>
          <Route path="/documents/:id" element={<DocumentDetailPage />} />
        </Routes>
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

describe('DocumentDetailPage related documents panel', () => {
  it('shows empty state', async () => {
    mockUseDocumentRelationships.mockReturnValue({ isLoading: false, isError: false, isSuccess: true, data: [] });
    renderPage();
    expect(await screen.findByText('No related documents yet.')).toBeInTheDocument();
  });

  it('renders related document fields and link', async () => {
    mockUseDocumentRelationships.mockReturnValue({
      isLoading: false, isError: false, isSuccess: true,
      data: [{
        id: 'rel-1', status: 'confirmed', relationship_type: 'related', confidence: 0.88,
        related_document_id: 'doc-2', related_document_title: 'Doc 2', related_document_name: 'Doc 2',
        related_document_snippet: 'Snippet 2', direction: 'source', created_at: new Date().toISOString(), updated_at: null,
      }],
    });
    renderPage();
    expect(await screen.findByText('Doc 2')).toBeInTheDocument();
    expect(screen.getByText('Snippet 2')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Doc 2' })).toHaveAttribute('href', '/documents/doc-2');
  });
});
