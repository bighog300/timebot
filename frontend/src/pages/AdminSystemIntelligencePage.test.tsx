import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AdminSystemIntelligencePage } from './AdminSystemIntelligencePage';

vi.mock('@/services/http', () => ({
  http: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
}));
import { http } from '@/services/http';

function wrap() {
  return render(<QueryClientProvider client={new QueryClient()}><AdminSystemIntelligencePage /></QueryClientProvider>);
}

describe('AdminSystemIntelligencePage web references', () => {
  beforeEach(() => {
    vi.mocked(http.get).mockImplementation(async (url: string) => {
      if (url.includes('/web-references')) return { data: [{ id: 'r1', title: 'Ref 1', url: 'https://justice.gov.za/a', source_domain: 'justice.gov.za', status: 'candidate' }, { id: 'r2', title: 'Ref 2', url: 'https://justice.gov.za/b', source_domain: 'justice.gov.za', status: 'active' }] } as never;
      return { data: [] } as never;
    });
    vi.mocked(http.post).mockResolvedValue({ data: {} } as never);
    vi.mocked(http.delete).mockResolvedValue({ data: { ok: true } } as never);
  });

  it('creates candidate and supports approve/archive/delete/status filters', async () => {
    wrap();
    fireEvent.click(await screen.findByRole('button', { name: 'Web References' }));
    expect(await screen.findByText('Ref 1')).toBeTruthy();

    fireEvent.change(screen.getByDisplayValue('all'), { target: { value: 'candidate' } });
    expect(screen.getByText('Ref 1')).toBeTruthy();

    fireEvent.change(screen.getByPlaceholderText('URL'), { target: { value: 'https://gov.za/x' } });
    fireEvent.change(screen.getByPlaceholderText('Title'), { target: { value: 'Gov ref' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add candidate' }));

    fireEvent.click(screen.getAllByText('approve/activate')[0]);
    fireEvent.click(screen.getAllByText('archive')[0]);
    fireEvent.click(screen.getAllByText('delete')[0]);

    await waitFor(() => expect(vi.mocked(http.post)).toHaveBeenCalled());
    expect(vi.mocked(http.delete)).toHaveBeenCalled();
  });
});
