import { describe, expect, test, vi } from 'vitest';

const { get, post } = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn().mockResolvedValue({ data: {} }),
}));

vi.mock('@/services/http', () => ({ http: { get, post } }));

import { api } from '@/services/api';

describe('prompt templates api', () => {
  test('createPromptTemplate posts backend keys directly', async () => {
    const payload = {
      type: 'chat' as const,
      name: 'n',
      content: 'c',
      provider: 'openai' as const,
      model: 'gpt-4.1-mini',
      temperature: 0.2,
      max_tokens: 100,
      top_p: 1,
      enabled: true,
      is_default: false,
      fallback_enabled: false,
    };

    await api.createPromptTemplate(payload);
    expect(post).toHaveBeenCalledWith('/admin/prompts', payload);
    expect(post.mock.calls[0][1]).not.toHaveProperty('prompt_type');
  });

  test('testPromptTemplate posts type and content directly', async () => {
    const payload = {
      type: 'chat' as const,
      content: 'Prompt body',
      sample_context: 'Sample',
      provider: 'openai' as const,
      model: 'gpt-4.1-mini',
      temperature: 0.2,
      max_tokens: 100,
      top_p: 1,
    };

    await api.testPromptTemplate(payload);
    expect(post).toHaveBeenCalledWith('/admin/prompts/test', payload);
    expect(post.mock.calls[0][1]).not.toHaveProperty('prompt_type');
  });

  test('listPromptTemplates normalizes legacy prompt_type into type', async () => {
    get.mockResolvedValueOnce({ data: [{ id: '1', prompt_type: 'chat', name: 'n', content: 'c' }] });
    const result = await api.listPromptTemplates();
    expect(result[0]).toMatchObject({ type: 'chat' });
  });
});
