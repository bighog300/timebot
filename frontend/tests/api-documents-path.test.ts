import { describe, expect, test, vi } from 'vitest';

const { get } = vi.hoisted(() => ({
  get: vi.fn().mockResolvedValue({ data: [] }),
}));

vi.mock('@/services/http', () => ({ http: { get } }));

import { api } from '@/services/api';

describe('documents API path', () => {
  test('listDocuments uses canonical trailing slash endpoint', async () => {
    await api.listDocuments(false);
    expect(get).toHaveBeenCalledWith('/documents/', { params: { include_archived: false } });
  });
});
