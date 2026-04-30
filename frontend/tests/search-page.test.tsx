import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { expect, test, vi } from 'vitest';
import { SearchPage } from '@/pages/SearchPage';

const apiMocks = vi.hoisted(() => ({
  searchKeyword: vi.fn(),
  searchSemantic: vi.fn(),
  listSuggestions: vi.fn(),
  listFacets: vi.fn(),
}));

vi.mock('@/services/api', () => ({
  api: apiMocks,
}));

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <SearchPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

test('shows empty state when query has no results', async () => {
  apiMocks.searchKeyword.mockResolvedValue({ query: 'missing', results: [], total: 0, page: 1, pages: 1 });
  apiMocks.searchSemantic.mockResolvedValue({ query: 'missing', results: [], total: 0 });
  apiMocks.listSuggestions.mockResolvedValue([]);
  apiMocks.listFacets.mockResolvedValue({});

  renderPage();

  const user = userEvent.setup();
  await user.type(screen.getByPlaceholderText('Search documents'), 'missing');

  expect(await screen.findByText('No results found')).toBeInTheDocument();
});
