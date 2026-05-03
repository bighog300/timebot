import { useAdminPromptExecutions } from '@/hooks/useApi';
import type { PromptExecutionLog } from '@/types/api';

export function AdminPromptAuditPage() {
  const q = useAdminPromptExecutions();
  const rows: PromptExecutionLog[] = q.data ?? [];

  if (q.isLoading) return <div>Loading prompt executions...</div>;
  if (q.isError) return <div>Failed to load prompt executions</div>;
  if (!rows.length) return <div>No prompt executions yet.</div>;

  return <div><h1 className="text-xl font-semibold">Prompt Audit Log</h1><table><thead><tr><th>Provider</th><th>Model</th><th>Status</th><th>Fallback</th><th>Latency</th><th>Tokens</th><th>Source</th><th>Created</th><th>Error</th></tr></thead><tbody>{rows.map((r)=><tr key={r.id}><td>{r.provider}</td><td>{r.model}</td><td>{r.success ? 'Success' : 'Failed'}</td><td>{r.fallback_used ? 'Yes' : 'No'}</td><td>{r.latency_ms ?? '-'}</td><td>{r.total_tokens ?? '-'}</td><td>{r.source ?? '-'}</td><td>{new Date(r.created_at).toLocaleString()}</td><td>{r.error_message ?? '-'}</td></tr>)}</tbody></table></div>;
}
