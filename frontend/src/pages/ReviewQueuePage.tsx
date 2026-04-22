import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQueueStats, useReviewDocument, useReviewQueue } from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { useUIStore } from '@/store/uiStore';
import type { Document } from '@/types/api';

function confidenceColor(confidence: number | null | undefined) {
  if (confidence == null || confidence < 0.5) return 'bg-red-500';
  if (confidence < 0.75) return 'bg-amber-500';
  return 'bg-emerald-500';
}

function normalizeTags(raw: string) {
  return raw
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function ReviewQueueCard({ document }: { document: Document }) {
  const pushToast = useUIStore((s) => s.pushToast);
  const review = useReviewDocument();
  const [editing, setEditing] = useState(false);
  const [summary, setSummary] = useState(document.override_summary ?? document.summary ?? '');
  const [tagsInput, setTagsInput] = useState((document.override_tags ?? document.ai_tags ?? []).join(', '));

  const confidence = document.ai_confidence ?? 0;

  const submitAction = async (action: 'approve' | 'reject' | 'edit') => {
    try {
      await review.mutateAsync({
        id: document.id,
        action,
        overrideSummary: action === 'edit' ? summary : undefined,
        overrideTags: action === 'edit' ? normalizeTags(tagsInput) : undefined,
      });
      pushToast(`Document ${action}d`);
      if (action === 'edit') {
        setEditing(false);
      }
    } catch {
      pushToast('Review update failed');
    }
  };

  return (
    <Card>
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="font-medium">{document.filename}</div>
            <span className="rounded bg-slate-800 px-2 py-0.5 text-xs uppercase text-slate-300">{document.file_type}</span>
          </div>
          <div className="text-right text-xs text-slate-400">
            Confidence {(confidence * 100).toFixed(0)}%
          </div>
        </div>

        <div className="h-2 w-full overflow-hidden rounded bg-slate-800">
          <div className={`h-full ${confidenceColor(document.ai_confidence)}`} style={{ width: `${Math.max(5, confidence * 100)}%` }} />
        </div>

        <p className="text-sm text-slate-200">{document.summary || 'No AI summary available.'}</p>

        <div className="flex flex-wrap gap-2">
          {(document.ai_tags ?? []).map((tag) => (
            <span key={tag} className="rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-300">#{tag}</span>
          ))}
        </div>

        {editing && (
          <div className="space-y-2 rounded border border-slate-700 p-3">
            <textarea
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              rows={4}
              className="w-full rounded border border-slate-700 bg-slate-950 p-2 text-sm"
            />
            <input
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              className="w-full rounded border border-slate-700 bg-slate-950 p-2 text-sm"
              placeholder="tag1, tag2"
            />
            <Button className="bg-slate-600 hover:bg-slate-500" onClick={() => void submitAction('edit')} disabled={review.isPending}>
              Save edits
            </Button>
          </div>
        )}

        <div className="flex gap-2">
          <Button className="bg-emerald-600 hover:bg-emerald-500" onClick={() => void submitAction('approve')} disabled={review.isPending}>
            Approve
          </Button>
          <Button className="bg-red-600 hover:bg-red-500" onClick={() => void submitAction('reject')} disabled={review.isPending}>
            Reject
          </Button>
          <Button className="bg-transparent ring-1 ring-slate-600 hover:bg-slate-800" onClick={() => setEditing((v) => !v)}>
            Edit
          </Button>
        </div>
      </div>
    </Card>
  );
}

export function ReviewQueuePage() {
  const queue = useReviewQueue();
  const stats = useQueueStats();

  const sorted = useMemo(
    () => [...(queue.data ?? [])].sort((a, b) => (a.ai_confidence ?? 0) - (b.ai_confidence ?? 0)),
    [queue.data],
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold">Review queue</h1>
          <span className="rounded-full bg-red-600/20 px-2 py-0.5 text-xs text-red-300">
            {stats.data?.pending_review_count ?? 0}
          </span>
        </div>
        <Link className="text-sm text-blue-300 hover:text-blue-200" to="/queue">Back to queue</Link>
      </div>

      {queue.isLoading && <LoadingState label="Loading review queue..." />}
      {queue.isError && <ErrorState message="Failed to load review queue" />}
      {queue.isSuccess && sorted.length === 0 && <EmptyState label="All AI outputs are approved" />}

      <div className="space-y-3">
        {sorted.map((doc) => (
          <ReviewQueueCard key={doc.id} document={doc} />
        ))}
      </div>
    </div>
  );
}
