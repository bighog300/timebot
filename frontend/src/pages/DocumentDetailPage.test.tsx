import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DocumentDetailPage } from './DocumentDetailPage';

vi.mock('@/store/uiStore', () => ({ useUIStore: vi.fn() }));
vi.mock('@/services/api', () => ({
  api: {
    getDocument: vi.fn(),
    findSimilar: vi.fn(),
    updateDocument: vi.fn(),
    reprocessDocument: vi.fn(),
    deleteDocument: vi.fn(),
  },
}));
vi.mock('@/hooks/useApi', () => ({
  useDocumentIntelligence: vi.fn(),
  useCategories: vi.fn(),
  useDocumentActionItems: vi.fn(),
  useDocumentAuditHistory: vi.fn(),
  useDocumentRelationships: vi.fn(),
  usePatchDocumentIntelligence: vi.fn(),
  useApproveDocumentCategory: vi.fn(),
  useOverrideDocumentCategory: vi.fn(),
}));

import { useUIStore } from '@/store/uiStore';
import { api } from '@/services/api';
import {
  useApproveDocumentCategory,
  useCategories,
  useDocumentActionItems,
  useDocumentAuditHistory,
  useDocumentIntelligence,
  useDocumentRelationships,
  useOverrideDocumentCategory,
  usePatchDocumentIntelligence,
} from '@/hooks/useApi';

const baseRelationships = [
  { id: '1', relationship_type: 'thread', status: 'confirmed', confidence: 0.95, related_document_id: 'r1', related_document_title: 'Thread Doc', related_document_name: 'Thread Doc', related_document_snippet: 'thread', direction: 'source', created_at: '', updated_at: null, explanation_metadata: { signals: ['subject_match'] } },
  { id: '2', relationship_type: 'attachment', status: 'pending', confidence: 0.91, related_document_id: 'r2', related_document_title: 'Attachment Doc', related_document_name: 'Attachment Doc', related_document_snippet: 'attachment', direction: 'source', created_at: '', updated_at: null, explanation_metadata: null },
  { id: '3', relationship_type: 'related', status: 'pending', confidence: 0.82, related_document_id: 'r3', related_document_title: 'Related Doc', related_document_name: 'Related Doc', related_document_snippet: 'related', direction: 'source', created_at: '', updated_at: null, explanation_metadata: { signals: ['semantic_similarity'], confidence: 0.82 } },
] as const;

function renderPage() {
  const qc = new QueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/documents/doc-1']}>
        <Routes>
          <Route path="/documents/:id" element={<DocumentDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('DocumentDetailPage relationship filtering', () => {
  beforeEach(() => {
    vi.mocked(useUIStore).mockImplementation(((selector: (state: { pushToast: (msg: string) => void }) => unknown) => selector({ pushToast: vi.fn() })) as never);
    vi.mocked(api.getDocument).mockResolvedValue({ id: 'doc-1', filename: 'Contract.pdf', processing_status: 'processed', processing_error: null, is_favorite: false, is_archived: false, summary: '', ai_category: null } as never);
    vi.mocked(api.findSimilar).mockResolvedValue({ results: [], query: '', total: 0 } as never);
    vi.mocked(useDocumentIntelligence).mockReturnValue({ isLoading: false, isError: false, isSuccess: true, data: null } as never);
    vi.mocked(useCategories).mockReturnValue({ data: [] } as never);
    vi.mocked(useDocumentActionItems).mockReturnValue({ isLoading: false, isError: false, isSuccess: true, data: [] } as never);
    vi.mocked(useDocumentAuditHistory).mockReturnValue({ isLoading: false, isError: false, isSuccess: true, data: [] } as never);
    vi.mocked(usePatchDocumentIntelligence).mockReturnValue({ mutate: vi.fn() } as never);
    vi.mocked(useApproveDocumentCategory).mockReturnValue({ mutate: vi.fn() } as never);
    vi.mocked(useOverrideDocumentCategory).mockReturnValue({ mutate: vi.fn() } as never);
    vi.mocked(useDocumentRelationships).mockReturnValue({ isLoading: false, isError: false, isSuccess: true, data: baseRelationships } as never);
  });

  it('renders filter buttons', async () => {
    renderPage();
    expect(await screen.findByRole('button', { name: 'All' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Structural' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'AI-detected' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Confirmed' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Pending' })).toBeTruthy();
  });

  it('filters displayed relationships and keeps grouping sections', async () => {
    renderPage();
    await screen.findByText('Thread Doc');
    fireEvent.click(screen.getByRole('button', { name: 'Pending' }));
    expect(screen.queryByText('Thread Doc')).toBeNull();
    expect(screen.getByText('Attachment Doc')).toBeTruthy();
    expect(screen.getByText('Related Doc')).toBeTruthy();
    expect(screen.getByText('Email Thread')).toBeTruthy();
    expect(screen.getByText('Attachments')).toBeTruthy();
    expect(screen.getByText('Related Documents')).toBeTruthy();
  });

  it('renders confidence indicator when available', async () => {
    renderPage();
    expect(await screen.findByText('82% confidence')).toBeTruthy();
  });

  it('does not crash when metadata is missing', async () => {
    vi.mocked(useDocumentRelationships).mockReturnValue({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: [{ ...baseRelationships[2], id: 'x', related_document_title: 'No Metadata Doc', explanation_metadata: null, confidence: null }],
    } as never);
    renderPage();
    expect(await screen.findByText('No Metadata Doc')).toBeTruthy();
    expect(screen.getAllByText('n/a confidence').length).toBeGreaterThan(0);
  });
});
