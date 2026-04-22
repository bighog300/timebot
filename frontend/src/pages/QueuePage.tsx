import { useMutation } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useQueueItems, useQueueStats } from '@/hooks/useApi';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { useUIStore } from '@/store/uiStore';

export function QueuePage() {
  const stats = useQueueStats();
  const items = useQueueItems();
  const pushToast = useUIStore((s) => s.pushToast);
  const retry = useMutation({
    mutationFn: api.retryFailedQueue,
    onSuccess: (res) => pushToast(res.message || 'Retry queued'),
    onError: () => pushToast('Retry failed'),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Queue</h1>
        <div className="flex items-center gap-2">
          <Link to="/review" className="text-sm text-blue-300 hover:text-blue-200">Go to review queue →</Link>
          <Button onClick={() => retry.mutate()}>Retry Failed</Button>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-5">
        {stats.isLoading && <LoadingState label="Loading queue stats..." />}
        {stats.isError && <ErrorState message="Failed to load queue stats" />}
        {Object.entries(stats.data ?? {}).filter(([k]) => ['queued', 'processing', 'completed', 'failed', 'total'].includes(k)).map(([k, v]) => (
          <Card key={k}><div className="text-xs uppercase text-slate-400">{k}</div><div className="text-2xl">{String(v)}</div></Card>
        ))}
        {stats.data && (
          <Card>
            <div className="text-xs uppercase text-slate-400">pending review</div>
            <div className="text-2xl">{stats.data.pending_review_count}</div>
          </Card>
        )}
      </div>
      <Card>
        <h3 className="mb-2">Items</h3>
        {items.isLoading && <LoadingState label="Loading queue items..." />}
        {items.isError && <ErrorState message="Failed to load queue items" />}
        {items.isSuccess && (items.data?.length ?? 0) === 0 && <EmptyState label="No queued items." />}
        <ul className="space-y-1 text-sm">{items.data?.map((it) => <li key={it.id}>{it.task_type} • {it.status} • attempts {it.attempts}/{it.max_attempts}</li>)}</ul>
      </Card>
    </div>
  );
}
