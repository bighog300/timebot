import { describe, expect, test } from 'vitest';
import { resolveApiBaseUrl, resolveWsBaseUrl } from '@/lib/env';

describe('env config resolution', () => {
  test('uses VITE_API_URL for api base and derives ws base', () => {
    const input = { VITE_API_URL: 'http://192.168.88.212:8001/' };
    expect(resolveApiBaseUrl(input)).toBe('http://192.168.88.212:8001/api/v1');
    expect(resolveWsBaseUrl(input)).toBe('ws://192.168.88.212:8001');
  });

  test('maps https API URL to secure websocket', () => {
    const input = { VITE_API_URL: 'https://example.com' };
    expect(resolveWsBaseUrl(input)).toBe('wss://example.com');
  });

  test('prefers explicit websocket override', () => {
    const input = {
      VITE_API_URL: 'http://localhost:8000',
      VITE_WS_URL: 'ws://events.example.test:9000/',
    };
    expect(resolveWsBaseUrl(input)).toBe('ws://events.example.test:9000');
  });

  test('preserves legacy defaults', () => {
    expect(resolveApiBaseUrl({})).toBe('/api/v1');
    expect(resolveWsBaseUrl({})).toBe('ws://localhost:8001');
  });
});
