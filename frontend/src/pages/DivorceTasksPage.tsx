import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

const workspaceId = () => localStorage.getItem('active_workspace_id') || localStorage.getItem('activeWorkspaceId') || '';

export function DivorceTasksPage(){
  const qc = useQueryClient();
  const ws = workspaceId();
  const tasks = useQuery({queryKey:['divorce-tasks', ws], queryFn:()=>api.listDivorceTasks(ws), enabled: !!ws});
  const extract = useMutation({mutationFn:()=>api.extractDivorceTasks(ws), onSuccess:()=>qc.invalidateQueries({queryKey:['divorce-tasks', ws]})});
  const accept = useMutation({mutationFn:(id:string)=>api.acceptDivorceTask(id), onSuccess:()=>qc.invalidateQueries({queryKey:['divorce-tasks', ws]})});
  const reject = useMutation({mutationFn:(id:string)=>api.rejectDivorceTask(id), onSuccess:()=>qc.invalidateQueries({queryKey:['divorce-tasks', ws]})});
  const mark = useMutation({mutationFn:({id,status}:{id:string;status:string})=>api.patchDivorceTask(id,{status}), onSuccess:()=>qc.invalidateQueries({queryKey:['divorce-tasks', ws]})});

  const suggested = (tasks.data||[]).filter(t=>t.status==='suggested');
  const rest = (tasks.data||[]).filter(t=>t.status!=='suggested');

  return <div className='space-y-4'><h1 className='text-xl font-semibold'>Divorce Tasks</h1><p className='text-xs text-slate-400'>Legal disclaimer: informational support only. AI-generated items must be verified before legal use.</p>
    <button className='rounded bg-indigo-700 px-3 py-2 text-sm' onClick={()=>extract.mutate()}>Extract tasks from documents</button>
    <h2 className='font-medium'>Suggested tasks ({suggested.length})</h2>
    {suggested.map(t=><div key={t.id} className='rounded border p-3 text-sm'><div><span className='text-[10px] uppercase text-amber-300'>AI-generated, verify before legal use</span><div>{t.content}</div></div><div>{t.category} · {t.priority} · {t.due_date||'No due date'}</div><div>{t.source_snippet||t.source_quote}</div><button onClick={()=>accept.mutate(t.id)}>Accept</button> <button onClick={()=>reject.mutate(t.id)}>Reject</button></div>)}
    <h2 className='font-medium'>Open/Active tasks ({rest.length})</h2>
    {rest.map(t=><div key={t.id} className='rounded border p-3 text-sm'><div><span className='text-[10px] uppercase text-amber-300'>AI-generated, verify before legal use</span><div>{t.content}</div></div><div>{t.status} · {t.category} · {t.priority} · {t.due_date||'No due date'}</div><button onClick={()=>mark.mutate({id:t.id,status:'done'})}>Mark done</button> <button onClick={()=>mark.mutate({id:t.id,status:'dismissed'})}>Dismiss</button></div>)}
  </div>
}
