import { describe, expect, it, vi, beforeEach } from 'vitest';

const { mockGet } = vi.hoisted(() => ({ mockGet: vi.fn() }));

vi.mock('@/services/http', () => ({
  http: {
    get: mockGet,
  },
}));

import { api } from '@/services/api';

describe('api.getStructuredInsights', () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it('returns insights array when backend responds with { insights } envelope', async () => {
    const insight = { type: 'risk', title: 'T', description: 'D', severity: 'high' };
    mockGet.mockResolvedValue({ data: { generated_at: '2026-05-01T00:00:00Z', count: 1, insights: [insight] } });

    await expect(api.getStructuredInsights()).resolves.toEqual([insight]);
    expect(mockGet).toHaveBeenCalledWith('/insights/structured');
  });

  it('returns array payload unchanged for backward compatibility', async () => {
    const insights = [{ type: 'info', title: 'T', description: 'D', severity: 'low' }];
    mockGet.mockResolvedValue({ data: insights });

    await expect(api.getStructuredInsights()).resolves.toEqual(insights);
  });

  it('returns [] for missing or malformed insights payloads', async () => {
    mockGet.mockResolvedValueOnce({ data: { generated_at: '2026-05-01T00:00:00Z', count: 0 } });
    await expect(api.getStructuredInsights()).resolves.toEqual([]);

    mockGet.mockResolvedValueOnce({ data: { insights: null } });
    await expect(api.getStructuredInsights()).resolves.toEqual([]);

    mockGet.mockResolvedValueOnce({ data: null });
    await expect(api.getStructuredInsights()).resolves.toEqual([]);
  });
});
