import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useBulkDismissReviewItems, useBulkResolveReviewItems, useDismissReviewItem, useResolveReviewItem, useReviewItems } from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { useUIStore } from '@/store/uiStore';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { PaginationControls } from '@/components/ui/PaginationControls';
import { useRoleAccess } from '@/hooks/useRoleAccess';

export function ReviewQueuePage() {
  const [status, setStatus] = useState<'open' | 'resolved' | 'dismissed'>('open');
  const [reviewType, setReviewType] = useState('all');
  const [priority, setPriority] = useState('all');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [page, setPage] = useState(0);
  const [bulkAction, setBulkAction] = useState<'resolve' | 'dismiss' | null>(null);
  const pushToast = useUIStore((s) => s.pushToast);
  const { canMutate } = useRoleAccess();

  const items = useReviewItems(status, page, 20);
  const resolveItem = useResolveReviewItem();
  const dismissItem = useDismissReviewItem();
  const bulkResolve = useBulkResolveReviewItems();
  const bulkDismiss = useBulkDismissReviewItems();

  const filtered = useMemo(() => (items.data?.items ?? []).filter((item) => (reviewType === 'all' || item.review_type === reviewType) && (priority === 'all' || String(item.payload?.priority ?? 'normal') === priority)), [items.data, priority, reviewType]);

  return <div className="space-y-4"><h1 className="text-xl font-semibold">Review queue dashboard</h1>
    <Card><div className="flex flex-wrap items-end gap-3"><label className="text-sm"><span className="mb-1 block text-slate-400">Status</span><select className="rounded border border-slate-700 bg-slate-950 px-2 py-2" value={status} onChange={(e) => { setStatus(e.target.value as typeof status); setPage(0); }}><option value="open">Open</option><option value="resolved">Resolved</option><option value="dismissed">Dismissed</option></select></label><label className="text-sm"><span className="mb-1 block text-slate-400">Review type</span><input value={reviewType} onChange={(e) => setReviewType(e.target.value)} className="rounded border border-slate-700 bg-slate-950 px-2 py-2" /></label><label className="text-sm"><span className="mb-1 block text-slate-400">Priority</span><input value={priority} onChange={(e) => setPriority(e.target.value)} className="rounded border border-slate-700 bg-slate-950 px-2 py-2" /></label><Button title={!canMutate ? 'Your role does not allow this action' : undefined} onClick={() => setBulkAction('resolve')} disabled={!canMutate || selectedIds.length === 0}>Bulk resolve</Button><Button title={!canMutate ? 'Your role does not allow this action' : undefined} className="bg-slate-700 hover:bg-slate-600" onClick={() => setBulkAction('dismiss')} disabled={!canMutate || selectedIds.length === 0}>Bulk dismiss</Button></div></Card>
    <ConfirmModal open={bulkAction !== null} title="Confirm bulk review action" description={`${bulkAction} ${selectedIds.length} selected item(s)?`} onCancel={() => setBulkAction(null)} onConfirm={async () => { try { if (bulkAction === 'resolve') await bulkResolve.mutateAsync({ ids: selectedIds }); else await bulkDismiss.mutateAsync({ ids: selectedIds }); pushToast(`Bulk ${bulkAction} complete`); setSelectedIds([]); } catch (e) { pushToast((e as Error).message, 'error'); } setBulkAction(null); }} />
    {items.isLoading && <LoadingState label="Loading review items..." />}
    {items.isError && <ErrorState message="Failed to load review items" />}
    {items.isSuccess && filtered.length === 0 && <EmptyState label="No review items for current filters." />}
    <div className="space-y-2">{filtered.map((item) => <Card key={item.id}><div className="flex flex-wrap items-start justify-between gap-2"><div className="space-y-1"><label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => setSelectedIds((prev) => (prev.includes(item.id) ? prev.filter((curr) => curr !== item.id) : [...prev, item.id]))} /><span className="font-medium">{item.review_type}</span></label><div className="text-xs text-slate-400">Status: {item.status}</div><div className="text-sm text-slate-200">{item.reason || 'No reason provided.'}</div><Link to={`/documents/${item.document_id}`} className="text-sm text-blue-300 hover:text-blue-200">View document</Link></div><div className="flex gap-2"><Button title={!canMutate ? 'Your role does not allow this action' : undefined} className="bg-emerald-700 hover:bg-emerald-600" disabled={!canMutate || item.status !== 'open'} onClick={() => resolveItem.mutate({ id: item.id })}>Resolve</Button><Button title={!canMutate ? 'Your role does not allow this action' : undefined} className="bg-slate-700 hover:bg-slate-600" disabled={!canMutate || item.status !== 'open'} onClick={() => dismissItem.mutate({ id: item.id })}>Dismiss</Button></div></div></Card>)}</div>
    <PaginationControls page={page} total={items.data ? Math.max(1, Math.ceil(items.data.total_count / items.data.limit)) : undefined} hasNext={Boolean(items.data?.items?.length)} onPrev={() => setPage((p) => Math.max(0, p - 1))} onNext={() => setPage((p) => p + 1)} />
  </div>;
}
