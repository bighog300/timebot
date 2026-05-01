import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AdminPromptTemplatesPage } from '@/pages/AdminPromptTemplatesPage';

const mutateCreate = vi.fn(async () => ({}));
const mutateUpdate = vi.fn(async () => ({}));
const mutateActivate = vi.fn(async () => ({}));

vi.mock('@/hooks/useApi', () => ({
  useAdminPromptTemplates: () => ({ data: [
    { id: 'p1', prompt_type: 'chat', name: 'Chat v1', content: 'Prompt A', version: 1, is_active: true, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-02T00:00:00Z' },
    { id: 'p2', prompt_type: 'report', name: 'Report v1', content: 'Prompt B', version: 1, is_active: false, created_at: '2026-01-03T00:00:00Z', updated_at: '2026-01-04T00:00:00Z' },
  ], isLoading: false, isError: false }),
  useCreatePromptTemplate: () => ({ mutateAsync: mutateCreate }),
  useUpdatePromptTemplate: () => ({ mutateAsync: mutateUpdate }),
  useActivatePromptTemplate: () => ({ mutateAsync: mutateActivate }),
}));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));

afterEach(() => { cleanup(); mutateCreate.mockClear(); mutateUpdate.mockClear(); mutateActivate.mockClear(); });

describe('admin prompt templates', () => {
  it('lists templates and active badge', () => {
    render(<AdminPromptTemplatesPage />);
    expect(screen.getByText('Chat v1')).toBeInTheDocument();
    expect(screen.getByText('Report v1')).toBeInTheDocument();
    expect(screen.getByTestId('active-badge-p1')).toBeInTheDocument();
  });

  it('create form calls create hook', async () => {
    render(<AdminPromptTemplatesPage />);
    fireEvent.change(screen.getByPlaceholderText('Template name'), { target: { value: 'New Prompt' } });
    fireEvent.change(screen.getByPlaceholderText('Prompt content'), { target: { value: 'Body' } });
    fireEvent.click(screen.getAllByText('Create template')[1]);
    expect(mutateCreate).toHaveBeenCalled();
  });

  it('edit form calls update hook', async () => {
    render(<AdminPromptTemplatesPage />);
    fireEvent.click(screen.getAllByText('Edit')[0]);
    fireEvent.change(screen.getAllByDisplayValue('Chat v1')[0], { target: { value: 'Chat v2' } });
    fireEvent.click(screen.getByText('Save changes'));
    expect(mutateUpdate).toHaveBeenCalled();
  });

  it('activate action calls activate hook', async () => {
    render(<AdminPromptTemplatesPage />);
    fireEvent.click(screen.getAllByText('Activate')[0]);
    expect(mutateActivate).toHaveBeenCalledWith('p1');
  });
});
