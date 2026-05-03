import { Link } from 'react-router-dom';
import { useState } from 'react';
import { useCreateWorkspace, useWorkspaces } from '@/hooks/useApi';

export function WorkspacesPage() {
  const { data, isLoading, isError, error } = useWorkspaces();
  const createWorkspace = useCreateWorkspace();
  const [name, setName] = useState('');

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    await createWorkspace.mutateAsync({ name: name.trim() });
    setName('');
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Workspaces</h1>
        <p className="text-sm text-slate-300">Manage your personal and team workspaces.</p>
      </div>
      <form onSubmit={onCreate} className="flex gap-2">
        <input value={name} onChange={(e)=>setName(e.target.value)} placeholder="New team workspace" className="rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm" />
        <button className="rounded bg-blue-600 px-3 py-2 text-sm" type="submit" disabled={createWorkspace.isPending}>Create team workspace</button>
      </form>
      {isLoading && <p>Loading workspaces...</p>}
      {isError && <p className="text-red-400">Failed to load workspaces: {(error as Error).message}</p>}
      {!isLoading && !isError && (data?.length ?? 0) === 0 && <p>No workspaces yet.</p>}
      {!!data?.length && (
        <ul className="space-y-2">
          {data.map((ws) => (
            <li key={ws.id} className="rounded border border-slate-800 p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">{ws.name}</div>
                  <div className="text-xs text-slate-400">{ws.type}</div>
                </div>
                <Link className="text-blue-400 underline" to={`/workspaces/${ws.id}`}>Manage</Link>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
