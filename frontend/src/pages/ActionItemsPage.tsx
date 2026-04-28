import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  useActionItems,
  useBulkCompleteActionItems,
  useBulkDismissActionItems,
  useCompleteActionItem,
  useDismissActionItem,
} from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';

export function ActionItemsPage() {
  const [state, setState] = useState<'open' | 'completed' | 'dismissed' | ''>('open');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const items = useActionItems(state);
  const completeItem = useCompleteActionItem();
  const dismissItem = useDismissActionItem();
  const bulkComplete = useBulkCompleteActionItems();
  const bulkDismiss = useBulkDismissActionItems();

  const toggleSelection = (id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((curr) => curr !== id) : [...prev, id]));
  };

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Action item dashboard</h1>
      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-sm">
            <span className="mb-1 block text-slate-400">Status</span>
            <select className="rounded border border-slate-700 bg-slate-950 px-2 py-2" value={state} onChange={(e) => setState(e.target.value as typeof state)}>
              <option value="">All</option>
              <option value="open">Open</option>
              <option value="completed">Completed</option>
              <option value="dismissed">Dismissed</option>
            </select>
          </label>
          <Button onClick={() => bulkComplete.mutate({ ids: selectedIds })} disabled={selectedIds.length === 0 || bulkComplete.isPending}>Bulk complete</Button>
          <Button className="bg-slate-700 hover:bg-slate-600" onClick={() => bulkDismiss.mutate({ ids: selectedIds })} disabled={selectedIds.length === 0 || bulkDismiss.isPending}>Bulk dismiss</Button>
        </div>
      </Card>

      {items.isLoading && <LoadingState label="Loading action items..." />}
      {items.isError && <ErrorState message="Failed to load action items" />}
      {items.isSuccess && (items.data?.length ?? 0) === 0 && <EmptyState label="No action items available." />}

      <div className="space-y-2">
        {(items.data ?? []).map((item) => (
          <Card key={item.id}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="space-y-1">
                <label className="inline-flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => toggleSelection(item.id)} />
                  <span className="font-medium">{item.content}</span>
                </label>
                <div className="text-xs text-slate-400">State: {item.state} · Source: {item.source}</div>
                <Link to={`/documents/${item.document_id}`} className="text-sm text-blue-300 hover:text-blue-200">View document</Link>
              </div>
              <div className="flex gap-2">
                <Button className="bg-emerald-700 hover:bg-emerald-600" disabled={item.state !== 'open'} onClick={() => completeItem.mutate(item.id)}>Complete</Button>
                <Button className="bg-slate-700 hover:bg-slate-600" disabled={item.state !== 'open'} onClick={() => dismissItem.mutate(item.id)}>Dismiss</Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
