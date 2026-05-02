import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
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
  useDocumentClusters: vi.fn(),
  useCategories: vi.fn(),
  useDocumentActionItems: vi.fn(),
  useDocumentAuditHistory: vi.fn(),
  useDocumentRelationships: vi.fn(),
  useConfirmDocumentRelationship: vi.fn(),
  useDismissDocumentRelationship: vi.fn(),
  usePatchDocumentIntelligence: vi.fn(),
  useApproveDocumentCategory: vi.fn(),
  useOverrideDocumentCategory: vi.fn(),
  useStructuredInsights: vi.fn(),
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
  useDocumentClusters,
  useConfirmDocumentRelationship,
  useDismissDocumentRelationship,
  useOverrideDocumentCategory,
  usePatchDocumentIntelligence,
  useStructuredInsights,
} from '@/hooks/useApi';

const baseRelationships = [
  { id: '1', relationship_type: 'thread', status: 'confirmed', confidence: 0.95, related_document_id: 'r1', related_document_title: 'Thread Doc', related_document_name: 'Thread Doc', related_document_snippet: 'thread', direction: 'source', created_at: '', updated_at: null, explanation_metadata: { signals: ['subject_match'] } },
  { id: '2', relationship_type: 'attachment', status: 'pending', confidence: 0.91, related_document_id: 'r2', related_document_title: 'Attachment Doc', related_document_name: 'Attachment Doc', related_document_snippet: 'attachment', direction: 'source', created_at: '', updated_at: null, explanation_metadata: null },
  { id: '3', relationship_type: 'related', status: 'pending', confidence: 0.82, related_document_id: 'r3', related_document_title: 'Related Doc', related_document_name: 'Related Doc', related_document_snippet: 'related', direction: 'source', created_at: '', updated_at: null, explanation_metadata: { reason: 'Common project context', signals: ['shared_terms', 'timeline_proximity'], confidence: 0.82 } },
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
  afterEach(() => cleanup());
  const pushToast = vi.fn();
  const confirmMutate = vi.fn();
  const dismissMutate = vi.fn();

  beforeEach(() => {
    pushToast.mockReset();
    confirmMutate.mockReset();
    dismissMutate.mockReset();
    vi.mocked(useUIStore).mockImplementation(((selector: (state: { pushToast: (msg: string) => void }) => unknown) => selector({ pushToast })) as never);
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
    vi.mocked(useDocumentClusters).mockReturnValue({ isLoading: false, isError: false, isSuccess: true, data: [{ cluster_id: 'cluster-1', document_ids: ['doc-1', 'r3'], document_titles: ['Contract.pdf', 'Related Doc'], relationship_count: 1, dominant_signals: ['ai_detected'] }] } as never);
    vi.mocked(useStructuredInsights).mockReturnValue({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: [],
    } as never);
    vi.mocked(useConfirmDocumentRelationship).mockReturnValue({ isPending: false, mutate: confirmMutate } as never);
    vi.mocked(useDismissDocumentRelationship).mockReturnValue({ isPending: false, mutate: dismissMutate } as never);
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

  it('shows Confirm and Reject for pending AI relationships only', async () => {
    renderPage();
    await screen.findAllByText('Related Doc');
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Reject' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Structural' }));
    expect(screen.queryByRole('button', { name: 'Confirm' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Reject' })).toBeNull();
  });

  it('clicking Confirm updates visible status', async () => {
    const onSuccess = vi.fn();
    vi.mocked(useConfirmDocumentRelationship).mockReturnValue({ isPending: false, mutate: onSuccess } as never);
    renderPage();
    await screen.findByText('Related Doc');
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));
    expect(onSuccess).toHaveBeenCalled();
  });

  it('clicking Reject hides relationship under Pending filter', async () => {
    vi.mocked(useDocumentRelationships).mockReturnValue({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: baseRelationships.map((r) => (r.id === '3' ? { ...r, status: 'dismissed' } : r)),
    } as never);
    renderPage();
    await screen.findByText('Related Doc');
    fireEvent.click(screen.getByRole('button', { name: 'Pending' }));
    expect(screen.queryByText('Related Doc')).toBeNull();
  });

  it('shows error toast when confirm action fails', async () => {
    vi.mocked(useConfirmDocumentRelationship).mockReturnValue({
      isPending: false,
      mutate: (_id: string, opts?: { onError?: () => void }) => opts?.onError?.(),
    } as never);
    renderPage();
    await screen.findByText('Related Doc');
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));
    expect(pushToast).toHaveBeenCalledWith('Failed to confirm relationship');
  });

  it('shows expandable Why related details when metadata exists', async () => {
    renderPage();
    await screen.findByText('Related Doc');
    expect(screen.getAllByText('Why related:').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Common project context').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Why related details').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Reason:').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Confidence:').length).toBeGreaterThan(0);
  });

  it('renders friendly signal labels in explainability details', async () => {
    renderPage();
    await screen.findByText('Related Doc');
    expect(screen.getByText('Shared terms')).toBeTruthy();
    expect(screen.getByText('Timeline proximity')).toBeTruthy();
  });

  it('hides Why related details when metadata is missing', async () => {
    vi.mocked(useDocumentRelationships).mockReturnValue({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: [{ ...baseRelationships[2], id: 'x', related_document_title: 'No Metadata Doc', explanation_metadata: null }],
    } as never);
    renderPage();
    await screen.findByText('No Metadata Doc');
    expect(screen.queryByText('Why related details')).toBeNull();
    expect(screen.queryByText('Why related:')).toBeNull();
  });

  it('keeps filters and inline review actions with explainability details', async () => {
    renderPage();
    await screen.findByText('Related Doc');
    expect(screen.getByRole('button', { name: 'AI-detected' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Pending' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Reject' })).toBeTruthy();
    expect(screen.getAllByText('Why related details').length).toBeGreaterThan(0);
  });

  it('shows View related cluster action when current document has a cluster', async () => {
    renderPage();
    const links = await screen.findAllByRole('link', { name: 'View related cluster' });
    expect(links[0]).toHaveAttribute('href', '/documents?cluster=cluster-1');
  });

  it('does not show View related cluster action when cluster is missing', async () => {
    vi.mocked(useDocumentClusters).mockReturnValue({ isLoading: false, isError: false, isSuccess: true, data: [] } as never);
    renderPage();
    await screen.findByText('Related Doc');
    expect(screen.queryByRole('link', { name: 'View related cluster' })).toBeNull();
  });

  it('renders document-level insights for this document only', async () => {
    vi.mocked(useStructuredInsights).mockReturnValue({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: [
        { type: 'risk', title: 'Low risk', severity: 'low', description: 'Low severity.', related_documents: [{ document_id: 'doc-1', title: 'Contract.pdf' }] },
        { type: 'risk', title: 'Late delivery risk', severity: 'high', description: 'Potential delay noted.', related_documents: [{ document_id: 'doc-1', title: 'Contract.pdf' }] },
        { type: 'risk', title: 'Unknown severity risk', description: 'Missing severity.', related_documents: [{ document_id: 'doc-1', title: 'Contract.pdf' }] },
        { type: 'change', title: 'Scope changed', severity: 'medium', description: 'Scope modified.', related_documents: [{ document_id: 'doc-2', title: 'Other.pdf' }] },
      ],
    } as never);
    renderPage();
    expect(await screen.findByText('Insights for this document')).toBeTruthy();
    const insightsSection = (await screen.findByText('Insights for this document')).closest('div');
    const insightText = insightsSection?.textContent ?? '';
    expect(insightText.indexOf('Late delivery risk')).toBeLessThan(insightText.indexOf('Low risk'));
    expect(insightText.indexOf('Low risk')).toBeLessThan(insightText.indexOf('Unknown severity risk'));
    expect(screen.queryByText('Scope changed')).toBeNull();
    expect(screen.getByText('Severity: High')).toBeTruthy();
    expect(screen.getByText('Severity: Unknown')).toBeTruthy();
    expect(screen.getByText('Potential delay noted.')).toBeTruthy();
  });

  it('renders empty state when no insights match this document id', async () => {
    vi.mocked(useStructuredInsights).mockReturnValue({
      isLoading: false,
      isError: false,
      isSuccess: true,
      data: [{ type: 'risk', title: 'Other doc risk', severity: 'low', description: 'No match.', related_documents: [{ document_id: 'doc-999' }] }],
    } as never);
    renderPage();
    expect(await screen.findByText('No insights found for this document.')).toBeTruthy();
  });
});


it('shows enrichment pending and degraded banners', async () => {
  vi.mocked(api.getDocument).mockResolvedValue({ id: 'doc-1', filename: 'Contract.pdf', processing_status: 'completed', enrichment_pending: true, ai_analysis_degraded: true, processing_error: null, is_favorite: false, is_archived: false, summary: '', ai_category: null, file_type:'pdf', file_size:1, source:'upload', upload_date:new Date().toISOString(), ai_tags:[], user_tags:[] } as never);
  vi.mocked(api.findSimilar).mockResolvedValue({ query: '', total: 0, results: [] } as never);
  vi.mocked(api.getDocumentIntelligence).mockResolvedValue(null as never);
  renderPage();
  expect(await screen.findByText('Analysis complete. Final enrichment is still running.')).toBeInTheDocument();
  expect(await screen.findByText('Analysis completed with partial AI output.')).toBeInTheDocument();
});
