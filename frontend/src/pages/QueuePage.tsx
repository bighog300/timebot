import { useMutation } from '@tanstack/react-query';
import { useQueueItems, useQueueStats } from '@/hooks/useApi';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export function QueuePage() {
  const stats = useQueueStats();
  const items = useQueueItems();
  const retry = useMutation({ mutationFn: api.retryFailedQueue });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Queue</h1>
        <Button onClick={() => retry.mutate()}>Retry Failed</Button>
      </div>
      <div className="grid gap-3 md:grid-cols-5">
        {Object.entries(stats.data ?? {}).filter(([k]) => ['queued', 'processing', 'completed', 'failed', 'total'].includes(k)).map(([k, v]) => (
          <Card key={k}><div className="text-xs uppercase text-slate-400">{k}</div><div className="text-2xl">{String(v)}</div></Card>
        ))}
      </div>
      <Card>
        <h3 className="mb-2">Items</h3>
        <ul className="space-y-1 text-sm">{items.data?.map((it) => <li key={it.id}>{it.task_type} • {it.status} • attempts {it.attempts}/{it.max_attempts}</li>)}</ul>
      </Card>
    </div>
  );
}
