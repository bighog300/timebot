import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';

export function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return <div className="p-6 text-slate-300">Loading session…</div>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}
