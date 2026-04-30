import { useState } from 'react';
import { useCreateReport, useReport, useReports } from '@/hooks/useApi';
import { api, getErrorDetail } from '@/services/api';
import { useUIStore } from '@/store/uiStore';

export function ReportsPage() {
  const reports = useReports();
  const [selectedId, setSelectedId] = useState('');
  const detail = useReport(selectedId);
  const create = useCreateReport();
  const { pushToast } = useUIStore();
  const [title, setTitle] = useState(''); const [prompt, setPrompt] = useState(''); const [docIds, setDocIds] = useState('');
  const [includeTimeline, setIncludeTimeline] = useState(true); const [includeRelationships, setIncludeRelationships] = useState(true); const [includeFullText, setIncludeFullText] = useState(false);
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
  </div><div>{detail.data && <div><h2 className='text-lg'>{detail.data.title}</h2><a href={api.getReportDownloadUrl(detail.data.id)} target='_blank'>Download report</a><pre className='whitespace-pre-wrap'>{detail.data.markdown_content}</pre></div>}</div></div>;
}
