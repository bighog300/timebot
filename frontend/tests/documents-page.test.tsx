import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { DocumentsPage } from '@/pages/DocumentsPage';

vi.mock('@/hooks/useApi', () => ({
  useDocuments: () => ({ data: [{ id: '1', filename: 'a.pdf', processing_status: 'completed', summary: 'done', upload_date: new Date().toISOString() }], isLoading: false, isError: false }),
  useUploadDocument: () => ({ mutateAsync: vi.fn() }),
}));

test('renders documents list', () => {
  const qc = new QueryClient();
  render(<MemoryRouter><QueryClientProvider client={qc}><DocumentsPage /></QueryClientProvider></MemoryRouter>);
  expect(screen.getByText('a.pdf')).toBeInTheDocument();
});
