import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { http } from '@/services/http';
import type { AuthResponse, AuthUser } from '@/types/api';

type AuthContextValue = {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  logout: () => void;
};

const AUTH_TOKEN_KEY = 'timebot.auth.token';
export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function applyToken(token: string | null) {
  if (token) http.defaults.headers.common.Authorization = `Bearer ${token}`;
  else delete http.defaults.headers.common.Authorization;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(AUTH_TOKEN_KEY));
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    applyToken(token);
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    http
      .get<AuthUser>('/auth/me')
      .then((resp) => setUser(resp.data))
      .catch(() => {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      loading,
      async login(email: string, password: string) {
        const resp = await http.post<AuthResponse>('/auth/login', { email, password });
        localStorage.setItem(AUTH_TOKEN_KEY, resp.data.access_token);
        setToken(resp.data.access_token);
        setUser(resp.data.user);
      },
      async register(email: string, password: string, displayName: string) {
        const resp = await http.post<AuthResponse>('/auth/register', { email, password, display_name: displayName });
        localStorage.setItem(AUTH_TOKEN_KEY, resp.data.access_token);
        setToken(resp.data.access_token);
        setUser(resp.data.user);
      },
      logout() {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        setToken(null);
        setUser(null);
      },
    }),
    [user, token, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
