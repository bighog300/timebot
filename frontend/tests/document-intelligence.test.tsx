import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor, renderHook, fireEvent } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, expect, test, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { DocumentDetailPage } from '@/pages/DocumentDetailPage';
import { useDocumentIntelligence } from '@/hooks/useApi';
import { api } from '@/services/api';

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({ token: 'token-abc', loading: false }),
}));

vi.mock('@/services/api', async () => {
  const actual = await vi.importActual<typeof import('@/services/api')>('@/services/api');
  return {
    ...actual,
    api: {
      ...actual.api,
      getDocument: vi.fn(),
      findSimilar: vi.fn(),
      getDocumentIntelligence: vi.fn(),
      listCategories: vi.fn().mockResolvedValue([]),
      listDocumentActionItems: vi.fn().mockResolvedValue([]),
      getDocumentAuditHistory: vi.fn().mockResolvedValue([]),
      reprocessDocument: vi.fn().mockResolvedValue(undefined),
    },
  };
});

function wrapper(children: ReactNode) {
  const qc = new QueryClient();
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

beforeEach(() => {
  vi.clearAllMocks();
  cleanup();
});

test('document detail shows pending state when intelligence is null', async () => {
  vi.mocked(api.getDocument).mockResolvedValue({
    id: 'doc-1', filename: 'a.pdf', file_type: 'pdf', file_size: 1, source: 'upload', upload_date: new Date().toISOString(), processing_status: 'completed',
    ai_tags: [], user_tags: [], is_favorite: false, is_archived: false,
  } as never);
  vi.mocked(api.findSimilar).mockResolvedValue({ query: '', total: 0, results: [] });
  vi.mocked(api.getDocumentIntelligence).mockResolvedValue(null);

  const qc = new QueryClient();
  render(
    <MemoryRouter initialEntries={['/documents/doc-1']}>
      <QueryClientProvider client={qc}>
        <Routes><Route path="/documents/:id" element={<DocumentDetailPage />} /></Routes>
      </QueryClientProvider>
    </MemoryRouter>,
  );

  expect(await screen.findByText('Intelligence is not available yet.')).toBeInTheDocument();
});

test('useDocumentIntelligence does not retry on 404', async () => {
  vi.mocked(api.getDocumentIntelligence).mockRejectedValue({ isAxiosError: true, response: { status: 404 } });

  const { result } = renderHook(() => useDocumentIntelligence('doc-404'), {
    wrapper: ({ children }) => wrapper(children),
  });

  await waitFor(() => expect(result.current.isError).toBe(true));
  expect(api.getDocumentIntelligence).toHaveBeenCalledTimes(1);
});

test('document detail does not fetch intelligence while processing', async () => {
  vi.mocked(api.getDocument).mockResolvedValue({
    id: 'doc-2', filename: 'b.pdf', file_type: 'pdf', file_size: 1, source: 'upload', upload_date: new Date().toISOString(), processing_status: 'processing',
    ai_tags: [], user_tags: [], is_favorite: false, is_archived: false,
  } as never);
  vi.mocked(api.findSimilar).mockResolvedValue({ query: '', total: 0, results: [] });

  const qc = new QueryClient();
  render(
    <MemoryRouter initialEntries={['/documents/doc-2']}>
      <QueryClientProvider client={qc}>
        <Routes><Route path="/documents/:id" element={<DocumentDetailPage />} /></Routes>
      </QueryClientProvider>
    </MemoryRouter>,
  );

  expect(await screen.findByText('Document is still processing. Intelligence is not available yet.')).toBeInTheDocument();
  expect(api.getDocumentIntelligence).not.toHaveBeenCalled();
});


test('reprocess click calls API endpoint', async () => {
  vi.mocked(api.getDocument).mockResolvedValue({
    id: 'doc-3', filename: 'c.pdf', file_type: 'pdf', file_size: 1, source: 'upload', upload_date: new Date().toISOString(), processing_status: 'completed',
    ai_tags: [], user_tags: [], is_favorite: false, is_archived: false,
  } as never);
  vi.mocked(api.findSimilar).mockResolvedValue({ query: '', total: 0, results: [] });
  vi.mocked(api.getDocumentIntelligence).mockResolvedValue(null);

  const qc = new QueryClient();
  render(
    <MemoryRouter initialEntries={['/documents/doc-3']}>
      <QueryClientProvider client={qc}>
        <Routes><Route path="/documents/:id" element={<DocumentDetailPage />} /></Routes>
      </QueryClientProvider>
    </MemoryRouter>,
  );

  const btn = (await screen.findAllByText('Reprocess'))[0];
  fireEvent.click(btn);
  await waitFor(() => expect(api.reprocessDocument).toHaveBeenCalledWith('doc-3'));
});

test('document detail displays intelligence summary when available', async () => {
  vi.mocked(api.getDocument).mockResolvedValue({
    id: 'doc-4', filename: 'd.pdf', file_type: 'pdf', file_size: 1, source: 'upload', upload_date: new Date().toISOString(), processing_status: 'completed',
    ai_tags: [], user_tags: [], is_favorite: false, is_archived: false, summary: 'doc summary',
  } as never);
  vi.mocked(api.findSimilar).mockResolvedValue({ query: '', total: 0, results: [] });
  vi.mocked(api.getDocumentIntelligence).mockResolvedValue({
    document_id: 'doc-4', summary: 'intel summary', key_points: [], suggested_category_id: null, confidence: 'high', suggested_tags: [], entities: {},
    model_name: null, model_version: null, model_metadata: {}, category_status: 'suggested', generated_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  } as never);

  render(<MemoryRouter initialEntries={['/documents/doc-4']}><QueryClientProvider client={new QueryClient()}><Routes><Route path="/documents/:id" element={<DocumentDetailPage />} /></Routes></QueryClientProvider></MemoryRouter>);
  expect(await screen.findByDisplayValue('intel summary')).toBeInTheDocument();
});

test('document detail falls back to document summary when intelligence summary blank', async () => {
  vi.mocked(api.getDocument).mockResolvedValue({
    id: 'doc-5', filename: 'e.pdf', file_type: 'pdf', file_size: 1, source: 'upload', upload_date: new Date().toISOString(), processing_status: 'completed',
    ai_tags: [], user_tags: [], is_favorite: false, is_archived: false, summary: 'fallback document summary',
  } as never);
  vi.mocked(api.findSimilar).mockResolvedValue({ query: '', total: 0, results: [] });
  vi.mocked(api.getDocumentIntelligence).mockResolvedValue({
    document_id: 'doc-5', summary: '', key_points: [], suggested_category_id: null, confidence: 'high', suggested_tags: [], entities: {},
    model_name: null, model_version: null, model_metadata: {}, category_status: 'suggested', generated_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  } as never);

  render(<MemoryRouter initialEntries={['/documents/doc-5']}><QueryClientProvider client={new QueryClient()}><Routes><Route path="/documents/:id" element={<DocumentDetailPage />} /></Routes></QueryClientProvider></MemoryRouter>);
  expect(await screen.findByText('fallback document summary')).toBeInTheDocument();
});
