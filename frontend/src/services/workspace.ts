import { WORKSPACE_STORAGE_KEY } from '@/services/http';

export function getActiveWorkspaceId(): string {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem(WORKSPACE_STORAGE_KEY) || '';
}

export function setActiveWorkspaceId(workspaceId: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(WORKSPACE_STORAGE_KEY, workspaceId);
}
