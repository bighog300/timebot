import { useAuth } from '@/auth/AuthContext';

export function SettingsAccountPage() {
  const { user } = useAuth();

  return (
    <section className="space-y-4" aria-label="Account settings">
      <h2 className="text-xl font-semibold">Account & profile</h2>
      <div className="rounded border border-slate-800 bg-slate-900 p-4 text-sm">
        <div>Email: <span className="font-medium">{user?.email ?? 'Unknown'}</span></div>
        <div>Display name: <span className="font-medium">{user?.display_name ?? 'Not set'}</span></div>
        <div>Role: <span className="font-medium capitalize">{user?.role ?? 'Unknown'}</span></div>
      </div>

      <div className="rounded border border-slate-800 bg-slate-900 p-4 text-sm">
        <h3 className="mb-1 font-medium">Password & security</h3>
        <p className="text-slate-300">Password or MFA controls are not currently available in the app settings UI.</p>
      </div>
    </section>
  );
}
