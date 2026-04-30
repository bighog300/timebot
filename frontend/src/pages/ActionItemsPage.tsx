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
import { PaginationControls } from '@/components/ui/PaginationControls';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { useRoleAccess } from '@/hooks/useRoleAccess';
import { useUIStore } from '@/store/uiStore';

export function ActionItemsPage() {
  const [state, setState] = useState<'open' | 'completed' | 'dismissed' | ''>('open');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [page, setPage] = useState(0);
  const [modal, setModal] = useState<null | 'complete' | 'dismiss'>(null);
  const items = useActionItems(state, page, 20);
  const completeItem = useCompleteActionItem();
  const dismissItem = useDismissActionItem();
  const bulkComplete = useBulkCompleteActionItems();
  const bulkDismiss = useBulkDismissActionItems();
  const { canMutate } = useRoleAccess();
  const pushToast = useUIStore((s) => s.pushToast);

  const toggleSelection = (id: string) => setSelectedIds((prev) => (prev.includes(id) ? prev.filter((curr) => curr !== id) : [...prev, id]));
  const disabledReason = canMutate ? undefined : 'Your role does not allow this action';

  return <div className="space-y-4">
    <h1 className="text-xl font-semibold">Action item dashboard</h1>
    <Card><div className="flex flex-wrap items-end gap-3">
      <label className="text-sm"><span className="mb-1 block text-slate-400">Status</span>
        <select className="rounded border border-slate-700 bg-slate-950 px-2 py-2" value={state} onChange={(e) => { setState(e.target.value as typeof state); setPage(0); }}>
          <option value="">All</option><option value="open">Open</option><option value="completed">Completed</option><option value="dismissed">Dismissed</option>
        </select>
      </label>
      <Button title={disabledReason} onClick={() => setModal('complete')} disabled={!canMutate || selectedIds.length === 0 || bulkComplete.isPending}>Bulk complete</Button>
      <Button title={disabledReason} className="bg-slate-700 hover:bg-slate-600" onClick={() => setModal('dismiss')} disabled={!canMutate || selectedIds.length === 0 || bulkDismiss.isPending}>Bulk dismiss</Button>
    </div></Card>
    <ConfirmModal open={modal !== null} title="Confirm bulk action" description={`${modal === 'complete' ? 'Complete' : 'Dismiss'} ${selectedIds.length} selected item(s)?`} onCancel={() => setModal(null)} onConfirm={async () => {
      try { if (modal === 'complete') await bulkComplete.mutateAsync({ ids: selectedIds }); else await bulkDismiss.mutateAsync({ ids: selectedIds }); pushToast('Bulk update complete'); setSelectedIds([]); } catch (e) { pushToast((e as Error).message, 'error'); }
      setModal(null);
    }} />

    {items.isLoading && <LoadingState label="Loading action items..." />}
    {items.isError && <ErrorState message="Failed to load action items" />}
    {items.isSuccess && (items.data?.items?.length ?? 0) === 0 && <EmptyState label="No action items" />}

    <div className="space-y-2">{(items.data?.items ?? []).map((item) => <Card key={item.id}><div className="flex flex-wrap items-start justify-between gap-2"><div className="space-y-1"><label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => toggleSelection(item.id)} /><span className="font-medium">{item.content}</span></label><div className="text-xs text-slate-400">State: {item.state} · Source: {item.source}</div><Link to={`/documents/${item.document_id}`} className="text-sm text-blue-300 hover:text-blue-200">View document</Link></div><div className="flex gap-2"><Button title={disabledReason} className="bg-emerald-700 hover:bg-emerald-600" disabled={!canMutate || item.state !== 'open'} onClick={async () => { try { await completeItem.mutateAsync(item.id); pushToast('Action item completed'); } catch (e) { pushToast((e as Error).message, 'error'); } }}>Complete</Button><Button title={disabledReason} className="bg-slate-700 hover:bg-slate-600" disabled={!canMutate || item.state !== 'open'} onClick={async () => { try { await dismissItem.mutateAsync(item.id); pushToast('Action item dismissed'); } catch (e) { pushToast((e as Error).message, 'error'); } }}>Dismiss</Button></div></div></Card>)}</div>
    <PaginationControls page={page} total={items.data ? Math.max(1, Math.ceil(items.data.total_count / items.data.limit)) : undefined} hasNext={Boolean(items.data?.items?.length)} onPrev={() => setPage((p) => Math.max(0, p - 1))} onNext={() => setPage((p) => p + 1)} />
  </div>;
}
