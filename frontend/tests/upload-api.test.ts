import { beforeEach, expect, test, vi } from 'vitest';
import { api } from '@/services/api';

const postMock = vi.fn();

vi.mock('@/services/http', () => ({
  http: {
    post: (...args: unknown[]) => postMock(...args),
    get: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

beforeEach(() => {
  postMock.mockReset();
});

test('upload sends FormData to /upload/ with Authorization header', async () => {
  postMock.mockResolvedValue({ data: { id: '1', filename: 'a.pdf', processing_status: 'queued' } });
  const file = new File(['pdf'], 'a.pdf', { type: 'application/pdf' });

  await api.uploadDocument(file, 'token-abc');

  expect(postMock).toHaveBeenCalledTimes(1);
  const [url, body, config] = postMock.mock.calls[0];
  expect(url).toBe('/upload/');
  expect(body).toBeInstanceOf(FormData);
  expect(config.headers.Authorization).toBe('Bearer token-abc');
});
