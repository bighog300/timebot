import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { env } from '@/lib/env';
import { keys } from '@/hooks/useApi';

export function useLiveEvents() {
  const qc = useQueryClient();

  useEffect(() => {
    const ws = new WebSocket(`${env.wsBaseUrl}/all`);
    ws.onmessage = () => {
      qc.invalidateQueries({ queryKey: keys.documents });
      qc.invalidateQueries({ queryKey: keys.queueStats });
      qc.invalidateQueries({ queryKey: keys.queueItems });
      qc.invalidateQueries({ queryKey: keys.connections });
    };
    return () => ws.close();
  }, [qc]);
}
