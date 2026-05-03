import { useAdminPromptExecutionSummary, useAdminPromptExecutions } from '@/hooks/useApi';
import type { PromptExecutionLog } from '@/types/api';

function fmtCost(v: number) { return `$${v.toFixed(6)}`; }

export function AdminPromptAuditPage() {
  const q = useAdminPromptExecutions();
  const summaryQ = useAdminPromptExecutionSummary();
  const rows: PromptExecutionLog[] = q.data ?? [];

  if (q.isLoading) return <div>Loading prompt executions...</div>;
  if (q.isError) return <div>Failed to load prompt executions</div>;
  if (!rows.length) return <div>No prompt executions yet.</div>;

  return <div><h1 className="text-xl font-semibold">Prompt Audit Log</h1>
    {summaryQ.data ? <p>Total estimated cost: <strong>{fmtCost(summaryQ.data.total_estimated_cost_usd)}</strong></p> : null}
    <table><thead><tr><th>Provider</th><th>Model</th><th>Status</th><th>Fallback</th><th>Latency</th><th>Tokens</th><th>Estimated Cost</th><th>Source</th><th>Created</th><th>Error</th></tr></thead><tbody>{rows.map((r)=><tr key={r.id}><td>{r.provider}</td><td>{r.model}</td><td>{r.success ? 'Success' : 'Failed'}</td><td>{r.fallback_used ? 'Yes' : 'No'}</td><td>{r.latency_ms ?? '-'}</td><td>{r.total_tokens ?? '-'}</td><td>{r.pricing_known && r.estimated_cost_usd != null ? `${r.currency ?? 'USD'} ${fmtCost(r.estimated_cost_usd).slice(1)}` : 'pricing unknown'}</td><td>{r.source ?? '-'}</td><td>{new Date(r.created_at).toLocaleString()}</td><td>{r.error_message ?? '-'}</td></tr>)}</tbody></table></div>;
}
