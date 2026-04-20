import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { env } from '@/lib/env';
import { keys } from '@/hooks/useApi';

type LiveEventPayload = {
  event_type?: string;
  event_version?: number | string;
  timestamp?: string | number;
};

function isValidTimestamp(value: unknown): boolean {
  if (typeof value === 'number') {
    return Number.isFinite(value);
  }
  if (typeof value === 'string') {
    return !Number.isNaN(Date.parse(value));
  }
  return false;
}

export function useLiveEvents() {
  const qc = useQueryClient();

  useEffect(() => {
    const ws = new WebSocket(`${env.wsBaseUrl}/all`);
    ws.onmessage = (message) => {
      let payload: LiveEventPayload | null = null;
      if (typeof message.data === 'string' && message.data.length > 0) {
        try {
          payload = JSON.parse(message.data) as LiveEventPayload;
        } catch {
          payload = null;
        }
      }

      const rawVersion = payload?.event_version;
      const parsedVersion =
        typeof rawVersion === 'number'
          ? rawVersion
          : typeof rawVersion === 'string'
            ? Number.parseInt(rawVersion, 10)
            : Number.NaN;
      const hasSafeVersion = Number.isFinite(parsedVersion) && parsedVersion >= 1;
      const hasSafeTimestamp = isValidTimestamp(payload?.timestamp);

      if (payload && (!hasSafeVersion || !hasSafeTimestamp)) {
        return;
      }

      qc.invalidateQueries({ queryKey: keys.documents });
      qc.invalidateQueries({ queryKey: keys.queueStats });
      qc.invalidateQueries({ queryKey: keys.queueItems });
      qc.invalidateQueries({ queryKey: keys.connections });
    };
    return () => ws.close();
  }, [qc]);
}
