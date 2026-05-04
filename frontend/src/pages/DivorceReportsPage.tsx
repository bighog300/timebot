import { useEffect, useState } from 'react';
import { api, getErrorDetail } from '@/services/api';
import type { DivorceReport } from '@/types/api';

const REPORT_TYPES = [
  'case_overview_report','legal_advisor_summary','psychological_communication_dynamics_report','evidence_timeline_report','task_deadline_report','lawyer_handoff_pack',
];

export function DivorceReportsPage(){
  const workspaceId = typeof window !== 'undefined' ? (new URLSearchParams(window.location.search).get('workspace_id') ?? '') : '';
  const [items,setItems]=useState<DivorceReport[]>([]); const [sel,setSel]=useState('case_overview_report'); const [title,setTitle]=useState(''); const [err,setErr]=useState('');
  const [selected,setSelected]=useState<DivorceReport|null>(null);
  const load=()=>api.listDivorceReports(workspaceId).then(setItems).catch((e)=>setErr(getErrorDetail(e)));
  useEffect(()=>{ if(workspaceId) void load(); },[workspaceId]);
  const gen=async()=>{ try{ setErr(''); const r=await api.generateDivorceReport(workspaceId,{report_type:sel,title:title||undefined}); await load(); setSelected(r);}catch(e){setErr(getErrorDetail(e));} };
  const archive=async(id:string)=>{ await api.patchDivorceReport(id,{status:'archived'}); await load(); };
  const del=async(id:string)=>{ await api.deleteDivorceReport(id); await load(); if(selected?.id===id) setSelected(null); };
  return <div><h1>Divorce Reports</h1><p>This report is informational and not legal advice. AI-generated, verify before legal use.</p>
    {err?<div>{err}{err.includes('upgrade_required')?' Upgrade to Pro to unlock this report type.':''}</div>:null}
    <div><select value={sel} onChange={(e)=>setSel(e.target.value)}>{REPORT_TYPES.map((t)=><option key={t} value={t}>{t}</option>)}</select><input placeholder='Title optional' value={title} onChange={(e)=>setTitle(e.target.value)} /><button onClick={gen}>Generate report</button></div>
    <ul>{items.map((r)=><li key={r.id}><button onClick={()=>setSelected(r)}>{r.title}</button> ({r.status}) sources: T{r.source_task_ids_json?.length||0}/L{r.source_timeline_item_ids_json?.length||0}/D{r.source_document_ids_json?.length||0} <button onClick={()=>archive(r.id)}>Archive</button> <button onClick={()=>del(r.id)}>Delete</button></li>)}</ul>
    {selected?<article><h2>{selected.title}</h2><pre style={{whiteSpace:'pre-wrap'}}>{selected.content_markdown}</pre></article>:null}
  </div>
}
