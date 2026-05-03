import { useMemo } from 'react';
import { getErrorDetail } from '@/services/api';
import { useCreateCustomerPortalSession, usePlans, useSubscription } from '@/hooks/useApi';
import { useUIStore } from '@/store/uiStore';

export function SettingsBillingPage() {
  const subscription = useSubscription();
  const plans = usePlans();
  const portal = useCreateCustomerPortalSession();
  const pushToast = useUIStore((s) => s.pushToast);

  const billingConfigured = useMemo(
    () => (plans.data ?? []).some((plan) => plan.slug !== 'free' && plan.price_monthly_cents > 0 && plan.features?.billing_configured !== false),
    [plans.data],
  );

  if (subscription.isLoading || plans.isLoading) return <div>Loading billing settings…</div>;
  if (subscription.isError || plans.isError) return <div>Unable to load billing settings.</div>;

  return (
    <section className="space-y-4" aria-label="Billing settings">
      <h2 className="text-xl font-semibold">Billing & subscription</h2>
      <div className="rounded border border-slate-800 bg-slate-900 p-4 text-sm">
        <div>Current plan: <span className="font-semibold uppercase">{subscription.data?.plan.slug ?? 'free'}</span></div>
        {subscription.data && (subscription.data.status === 'active' || subscription.data.status === 'trialing') ? (
          <>
            <div>Status: <span className="font-medium capitalize">{subscription.data.status}</span></div>
            <div>Period end: {subscription.data.current_period_end ?? 'Not available'}</div>
          </>
        ) : (
          <div className="text-slate-300">No active subscription yet. You are currently on the free plan.</div>
        )}
      </div>

      <button
        disabled={!billingConfigured || portal.isPending}
        className="rounded bg-slate-700 px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50"
        onClick={async () => {
          try {
            const session = await portal.mutateAsync();
            window.location.href = session.portal_url;
          } catch (error) {
            pushToast(getErrorDetail(error), 'error');
          }
        }}
      >
        {billingConfigured ? 'Open billing portal' : 'Billing unavailable'}
      </button>
      {!billingConfigured && <p className="text-sm text-slate-300">Billing is not configured yet. Please try again later.</p>}
    </section>
  );
}
