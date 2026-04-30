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
