import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Card } from '@/components/ui/Card';

export function TimelinePage() {
  const { data } = useQuery({ queryKey: ['timeline'], queryFn: api.getTimeline });

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Timeline</h1>
      {(data?.buckets ?? []).map((bucket) => (
        <Card key={bucket.period}>
          <div className="mb-2 flex items-center justify-between">
            <strong>{bucket.period}</strong>
            <span className="text-xs text-slate-400">{bucket.count} events</span>
          </div>
          <ul className="space-y-1 text-sm text-slate-300">
            {bucket.events.slice(0, 5).map((event, i) => (
              <li key={`${bucket.period}-${i}`}>{String(event.filename ?? event.type)}</li>
            ))}
          </ul>
        </Card>
      ))}
    </div>
  );
}
