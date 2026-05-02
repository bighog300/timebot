import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DocumentsPage } from './DocumentsPage';

vi.mock('@/auth/AuthContext', () => ({ useAuth: vi.fn() }));
vi.mock('@/hooks/useApi', () => ({
  useDocuments: vi.fn(),
  useDocumentClusters: vi.fn(),
  useConnections: vi.fn(),
  useGmailPreview: vi.fn(),
  useGmailImport: vi.fn(),
  useUploadDocument: vi.fn(),
}));
vi.mock('@/store/uiStore', () => ({ useUIStore: vi.fn() }));

import { useAuth } from '@/auth/AuthContext';
import { useConnections, useDocumentClusters, useDocuments, useGmailImport, useGmailPreview, useUploadDocument } from '@/hooks/useApi';
import { useUIStore } from '@/store/uiStore';

function renderPage(initialEntry = '/documents') {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/documents" element={<DocumentsPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('DocumentsPage onboarding and first-value guidance', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({ token: 't', loading: false } as never);
    vi.mocked(useUIStore).mockImplementation(((selector: (state: { pushToast: (msg: string) => void }) => unknown) => selector({ pushToast: vi.fn() })) as never);
    vi.mocked(useUploadDocument).mockReturnValue({ isPending: false, mutateAsync: vi.fn() } as never);
    vi.mocked(useGmailPreview).mockReturnValue({ isPending: false, mutateAsync: vi.fn() } as never);
    vi.mocked(useGmailImport).mockReturnValue({ isPending: false, mutateAsync: vi.fn() } as never);
    vi.mocked(useConnections).mockReturnValue({ data: [{ type: 'gmail', is_authenticated: true, provider_is_configured: true }] } as never);
    vi.mocked(useDocuments).mockReturnValue({ data: [], isLoading: false, isError: false } as never);
    vi.mocked(useDocumentClusters).mockReturnValue({ data: [], isSuccess: true } as never);
  });

  afterEach(() => {
    cleanup();
  });

  it('shows upload onboarding hint when onboardingAction=upload', () => {
    renderPage('/documents?onboardingAction=upload');
    expect(screen.getByTestId('onboarding-upload-hint')).toBeTruthy();
  });

  it('shows Gmail onboarding hint when onboardingAction=gmail', () => {
    renderPage('/documents?onboardingAction=gmail');
    expect(screen.getByTestId('onboarding-gmail-hint')).toBeTruthy();
  });

  it('shows suggested next actions when documents exist', () => {
    vi.mocked(useDocuments).mockReturnValue({
      data: [{ id: 'doc-1', filename: 'A.pdf', summary: 'A summary', upload_date: '2026-01-01T00:00:00Z', processing_status: 'processed' }],
      isLoading: false,
      isError: false,
    } as never);

    renderPage('/documents');
    expect(screen.getByText('Suggested next actions')).toBeTruthy();
    expect(screen.getByRole('link', { name: 'View summary' })).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Open timeline' })).toBeTruthy();
  });

  it('shows starter chat question action when documents exist', () => {
    vi.mocked(useDocuments).mockReturnValue({
      data: [{ id: 'doc-1', filename: 'A.pdf', summary: 'A summary', upload_date: '2026-01-01T00:00:00Z', processing_status: 'processed' }],
      isLoading: false,
      isError: false,
    } as never);

    renderPage('/documents');
    expect(screen.getByRole('link', { name: 'Ask: What are the key events in these documents?' })).toBeTruthy();
  });

  it('preserves normal behavior without onboardingAction', () => {
    renderPage('/documents');
    expect(screen.queryByTestId('onboarding-upload-hint')).toBeNull();
    expect(screen.queryByTestId('onboarding-gmail-hint')).toBeNull();
    expect(screen.getByText('Drag and drop documents here')).toBeTruthy();
    expect(screen.getByText('Import from Gmail')).toBeTruthy();
  });

  it('renders clusters and document names', () => {
    vi.mocked(useDocuments).mockReturnValue({
      data: [{ id: 'doc-1', filename: 'A.pdf', summary: 'A summary', upload_date: '2026-01-01T00:00:00Z', processing_status: 'processed' }],
      isLoading: false,
      isError: false,
    } as never);
    vi.mocked(useDocumentClusters).mockReturnValue({
      isSuccess: true,
      data: [{ cluster_id: 'c1', document_ids: ['doc-1', 'doc-2'], document_titles: ['A.pdf', 'B.pdf'], relationship_count: 1, dominant_signals: ['ai_detected'] }],
    } as never);
    renderPage('/documents');
    expect(screen.getByText('Cluster (2 documents)')).toBeTruthy();
    expect(screen.getByText('A.pdf, B.pdf')).toBeTruthy();
  });

  it('renders cluster empty state', () => {
    vi.mocked(useDocuments).mockReturnValue({
      data: [{ id: 'doc-1', filename: 'A.pdf', summary: 'A summary', upload_date: '2026-01-01T00:00:00Z', processing_status: 'processed' }],
      isLoading: false,
      isError: false,
    } as never);
    vi.mocked(useDocumentClusters).mockReturnValue({ isSuccess: true, data: [] } as never);
    renderPage('/documents');
    expect(screen.getByText('No clusters yet.')).toBeTruthy();
  });
  it('renders responsive desktop and mobile document layouts without table role assumptions', () => {
    vi.mocked(useDocuments).mockReturnValue({
      data: [{ id: 'doc-1', filename: 'A.pdf', summary: 'A summary', upload_date: '2026-01-01T00:00:00Z', processing_status: 'processed' }],
      isLoading: false,
      isError: false,
    } as never);

    renderPage('/documents');
    expect(screen.getByTestId('documents-desktop-list')).toBeTruthy();
    expect(screen.getByTestId('documents-mobile-cards')).toBeTruthy();
    expect(screen.queryByRole('table')).toBeNull();
  });

  it('shows stage-aware status label on document list entries', () => {
    vi.mocked(useDocuments).mockReturnValue({
      data: [{ id: 'doc-1', filename: 'A.pdf', summary: 'A summary', upload_date: '2026-01-01T00:00:00Z', processing_status: 'processing', processing_stage: 'enriching' }],
      isLoading: false,
      isError: false,
    } as never);
    renderPage('/documents');
    expect(screen.getAllByText('enriching').length).toBeGreaterThan(0);
  });

  it('keeps upload and gmail actions accessible', () => {
    renderPage('/documents');
    expect(screen.getByRole('button', { name: 'Choose files' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Preview' })).toBeTruthy();
  });

});
