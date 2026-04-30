import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { DocumentsPage } from '@/pages/DocumentsPage';

const mutateAsync = vi.fn();
const gmailPreviewMutateAsync = vi.fn();
const gmailImportMutateAsync = vi.fn();
const pushToast = vi.fn();

vi.mock('@/auth/AuthContext', () => ({ useAuth: () => ({ token: 'token-abc', loading: false }) }));
vi.mock('@/store/uiStore', () => ({ useUIStore: (selector: (s: { pushToast: typeof pushToast }) => unknown) => selector({ pushToast }) }));
vi.mock('@/hooks/useApi', () => ({
  useDocuments: () => ({ data: [{ id: '1', filename: 'a.pdf', processing_status: 'completed', summary: 'done', upload_date: new Date().toISOString() }], isLoading: false, isError: false }),
  useUploadDocument: () => ({ mutateAsync, isPending: false }),
  useConnections: () => ({ data: [{ type: 'gmail', is_authenticated: true, provider_is_configured: true }] }),
  useGmailPreview: () => ({ mutateAsync: gmailPreviewMutateAsync, isPending: false }),
  useGmailImport: () => ({ mutateAsync: gmailImportMutateAsync, isPending: false }),
}));

const renderPage = () => {
  const queryClient = new QueryClient();
  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <DocumentsPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
};

beforeEach(() => {
  mutateAsync.mockReset();
  mutateAsync.mockResolvedValue({});
  pushToast.mockReset();
  gmailPreviewMutateAsync.mockReset();
  gmailImportMutateAsync.mockReset();
  gmailPreviewMutateAsync.mockResolvedValue({ messages: [] });
  gmailImportMutateAsync.mockResolvedValue({ imported_count: 1 });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

test('renders documents list', () => {
  renderPage();
  expect(screen.getByText('a.pdf')).toBeInTheDocument();
});

test('clicking upload triggers native file input click', () => {
  const clickSpy = vi.spyOn(HTMLInputElement.prototype, 'click');
  renderPage();
  fireEvent.click(screen.getByRole('button', { name: 'Upload' }));
  expect(clickSpy).toHaveBeenCalled();
});

test('drag-over state appears and clears on drag leave', () => {
  renderPage();
  const dz = screen.getByTestId('documents-dropzone');
  fireEvent.dragOver(dz);
  expect(dz.className).toContain('border-blue-400');

  fireEvent.dragLeave(dz);
  expect(dz.className).not.toContain('border-blue-400');
});

test('dropping accepted file calls upload mutation', async () => {
  renderPage();
  const dz = screen.getByTestId('documents-dropzone');
  const file = new File(['x'], 'a.pdf', { type: 'application/pdf' });

  fireEvent.drop(dz, { dataTransfer: { files: [file] } });

  await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1));
  expect(mutateAsync).toHaveBeenCalledWith(file);
});

test('unsupported file shows error and does not upload', async () => {
  renderPage();
  const dz = screen.getByTestId('documents-dropzone');

  fireEvent.drop(dz, { dataTransfer: { files: [new File(['x'], 'malware.exe', { type: 'application/octet-stream' })] } });

  await waitFor(() => expect(pushToast).toHaveBeenCalledWith('Unsupported file type: .exe'));
  expect(mutateAsync).not.toHaveBeenCalled();
});

test('multiple files are handled', async () => {
  renderPage();
  const dz = screen.getByTestId('documents-dropzone');
  const fileA = new File(['1'], 'a.pdf');
  const fileB = new File(['2'], 'b.txt');

  fireEvent.drop(dz, { dataTransfer: { files: [fileA, fileB] } });

  await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(2));
  expect(mutateAsync).toHaveBeenNthCalledWith(1, fileA);
  expect(mutateAsync).toHaveBeenNthCalledWith(2, fileB);
});

test('preview form submits request and renders results', async () => {
  gmailPreviewMutateAsync.mockResolvedValueOnce({
    messages: [{ gmail_message_id: 'm1', subject: 'Subject A', sender: 'a@example.com', received_at: '2026-01-01T10:00:00Z', snippet: 'Snippet A', already_imported: false, attachments: [] }],
  });
  renderPage();
  fireEvent.change(screen.getByPlaceholderText('sender@example.com'), { target: { value: 'a@example.com' } });
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }));
  await waitFor(() => expect(gmailPreviewMutateAsync).toHaveBeenCalledWith({ sender_email: 'a@example.com', max_results: 20, include_attachments: false }));
  expect(screen.getByText('Subject A')).toBeInTheDocument();
});

test('selecting messages enables import and calls API', async () => {
  gmailPreviewMutateAsync.mockResolvedValueOnce({
    messages: [{ gmail_message_id: 'm2', subject: 'Subject B', sender: 'b@example.com', received_at: null, snippet: 'Snippet B', already_imported: false, attachments: [] }],
  });
  renderPage();
  fireEvent.change(screen.getByPlaceholderText('sender@example.com'), { target: { value: 'b@example.com' } });
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }));
  await screen.findByText('Subject B');
  const importBtn = screen.getByRole('button', { name: 'Import selected' });
  expect(importBtn).toBeDisabled();
  fireEvent.click(screen.getAllByRole('checkbox')[1]);
  expect(importBtn).not.toBeDisabled();
  fireEvent.click(importBtn);
  await waitFor(() => expect(gmailImportMutateAsync).toHaveBeenCalledWith({ sender_email: 'b@example.com', message_ids: ['m2'], include_attachments: false }));
});

test('already imported badge appears', async () => {
  gmailPreviewMutateAsync.mockResolvedValueOnce({
    messages: [{ gmail_message_id: 'm3', subject: 'Imported', sender: 'c@example.com', received_at: null, snippet: 'Done', already_imported: true, attachments: [] }],
  });
  renderPage();
  fireEvent.change(screen.getByPlaceholderText('sender@example.com'), { target: { value: 'c@example.com' } });
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }));
  await screen.findByText('already imported');
});

test('gmail error state renders', async () => {
  gmailPreviewMutateAsync.mockRejectedValueOnce({ response: { data: { detail: 'OAuth not configured' } } });
  renderPage();
  fireEvent.change(screen.getByPlaceholderText('sender@example.com'), { target: { value: 'd@example.com' } });
  fireEvent.click(screen.getByRole('button', { name: 'Preview' }));
  await screen.findByText('Gmail is not connected or not configured.');
});
