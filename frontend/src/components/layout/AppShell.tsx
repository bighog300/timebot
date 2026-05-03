import { type FormEvent, useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  readOnboardingCompleted,
  readOnboardingStep,
  writeOnboardingCompleted,
  writeOnboardingStep,
  type OnboardingStep,
} from '@/components/layout/onboarding';
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
  ['/chat', 'Chat'],
  ['/reports', 'Reports'],
  ['/settings', 'Settings'],
] as const;

const adminLinks = [['/admin', 'Admin Overview'], ['/admin/users', 'Users'], ['/admin/settings', 'Settings']] as const;

export function AppShell() {
  const { toasts, dismissToast } = useUIStore();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const queueStats = useQueueStats();
  const pendingReviewCount = queueStats.data?.pending_review_count ?? 0;

  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState<OnboardingStep>('welcome');
  const [selectedUseCase, setSelectedUseCase] = useState<string | null>(null);

  useEffect(() => {
    const completed = readOnboardingCompleted();
    setShowOnboarding(!completed);
    setOnboardingStep(completed ? 'complete' : readOnboardingStep());
  }, []);

  const selectUseCase = (useCase: string) => {
    setSelectedUseCase(useCase);
    setOnboardingStep('first_action');
    writeOnboardingStep('first_action');
  };

  const completeOnboarding = (action: 'upload' | 'gmail') => {
    writeOnboardingCompleted();
    setOnboardingStep('complete');
    setShowOnboarding(false);
    navigate(`/documents?onboardingAction=${action}`);
  };

  const skipOnboarding = () => {
    setShowOnboarding(false);
  };

  const onHeaderSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const q = String(formData.get('q') ?? '').trim();
    navigate(q ? `/search?q=${encodeURIComponent(q)}` : '/search');
  };

  const navLinks = [...baseLinks, ...(user?.role === 'admin' ? adminLinks : [])];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-3 py-3 sm:px-4">
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

      <nav
        aria-label="Mobile"
        className="border-b border-slate-800 px-2 py-2 md:hidden"
      >
        <div className="flex gap-1 overflow-x-auto whitespace-nowrap pb-1">
          {navLinks.map(([to, label]) => (
            <NavLink
              key={`mobile-${to}`}
              to={to}
              end={to === '/review'}
              className={({ isActive }) =>
                `shrink-0 rounded px-2.5 py-1.5 text-xs ${isActive ? 'bg-slate-700 text-white' : 'text-slate-300 hover:bg-slate-800'}`
              }
            >
              <span className="inline-flex items-center gap-1.5">
                {label}
                {to === '/review' && pendingReviewCount > 0 && (
                  <span className="rounded-full bg-red-600 px-1.5 py-0.5 text-[10px] text-white">{pendingReviewCount}</span>
                )}
              </span>
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="grid min-h-[calc(100vh-57px)] grid-cols-1 md:grid-cols-[220px_minmax(0,1fr)]">
        <aside className="hidden border-r border-slate-800 p-3 md:block" aria-label="Desktop">
          <nav className="flex flex-col gap-1">
            {navLinks.map(([to, label]) => (
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
        <main className="min-w-0 overflow-x-auto overflow-y-auto p-3 sm:p-4 md:p-5">
          <Outlet />
        </main>
      </div>
      {showOnboarding && (
        <div className="fixed inset-0 z-40 bg-slate-950/90 p-4 sm:p-6" role="dialog" aria-modal="true" aria-label="Onboarding">
          <div className="mx-auto w-full max-w-xl rounded-lg border border-slate-700 bg-slate-900 p-4 sm:p-6">
            {onboardingStep === 'welcome' && (
              <div className="space-y-3">
                <h2 className="text-xl font-semibold">Welcome to Timebot</h2>
                <p className="text-sm text-slate-300">Choose your primary use case to get started.</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  <button className="rounded border border-slate-600 p-3 text-left hover:bg-slate-800" onClick={() => selectUseCase('casework')}>Casework & investigations</button>
                  <button className="rounded border border-slate-600 p-3 text-left hover:bg-slate-800" onClick={() => selectUseCase('ops')}>Operations & reporting</button>
                </div>
                <button className="text-sm text-slate-400 underline" onClick={skipOnboarding}>Skip for now</button>
              </div>
            )}

            {onboardingStep === 'first_action' && (
              <div className="space-y-3">
                <h2 className="text-xl font-semibold">Great. Add your first document source.</h2>
                <p className="text-sm text-slate-300">Use case: {selectedUseCase ?? 'General'}</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  <button className="rounded bg-blue-600 px-3 py-2 text-sm font-medium hover:bg-blue-500" onClick={() => completeOnboarding('upload')}>Upload files</button>
                  <button className="rounded bg-emerald-700 px-3 py-2 text-sm font-medium hover:bg-emerald-600" onClick={() => completeOnboarding('gmail')}>Import from Gmail</button>
                </div>
                <button className="text-sm text-slate-400 underline" onClick={skipOnboarding}>Skip for now</button>
              </div>
            )}

            {onboardingStep === 'complete' && (
              <div className="space-y-3">
                <h2 className="text-xl font-semibold">You are all set</h2>
                <button className="rounded bg-slate-700 px-3 py-2 text-sm" onClick={() => setShowOnboarding(false)}>Continue</button>
              </div>
            )}
          </div>
        </div>
      )}
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
