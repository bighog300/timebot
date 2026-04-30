import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import type { SearchResponse, SearchResultItem, SemanticSearchResponse, SemanticSearchResult } from '@/types/api';

type SearchMode = 'keyword' | 'semantic';
type SearchResult = SearchResponse | SemanticSearchResponse;

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function highlightMatches(text: string, query: string) {
  const terms = query
    .trim()
    .split(/\s+/)
    .map((term) => term.trim())
    .filter(Boolean);

  if (!text || terms.length === 0) return text;

  const pattern = new RegExp(`(${terms.map((t) => escapeRegExp(t)).join('|')})`, 'ig');
  const parts = text.split(pattern);

  return parts.map((part, idx) =>
    terms.some((term) => part.toLowerCase() === term.toLowerCase()) ? (
      <mark key={`${part}-${idx}`} className="rounded bg-amber-300/30 px-0.5 text-amber-100">
        {part}
      </mark>
    ) : (
      <span key={`${part}-${idx}`}>{part}</span>
    ),
  );
}

export function SearchPage() {
  const [searchParams] = useSearchParams();
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<SearchMode>('keyword');
  const [semanticUnavailable, setSemanticUnavailable] = useState(false);

  useEffect(() => {
    const urlQuery = searchParams.get('q') ?? '';
    if (urlQuery && urlQuery !== query) {
      setQuery(urlQuery);
    }
  }, [searchParams, query]);

  const search = useQuery<SearchResult>({
    queryKey: ['search', mode, query],
    queryFn: async () => {
      if (mode === 'keyword') {
        return api.searchKeyword(query);
      }
      try {
        setSemanticUnavailable(false);
        return await api.searchSemantic(query);
      } catch {
        setSemanticUnavailable(true);
        return { query, results: [], total: 0 } satisfies SemanticSearchResponse;
      }
    },
    enabled: query.length > 1,
  });
  const suggestions = useQuery({ queryKey: ['suggestions', query], queryFn: () => api.listSuggestions(query), enabled: query.length > 0 });
  const facets = useQuery({ queryKey: ['facets', query], queryFn: () => api.listFacets(query) });

  const resultItems: Array<SearchResultItem | SemanticSearchResult> = search.data?.results ?? [];
  const showSearching = search.isFetching && query.length > 1;

  const normalizedQuery = useMemo(() => query.trim(), [query]);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Search</h1>
      <div className="flex gap-2">
        <input className="flex-1 rounded border border-slate-700 bg-slate-900 px-3 py-2" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search documents" />
        <Button onClick={() => setMode('keyword')} className={mode === 'keyword' ? '' : 'bg-slate-700'}>Keyword</Button>
        <Button onClick={() => setMode('semantic')} className={mode === 'semantic' ? '' : 'bg-slate-700'}>Semantic</Button>
      </div>
      {mode === 'semantic' && semanticUnavailable && (
        <p className="text-xs text-slate-400">Semantic search unavailable</p>
      )}
      <Card>
        <h3 className="mb-2 text-sm">Suggestions</h3>
        {suggestions.isLoading && <LoadingState label="Loading suggestions..." />}
        {suggestions.isError && <ErrorState message="Failed to load suggestions" />}
        <div className="flex flex-wrap gap-2">{suggestions.data?.map((s) => <button key={s} className="rounded bg-slate-800 px-2 py-1 text-xs" onClick={() => setQuery(s)}>{s}</button>)}</div>
      </Card>
      <Card>
        <h3 className="mb-2 text-sm">Facets</h3>
        {facets.isLoading && <LoadingState label="Loading facets..." />}
        {facets.isError && <ErrorState message="Failed to load facets" />}
        <pre className="overflow-auto text-xs text-slate-300">{JSON.stringify(facets.data ?? {}, null, 2)}</pre>
      </Card>
      <div className="space-y-2">
        {showSearching && <LoadingState label="Searching documents..." />}
        {search.isError && <ErrorState message="Search failed" />}
        {search.isSuccess && resultItems.length === 0 && <EmptyState label="No results found" />}
        {resultItems.map((item) => {
          const summary = item.document.summary?.trim() || 'No summary available.';
          return (
            <Card key={item.document.id}>
              <div className="font-medium">{item.document.filename}</div>
              <div className="text-xs text-slate-400">{'relevance' in item ? `Relevance ${item.relevance.toFixed(3)}` : `Similarity ${item.similarity_score.toFixed(3)}`}</div>
              <div className="mt-2 text-sm text-slate-300">
                {mode === 'keyword' ? highlightMatches(summary, normalizedQuery) : summary}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
