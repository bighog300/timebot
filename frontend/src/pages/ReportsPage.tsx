import { useState } from 'react';
import { useCreateReport, useReport, useReports } from '@/hooks/useApi';
import { api, getErrorDetail } from '@/services/api';
import { useUIStore } from '@/store/uiStore';

function ReportSection({ title, content }: { title: string; content: string }) {
  return (
    <section className='rounded border border-slate-700 bg-slate-900/50 p-3'>
      <h3 className='mb-2 text-sm font-semibold text-slate-100'>{title}</h3>
      <p className='text-sm whitespace-pre-wrap break-words text-slate-200'>{content}</p>
    </section>
  );
}

export function ReportsPage() {
  const reports = useReports();
  const [selectedId, setSelectedId] = useState('');
  const detail = useReport(selectedId);
  const create = useCreateReport();
  const { pushToast } = useUIStore();
  const [title, setTitle] = useState(''); const [prompt, setPrompt] = useState(''); const [docIds, setDocIds] = useState('');
  const [includeTimeline, setIncludeTimeline] = useState(true); const [includeRelationships, setIncludeRelationships] = useState(true); const [includeFullText, setIncludeFullText] = useState(false);
  const sections = detail.data?.sections;
  const summaryContent = sections?.executive_summary || sections?.summary;
  const hasStructuredSections = Boolean(summaryContent || sections?.timeline_analysis || sections?.relationship_analysis);

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
  </div><div>{detail.data && <div><h2 className='text-lg'>{detail.data.title}</h2><a href={api.getReportDownloadUrl(detail.data.id)} target='_blank'>Download report</a>{hasStructuredSections ? <div className='mt-3 space-y-3'>
    {summaryContent && <ReportSection title='Executive Summary / Summary' content={summaryContent} />}
    {sections?.timeline_analysis && <ReportSection title='Timeline Analysis' content={sections.timeline_analysis} />}
    {sections?.relationship_analysis && <ReportSection title='Relationship Analysis' content={sections.relationship_analysis} />}
  </div> : <pre className='mt-3 whitespace-pre-wrap break-words'>{detail.data.markdown_content}</pre>}</div>}</div></div>;
}
