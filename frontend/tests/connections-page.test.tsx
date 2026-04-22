import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';
import { ConnectionsPage } from '@/pages/ConnectionsPage';
import type { Connection } from '@/types/api';

const mockStart = vi.fn();
const mockDisconnect = vi.fn();
const mockSync = vi.fn();
let connections: Connection[] = [];

vi.mock('@/hooks/useApi', () => ({
  useConnections: () => ({ data: connections, isLoading: false, isError: false, refetch: vi.fn() }),
}));

vi.mock('@/services/api', () => ({
  api: {
    startConnectProvider: (...args: unknown[]) => mockStart(...args),
    disconnectProvider: (...args: unknown[]) => mockDisconnect(...args),
    syncProvider: (...args: unknown[]) => mockSync(...args),
    getSyncLogs: vi.fn().mockResolvedValue([]),
  },
}));

function renderPage() {
  const qc = new QueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <ConnectionsPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  document.body.innerHTML = '';
  connections = [
    {
      id: '1',
      type: 'gdrive',
      status: 'disconnected',
      display_name: 'Google Drive',
      email: null,
      sync_progress: 0,
      document_count: 0,
      total_size: 0,
      auto_sync: true,
      sync_interval: 15,
      is_authenticated: false,
      last_sync_status: null,
      last_sync_date: null,
      external_account_id: null,
      last_error_message: null,
      last_error_at: null,
    },
  ];
  mockStart.mockReset();
  mockDisconnect.mockReset();
  mockSync.mockReset();
  mockStart.mockResolvedValue({ provider: 'gdrive', state: 's1', authorization_url: 'https://accounts.google.com/test' });
  mockDisconnect.mockResolvedValue(connections[0]);
  mockSync.mockResolvedValue({ message: 'ok', files_seen: 1, documents_added: 1, documents_updated: 0, documents_failed: 0, bytes_synced: 10, connection: connections[0] });
});

test('connect action starts oauth redirect flow', async () => {
  renderPage();
  fireEvent.click(screen.getByText('Connect'));
  await waitFor(() => expect(mockStart).toHaveBeenCalledWith('gdrive'));
});

test('sync button is disabled when not authenticated', () => {
  renderPage();
  expect(screen.getAllByText('Sync')[0]).toBeDisabled();
});
