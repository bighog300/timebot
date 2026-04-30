import type { FormEvent } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useUIStore } from '@/store/uiStore';
import { useQueueStats } from '@/hooks/useApi';
import { useAuth } from '@/auth/AuthContext';

const baseLinks = [
  ['/dashboard', 'Dashboard'],
  ['/timeline', 'Timeline'],
  ['/documents', 'Documents'],
  ['/search', 'Search'],
  ['/queue', 'Queue'],
  ['/review', 'Review'],
  ['/review/relationships', 'Relationships'],
  ['/action-items', 'Action Items'],
  ['/categories', 'Categories'],
  ['/insights', 'Insights'],
  ['/connections', 'Connections'],
] as const;

export function AppShell() {
  const { toasts, dismissToast } = useUIStore();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const queueStats = useQueueStats();
  const pendingReviewCount = queueStats.data?.pending_review_count ?? 0;

  const onHeaderSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const q = String(formData.get('q') ?? '').trim();
    navigate(q ? `/search?q=${encodeURIComponent(q)}` : '/search');
  };
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-4 py-3">
        <div className="font-semibold">Document Intelligence Platform</div>
        <form onSubmit={onHeaderSearch} className="flex min-w-[220px] flex-1 items-center gap-2 md:max-w-md">
          <input
            name="q"
            placeholder="Search documents"
            className="w-full rounded border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm"
          />
          <button type="submit" className="rounded bg-slate-700 px-2 py-1.5 text-sm hover:bg-slate-600">Search</button>
        </form>
        <div className="flex items-center gap-3 text-sm text-slate-300">
          <span>{user?.email}</span>
          <button className="rounded bg-slate-700 px-2 py-1 hover:bg-slate-600" onClick={logout}>Logout</button>
        </div>
      </header>
      <div className="grid min-h-[calc(100vh-57px)] grid-cols-1 md:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="border-r border-slate-800 p-3">
          <nav className="flex flex-col gap-1">
            {[...baseLinks, ...(user?.role === "admin" ? [['/admin', 'Admin'] as const] : [])].map(([to, label]) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/review'}
                className={({ isActive }) =>
                  `rounded px-3 py-2 text-sm ${isActive ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-slate-800'}`
                }
              >
                <span className="inline-flex items-center gap-2">
                  {label}
                  {to === '/review' && pendingReviewCount > 0 && (
                    <span className="rounded-full bg-red-600 px-2 py-0.5 text-[10px] text-white">{pendingReviewCount}</span>
                  )}
                </span>
              </NavLink>
            ))}
          </nav>
        </aside>
        <main className="min-w-0 overflow-x-hidden p-4">
          <Outlet />
        </main>
      </div>
      <div className="fixed bottom-4 right-4 flex flex-col gap-2">
        {toasts.map((toast) => (
          <button
            key={toast.id}
            onClick={() => dismissToast(toast.id)}
            className={`rounded px-3 py-2 text-sm text-white shadow ${toast.type === 'error' ? 'bg-red-700' : 'bg-emerald-700'}`}
          >
            {toast.message}
          </button>
        ))}
      </div>
    </div>
  );
}
