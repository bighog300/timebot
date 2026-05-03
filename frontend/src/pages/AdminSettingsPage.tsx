import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { useUIStore } from '@/store/uiStore';
import {
  useAdminAudit,
  useAdminSubscriptions,
  useAdminUsageSummary,
  useAdminUpdateUserPlan,
  useAdminUpdateUsageControls,
  useAdminCancelOrDowngrade,
  useAdminSystemStatus,
  useAdminLlmModels,
} from '@/hooks/useApi';

export function AdminSubscriptionsPage() {
  const { pushToast } = useUIStore();
  const subs = useAdminSubscriptions();
  const updatePlan = useAdminUpdateUserPlan();
  const updateUsage = useAdminUpdateUsageControls();
  const cancelOrDowngrade = useAdminCancelOrDowngrade();

  if (subs.isLoading) return <Card>Loading subscriptions...</Card>;
  if (subs.isError) return <Card>Failed loading subscriptions.</Card>;
  if (!subs.data?.length) return <Card>No subscriptions found.</Card>;

  return <Card><h2 className='mb-2 text-lg'>Subscription controls</h2>
    <div className='overflow-x-auto'>
      <table className='w-full min-w-[56rem] text-sm'>
        <thead><tr className='text-left'><th>Email</th><th>Plan</th><th>Status</th><th>Credits</th><th>Overrides</th><th>Actions</th></tr></thead>
        <tbody>
          {subs.data.map((s) => <tr key={s.subscription_id} className='border-t border-slate-800'>
            <td><Link className='underline' to={`/admin/users/${s.user_id}/usage`}>{s.email}</Link></td>
            <td>{s.plan_slug}</td><td>{s.status}</td>
            <td>{JSON.stringify(s.usage_credits)}</td><td>{JSON.stringify(s.limit_overrides)}</td>
            <td className='space-x-2'>
              <button onClick={async ()=>{ try { await updatePlan.mutateAsync({ userId: s.user_id, plan_slug: s.plan_slug === 'free' ? 'pro' : 'free' }); pushToast('Plan updated'); } catch(e){ pushToast((e as Error).message, 'error'); } }} className='rounded bg-slate-700 px-2 py-1'>Toggle plan</button>
              <button onClick={async ()=>{ try { await updateUsage.mutateAsync({ userId: s.user_id, usage_credits: { reports: 5 }, limit_overrides: { reports: 500 } }); pushToast('Usage controls updated'); } catch(e){ pushToast((e as Error).message, 'error'); } }} className='rounded bg-slate-700 px-2 py-1'>Grant usage</button>
              <button onClick={async ()=>{ try { await cancelOrDowngrade.mutateAsync({ userId: s.user_id, downgrade_to_plan_slug: 'free' }); pushToast('Subscription downgraded/canceled'); } catch(e){ pushToast((e as Error).message, 'error'); } }} className='rounded bg-amber-800 px-2 py-1'>Cancel/Downgrade</button>
            </td>
          </tr>)}
        </tbody>
      </table>
    </div>
  </Card>;
}

export function AdminUserUsagePage() {
  const { userId = '' } = useParams();
  const usage = useAdminUsageSummary(userId);
  if (usage.isLoading) return <Card>Loading usage summary...</Card>;
  if (usage.isError) return <Card>Failed loading usage summary.</Card>;
  return <Card><h2 className='text-lg mb-2'>User usage summary</h2><pre className='overflow-x-auto text-xs'>{JSON.stringify(usage.data, null, 2)}</pre></Card>;
}

export function AdminBillingPage() {
  const systemStatus = useAdminSystemStatus();

  if (systemStatus.isLoading) return <Card>Loading billing/system status...</Card>;
  if (systemStatus.isError) return <Card><div className='border border-amber-700 bg-amber-950/40 p-3 text-amber-200 rounded'>Failed to load billing/system status. Please try again.</div></Card>;

  const status = systemStatus.data;
  if (!status) return <Card>System status unavailable.</Card>;

  const billingOk = status.billing_configured;
  const stripeOk = status.stripe_configured;

  return <Card><div className='space-y-2'>
    <h2 className='text-lg'>Billing & system configuration</h2>
    <p>Billing configured: <strong className={billingOk ? 'text-emerald-400' : 'text-amber-300'}>{billingOk ? 'Configured' : 'Not configured'}</strong></p>
    <p>Stripe configured: <strong className={stripeOk ? 'text-emerald-400' : 'text-amber-300'}>{stripeOk ? 'Configured' : 'Missing'}</strong></p>
    <p>Stripe prices configured: <strong className={status.stripe_prices_configured ? 'text-emerald-400' : 'text-amber-300'}>{status.stripe_prices_configured ? 'Configured' : 'Missing'}</strong></p>
    <p>Environment: <strong>{status.environment}</strong></p>
    <p>Limits configured: <strong className={status.limits_configured ? 'text-emerald-400' : 'text-amber-300'}>{status.limits_configured ? 'Configured' : 'Missing/invalid'}</strong></p>
    {!billingOk && <div className='rounded border border-amber-700 bg-amber-950/40 p-3 text-amber-200'>Warning: Billing is misconfigured. Set Stripe secret key and required Stripe price IDs.</div>}
  </div></Card>;
}

export function AdminAuditPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const page = Number(new URLSearchParams(location.search).get('page') ?? '0');
  const audit = useAdminAudit(page, 20);
  if (audit.isLoading) return <Card>Loading audit log...</Card>;
  if (audit.isError) return <Card>Audit log API is not yet exposed.</Card>;
  if (!audit.data?.items?.length) return <Card>Audit log is empty.</Card>;
  return <Card><h2 className='mb-2 text-lg'>Audit log</h2>
    <div className='space-y-2'>
      {audit.data.items.map((item) => <div key={item.id} className='rounded border border-slate-800 p-2 text-sm'>{item.actor_email ?? 'system'} • {item.action} • {new Date(item.created_at).toLocaleString()}</div>)}
    </div>
    <div className='mt-3 flex gap-2'><button className='rounded bg-slate-700 px-2 py-1' onClick={()=>navigate(`?page=${Math.max(0, page-1)}`)}>Prev</button><button className='rounded bg-slate-700 px-2 py-1' onClick={()=>navigate(`?page=${page+1}`)}>Next</button></div>
  </Card>;
}


export function AdminSystemPage() { return <AdminBillingPage />; }

export function AdminPlansPage() {
  const subs = useAdminSubscriptions();
  if (subs.isLoading) return <Card>Loading plans & limits...</Card>;
  if (subs.isError) return <Card>Editable plan limits are not yet exposed by the backend.</Card>;
  if (!subs.data?.length) return <Card>Editable plan limits are not yet exposed by the backend.</Card>;
  return <Card><div className='space-y-2'><h2 className='text-lg'>Plans & limits</h2><p className='text-sm text-slate-300'>Editable plan limits are not yet exposed by the backend.</p><div className='overflow-x-auto'><table className='w-full min-w-[42rem] text-sm'><thead><tr className='text-left'><th>Email</th><th>Plan</th><th>Status</th><th>Credits</th><th>Overrides</th></tr></thead><tbody>{subs.data.map((s)=><tr key={s.subscription_id} className='border-t border-slate-800'><td>{s.email}</td><td>{s.plan_slug}</td><td>{s.status}</td><td>{JSON.stringify(s.usage_credits)}</td><td>{JSON.stringify(s.limit_overrides)}</td></tr>)}</tbody></table></div></div></Card>;
}

export function AdminLlmProvidersPage() {
  const llm = useAdminLlmModels();
  if (llm.isLoading) return <Card>Loading LLM providers...</Card>;
  if (llm.isError || !llm.data) return <Card>Failed loading LLM providers.</Card>;
  return <Card><div className='space-y-2'><h2 className='text-lg'>LLM providers</h2><div className='overflow-x-auto'><table className='w-full min-w-[42rem] text-sm'><thead><tr className='text-left'><th>Provider</th><th>Configured</th><th>Available models</th></tr></thead><tbody>{llm.data.providers.map((provider)=><tr key={provider.id} className='border-t border-slate-800'><td>{provider.name}</td><td>{provider.configured ? 'Yes' : 'No'}</td><td>{provider.models.map((model)=>model.name).join(', ') || 'None'}</td></tr>)}</tbody></table></div><p className='text-xs text-slate-400'>API keys and secrets are only stored in environment configuration and are never shown here.</p></div></Card>;
}
