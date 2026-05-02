import { Card } from '@/components/ui/Card';
import { usePlans, useSubscription } from '@/hooks/useApi';

export function PricingPage() {
  const plans = usePlans();
  const subscription = useSubscription();

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Plans & Pricing</h1>
      <p className="text-sm text-slate-300">Billing checkout is coming soon. You can review plan limits and features now.</p>
      <div className="text-sm">Current plan: <span className="font-semibold uppercase">{subscription.data?.plan.slug ?? 'free'}</span></div>
      <div className="grid gap-3 md:grid-cols-3">
        {(plans.data || []).map((plan) => (
          <Card key={plan.slug}>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">{plan.name}</h2>
              {plan.is_current ? <span className="rounded bg-emerald-700 px-2 py-0.5 text-xs">Current</span> : null}
            </div>
            <div className="mt-2 text-sm">${(plan.price_monthly_cents / 100).toFixed(2)}/month</div>
            <ul className="mt-3 space-y-1 text-xs text-slate-300">
              {Object.entries(plan.limits).slice(0, 4).map(([k, v]) => <li key={k}>{k}: {v ?? 'Unlimited'}</li>)}
            </ul>
            <button className="mt-3 rounded bg-indigo-700 px-3 py-2 text-sm">
              {plan.is_current ? 'Current plan' : 'Upgrade (Billing coming soon)'}
            </button>
          </Card>
        ))}
      </div>
    </div>
  );
}
