import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';

export function DivorceDashboardPage() {
  const workspaceId = localStorage.getItem('active_workspace_id') || '';
  const { data } = useQuery({ queryKey: ['divorce-dash', workspaceId], queryFn: () => api.getDivorceDashboard(workspaceId), enabled: !!workspaceId });
  return <div><h1>Divorce Dashboard</h1><pre>{JSON.stringify(data, null, 2)}</pre></div>;
}
