import { useState } from 'react';
import { useAdminAudit, useAdminMetrics, useAdminProcessingSummary, useAdminUsers, useUpdateUserRole } from '@/hooks/useApi';
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
  const processingSummary = useAdminProcessingSummary();
  const updateRole = useUpdateUserRole();

  return <div className='space-y-6'>
    <h1 className='text-xl font-semibold'>Admin Panel</h1>
    <div className='grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-4'>{Object.entries(metrics.data || {}).map(([k,v])=><Card key={k}><div className='text-sm text-slate-400 break-words'>{k}</div><div className='text-lg break-words'>{String(v)}</div></Card>)}</div>
    <Card>
      <h2 className='mb-2 text-lg'>Processing Summary</h2>
      {processingSummary.isLoading ? 'Loading processing summary...' : processingSummary.isError ? 'Failed loading processing summary' : (
        <div className='grid grid-cols-1 gap-2 text-sm sm:grid-cols-2 md:grid-cols-5'>
          <div className='rounded border border-slate-800 p-2'><div className='text-slate-400'>pending</div><div>{processingSummary.data?.pending ?? 0}</div></div>
          <div className='rounded border border-slate-800 p-2'><div className='text-slate-400'>processing</div><div>{processingSummary.data?.processing ?? 0}</div></div>
          <div className='rounded border border-slate-800 p-2'><div className='text-slate-400'>completed</div><div>{processingSummary.data?.completed ?? 0}</div></div>
          <div className='rounded border border-slate-800 p-2'><div className='text-slate-400'>failed</div><div>{processingSummary.data?.failed ?? 0}</div></div>
          <div className='rounded border border-slate-800 p-2'><div className='text-slate-400'>recently failed</div><div>{processingSummary.data?.recently_failed ?? 0}</div></div>
        </div>
      )}
    </Card>
    <Card><h2 className='mb-2 text-lg'>User Management</h2>
      {users.isLoading ? 'Loading users...' : users.isError ? 'Failed loading users' : <div className='overflow-x-auto'><table className='w-full min-w-[42rem] text-sm'><thead><tr className='text-left'><th className='pr-3'>Email</th><th className='pr-3'>Name</th><th className='pr-3'>Role</th><th>Created</th></tr></thead><tbody>{users.data?.items.map(u=><tr key={u.id} className='border-t border-slate-800'><td className='break-words pr-3'>{u.email}</td><td className='break-words pr-3'>{u.display_name}</td><td className='pr-3'><select value={u.role} onChange={async (e)=>{ try { await updateRole.mutateAsync({userId:u.id, role:e.target.value}); pushToast('Role updated'); } catch (err) { pushToast((err as Error).message, 'error'); } }}><option>viewer</option><option>editor</option><option>admin</option></select></td><td>{new Date(u.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>}
      <PaginationControls page={page} total={users.data ? Math.max(1, Math.ceil(users.data.total_count / users.data.limit)) : undefined} hasNext={Boolean(users.data?.items?.length)} onPrev={()=>setPage((p)=>Math.max(0,p-1))} onNext={()=>setPage((p)=>p+1)} />
    </Card>
    <Card><h2 className='mb-2 text-lg'>Audit Explorer</h2>
      {audit.isLoading ? 'Loading audit...' : audit.isError ? 'Failed loading audit' : <div className='overflow-x-auto'><table className='w-full min-w-[48rem] text-sm'><thead><tr className='text-left'><th className='pr-3'>Actor</th><th className='pr-3'>Entity</th><th className='pr-3'>ID</th><th className='pr-3'>Action</th><th>Created</th></tr></thead><tbody>{audit.data?.items.map(a=><tr key={a.id} className='border-t border-slate-800'><td className='break-words pr-3'>{a.actor_email || 'system'}</td><td className='break-words pr-3'>{a.entity_type}</td><td className='break-words pr-3'>{a.entity_id}</td><td className='break-words pr-3'>{a.action}</td><td>{new Date(a.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>}
      <PaginationControls page={auditPage} total={audit.data ? Math.max(1, Math.ceil(audit.data.total_count / audit.data.limit)) : undefined} hasNext={Boolean(audit.data?.items?.length)} onPrev={()=>setAuditPage((p)=>Math.max(0,p-1))} onNext={()=>setAuditPage((p)=>p+1)} />
    </Card>
  </div>;
}
