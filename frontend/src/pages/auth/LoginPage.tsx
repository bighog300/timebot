import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';

export function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };

  if (user) return <Navigate to={location.state?.from || '/'} replace />;

  useEffect(() => {
    api.getAuthConfig().then((cfg) => setGoogleEnabled(Boolean(cfg.google_login_enabled))).catch(() => setGoogleEnabled(false));
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate(location.state?.from || '/', { replace: true });
    } catch {
      setError('Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto mt-16 max-w-md rounded border border-slate-800 bg-slate-900 p-6">
      <h1 className="mb-4 text-2xl font-semibold">Sign in</h1>
      <form className="space-y-3" onSubmit={submit}>
        <input className="w-full rounded bg-slate-800 p-2" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
        <input className="w-full rounded bg-slate-800 p-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button className="w-full rounded bg-blue-600 p-2 disabled:opacity-50" disabled={loading}>{loading ? 'Signing in…' : 'Sign in'}</button>
      </form>
      {googleEnabled && <button className='mt-3 w-full rounded bg-rose-600 p-2' onClick={() => setError('Google sign-in flow is enabled server-side. Complete OAuth wiring in client integration.')}>Continue with Google</button>}
      <p className="mt-4 text-sm text-slate-400">No account? <Link className="text-blue-400" to="/register">Create one</Link></p>
    </div>
  );
}
