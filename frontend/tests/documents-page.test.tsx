import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { DocumentsPage } from '@/pages/DocumentsPage';

vi.mock('@/hooks/useApi', () => ({
  useDocuments: () => ({ data: [{ id: '1', filename: 'a.pdf', processing_status: 'completed', summary: 'done', upload_date: new Date().toISOString() }], isLoading: false, isError: false }),
  useUploadDocument: () => ({ mutateAsync: vi.fn() }),
}));

test('renders documents list', () => {
  const qc = new QueryClient();
  render(<QueryClientProvider client={qc}><DocumentsPage /></QueryClientProvider>);
  expect(screen.getByText('a.pdf')).toBeInTheDocument();
});
