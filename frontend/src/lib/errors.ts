import axios from 'axios';

export function getUserFacingErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    if (status === 401) return 'Your session has expired. Please sign in again.';
    if (status === 403) return 'Access denied. You do not have permission to view this data.';
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim().length > 0) return detail;
    if (detail && typeof detail === 'object') {
      const message = (detail as { message?: unknown }).message;
      if (typeof message === 'string' && message.trim().length > 0) return message;
    }
  }

  if (error instanceof Error && error.message.trim().length > 0) return error.message;
  return fallback;
}
