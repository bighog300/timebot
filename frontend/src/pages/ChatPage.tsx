import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useCreateChatSession, useChatSession, useChatSessions, useSendChatMessage, useCreateReport } from '@/hooks/useApi';
import { useUIStore } from '@/store/uiStore';
import { getErrorDetail } from '@/services/api';

export function ChatPage() {
  const { pushToast } = useUIStore();
  const sessions = useChatSessions();
  const createSession = useCreateChatSession();
  const [sessionId, setSessionId] = useState('');
  const currentSessionId = sessionId || sessions.data?.[0]?.id || '';
  const session = useChatSession(currentSessionId);
  const send = useSendChatMessage(currentSessionId);
  const createReport = useCreateReport();
  const [message, setMessage] = useState('');
  const [docIds, setDocIds] = useState('');
  const [includeTimeline, setIncludeTimeline] = useState(true);
  const [includeFullText, setIncludeFullText] = useState(false);
  const ids = useMemo(() => docIds.split(',').map((d) => d.trim()).filter(Boolean), [docIds]);

  const onNew = async () => { const s = await createSession.mutateAsync(undefined); setSessionId(s.id); };
  const onSend = async () => {
    try {
      let sid = currentSessionId;
      if (!sid) { const s = await createSession.mutateAsync(undefined); sid = s.id; setSessionId(sid); }
      await send.mutateAsync({ message, document_ids: ids, include_timeline: includeTimeline, include_full_text: includeFullText });
      setMessage('');
    } catch (e) {
      const detail = getErrorDetail(e);
      pushToast(detail.includes('503') ? 'OpenAI unavailable. Please retry shortly.' : detail, 'error');
    }
  };

  return <div className='grid gap-4 md:grid-cols-[260px_minmax(0,1fr)]'>
    <div className='space-y-3'><button onClick={onNew} className='rounded bg-slate-700 px-3 py-2 text-sm'>New Chat</button>
      {(sessions.data||[]).map(s => <button key={s.id} onClick={()=>setSessionId(s.id)} className='block w-full rounded border border-slate-700 p-2 text-left text-sm'>{s.title || `Session ${s.id.slice(0,8)}`}</button>)}
    </div>
    <div className='space-y-3'>
      <h1 className='text-xl font-semibold'>Chat</h1>
      <div className='rounded border border-slate-700 p-3 space-y-3'>
        {(session.data?.messages||[]).map(m => <div key={m.id}><div className='text-xs uppercase text-slate-400'>{m.role}</div><div>{m.content}</div>{m.role==='assistant' && (m.source_refs?.length||0)>0 && <div className='mt-2 text-xs'><div>Sources</div>{m.source_refs?.map((r,i)=><Link className='block text-cyan-300' key={i} to={`/documents/${r.document_id}`}>{r.document_title}</Link>)}</div>}</div>)}
        {(session.isLoading || send.isPending) && <div>Loading...</div>}
      </div>
      <textarea value={message} onChange={(e)=>setMessage(e.target.value)} className='w-full rounded border border-slate-700 bg-slate-900 p-2' placeholder='Ask a question' />
      <input value={docIds} onChange={(e)=>setDocIds(e.target.value)} placeholder='Document IDs comma-separated (optional)' className='w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm'/>
      <label><input type='checkbox' checked={includeTimeline} onChange={(e)=>setIncludeTimeline(e.target.checked)} /> include timeline</label>
      <label className='ml-3'><input type='checkbox' checked={includeFullText} onChange={(e)=>setIncludeFullText(e.target.checked)} /> include full text</label>
      <div className='flex gap-2'><button onClick={onSend} className='rounded bg-indigo-700 px-3 py-2 text-sm'>Send</button><button onClick={async()=>{if(!currentSessionId) return; await createReport.mutateAsync({ title:'Chat report', prompt:'Generate report from this conversation', include_timeline: includeTimeline, include_full_text: includeFullText, document_ids: ids }); pushToast('Report generated');}} className='rounded bg-emerald-700 px-3 py-2 text-sm'>Generate report from this conversation/answer</button></div>
    </div>
  </div>;
}
