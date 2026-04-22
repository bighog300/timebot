import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';

export function RegisterPage() {
  const { user, register } = useAuth();
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  if (user) return <Navigate to="/" replace />;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(email, password, displayName);
      navigate('/', { replace: true });
    } catch {
      setError('Could not register with those details');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto mt-16 max-w-md rounded border border-slate-800 bg-slate-900 p-6">
      <h1 className="mb-4 text-2xl font-semibold">Create account</h1>
      <form className="space-y-3" onSubmit={submit}>
        <input className="w-full rounded bg-slate-800 p-2" value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="Display name" />
        <input className="w-full rounded bg-slate-800 p-2" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
        <input className="w-full rounded bg-slate-800 p-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button className="w-full rounded bg-blue-600 p-2 disabled:opacity-50" disabled={loading}>{loading ? 'Creating…' : 'Create account'}</button>
      </form>
      <p className="mt-4 text-sm text-slate-400">Already have an account? <Link className="text-blue-400" to="/login">Sign in</Link></p>
    </div>
  );
}
