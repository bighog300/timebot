import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import { getActiveWorkspaceId } from '@/services/workspace';

export function DivorceTimelinePage() {
  const ws = getActiveWorkspaceId();
  const qc = useQueryClient();
  const [category, setCategory] = useState('all');
  const [status, setStatus] = useState('all');
  const [newTitle, setNewTitle] = useState('');
  const [newDate, setNewDate] = useState('');
  const timeline = useQuery({ queryKey: ['divorce-timeline', ws], queryFn: () => api.listDivorceTimeline(ws), enabled: !!ws });
  const extract = useMutation({ mutationFn: () => api.extractDivorceTimeline(ws), onSuccess: () => qc.invalidateQueries({ queryKey: ['divorce-timeline', ws] }) });
  const accept = useMutation({ mutationFn: (id: string) => api.acceptDivorceTimeline(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['divorce-timeline', ws] }) });
  const reject = useMutation({ mutationFn: (id: string) => api.rejectDivorceTimeline(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['divorce-timeline', ws] }) });
  const create = useMutation({ mutationFn: () => api.createDivorceTimelineManual(ws, { title: newTitle, event_date: newDate || null, category: 'other' }), onSuccess: () => { setNewTitle(''); setNewDate(''); qc.invalidateQueries({ queryKey: ['divorce-timeline', ws] }); } });
  const items = timeline.data || [];
  const filtered = useMemo(() => items.filter((i) => (category === 'all' || i.category === category) && (status === 'all' || i.review_status === status)), [items, category, status]);
  return <div className='space-y-3'><h1>Divorce Timeline</h1><p>Legal disclaimer: informational support only, not legal advice. Verify AI output before legal use.</p>
    <button onClick={() => extract.mutate()}>Extract timeline</button>
    <div><input value={newTitle} onChange={(e) => setNewTitle(e.target.value)} placeholder='Manual event title' /><input type='date' value={newDate} onChange={(e) => setNewDate(e.target.value)} /><button onClick={() => create.mutate()}>Add event</button></div>
    <div><select value={category} onChange={(e) => setCategory(e.target.value)}><option value='all'>all categories</option>{['legal','financial','children','communication','evidence','court','admin','safety','other'].map((c)=><option key={c} value={c}>{c}</option>)}</select>
    <select value={status} onChange={(e) => setStatus(e.target.value)}><option value='all'>all status</option>{['suggested','accepted','rejected','edited'].map((s)=><option key={s} value={s}>{s}</option>)}</select></div>
    <h2>Suggested</h2>{filtered.filter((i)=>i.review_status==='suggested').map((i)=><div key={i.id}><b>{i.event_date || 'unknown/inferred'} {i.date_precision !== 'exact' ? `(${i.date_precision})` : ''}</b> {i.title} <span>{Math.round((i.confidence||0)*100)}%</span><div>{i.source_snippet || i.source_quote}</div><button onClick={()=>accept.mutate(i.id)}>Accept</button><button onClick={()=>reject.mutate(i.id)}>Reject</button></div>)}
    <h2>Accepted</h2>{filtered.filter((i)=>i.review_status!=='suggested').map((i)=><div key={i.id}>{i.event_date || 'unknown'} {i.title}</div>)}
  </div>;
}
