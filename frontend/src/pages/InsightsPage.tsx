import { useInsightsOverview } from '@/hooks/useApi';
import { Card } from '@/components/ui/Card';

export function InsightsPage() {
  const { data } = useInsightsOverview();
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Insights</h1>
      <Card><h3 className="mb-2">Action Items</h3><pre className="text-xs">{JSON.stringify(data?.action_item_summary ?? {}, null, 2)}</pre></Card>
      <Card><h3 className="mb-2">Category distribution</h3><pre className="text-xs">{JSON.stringify(data?.category_distribution ?? [], null, 2)}</pre></Card>
      <Card><h3 className="mb-2">Recent activity</h3><pre className="text-xs">{JSON.stringify(data?.recent_activity ?? [], null, 2)}</pre></Card>
    </div>
  );
}
