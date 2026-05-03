import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AdminPage } from './AdminPage';
import { AdminPromptTemplatesPage } from './AdminPromptTemplatesPage';
import { RequireAdmin } from '@/components/auth/RequireAdmin';

vi.mock('@/hooks/useApi', () => ({
  useAdminAudit: vi.fn(),
  useAdminMetrics: vi.fn(),
  useAdminProcessingSummary: vi.fn(),
  useAdminUsers: vi.fn(),
  useUpdateUserRole: vi.fn(),
  useAdminPromptTemplates: vi.fn(),
  useAdminLlmModels: vi.fn(),
  useCreatePromptTemplate: vi.fn(),
  useUpdatePromptTemplate: vi.fn(),
  useActivatePromptTemplate: vi.fn(),
  useTestPromptTemplate: vi.fn(),
}));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));
vi.mock('@/auth/AuthContext', () => ({ useAuth: vi.fn() }));

import {
  useAdminAudit,
  useAdminMetrics,
  useAdminProcessingSummary,
  useAdminUsers,
  useUpdateUserRole,
  useAdminPromptTemplates,
  useAdminLlmModels,
  useCreatePromptTemplate,
  useUpdatePromptTemplate,
  useActivatePromptTemplate,
  useTestPromptTemplate,
} from '@/hooks/useApi';
import { useAuth } from '@/auth/AuthContext';

function wrap(node: React.ReactNode) {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>{node}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Admin responsiveness and guard behavior', () => {
  beforeEach(() => {
    vi.mocked(useAdminMetrics).mockReturnValue({ data: { users: 10, docs: 22, jobs: 3, alerts: 1 } } as never);
    vi.mocked(useAdminProcessingSummary).mockReturnValue({ isLoading: false, isError: false, data: { pending: 1, processing: 2, completed: 3, failed: 4, recently_failed: 5 } } as never);
    vi.mocked(useAdminUsers).mockReturnValue({ isLoading: false, isError: false, data: { items: [], total_count: 0, limit: 10 } } as never);
    vi.mocked(useAdminAudit).mockReturnValue({ isLoading: false, isError: false, data: { items: [], total_count: 0, limit: 10 } } as never);
    vi.mocked(useUpdateUserRole).mockReturnValue({ mutateAsync: vi.fn() } as never);

    vi.mocked(useAdminPromptTemplates).mockReturnValue({
      isLoading: false,
      isError: false,
      data: [{ id: 'p1', prompt_type: 'chat', name: 'Default', version: 1, is_active: true, updated_at: '2026-01-01T00:00:00Z', created_at: '2026-01-01T00:00:00Z', content: 'hello' }],
    } as never);
    vi.mocked(useAdminLlmModels).mockReturnValue({
      isLoading: false,
      isError: false,
      data: { providers: [{ id: 'openai', name: 'OpenAI', configured: true, models: [{ id: 'gpt-4o-mini', name: 'GPT-4o Mini' }] }] },
    } as never);
    vi.mocked(useCreatePromptTemplate).mockReturnValue({ mutateAsync: vi.fn() } as never);
    vi.mocked(useUpdatePromptTemplate).mockReturnValue({ mutateAsync: vi.fn() } as never);
    vi.mocked(useActivatePromptTemplate).mockReturnValue({ mutateAsync: vi.fn() } as never);
    vi.mocked(useTestPromptTemplate).mockReturnValue({ mutateAsync: vi.fn(), isPending: false } as never);
  });

  it('admin dashboard renders responsive metrics and readable processing summary card', () => {
    const { container } = wrap(<AdminPage />);
    expect(container.innerHTML.includes('grid-cols-1')).toBe(true);
    expect(container.innerHTML.includes('sm:grid-cols-2')).toBe(true);
    expect(screen.getByText('Processing Summary')).toBeTruthy();
    expect(container.querySelectorAll('.rounded.border.border-slate-800.p-2').length).toBeGreaterThanOrEqual(5);
  });

  it('prompt templates page still renders and sandbox form remains usable on narrow screens', () => {
    const { container } = wrap(<AdminPromptTemplatesPage />);
    expect(screen.getByText('Prompt Templates')).toBeTruthy();
    expect(container.querySelector('.overflow-x-auto')).toBeTruthy();
    expect(screen.getByPlaceholderText('Prompt content for preview').className).toContain('min-w-0');
    const runPreview = screen.getByRole('button', { name: 'Run preview' });
    expect(runPreview.className).toContain('w-full');
    expect(runPreview).toBeDisabled();
  });

  it('non-admin guard still blocks access', () => {
    vi.mocked(useAuth).mockReturnValue({ user: { role: 'viewer' }, loading: false } as never);
    wrap(<RequireAdmin><div>Admin content</div></RequireAdmin>);
    expect(screen.getByText('Unauthorized: admin access required.')).toBeTruthy();
  });
});
