import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  useBulkDismissReviewItems,
  useBulkResolveReviewItems,
  useDismissReviewItem,
  useResolveReviewItem,
  useReviewItems,
} from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { useUIStore } from '@/store/uiStore';

export function ReviewQueuePage() {
  const [status, setStatus] = useState<'open' | 'resolved' | 'dismissed'>('open');
  const [reviewType, setReviewType] = useState('all');
  const [priority, setPriority] = useState('all');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const pushToast = useUIStore((s) => s.pushToast);

  const items = useReviewItems(status);
  const resolveItem = useResolveReviewItem();
  const dismissItem = useDismissReviewItem();
  const bulkResolve = useBulkResolveReviewItems();
  const bulkDismiss = useBulkDismissReviewItems();

  const filtered = useMemo(() => {
    return (items.data ?? []).filter((item) => {
      const matchesType = reviewType === 'all' || item.review_type === reviewType;
      const itemPriority = String(item.payload?.priority ?? 'normal');
      const matchesPriority = priority === 'all' || itemPriority === priority;
      return matchesType && matchesPriority;
    });
  }, [items.data, priority, reviewType]);

  const toggleSelection = (id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((curr) => curr !== id) : [...prev, id]));
  };

  const onBulkResolve = async () => {
    if (selectedIds.length === 0) return;
    await bulkResolve.mutateAsync({ ids: selectedIds });
    pushToast(`Resolved ${selectedIds.length} review item(s)`);
    setSelectedIds([]);
  };

  const onBulkDismiss = async () => {
    if (selectedIds.length === 0) return;
    await bulkDismiss.mutateAsync({ ids: selectedIds });
    pushToast(`Dismissed ${selectedIds.length} review item(s)`);
    setSelectedIds([]);
  };

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Review queue dashboard</h1>

      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-sm">
            <span className="mb-1 block text-slate-400">Status</span>
            <select className="rounded border border-slate-700 bg-slate-950 px-2 py-2" value={status} onChange={(e) => setStatus(e.target.value as typeof status)}>
              <option value="open">Open</option>
              <option value="resolved">Resolved</option>
              <option value="dismissed">Dismissed</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-slate-400">Review type</span>
            <input
              value={reviewType}
              onChange={(e) => setReviewType(e.target.value)}
              className="rounded border border-slate-700 bg-slate-950 px-2 py-2"
              aria-label="Filter by review type"
              placeholder="all or type"
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-slate-400">Priority</span>
            <input
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="rounded border border-slate-700 bg-slate-950 px-2 py-2"
              aria-label="Filter by priority"
              placeholder="all/high/normal/low"
            />
          </label>
          <Button onClick={() => void onBulkResolve()} disabled={selectedIds.length === 0 || bulkResolve.isPending}>Bulk resolve</Button>
          <Button className="bg-slate-700 hover:bg-slate-600" onClick={() => void onBulkDismiss()} disabled={selectedIds.length === 0 || bulkDismiss.isPending}>Bulk dismiss</Button>
        </div>
      </Card>

      {items.isLoading && <LoadingState label="Loading review items..." />}
      {items.isError && <ErrorState message="Failed to load review items" />}
      {items.isSuccess && filtered.length === 0 && <EmptyState label="No review items for current filters." />}

      <div className="space-y-2">
        {filtered.map((item) => (
          <Card key={item.id}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="space-y-1">
                <label className="inline-flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => toggleSelection(item.id)} />
                  <span className="font-medium">{item.review_type}</span>
                </label>
                <div className="text-xs text-slate-400">Status: {item.status} · Priority: {String(item.payload?.priority ?? 'normal')}</div>
                <div className="text-sm text-slate-200">{item.reason || 'No reason provided.'}</div>
                <Link to={`/documents/${item.document_id}`} className="text-sm text-blue-300 hover:text-blue-200">View document</Link>
              </div>
              <div className="flex gap-2">
                <Button
                  className="bg-emerald-700 hover:bg-emerald-600"
                  disabled={item.status !== 'open' || resolveItem.isPending}
                  onClick={() => resolveItem.mutate({ id: item.id })}
                >
                  Resolve
                </Button>
                <Button
                  className="bg-slate-700 hover:bg-slate-600"
                  disabled={item.status !== 'open' || dismissItem.isPending}
                  onClick={() => dismissItem.mutate({ id: item.id })}
                >
                  Dismiss
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
