import { Link, useParams } from 'react-router-dom';
import { useEffect } from 'react';
import { useAcceptWorkspaceInvite } from '@/hooks/useApi';

export function WorkspaceInviteAcceptPage() {
  const { token = '' } = useParams();
  const acceptInvite = useAcceptWorkspaceInvite();
  useEffect(() => { if (token) acceptInvite.mutate({ token }); }, [token]);

  return <div className="space-y-3">
    <h1 className="text-2xl font-semibold">Accept Workspace Invite</h1>
    {acceptInvite.isPending && <p>Accepting invite...</p>}
    {acceptInvite.isSuccess && <p className="text-emerald-400">Invite accepted successfully.</p>}
    {acceptInvite.isError && <p className="text-red-400">Failed to accept invite.</p>}
    <Link className="underline text-blue-400" to="/workspaces">Back to Workspaces</Link>
  </div>;
}
