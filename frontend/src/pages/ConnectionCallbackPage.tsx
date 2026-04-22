import { useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Card } from '@/components/ui/Card';
import { useUIStore } from '@/store/uiStore';

export function ConnectionCallbackPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const pushToast = useUIStore((s) => s.pushToast);

  const provider = useMemo(() => params.get('provider') ?? 'gdrive', [params]);
  const code = params.get('code');
  const state = params.get('state');
  const oauthError = params.get('error');

  const complete = useMutation({
    mutationFn: (payload: { type: string; code: string; state: string }) =>
      api.completeConnectProvider(payload.type, payload.code, payload.state),
    onSuccess: () => {
      pushToast('Connection successful');
      navigate('/connections');
    },
    onError: () => {
      pushToast('OAuth callback failed');
    },
  });

  useEffect(() => {
    if (oauthError) {
      pushToast(`OAuth denied: ${oauthError}`);
      navigate('/connections');
      return;
    }
    if (!code || !state) {
      return;
    }
    complete.mutate({ type: provider, code, state });
  }, [code, state, provider, oauthError]);

  return (
    <Card>
      <h1 className="mb-2 text-lg font-semibold">Completing connection…</h1>
      <p className="text-sm text-slate-400">Please wait while we finalize OAuth and return you to Connections.</p>
    </Card>
  );
}
