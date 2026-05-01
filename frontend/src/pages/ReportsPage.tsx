import { useState } from 'react';
import { useCreateReport, useReport, useReports, useUpdateReport } from '@/hooks/useApi';
import { api, getErrorDetail } from '@/services/api';
import { useUIStore } from '@/store/uiStore';

function ReportSection({
  title, content, canEdit, isSaving, onSave,
}: { title: string; content: string; canEdit: boolean; isSaving: boolean; onSave: (next: string) => Promise<void> }) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(content);
  const [error, setError] = useState('');
  return (
    <section className='rounded border border-slate-700 bg-slate-900/50 p-3'>
      <div className='mb-2 flex items-center justify-between gap-2'>
        <h3 className='text-sm font-semibold text-slate-100'>{title}</h3>
        {canEdit && !isEditing && <button className='rounded border border-slate-600 px-2 py-1 text-xs' onClick={() => { setDraft(content); setError(''); setIsEditing(true); }}>Edit</button>}
      </div>
      {isEditing ? <div>
        <textarea value={draft} onChange={(e) => setDraft(e.target.value)} className='min-h-28 w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
        {error && <p className='mt-2 text-xs text-rose-300'>{error}</p>}
        <div className='mt-2 flex gap-2'>
          <button disabled={isSaving} onClick={async () => { try { setError(''); await onSave(draft); setIsEditing(false); } catch (e) { setError(getErrorDetail(e)); } }} className='rounded bg-indigo-700 px-2 py-1 text-xs disabled:opacity-50'>{isSaving ? 'Saving...' : 'Save'}</button>
          <button disabled={isSaving} onClick={() => { setDraft(content); setError(''); setIsEditing(false); }} className='rounded border border-slate-600 px-2 py-1 text-xs'>Cancel</button>
        </div>
      </div> : <p className='text-sm whitespace-pre-wrap break-words text-slate-200'>{content}</p>}
    </section>
  );
}

export function ReportsPage() {
  const reports = useReports();
  const [selectedId, setSelectedId] = useState('');
  const detail = useReport(selectedId);
  const create = useCreateReport();
  const update = useUpdateReport();
  const { pushToast } = useUIStore();
  const [title, setTitle] = useState(''); const [prompt, setPrompt] = useState(''); const [docIds, setDocIds] = useState('');
  const [includeTimeline, setIncludeTimeline] = useState(true); const [includeRelationships, setIncludeRelationships] = useState(true); const [includeFullText, setIncludeFullText] = useState(false);
  const sections = detail.data?.sections;
  const summaryContent = sections?.executive_summary || sections?.summary;
  const timelineContent = sections?.timeline_analysis || sections?.timeline;
  const relationshipContent = sections?.relationship_analysis || sections?.relationships;
  const hasStructuredSections = Boolean(summaryContent || timelineContent || relationshipContent);
  const saveSection = async (keys: string[], value: string) => {
    if (!detail.data || !detail.data.sections) return;
    const nextSections: Record<string, string> = {};
    Object.entries(detail.data.sections).forEach(([key, current]) => {
      nextSections[key] = String(current ?? '');
    });
    keys.forEach((key) => { nextSections[key] = value; });
    await update.mutateAsync({ reportId: detail.data.id, payload: { sections: nextSections } });
  };

  return <div className='grid gap-4 md:grid-cols-[360px_minmax(0,1fr)]'><div className='space-y-2'>
    <h1 className='text-xl font-semibold'>Reports</h1>
    <input value={title} onChange={(e)=>setTitle(e.target.value)} placeholder='title' className='w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
    <textarea value={prompt} onChange={(e)=>setPrompt(e.target.value)} placeholder='prompt' className='w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
    <input value={docIds} onChange={(e)=>setDocIds(e.target.value)} placeholder='doc ids' className='w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm' />
    <label><input type='checkbox' checked={includeTimeline} onChange={(e)=>setIncludeTimeline(e.target.checked)} /> timeline</label>
    <label className='ml-2'><input type='checkbox' checked={includeRelationships} onChange={(e)=>setIncludeRelationships(e.target.checked)} /> relationships</label>
    <label className='ml-2'><input type='checkbox' checked={includeFullText} onChange={(e)=>setIncludeFullText(e.target.checked)} /> full text</label>
    <button onClick={async()=>{try{const r=await create.mutateAsync({title,prompt,document_ids:docIds.split(',').map(s=>s.trim()).filter(Boolean),include_timeline:includeTimeline,include_relationships:includeRelationships,include_full_text:includeFullText}); setSelectedId(r.id); pushToast('Report created');}catch(e){pushToast(getErrorDetail(e),'error')}}} className='rounded bg-indigo-700 px-3 py-2 text-sm'>Create report</button>
    {(reports.data||[]).map(r=><button key={r.id} onClick={()=>setSelectedId(r.id)} className='block w-full rounded border border-slate-700 p-2 text-left text-sm'>{r.title}</button>)}
  </div><div>{detail.data && <div><h2 className='text-lg'>{detail.data.title}</h2><div className='mt-2 flex gap-3 text-sm'><a href={api.getReportDownloadUrl(detail.data.id, 'md')} target='_blank'>Download Markdown</a><a href={api.getReportDownloadUrl(detail.data.id, 'pdf')} target='_blank'>Download PDF</a></div>{hasStructuredSections ? <div className='mt-3 space-y-3'>
    {summaryContent && <ReportSection title='Executive Summary / Summary' content={summaryContent} canEdit={hasStructuredSections} isSaving={update.isPending} onSave={(value)=>saveSection(['executive_summary', 'summary'], value)} />}
    {timelineContent && <ReportSection title='Timeline Analysis' content={timelineContent} canEdit={hasStructuredSections} isSaving={update.isPending} onSave={(value)=>saveSection(['timeline_analysis', 'timeline'], value)} />}
    {relationshipContent && <ReportSection title='Relationship Analysis' content={relationshipContent} canEdit={hasStructuredSections} isSaving={update.isPending} onSave={(value)=>saveSection(['relationship_analysis', 'relationships'], value)} />}
  </div> : <pre className='mt-3 whitespace-pre-wrap break-words'>{detail.data.markdown_content}</pre>}</div>}</div></div>;
}
