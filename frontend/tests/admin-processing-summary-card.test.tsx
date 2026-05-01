import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AdminPage } from '@/pages/AdminPage';

vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));
vi.mock('@/hooks/useApi', () => ({
  useAdminUsers: () => ({ isLoading: false, isError: false, data: { items: [], total_count: 0, limit: 10, offset: 0 } }),
  useAdminAudit: () => ({ isLoading: false, isError: false, data: { items: [], total_count: 0, limit: 10, offset: 0 } }),
  useAdminMetrics: () => ({ data: { total_users: 1 } }),
  useAdminProcessingSummary: () => ({ isLoading: false, isError: false, data: { pending: 2, processing: 1, completed: 5, failed: 3, recently_failed: 1 } }),
  useUpdateUserRole: () => ({ mutateAsync: vi.fn() }),
}));

describe('admin processing summary card', () => {
  afterEach(() => cleanup());

  it('renders processing summary card', () => {
    render(<AdminPage />);
    expect(screen.getByText('Processing Summary')).toBeInTheDocument();
  });

  it('renders failed count', () => {
    render(<AdminPage />);
    expect(screen.getAllByText('failed').length).toBeGreaterThan(0);
    expect(screen.getByText('3')).toBeInTheDocument();
  });
});
