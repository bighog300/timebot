import { FormEvent, useEffect, useState } from 'react';
import { api, getErrorDetail } from '@/services/api';
import type { MessageThread } from '@/types/api';

export function MessagesPage() {
  const [threads, setThreads] = useState<MessageThread[]>([]);
  const [active, setActive] = useState<MessageThread | null>(null);
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [category, setCategory] = useState('support');
  const [workspaceId, setWorkspaceId] = useState('');
  const [replyBody, setReplyBody] = useState('');
  const [error, setError] = useState<string | null>(null);

  const load = async () => { const items = await api.listMessages(); setThreads(items); if (active) setActive(await api.getMessageThread(active.id)); };
  useEffect(() => { load().catch((e) => setError(getErrorDetail(e))); }, []);

  const onCreate = async (e: FormEvent) => { e.preventDefault(); setError(null); try { await api.createMessageThread({ category, subject, body, workspace_id: workspaceId || undefined }); setSubject(''); setBody(''); setWorkspaceId(''); await load(); } catch (err) { setError(getErrorDetail(err)); } };
  return <div className='grid gap-4 md:grid-cols-[280px_minmax(0,1fr)]'>
    <div className='space-y-3'>
      <h1 className='text-xl font-semibold'>Messages</h1>
      <form onSubmit={onCreate} className='space-y-2 rounded border border-slate-700 p-3'>
        <div className='text-sm font-medium'>New request</div>
        <select value={category} onChange={(e)=>setCategory(e.target.value)} className='w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm'><option value='bug_report'>Bug report</option><option value='feature_request'>Feature request</option><option value='support'>Support request</option></select>
        <input value={subject} onChange={(e)=>setSubject(e.target.value)} placeholder='Subject' className='w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm' required />
        <input value={workspaceId} onChange={(e)=>setWorkspaceId(e.target.value)} placeholder='Workspace ID (optional)' className='w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm' />
        <textarea value={body} onChange={(e)=>setBody(e.target.value)} placeholder='Describe your request' className='min-h-24 w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm' required />
        <button className='rounded bg-blue-700 px-3 py-1.5 text-sm'>Send</button>
      </form>
      <div className='space-y-2'>
        {threads.length === 0 ? <div className='text-sm text-slate-400'>No threads yet.</div> : threads.map((t)=><button key={t.id} className='w-full rounded border border-slate-700 p-2 text-left' onClick={async()=>setActive(await api.getMessageThread(t.id))}>{t.subject}<div className='text-xs text-slate-400'>{t.category} · {t.status}</div></button>)}
      </div>
    </div>
    <div className='rounded border border-slate-700 p-3'>
      {error ? <div className='mb-2 text-sm text-red-300'>{error}</div> : null}
      {!active ? <div className='text-sm text-slate-400'>Select a thread to view details.</div> : <div className='space-y-3'>
        <div className='text-lg font-semibold'>{active.subject}</div>
        {(active.messages || []).map((m)=><div key={m.id} className='rounded border border-slate-800 p-2'><div className='text-xs text-slate-400'>{m.sender_type}</div><div>{m.body}</div></div>)}
        <form onSubmit={async(e)=>{e.preventDefault(); await api.replyMessageThread(active.id, replyBody); setReplyBody(''); setActive(await api.getMessageThread(active.id)); await load();}} className='space-y-2'>
          <textarea value={replyBody} onChange={(e)=>setReplyBody(e.target.value)} required className='min-h-24 w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm' placeholder='Reply' />
          <button className='rounded bg-slate-700 px-3 py-1.5 text-sm'>Reply</button>
        </form>
      </div>}
    </div>
  </div>;
}
