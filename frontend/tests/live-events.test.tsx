import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, expect, test, vi } from 'vitest';
import { useLiveEvents } from '@/hooks/useLiveEvents';
import { AuthContext } from '@/auth/AuthContext';
import { useUIStore } from '@/store/uiStore';

class MockSocket {
  static instance: MockSocket | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  constructor() { MockSocket.instance = this; }
  close() {}
}

function Harness() { useLiveEvents(); return null; }

describe('useLiveEvents', () => {
  test('handles websocket close 1008 gracefully', () => {
    vi.stubGlobal('WebSocket', MockSocket as unknown as typeof WebSocket);
    const qc = new QueryClient();
    const pushToast = vi.fn();
    useUIStore.setState({ toasts: [], pushToast, dismissToast: () => {} });
    render(
      <AuthContext.Provider value={{ user: null, token: 't', loading: false, login: vi.fn(), register: vi.fn(), logout: vi.fn() }}>
        <QueryClientProvider client={qc}><Harness /></QueryClientProvider>
      </AuthContext.Provider>,
    );
    MockSocket.instance?.onclose?.({ code: 1008 } as CloseEvent);
    expect(pushToast).toHaveBeenCalled();
  });
});
