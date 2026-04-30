import { Navigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';

export function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-4 text-slate-300">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'admin') return <div className="rounded border border-amber-700 bg-amber-950/40 p-4 text-amber-200">Unauthorized: admin access required.</div>;
  return <>{children}</>;
}
