import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AdminPromptTemplatesPage } from '@/pages/AdminPromptTemplatesPage';

const mutateCreate = vi.fn(async () => ({}));
const mutateUpdate = vi.fn(async () => ({}));
const mutateActivate = vi.fn(async () => ({}));
const mutateTest = vi.fn(async () => ({ preview: 'Preview output', fallback_used: true, provider_used: 'gemini', model_used: 'gemini-1.5-flash', primary_error: 'APIError: boom' }));

vi.mock('@/hooks/useApi', () => ({
  useAdminPromptTemplates: () => ({ data: [
    { id: 'p1', type: 'chat', name: 'Chat v1', content: 'Prompt A', version: 1, is_active: true, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-02T00:00:00Z', top_p: 0.4, enabled: false, is_default: false, fallback_enabled: true, fallback_provider: 'openai', fallback_model: 'gpt-4.1-mini' },
    { id: 'p2', type: 'report', name: 'Report v1', content: 'Prompt B', version: 1, is_active: false, created_at: '2026-01-03T00:00:00Z', updated_at: '2026-01-04T00:00:00Z', top_p: 1, enabled: true, is_default: false, fallback_enabled: false, fallback_provider: 'openai', fallback_model: 'gpt-4.1-mini' },
  ], isLoading: false, isError: false }),
  useAdminLlmModels: () => ({ data: { providers: [
    { id: 'openai', name: 'OpenAI', configured: true, models: [{ id: 'gpt-4.1-mini', name: 'GPT-4.1 Mini' }, { id: 'gpt-4o-mini', name: 'GPT-4o Mini' }] },
    { id: 'gemini', name: 'Gemini', configured: false, models: [{ id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash' }] },
  ] }, isLoading: false, isError: false }),
  useCreatePromptTemplate: () => ({ mutateAsync: mutateCreate }),
  useUpdatePromptTemplate: () => ({ mutateAsync: mutateUpdate }),
  useActivatePromptTemplate: () => ({ mutateAsync: mutateActivate }),
  useTestPromptTemplate: () => ({ mutateAsync: mutateTest, isPending: false }),
}));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));

afterEach(() => { cleanup(); mutateCreate.mockClear(); mutateUpdate.mockClear(); mutateActivate.mockClear(); mutateTest.mockClear(); });

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

  it('active row has disabled Active button and does not activate', async () => {
    render(<AdminPromptTemplatesPage />);
    const activeButton = screen.getByRole('button', { name: 'Active' });
    expect(activeButton).toBeDisabled();
    fireEvent.click(activeButton);
    expect(mutateActivate).not.toHaveBeenCalled();
  });

  it('inactive row activate action calls activate hook', async () => {
    render(<AdminPromptTemplatesPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Activate' }));
    expect(mutateActivate).toHaveBeenCalledWith('p2');
  });

  it('sandbox form renders', () => {
    render(<AdminPromptTemplatesPage />);
    expect(screen.getByText('Test prompt')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Prompt content for preview')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Sample context/query/document text')).toBeInTheDocument();
  });

  it('provider/model dropdowns render from catalog and unavailable provider is disabled', () => {
    render(<AdminPromptTemplatesPage />);
    const providerOptions = screen.getAllByRole('option', { name: /OpenAI|Gemini/i });
    expect(providerOptions.some((option) => option.textContent?.includes('OpenAI'))).toBe(true);
    expect(providerOptions.some((option) => option.textContent?.includes('Unavailable'))).toBe(true);
  });

  it('changing provider updates model options', () => {
    render(<AdminPromptTemplatesPage />);
    const selects = screen.getAllByRole('combobox');
    const createProvider = selects[1];
    const createModel = selects[2];
    fireEvent.change(createProvider, { target: { value: 'gemini' } });
    expect((createModel as HTMLSelectElement).value).toBe('gemini-1.5-flash');
  });

  it('running preview calls test endpoint hook', async () => {
    render(<AdminPromptTemplatesPage />);
    fireEvent.change(screen.getByPlaceholderText('Prompt content for preview'), { target: { value: 'Prompt body' } });
    fireEvent.change(screen.getByPlaceholderText('Sample context/query/document text'), { target: { value: 'Sample question' } });
    fireEvent.click(screen.getByText('Run preview'));
    expect(mutateTest).toHaveBeenCalled();
  });

  it('preview response renders', async () => {
    render(<AdminPromptTemplatesPage />);
    fireEvent.change(screen.getByPlaceholderText('Prompt content for preview'), { target: { value: 'Prompt body' } });
    fireEvent.change(screen.getByPlaceholderText('Sample context/query/document text'), { target: { value: 'Sample question' } });
    fireEvent.click(screen.getByText('Run preview'));
    expect(await screen.findByText('Preview output')).toBeInTheDocument();
    expect(screen.getByText(/Fallback used: yes/)).toBeInTheDocument();
  });



  it('edit panel shows execution and fallback controls', () => {
    render(<AdminPromptTemplatesPage />);
    fireEvent.click(screen.getAllByText('Edit')[0]);
    expect(screen.getByLabelText('edit-top_p')).toBeInTheDocument();
    expect(screen.getByLabelText('edit-enabled')).toBeInTheDocument();
    expect(screen.getByLabelText('edit-is_default')).toBeInTheDocument();
    expect(screen.getByLabelText('edit-fallback_provider')).toBeInTheDocument();
    expect(screen.getByLabelText('edit-fallback_model')).toBeInTheDocument();
  });

  it('edit save includes updated top_p, booleans, and fallback provider/model', async () => {
    render(<AdminPromptTemplatesPage />);
    fireEvent.click(screen.getAllByText('Edit')[0]);
    fireEvent.change(screen.getByLabelText('edit-top_p'), { target: { value: '0.7' } });
    fireEvent.click(screen.getByLabelText('edit-enabled'));
    fireEvent.click(screen.getByLabelText('edit-is_default'));
    fireEvent.change(screen.getByLabelText('edit-fallback_provider'), { target: { value: 'gemini' } });
    fireEvent.change(screen.getByLabelText('edit-fallback_model'), { target: { value: 'gemini-1.5-flash' } });
    fireEvent.click(screen.getByText('Save changes'));

    expect(mutateUpdate).toHaveBeenCalledWith(expect.objectContaining({
      promptId: 'p1',
      payload: expect.objectContaining({
        top_p: 0.7,
        enabled: true,
        is_default: true,
        fallback_provider: 'gemini',
        fallback_model: 'gemini-1.5-flash',
      }),
    }));
  });

  it('error state renders', async () => {
    mutateTest.mockImplementationOnce(async () => { throw new Error('preview failed'); });
    render(<AdminPromptTemplatesPage />);
    fireEvent.change(screen.getByPlaceholderText('Prompt content for preview'), { target: { value: 'Prompt body' } });
    fireEvent.change(screen.getByPlaceholderText('Sample context/query/document text'), { target: { value: 'Sample question' } });
    fireEvent.click(screen.getByText('Run preview'));
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });

});


it('fallback controls render and disable until enabled', () => {
  render(<AdminPromptTemplatesPage />);
  const fallbackToggle = screen.getByLabelText('Enable fallback');
  expect(fallbackToggle).toBeInTheDocument();
  const selects = screen.getAllByRole('combobox');
  expect((selects[3] as HTMLSelectElement).disabled).toBe(true);
  fireEvent.click(fallbackToggle);
  expect((selects[3] as HTMLSelectElement).disabled).toBe(false);
});
