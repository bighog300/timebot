import { FormEvent, useEffect, useState } from 'react';
import { api, getErrorDetail } from '@/services/api';
import type { MessageThread } from '@/types/api';

export function AdminMessagesPage() {
  const [threads, setThreads] = useState<MessageThread[]>([]);
  const [active, setActive] = useState<MessageThread | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [reply, setReply] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const load = async () => { setLoading(true); setError(null); try { setThreads(await api.adminListMessages({ status: statusFilter || undefined, category: categoryFilter || undefined })); } catch (e) { setError(getErrorDetail(e)); } finally { setLoading(false); } };
  useEffect(() => { void load(); }, [statusFilter, categoryFilter]);

  const openThread = async (id: string) => setActive(await api.adminGetMessageThread(id));

  return <div className='grid gap-4 md:grid-cols-[320px_minmax(0,1fr)]'>
    <div className='space-y-3'>
      <h2 className='text-lg font-semibold'>Admin Messages</h2>
      <div className='flex gap-2'>
        <select value={statusFilter} onChange={(e)=>setStatusFilter(e.target.value)} className='rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm'><option value=''>All status</option><option>open</option><option>in_progress</option><option>closed</option></select>
        <select value={categoryFilter} onChange={(e)=>setCategoryFilter(e.target.value)} className='rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm'><option value=''>All category</option><option value='bug_report'>Bug report</option><option value='feature_request'>Feature request</option><option value='support'>Support</option></select>
      </div>
      {loading ? <div className='text-sm text-slate-400'>Loading threads...</div> : null}
      {error ? <div className='text-sm text-red-300'>{error}</div> : null}
      {!loading && !threads.length ? <div className='text-sm text-slate-400'>No threads for current filters.</div> : threads.map((t)=><button key={t.id} onClick={()=>void openThread(t.id)} className='w-full rounded border border-slate-700 p-2 text-left'>{t.subject}<div className='text-xs text-slate-400'>{t.category} · {t.status}</div></button>)}
    </div>
    <div className='rounded border border-slate-700 p-3'>
      {!active ? <div className='text-sm text-slate-400'>Pick a thread.</div> : <div className='space-y-3'>
        <div className='flex items-center justify-between'><div className='text-lg font-semibold'>{active.subject}</div><select value={active.status} onChange={async(e)=>setActive(await api.adminPatchMessageThread(active.id, e.target.value))} className='rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm'><option>open</option><option>in_progress</option><option>closed</option></select></div>
        {(active.messages || []).map((m)=><div key={m.id} className='rounded border border-slate-800 p-2'><div className='text-xs text-slate-400'>{m.sender_type}</div><div>{m.body}</div></div>)}
        <form onSubmit={async(e: FormEvent)=>{e.preventDefault(); setActive(await api.adminReplyMessageThread(active.id, reply)); setReply(''); await load();}} className='space-y-2'>
          <textarea value={reply} onChange={(e)=>setReply(e.target.value)} className='min-h-24 w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm' required />
          <button className='rounded bg-blue-700 px-3 py-1.5 text-sm'>Send reply</button>
        </form>
      </div>}
    </div>
  </div>;
}
