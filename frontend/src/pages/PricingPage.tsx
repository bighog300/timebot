import { Card } from '@/components/ui/Card';
import axios from 'axios';
import { useCreateCheckoutSession, useCreateCustomerPortalSession, usePlans, useSubscription } from '@/hooks/useApi';
import { useUIStore } from '@/store/uiStore';

export function PricingPage() {
  const { pushToast } = useUIStore();
  const plans = usePlans();
  const subscription = useSubscription();
  const checkout = useCreateCheckoutSession();
  const portal = useCreateCustomerPortalSession();
  const billingConfigured = (plans.data ?? []).some((plan) => plan.slug !== 'free' && plan.price_monthly_cents > 0 && plan.features?.billing_configured !== false);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Plans & Pricing</h1>
      <div className="text-sm">Current plan: <span className="font-semibold uppercase">{subscription.data?.plan.slug ?? 'free'}</span></div>
      <button disabled={!billingConfigured} className="rounded bg-slate-700 px-3 py-2 text-sm disabled:opacity-50" onClick={async () => {
        try {
          const result = await portal.mutateAsync();
          window.location.href = result.portal_url;
        } catch {
          pushToast('Unable to open billing portal', 'error');
        }
      }}>Manage billing</button>
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
            <button disabled={plan.is_current || checkout.isPending || (!billingConfigured && plan.slug !== 'free')} className="mt-3 rounded bg-indigo-700 px-3 py-2 text-sm disabled:opacity-50" onClick={async () => {
              try {
                const result = await checkout.mutateAsync(plan.slug);
                window.location.href = result.checkout_url;
              } catch (error) {
                if (axios.isAxiosError(error)) {
                  const detail = error.response?.data?.detail;
                  if (detail?.code === 'billing_not_configured') {
                    pushToast(detail.message, 'error');
                    return;
                  }
                  if (typeof detail === 'string') {
                    pushToast(detail, 'error');
                    return;
                  }
                }
                pushToast('Unable to start checkout', 'error');
              }
            }}>
              {plan.is_current ? 'Current plan' : (!billingConfigured && plan.slug !== 'free' ? 'Billing not configured' : 'Choose plan')}
            </button>
          </Card>
        ))}
      </div>
    </div>
  );
}
