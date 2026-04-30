import { useState } from 'react';
import { useChatbotSettings, useResetChatbotSettings, useUpdateChatbotSettings } from '@/hooks/useApi';
import { useUIStore } from '@/store/uiStore';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { getErrorDetail } from '@/services/api';
import type { ChatbotSettings } from '@/types/api';

const textFields: Array<keyof Pick<ChatbotSettings, 'system_prompt'|'retrieval_prompt'|'report_prompt'|'citation_prompt'|'default_report_template'|'model'>> = [
  'system_prompt','retrieval_prompt','report_prompt','citation_prompt','default_report_template','model',
];

export function AdminChatbotSettingsPage() {
  const settings = useChatbotSettings();
  const update = useUpdateChatbotSettings();
  const reset = useResetChatbotSettings();
  const { pushToast } = useUIStore();
  const [showConfirm, setShowConfirm] = useState(false);
  const [form, setForm] = useState<ChatbotSettings | null>(null);
  const v = form ?? settings.data;
  if (settings.isLoading) return <div>Loading...</div>;
  if (settings.isError || !v) return <div>Failed to load settings</div>;
  const set = <K extends keyof ChatbotSettings>(k: K, val: ChatbotSettings[K]) => setForm((f) => ({ ...(f ?? settings.data!), [k]: val }));

  return <div className='space-y-3'><h1 className='text-xl font-semibold'>Chatbot Settings</h1>
    {textFields.map((k) => <textarea key={k} value={v[k]} onChange={(e) => set(k, e.target.value)} className='w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />)}
    <input value={v.temperature} type='number' onChange={(e) => set('temperature', Number(e.target.value))} />
    <input value={v.max_tokens} type='number' onChange={(e) => set('max_tokens', Number(e.target.value))} />
    <input value={v.max_documents} type='number' onChange={(e) => set('max_documents', Number(e.target.value))} />
    <label><input type='checkbox' checked={v.allow_full_text_retrieval} onChange={(e) => set('allow_full_text_retrieval', e.target.checked)} />allow full text retrieval</label>
    <div className='flex gap-2'><button onClick={async () => { try { await update.mutateAsync(v); pushToast('Settings saved'); } catch (e) { pushToast(getErrorDetail(e), 'error'); } }} className='rounded bg-indigo-700 px-3 py-2 text-sm'>Save</button><button onClick={() => setShowConfirm(true)} className='rounded bg-red-700 px-3 py-2 text-sm'>Reset defaults</button></div>
    <ConfirmModal open={showConfirm} title='Reset defaults' description='Reset chatbot settings?' onCancel={() => setShowConfirm(false)} onConfirm={async () => { await reset.mutateAsync(); pushToast('Defaults restored'); setShowConfirm(false); }} />
  </div>;
}
