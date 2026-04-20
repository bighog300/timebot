import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { SearchPage } from '@/pages/SearchPage';

const searchKeyword = vi.fn();
const searchSemantic = vi.fn();
const listSuggestions = vi.fn();
const listFacets = vi.fn();

vi.mock('@/services/api', () => ({
  api: {
    searchKeyword,
    searchSemantic,
    listSuggestions,
    listFacets,
  },
}));

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  render(
    <QueryClientProvider client={qc}>
      <SearchPage />
    </QueryClientProvider>,
  );
}

test('shows empty state when query has no results', async () => {
  searchKeyword.mockResolvedValue({ query: 'missing', results: [], total: 0, page: 1, pages: 1 });
  searchSemantic.mockResolvedValue({ query: 'missing', results: [], total: 0 });
  listSuggestions.mockResolvedValue([]);
  listFacets.mockResolvedValue({});

  renderPage();

  const user = userEvent.setup();
  await user.type(screen.getByPlaceholderText('Search documents'), 'missing');

  expect(await screen.findByText('No matching documents found.')).toBeInTheDocument();
});
