import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { ErrorState, LoadingState } from '@/components/ui/States';

export function DocumentDetailPage() {
  const { id = '' } = useParams();
  const qc = useQueryClient();
  const documentQuery = useQuery({ queryKey: ['document', id], queryFn: () => api.getDocument(id), enabled: !!id });
  const similarQuery = useQuery({ queryKey: ['similar', id], queryFn: () => api.findSimilar(id), enabled: !!id });

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['document', id] });
    qc.invalidateQueries({ queryKey: ['documents'] });
  };

  const updateMutation = useMutation({
    mutationFn: (patch: Record<string, unknown>) => api.updateDocument(id, patch),
    onSuccess: refresh,
  });
  const reprocessMutation = useMutation({ mutationFn: () => api.reprocessDocument(id), onSuccess: refresh });
  const deleteMutation = useMutation({ mutationFn: () => api.deleteDocument(id), onSuccess: () => (window.location.href = '/documents') });

  if (documentQuery.isLoading) return <LoadingState />;
  if (documentQuery.isError || !documentQuery.data) return <ErrorState message="Document not found" />;

  const doc = documentQuery.data;
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{doc.filename}</h1>
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => updateMutation.mutate({ is_favorite: !doc.is_favorite })}>{doc.is_favorite ? 'Unfavorite' : 'Favorite'}</Button>
        <Button onClick={() => updateMutation.mutate({ is_archived: !doc.is_archived })}>{doc.is_archived ? 'Unarchive' : 'Archive'}</Button>
        <Button onClick={() => reprocessMutation.mutate()}>Reprocess</Button>
        <Button className="bg-red-700 hover:bg-red-600" onClick={() => deleteMutation.mutate()}>Delete</Button>
      </div>
      <Card>
        <h2 className="mb-2 text-lg">Summary</h2>
        <p className="text-slate-300">{doc.summary ?? 'No summary'}</p>
      </Card>
      <div className="grid gap-3 md:grid-cols-2">
        <Card>
          <h3 className="mb-2">Key points</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm">{(doc.key_points ?? []).map((point) => <li key={point}>{point}</li>)}</ul>
        </Card>
        <Card>
          <h3 className="mb-2">Action items</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm">{(doc.action_items ?? []).map((item) => <li key={item}>{item}</li>)}</ul>
        </Card>
      </div>
      <Card>
        <h3 className="mb-2">Tags</h3>
        <div className="flex flex-wrap gap-2">{[...doc.ai_tags, ...doc.user_tags].map((tag) => <span className="rounded bg-slate-700 px-2 py-1 text-xs" key={tag}>{tag}</span>)}</div>
      </Card>
      <Card>
        <h3 className="mb-2">Entities</h3>
        <pre className="overflow-auto text-xs text-slate-300">{JSON.stringify(doc.entities ?? {}, null, 2)}</pre>
      </Card>
      <Card>
        <h3 className="mb-2">Similar documents</h3>
        <ul className="space-y-1 text-sm text-slate-300">
          {similarQuery.data?.results.map((row) => <li key={row.document.id}>{row.document.filename} ({row.similarity_score.toFixed(2)})</li>)}
        </ul>
      </Card>
    </div>
  );
}
