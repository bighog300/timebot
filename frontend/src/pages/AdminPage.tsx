import { useState } from 'react';
import { useAdminAudit, useAdminMetrics, useAdminUsers, useUpdateUserRole } from '@/hooks/useApi';
import { useUIStore } from '@/store/uiStore';
import { Card } from '@/components/ui/Card';
import { PaginationControls } from '@/components/ui/PaginationControls';

export function AdminPage() {
  const [page, setPage] = useState(0);
  const [auditPage, setAuditPage] = useState(0);
  const limit = 10;
  const { pushToast } = useUIStore();
  const users = useAdminUsers(page, limit);
  const audit = useAdminAudit(auditPage, limit);
  const metrics = useAdminMetrics();
  const updateRole = useUpdateUserRole();

  return <div className='space-y-6'>
    <h1 className='text-xl font-semibold'>Admin Panel</h1>
    <div className='grid grid-cols-2 gap-3 md:grid-cols-4'>{Object.entries(metrics.data || {}).map(([k,v])=><Card key={k}><div className='text-sm text-slate-400'>{k}</div><div className='text-lg'>{String(v)}</div></Card>)}</div>
    <Card><h2 className='mb-2 text-lg'>User Management</h2>
      {users.isLoading ? 'Loading users...' : users.isError ? 'Failed loading users' : <table className='w-full text-sm'><thead><tr className='text-left'><th>Email</th><th>Name</th><th>Role</th><th>Created</th></tr></thead><tbody>{users.data?.items.map(u=><tr key={u.id} className='border-t border-slate-800'><td>{u.email}</td><td>{u.display_name}</td><td><select value={u.role} onChange={async (e)=>{ try { await updateRole.mutateAsync({userId:u.id, role:e.target.value}); pushToast('Role updated'); } catch (err) { pushToast((err as Error).message, 'error'); } }}><option>viewer</option><option>editor</option><option>admin</option></select></td><td>{new Date(u.created_at).toLocaleString()}</td></tr>)}</tbody></table>}
      <PaginationControls page={page} total={users.data ? Math.max(1, Math.ceil(users.data.total_count / users.data.limit)) : undefined} hasNext={Boolean(users.data?.items?.length)} onPrev={()=>setPage((p)=>Math.max(0,p-1))} onNext={()=>setPage((p)=>p+1)} />
    </Card>
    <Card><h2 className='mb-2 text-lg'>Audit Explorer</h2>
      {audit.isLoading ? 'Loading audit...' : audit.isError ? 'Failed loading audit' : <table className='w-full text-sm'><thead><tr className='text-left'><th>Actor</th><th>Entity</th><th>ID</th><th>Action</th><th>Created</th></tr></thead><tbody>{audit.data?.items.map(a=><tr key={a.id} className='border-t border-slate-800'><td>{a.actor_email || 'system'}</td><td>{a.entity_type}</td><td>{a.entity_id}</td><td>{a.action}</td><td>{new Date(a.created_at).toLocaleString()}</td></tr>)}</tbody></table>}
      <PaginationControls page={auditPage} total={audit.data ? Math.max(1, Math.ceil(audit.data.total_count / audit.data.limit)) : undefined} hasNext={Boolean(audit.data?.items?.length)} onPrev={()=>setAuditPage((p)=>Math.max(0,p-1))} onNext={()=>setAuditPage((p)=>p+1)} />
    </Card>
  </div>;
}
