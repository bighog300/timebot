import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { useActionItemMetrics, useCreateCheckoutSession, useReviewMetrics, useUsage } from '@/hooks/useApi';
import { useUIStore } from '@/store/uiStore';

export function DashboardPage() {
  const { pushToast } = useUIStore();
  const reviewMetrics = useReviewMetrics();
  const actionMetrics = useActionItemMetrics();
  const usage = useUsage();
  const checkout = useCreateCheckoutSession();

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Dashboard</h1>

      {(reviewMetrics.isLoading || actionMetrics.isLoading) && <LoadingState label="Loading dashboard metrics..." />}
      {(reviewMetrics.isError || actionMetrics.isError) && <ErrorState message="Failed to load metrics." />}

      {reviewMetrics.data && actionMetrics.data && (
        <>
          <div className="grid gap-3 md:grid-cols-4">
            <Card><div className="text-xs text-slate-400">Open reviews</div><div className="text-2xl font-semibold">{reviewMetrics.data.open_review_count}</div></Card>
            <Card><div className="text-xs text-slate-400">Resolved reviews</div><div className="text-2xl font-semibold">{reviewMetrics.data.resolved_review_count}</div></Card>
            <Card><div className="text-xs text-slate-400">Open action items</div><div className="text-2xl font-semibold">{actionMetrics.data.open_count}</div></Card>
            <Card><div className="text-xs text-slate-400">Completion rate</div><div className="text-2xl font-semibold">{(actionMetrics.data.completion_rate * 100).toFixed(0)}%</div></Card>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <Card>
              <h2 className="mb-2 text-sm font-semibold">Open review breakdown</h2>
              {Object.keys(reviewMetrics.data.open_by_type).length === 0 ? (
                <EmptyState label="No open review items." />
              ) : (
                <ul className="space-y-1 text-sm">
                  {Object.entries(reviewMetrics.data.open_by_type).map(([key, value]) => (
                    <li key={key} className="flex justify-between"><span>{key}</span><span>{value}</span></li>
                  ))}
                </ul>
              )}
            </Card>
            <Card>
              <h2 className="mb-2 text-sm font-semibold">Priority breakdown</h2>
              {Object.keys(reviewMetrics.data.open_by_priority).length === 0 ? (
                <EmptyState label="No priority data." />
              ) : (
                <ul className="space-y-1 text-sm">
                  {Object.entries(reviewMetrics.data.open_by_priority).map(([key, value]) => (
                    <li key={key} className="flex justify-between"><span>{key}</span><span>{value}</span></li>
                  ))}
                </ul>
              )}
            </Card>
            <Card>
              <h2 className="mb-2 text-sm font-semibold">Plan & Usage</h2>
              <div className="space-y-1 text-sm">
                <div>Current plan: <span className="font-semibold uppercase">{usage.data?.plan || 'free'}</span></div>
                <div>Documents: {usage.data?.documents?.used ?? 0} / {usage.data?.documents?.limit ?? '∞'}</div>
                <div>Reports: {usage.data?.reports?.used ?? 0} / {usage.data?.reports?.limit ?? '∞'}</div>
                <div>Chat messages: {usage.data?.chat_messages?.used ?? 0} / {usage.data?.chat_messages?.limit ?? '∞'}</div>
              </div>
              <button className="mt-3 rounded bg-indigo-700 px-3 py-2 text-sm" onClick={async () => {
                try {
                  const result = await checkout.mutateAsync('pro');
                  pushToast(`Upgrade started: ${result.plan}`);
                } catch {
                  pushToast('Upgrade currently unavailable', 'error');
                }
              }}>Upgrade to Pro</button>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
