import axios from 'axios';
import { describe, expect, test } from 'vitest';
import { getUserFacingErrorMessage } from '@/lib/errors';

describe('getUserFacingErrorMessage', () => {
  test('shows access denied message for 403', () => {
    const error = {
      isAxiosError: true,
      response: { status: 403, data: { detail: 'forbidden' } },
      message: 'Request failed',
    } as unknown;
    expect(getUserFacingErrorMessage(error, 'fallback')).toContain('Access denied');
  });

  test('shows sign in again message for 401', () => {
    const error = { isAxiosError: true, response: { status: 401 }, message: 'Unauthorized' } as unknown;
    expect(getUserFacingErrorMessage(error, 'fallback')).toContain('sign in again');
  });
});
