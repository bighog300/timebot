import { useMutation, useQuery } from '@tanstack/react-query';
import { useConnections } from '@/hooks/useApi';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';
import { useUIStore } from '@/store/uiStore';

export function ConnectionsPage() {
  const { data, refetch, isLoading, isError } = useConnections();
  const pushToast = useUIStore((s) => s.pushToast);
  const [first] = data ?? [];
  const logs = useQuery({ queryKey: ['sync-logs', first?.type], queryFn: () => api.getSyncLogs(first.type), enabled: !!first });

  const connect = useMutation({
    mutationFn: (type: string) => api.startConnectProvider(type),
    onSuccess: (result) => {
      window.location.assign(result.authorization_url);
    },
    onError: () => pushToast('Unable to start OAuth flow'),
  });

  const disconnect = useMutation({
    mutationFn: (type: string) => api.disconnectProvider(type),
    onSuccess: () => {
      pushToast('Disconnected');
      refetch();
    },
    onError: () => pushToast('Disconnect failed'),
  });

  const sync = useMutation({
    mutationFn: (type: string) => api.syncProvider(type),
    onSuccess: (payload) => {
      pushToast(`Sync complete: +${payload.documents_added} / ~${payload.documents_updated}`);
      refetch();
      logs.refetch();
    },
    onError: () => pushToast('Sync failed'),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Connections</h1>
      {isLoading && <LoadingState />}
      {isError && <ErrorState message="Failed to load connections" />}
      {!isLoading && !isError && (data?.length ?? 0) === 0 && <EmptyState label="No providers configured." />}
      <div className="grid gap-3 md:grid-cols-2">
        {data?.map((conn) => (
          <Card key={conn.id}>
            <div className="mb-2 flex items-center justify-between">
              <strong>{conn.display_name}</strong>
              <span className="text-xs text-slate-400">{conn.status}</span>
            </div>
            <div className="mb-1 text-sm text-slate-400">{conn.email || 'Not connected'}</div>
            <div className="mb-1 text-sm text-slate-400">{conn.document_count} docs • {conn.last_sync_status || 'never synced'}</div>
            <div className="mb-3 text-xs text-slate-500">Last sync: {conn.last_sync_date ? new Date(conn.last_sync_date).toLocaleString() : 'n/a'}</div>
            {conn.last_error_message && <div className="mb-3 rounded bg-red-950/30 p-2 text-xs text-red-300">{conn.last_error_message}</div>}
            <div className="flex gap-2">
              <Button onClick={() => connect.mutate(conn.type)} disabled={connect.isPending}>{conn.is_authenticated ? 'Reconnect' : 'Connect'}</Button>
              <Button onClick={() => disconnect.mutate(conn.type)} className="bg-slate-700" disabled={!conn.is_authenticated || disconnect.isPending}>Disconnect</Button>
              <Button onClick={() => sync.mutate(conn.type)} className="bg-emerald-700" disabled={!conn.is_authenticated || sync.isPending}>Sync</Button>
            </div>
          </Card>
        ))}
      </div>
      <Card>
        <h3 className="mb-2">Sync history ({first?.display_name ?? 'n/a'})</h3>
        {logs.isLoading && <LoadingState label="Loading sync history..." />}
        {logs.isError && <ErrorState message="Failed to load sync history" />}
        {logs.isSuccess && (logs.data?.length ?? 0) === 0 && <EmptyState label="No sync history yet." />}
        <ul className="space-y-1 text-sm">
          {logs.data?.map((log) => (
            <li key={log.id}>{log.status} • +{log.documents_added} / ~{log.documents_updated} / !{log.documents_failed}</li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
