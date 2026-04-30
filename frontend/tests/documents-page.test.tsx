import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { DocumentsPage } from '@/pages/DocumentsPage';

const mutateAsync = vi.fn();

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({ token: 'token-abc', loading: false }),
}));

vi.mock('@/hooks/useApi', () => ({
  useDocuments: () => ({ data: [{ id: '1', filename: 'a.pdf', processing_status: 'completed', summary: 'done', upload_date: new Date().toISOString() }], isLoading: false, isError: false }),
  useUploadDocument: () => ({ mutateAsync, isPending: false }),
}));

test('renders documents list', () => {
  const qc = new QueryClient();
  render(<MemoryRouter><QueryClientProvider client={qc}><DocumentsPage /></QueryClientProvider></MemoryRouter>);
  expect(screen.getByText('a.pdf')).toBeInTheDocument();
});

test('clicking upload triggers native file input click', () => {
  const qc = new QueryClient();
  const clickSpy = vi.spyOn(HTMLInputElement.prototype, 'click');

  render(<MemoryRouter><QueryClientProvider client={qc}><DocumentsPage /></QueryClientProvider></MemoryRouter>);

  fireEvent.click(screen.getAllByRole('button', { name: 'Upload' })[0]);
  expect(clickSpy).toHaveBeenCalled();

  clickSpy.mockRestore();
});
