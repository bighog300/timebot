import { useMemo, useState } from 'react';
import { useAdminPromptExecutionSummary } from '@/hooks/useApi';

function pct(v: number) { return `${(v * 100).toFixed(1)}%`; }
function usd(v: number) { return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(v); }
function num(v: number) { return new Intl.NumberFormat('en-US').format(v); }

function Breakdown({ title, data, formatter = (v:number)=>String(v) }: { title: string; data: Record<string, number>; formatter?: (v:number)=>string }) {
  const entries = Object.entries(data);
  return <section><h3 className="font-semibold">{title}</h3>{entries.length ? <ul>{entries.map(([k,v]) => <li key={k}>{k}: {formatter(v)}</li>)}</ul> : <p>No data.</p>}</section>;
}

export function AdminPromptAnalyticsPage() {
  const [filters, setFilters] = useState<Record<string, string>>({});
  const parsed = useMemo(() => ({
    provider: filters.provider || undefined,
    model: filters.model || undefined,
    source: filters.source || undefined,
    purpose: filters.purpose || undefined,
    actor_user_id: filters.actor_user_id || undefined,
    success: filters.success === '' ? undefined : filters.success === 'true',
    fallback_used: filters.fallback_used === '' ? undefined : filters.fallback_used === 'true',
    created_after: filters.created_after || undefined,
    created_before: filters.created_before || undefined,
  }), [filters]);
  const q = useAdminPromptExecutionSummary(parsed);

  if (q.isLoading) return <div>Loading prompt analytics...</div>;
  if (q.isError) return <div>Failed to load prompt analytics.</div>;
  if (!q.data || q.data.total_calls === 0) return <div><h1>Prompt Analytics</h1><p>No prompt analytics data yet.</p></div>;

  const d = q.data;
  return <div>
    <h1 className="text-xl font-semibold">Prompt Analytics</h1>
    <div>
      <label>Provider <input aria-label="provider" value={filters.provider ?? ''} onChange={(e)=>setFilters((f)=>({...f, provider:e.target.value}))} /></label>
      <label>Model <input aria-label="model" value={filters.model ?? ''} onChange={(e)=>setFilters((f)=>({...f, model:e.target.value}))} /></label>
      <label>Source <input aria-label="source" value={filters.source ?? ''} onChange={(e)=>setFilters((f)=>({...f, source:e.target.value}))} /></label>
      <label>Purpose <input aria-label="purpose" value={filters.purpose ?? ''} onChange={(e)=>setFilters((f)=>({...f, purpose:e.target.value}))} /></label>
      <label>User ID <input aria-label="actor_user_id" value={filters.actor_user_id ?? ''} onChange={(e)=>setFilters((f)=>({...f, actor_user_id:e.target.value}))} /></label>
      <label>Success <select aria-label="success" value={filters.success ?? ''} onChange={(e)=>setFilters((f)=>({...f, success:e.target.value}))}><option value="">All</option><option value="true">Success</option><option value="false">Failure</option></select></label>
      <label>Fallback <select aria-label="fallback" value={filters.fallback_used ?? ''} onChange={(e)=>setFilters((f)=>({...f, fallback_used:e.target.value}))}><option value="">All</option><option value="true">Used</option><option value="false">Not Used</option></select></label>
      <label>Created after <input aria-label="created_after" type="date" value={filters.created_after ?? ''} onChange={(e)=>setFilters((f)=>({...f, created_after:e.target.value}))} /></label>
      <label>Created before <input aria-label="created_before" type="date" value={filters.created_before ?? ''} onChange={(e)=>setFilters((f)=>({...f, created_before:e.target.value}))} /></label>
    </div>
    <p>Total calls: {num(d.total_calls)}</p><p>Success rate: {pct(d.success_rate)}</p><p>Fallback rate: {pct(d.fallback_rate)}</p><p>Average latency: {d.avg_latency_ms?.toFixed(1) ?? '-'} ms</p><p>Total tokens: {num(d.total_tokens)}</p><p>Total estimated cost: {usd(d.total_estimated_cost_usd)}</p><p>Unknown pricing count: {num(d.pricing_unknown_count)}</p>
    <Breakdown title="Calls by provider" data={d.calls_by_provider} />
    <Breakdown title="Calls by model" data={d.calls_by_model} />
    <Breakdown title="Cost by provider" data={d.cost_by_provider} formatter={usd} />
    <Breakdown title="Cost by model" data={d.cost_by_model} formatter={usd} />
    <Breakdown title="Calls by source" data={d.calls_by_source} />
    <Breakdown title="Failures by provider" data={d.failures_by_provider} />
    <Breakdown title="Fallback usage by provider" data={d.fallback_by_provider} />
  </div>;
}
