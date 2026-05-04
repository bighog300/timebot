import { useState } from 'react';
import { getErrorDetail } from '@/services/api';
import { useCancelWorkspaceInvite, useInviteWorkspaceMember, useRemoveWorkspaceMember, useResendWorkspaceInvite, useUpdateWorkspaceMemberRole, useWorkspaceDetail } from '@/hooks/useApi';
import { useAuth } from '@/auth/AuthContext';
import { useParams } from 'react-router-dom';

export function WorkspaceDetailPage() {
  const { workspaceId = '' } = useParams();
  const { user } = useAuth();
  const { data, isLoading, isError, error } = useWorkspaceDetail(workspaceId);
  const inviteMember = useInviteWorkspaceMember(workspaceId);
  const updateRole = useUpdateWorkspaceMemberRole(workspaceId);
  const removeMember = useRemoveWorkspaceMember(workspaceId);
  const resendInvite = useResendWorkspaceInvite(workspaceId);
  const cancelInvite = useCancelWorkspaceInvite(workspaceId);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('member');
  const [devInviteLink, setDevInviteLink] = useState<string | null>(null);

  const myMember = data?.members?.find((m) => m.user_id === user?.id);
  const canManage = myMember?.role === 'owner' || myMember?.role === 'admin';

  if (isLoading) return <p>Loading workspace...</p>;
  if (isError) return <p className="text-red-400">Failed to load workspace: {(error as Error).message}</p>;
  if (!data) return <p>Workspace not found.</p>;

  return <div className="space-y-6">
    <div>
      <h1 className="text-2xl font-semibold">{data.name}</h1>
      <p className="text-sm text-slate-300">Type: {data.type}</p>
    </div>
    {canManage && <form className="space-y-2" onSubmit={async (e)=>{e.preventDefault(); const resp = await inviteMember.mutateAsync({ email, role }); setDevInviteLink(resp.dev_invite_link ?? null); setEmail(''); }}>
      <h2 className="font-medium">Invite member</h2>
      <div className="flex gap-2">
        <input placeholder="member@example.com" value={email} onChange={(e)=>setEmail(e.target.value)} className="rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm" />
        <select value={role} onChange={(e)=>setRole(e.target.value)} className="rounded border border-slate-700 bg-slate-900 px-2 py-2 text-sm"><option value="member">member</option><option value="admin">admin</option></select>
        <button type="submit" className="rounded bg-blue-600 px-3 py-2 text-sm">Invite</button>
      </div>
      {inviteMember.isError && <p className="text-red-400">{getErrorDetail(inviteMember.error)}</p>}
      {devInviteLink && <p className="text-emerald-400">Dev invite link: {devInviteLink}</p>}
    </form>}

    <div>
      <h2 className="font-medium">Members</h2>
      {!data.members && <p className="text-sm text-slate-400">Member list is unavailable from current backend response.</p>}
      {!!data.members?.length && <ul className="space-y-2">{data.members.map((m) => <li key={m.user_id} className="rounded border border-slate-800 p-2 flex items-center justify-between">
        <div>{m.email ?? m.user_id} <span className="text-xs text-slate-400">({m.role})</span></div>
        {canManage && <div className="flex items-center gap-2">
          <select value={m.role} onChange={(e)=>updateRole.mutate({ userId: m.user_id, role: e.target.value as 'owner' | 'admin' | 'member' })} disabled={m.role === 'owner'} className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm"><option value="owner">owner</option><option value="admin">admin</option><option value="member">member</option></select>
          <button disabled={m.role === 'owner'} onClick={()=>removeMember.mutate(m.user_id)} className="rounded bg-red-700 px-2 py-1 text-xs disabled:opacity-50">Remove</button>
        </div>}
      </li>)}</ul>}
    </div>
    <div>
      <h2 className="font-medium">Pending invites</h2>
      <ul>{(data.invites || []).filter((i)=>i.status === 'pending').map((i)=><li key={i.id}>{i.email} ({i.role}) <button onClick={()=>resendInvite.mutate(i.id)}>Resend</button> <button onClick={()=>cancelInvite.mutate(i.id)}>Cancel</button> {i.dev_invite_link && <span>{i.dev_invite_link}</span>}</li>)}</ul>
    </div>
  </div>;
}
