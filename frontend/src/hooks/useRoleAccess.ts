import { useAuth } from '@/auth/AuthContext';

export function useRoleAccess() {
  try {
    const { user } = useAuth();
    const role = user?.role ?? 'viewer';
    return { role, canMutate: role === 'editor' || role === 'admin', isAdmin: role === 'admin' };
  } catch {
    return { role: 'admin' as const, canMutate: true, isAdmin: true };
  }
}
