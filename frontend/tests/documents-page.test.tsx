import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { DocumentsPage } from '@/pages/DocumentsPage';

const mutateAsync = vi.fn();
const pushToast = vi.fn();

vi.mock('@/auth/AuthContext', () => ({ useAuth: () => ({ token: 'token-abc', loading: false }) }));
vi.mock('@/store/uiStore', () => ({ useUIStore: (selector: (s: { pushToast: typeof pushToast }) => unknown) => selector({ pushToast }) }));
vi.mock('@/hooks/useApi', () => ({
  useDocuments: () => ({ data: [{ id: '1', filename: 'a.pdf', processing_status: 'completed', summary: 'done', upload_date: new Date().toISOString() }], isLoading: false, isError: false }),
  useUploadDocument: () => ({ mutateAsync, isPending: false }),
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
