import { Card } from '@/components/ui/Card';
import { getErrorDetail } from '@/services/api';
import { useBillingStatus, useCreateCheckoutSession, usePlans, useSubscription, useUsage } from '@/hooks/useApi';
import { useUIStore } from '@/store/uiStore';

const lockedFeatures = [
  'Specialist assistants',
  'Custom prompts',
  'Higher message limits',
  'Report export',
  'System intelligence/legal web references',
  'Team workspaces/business features',
];

export function PricingPage() {
  const plans = usePlans();
  const subscription = useSubscription();
  const usage = useUsage();
  const billingStatus = useBillingStatus();
  const checkout = useCreateCheckoutSession();
  const pushToast = useUIStore((s) => s.pushToast);

  const currentPlan = subscription.data?.plan.slug ?? 'free';
  const sorted = (plans.data ?? []).sort((a, b) => a.price_monthly_cents - b.price_monthly_cents);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Plans & Pricing</h1>
      <div className="text-sm">Current plan: <span className="font-semibold uppercase">{currentPlan}</span></div>

      <section className="rounded border border-slate-800 bg-slate-900 p-4 text-sm" aria-label="Billing status">
        <h2 className="font-semibold">Account billing status</h2>
        <div className="mt-2">subscription_status: {subscription.data?.status ?? 'n/a'}</div>
        <div>plan_started_at: {subscription.data?.current_period_start ?? 'n/a'}</div>
        <div>plan_expires_at: {subscription.data?.current_period_end ?? 'n/a'}</div>
      </section>

      <section className="rounded border border-slate-800 bg-slate-900 p-4 text-sm" aria-label="Usage meters">
        <h2 className="font-semibold">Usage this month</h2>
        <div className="mt-2">Messages: {usage.data?.chat_messages?.used ?? 0} / {usage.data?.chat_messages?.limit ?? 'Unlimited'}</div>
        <div>Reports: {usage.data?.reports?.used ?? 0} / {usage.data?.reports?.limit ?? 'Unlimited'}</div>
      </section>

      <div className="grid gap-3 md:grid-cols-3">
        {sorted.map((plan) => (
          <Card key={plan.slug}>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">{plan.name}</h2>
              {(plan.is_current || plan.slug === currentPlan) ? <span className="rounded bg-emerald-700 px-2 py-0.5 text-xs">Current</span> : null}
            </div>
            <div className="mt-2 text-sm">${(plan.price_monthly_cents / 100).toFixed(2)}/month</div>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-slate-300">
              {lockedFeatures.map((feature) => <li key={`${plan.slug}-${feature}`}>{feature}</li>)}
            </ul>
            <button className="mt-3 rounded bg-indigo-700 px-3 py-2 text-sm disabled:opacity-50" disabled={plan.slug === currentPlan || checkout.isPending}
              onClick={async () => {
                if (plan.slug === 'free') return;
                if (!billingStatus.data?.enabled) return;
                try {
                  const session = await checkout.mutateAsync(plan.slug);
                  window.location.href = session.checkout_url;
                } catch (error) { pushToast(getErrorDetail(error), 'error'); }
              }}>
              {plan.slug === 'free' ? 'Current plan' : plan.slug === 'pro' ? 'Request upgrade' : 'Contact sales'}
            </button>
          </Card>
        ))}
      </div>
    </div>
  );
}
