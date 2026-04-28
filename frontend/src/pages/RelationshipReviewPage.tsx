import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useConfirmRelationshipReview, useDismissRelationshipReview, useRelationshipReviews } from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';

export function RelationshipReviewPage() {
  const [status, setStatus] = useState<'pending' | 'confirmed' | 'dismissed'>('pending');
  const reviews = useRelationshipReviews(status);
  const confirm = useConfirmRelationshipReview();
  const dismiss = useDismissRelationshipReview();

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Relationship review</h1>
      <Card>
        <label className="text-sm">
          <span className="mb-1 block text-slate-400">Status</span>
          <select className="rounded border border-slate-700 bg-slate-950 px-2 py-2" value={status} onChange={(e) => setStatus(e.target.value as typeof status)}>
            <option value="pending">Pending</option>
            <option value="confirmed">Confirmed</option>
            <option value="dismissed">Dismissed</option>
          </select>
        </label>
      </Card>

      {reviews.isLoading && <LoadingState label="Loading relationship reviews..." />}
      {reviews.isError && <ErrorState message="Failed to load relationship reviews" />}
      {reviews.isSuccess && (reviews.data?.length ?? 0) === 0 && <EmptyState label="No relationship reviews for this status." />}

      <div className="space-y-2">
        {(reviews.data ?? []).map((item) => (
          <Card key={item.id}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="space-y-1 text-sm">
                <div className="font-medium">{item.relationship_type} ({item.confidence != null ? `${Math.round(item.confidence * 100)}%` : 'n/a'})</div>
                <div className="text-slate-300">Source: <Link to={`/documents/${item.source_document_id}`} className="text-blue-300 hover:text-blue-200">{item.source_document_id}</Link></div>
                <div className="text-slate-300">Target: <Link to={`/documents/${item.target_document_id}`} className="text-blue-300 hover:text-blue-200">{item.target_document_id}</Link></div>
              </div>
              <div className="flex gap-2">
                <Button className="bg-emerald-700 hover:bg-emerald-600" disabled={item.status !== 'pending' || confirm.isPending} onClick={() => confirm.mutate(item.id)}>Confirm</Button>
                <Button className="bg-slate-700 hover:bg-slate-600" disabled={item.status !== 'pending' || dismiss.isPending} onClick={() => dismiss.mutate(item.id)}>Dismiss</Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
