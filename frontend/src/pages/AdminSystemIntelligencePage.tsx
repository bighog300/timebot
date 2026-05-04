import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { http } from '@/services/http';

const tabs = ['Library', 'Upload', 'Review Submissions', 'Web References', 'Audit Log'] as const;

export function AdminSystemIntelligencePage() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<(typeof tabs)[number]>('Library');
  const docs = useQuery({ queryKey: ['si-docs'], queryFn: async () => (await http.get('/api/v1/admin/system-intelligence/documents')).data });
  const submissions = useQuery({ queryKey: ['si-subs'], queryFn: async () => (await http.get('/api/v1/admin/system-intelligence/submissions')).data });
  const refs = useQuery({ queryKey: ['si-refs'], queryFn: async () => (await http.get('/api/v1/admin/system-intelligence/web-references')).data });
  const logs = useQuery({ queryKey: ['si-audit'], queryFn: async () => (await http.get('/api/v1/admin/system-intelligence/audit-log')).data });
  const createDoc = useMutation({ mutationFn: async (payload: { title: string; description?: string }) => (await http.post('/api/v1/admin/system-intelligence/documents', { source_type: 'admin_upload', ...payload })).data, onSuccess: () => qc.invalidateQueries({ queryKey: ['si-docs'] }) });

  return <div className="space-y-4"><h1 className="text-2xl font-semibold">System Intelligence</h1>
    <div className="flex gap-2">{tabs.map(t => <button key={t} onClick={() => setTab(t)} className="rounded border px-3 py-1">{t}</button>)}</div>
    {tab==='Library' && <pre className="text-xs overflow-auto">{JSON.stringify(docs.data ?? [], null, 2)}</pre>}
    {tab==='Upload' && <form onSubmit={(e)=>{e.preventDefault(); const fd=new FormData(e.currentTarget); createDoc.mutate({title:String(fd.get('title')||''), description:String(fd.get('description')||'')});}} className="space-y-2"><input name="title" placeholder="Title" className="w-full rounded bg-slate-800 p-2"/><textarea name="description" placeholder="Description" className="w-full rounded bg-slate-800 p-2"/><button className="rounded bg-blue-600 px-3 py-2">Create</button></form>}
    {tab==='Review Submissions' && <pre className="text-xs overflow-auto">{JSON.stringify(submissions.data ?? [], null, 2)}</pre>}
    {tab==='Web References' && <pre className="text-xs overflow-auto">{JSON.stringify(refs.data ?? [], null, 2)}</pre>}
    {tab==='Audit Log' && <pre className="text-xs overflow-auto">{JSON.stringify(logs.data ?? [], null, 2)}</pre>}
  </div>;
}
