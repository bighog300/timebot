import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useConfirmRelationshipReview, useDismissRelationshipReview, useRelationshipReviews } from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { useRoleAccess } from '@/hooks/useRoleAccess';
import { useUIStore } from '@/store/uiStore';

export function RelationshipReviewPage() {
  const [status, setStatus] = useState<'pending' | 'confirmed' | 'dismissed'>('pending');
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<'confirm' | 'dismiss' | null>(null);
  const reviews = useRelationshipReviews(status);
  const confirm = useConfirmRelationshipReview();
  const dismiss = useDismissRelationshipReview();
  const { canMutate } = useRoleAccess();
  const pushToast = useUIStore((s) => s.pushToast);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Relationship review</h1>
      <Card>
        <label className="block text-sm">
          <span className="mb-1 block text-slate-400">Status</span>
          <select className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-2 sm:w-auto" value={status} onChange={(e) => setStatus(e.target.value as typeof status)}>
            <option value="pending">Pending</option><option value="confirmed">Confirmed</option><option value="dismissed">Dismissed</option>
          </select>
        </label>
      </Card>
      <ConfirmModal open={Boolean(pendingId && pendingAction)} title="Confirm relationship action" description={`Are you sure you want to ${pendingAction} this relationship?`} onCancel={() => { setPendingId(null); setPendingAction(null); }} onConfirm={async () => {
        try { if (pendingAction === 'confirm' && pendingId) await confirm.mutateAsync(pendingId); if (pendingAction === 'dismiss' && pendingId) await dismiss.mutateAsync(pendingId); pushToast(`Relationship ${pendingAction}ed`); } catch (e) { pushToast((e as Error).message, 'error'); }
        setPendingId(null); setPendingAction(null);
      }} />

      {reviews.isLoading && <LoadingState label="Loading relationship reviews..." />}
      {reviews.isError && <ErrorState message="Failed to load relationship reviews" />}
      {reviews.isSuccess && (reviews.data?.length ?? 0) === 0 && <EmptyState label="No relationships to review" />}

      <div className="space-y-3">{(reviews.data ?? []).map((item) => (
        <Card key={item.id}><div className="grid gap-4 lg:grid-cols-[1fr_1fr_minmax(11rem,auto)]"><div className="min-w-0 space-y-2 text-sm"><div className="text-xs uppercase tracking-wide text-slate-400">Source document</div><Link to={`/documents/${item.source_document_id}`} className="break-words font-medium text-blue-300 hover:text-blue-200">{item.source_document_title || item.source_document_name || item.source_document_id}</Link><p className="break-words text-slate-500 text-xs">{item.source_document_id}</p><p className="break-words text-slate-300">{item.source_document_snippet || item.source_snippet || 'No source summary/snippet available.'}</p></div><div className="min-w-0 space-y-2 text-sm"><div className="text-xs uppercase tracking-wide text-slate-400">Target document</div><Link to={`/documents/${item.target_document_id}`} className="break-words font-medium text-blue-300 hover:text-blue-200">{item.target_document_title || item.target_document_name || item.target_document_id}</Link><p className="break-words text-slate-500 text-xs">{item.target_document_id}</p><p className="break-words text-slate-300">{item.target_document_snippet || item.target_snippet || 'No target summary/snippet available.'}</p></div><div className="min-w-0 space-y-2"><div className="break-words rounded bg-slate-800 px-2 py-1 text-xs">{item.relationship_type} · {item.confidence != null ? `${Math.round(item.confidence * 100)}% confidence` : 'n/a'}</div><div className="grid grid-cols-2 gap-2 lg:grid-cols-1"><Button title={!canMutate ? 'Your role does not allow this action' : undefined} className="min-h-10 w-full bg-emerald-700 hover:bg-emerald-600" disabled={!canMutate || item.status !== 'pending' || confirm.isPending} onClick={() => { setPendingId(item.id); setPendingAction('confirm'); }}>Confirm</Button><Button title={!canMutate ? 'Your role does not allow this action' : undefined} className="min-h-10 w-full bg-slate-700 hover:bg-slate-600" disabled={!canMutate || item.status !== 'pending' || dismiss.isPending} onClick={() => { setPendingId(item.id); setPendingAction('dismiss'); }}>Dismiss</Button></div></div></div></Card>
      ))}</div>
    </div>
  );
}
