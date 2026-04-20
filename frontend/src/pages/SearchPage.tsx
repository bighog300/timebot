import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export function SearchPage() {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<'keyword' | 'semantic'>('keyword');

  const search = useQuery({
    queryKey: ['search', mode, query],
    queryFn: () => (mode === 'keyword' ? api.searchKeyword(query) : api.searchSemantic(query)),
    enabled: query.length > 1,
  });
  const suggestions = useQuery({ queryKey: ['suggestions', query], queryFn: () => api.listSuggestions(query), enabled: query.length > 0 });
  const facets = useQuery({ queryKey: ['facets', query], queryFn: () => api.listFacets(query) });

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Search</h1>
      <div className="flex gap-2">
        <input className="flex-1 rounded border border-slate-700 bg-slate-900 px-3 py-2" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search documents" />
        <Button onClick={() => setMode('keyword')} className={mode === 'keyword' ? '' : 'bg-slate-700'}>Keyword</Button>
        <Button onClick={() => setMode('semantic')} className={mode === 'semantic' ? '' : 'bg-slate-700'}>Semantic</Button>
      </div>
      <Card>
        <h3 className="mb-2 text-sm">Suggestions</h3>
        <div className="flex flex-wrap gap-2">{suggestions.data?.map((s) => <button key={s} className="rounded bg-slate-800 px-2 py-1 text-xs" onClick={() => setQuery(s)}>{s}</button>)}</div>
      </Card>
      <Card>
        <h3 className="mb-2 text-sm">Facets</h3>
        <pre className="overflow-auto text-xs text-slate-300">{JSON.stringify(facets.data ?? {}, null, 2)}</pre>
      </Card>
      <div className="space-y-2">
        {'results' in (search.data ?? {})
          ? (search.data?.results ?? []).map((item) => (
              <Card key={item.document.id}>
                <div className="font-medium">{item.document.filename}</div>
                <div className="text-xs text-slate-400">{'relevance' in item ? item.relevance : item.similarity_score}</div>
              </Card>
            ))
          : null}
      </div>
    </div>
  );
}
