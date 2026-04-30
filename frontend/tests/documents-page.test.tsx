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
  const qc = new QueryClient();
  return render(<MemoryRouter><QueryClientProvider client={qc}><DocumentsPage /></QueryClientProvider></MemoryRouter>);
};

beforeEach(() => { mutateAsync.mockReset(); mutateAsync.mockResolvedValue({}); pushToast.mockReset(); });
afterEach(() => cleanup());

test('renders documents list', () => { renderPage(); expect(screen.getByText('a.pdf')).toBeInTheDocument(); });

test('clicking upload triggers native file input click', () => {
  const clickSpy = vi.spyOn(HTMLInputElement.prototype, 'click');
  renderPage();
  fireEvent.click(screen.getByRole('button', { name: 'Upload' }));
  expect(clickSpy).toHaveBeenCalled();
  clickSpy.mockRestore();
});

test('drag-over state appears', () => {
  renderPage();
  const dz = screen.getByTestId('documents-dropzone');
  fireEvent.dragOver(dz);
  expect(dz.className).toContain('border-blue-400');
});

test('dropping accepted file calls upload mutation', async () => {
  renderPage();
  const dz = screen.getByTestId('documents-dropzone');
  fireEvent.drop(dz, { dataTransfer: { files: [new File(['x'], 'a.pdf', { type: 'application/pdf' })] } });
  await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1));
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
  fireEvent.drop(dz, { dataTransfer: { files: [new File(['1'], 'a.pdf'), new File(['2'], 'b.txt')] } });
  await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(2));
});
