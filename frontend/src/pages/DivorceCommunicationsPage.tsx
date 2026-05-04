import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { getActiveWorkspaceId } from '@/services/workspace';

export function DivorceCommunicationsPage(){
  const ws = getActiveWorkspaceId();
  const qc = useQueryClient();
  const [category, setCategory] = useState('all');
  const [tone, setTone] = useState('all');
  const [status, setStatus] = useState('all');
  const q = useQuery({queryKey:['divorce-comms',ws], queryFn:()=>api.listDivorceCommunications(ws), enabled:!!ws});
  const extract = useMutation({mutationFn:()=>api.extractDivorceCommunications(ws), onSuccess:()=>qc.invalidateQueries({queryKey:['divorce-comms',ws]})});
  const accept = useMutation({mutationFn:(id:string)=>api.acceptDivorceCommunication(id), onSuccess:()=>qc.invalidateQueries({queryKey:['divorce-comms',ws]})});
  const reject = useMutation({mutationFn:(id:string)=>api.rejectDivorceCommunication(id), onSuccess:()=>qc.invalidateQueries({queryKey:['divorce-comms',ws]})});
  const del = useMutation({mutationFn:(id:string)=>api.deleteDivorceCommunication(id), onSuccess:()=>qc.invalidateQueries({queryKey:['divorce-comms',ws]})});
  const items = q.data||[];
  const filtered = useMemo(()=>items.filter(i=>(category==='all'||i.category===category)&&(tone==='all'||i.tone===tone)&&(status==='all'||i.review_status===status)),[items,category,tone,status]);
  const suggested = filtered.filter(i=>i.review_status==='suggested');
  const accepted = filtered.filter(i=>i.review_status!=='suggested');
  return <div className='space-y-3'><h1>Divorce Communications</h1><p>Legal disclaimer: communication analysis is AI-generated support content, verify before legal use.</p>
    <button onClick={()=>extract.mutate()}>Extract communications</button>
    <div><select value={category} onChange={e=>setCategory(e.target.value)}><option value='all'>all categories</option>{['lawyer','spouse_or_other_party','court','financial','children','school','mediator','unknown'].map(c=><option key={c} value={c}>{c}</option>)}</select>
    <select value={tone} onChange={e=>setTone(e.target.value)}><option value='all'>all tones</option>{['neutral','hostile','cooperative','urgent','threatening','unclear'].map(c=><option key={c} value={c}>{c}</option>)}</select>
    <select value={status} onChange={e=>setStatus(e.target.value)}><option value='all'>all statuses</option>{['suggested','accepted','rejected','edited'].map(c=><option key={c} value={c}>{c}</option>)}</select></div>
    <h2>Suggested communications ({suggested.length})</h2>
    {suggested.map(i=><div key={i.id}><span className='text-[10px] uppercase text-amber-300'>AI-generated, verify before legal use</span><b>{i.sender}</b> → {String(i.recipient||'')} · {String(i.subject||'')} · {i.sent_at || 'unknown'}<div>Inferred: {i.category} / {i.tone}</div><div>Quoted/source: {String((i.metadata_json?.source_snippet as string | undefined) || '')}</div><div>Issues: {JSON.stringify(i.extracted_issues_json)}</div><div>Deadlines: {JSON.stringify(i.extracted_deadlines_json)}</div><div>Offers: {JSON.stringify(i.extracted_offers_json)}</div><div>Allegations: {JSON.stringify(i.extracted_allegations_json)}</div><button onClick={()=>accept.mutate(i.id)}>Accept</button><button onClick={()=>reject.mutate(i.id)}>Reject</button><button onClick={()=>del.mutate(i.id)}>Delete</button></div>)}
    <h2>Accepted/Reviewed ({accepted.length})</h2>
    {accepted.map(i=><div key={i.id}>{i.sender} · {i.subject} · {i.review_status}</div>)}
  </div>
}
