import { FormEvent, useMemo, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { useUIStore } from '@/store/uiStore';
import { getErrorDetail } from '@/services/api';
import {
  useAdminUsers,
  useCreateAdminUser,
  useInviteAdminUser,
  useAdminInvites,
  useUpdateUserRole,
  useDeactivateAdminUser,
  useReactivateAdminUser,
  useDeleteAdminUser,
  useResendAdminInvite,
  useCancelAdminInvite,
} from '@/hooks/useApi';

export function AdminUsersPage() {
  const { pushToast } = useUIStore();
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [showInvite, setShowInvite] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; email: string } | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState('');

  const users = useAdminUsers(0, 100, { q: search || undefined, role: roleFilter || undefined, is_active: statusFilter === '' ? undefined : statusFilter === 'active' });
  const invites = useAdminInvites();
  const createUser = useCreateAdminUser();
  const inviteUser = useInviteAdminUser();
  const updateRole = useUpdateUserRole();
  const deactivate = useDeactivateAdminUser();
  const reactivate = useReactivateAdminUser();
  const deleteUser = useDeleteAdminUser();
  const resendInvite = useResendAdminInvite();
  const cancelInvite = useCancelAdminInvite();

  const deletePhrase = useMemo(() => `delete ${deleteTarget?.email ?? ''}`, [deleteTarget]);

  async function handleDelete() {
    if (!deleteTarget || (deleteConfirm !== deleteTarget.email && deleteConfirm !== 'DELETE')) return;
    try {
      await deleteUser.mutateAsync({ userId: deleteTarget.id, confirmation: deleteConfirm });
      pushToast('User deleted.');
      setDeleteTarget(null);
      setDeleteConfirm('');
    } catch (error) {
      pushToast(getErrorDetail(error), 'error');
    }
  }

  return <div className='space-y-4'>
    <h2 className='text-lg font-semibold'>Admin Users</h2>
    <Card>
      <div className='mb-3 flex flex-wrap gap-2'>
        <input aria-label='Search users' value={search} onChange={(e) => setSearch(e.target.value)} placeholder='Search email/name' className='rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm' />
        <select aria-label='Role filter' value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className='rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm'><option value=''>All roles</option><option value='admin'>Admin</option><option value='viewer'>Viewer</option><option value='editor'>Editor</option></select>
        <select aria-label='Status filter' value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className='rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm'><option value=''>All status</option><option value='active'>Active</option><option value='inactive'>Inactive</option></select>
        <button onClick={() => setShowCreate(true)} className='rounded bg-blue-700 px-3 py-1.5 text-sm'>Create User</button>
        <button onClick={() => setShowInvite(true)} className='rounded bg-emerald-700 px-3 py-1.5 text-sm'>Invite User</button>
      </div>

      {users.isLoading && <p>Loading users...</p>}
      {users.isError && <p className='text-red-300'>Failed to load users.</p>}
      {!users.isLoading && !users.isError && !users.data?.items?.length && <p>No users found.</p>}
      {!!users.data?.items?.length && <div className='overflow-x-auto'><table className='w-full min-w-[64rem] text-sm'><thead><tr className='text-left'><th>Email</th><th>Name</th><th>Role</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead><tbody>
        {users.data.items.map((u) => <tr key={u.id} className='border-t border-slate-800'>
          <td>{u.email}</td><td>{u.display_name}</td>
          <td><select aria-label={`Role for ${u.email}`} value={u.role} onChange={async (e)=>{ try { await updateRole.mutateAsync({ userId: u.id, role: e.target.value }); pushToast('Role updated.'); } catch (error) { pushToast(getErrorDetail(error), 'error'); } }} className='rounded border border-slate-700 bg-slate-900 px-2 py-1'><option value='viewer'>viewer</option><option value='editor'>editor</option><option value='admin'>admin</option></select></td>
          <td>{u.is_active ? 'active' : 'inactive'}</td>
          <td>{new Date(u.created_at).toLocaleDateString()}</td>
          <td className='space-x-2'>
            {u.is_active ? <button className='rounded bg-amber-700 px-2 py-1' onClick={async ()=>{ try { await deactivate.mutateAsync(u.id); pushToast('User deactivated.'); } catch (error) { pushToast(getErrorDetail(error), 'error'); } }}>Deactivate</button> : <button className='rounded bg-emerald-700 px-2 py-1' onClick={async ()=>{ try { await reactivate.mutateAsync(u.id); pushToast('User reactivated.'); } catch (error) { pushToast(getErrorDetail(error), 'error'); } }}>Reactivate</button>}
            <button className='rounded bg-red-800 px-2 py-1' onClick={() => { setDeleteTarget({ id: u.id, email: u.email }); setDeleteConfirm(''); }}>Delete</button>
          </td>
        </tr>)}
      </tbody></table></div>}
    </Card>

    <Card><h3 className='mb-2 text-base font-semibold'>Invites</h3>
      {invites.isLoading && <p>Loading invites...</p>}
      {invites.isError && <p className='text-red-300'>Failed to load invites.</p>}
      {!invites.isLoading && !invites.isError && !invites.data?.length && <p>No invites.</p>}
      {!!invites.data?.length && <div className='space-y-2'>{invites.data.map((invite) => <div key={invite.id} className='rounded border border-slate-700 p-2 text-sm'>
        <div>{invite.email} • {invite.role} • {invite.status}</div>
        {invite.dev_invite_link && <div className='break-all text-xs text-emerald-300'>Dev invite link: <a className='underline' href={invite.dev_invite_link} target='_blank' rel='noreferrer'>{invite.dev_invite_link}</a></div>}
        <div className='mt-2 space-x-2'>
          <button className='rounded bg-slate-700 px-2 py-1' onClick={async ()=>{ try { await resendInvite.mutateAsync(invite.id); pushToast('Invite resent.'); } catch (error) { pushToast(getErrorDetail(error), 'error'); } }}>Resend</button>
          <button className='rounded bg-amber-700 px-2 py-1' onClick={async ()=>{ try { await cancelInvite.mutateAsync(invite.id); pushToast('Invite canceled.'); } catch (error) { pushToast(getErrorDetail(error), 'error'); } }}>Cancel</button>
        </div>
      </div>)}</div>}
    </Card>

    {showCreate && <UserModal title='Create User' onClose={()=>setShowCreate(false)} onSubmit={async(payload)=>{ await createUser.mutateAsync(payload); pushToast('User created.'); setShowCreate(false); }} />}
    {showInvite && <UserModal title='Invite User' onClose={()=>setShowInvite(false)} onSubmit={async(payload)=>{ const result = await inviteUser.mutateAsync(payload); pushToast('Invite created.'); if (result?.dev_invite_link) pushToast('Dev invite link returned.'); setShowInvite(false); }} />}

    {deleteTarget && <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4'><div className='w-full max-w-md rounded border border-slate-700 bg-slate-900 p-4'>
      <h4 className='font-semibold'>Confirm delete</h4><p className='text-sm text-slate-300'>Type <code>{deleteTarget.email}</code> or <code>DELETE</code> to confirm.</p>
      <input aria-label='Delete confirmation' value={deleteConfirm} onChange={(e)=>setDeleteConfirm(e.target.value)} className='mt-2 w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5'/>
      <div className='mt-3 flex justify-end gap-2'><button className='rounded bg-slate-700 px-3 py-1.5' onClick={()=>setDeleteTarget(null)}>Cancel</button><button disabled={deleteConfirm !== deleteTarget.email && deleteConfirm !== 'DELETE'} className='rounded bg-red-700 px-3 py-1.5 disabled:opacity-50' onClick={handleDelete}>Delete</button></div>
    </div></div>}
  </div>;
}

function UserModal({ title, onClose, onSubmit }: { title: string; onClose: () => void; onSubmit: (payload: { email: string; display_name: string; role: string; password?: string; send_invite?: boolean }) => Promise<void> }) {
  const [email, setEmail] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [role, setRole] = useState('viewer');
  const [password, setPassword] = useState('');
  const { pushToast } = useUIStore();
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    try {
      await onSubmit({ email, display_name: displayName, role, ...(title === 'Create User' ? { password } : { send_invite: true }) });
    } catch (error) {
      pushToast(getErrorDetail(error), 'error');
    } finally {
      setSaving(false);
    }
  }

  return <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4'><form onSubmit={submit} className='w-full max-w-md space-y-2 rounded border border-slate-700 bg-slate-900 p-4'>
    <h4 className='font-semibold'>{title}</h4>
    <input required placeholder='Email' value={email} onChange={(e)=>setEmail(e.target.value)} className='w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5'/>
    <input required placeholder='Display name' value={displayName} onChange={(e)=>setDisplayName(e.target.value)} className='w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5'/>
    <select value={role} onChange={(e)=>setRole(e.target.value)} className='w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5'><option value='viewer'>viewer</option><option value='editor'>editor</option><option value='admin'>admin</option></select>
    {title === 'Create User' && <input type='password' minLength={8} required placeholder='Password' value={password} onChange={(e)=>setPassword(e.target.value)} className='w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5' />}
    <div className='flex justify-end gap-2'><button type='button' onClick={onClose} className='rounded bg-slate-700 px-3 py-1.5'>Cancel</button><button disabled={saving} className='rounded bg-blue-700 px-3 py-1.5'>{saving ? 'Saving...' : 'Submit'}</button></div>
  </form></div>;
}
