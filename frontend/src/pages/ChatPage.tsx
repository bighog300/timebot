import { useMemo, useState } from 'react';
import { useAssistants, useChatSession, useChatSessions, useCreateChatSession, useDeleteChatSession, useUpdateChatSession } from '@/hooks/useApi';
import { api, getErrorDetail } from '@/services/api';
import { useUIStore } from '@/store/uiStore';
import { UpgradePrompt } from '@/components/billing/UpgradePrompt';
import type { ChatSession } from '@/types/api';

export function ChatPage() {
  const { pushToast } = useUIStore();
  const sessions = useChatSessions();
  const assistants = useAssistants();
  const createSession = useCreateChatSession();
  const updateSession = useUpdateChatSession();
  const deleteSession = useDeleteChatSession();
  const [sessionId, setSessionId] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState('New chat');
  const [assistantId, setAssistantId] = useState('');
  const [promptTemplateId, setPromptTemplateId] = useState('');
  const [linkedDocuments, setLinkedDocuments] = useState('');
  const [message, setMessage] = useState('');
  const [monetizationError, setMonetizationError] = useState<string | null>(null);

  const currentSessionId = sessionId || sessions.data?.find((s) => !s.is_archived)?.id || '';
  const session = useChatSession(currentSessionId);
  const activeChats = (sessions.data || []).filter((s) => !s.is_archived && !s.is_deleted);
  const archivedChats = (sessions.data || []).filter((s) => s.is_archived && !s.is_deleted);

  const assistantMap = useMemo(() => new Map((assistants.data || []).map((a) => [a.id, a])), [assistants.data]);
  const selectedAssistant = session.data?.assistant_id ? assistantMap.get(session.data.assistant_id) : undefined;
  const lastAssistantMessage = [...(session.data?.messages || [])].reverse().find((m) => m.role === 'assistant');

  const onCreate = async () => {
    const created = await createSession.mutateAsync({ title, assistant_id: assistantId || null, prompt_template_id: promptTemplateId || null, linked_document_ids: linkedDocuments.split(',').map((x) => x.trim()).filter(Boolean) });
    setSessionId(created.id);
    setShowCreate(false);
  };

  const onSend = async () => {
    if (!currentSessionId || session.data?.is_archived || session.data?.is_deleted) return;
    try {
      setMonetizationError(null);
      await api.sendChatMessageStream(currentSessionId, { message }, { onEvent: () => undefined });
      setMessage('');
    } catch (e) {
      const detail = getErrorDetail(e);
      if (detail.includes('402') || detail.includes('upgrade_required')) {
        setMonetizationError('Upgrade required to use this assistant/template.');
      }
      pushToast(detail, 'error');
    }
  };

  const renameChat = async (s: ChatSession) => {
    const next = window.prompt('Rename chat', s.title || '');
    if (!next) return;
    await updateSession.mutateAsync({ sessionId: s.id, payload: { title: next } });
  };

  return <div className='grid grid-cols-[280px_1fr_300px] gap-3'>
    <aside className='space-y-3'>
      <button className='rounded bg-slate-700 px-3 py-2 text-sm' onClick={() => setShowCreate(true)}>New Chat</button>
      <div><h3 className='text-xs uppercase text-slate-400'>Active chats</h3>{activeChats.map((s) => <div key={s.id} className='mt-2 rounded border border-slate-700 p-2'><button className='block w-full text-left' onClick={() => setSessionId(s.id)}>{s.title || 'Untitled'}</button><div className='mt-1 flex gap-1 text-xs'><button onClick={() => renameChat(s)}>Rename</button><button onClick={() => updateSession.mutate({ sessionId: s.id, payload: { is_archived: true } })}>Archive</button><button onClick={() => window.confirm('Delete chat?') && deleteSession.mutate(s.id)}>Delete</button></div></div>)}</div>
      <div><h3 className='text-xs uppercase text-slate-400'>Archived chats</h3>{archivedChats.map((s) => <button key={s.id} className='mt-2 block w-full rounded border border-slate-700 p-2 text-left' onClick={() => setSessionId(s.id)}>{s.title || 'Untitled'}</button>)}</div>
    </aside>
    <main>
      <h1 className='text-xl font-semibold'>Chat {selectedAssistant ? <span className='ml-2 rounded bg-slate-800 px-2 py-1 text-sm'>Assistant: {selectedAssistant.name}</span> : null}</h1>
      {monetizationError ? <UpgradePrompt title='Upgrade required' message={monetizationError} /> : null}
      <div className='mt-3 min-h-72 space-y-2 rounded border border-slate-700 p-3'>{(session.data?.messages || []).map((m) => <div key={m.id}><b>{m.role}:</b> {m.content}</div>)}</div>
      {(session.data?.is_archived || session.data?.is_deleted) ? <div className='mt-2 text-amber-300'>This chat is archived/deleted and read-only.</div> : null}
      <div className='mt-2 flex gap-2'><textarea disabled={Boolean(session.data?.is_archived || session.data?.is_deleted)} value={message} onChange={(e) => setMessage(e.target.value)} placeholder='Ask a question' className='w-full rounded border border-slate-700 bg-slate-900 p-2' /><button onClick={onSend} disabled={Boolean(session.data?.is_archived || session.data?.is_deleted)} className='rounded bg-indigo-700 px-3'>Send</button></div>
    </main>
    <aside className='rounded border border-slate-700 p-3'>
      <h3 className='font-medium'>Context</h3>
      <div className='mt-2 text-sm'>Assistant: {selectedAssistant?.name || 'None'}</div>
      <div className='text-sm'>Prompt template: {session.data?.prompt_template_id || 'None'}</div>
      <div className='text-sm'>Linked docs: {(session.data?.linked_document_ids || []).join(', ') || 'None'}</div>
      <div className='mt-2 text-sm'>User evidence refs: {((lastAssistantMessage?.metadata_json?.user_evidence_refs as { document_title?: string }[]|undefined) || []).map((r) => r.document_title || 'Untitled').join(', ') || 'None'}</div>
      <div className='text-sm'>System intelligence refs: {((lastAssistantMessage?.metadata_json?.system_intelligence_refs as { title?: string }[]|undefined) || []).map((r) => r.title || 'Untitled').join(', ') || 'None'}</div>
      <div className='text-sm'>Legal web refs: {((lastAssistantMessage?.metadata_json?.legal_web_refs as { title?: string }[]|undefined) || []).map((r) => r.title || 'Untitled').join(', ') || 'None'}</div>
    </aside>
    {showCreate && <div className='fixed inset-0 bg-black/60 p-6'><div className='mx-auto max-w-lg rounded bg-slate-900 p-4'><h2 className='text-lg'>Create chat</h2><input className='mt-2 w-full rounded border border-slate-700 bg-slate-800 p-2' value={title} onChange={(e) => setTitle(e.target.value)} placeholder='title' /><select className='mt-2 w-full rounded border border-slate-700 bg-slate-800 p-2' value={assistantId} onChange={(e) => setAssistantId(e.target.value)}><option value=''>Select assistant</option>{(assistants.data || []).map((a) => <option key={a.id} value={a.id}>{a.name}{a.required_plan !== 'free' ? ' 🔒 Pro' : ''}</option>)}</select><input className='mt-2 w-full rounded border border-slate-700 bg-slate-800 p-2' value={promptTemplateId} onChange={(e) => setPromptTemplateId(e.target.value)} placeholder='prompt template id' /><input className='mt-2 w-full rounded border border-slate-700 bg-slate-800 p-2' value={linkedDocuments} onChange={(e) => setLinkedDocuments(e.target.value)} placeholder='linked documents comma-separated' /><div className='mt-3 flex justify-end gap-2'><button onClick={() => setShowCreate(false)}>Cancel</button><button onClick={onCreate} className='rounded bg-indigo-700 px-3 py-1'>Create</button></div></div></div>}
  </div>;
}
