import { useMemo, useState } from 'react';
import { useActivatePromptTemplate, useAdminPromptTemplates, useCreatePromptTemplate, useTestPromptTemplate, useUpdatePromptTemplate } from '@/hooks/useApi';
import { getErrorDetail } from '@/services/api';
import { useUIStore } from '@/store/uiStore';
import type { PromptTemplateType } from '@/types/api';

const promptTypes: PromptTemplateType[] = ['chat', 'retrieval', 'report', 'timeline_extraction', 'relationship_detection'];

export function AdminPromptTemplatesPage() {
  const prompts = useAdminPromptTemplates();
  const createPrompt = useCreatePromptTemplate();
  const updatePrompt = useUpdatePromptTemplate();
  const activatePrompt = useActivatePromptTemplate();
  const testPrompt = useTestPromptTemplate();
  const { pushToast } = useUIStore();
  const [createForm, setCreateForm] = useState({ prompt_type: 'chat' as PromptTemplateType, name: '', content: '' });
  const [selectedId, setSelectedId] = useState<string>('');
  const selectedPrompt = useMemo(() => prompts.data?.find((item) => item.id === selectedId) ?? null, [prompts.data, selectedId]);
  const [editForm, setEditForm] = useState({ name: '', content: '' });
  const [testForm, setTestForm] = useState({ prompt_type: 'chat' as PromptTemplateType, prompt_content: '', sample_context: '' });
  const [preview, setPreview] = useState('');
  const [previewError, setPreviewError] = useState('');

  if (prompts.isLoading) return <div>Loading prompt templates...</div>;
  if (prompts.isError) return <div>Failed to load prompt templates</div>;

  return <div className='space-y-4'>
    <h1 className='text-xl font-semibold'>Prompt Templates</h1>
    <div className='overflow-x-auto rounded border border-slate-800'>
      <table className='w-full text-sm'>
        <thead><tr className='text-left text-slate-300'><th className='p-2'>Type</th><th className='p-2'>Name</th><th className='p-2'>Version</th><th className='p-2'>Status</th><th className='p-2'>Updated</th><th className='p-2'>Created</th><th className='p-2'>Actions</th></tr></thead>
        <tbody>{prompts.data?.map((item) => <tr key={item.id} className='border-t border-slate-800'><td className='p-2'>{item.prompt_type}</td><td className='p-2'>{item.name}</td><td className='p-2'>v{item.version}</td><td className='p-2'>{item.is_active ? <span className='rounded bg-emerald-700 px-2 py-1 text-xs' data-testid={`active-badge-${item.id}`}>Active</span> : <span className='text-slate-400'>Inactive</span>}</td><td className='p-2'>{new Date(item.updated_at).toLocaleString()}</td><td className='p-2'>{new Date(item.created_at).toLocaleString()}</td><td className='p-2'><button className='mr-2 rounded bg-slate-700 px-2 py-1' onClick={() => { setSelectedId(item.id); setEditForm({ name: item.name, content: item.content }); }}>Edit</button><button className='rounded bg-indigo-700 px-2 py-1' onClick={async () => { try { await activatePrompt.mutateAsync(item.id); pushToast('Prompt activated'); } catch (e) { pushToast(getErrorDetail(e), 'error'); } }}>Activate</button></td></tr>)}</tbody>
      </table>
    </div>

    <div className='space-y-2 rounded border border-slate-800 p-3'>
      <h2 className='font-semibold'>Create template</h2>
      <select value={createForm.prompt_type} onChange={(e) => setCreateForm((v) => ({ ...v, prompt_type: e.target.value as PromptTemplateType }))} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm'>
        {promptTypes.map((type) => <option key={type} value={type}>{type}</option>)}
      </select>
      <input placeholder='Template name' value={createForm.name} onChange={(e) => setCreateForm((v) => ({ ...v, name: e.target.value }))} className='w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <textarea placeholder='Prompt content' value={createForm.content} onChange={(e) => setCreateForm((v) => ({ ...v, content: e.target.value }))} className='h-40 w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <button className='w-full rounded bg-emerald-700 px-3 py-2 text-sm sm:w-auto' onClick={async () => { try { await createPrompt.mutateAsync(createForm); pushToast('Prompt template created'); setCreateForm({ prompt_type: 'chat', name: '', content: '' }); } catch (e) { pushToast(getErrorDetail(e), 'error'); } }}>Create template</button>
    </div>


    <div className='space-y-2 rounded border border-slate-800 p-3'>
      <h2 className='font-semibold'>Test prompt</h2>
      <select value={testForm.prompt_type} onChange={(e) => setTestForm((v) => ({ ...v, prompt_type: e.target.value as PromptTemplateType }))} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm'>
        {promptTypes.map((type) => <option key={type} value={type}>{type}</option>)}
      </select>
      <textarea placeholder='Prompt content for preview' value={testForm.prompt_content} onChange={(e) => setTestForm((v) => ({ ...v, prompt_content: e.target.value }))} className='h-32 w-full min-w-0 rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <textarea placeholder='Sample context/query/document text' value={testForm.sample_context} onChange={(e) => setTestForm((v) => ({ ...v, sample_context: e.target.value }))} className='h-32 w-full min-w-0 rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <button className='w-full rounded bg-indigo-700 px-3 py-2 text-sm sm:w-auto' onClick={async () => {
        setPreview(''); setPreviewError('');
        if (!testForm.prompt_content.trim() || !testForm.sample_context.trim()) {
          setPreviewError('Prompt content and sample context are required.');
          return;
        }
        try {
          const resp = await testPrompt.mutateAsync(testForm);
          setPreview(resp.preview);
        } catch (e) {
          console.error('Prompt test request failed', (e as { response?: { data?: unknown } })?.response?.data ?? e);
          setPreviewError(getErrorDetail(e));
        }
      }} disabled={testPrompt.isPending || !testForm.prompt_content.trim() || !testForm.sample_context.trim()}>Run preview</button>
      {testPrompt.isPending && <div className='text-sm text-slate-300'>Generating preview...</div>}
      {previewError && <div className='text-sm text-rose-400' role='alert'>{previewError}</div>}
      {preview && <pre className='overflow-x-auto whitespace-pre-wrap break-words rounded border border-slate-700 bg-slate-950 p-2 text-sm'>{preview}</pre>}
    </div>

    {selectedPrompt && <div className='space-y-2 rounded border border-slate-800 p-3'>
      <h2 className='font-semibold'>Edit template</h2>
      <div className='text-xs text-slate-400'>{selectedPrompt.prompt_type} · v{selectedPrompt.version}</div>
      <input value={editForm.name} onChange={(e) => setEditForm((v) => ({ ...v, name: e.target.value }))} className='w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <textarea value={editForm.content} onChange={(e) => setEditForm((v) => ({ ...v, content: e.target.value }))} className='h-48 w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <button className='w-full rounded bg-indigo-700 px-3 py-2 text-sm sm:w-auto' onClick={async () => { try { await updatePrompt.mutateAsync({ promptId: selectedPrompt.id, payload: editForm }); pushToast('Prompt template saved'); } catch (e) { pushToast(getErrorDetail(e), 'error'); } }}>Save changes</button>
    </div>}
  </div>;
}
