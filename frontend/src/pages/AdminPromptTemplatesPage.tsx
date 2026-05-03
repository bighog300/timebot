import { useMemo, useState } from 'react';
import { useActivatePromptTemplate, useAdminLlmModels, useAdminPromptTemplates, useCreatePromptTemplate, useTestPromptTemplate, useUpdatePromptTemplate } from '@/hooks/useApi';
import { getErrorDetail } from '@/services/api';
import { useUIStore } from '@/store/uiStore';
import type { LlmProviderCatalog, PromptTemplate, PromptTemplateTestResponse, PromptTemplateType } from '@/types/api';

const promptTypes: PromptTemplateType[] = ['chat', 'retrieval', 'report', 'timeline_extraction', 'relationship_detection'];

type PromptFormState = { prompt_type: PromptTemplateType; name: string; content: string; provider: 'openai' | 'gemini'; model: string; temperature: number; max_tokens: number; top_p: number; enabled: boolean; is_default: boolean; fallback_enabled: boolean; fallback_order: 'provider_then_model'|'model_then_provider'; max_fallback_attempts: number; retry_on_provider_errors: boolean; retry_on_rate_limit: boolean; retry_on_validation_error: boolean; fallback_provider: 'openai' | 'gemini' | null; fallback_model: string | null };
const EMPTY_CREATE_FORM: PromptFormState = { prompt_type: 'chat', name: '', content: '', provider: 'openai', model: 'gpt-4o-mini', temperature: 0.2, max_tokens: 800, top_p: 1, enabled: true, is_default: false, fallback_enabled: false, fallback_order: 'provider_then_model', max_fallback_attempts: 1, retry_on_provider_errors: true, retry_on_rate_limit: true, retry_on_validation_error: false, fallback_provider: 'openai', fallback_model: 'gpt-4.1-mini' };
const toEditForm = (item: PromptTemplate): PromptFormState => ({ prompt_type: item.prompt_type, name: item.name, content: item.content, provider: item.provider ?? 'openai', model: item.model ?? 'gpt-4o-mini', temperature: item.temperature ?? 0.2, max_tokens: item.max_tokens ?? 800, top_p: item.top_p ?? 1, enabled: item.enabled ?? true, is_default: item.is_default ?? false, fallback_enabled: item.fallback_enabled ?? false, fallback_order: item.fallback_order ?? 'provider_then_model', max_fallback_attempts: item.max_fallback_attempts ?? 1, retry_on_provider_errors: item.retry_on_provider_errors ?? true, retry_on_rate_limit: item.retry_on_rate_limit ?? true, retry_on_validation_error: item.retry_on_validation_error ?? false, fallback_provider: item.fallback_provider ?? 'openai', fallback_model: item.fallback_model ?? 'gpt-4.1-mini' });

export function AdminPromptTemplatesPage() {
  const prompts = useAdminPromptTemplates();
  const llmModels = useAdminLlmModels();
  const createPrompt = useCreatePromptTemplate();
  const updatePrompt = useUpdatePromptTemplate();
  const activatePrompt = useActivatePromptTemplate();
  const testPrompt = useTestPromptTemplate();
  const { pushToast } = useUIStore();
  const [createForm, setCreateForm] = useState<PromptFormState>({ ...EMPTY_CREATE_FORM });
  const [selectedId, setSelectedId] = useState<string>('');
  const selectedPrompt = useMemo(() => prompts.data?.find((item) => item.id === selectedId) ?? null, [prompts.data, selectedId]);
  const [editForm, setEditForm] = useState<PromptFormState>({ ...EMPTY_CREATE_FORM });
  const [testForm, setTestForm] = useState<{ prompt_type: PromptTemplateType; prompt_content: string; sample_context: string; provider: 'openai' | 'gemini'; model: string; temperature: number; max_tokens: number; top_p: number; fallback_enabled: boolean; fallback_order: 'provider_then_model'|'model_then_provider'; max_fallback_attempts: number; retry_on_provider_errors: boolean; retry_on_rate_limit: boolean; retry_on_validation_error: boolean; fallback_provider: 'openai' | 'gemini' | null; fallback_model: string | null }>({ prompt_type: 'chat', prompt_content: '', sample_context: '', provider: 'openai', model: 'gpt-4o-mini', temperature: 0.2, max_tokens: 800, top_p: 1, fallback_enabled: false, fallback_order: 'provider_then_model', max_fallback_attempts: 1, retry_on_provider_errors: true, retry_on_rate_limit: true, retry_on_validation_error: false, fallback_provider: 'openai', fallback_model: 'gpt-4.1-mini' });
  const [preview, setPreview] = useState('');
  const [previewMeta, setPreviewMeta] = useState<PromptTemplateTestResponse | null>(null);
  const [previewError, setPreviewError] = useState('');
  const providerCatalog: LlmProviderCatalog[] = llmModels.data?.providers ?? [];
  const getModelsForProvider = (providerId: 'openai' | 'gemini') => providerCatalog.find((provider) => provider.id === providerId)?.models ?? [];


  if (prompts.isLoading || llmModels.isLoading) return <div>Loading prompt templates...</div>;
  if (prompts.isError || llmModels.isError) return <div>Failed to load prompt templates</div>;

  return <div className='space-y-4'>
    <h1 className='text-xl font-semibold'>Prompt Templates</h1>
    <div className='overflow-x-auto rounded border border-slate-800'>
      <table className='w-full text-sm'>
        <thead><tr className='text-left text-slate-300'><th className='p-2'>Type</th><th className='p-2'>Name</th><th className='p-2'>Version</th><th className='p-2'>Status</th><th className='p-2'>Updated</th><th className='p-2'>Created</th><th className='p-2'>Actions</th></tr></thead>
        <tbody>{prompts.data?.map((item) => <tr key={item.id} className='border-t border-slate-800'><td className='p-2'>{item.prompt_type}</td><td className='p-2'>{item.name}</td><td className='p-2'>v{item.version}</td><td className='p-2'>{item.is_active ? <span className='rounded bg-emerald-700 px-2 py-1 text-xs' data-testid={`active-badge-${item.id}`}>Active</span> : <span className='text-slate-400'>Inactive</span>}</td><td className='p-2'>{new Date(item.updated_at).toLocaleString()}</td><td className='p-2'>{new Date(item.created_at).toLocaleString()}</td><td className='p-2'><button className='mr-2 rounded bg-slate-700 px-2 py-1' onClick={() => { setSelectedId(item.id); setEditForm(toEditForm(item)); }}>Edit</button><button className='rounded bg-indigo-700 px-2 py-1 disabled:cursor-not-allowed disabled:opacity-60' disabled={item.is_active} onClick={async () => { if (item.is_active) return; try { await activatePrompt.mutateAsync(item.id); pushToast('Prompt activated'); } catch (e) { pushToast(getErrorDetail(e), 'error'); } }}>{item.is_active ? 'Active' : 'Activate'}</button></td></tr>)}</tbody>
      </table>
    </div>

    <div className='space-y-2 rounded border border-slate-800 p-3'>
      <h2 className='font-semibold'>Create template</h2>
      <select value={createForm.prompt_type} onChange={(e) => setCreateForm((v) => ({ ...v, prompt_type: e.target.value as PromptTemplateType }))} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm'>
        {promptTypes.map((type) => <option key={type} value={type}>{type}</option>)}
      </select>
      <input placeholder='Template name' value={createForm.name} onChange={(e) => setCreateForm((v) => ({ ...v, name: e.target.value }))} className='w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      
      <div className='grid grid-cols-2 gap-2'>
      <select value={createForm.provider} onChange={(e) => {
        const provider = e.target.value as 'openai' | 'gemini';
        const nextModels = getModelsForProvider(provider);
        setCreateForm((v) => ({ ...v, provider, model: nextModels[0]?.id ?? '' }));
      }} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm'>
        {providerCatalog.map((provider) => <option key={provider.id} value={provider.id} disabled={!provider.configured}>{provider.name}{provider.configured ? '' : ' (Unavailable)'}</option>)}
      </select>
      <select value={createForm.model} onChange={(e)=>setCreateForm((v)=>({...v, model:e.target.value}))} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm'>
        {getModelsForProvider(createForm.provider).map((model)=> <option key={model.id} value={model.id}>{model.name}</option>)}
      </select>
      </div>

      <label className='flex items-center gap-2 text-sm'><input type='checkbox' checked={createForm.is_default} onChange={(e)=>setCreateForm((v)=>({...v, is_default: e.target.checked}))} />Set as default (one per purpose)</label>
      <label className='flex items-center gap-2 text-sm'><input type='checkbox' checked={createForm.fallback_enabled} onChange={(e)=>setCreateForm((v)=>({...v, fallback_enabled: e.target.checked}))} />Enable fallback</label>
      <div className='grid grid-cols-2 gap-2'>
      <select value={createForm.fallback_provider ?? ''} disabled={!createForm.fallback_enabled} onChange={(e) => {
        const provider = e.target.value as 'openai' | 'gemini';
        const nextModels = getModelsForProvider(provider);
        setCreateForm((v) => ({ ...v, fallback_provider: provider, fallback_model: nextModels[0]?.id ?? '' }));
      }} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm'>
        {providerCatalog.map((provider) => <option key={provider.id} value={provider.id} disabled={!provider.configured}>{provider.name}{provider.configured ? '' : ' (Unavailable)'}</option>)}
      </select>
      <select value={createForm.fallback_model ?? ''} disabled={!createForm.fallback_enabled} onChange={(e)=>setCreateForm((v)=>({...v, fallback_model:e.target.value}))} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm'>
        {getModelsForProvider((createForm.fallback_provider ?? 'openai') as 'openai'|'gemini').map((model)=> <option key={model.id} value={model.id}>{model.name}</option>)}
      </select>
      </div>
      <div className='grid grid-cols-2 gap-2 text-sm'>
        <input aria-label='max_fallback_attempts' type='number' min={0} max={5} value={createForm.max_fallback_attempts} onChange={(e)=>setCreateForm((v)=>({...v, max_fallback_attempts:Number(e.target.value)}))} className='rounded border border-slate-700 bg-slate-900 p-2' />
        <select aria-label='fallback_order' value={createForm.fallback_order} onChange={(e)=>setCreateForm((v)=>({...v, fallback_order:e.target.value as 'provider_then_model'|'model_then_provider'}))} className='rounded border border-slate-700 bg-slate-900 p-2'><option value='provider_then_model'>Provider then model</option><option value='model_then_provider'>Model then provider</option></select>
      </div>
      <textarea placeholder='Prompt content' value={createForm.content} onChange={(e) => setCreateForm((v) => ({ ...v, content: e.target.value }))} className='h-40 w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <button className='w-full rounded bg-emerald-700 px-3 py-2 text-sm sm:w-auto' onClick={async () => { try { await createPrompt.mutateAsync(createForm); pushToast('Prompt template created'); setCreateForm({ ...EMPTY_CREATE_FORM }); } catch (e) { pushToast(getErrorDetail(e), 'error'); } }}>Create template</button>
    </div>


    <div className='space-y-2 rounded border border-slate-800 p-3'>
      <h2 className='font-semibold'>Test prompt</h2>
      <select value={testForm.prompt_type} onChange={(e) => setTestForm((v) => ({ ...v, prompt_type: e.target.value as PromptTemplateType }))} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm'>
        {promptTypes.map((type) => <option key={type} value={type}>{type}</option>)}
      </select>
      <textarea placeholder='Prompt content for preview' value={testForm.prompt_content} onChange={(e) => setTestForm((v) => ({ ...v, prompt_content: e.target.value }))} className='h-32 w-full min-w-0 rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <textarea placeholder='Sample context/query/document text' value={testForm.sample_context} onChange={(e) => setTestForm((v) => ({ ...v, sample_context: e.target.value }))} className='h-32 w-full min-w-0 rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <button className='w-full rounded bg-indigo-700 px-3 py-2 text-sm sm:w-auto' onClick={async () => {
        setPreview(''); setPreviewMeta(null); setPreviewError('');
        if (!testForm.prompt_content.trim() || !testForm.sample_context.trim()) {
          setPreviewError('Prompt content and sample context are required.');
          return;
        }
        try {
          const resp = await testPrompt.mutateAsync(testForm);
          setPreview(resp.preview);
          setPreviewMeta(resp);
        } catch (e) {
          console.error('Prompt test request failed', (e as { response?: { data?: unknown } })?.response?.data ?? e);
          setPreviewError(getErrorDetail(e));
        }
      }} disabled={testPrompt.isPending || !testForm.prompt_content.trim() || !testForm.sample_context.trim()}>Run preview</button>
      {testPrompt.isPending && <div className='text-sm text-slate-300'>Generating preview...</div>}
      {previewError && <div className='text-sm text-rose-400' role='alert'>{previewError}</div>}
      {preview && <div className='text-xs text-slate-400'>Latency: {previewMeta?.latency_ms ?? 'n/a'} ms · Tokens: {previewMeta?.usage_tokens ?? 'n/a'} · Fallback used: {previewMeta?.fallback_used ? 'yes' : 'no'} · Used: {previewMeta?.provider_used ?? ''}/{previewMeta?.model_used ?? ''}</div>}
      {preview && previewMeta?.primary_error && <div className='text-xs text-amber-400'>Primary error: {previewMeta?.primary_error}</div>}
      {preview && <pre className='overflow-x-auto whitespace-pre-wrap break-words rounded border border-slate-700 bg-slate-950 p-2 text-sm'>{preview}</pre>}
    </div>

    {selectedPrompt && <div className='space-y-2 rounded border border-slate-800 p-3'>
      <h2 className='font-semibold'>Edit template</h2>
      <div className='text-xs text-slate-400'>{selectedPrompt.prompt_type} · v{selectedPrompt.version}</div>
      <input value={editForm.name} onChange={(e) => setEditForm((v) => ({ ...v, name: e.target.value }))} className='w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <textarea value={editForm.content} onChange={(e) => setEditForm((v) => ({ ...v, content: e.target.value }))} className='h-48 w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <div className='grid grid-cols-2 gap-2'>
      <select value={editForm.provider} onChange={(e)=>setEditForm((v)=>({...v, provider:e.target.value as 'openai'|'gemini'}))} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm'>{providerCatalog.map((provider) => <option key={provider.id} value={provider.id}>{provider.name}</option>)}</select>
      <input value={editForm.model} onChange={(e)=>setEditForm((v)=>({...v, model:e.target.value}))} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <input aria-label='edit-temperature' type='number' step='0.1' value={editForm.temperature} onChange={(e)=>setEditForm((v)=>({...v, temperature:Number(e.target.value)}))} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      <input aria-label='edit-max_tokens' type='number' value={editForm.max_tokens} onChange={(e)=>setEditForm((v)=>({...v, max_tokens:Number(e.target.value)}))} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
      </div>
      <label className='flex items-center gap-2 text-sm'><input type='checkbox' checked={editForm.fallback_enabled} onChange={(e)=>setEditForm((v)=>({...v, fallback_enabled:e.target.checked}))}/>Enable fallback</label>
      <select aria-label='edit-fallback_order' value={editForm.fallback_order} onChange={(e)=>setEditForm((v)=>({...v, fallback_order:e.target.value as 'provider_then_model'|'model_then_provider'}))} className='rounded border border-slate-700 bg-slate-900 p-2 text-sm'><option value='provider_then_model'>Provider then model</option><option value='model_then_provider'>Model then provider</option></select>
      <button className='w-full rounded bg-indigo-700 px-3 py-2 text-sm sm:w-auto' onClick={async () => { try { const payload = { ...editForm }; delete (payload as { prompt_type?: PromptTemplateType }).prompt_type; await updatePrompt.mutateAsync({ promptId: selectedPrompt.id, payload }); pushToast('Prompt template saved'); } catch (e) { pushToast(getErrorDetail(e), 'error'); } }}>Save changes</button>
    </div>}
  </div>;
}
