import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useCreateChatSession, useChatSession, useChatSessions, useCreateReport, useInvalidateChatSession } from '@/hooks/useApi';
import { useUIStore } from '@/store/uiStore';
import { api, getErrorDetail } from '@/services/api';
import type { ChatMessage, SourceRef } from '@/types/api';

function CitationSection({ sourceRefs }: { sourceRefs: SourceRef[] }) {
  if (sourceRefs.length === 0) return null;

  return (
    <details className='mt-2 rounded border border-slate-700/80 bg-slate-900/40 p-2 text-xs' open>
      <summary className='cursor-pointer text-slate-300'>Citations ({sourceRefs.length})</summary>
      <div className='mt-2 space-y-2'>
        {sourceRefs.map((ref, index) => {
          const title = ref.document_title || ref.title || 'Untitled source';
          const typeLabel = ref.source_type || ref.kind || null;
          const snippet = ref.snippet || ref.preview || null;
          const card = (
            <div className='rounded border border-slate-700 bg-slate-900/70 p-2'>
              <div className='font-medium text-cyan-300'>{title}</div>
              {typeLabel && <div className='mt-1 text-[11px] uppercase tracking-wide text-slate-400'>{typeLabel}</div>}
              {snippet && <div className='mt-1 text-slate-300'>{snippet}</div>}
            </div>
          );
          if (ref.document_id) {
            return <Link key={`${ref.document_id}-${index}`} className='block' to={`/documents/${ref.document_id}`}>{card}</Link>;
          }
          return <div key={`citation-${index}`}>{card}</div>;
        })}
      </div>
    </details>
  );
}

export function ChatPage() {
  const { pushToast } = useUIStore();
  const sessions = useChatSessions();
  const createSession = useCreateChatSession();
  const [sessionId, setSessionId] = useState('');
  const currentSessionId = sessionId || sessions.data?.[0]?.id || '';
  const session = useChatSession(currentSessionId);
  const invalidateChatSession = useInvalidateChatSession();
  const createReport = useCreateReport();
  const [message, setMessage] = useState('');
  const [docIds, setDocIds] = useState('');
  const [includeTimeline, setIncludeTimeline] = useState(true);
  const [includeFullText, setIncludeFullText] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [streamingSourceRefs, setStreamingSourceRefs] = useState<SourceRef[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const ids = useMemo(() => docIds.split(',').map((d) => d.trim()).filter(Boolean), [docIds]);

  const onNew = async () => { const s = await createSession.mutateAsync(undefined); setSessionId(s.id); };
  const onSend = async () => {
    try {
      setStreamError(null);
      let sid = currentSessionId;
      if (!sid) { const s = await createSession.mutateAsync(undefined); sid = s.id; setSessionId(sid); }
      setIsStreaming(true);
      setStreamingMessage('');
      setStreamingSourceRefs([]);
      await api.sendChatMessageStream(sid, { message, document_ids: ids, include_timeline: includeTimeline, include_full_text: includeFullText }, {
        onEvent: (event) => {
          if (event.type === 'chunk') {
            setStreamingMessage((prev) => prev + event.content);
          }
          if (event.type === 'final') {
            setStreamingMessage(event.content);
            setStreamingSourceRefs(event.source_refs || []);
          }
        },
      });
      invalidateChatSession(sid);
      setMessage('');
    } catch (e) {
      const detail = getErrorDetail(e);
      setStreamError(detail);
      pushToast(detail.includes('503') ? 'OpenAI unavailable. Please retry shortly.' : detail, 'error');
    } finally {
      setIsStreaming(false);
    }
  };

  const messages: ChatMessage[] = session.data?.messages || [];

  return <div className='grid gap-4 md:grid-cols-[260px_minmax(0,1fr)]'>
    <div className='space-y-3'><button onClick={onNew} className='rounded bg-slate-700 px-3 py-2 text-sm'>New Chat</button>
      {(sessions.data||[]).map(s => <button key={s.id} onClick={()=>setSessionId(s.id)} className='block w-full rounded border border-slate-700 p-2 text-left text-sm'>{s.title || `Session ${s.id.slice(0,8)}`}</button>)}
    </div>
    <div className='space-y-3'>
      <h1 className='text-xl font-semibold'>Chat</h1>
      <div className='rounded border border-slate-700 p-3 space-y-3'>
        {messages.map(m => <div key={m.id}><div className='text-xs uppercase text-slate-400'>{m.role}</div><div>{m.content}</div>{m.role==='assistant' && <CitationSection sourceRefs={m.source_refs || []} />}</div>)}
        {isStreaming && <div data-testid='streaming-message'><div className='text-xs uppercase text-slate-400'>assistant</div><div>{streamingMessage || 'Streaming response...'}</div><CitationSection sourceRefs={streamingSourceRefs} /></div>}
        {streamError && <div className='text-sm text-rose-400'>Streaming failed. Retry sending your message. ({streamError})</div>}
        {(session.isLoading || isStreaming) && <div>{isStreaming ? 'Streaming...' : 'Loading...'}</div>}
      </div>
      <textarea disabled={isStreaming} value={message} onChange={(e)=>setMessage(e.target.value)} className='w-full rounded border border-slate-700 bg-slate-900 p-2' placeholder='Ask a question' />
      <input value={docIds} onChange={(e)=>setDocIds(e.target.value)} placeholder='Document IDs comma-separated (optional)' className='w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm'/>
      <label><input type='checkbox' checked={includeTimeline} onChange={(e)=>setIncludeTimeline(e.target.checked)} /> include timeline</label>
      <label className='ml-3'><input type='checkbox' checked={includeFullText} onChange={(e)=>setIncludeFullText(e.target.checked)} /> include full text</label>
      <div className='flex gap-2'><button disabled={isStreaming} onClick={onSend} className='rounded bg-indigo-700 px-3 py-2 text-sm disabled:opacity-60'>Send</button><button onClick={async()=>{if(!currentSessionId) return; await createReport.mutateAsync({ title:'Chat report', prompt:'Generate report from this conversation', include_timeline: includeTimeline, include_full_text: includeFullText, document_ids: ids }); pushToast('Report generated');}} className='rounded bg-emerald-700 px-3 py-2 text-sm'>Generate report from this conversation/answer</button></div>
    </div>
  </div>;
}
