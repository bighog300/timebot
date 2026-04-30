import { useState } from 'react';
import { useAdminAudit, useAdminMetrics, useAdminUsers, useUpdateUserRole } from '@/hooks/useApi';
import { useUIStore } from '@/store/uiStore';

export function AdminPage() {
  const [page, setPage] = useState(0);
  const [auditPage, setAuditPage] = useState(0);
  const limit = 10;
  const { pushToast } = useUIStore();
  const users = useAdminUsers(page, limit);
  const audit = useAdminAudit(auditPage, limit);
  const metrics = useAdminMetrics();
  const updateRole = useUpdateUserRole();

  const onUpdate = async (userId: string, role: string) => {
    try {
      await updateRole.mutateAsync({ userId, role });
      pushToast('Role updated');
    } catch (e) {
      pushToast((e as Error).message || 'Role update failed');
    }
  };

  return <div className='space-y-6'>Admin Panel
    <div className='grid grid-cols-2 md:grid-cols-4 gap-3'>{Object.entries(metrics.data || {}).map(([k,v])=><div key={k} className='rounded bg-slate-900 p-3'><div>{k}</div><div>{String(v)}</div></div>)}</div>
    <div>
      <h2>User Management</h2>
      {users.isLoading ? 'Loading users...' : users.isError ? 'Failed loading users' : <table><thead><tr><th>Email</th><th>Name</th><th>Role</th><th>Created</th><th /></tr></thead><tbody>{users.data?.items.map(u=><tr key={u.id}><td>{u.email}</td><td>{u.display_name}</td><td><select defaultValue={u.role} onChange={(e)=>onUpdate(u.id,e.target.value)}><option>viewer</option><option>editor</option><option>admin</option></select></td><td>{new Date(u.created_at).toLocaleString()}</td><td /></tr>)}</tbody></table>}
      <button onClick={()=>setPage((p)=>Math.max(0,p-1))}>Prev</button><button onClick={()=>setPage((p)=>p+1)}>Next</button>
    </div>
    <div>
      <h2>Audit Explorer</h2>
      {audit.isLoading ? 'Loading audit...' : audit.isError ? 'Failed loading audit' : <table><thead><tr><th>Actor</th><th>Entity</th><th>ID</th><th>Action</th><th>Created</th></tr></thead><tbody>{audit.data?.items.map(a=><tr key={a.id}><td>{a.actor_email || 'system'}</td><td>{a.entity_type}</td><td>{a.entity_id}</td><td>{a.action}</td><td>{new Date(a.created_at).toLocaleString()}</td></tr>)}</tbody></table>}
      <button onClick={()=>setAuditPage((p)=>Math.max(0,p-1))}>Prev</button><button onClick={()=>setAuditPage((p)=>p+1)}>Next</button>
    </div>
  </div>;
}
