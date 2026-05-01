import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useCreateChatSession, useChatSession, useChatSessions, useCreateReport, useInvalidateChatSession } from '@/hooks/useApi';
import { useUIStore } from '@/store/uiStore';
import { api, getErrorDetail } from '@/services/api';
import type { ChatMessage, SourceRef } from '@/types/api';

type FollowUpContext = {
  includeTimeline: boolean;
  includeFullText: boolean;
  sourceRefCount: number;
};

function getFollowUpSuggestions(context: FollowUpContext): string[] {
  const suggestions = new Set<string>([
    'What are the key risks?',
    'Are there inconsistencies?',
    'Generate a report from this answer',
  ]);

  if (context.includeTimeline) suggestions.add('What changed over time?');
  if (context.sourceRefCount > 0) suggestions.add('Which documents support this?');
  if (context.includeFullText) suggestions.add('What important details might be missing?');

  return Array.from(suggestions);
}

function FollowUpSuggestions({
  suggestions,
  onSelect,
}: {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
}) {
  if (suggestions.length === 0) return null;

  return (
    <div className='mt-2 space-y-2'>
      <div className='text-xs uppercase tracking-wide text-slate-400'>Suggested follow-ups</div>
      <div className='flex flex-wrap gap-2'>
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            type='button'
            onClick={() => onSelect(suggestion)}
            className='rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-200 hover:border-slate-500'
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}

function CitationSection({ sourceRefs }: { sourceRefs: SourceRef[] }) {
  if (sourceRefs.length === 0) return null;

  return (
    <details className='mt-2 rounded border border-slate-700/80 bg-slate-900/40 p-2 text-xs' open>
      <summary className='cursor-pointer text-slate-300'>Citations ({sourceRefs.length})</summary>
      <div className='mt-2 grid gap-2 sm:grid-cols-2'>
        {sourceRefs.map((ref, index) => {
          const title = ref.document_title || ref.title || 'Untitled source';
          const typeLabel = ref.source_type || ref.kind || null;
          const snippet = ref.snippet || ref.preview || null;
          const card = (
            <div className='h-full rounded border border-slate-700 bg-slate-900/70 p-2'>
              <div className='break-words font-medium text-cyan-300'>{title}</div>
              {typeLabel && <div className='mt-1 text-[11px] uppercase tracking-wide text-slate-400'>{typeLabel}</div>}
              {snippet && <div className='mt-1 break-words text-slate-300'>{snippet}</div>}
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
  const [hasStreamFinal, setHasStreamFinal] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const chunkBufferRef = useRef('');
  const frameRef = useRef<number | null>(null);
  const hasFinalEventRef = useRef(false);
  const ids = useMemo(() => docIds.split(',').map((d) => d.trim()).filter(Boolean), [docIds]);

  useEffect(() => () => {
    if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
  }, []);

  const flushChunkBuffer = () => {
    if (!chunkBufferRef.current) return;
    const buffer = chunkBufferRef.current;
    chunkBufferRef.current = '';
    setStreamingMessage((prev) => prev + buffer);
  };

  const onNew = async () => { const s = await createSession.mutateAsync(undefined); setSessionId(s.id); };
  const onSend = async () => {
    try {
      setStreamError(null);
      let sid = currentSessionId;
      if (!sid) { const s = await createSession.mutateAsync(undefined); sid = s.id; setSessionId(sid); }
      setIsStreaming(true);
      hasFinalEventRef.current = false;
      setHasStreamFinal(false);
      setStreamingMessage('');
      setStreamingSourceRefs([]);
      await api.sendChatMessageStream(sid, { message, document_ids: ids, include_timeline: includeTimeline, include_full_text: includeFullText }, {
        onEvent: (event) => {
          if (event.type === 'chunk') {
            chunkBufferRef.current += event.content;
            if (frameRef.current === null) {
              frameRef.current = window.requestAnimationFrame(() => {
                flushChunkBuffer();
                frameRef.current = null;
              });
            }
          }
          if (event.type === 'final') {
            hasFinalEventRef.current = true;
            if (frameRef.current !== null) {
              window.cancelAnimationFrame(frameRef.current);
              frameRef.current = null;
            }
            flushChunkBuffer();
            setStreamingMessage(event.content);
            setStreamingSourceRefs(event.source_refs || []);
            setHasStreamFinal(true);
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
      if (!hasFinalEventRef.current && frameRef.current !== null) {
        window.cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
        flushChunkBuffer();
      }
      setIsStreaming(false);
    }
  };

  const messages: ChatMessage[] = session.data?.messages || [];

  return <div className='grid min-h-[calc(100vh-8rem)] gap-4 md:grid-cols-[260px_minmax(0,1fr)]'>
    <div className='space-y-3'>
      <button onClick={onNew} className='rounded bg-slate-700 px-3 py-2 text-sm'>New Chat</button>
      <div className='grid max-h-52 gap-2 overflow-auto pr-1 md:max-h-none'>
        {(sessions.data || []).map((s) => <button key={s.id} onClick={() => setSessionId(s.id)} className='block w-full rounded border border-slate-700 p-2 text-left text-sm'>{s.title || `Session ${s.id.slice(0, 8)}`}</button>)}
      </div>
    </div>
    <div className='flex min-h-0 flex-col space-y-3'>
      <h1 className='text-xl font-semibold'>Chat</h1>
      <div data-testid='chat-message-list' className='min-h-[18rem] flex-1 space-y-3 overflow-y-auto rounded border border-slate-700 p-3'>
        {messages.map((m) => <div key={m.id} className='rounded bg-slate-900/40 p-2'><div className='text-xs uppercase text-slate-400'>{m.role}</div><div className='whitespace-pre-wrap break-words'>{m.content}</div>{m.role === 'assistant' && <><CitationSection sourceRefs={m.source_refs || []} /><FollowUpSuggestions suggestions={getFollowUpSuggestions({ includeTimeline, includeFullText, sourceRefCount: (m.source_refs || []).length })} onSelect={setMessage} /></>}</div>)}
        {isStreaming && <div data-testid='streaming-message' className='rounded bg-slate-900/40 p-2'><div className='text-xs uppercase text-slate-400'>assistant</div><div className='min-h-[4rem] whitespace-pre-wrap break-words leading-relaxed'>{streamingMessage || ' '}</div>{!hasStreamFinal && <div data-testid='streaming-indicator' aria-live='polite' className='mt-2 inline-flex items-center gap-1 text-xs text-slate-400'><span className='h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400 [animation-delay:0ms]' /><span className='h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400 [animation-delay:120ms]' /><span className='h-1.5 w-1.5 animate-pulse rounded-full bg-slate-400 [animation-delay:240ms]' /><span>Assistant is typing</span></div>}<CitationSection sourceRefs={streamingSourceRefs} />{hasStreamFinal && <FollowUpSuggestions suggestions={getFollowUpSuggestions({ includeTimeline, includeFullText, sourceRefCount: streamingSourceRefs.length })} onSelect={setMessage} />}</div>}
        {streamError && <div className='text-sm text-rose-400'>Streaming failed. Retry sending your message. ({streamError})</div>}
        {(session.isLoading || isStreaming) && <div>{isStreaming ? 'Streaming...' : 'Loading...'}</div>}
      </div>
      <div data-testid='chat-input-panel' className='sticky bottom-0 z-10 space-y-2 rounded border border-slate-700 bg-slate-950/95 p-2 backdrop-blur'>
        <textarea disabled={isStreaming} value={message} onChange={(e) => setMessage(e.target.value)} className='max-h-40 w-full rounded border border-slate-700 bg-slate-900 p-2' placeholder='Ask a question' />
        <input value={docIds} onChange={(e) => setDocIds(e.target.value)} placeholder='Document IDs comma-separated (optional)' className='w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
        <div className='flex flex-wrap items-center gap-3'>
          <label><input type='checkbox' checked={includeTimeline} onChange={(e) => setIncludeTimeline(e.target.checked)} /> include timeline</label>
          <label><input type='checkbox' checked={includeFullText} onChange={(e) => setIncludeFullText(e.target.checked)} /> include full text</label>
        </div>
        <div className='flex flex-wrap gap-2'>
          <button disabled={isStreaming} onClick={onSend} className='rounded bg-indigo-700 px-3 py-2 text-sm disabled:opacity-60'>Send</button>
          <button onClick={async () => { if (!currentSessionId) return; await createReport.mutateAsync({ title: 'Chat report', prompt: 'Generate report from this conversation', include_timeline: includeTimeline, include_full_text: includeFullText, document_ids: ids }); pushToast('Report generated'); }} className='rounded bg-emerald-700 px-3 py-2 text-sm'>Generate report from this conversation/answer</button>
        </div>
      </div>
    </div>
  </div>;
}
